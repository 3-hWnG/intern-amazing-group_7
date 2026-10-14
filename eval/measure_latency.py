"""Mục 3.1/3.4 của kế hoạch: độ trễ đầu-cuối qua /chat, p50/p95 theo loại câu.
Loại câu (lấy từ DEV và ctx, mẫu cố định theo seed, gửi tuần tự):
  simple   = một lượt, một thủ tục (expected có đúng 1 task, hành vi answer)
  complex  = nhiều ý (>= 2 task) hoặc hội thoại nhiều lượt (tính lượt cuối)
  clarify  = câu bị hỏi lại; out     = câu ngoài phạm vi (từ chối)
  llm      = câu có bước sinh chữ bằng LLM (cases_composer.jsonl; chỉ khi --llm 1, đây là đường chậm)
Cấu hình: --llm 0 = S3_USE_LLM=0 (chỉ luật, chạy trên CPU; thay cho "không GPU"), --llm 1 = mặc định thật (bước sinh chữ bằng Ollama).
Chạy:  PYTHONIOENCODING=utf-8 python run_server.py eval/measure_latency.py --llm 0 [--n 30] [--name x]   -> results/latency_<name>_llm<0|1>.json
Lưu ý: llm=0 đo CPU thật của máy này, không phải máy không có GPU nào khác; máy khác ra số khác."""
import argparse, json, os, random, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = 8394
ap = argparse.ArgumentParser()
ap.add_argument("--llm", type=int, choices=(0, 1), required=True)
ap.add_argument("--n", type=int, default=30, help="số câu mỗi loại")
ap.add_argument("--name", default="x")
ap.add_argument("--seed", type=int, default=31)
a = ap.parse_args()


def load(fn):
    return [json.loads(l) for l in open(os.path.join(HERE, fn), encoding="utf-8")]


def users(c):
    return [t for t in c["turns"] if t["role"] == "user"]


def klass(c):
    e, n = c["expected"], len(users(c))
    tasks = e.get("tasks") or []
    beh = e.get("behavior")
    if beh == "clarify":
        return "clarify"
    if beh == "apologize" and not tasks:
        return "out"
    if n >= 2 or len(tasks) >= 2:
        return "complex"
    if len(tasks) == 1 and beh in (None, "answer"):
        return "simple"
    return None


def pick():
    rows = [c for c in load("cases.jsonl") if c["split"] == "dev"] + load("cases_ctx.jsonl")
    by = {}
    for c in rows:
        k = klass(c)
        if k:
            by.setdefault(k, []).append(c)
    if a.llm:
        by["llm"] = load("cases_composer.jsonl")
    rng = random.Random(a.seed)
    return {k: rng.sample(v, min(a.n, len(v))) for k, v in sorted(by.items())}


def pct(v, q):
    return sorted(v)[min(len(v) - 1, int(q * len(v)))] if v else 0


tmp = tempfile.mkdtemp()
env = {k: v for k, v in os.environ.items() if k not in ("S3_USE_LLM", "S3_NO_WARMUP")}
env.update(APP_PORT=str(PORT), S3_DB_PATH=os.path.join(tmp, "s3.db"), S3_DEV="1", S3_PLANNER_MODE="rules", PYTHONIOENCODING="utf-8")
if a.llm == 0:
    env.update(S3_USE_LLM="0", S3_NO_WARMUP="1")
logf = open(os.path.join(tmp, "server.log"), "wb")     # không dùng PIPE: đầy bộ đệm thì server kẹt
srv = subprocess.Popen([sys.executable, "run_server.py"], cwd=ROOT, env=env, stdout=logf, stderr=subprocess.STDOUT)


def call(path, body=None, timeout=120):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", json.dumps(body).encode() if body is not None else None, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def run(c):
    cid, ms, r = None, 0, None
    for t in users(c):
        t0 = time.perf_counter()
        r = call("/chat", {"text": t["text"], "conversation_id": cid})
        cid, ms = r["conversation_id"], (time.perf_counter() - t0) * 1000
    return round(ms), r["kind"]


out = {"use_llm": a.llm, "seed": a.seed}
try:
    for _ in range(120):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2)
            break
        except Exception:
            time.sleep(1)
    if a.llm:
        for _ in range(90):                       # chờ nạp model
            if call("/config")["model_loaded"]:
                break
            time.sleep(1)
    out["config"] = {k: v for k, v in call("/config").items() if k in ("answer_llm", "model_loaded", "model", "mode")}
    print("config:", out["config"], flush=True)
    sets = pick()
    for k, cs in sets.items():
        ms = []
        for c in cs:
            ms.append(run(c)[0])
        out[k] = {"n": len(ms), "p50": pct(ms, .5), "p95": pct(ms, .95), "max": max(ms), "ms": ms}
        print(f"{k:8s} n={len(ms):3d} p50={out[k]['p50']:6d} ms  p95={out[k]['p95']:6d} ms  max={max(ms)} ms", flush=True)
    allms = [m for k in sets for m in out[k]["ms"]]
    out["all"] = {"n": len(allms), "p50": pct(allms, .5), "p95": pct(allms, .95)}
    print("all", {k: v for k, v in out["all"].items()}, flush=True)
    json.dump(out, open(os.path.join(HERE, "results", f"latency_{a.name}_llm{a.llm}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
finally:
    srv.terminate()

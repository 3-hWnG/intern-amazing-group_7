"""Phase 27: độ trễ ĐẦU-CUỐI qua /chat (hàng đợi 1 worker + Planner luật + Answerer + LLM) với cấu hình MẶC ĐỊNH (không đặt S3_USE_LLM).
Khởi động server tạm (cổng 8393, DB hội thoại tạm, S3_DEV=1 để thấy trace), chờ warm-up nạp model, rồi gửi tuần tự (không song song):
  A) 63 ca của cases_composer.jsonl (đều kích hoạt bước LLM): p50/p95/max, tỉ lệ lượt có 'llm lỗi' (timeout/lỗi), tỉ lệ lượt LLM giữ được ý;
  B) mẫu DEV một lượt không kích hoạt LLM (seed 27, tối đa 150 ca) để có phân phối thật của mọi câu.
Chạy: cd eval && PYTHONIOENCODING=utf-8 python p27_e2e.py [--limit N] [--name x]   (cần Ollama + qwen3:4b; ghi results/p27_e2e_<name>.json)."""
import argparse, json, os, random, statistics, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = 8393
ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--name", default="x")
a = ap.parse_args()
tmp = tempfile.mkdtemp()
env = {k: v for k, v in os.environ.items() if k not in ("S3_USE_LLM", "S3_NO_WARMUP")}      # mặc định thật
env.update(APP_PORT=str(PORT), S3_DB_PATH=os.path.join(tmp, "s3.db"), S3_DEV="1", S3_PLANNER_MODE="rules", PYTHONIOENCODING="utf-8")
logf = open(os.path.join(tmp, "server.log"), "wb")      # KHÔNG dùng PIPE chưa đọc: đầy bộ đệm ống (~64 KB) thì server kẹt khi ghi log và /chat treo
srv = subprocess.Popen([sys.executable, "run_server.py"], cwd=ROOT, env=env, stdout=logf, stderr=subprocess.STDOUT)


def call(path, body=None, timeout=60):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", json.dumps(body).encode() if body is not None else None, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def pct(v, q):
    return sorted(v)[min(len(v) - 1, int(q * len(v)))] if v else 0


def run_turns(turns):
    cid, last = None, None
    for t in [x["text"] for x in turns if x["role"] == "user"]:
        t0 = time.perf_counter()
        r = call("/chat", {"text": t, "conversation_id": cid}, timeout=120)
        cid = r["conversation_id"]
        last = (time.perf_counter() - t0) * 1000, r
    ms, r = last
    v = (r.get("dev", {}).get("trace") or {}).get("verify") or []
    return {"ms": round(ms), "server_ms": (r.get("dev") or {}).get("total_ms"), "kind": r["kind"],
            "llm_err": any("llm lỗi" in x for x in v), "so_sanh": any(b.get("title") == "So sánh" for b in r["blocks"]),
            "dropped": sum(1 for x in v if x.startswith("bỏ ý"))}


out = {}
try:
    for _ in range(90):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2)
            break
        except Exception:
            time.sleep(1)
    cfg0 = call("/config")
    for _ in range(60):          # warm-up chạy nền
        cfg = call("/config")
        if cfg["model_loaded"]:
            break
        time.sleep(1)
    out["config"] = {k: cfg[k] for k in ("answer_llm", "answer_timeout", "model_loaded", "mode", "model")}
    print("config mặc định:", out["config"], flush=True)
    A = [json.loads(l) for l in open(os.path.join(HERE, "cases_composer.jsonl"), encoding="utf-8")]
    trig = {c["id"] for c in A}
    if a.limit:
        A = A[:a.limit]
    ra = []
    for c in A:
        ra.append({"id": c["id"], **run_turns(c["turns"])})
        print(f"A {c['id']:24s} {ra[-1]['ms']:6d} ms llm_err={ra[-1]['llm_err']} so_sanh={ra[-1]['so_sanh']}", flush=True)
    B = [json.loads(l) for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8")]
    B = [c for c in B if c["split"] == "dev" and c["id"] not in trig and len([t for t in c["turns"] if t["role"] == "user"]) == 1]
    B = random.Random(27).sample(B, min(150 if not a.limit else a.limit, len(B)))
    rb = []
    for c in B:
        rb.append({"id": c["id"], **run_turns(c["turns"])})
    for name, rows in (("A_llm", ra), ("B_dev_khac", rb), ("A+B", ra + rb)):
        v = [r["ms"] for r in rows]
        out[name] = {"n": len(v), "p50": pct(v, .5), "p95": pct(v, .95), "max": max(v), "llm_err": sum(r["llm_err"] for r in rows),
                     "so_sanh": sum(r["so_sanh"] for r in rows)}
        print(name, out[name], flush=True)
    out["rows_A"], out["rows_B"] = ra, rb
    json.dump(out, open(os.path.join(HERE, "results", f"p27_e2e_{a.name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
finally:
    srv.terminate()

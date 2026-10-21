"""Đo tải 10 người giả trên model THẬT (G3.4, P16): điền bảng SLO (docs/ARCHITECTURE_REVIEW_2026-10-15.md mục 5.4).

    python run_server.py system4/eval/load_test.py [--users 10] [--turns 6] [--db data/runtime/knowledge/3-....db]

Tự chạy một server riêng (cổng 8397, S4_ENABLED=1, thư mục runtime tạm, Ollama thật), nạp model trước (đo "nóng"),
rồi N người dùng song song, mỗi người `turns` lượt xen kẽ Strict (chỉ luật / có bước LLM) và Friendly, nghỉ 1–3 giây giữa các lượt.
Lượt Strict được xếp loại theo trace (có lời gọi LLM hay không), không theo ý định câu hỏi.
Số đo:
  Strict: thời gian phía người dùng (request -> có câu trả lời); bước LLM tách chờ GPU / nạp / đọc lời dặn / sinh chữ (trace.llm_calls)
  Friendly: chữ đầu tiên, cả câu (sự kiện "done"), chờ tới lượt GPU (meta.queue_ms)
Ghi system4/eval/results/load_<n>users.json. Không gọi dịch vụ ngoài (Tìm web tắt)."""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
PORT = 8397
BASE = f"http://127.0.0.1:{PORT}"
STRICT_RULES = ["Đăng ký khai sinh cần giấy tờ gì?", "Đăng ký kết hôn nộp ở đâu?", "Lệ phí cấp hộ chiếu là bao nhiêu?",
                "Đăng ký tạm trú mất bao lâu?", "Chứng thực bản sao lệ phí bao nhiêu?", "Khai tử cần giấy tờ gì?"]
STRICT_LLM = ["Tôi ở nhà thuê thì đăng ký thường trú cần giấy tờ gì?", "Tạm trú với thường trú khác nhau chỗ nào?",
              "Hộ gia đình tách hộ vì ly hôn thì cần giấy tờ gì?", "Cho mình hỏi các bước tách hộ và các bước xóa đăng ký thường trú"]
FRIENDLY = ["Cho mình vài mẹo học tiếng Anh mỗi ngày", "Viết giúp mình lời chúc sinh nhật ngắn cho mẹ",
            "Làm sao để ngủ ngon hơn?", "Gợi ý 3 món ăn sáng nhanh gọn", "Giải thích lãi suất kép bằng ví dụ đơn giản",
            "Mình nên chuẩn bị gì cho buổi phỏng vấn xin việc?"]


def pct(xs, q):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))], 2) if xs else None


def summ(xs):
    return {"n": len(xs), "p50": pct(xs, 0.5), "p95": pct(xs, 0.95), "max": round(max(xs), 2) if xs else None}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=10)
    ap.add_argument("--turns", type=int, default=6)
    ap.add_argument("--db", default="")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--pause", default="1,3", help="nghỉ giữa hai lượt của một người, giây 'min,max' (1,3 = dồn dập; 20,40 = thực tế)")
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="s4load_")
    env = {k: v for k, v in os.environ.items() if k not in ("S3_USE_LLM", "S3_NO_WARMUP", "S4_FORCE_CPU")}
    env.update(APP_PORT=str(PORT), S4_ENABLED="1", S3_DB_PATH=os.path.join(tmp, "s3.db"), S4_RUNTIME_DIR=os.path.join(tmp, "s4"),
               S3_PLANNER_MODE="rules", S4_ABI_SYNC="0", PYTHONIOENCODING="utf-8",
               S4_RATE_LIMIT="0")   # đo sức chịu của model, không đo giới hạn lượt hỏi (ratelimit.py)
    if a.db:
        env["S3_DATA_DB"] = a.db
    log = open(os.path.join(tmp, "server.log"), "w", encoding="utf-8")
    srv = subprocess.Popen([sys.executable, "run_server.py"], cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(180):
            try:
                if httpx.get(BASE + "/health", timeout=2).status_code == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            print("server không lên; xem", log.name)
            return 2
        admin = httpx.Client(base_url=BASE, timeout=300)
        assert admin.post("/s4/auth/signup", json={"username": "loadadmin", "password": "matkhau123"}).status_code == 200
        clients = []
        for i in range(a.users):
            cl = httpx.Client(base_url=BASE, timeout=300)
            assert cl.post("/s4/auth/signup", json={"username": f"load{i}", "password": "matkhau123"}).status_code == 200
            clients.append(cl)
        # nạp model trước (đo "nóng"), không tính
        friendly(clients[0], "Xin chào")
        strict(clients[0], admin, STRICT_LLM[0])
        print(f"đã nạp model; {a.users} người x {a.turns} lượt", flush=True)

        rng = random.Random(a.seed)
        pmin, pmax = (float(x) for x in a.pause.split(","))
        plans = []
        for i in range(a.users):
            kinds = (["rules", "llm", "friendly"] * a.turns)[:a.turns]
            rng.shuffle(kinds)
            plans.append([(k, rng.choice({"rules": STRICT_RULES, "llm": STRICT_LLM, "friendly": FRIENDLY}[k]), rng.uniform(pmin, pmax))
                          for k in kinds])
        out, lock = [], threading.Lock()

        def run_user(i):
            time.sleep(rng.uniform(0, 2))
            for kind, q, pause in plans[i]:
                try:
                    r = friendly(clients[i], q) if kind == "friendly" else strict(clients[i], admin, q)
                    r.update(user=i, asked=kind, q=q)
                except Exception as e:   # noqa: BLE001 - ghi lỗi, đo tiếp
                    r = {"user": i, "asked": kind, "q": q, "error": f"{type(e).__name__}: {e}"[:200]}
                with lock:
                    out.append(r)
                time.sleep(pause)

        t0 = time.time()
        ths = [threading.Thread(target=run_user, args=(i,)) for i in range(a.users)]
        for t in ths:
            t.start()
        for t in ths:
            t.join()
        wall = time.time() - t0
    finally:
        srv.terminate()
        try:
            srv.wait(15)
        except subprocess.TimeoutExpired:
            srv.kill()
        log.close()

    sr = [r for r in out if r.get("kind") == "strict_rules"]
    sl = [r for r in out if r.get("kind") == "strict_llm"]
    fr = [r for r in out if r.get("kind") == "friendly"]
    calls = [c for r in sl for c in r.get("llm_calls", [])]
    res = {
        "at": time.strftime("%Y-%m-%d %H:%M:%S"), "users": a.users, "turns_per_user": a.turns, "pause_s": a.pause, "wall_s": round(wall, 1),
        "errors": [r for r in out if "error" in r],
        "strict_rules_s": summ([r["s"] for r in sr]),
        "strict_llm_s": summ([r["s"] for r in sl]),
        "strict_llm_parts_s": {k: summ([c.get(k, 0) for c in calls]) for k in ("wait_s", "load_s", "prompt_s", "gen_s", "call_s")},
        "strict_llm_gave_up": sum(1 for r in sl if any(c.get("error") for c in r.get("llm_calls", []))),
        "friendly_first_s": summ([r["first"] for r in fr if r.get("first") is not None]),
        "friendly_done_s": summ([r["done"] for r in fr if r.get("done") is not None]),
        "friendly_queue_s": summ([r["queue_ms"] / 1000 for r in fr if r.get("queue_ms") is not None]),
        "turns": out,
    }
    path = Path(__file__).resolve().parent / "results" / f"load_{a.users}users{('_' + a.name) if a.name else ''}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in res.items():
        if k not in ("turns", "errors"):
            print(f"{k}: {v}")
    print(f"lỗi: {len(res['errors'])} — ghi {path}")
    return 0 if not res["errors"] else 1


def strict(cl, admin, q):
    t = time.perf_counter()
    r = cl.post("/s4/strict/chat", json={"text": q})
    r.raise_for_status()
    s = time.perf_counter() - t
    tr = admin.get(f"/s4/strict/trace/{r.json()['message_id']}").json().get("s3_trace") or {}
    tr = tr.get("trace") or {}
    calls = tr.get("llm_calls") or []
    return {"kind": "strict_llm" if calls else "strict_rules", "s": round(s, 3), "llm_calls": calls, "verify": tr.get("verify") or []}


def friendly(cl, q):
    t0, first, done, cid = time.perf_counter(), None, None, None
    with cl.stream("POST", "/s4/chat", json={"text": q}) as r:
        r.raise_for_status()
        buf = ""
        for chunk in r.iter_text():
            buf += chunk
            while "\n\n" in buf:
                line, buf = buf.split("\n\n", 1)
                if not line.startswith("data: "):
                    continue
                ev = json.loads(line[6:])
                if ev["type"] == "meta":
                    cid = ev["conversation_id"]
                elif ev["type"] == "delta" and first is None:
                    first = time.perf_counter() - t0
                elif ev["type"] == "done":
                    done = time.perf_counter() - t0   # người dùng thấy xong câu ở đây; luồng còn mở chờ việc nền (bộ nhớ)
                elif ev["type"] == "error":
                    raise RuntimeError(ev.get("message"))
    total = time.perf_counter() - t0
    meta = cl.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]["meta"]
    return {"kind": "friendly", "first": round(first, 3) if first is not None else None,
            "done": round(done, 3) if done is not None else None, "stream_closed": round(total, 3),
            "queue_ms": meta.get("queue_ms"), "timing": meta.get("timing")}


if __name__ == "__main__":
    raise SystemExit(main())

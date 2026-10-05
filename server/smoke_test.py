"""Smoke test: chạy `python smoke_test.py` (khởi động server riêng, DB tạm, cổng 8391)."""
import json, os, sqlite3, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

here = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp()) / "t.db"
env = {**os.environ, "S3_DB_PATH": str(tmp), "APP_PORT": "8391", "S3_DEV": "1", "PYTHONIOENCODING": "utf-8"}
srv = subprocess.Popen([sys.executable, "main.py"], cwd=here, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
U = "http://127.0.0.1:8391"


def call(path, body=None):
    req = urllib.request.Request(U + path, json.dumps(body).encode() if body else None,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.status, json.load(r)


try:
    for _ in range(30):
        try:
            call("/health"); break
        except Exception:
            time.sleep(0.3)
    print("health", call("/health"))
    s, a = call("/chat", {"text": "Xin chào, làm khai sinh?"})
    assert s == 200 and len(a["blocks"]) == 2 and a["conversation_id"], a
    s, b = call("/chat", {"text": "cho clarify", "conversation_id": a["conversation_id"]})
    assert b["kind"] == "clarify" and b["clarify"]["options"], b
    s, c = call("/chat", {"text": "Đăng ký khai sinh", "conversation_id": a["conversation_id"],
                          "reply_to": b["message_id"]})
    assert "Bạn chọn" in c["blocks"][0]["text"], c
    s, m = call(f"/conversations/{a['conversation_id']}/messages")
    assert len(m["messages"]) == 6, len(m["messages"])
    db = sqlite3.connect(tmp)
    print("rows", {t: db.execute(f"select count(*) from {t}").fetchone()[0]
                   for t in ("conversations", "messages", "turn_traces")})
    db.close()
    print("OK", json.dumps(c, ensure_ascii=False)[:200])
finally:
    srv.terminate()

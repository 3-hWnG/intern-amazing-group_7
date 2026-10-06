"""Smoke test: chạy `python smoke_test.py` (khởi động server riêng, DB tạm, cổng 8391, S3_USE_LLM=0). Cần PYTHONPATH=<gốc chứa system3>."""
import json, os, sqlite3, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path

here = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp()) / "t.db"
PORT = 8391
env = {**os.environ, "S3_DB_PATH": str(tmp), "APP_PORT": str(PORT), "S3_DEV": "1", "S3_USE_LLM": "0", "PYTHONIOENCODING": "utf-8"}
srv = subprocess.Popen([sys.executable, "main.py"], cwd=here, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
U = f"http://127.0.0.1:{PORT}"


def call(path, body=None):
    req = urllib.request.Request(U + path, json.dumps(body).encode() if body is not None else None,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, json.load(r)


try:
    for _ in range(60):
        try:
            call("/health"); break
        except Exception:
            time.sleep(0.5)
    s, h = call("/health")
    assert s == 200 and h["ok"], h
    print("health", h)

    # 1) câu thủ tục rõ: trả lời có nguồn
    s, a = call("/chat", {"text": "Đăng ký khai sinh cần giấy tờ gì?"})
    cid = a["conversation_id"]
    assert s == 200 and a["kind"] == "answer" and a["blocks"] and cid, a
    assert any(b.get("sources") for b in a["blocks"]), "trả lời thiếu nguồn"

    # 2) câu mơ hồ: hỏi lại, bấm nút -> trả lời đúng thủ tục đã chọn
    s, b = call("/chat", {"text": "Tôi muốn xin trợ cấp hàng tháng"})   # hội thoại mới: không kế thừa mục đang hỏi
    cid = b["conversation_id"]
    assert b["kind"] == "clarify" and len(b["clarify"]["options"]) >= 2, b
    label = b["clarify"]["options"][0]
    pid = b["clarify"]["meta"]["option_ids"][label]
    s, c = call("/chat", {"text": label, "conversation_id": cid, "reply_to": b["message_id"]})
    assert c["kind"] == "answer" and c["blocks"], c
    assert any(pid in json.dumps(x, ensure_ascii=False) for x in (c["dev"]["plan"], c["dev"]["trace"])), "không dùng đúng thủ tục đã chọn"

    # 3) messages + trace (hội thoại thứ hai: 2 lượt x (user + assistant))
    s, m = call(f"/conversations/{cid}/messages")
    assert len(m["messages"]) == 4, len(m["messages"])
    s, t = call(f"/conversations/{cid}/messages/{c['message_id']}/trace")
    assert s == 200 and t, t
    try:
        call(f"/conversations/{cid}/messages/999999/trace")
        raise AssertionError("trace không tồn tại phải 404")
    except urllib.error.HTTPError as e:
        assert e.code == 404, e.code
    db = sqlite3.connect(tmp)
    rows = {k: db.execute(f"select count(*) from {k}").fetchone()[0] for k in ("conversations", "messages", "turn_traces")}
    db.close()
    assert rows["conversations"] == 2 and rows["messages"] == 6 and rows["turn_traces"] == 3, rows
    print("rows", rows)
    print("OK")
finally:
    srv.terminate()

"""Câu hỏi tổng quát về tệp văn bản ("tóm tắt file") nhận các đoạn đầu của tệp; câu hỏi thường thì không.
Model giả (embedding, reranker, LLM). Chạy:  python run_server.py system4/tests/overview_test.py"""
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server"))
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RUNTIME_DIR=os.path.join(TMP, "s4"))

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, llm, search

for q in ("Tóm tắt nội dung file giúp mình", "file này nói về cái gì?", "Tài liệu này nói gì vậy", "tom tat tai lieu", "Nội dung của tệp là gì"):
    assert search.is_overview(q), q
for q in ("Phí cấp căn cước là bao nhiêu?", "Domain mềm khác domain cứng thế nào?", "Ai phụ trách viết báo cáo?"):
    assert not search.is_overview(q), q


def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * 1024
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 1024] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


prompts = []
sent = lambda: "\n".join(m["content"] for m in prompts[-1])   # system + tin người dùng (dữ liệu nằm ở một trong hai)


async def fake_fast(messages, schema):
    prompts.append(messages)
    raw = json.dumps({"plan": "", "answer": "Dạ [1].", "ask_back": False, "choices": [], "sources": [1]})
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


search.embed = fake_embed
search.rerank = lambda q, ts: [-10.0] * len(ts)   # không đoạn nào qua ngưỡng: chỉ đường dự phòng mới có chữ
llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
TEXT = ("Quy chế nội bộ\n\nĐiều 1. Giờ làm việc từ 8 giờ đến 17 giờ.\n\nĐiều 2. Nghỉ trưa một tiếng.\n\n"
        "Điều 3. Đi muộn quá ba lần trong tháng thì bị nhắc nhở bằng văn bản.").encode("utf-8")

with TestClient(main.app) as c:
    c.cookies.clear()
    tok = c.post("/s4/auth/signup", json={"username": "dev1", "password": "123456"}).cookies.get(auth.COOKIE)
    c.cookies.clear()
    c.cookies.set(auth.COOKIE, tok)
    r = c.post("/s4/datasets", files={"file": ("quy che.txt", TEXT)})
    assert r.status_code == 200, r.text
    d = r.json()["dataset"]
    for _ in range(100):
        d = next(x for x in c.get("/s4/datasets").json()["datasets"] if x["id"] == d["id"])
        if d["status"] in ("ready", "error"):
            break
        time.sleep(0.2)
    assert d["status"] == "ready" and d["kind"] == "text", d
    c.post("/s4/chat", json={"text": "Tóm tắt nội dung file này"})
    assert "Giờ làm việc từ 8 giờ" in sent(), "tóm tắt: phải có đoạn đầu của tệp"
    c.post("/s4/chat", json={"text": "Ai là giám đốc?"})
    assert "Giờ làm việc từ 8 giờ" not in sent(), "câu hỏi thường không dùng đường dự phòng"
print("OK overview_test")

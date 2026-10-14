"""Nút gợi ý (choices) do AI sinh chỉ giữ cái mà bộ dữ liệu đang bật tìm được đoạn khớp.
Model giả (embedding, reranker, LLM). Chạy:  python run_server.py system4/tests/choices_test.py"""
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


def words(t):
    return set(re.findall(r"\w+", t.lower()))


def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * 1024
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 1024] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


CHOICES = ["Giờ làm việc", "Giá vé máy bay", "Nghỉ trưa"]
ask = {"on": True}


async def fake_fast(messages, schema):
    d = ({"plan": "", "answer": "Bạn muốn hỏi về mục nào?", "ask_back": True, "choices": CHOICES, "sources": []} if ask["on"]
         else {"plan": "", "answer": "Dạ.", "ask_back": False, "choices": [], "sources": []})
    raw = json.dumps(d)
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


search.embed = fake_embed
search.rerank_pairs = lambda ps: [5.0 if words(q) & words(t) else -10.0 for q, t in ps]   # có từ chung với đoạn thì qua ngưỡng
search.rerank = lambda q, ts: search.rerank_pairs([(q, t) for t in ts])
llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
TEXT = ("Quy chế nội bộ\n\nĐiều 1. Giờ làm việc từ 8 giờ đến 17 giờ.\n\nĐiều 2. Nghỉ trưa một tiếng.").encode("utf-8")

with TestClient(main.app) as c:
    c.cookies.clear()
    tok = c.post("/s4/auth/signup", json={"username": "dev1", "password": "123456"}).cookies.get(auth.COOKIE)
    c.cookies.clear()
    c.cookies.set(auth.COOKIE, tok)

    def last_meta(text):
        r = c.post("/s4/chat", json={"text": text})
        cid = json.loads(r.text.split("\n\n")[0][6:])["conversation_id"]
        return c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]["meta"]

    m = last_meta("Cho mình hỏi")   # chưa có dữ liệu: AI chung, giữ nguyên các nút
    assert m.get("choices") == CHOICES and "choices_filter" not in m, m

    r = c.post("/s4/datasets", files={"file": ("quy che.txt", TEXT)})
    assert r.status_code == 200, r.text
    ds_id = r.json()["dataset"]["id"]
    for _ in range(100):
        d = next(x for x in c.get("/s4/datasets").json()["datasets"] if x["id"] == ds_id)
        if d["status"] in ("ready", "error"):
            break
        time.sleep(0.2)
    assert d["status"] == "ready", d

    m = last_meta("Cho mình hỏi")   # có dữ liệu: bỏ nút mà dữ liệu không có
    assert m.get("choices") == ["Giờ làm việc", "Nghỉ trưa"], m
    assert m["choices_filter"] == {"before": 3, "kept": 2}, m

    CHOICES[:] = ["Giá vé máy bay", "Thời tiết hôm nay"]   # không nút nào có trong dữ liệu: không hiện nút nào
    m = last_meta("Cho mình hỏi")
    assert not m.get("choices") and m["choices_filter"]["kept"] == 0, m

    ask["on"] = False   # không hỏi lại: không chạy bước lọc
    assert "choices_filter" not in last_meta("Giờ làm việc thế nào?")
print("OK choices_test")

"""2c: domain cứng / mềm, dataset theo domain, guardrail của domain, khoá theo loại tài khoản (dev / cán bộ / người dân).
Model giả (embedding, reranker, LLM): không cần Ollama. Chạy: python run_server.py system4/tests/test_domains.py"""
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import time

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RUNTIME_DIR=os.path.join(TMP, "s4"),
                  OLLAMA_HOST="http://127.0.0.1:1")

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, llm, search
import nv5_off
nv5_off.apply()


def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0] * 1024
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 1024] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        out.append([x / n for x in v])
    return out


def fake_rerank(query, texts):
    q = set(re.findall(r"\w+", query.lower()))
    return [len(q & set(re.findall(r"\w+", t.lower()))) * 3 - 4.0 for t in texts]


prompts = []


async def fake_fast(messages, schema):
    prompts.append(messages[0]["content"] + messages[-1]["content"])
    d = {"plan": "", "answer": "Theo dữ liệu, giá là 55.000đ [1].", "ask_back": False, "choices": [], "sources": [1]}
    if "sources" not in schema["properties"]:
        d = {k: v for k, v in d.items() if k != "sources"}
    raw = json.dumps(d)
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


search.embed, search.rerank = fake_embed, fake_rerank
llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}

CSV = "Tên sản phẩm,Giá,Mô tả\nPhở bò tái,55.000đ,Phở bò Hà Nội nước dùng hầm xương\nBánh mì thịt,25.000đ,Bánh mì kẹp thịt nướng\n".encode()
Q = "phở bò tái giá bao nhiêu"

with TestClient(main.app) as c:
    tok = {}

    def as_(name):
        c.cookies.clear()
        c.cookies.set(auth.COOKIE, tok[name])
        return c

    tok["boss"] = c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE)
    tok["dan"] = c.post("/s4/auth/signup", json={"username": "dan", "password": "123456"}).cookies.get(auth.COOKIE)
    as_("boss")
    assert c.post("/s4/admin/users", json={"username": "canbo", "password": "123456", "role": "can_bo"}).status_code == 200
    tok["canbo"] = c.post("/s4/auth/login", json={"username": "canbo", "password": "123456"}).cookies.get(auth.COOKIE)

    def doms(name):
        return {d["name"]: d for d in as_(name).get("/s4/domains").json()["domains"]}

    def chat(name, text, did=None):
        as_(name)
        r = c.post("/s4/chat", json={"text": text, **({"domain_id": did} if did else {})})
        return r

    def wait_ready(name, did):
        as_(name)
        for _ in range(80):
            lst = c.get(f"/s4/datasets?domain_id={did}").json()["datasets"]
            if lst and all(d["status"] in ("ready", "error") for d in lst):
                return lst
            time.sleep(0.25)
        raise AssertionError("dataset chưa xử lý xong")

    # --- có sẵn 2 domain
    d = doms("dan")
    assert d["Thủ tục"]["kind"] == "hard" and d["Thủ tục"]["engine"] == "strict" and d["Trò chuyện chung"]["kind"] == "soft", d
    # --- chỉ dev thêm domain cứng; user thêm được domain mềm riêng
    as_("dan")
    assert c.post("/s4/domains", json={"name": "Du lịch", "kind": "hard"}).status_code == 403
    mine = c.post("/s4/domains", json={"name": "Sách của tôi", "guardrail": "Trả lời ngắn."}).json()["domain"]
    assert mine["kind"] == "soft" and mine["mine"] and mine["can_delete"] and mine["guardrail"] == "Trả lời ngắn."
    assert "Sách của tôi" not in doms("boss") and "Sách của tôi" in doms("dan")    # domain mềm của user: riêng của họ
    as_("boss")
    hard = c.post("/s4/domains", json={"name": "Du lịch", "kind": "hard", "guardrail": "Luôn xưng là em."}).json()["domain"]
    assert hard["kind"] == "hard" and not hard["can_delete"]
    # --- dataset của domain cứng: dev tải, người dân dùng nhưng không tải được
    r = c.post("/s4/datasets", files={"file": ("menu.csv", io.BytesIO(CSV), "text/csv")}, data={"domain_id": str(hard["id"])})
    assert r.status_code == 200, r.text
    ds_id = r.json()["dataset"]["id"]
    assert wait_ready("boss", hard["id"])[0]["status"] == "ready"
    as_("dan")
    assert c.post("/s4/datasets", files={"file": ("x.csv", io.BytesIO(CSV), "text/csv")}, data={"domain_id": str(hard["id"])}).status_code == 403
    lst = c.get(f"/s4/datasets?domain_id={hard['id']}").json()
    assert [x["id"] for x in lst["datasets"]] == [ds_id] and not lst["can_upload"], lst
    assert c.get("/s4/datasets?domain_id=2").json()["datasets"] == []             # dataset không hiện ở domain khác
    assert c.get(f"/s4/datasets/{ds_id}/records").status_code == 200              # đọc được bản ghi để xem nguồn
    # --- hỏi trong domain: có bằng chứng + guardrail của domain; ở domain khác thì không
    prompts.clear()
    r = chat("dan", Q, hard["id"])
    assert r.status_code == 200 and "Phở bò tái" in prompts[-1] and "Luôn xưng là em" in prompts[-1], prompts[-1][-600:]
    assert '"specialist": true' in r.text.replace('":true', '": true') or "specialist" in r.text
    prompts.clear()
    chat("dan", Q, 2)
    assert "Phở bò tái" not in prompts[-1] and "Luôn xưng là em" not in prompts[-1]
    # --- hội thoại nhớ domain của nó
    as_("dan")
    convs = c.get("/s4/conversations").json()["conversations"]
    assert {x["domain_id"] for x in convs if x["mode"] == "friendly"} == {hard["id"], 2}, convs
    # --- khoá dataset: người dân không thấy, cán bộ vẫn thấy
    as_("boss")
    assert c.patch(f"/s4/datasets/{ds_id}", json={"locked": True}).status_code == 200
    as_("dan")
    assert c.patch(f"/s4/datasets/{ds_id}", json={"locked": False}).status_code in (403, 404)
    assert c.get(f"/s4/datasets?domain_id={hard['id']}").json()["datasets"] == []
    assert c.get(f"/s4/datasets/{ds_id}/records").status_code == 404
    prompts.clear(); chat("dan", Q, hard["id"])
    assert "Phở bò tái" not in prompts[-1]
    assert len(as_("canbo").get(f"/s4/datasets?domain_id={hard['id']}").json()["datasets"]) == 1
    prompts.clear(); chat("canbo", Q, hard["id"])
    assert "Phở bò tái" in prompts[-1]
    # --- khoá domain: người dân không thấy / không dùng; cán bộ dùng được
    as_("boss")
    assert c.patch(f"/s4/domains/{hard['id']}", json={"locked": True}).status_code == 200
    assert "Du lịch" not in doms("dan") and "Du lịch" in doms("canbo")
    assert chat("dan", "xin chào", hard["id"]).status_code == 403
    assert chat("canbo", "xin chào", hard["id"]).status_code == 200
    as_("dan")
    assert all(x["domain_id"] != hard["id"] for x in c.get("/s4/conversations").json()["conversations"])   # hội thoại cũ trong domain khoá bị ẩn
    assert c.patch(f"/s4/domains/{hard['id']}", json={"locked": False}).status_code in (403, 404)
    # --- domain Thủ tục (Strict) cũng khoá được
    as_("boss")
    assert c.patch("/s4/domains/1", json={"locked": True}).status_code == 200
    as_("dan")
    assert c.post("/s4/strict/chat", json={"text": "khai báo tạm vắng cần giấy tờ gì"}).status_code == 403
    assert c.post("/chat", json={"text": "khai báo tạm vắng cần giấy tờ gì"}).status_code == 403
    assert as_("canbo").post("/s4/strict/chat", json={"text": "khai báo tạm vắng cần giấy tờ gì"}).status_code == 200
    as_("boss")
    c.patch("/s4/domains/1", json={"locked": False})
    assert c.patch("/s4/domains/1", json={"kind": "soft"}).status_code == 422                # Thủ tục luôn là domain cứng
    # --- không xoá được domain cứng / domain có sẵn; chuyển mềm <-> cứng
    assert c.delete(f"/s4/domains/{hard['id']}").status_code == 403
    assert c.delete("/s4/domains/2").status_code == 403 and c.delete("/s4/domains/1").status_code == 403
    as_("dan")
    r = c.post("/s4/datasets", files={"file": ("riêng.csv", io.BytesIO(CSV), "text/csv")}, data={"domain_id": "2"})   # domain 2 cho user tải
    assert r.status_code == 200, r.text
    wait_ready("dan", 2)
    as_("boss")
    r = c.patch("/s4/domains/2", json={"kind": "hard"})
    assert r.status_code == 422 and "riêng" in r.text, r.text                                  # dataset riêng không được thành dùng chung
    assert c.patch(f"/s4/domains/{hard['id']}", json={"kind": "soft"}).status_code == 200      # cứng -> mềm
    assert c.patch(f"/s4/domains/{hard['id']}", json={"kind": "hard"}).status_code == 200      # mềm -> cứng (chỉ có dữ liệu của dev)
    # --- user chỉ xoá được domain mềm của mình (kèm dữ liệu); hội thoại về Trò chuyện chung
    as_("dan")
    assert c.delete(f"/s4/domains/{mine['id']}").status_code == 200 and "Sách của tôi" not in doms("dan")
    # --- ghim
    as_("dan")
    assert doms("dan")["Thủ tục"]["pinned"]
    assert not c.post("/s4/domains/1/pin", json={"pinned": False}).json()["domains"][0]["pinned"]
print("OK test_domains")

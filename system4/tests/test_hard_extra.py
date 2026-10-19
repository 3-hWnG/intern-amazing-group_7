"""Lĩnh vực cứng dùng THÊM bộ dữ liệu tải lên bên cạnh dữ liệu cào / đồng bộ (leader 19/10/2026):
- ABI: dev / cán bộ tải thêm tệp; tệp được tìm chung với phiên bản đang dùng; chuyển phiên bản không tắt tệp tải thêm.
- Thủ tục: công tắc data_mode "s3" (chỉ System 3, mặc định) | "s4" (chỉ System 4 trên tệp tải lên); hai chế độ loại trừ nhau.
Model giả (embedding, reranker, LLM): không cần Ollama. Chạy: python run_server.py system4/tests/test_hard_extra.py"""
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
from system3.system4.server import auth, db, llm, search
from system3.system4.abi import index as abi_index
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


CSV = "Tên sản phẩm,Giá,Mô tả\nPhở bò tái,55.000đ,Phở bò Hà Nội nước dùng hầm xương\nBánh mì thịt,25.000đ,Bánh mì kẹp thịt nướng\n".encode()
Q = "phở bò tái giá bao nhiêu"

search.embed, search.rerank = fake_embed, fake_rerank
llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}

with TestClient(main.app) as c:
    tok = {}

    def as_(name):
        c.cookies.clear()
        c.cookies.set(auth.COOKIE, tok[name])
        return c

    tok["boss"] = c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE)
    tok["dan"] = c.post("/s4/auth/signup", json={"username": "dan", "password": "123456"}).cookies.get(auth.COOKIE)

    def doms(name):
        return {d["engine"]: d for d in as_(name).get("/s4/domains").json()["domains"]}

    def upload(name, did, fname="menu.csv"):
        return as_(name).post("/s4/datasets", files={"file": (fname, io.BytesIO(CSV), "text/csv")}, data={"domain_id": str(did)})

    def wait_ready(did):
        for _ in range(80):
            lst = as_("boss").get(f"/s4/datasets?domain_id={did}&uploaded=1").json()["datasets"]
            if lst and all(d["status"] in ("ready", "error") for d in lst):
                return lst
            time.sleep(0.25)
        raise AssertionError("dataset chưa xử lý xong")

    # ================================================================ ABI: tải thêm tệp
    abi = doms("dan")["abi"]
    assert not abi["can_upload"], abi                                                       # người dân không tải
    assert upload("dan", abi["id"]).status_code == 403
    assert doms("boss")["abi"]["can_upload"]
    r = upload("boss", abi["id"])
    assert r.status_code == 200, r.text
    extra_id = r.json()["dataset"]["id"]
    assert wait_ready(abi["id"])[0]["status"] == "ready"
    # một bộ dữ liệu "đồng bộ" giả của phiên bản 1 (như index.build tạo) để kiểm việc bật / tắt theo phiên bản
    boss_id = db.user_by_name("boss")["id"]
    sync_id = db.run("INSERT INTO datasets(user_id,name,filename,size_bytes,kind,status,progress,message,mapping,n_records,active,domain_id) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (boss_id, "abi.com.vn · phiên bản 1", "abi.com.vn", 0, "text", "ready", 100, "",
                                                         json.dumps({"kind": "text", "source": "abi_sync", "abi_version": 1}), 0, 1, abi["id"]))
    abi_index.set_active(None)                                                             # tắt mọi phiên bản…
    act = {d["id"] for d in db.active_datasets(boss_id, abi["id"], "dev")}
    assert extra_id in act and sync_id not in act, act                                     # …tệp tải thêm vẫn bật
    abi_index.set_active(1)
    act = {d["id"] for d in db.active_datasets(db.user_by_name("dan")["id"], abi["id"], "user")}
    assert act == {extra_id, sync_id}, act                                                 # người dân dùng cả hai (dùng chung)
    lst = as_("boss").get(f"/s4/datasets?domain_id={abi['id']}&uploaded=1").json()["datasets"]
    assert [d["id"] for d in lst] == [extra_id], lst                                       # thẻ "Dữ liệu tải thêm": không có bản đồng bộ
    assert {d["id"] for d in c.get(f"/s4/datasets?domain_id={abi['id']}").json()["datasets"]} == {extra_id, sync_id}
    db.run("DELETE FROM datasets WHERE id=?", (sync_id,))
    # hỏi trong lĩnh vực ABI: đoạn của tệp tải thêm có trong bằng chứng gửi AI (chưa đồng bộ abi.com.vn thì trả lời "chưa đồng bộ")
    from system3.system4.abi import store as abi_store
    abi_store.data = lambda: {"synced_at": "2026-10-19T08:00:00+07:00", "center": {"name": "Trung tâm Ươm tạo"}, "catalog": []}
    prompts.clear()
    r = as_("dan").post("/s4/chat", json={"text": Q, "domain_id": abi["id"]})
    assert r.status_code == 200 and prompts and "Phở bò tái" in prompts[-1], (r.text[-400:], prompts[-1:])

    # ================================================================ Thủ tục: System 3 hoặc System 4
    th = doms("boss")["strict"]
    assert th["data_mode"] == "s3" and "profile" not in th and th["can_upload"], th
    assert not doms("dan")["strict"]["can_upload"]
    assert as_("dan").post("/s4/chat", json={"text": Q, "domain_id": 1}).status_code == 409   # chế độ System 3: không có hội thoại Friendly
    r = upload("boss", 1, "thu_tuc_them.csv")
    assert r.status_code == 200, r.text
    assert wait_ready(1)[0]["status"] == "ready"
    assert as_("dan").patch("/s4/domains/1", json={"data_mode": "s4"}).status_code == 403          # chỉ dev / cán bộ
    assert as_("boss").patch("/s4/domains/2", json={"data_mode": "s4"}).status_code == 422          # chỉ lĩnh vực Thủ tục
    assert c.patch("/s4/domains/1", json={"data_mode": "x"}).status_code == 422
    assert c.patch("/s4/domains/1", json={"profile": {"clarify": False}}).status_code == 422       # System 3 không dùng hồ sơ
    r = c.patch("/s4/domains/1", json={"data_mode": "s4", "profile": {"clarify": False}})
    assert r.status_code == 200, r.text
    th = r.json()["domain"]
    assert th["data_mode"] == "s4" and th["profile"]["clarify"] is False and th["profile"]["answer_mode"] == "grounded", th
    # System 3 tắt: cả cầu nối Strict lẫn /chat gốc của System 3 đều từ chối
    assert as_("dan").post("/s4/strict/chat", json={"text": "làm căn cước"}).status_code == 409
    assert c.post("/chat", json={"text": "làm căn cước"}).status_code == 409
    # hội thoại Friendly trong Thủ tục: trả lời từ tệp tải lên + guardrail / hồ sơ của lĩnh vực
    prompts.clear()
    r = c.post("/s4/chat", json={"text": Q, "domain_id": 1})
    assert r.status_code == 200 and "Phở bò tái" in prompts[-1], (r.text[-400:], prompts[-1:])
    cid = next(x["id"] for x in c.get("/s4/conversations").json()["conversations"] if x.get("mode") == "friendly")
    assert db.get_conversation(cid)["domain_id"] == 1
    # quay lại System 3: hội thoại Friendly của Thủ tục không gửi tiếp được, Strict chạy lại
    assert as_("boss").patch("/s4/domains/1", json={"data_mode": "s3"}).json()["domain"]["data_mode"] == "s3"
    assert as_("dan").post("/s4/chat", json={"text": Q, "conversation_id": cid}).status_code == 409
    assert c.post("/s4/strict/chat", json={"text": "làm căn cước"}).status_code != 409
print("OK test_hard_extra")

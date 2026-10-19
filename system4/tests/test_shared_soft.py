"""Dataset DÙNG CHUNG trong lĩnh vực mềm (19/10/2026): dev / cán bộ tải vào lĩnh vực mềm không riêng ai và đặt "dùng chung"
-> mọi người dùng được lĩnh vực đều thấy, hỏi được (chỉ đọc). Mặc định vẫn là riêng. Lĩnh vực mềm riêng của một người: không chia sẻ.
Model giả (embedding, reranker, LLM). Chạy: python run_server.py system4/tests/test_shared_soft.py"""
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


prompts = []


async def fake_fast(messages, schema):
    prompts.append(messages[0]["content"] + messages[-1]["content"])
    d = {"plan": "", "answer": "Theo dữ liệu [1].", "ask_back": False, "choices": [], "sources": [1]}
    if "sources" not in schema["properties"]:
        d = {k: v for k, v in d.items() if k != "sources"}
    raw = json.dumps(d)
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


search.embed = fake_embed
search.rerank = lambda q, ts: [len(set(re.findall(r"\w+", q.lower())) & set(re.findall(r"\w+", t.lower()))) * 3 - 4.0 for t in ts]
llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
CSV = "Tên bệnh viện,Số giường,Tuyến\nBệnh viện Chợ Rẫy,1800,Trung ương\nBệnh viện Nhân dân Gia Định,1500,Tỉnh\n".encode()
Q = "Bệnh viện Chợ Rẫy có bao nhiêu giường"

with TestClient(main.app) as c:
    tok = {}

    def as_(name):
        c.cookies.clear()
        c.cookies.set(auth.COOKIE, tok[name])
        return c

    for n in ("boss", "dan", "mai"):
        tok[n] = c.post("/s4/auth/signup", json={"username": n, "password": "123456"}).cookies.get(auth.COOKIE)

    def ready(ds_id):
        for _ in range(80):
            if db.get_dataset(ds_id)["status"] in ("ready", "error"):
                return db.get_dataset(ds_id)
            time.sleep(0.25)
        raise AssertionError("chưa nạp xong")

    def up(name, did, shared=None, fname="bv.csv"):
        return as_(name).post("/s4/datasets", files={"file": (fname, io.BytesIO(CSV), "text/csv")},
                              data={"domain_id": str(did), **({"shared": shared} if shared else {})})

    yte = as_("boss").post("/s4/domains", json={"name": "Y tế"}).json()["domain"]          # lĩnh vực mềm của dev: không riêng ai
    assert yte["kind"] == "soft" and yte["can_share"], yte
    dan_view = next(d for d in as_("dan").get("/s4/domains").json()["domains"] if d["id"] == yte["id"])
    assert not dan_view["can_share"]
    # --- tải lên là dùng chung luôn (seed script) / tải thường thì riêng
    shared_id = up("boss", yte["id"], "1").json()["dataset"]["id"]
    private_id = up("boss", yte["id"], None, "rieng.csv").json()["dataset"]["id"]
    assert ready(shared_id)["shared"] == 1 and ready(private_id)["shared"] == 0
    lst = as_("dan").get(f"/s4/datasets?domain_id={yte['id']}").json()["datasets"]
    assert [d["id"] for d in lst] == [shared_id] and lst[0]["shared"], lst                # người dân chỉ thấy bộ dùng chung
    assert {d["id"] for d in db.active_datasets(db.user_by_name("dan")["id"], yte["id"], "user")} == {shared_id}
    assert c.get(f"/s4/datasets/{shared_id}/records").status_code == 200                # đọc được để xem nguồn
    assert c.get(f"/s4/datasets/{private_id}/records").status_code == 404
    assert c.patch(f"/s4/datasets/{shared_id}", json={"active": False}).status_code == 404   # không phải của mình: không đổi được
    assert c.delete(f"/s4/datasets/{shared_id}").status_code == 404
    prompts.clear()
    r = c.post("/s4/chat", json={"text": Q, "domain_id": yte["id"]})
    assert r.status_code == 200 and ("Chợ Rẫy" in "".join(prompts) or "1800" in r.text), r.text[-400:]
    # --- dev thôi dùng chung -> người dân không thấy nữa; cán bộ / dev đặt được, người dân thì không
    assert as_("boss").patch(f"/s4/datasets/{shared_id}", json={"shared": False}).status_code == 200
    assert as_("dan").get(f"/s4/datasets?domain_id={yte['id']}").json()["datasets"] == []
    assert as_("boss").patch(f"/s4/datasets/{shared_id}", json={"shared": True}).status_code == 200
    # --- lĩnh vực mềm riêng của một người dân: dataset của họ không chia sẻ được, người khác không thấy
    mine = as_("dan").post("/s4/domains", json={"name": "Sổ tay"}).json()["domain"]
    assert not mine["can_share"]
    # dataset bị đặt cờ shared ở lĩnh vực RIÊNG (cố tình ghi thẳng DB) vẫn không lộ ra: luật đòi lĩnh vực không riêng ai
    did = db.create_dataset(db.user_by_name("dan")["id"], "so", "so.csv", 10, mine["id"])
    db.update_dataset(did, shared=1, status="ready")
    assert as_("mai").get(f"/s4/datasets/{did}/records").status_code == 404
    assert as_("dan").patch(f"/s4/datasets/{did}", json={"shared": True}).status_code == 403   # người dân không đặt được
    # --- khoá dataset dùng chung: người dân không thấy, cán bộ / dev vẫn thấy
    db.update_dataset(shared_id, locked=1)
    assert as_("dan").get(f"/s4/datasets?domain_id={yte['id']}").json()["datasets"] == []
    assert any(d["id"] == shared_id for d in as_("boss").get(f"/s4/datasets?domain_id={yte['id']}").json()["datasets"])
print("OK test_shared_soft")

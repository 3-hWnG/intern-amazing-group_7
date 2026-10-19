"""Máy mới: có tài khoản dev là server tự nạp dữ liệu thật (system4/eval/real_domains/data) + bản chụp FLM, MỘT lần (server/bootstrap.py).
Model giả (embedding). Chạy: python run_server.py system4/tests/bootstrap_test.py"""
import hashlib
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
from system3.system4.server import auth, bootstrap, datasets, db, llm, search
from system3.system4.flm import store as flm_store
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


search.embed = fake_embed
llm.chat_json = lambda *a, **k: {}

with TestClient(main.app) as c:
    assert bootstrap.run_once() == {} and bootstrap.done() == {}                       # chưa có dev: chưa làm gì
    tok = c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE)
    out = bootstrap.run_once()
    assert len(out["real_domains"]) == 6 and out["flm_snapshot"]["ok"] and out["flm_snapshot"]["version"] == 1, out
    names = {d["name"] for d in db.run("SELECT name FROM domains WHERE kind='soft'", many=True)}
    assert {"Y tế", "Giáo dục", "Du lịch"} <= names, names
    for _ in range(600):
        rows = [db.get_dataset(i) for i in out["real_domains"]]
        if all(r["status"] in ("ready", "error") for r in rows):
            break
        time.sleep(0.5)
    assert all(r["status"] == "ready" and r["shared"] == 1 for r in rows), [(r["name"], r["status"], r["message"]) for r in rows]
    v = flm_store.versions()[0]
    assert flm_store.active_id() == 1 and v["synced_at"].startswith("2026-10-19") and v["counts"]["Môn học"] == 73, v
    assert db.get_dataset(v["dataset_id"])["status"] == "ready" and db.get_dataset(v["dataset_id"])["active"]
    # người dân mới đăng ký thấy ngay dữ liệu dùng chung
    c.cookies.clear()
    c.cookies.set(auth.COOKIE, c.post("/s4/auth/signup", json={"username": "dan", "password": "123456"}).cookies.get(auth.COOKIE))
    yte = next(d for d in c.get("/s4/domains").json()["domains"] if d["name"] == "Y tế")
    assert len(c.get(f"/s4/datasets?domain_id={yte['id']}").json()["datasets"]) == 2
    # chỉ một lần: lần sau không làm gì; dev xoá một bộ thì nó không tự quay về
    datasets.delete(rows[0])
    assert bootstrap.run_once() == {} and db.get_dataset(rows[0]["id"]) is None
    assert set(bootstrap.done()) == {"real_domains", "flm_snapshot"}
print("OK bootstrap_test")

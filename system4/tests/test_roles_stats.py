"""3 loại tài khoản (dev / can_bo / user) và thống kê thủ tục. Chạy: python run_server.py system4/tests/test_roles_stats.py"""
import os, sys, tempfile
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth

with TestClient(main.app) as c:
    c.cookies.set(auth.COOKIE, c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE))
    assert c.get("/s4/public").json()["user"]["role"] == "dev"
    r = c.post("/s4/admin/users", json={"username": "canbo1", "password": "123456", "role": "can_bo"})
    assert r.status_code == 200 and {u["username"]: u["role"] for u in r.json()["users"]}["canbo1"] == "can_bo", r.text
    assert c.post("/s4/admin/users", json={"username": "x1234", "password": "123456", "role": "root"}).status_code == 422
    uid = next(u["id"] for u in r.json()["users"] if u["username"] == "canbo1")
    assert c.patch(f"/s4/admin/users/{uid}", json={"role": "user"}).status_code == 200
    assert c.patch(f"/s4/admin/users/{uid}", json={"role": "admin"}).status_code == 422
    assert c.get("/s4/admin/stats").json()["procedures"] == []
    for q in ("thông báo lưu trú mất bao lâu thì xong", "thông báo lưu trú mất bao lâu thì xong", "khai báo tạm vắng cần giấy tờ gì"):
        c.post("/s4/strict/chat", json={"text": q})
    st = c.get("/s4/admin/stats").json()
    assert st["procedures"] and st["procedures"][0]["n"] >= 2, st
    assert st["roles"]["dev"] == 1 and st["roles"]["user"] == 1 and st["feedback"]["friendly"] == {"up": 0, "down": 0}, st
    fb = c.get("/s4/admin/feedback").json()
    assert fb["count"] == 0 and fb["items"] == []
    # người không phải dev không xem được thống kê
    c.cookies.clear()
    tok = c.post("/s4/auth/signup", json={"username": "dan", "password": "123456"}).cookies.get(auth.COOKIE)
    c.cookies.set(auth.COOKIE, tok)
    assert c.get("/s4/admin/stats").status_code == 403
print("OK test_roles_stats")

"""G1.2 (P02/F2): khi bật System 4, hồ sơ Strict (/memory*, bộ nhớ của /chat) khoá theo TÀI KHOẢN đăng nhập, không theo header
X-Client-Id hay 'default'. Hai tài khoản không thấy, không sửa, không xoá được hồ sơ của nhau.
Chạy: python run_server.py system4/tests/memory_accounts_test.py"""
import os, sys, tempfile
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
import user_memory
from system3.system4.server import auth

with TestClient(main.app) as c:
    tok = {}
    for name in ("alice", "bob"):
        c.cookies.clear()
        tok[name] = c.post("/s4/auth/signup", json={"username": name, "password": "123456"}).cookies.get(auth.COOKIE)

    def as_user(n):
        c.cookies.clear()
        c.cookies.set(auth.COOKIE, tok[n])

    as_user("alice")
    a = c.put("/memory/profile", json={"province": "Hà Nội", "note": "ghi chú của alice"}).json()
    a_cid = a["client_id"]
    assert a_cid.startswith("u") and a_cid != "default", a_cid
    assert a["profile"]["note"] == "ghi chú của alice"

    as_user("bob")
    b = c.get("/memory").json()
    assert b["client_id"] != a_cid and b["profile"]["note"] == "", b["profile"]
    # header tự khai bị bỏ qua khi đã đăng nhập: bob không đọc/xoá được hồ sơ alice bằng X-Client-Id của alice
    assert c.get("/memory", headers={"X-Client-Id": a_cid}).json()["profile"]["note"] == ""
    assert c.get("/memory", headers={"X-Client-Id": "default"}).json()["client_id"] == b["client_id"]
    c.delete("/memory", headers={"X-Client-Id": a_cid})
    c.delete("/memory")
    c.put("/memory/profile", json={"note": "của bob"}, headers={"X-Client-Id": a_cid})

    as_user("alice")
    a2 = c.get("/memory").json()
    assert a2["profile"]["note"] == "ghi chú của alice" and a2["profile"]["province"] == "Hà Nội", a2["profile"]
    # bộ nhớ dùng cho policy của /chat cũng theo tài khoản
    assert user_memory.snapshot(a_cid)["profile"]["note"] == "ghi chú của alice"
    assert user_memory.snapshot("default")["profile"]["note"] == "", "không còn ghi vào hồ sơ chung 'default'"
    r = c.post("/s4/strict/chat", json={"text": "Đăng ký khai sinh cần giấy tờ gì?"})
    assert r.status_code == 200, r.text

    # chưa đăng nhập: /memory bị chặn
    c.cookies.clear()
    assert c.get("/memory").status_code == 401
print("OK memory_accounts_test")

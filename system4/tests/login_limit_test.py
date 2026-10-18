"""G1.5 (P25): 5 lần đăng nhập sai trong 10 phút theo (tên, IP) -> 429 kèm thời gian chờ; đúng mật khẩu cũng bị chặn trong lúc khoá;
tên khác / hết cửa sổ thì thử lại được; đăng nhập đúng xoá bộ đếm. Đăng ký không đổi.
Chạy: python run_server.py system4/tests/login_limit_test.py"""
import os, sys, tempfile, time
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth

with TestClient(main.app) as c:
    for n in ("boss", "dan"):
        c.cookies.clear()
        assert c.post("/s4/auth/signup", json={"username": n, "password": "123456"}).status_code == 200
    c.cookies.clear()
    # đăng nhập đúng xoá bộ đếm
    for _ in range(4):
        assert c.post("/s4/auth/login", json={"username": "dan", "password": "sai"}).status_code == 401
    assert c.post("/s4/auth/login", json={"username": "dan", "password": "123456"}).status_code == 200
    c.cookies.clear()
    for _ in range(4):
        assert c.post("/s4/auth/login", json={"username": "dan", "password": "sai"}).status_code == 401
    # lần sai thứ 5 vẫn là 401; từ lần 6 là 429, kể cả mật khẩu đúng
    assert c.post("/s4/auth/login", json={"username": "Dan", "password": "sai"}).status_code == 401
    r = c.post("/s4/auth/login", json={"username": "dan", "password": "123456"})
    assert r.status_code == 429 and "Thử lại sau" in r.json()["detail"] and 0 < int(r.headers["retry-after"]) <= 601, (r.status_code, r.text)
    # tên khác không bị ảnh hưởng; đăng ký không bị giới hạn
    assert c.post("/s4/auth/login", json={"username": "boss", "password": "123456"}).status_code == 200
    c.cookies.clear()
    assert c.post("/s4/auth/signup", json={"username": "moi1", "password": "123456"}).status_code == 200
    # hết cửa sổ 10 phút: thử lại được
    now = time.time()
    assert auth.login_wait("dan", "testclient", now) > 0
    assert auth.login_wait("dan", "testclient", now + auth.LOGIN_WINDOW + 1) == 0
print("OK login_limit_test")

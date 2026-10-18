"""Bảng điều khiển lĩnh vực (hộp "Lĩnh vực", dashboard.js): quyền theo vai trò sau khi dời dữ liệu / thống kê khỏi trang Quản trị.
  dev + cán bộ: dữ liệu Strict (phiên bản, nháp, cào, xuất), ABI (phiên bản, đồng bộ), dữ liệu mọi người dùng, thống kê, đường nhanh, sửa lĩnh vực.
  chỉ dev: tài khoản người dùng, Thử tìm kiếm, trang /s4/admin, ⚙ Cài đặt.     người dùng thường: không gì trong số trên.
DB thủ tục là BẢN SAO tạm (như test_nv4). Không cần mạng, không cần LLM.
Chạy (từ thư mục server/): set PYTHONPATH=<pyroot> && python ../system4/tests/test_dashboard.py"""
import os
import shutil
import sys
import tempfile

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
REPO = os.path.dirname(SERVER)
sys.path[:0] = [SERVER, os.path.join(REPO, "eval")]
TMP = tempfile.mkdtemp()
import fixture_db
DATA_COPY = os.path.join(TMP, "system3_data.db")
shutil.copy(os.environ.get("S3_DATA_DB") or str(fixture_db.ensure(quiet=True)), DATA_COPY)
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), S3_DATA_DB=DATA_COPY)

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, llm, search

search.embed = lambda texts: [[1.0] + [0.0] * 1023 for _ in texts]
llm.chat_json = lambda *a, **k: {}

with TestClient(main.app) as c:
    tok = {}
    c.cookies.clear()
    tok["dev"] = c.post("/s4/auth/signup", json={"username": "dev1", "password": "123456"}).cookies.get(auth.COOKIE)   # tài khoản đầu = dev
    c.cookies.set(auth.COOKIE, tok["dev"])
    for name, role in (("canbo", "can_bo"), ("dan", "user")):
        assert c.post("/s4/admin/users", json={"username": name, "password": "123456", "role": role}).status_code == 200
    for name in ("canbo", "dan"):
        c.cookies.clear()
        tok[name] = c.post("/s4/auth/login", json={"username": name, "password": "123456"}).cookies.get(auth.COOKIE)

    def as_user(n):
        c.cookies.clear(); c.cookies.set(auth.COOKIE, tok[n])

    DATA = ["/s4/admin/procs", "/s4/admin/procs/records?version=draft&limit=5", "/s4/admin/procs/job", "/s4/admin/stats",
            "/s4/admin/datasets", "/s4/admin/feedback", "/s4/abi/status"]
    DEV_ONLY = ["/s4/admin/users"]

    # ---- trang chính có bảng điều khiển; tệp tĩnh mới được phục vụ
    as_user("dan")
    html = c.get("/").text
    assert 'id="domain-modal" class="s4-modal dash"' in html and "dashboard.js" in html and 'id="dash-userview"' in html
    assert c.get("/s4/static/js/dashboard.js").status_code == 200 and c.get("/s4/static/css/dashboard.css").status_code == 200

    # ---- người dùng thường: không thấy dữ liệu / thống kê / tài khoản
    for u in DATA + DEV_ONLY:
        assert c.get(u).status_code == 403, u
    assert c.post("/s4/admin/searchlab", json={"query": "x"}).status_code == 403
    assert c.get("/s4/admin", follow_redirects=False).status_code == 303
    assert c.post("/s4/domains", json={"name": "Cứng của dân", "kind": "hard"}).status_code == 403

    # ---- cán bộ = dev ở bảng điều khiển
    as_user("canbo")
    for u in DATA:
        r = c.get(u)
        assert r.status_code == 200, (u, r.status_code, r.text[:200])
    assert c.get("/s4/admin/feedback.csv").status_code == 200
    r = c.post("/s4/domains", json={"name": "Du lịch chung", "kind": "hard"})
    assert r.status_code == 200, r.text
    did = r.json()["domain"]["id"]
    assert c.patch(f"/s4/domains/{did}", json={"locked": True, "profile": {"fast_path": False}}).status_code == 200
    doms = {d["id"]: d for d in c.get("/s4/domains").json()["domains"]}
    assert doms[did]["can_upload"] and doms[did]["can_edit"] and doms[did]["profile"]["fast_path"] is False
    # ... nhưng tài khoản / Thử tìm kiếm / trang Quản trị / ⚙ vẫn chỉ dev
    for u in DEV_ONLY:
        assert c.get(u).status_code == 403, u
    assert c.post("/s4/admin/searchlab", json={"query": "x"}).status_code == 403
    assert c.get("/s4/admin", follow_redirects=False).status_code == 303
    r = c.post("/s4/settings", json={"values": {"FASTPATH_ENABLED": False}})
    assert r.status_code == 403, (r.status_code, r.text[:200])

    # ---- dev: như trước + trang Quản trị chỉ còn tài khoản và Thử tìm kiếm
    as_user("dev")
    for u in DATA + DEV_ONLY:
        assert c.get(u).status_code == 200, u
    page = c.get("/s4/admin").text
    assert 'data-tab="users"' in page and 'data-tab="lab"' in page and 'data-tab="strict"' not in page and 'data-tab="stats"' not in page

print("test_dashboard: OK")

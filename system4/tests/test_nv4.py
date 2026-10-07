"""NV4: trang Quản trị (người dùng, dữ liệu Strict: phiên bản / nháp / chuẩn dữ liệu / so sánh / áp dụng / cào) và
tính năng kiểu ChatGPT cho Strict (phiên bản bằng cách phát lại).
DB thủ tục của System 3 dùng BẢN SAO tạm (S3_DATA_DB) để bước "Áp dụng" không đụng DB thật. Không cần mạng, không cần LLM.
Chạy (từ thư mục server/): set PYTHONPATH=<pyroot> && python ../system4/tests/test_nv4.py"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
REPO = os.path.dirname(SERVER)
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
DATA_COPY = os.path.join(TMP, "system3_data.db")
shutil.copy(os.path.join(REPO, "data", "runtime", "system3.db"), DATA_COPY)
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), S3_DATA_DB=DATA_COPY)

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, db, procs


def n_procs():
    c = sqlite3.connect(DATA_COPY)
    try:
        return c.execute("SELECT COUNT(*) FROM procedures").fetchone()[0]
    finally:
        c.close()


with TestClient(main.app) as c:
    tok = {}
    for name in ("boss", "anna", "binh"):
        c.cookies.clear()
        tok[name] = c.post("/s4/auth/signup", json={"username": name, "password": "123456"}).cookies.get(auth.COOKIE)

    def as_user(n):
        c.cookies.clear(); c.cookies.set(auth.COOKIE, tok[n])

    # ---------------- quyền: chỉ dev
    as_user("anna")
    assert c.get("/s4/admin/users").status_code == 403 and c.get("/s4/admin/procs").status_code == 403
    assert c.get("/s4/admin", headers={"accept": "text/html"}, follow_redirects=False).status_code == 303
    as_user("boss")
    assert c.get("/s4/admin", headers={"accept": "text/html"}).status_code == 200

    # ---------------- người dùng
    users = c.get("/s4/admin/users").json()["users"]
    assert [u["username"] for u in users] == ["boss", "anna", "binh"] and users[0]["role"] == "dev"
    assert c.post("/s4/admin/users", json={"username": "Anna", "password": "123456"}).status_code == 422, "trùng tên"
    r = c.post("/s4/admin/users", json={"username": "chi", "password": "abcdef", "role": "dev"})
    assert next(u for u in r.json()["users"] if u["username"] == "chi")["role"] == "dev"
    me_id = users[0]["id"]
    an_id = users[1]["id"]
    assert c.patch(f"/s4/admin/users/{me_id}", json={"role": "user"}).status_code == 422, "không tự hạ quyền"
    assert c.delete(f"/s4/admin/users/{me_id}").status_code == 422, "không tự xoá"
    assert c.patch(f"/s4/admin/users/{an_id}", json={"disabled": True}).status_code == 200
    as_user("anna")
    assert c.get("/s4/auth/me").status_code == 401, "khoá -> đăng xuất ngay"
    c.cookies.clear()
    assert c.post("/s4/auth/login", json={"username": "anna", "password": "123456"}).status_code == 403
    as_user("boss")
    c.patch(f"/s4/admin/users/{an_id}", json={"disabled": False, "password": "newpass1"})
    c.cookies.clear()
    tok["anna"] = c.post("/s4/auth/login", json={"username": "anna", "password": "newpass1"}).cookies.get(auth.COOKIE)
    assert tok["anna"], "mật khẩu mới dùng được"

    # ---------------- Strict: phiên bản (phát lại)
    as_user("anna")
    r = c.post("/s4/strict/chat", json={"text": "Đăng ký khai sinh cần giấy tờ gì?"})
    assert r.status_code == 200, r.text
    root = r.json()["conversation_id"]
    c.post("/s4/strict/chat", json={"text": "lệ phí bao nhiêu?", "root": root})
    p = c.get(f"/s4/strict/{root}/messages").json()["messages"]
    assert [m["role"] for m in p] == ["user", "assistant", "user", "assistant"] and all(m["node_id"] for m in p), p
    assert p[1]["blocks"], "câu trả lời Strict giữ nguyên dạng khối của System 3"
    a2 = p[3]["node_id"]
    r = c.post(f"/s4/strict/{root}/regenerate", json={"node_id": a2})
    assert r.status_code == 200, r.text
    p = r.json()["messages"]
    assert len(p[3]["versions"]) == 2 and r.json()["replayed"] == 1, (p[3]["versions"], r.json()["replayed"])
    r = c.post(f"/s4/strict/{root}/edit", json={"node_id": p[0]["node_id"], "text": "Đăng ký kết hôn cần giấy tờ gì?"})
    assert r.status_code == 200, r.text
    p = r.json()["messages"]
    assert p[0]["content"] == "Đăng ký kết hôn cần giấy tờ gì?" and len(p) == 2 and len(p[0]["versions"]) == 2
    assert "kết hôn" in json.dumps(p[1]["blocks"], ensure_ascii=False).lower(), p[1]["blocks"]
    back = c.post(f"/s4/strict/{root}/switch", json={"node_id": p[0]["versions"][0]}).json()["messages"]
    assert len(back) == 4 and back[0]["content"] == "Đăng ký khai sinh cần giấy tờ gì?", "về phiên bản cũ: đi tới tin mới nhất của nhánh"
    # tiếp tục trên nhánh cũ sau khi chuyển: hỏi tiếp dùng đúng ngữ cảnh nhánh đó
    c.post("/s4/strict/chat", json={"text": "làm ở đâu?", "root": root})
    assert len(c.get(f"/s4/strict/{root}/messages").json()["messages"]) == 6
    # nhánh ẩn không hiện trong danh sách
    listed = [x["id"] for x in c.get("/s4/conversations").json()["conversations"]]
    assert listed.count(root) == 1 and not set(db.strict_branches(root)) & set(listed), (listed, db.strict_branches(root))
    assert db.strict_branches(root), "sửa / tạo lại tạo nhánh"
    assert not set(db.strict_branches(root)) & {x["id"] for x in c.get("/conversations").json()["conversations"]}
    # chủ đề mới, 👍, xuất
    p = c.post(f"/s4/strict/{root}/reset").json()["messages"]
    assert p[-1]["content"].startswith("Đã bắt đầu chủ đề mới")
    assert c.post(f"/s4/strict/{root}/feedback", json={"node_id": p[1]["node_id"], "value": 1}).status_code == 200
    assert c.get(f"/s4/strict/{root}/messages").json()["messages"][1]["feedback"] == 1
    md = c.get(f"/s4/strict/{root}/export?format=md")
    assert md.status_code == 200 and "khai sinh" in md.text.lower()
    # tạo lại sau "chủ đề mới": phát lại cả lệnh chủ đề mới
    c.post("/s4/strict/chat", json={"text": "Tôi muốn đăng ký thường trú", "root": root})
    p = c.get(f"/s4/strict/{root}/messages").json()["messages"]
    r = c.post(f"/s4/strict/{root}/regenerate", json={"node_id": p[-1]["node_id"]})
    assert r.status_code == 200 and len(r.json()["messages"][-1]["versions"]) == 2, r.text
    # hỏi lại có thẻ lựa chọn: bấm lựa chọn (reply_to = nút thẻ cuối) rồi tạo lại -> phát lại kèm reply_to
    r = c.post("/s4/strict/chat", json={"text": "Tôi muốn xin trợ cấp hàng tháng"}).json()
    root2 = r["conversation_id"]
    p = c.get(f"/s4/strict/{root2}/messages").json()["messages"]
    assert p[-1]["clarify"], "câu mơ hồ -> System 3 hỏi lại"
    opt = p[-1]["clarify"]["options"][0]
    c.post("/s4/strict/chat", json={"text": opt, "root": root2, "reply_to": p[-1]["node_id"]})
    p = c.get(f"/s4/strict/{root2}/messages").json()["messages"]
    assert p[2]["replied"] is True and not p[-1]["clarify"], p[-1]
    r = c.post(f"/s4/strict/{root2}/regenerate", json={"node_id": p[-1]["node_id"]})
    assert r.status_code == 200 and not r.json()["messages"][-1]["clarify"], "phát lại giữ lựa chọn đã bấm"
    # người khác không đụng được
    as_user("binh")
    assert c.get(f"/s4/strict/{root}/messages").status_code == 404
    assert c.post(f"/s4/strict/{root}/regenerate", json={"node_id": p[-1]["node_id"]}).status_code == 404
    assert c.post("/s4/strict/chat", json={"text": "x", "root": root}).status_code == 404
    # hội thoại Strict cũ (tạo qua API System 3) được dựng cây khi mở
    as_user("anna")
    old = c.post("/chat", json={"text": "Đăng ký khai tử cần gì?"}).json()["conversation_id"]
    p = c.get(f"/s4/strict/{old}/messages").json()["messages"]
    assert [m["role"] for m in p] == ["user", "assistant"] and p[0]["node_id"]
    # xoá: cả nhánh ẩn
    branches = db.strict_branches(root)
    assert c.delete(f"/s4/strict/{root}").json()["ok"]
    assert not any(main.store.conversation_exists(x) for x in [root] + branches)

    # ---------------- Dữ liệu Strict: phiên bản, nháp, chuẩn dữ liệu, so sánh
    as_user("boss")
    st = c.get("/s4/admin/procs").json()
    assert len(st["versions"]) == 1 and st["versions"][0]["label"] == "Gốc" and st["versions"][0]["n_records"] == 1350
    v0 = st["active_id"]
    r = c.get("/s4/admin/procs/records?version=draft&q=khai sinh").json()
    assert r["total"] >= 1
    pid = r["records"][0]["proc_id"]
    rec = c.get(f"/s4/admin/procs/record/{pid}?version=draft").json()
    assert rec["profile"]["name"] == ["str"]
    good = dict(rec["record"]); good["name"] = good["name"] + " (ĐÃ SỬA THỬ)"
    bad1 = dict(good); bad1.pop("fees")
    bad2 = dict(good); bad2["fees"] = "miễn phí"
    bad3 = dict(good); bad3["proc_id"] = "9.999"
    for b, msg in ((bad1, "Thiếu trường"), (bad2, "phải là kiểu"), (bad3, "mã thủ tục")):
        rr = c.put(f"/s4/admin/procs/draft/{pid}", json={"record": b})
        assert rr.status_code == 422 and msg in rr.json()["detail"], rr.text
    assert c.put(f"/s4/admin/procs/draft/{pid}", json={"record": good}).status_code == 200
    gone = c.get("/s4/admin/procs/records?version=draft&q=khai tử").json()["records"][0]["proc_id"]
    assert c.delete(f"/s4/admin/procs/draft/{gone}").status_code == 200
    st = c.get("/s4/admin/procs").json()
    assert st["draft"]["changes"] == 2 and st["draft"]["deleted"] == 1
    d = c.get(f"/s4/admin/procs/diff?a={v0}&b=draft").json()
    assert d["counts"] == {"added": 0, "removed": 1, "changed": 1} and d["changed"][0]["fields"] == ["name"], d["counts"]
    fd = c.get(f"/s4/admin/procs/diff/{pid}?a={v0}&b=draft").json()["fields"][0]
    assert fd["new"].endswith("(ĐÃ SỬA THỬ)")
    as_user("anna")
    assert c.put(f"/s4/admin/procs/draft/{pid}", json={"record": good}).status_code == 403
    as_user("boss")
    r = c.post("/s4/admin/procs/draft/save", json={"label": "Thử sửa"}).json()
    v1 = r["version_id"]
    assert r["diff"] == {"added": 0, "removed": 1, "changed": 1}
    assert c.get("/s4/admin/procs").json()["draft"]["changes"] == 0
    assert c.delete(f"/s4/admin/procs/versions/{v0}").status_code == 422, "không xoá bản Gốc"

    # ---------------- Áp dụng (dựng DB thật bằng system3.data.build, trên bản sao)
    assert n_procs() == 1350
    procs.apply(v1, wait=True)
    assert n_procs() == 1349 and procs.active_id() == v1, procs.job()
    c2 = sqlite3.connect(DATA_COPY)
    assert c2.execute("SELECT name FROM procedures WHERE proc_id=?", (pid,)).fetchone()[0].endswith("(ĐÃ SỬA THỬ)")
    c2.close()
    as_user("anna")
    r = c.post("/s4/strict/chat", json={"text": "Đăng ký khai sinh cần giấy tờ gì?"})
    assert r.status_code == 200, "Strict vẫn chạy sau khi áp dụng phiên bản mới"
    import planner.planner as _pl
    names = {p["proc_id"]: p["name"] for p in _pl._index().procs}
    assert gone not in names and names[pid].endswith("(ĐÃ SỬA THỬ)"), "Planner System 3 dùng dữ liệu mới (chỉ mục được dựng lại)"
    as_user("boss")
    assert c.delete(f"/s4/admin/procs/versions/{v1}").status_code == 422, "không xoá bản đang dùng"
    procs.apply(v0, wait=True)   # quay lại bản Gốc
    assert n_procs() == 1350 and procs.active_id() == v0

    # ---------------- Cào (giả lập tiến trình cào: không dùng mạng)
    import subprocess as _sp
    real_run = procs.subprocess.run

    def fake_run(args, **kw):
        if "system3.system4.scraper.run" in args:
            status = Path(args[args.index("--status") + 1])
            staging = Path(TMP) / "staging.jsonl"
            recs, _ = procs.load(v0)
            new = [dict(x) for x in recs[:3]]
            new[0]["name"] = "Tên mới từ Cổng"
            new.append({**recs[3], "proc_id": "9.000001", "name": "Thủ tục mới hoàn toàn"})
            staging.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in new), encoding="utf-8")
            status.write_text(json.dumps({"step": "done", "message": "ok", "staging": str(staging)}), encoding="utf-8")
            return _sp.CompletedProcess(args, 0)
        return real_run(args, **kw)

    procs.subprocess.run = fake_run
    assert c.post("/s4/admin/procs/scrape", json={"limit": 3}).status_code == 200
    import time
    for _ in range(100):
        j = c.get("/s4/admin/procs/job").json()["job"]
        if j["state"] != "running":
            break
        time.sleep(0.1)
    procs.subprocess.run = real_run
    assert j["state"] == "done" and j["result"]["diff"] == {"added": 1, "removed": 1347, "changed": 1}, j
    assert any(v["source"] == "scrape" for v in c.get("/s4/admin/procs").json()["versions"])
    assert procs.active_id() == v0, "cào xong KHÔNG tự áp dụng"

    # ---------------- dữ liệu người dùng + xoá người dùng (kéo theo dữ liệu)
    assert c.get("/s4/admin/datasets").status_code == 200
    as_user("binh")
    r = c.post("/s4/strict/chat", json={"text": "Đăng ký khai sinh"})
    binh_conv = r.json()["conversation_id"]
    as_user("boss")
    binh = next(u for u in c.get("/s4/admin/users").json()["users"] if u["username"] == "binh")
    assert binh["strict_chats"] == 1
    assert c.delete(f"/s4/admin/users/{binh['id']}").status_code == 200
    assert not main.store.conversation_exists(binh_conv) and not db.user_by_name("binh")

print("OK test_nv4")

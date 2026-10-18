"""G1.4 (P04, D13) + G1.7 (D12): ô "Tài khoản & quyền riêng tư" và hạn mức dung lượng gồm cả hội thoại.
- đổi mật khẩu (cần mật khẩu cũ), xoá hết hội thoại, xoá bộ nhớ, xem dung lượng
- xoá tài khoản (nhập lại mật khẩu; không xoá được dev cuối cùng): mọi thứ của người đó biến mất ở cả hai DB,
  chỉ còn các dòng feedback_log đã bỏ danh tính (user_id=0, conversation_id='') và đã che số
- vượt USER_QUOTA_MB thì /s4/chat và /s4/strict/chat bị từ chối; xoá bớt thì dùng lại được; dev không giới hạn
Chạy: python run_server.py system4/tests/account_test.py"""
import json, os, sqlite3, sys, tempfile
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, db, llm, settings

PHONE = "0912345678"


async def fake_fast(messages, schema):
    raw = json.dumps({"plan": "", "answer": "Dạ, mình đã ghi nhận.", "ask_back": False, "choices": []})
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
S3 = os.environ["S3_DB_PATH"]
S4 = os.path.join(TMP, "s4", "system4.db")


def q(path, sql, *a):
    c = sqlite3.connect(path)
    try:
        return c.execute(sql, a).fetchall()
    finally:
        c.close()


with TestClient(main.app) as c:
    tok = {}
    for name in ("boss", "dan"):
        c.cookies.clear()
        tok[name] = c.post("/s4/auth/signup", json={"username": name, "password": "123456"}).cookies.get(auth.COOKIE)

    def as_user(n):
        c.cookies.clear()
        c.cookies.set(auth.COOKIE, tok[n])

    # ---------------- dan dùng hệ thống: Strict + Friendly + 👍/👎 + bộ nhớ hai bên
    as_user("dan")
    dan_id = c.get("/s4/auth/me").json()["user"]["id"]
    r = c.post("/s4/strict/chat", json={"text": f"sđt {PHONE}, đăng ký khai sinh cần giấy tờ gì?"})
    assert r.status_code == 200, r.text
    root, node = r.json()["conversation_id"], r.json()["message_id"]
    assert c.post(f"/s4/strict/{root}/feedback", json={"node_id": node, "value": 1}).status_code == 200
    assert c.post("/s4/chat", json={"text": "Xin chào, cho mình hỏi về Python"}).status_code == 200
    fr = c.get("/s4/conversations").json()["conversations"]
    fid = next(x["id"] for x in fr if x.get("mode") == "friendly")
    am = next(m for m in c.get(f"/s4/conversations/{fid}/messages").json()["messages"] if m["role"] == "assistant")
    assert c.post(f"/s4/conversations/{fid}/messages/{am['id']}/feedback", json={"value": -1}).status_code == 200
    db.add_memory(dan_id, "Người dùng sống ở Đà Nẵng", 50)
    assert c.put("/memory/profile", json={"note": "ghi chú của dan"}).status_code == 200

    # ---------------- ô tài khoản: dung lượng gồm cả hội thoại
    info = c.get("/s4/account").json()
    u = info["usage"]
    assert u["strict"] > 0 and u["friendly"] > 0 and u["datasets"] == 0 and u["used"] == u["strict"] + u["friendly"], u
    assert u["quota"] == settings.get("USER_QUOTA_MB") * 1024 * 1024 and "kể cả khi bạn xoá tài khoản" in info["feedback_note"]

    # ---------------- đổi mật khẩu
    assert c.post("/s4/account/password", json={"old_password": "sai", "new_password": "abcdef"}).status_code == 403
    assert c.post("/s4/account/password", json={"old_password": "123456", "new_password": "ab"}).status_code == 422
    assert c.post("/s4/account/password", json={"old_password": "123456", "new_password": "matkhau2"}).status_code == 200
    assert c.get("/s4/account").status_code == 200, "phiên hiện tại vẫn dùng được"
    c.cookies.clear()
    assert c.post("/s4/auth/login", json={"username": "dan", "password": "123456"}).status_code == 401
    assert c.post("/s4/auth/login", json={"username": "dan", "password": "matkhau2"}).status_code == 200
    as_user("dan")

    # ---------------- G1.7: hạn mức dung lượng gồm hội thoại
    settings.save({"USER_QUOTA_MB": 10})
    ds = db.run("INSERT INTO datasets(user_id,name,filename,size_bytes,domain_id) VALUES (?,?,?,?,?)", (dan_id, "to", "to.csv", 10 * 1024 * 1024, 2))
    r = c.post("/s4/chat", json={"text": "câu nữa"})
    assert r.status_code == 413 and "hết dung lượng" in r.json()["detail"], (r.status_code, r.text[:200])
    r = c.post("/s4/strict/chat", json={"text": "đăng ký kết hôn cần gì"})
    assert r.status_code == 413 and "hết dung lượng" in r.json()["detail"], (r.status_code, r.text[:200])
    assert c.post("/chat", json={"text": "đăng ký kết hôn cần gì"}).status_code == 413, "gọi thẳng /chat của System 3 cũng bị chặn"
    as_user("boss")   # dev không giới hạn
    db.run("UPDATE datasets SET user_id=? WHERE id=?", (c.get("/s4/auth/me").json()["user"]["id"], ds))
    assert c.post("/s4/strict/chat", json={"text": "đăng ký kết hôn cần gì"}).status_code == 200
    db.run("UPDATE datasets SET user_id=? WHERE id=?", (dan_id, ds))
    as_user("dan")
    db.run("DELETE FROM datasets WHERE id=?", (ds,))   # xoá bớt -> dùng lại được
    assert c.post("/s4/strict/chat", json={"text": "đăng ký kết hôn cần gì", "root": root}).status_code == 200
    settings.save({"USER_QUOTA_MB": 1024})

    # ---------------- xoá bộ nhớ / xoá hết hội thoại (không xoá tài khoản)
    assert c.delete("/s4/account/memory").status_code == 200
    assert q(S4, "SELECT COUNT(*) FROM memories WHERE user_id=?", dan_id)[0][0] == 0
    assert c.get("/memory").json()["profile"]["note"] == ""
    r = c.delete("/s4/account/conversations").json()
    assert r["strict"] >= 1 and r["friendly"] >= 1 and r["usage"]["used"] == 0, r
    assert c.get("/s4/conversations").json()["conversations"] == []
    # dùng lại để có dữ liệu cho bước xoá tài khoản
    r = c.post("/s4/strict/chat", json={"text": f"sđt {PHONE}, khai tử cần gì?"})
    root2, node2 = r.json()["conversation_id"], r.json()["message_id"]
    assert c.post(f"/s4/strict/{root2}/feedback", json={"node_id": node2, "value": -1}).status_code == 200
    s3_ids = {root2} | set(db.strict_branches(root2))

    # ---------------- xoá tài khoản
    assert c.request("DELETE", "/s4/account", json={"password": "123456"}).status_code == 403, "sai mật khẩu"
    n_fb = q(S4, "SELECT COUNT(*) FROM feedback_log WHERE user_id=?", dan_id)[0][0]
    assert n_fb == 3, n_fb
    r = c.request("DELETE", "/s4/account", json={"password": "matkhau2"})
    assert r.status_code == 200 and r.json()["feedback_kept_anonymous"] == 3, r.text
    assert c.get("/s4/account").status_code == 401, "cookie bị xoá / phiên hết"
    # System 4: không còn gì gắn với dan, trừ feedback_log đã bỏ danh tính
    for t in ("users", "sessions", "conversations", "memories", "user_prefs", "datasets", "traces", "strict_owner", "domain_pins"):
        col = "id" if t == "users" else "user_id"
        assert q(S4, f"SELECT COUNT(*) FROM {t} WHERE {col}=?", dan_id)[0][0] == 0, t
    assert q(S4, "SELECT COUNT(*) FROM strict_nodes WHERE root IN (?)", root2)[0][0] == 0
    fb = q(S4, "SELECT user_id, conversation_id, prompt, answer FROM feedback_log")
    assert len(fb) == 3 and all(r[0] == 0 and r[1] == "" for r in fb), fb
    assert all(PHONE not in (r[2] + r[3]) for r in fb), "feedback_log đã che số"
    # System 3: hội thoại và hồ sơ của dan đã xoá
    for cid in s3_ids | {root}:
        assert q(S3, "SELECT COUNT(*) FROM conversations WHERE id=?", cid)[0][0] == 0, cid
    assert q(S3, "SELECT COUNT(*) FROM user_memory WHERE client_id=?", f"u{dan_id}")[0][0] == 0

    # ---------------- dev cuối cùng không tự xoá được
    as_user("boss")
    r = c.request("DELETE", "/s4/account", json={"password": "123456"})
    assert r.status_code == 422 and "dev cuối cùng" in r.json()["detail"], r.text
print("OK account_test")

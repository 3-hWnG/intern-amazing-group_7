"""Khách (không đăng nhập) + giới hạn lượt hỏi theo vai trò (guest.py, ratelimit.py).
- Khách: cookie ký HMAC, KHÔNG có dòng nào trong hai DB (users/sessions, hội thoại Friendly lẫn Strict); hội thoại khách nằm trong RAM,
  khách khác / tài khoản khác không thấy; chỉ gọi được API trò chuyện (403 cho bộ nhớ, tải dữ liệu, 👍/👎, cài đặt…); cookie sửa
  chữ ký -> không còn là khách; đăng nhập xoá cookie khách; tắt GUEST_ENABLED -> mời đăng nhập; quá 24 giờ -> dọn khỏi RAM.
- Giới hạn: mỗi phút / mỗi ngày / số câu đang trả lời / độ dài câu / theo IP của khách / số phiên khách mới / mọi API mỗi phút;
  trả lại lượt khi tin không hợp lệ; thả chỗ "đang trả lời" ngay ở sự kiện done.
Chạy: python run_server.py system4/tests/guest_limit_test.py"""
import asyncio, json, os, sqlite3, sys, tempfile, time
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0", S4_RATE_LIMIT="1",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, config, guest, llm, ratelimit, settings


async def fake_fast(messages, schema):
    raw = json.dumps({"plan": "chào", "answer": "Dạ, chào bạn.", "ask_back": False, "choices": []})
    for i in range(0, len(raw), 7):
        yield raw[i:i + 7]


llm.stream_json = fake_fast
llm.chat_json = lambda messages, schema, timeout=60: {"add": [], "remove": []} if "add" in schema.get("properties", {}) else {"summary": ""}


def rows(path, sql):
    c = sqlite3.connect(path)
    try:
        return c.execute(sql).fetchall()
    finally:
        c.close()


S4DB, S3DB = str(config.DB_PATH), os.environ["S3_DB_PATH"]

with TestClient(main.app) as c:
    # máy mới (chưa có tài khoản): chưa cho khách, tài khoản đầu tiên (dev) phải tạo trước
    assert c.get("/s4/public").json()["guest_enabled"] is False
    assert c.post("/s4/auth/guest").status_code == 403
    tok = {}
    for n in ("boss", "dan"):
        c.cookies.clear()
        tok[n] = c.post("/s4/auth/signup", json={"username": n, "password": "123456"}).cookies.get(auth.COOKIE)
    c.cookies.clear()

    # ---------------- vào chế độ khách
    p = c.get("/s4/public").json()
    assert p["guest_enabled"] and p["user"] is None and p["guest_limits"]["per_day"] == 20 and p["user_limits"]["per_day"] == 200
    assert c.get("/s4/conversations").status_code == 401
    r = c.post("/s4/auth/guest")
    assert r.status_code == 200 and r.json()["user"]["role"] == "guest" and r.json()["user"]["id"] < 0
    g1 = c.cookies.get(guest.COOKIE)
    assert g1 and r.json()["user"] == c.post("/s4/auth/guest").json()["user"], "đã là khách: dùng tiếp phiên cũ"
    assert c.get("/s4/auth/me").json()["user"]["role"] == "guest"
    assert c.get("/", headers={"accept": "text/html"}).status_code == 200
    me = c.get("/s4/public").json()
    assert me["user"]["role"] == "guest" and me["limits"]["left_today"] == 20 and me["limits"]["max_chars"] == 1000

    # ---------------- khách chỉ dùng được API trò chuyện
    for method, url in (("GET", "/s4/memory"), ("GET", "/s4/account"), ("GET", "/s4/settings"), ("POST", "/s4/datasets"),
                        ("POST", "/s4/domains"), ("POST", "/s4/domains/2/pin"), ("GET", "/s4/admin/users"), ("POST", "/s4/account/prefs"),
                        ("POST", "/s4/conversations/x/messages/1/feedback"), ("POST", "/s4/strict/x/feedback"), ("GET", "/s4/admin/stats")):
        r = c.request(method, url, json={})
        assert r.status_code == 403 and "Đăng nhập" in r.json()["detail"], (method, url, r.status_code, r.text)
    assert c.get("/s4/admin", headers={"accept": "text/html"}, follow_redirects=False).status_code == 303
    assert c.get("/s4/domains").status_code == 200
    ds = c.get("/s4/datasets?domain_id=2").json()
    assert ds["can_upload"] is False and all(not d["can_upload"] for d in c.get("/s4/domains").json()["domains"])

    # ---------------- trò chuyện: Friendly + Strict, không ghi DB
    n_users, n_msgs = rows(S4DB, "SELECT COUNT(*) FROM users")[0][0], rows(S4DB, "SELECT COUNT(*) FROM messages")[0][0]
    r = c.post("/s4/chat", json={"text": "xin chào", "domain_id": 2})
    assert r.status_code == 200 and '"type": "done"' in r.text, r.text[-300:]
    r = c.post("/s4/strict/chat", json={"text": "Đăng ký khai sinh cần giấy tờ gì?"})
    assert r.status_code == 200, r.text
    sroot = r.json()["conversation_id"]
    convs = c.get("/s4/conversations").json()["conversations"]
    assert {x["mode"] for x in convs} == {"friendly", "strict"}, convs
    fcid = next(x["id"] for x in convs if x["mode"] == "friendly")
    msgs = c.get(f"/s4/conversations/{fcid}/messages").json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"] and msgs[0]["id"] >= 10 ** 12, msgs
    assert len(c.get(f"/s4/strict/{sroot}/messages").json()["messages"]) == 2
    assert c.patch(f"/s4/conversations/{fcid}", json={"title": "Chào"}).json()["title"] == "Chào"
    assert c.get(f"/s4/conversations/{fcid}/export?format=md").status_code == 200
    # DB thật: không người dùng / phiên / hội thoại / tin nào của khách
    assert rows(S4DB, "SELECT COUNT(*) FROM users")[0][0] == n_users and rows(S4DB, "SELECT COUNT(*) FROM sessions WHERE user_id<0")[0][0] == 0
    assert rows(S4DB, "SELECT COUNT(*) FROM messages")[0][0] == n_msgs
    for t in ("conversations", "memories", "traces", "strict_owner", "strict_nodes"):
        assert rows(S4DB, f"SELECT COUNT(*) FROM {t} WHERE " + ("user_id<0" if t in ("conversations", "memories", "traces", "strict_owner") else "1"))[0][0] == 0, t
    assert rows(S4DB, f"SELECT COUNT(*) FROM conversations WHERE id='{fcid}'")[0][0] == 0
    assert rows(S3DB, f"SELECT COUNT(*) FROM conversations WHERE id='{sroot}'")[0][0] == 0
    assert rows(S3DB, "SELECT COUNT(*) FROM messages")[0][0] == 0
    # RAM có đủ
    assert guest._rams["s4"].c.execute("SELECT COUNT(*) FROM main.conversations").fetchone()[0] == 1
    assert guest._rams["s3"].c.execute("SELECT COUNT(*) FROM main.conversations WHERE id=?", (sroot,)).fetchone()[0] == 1

    # ---------------- khách khác / tài khoản không thấy hội thoại của khách này
    c.cookies.clear()
    assert c.post("/s4/auth/guest").status_code == 200
    g2 = c.cookies.get(guest.COOKIE)
    assert g2 != g1 and c.get("/s4/conversations").json()["conversations"] == []
    assert c.get(f"/s4/conversations/{fcid}/messages").status_code == 404 and c.get(f"/s4/strict/{sroot}/messages").status_code == 404
    c.cookies.clear(); c.cookies.set(auth.COOKIE, tok["dan"])
    assert c.get("/s4/conversations").json()["conversations"] == [] and c.get(f"/s4/conversations/{fcid}/messages").status_code == 404

    # ---------------- cookie sửa chữ ký -> không còn là khách
    c.cookies.clear(); c.cookies.set(guest.COOKIE, g1[:-1] + ("0" if g1[-1] != "0" else "1"))
    assert c.get("/s4/auth/me").status_code == 401

    # ---------------- giới hạn qua API: khách 3 câu / phút (đã dùng 2), câu dài
    c.cookies.clear(); c.cookies.set(guest.COOKIE, g1)
    assert c.post("/s4/chat", json={"text": "x" * 1001}).status_code == 413
    assert c.post("/s4/chat", json={"text": "  "}).status_code == 422   # tin rỗng: trả lại lượt
    assert c.get("/s4/public").json()["limits"]["used_today"] == 2
    assert c.post("/s4/chat", json={"text": "cảm ơn", "conversation_id": fcid}).status_code == 200
    r = c.post("/s4/chat", json={"text": "câu thứ tư", "conversation_id": fcid})
    assert r.status_code == 429 and "3 câu mỗi phút" in r.json()["detail"] and int(r.headers["retry-after"]) > 0, r.text
    r = c.post("/s4/strict/chat", json={"text": "khai tử cần gì?", "root": sroot})
    assert r.status_code == 429, "Strict tính chung hạn mức"
    assert c.get("/s4/public").json()["limits"]["left_today"] == 17

    # ---------------- đăng nhập xoá cookie khách
    r = c.post("/s4/auth/login", json={"username": "dan", "password": "123456"})
    assert r.status_code == 200 and any(h.startswith(guest.COOKIE + '=""') and "Max-Age=0" in h for h in r.headers.get_list("set-cookie"))

    # ---------------- ratelimit (đồng hồ giả)
    ratelimit.reset()
    t0 = time.mktime(time.strptime("2026-10-20 08:00:00", "%Y-%m-%d %H:%M:%S"))
    gu = {"id": -5, "role": "guest", "guest": "abc"}
    for i in range(20):   # mỗi ngày 20 câu
        ratelimit.begin_turn(gu, "1.1.1.1", 10, now=t0 + i * 61).end()
    try:
        ratelimit.begin_turn(gu, "1.1.1.1", 10, now=t0 + 30 * 61)
        raise AssertionError("câu 21 của khách phải bị chặn")
    except ratelimit.Limited as e:
        assert e.status_code == 429 and "Đăng nhập" in e.detail and "200 câu" in e.detail and int(e.headers["Retry-After"]) > 3600
    ratelimit.begin_turn(gu, "1.1.1.1", 10, now=t0 + 86400).end()   # hôm sau: làm mới
    # theo IP: 5 khách x 20 câu = 100 câu / IP / ngày; khách thứ 6 cùng IP bị chặn dù mã khách mới
    ratelimit.reset()
    for k in range(5):
        for i in range(20):
            ratelimit.begin_turn({"id": -10 - k, "role": "guest", "guest": f"k{k}"}, "2.2.2.2", 0, now=t0 + k * 2000 + i * 61).end()
    try:
        ratelimit.begin_turn({"id": -99, "role": "guest", "guest": "moi"}, "2.2.2.2", 0, now=t0 + 20000)
        raise AssertionError("IP đã hết lượt khách")
    except ratelimit.Limited as e:
        assert "Mạng của bạn" in e.detail
    ratelimit.begin_turn({"id": -99, "role": "guest", "guest": "moi"}, "3.3.3.3", 0, now=t0 + 20000).end()   # IP khác vẫn được
    # đang trả lời cùng lúc: người dân 1, dev 5; trả lại lượt
    ratelimit.reset()
    dan, boss = {"id": 2, "role": "user"}, {"id": 1, "role": "dev"}
    t = ratelimit.begin_turn(dan, "4.4.4.4", 0, now=t0)
    try:
        ratelimit.begin_turn(dan, "4.4.4.4", 0, now=t0 + 1)
        raise AssertionError("người dân chỉ 1 câu đang trả lời")
    except ratelimit.Limited as e:
        assert "đang được trả lời" in e.detail
    t.refund()
    assert ratelimit.usage(dan, now=t0)["used_today"] == 0
    ratelimit.begin_turn(dan, "4.4.4.4", 0, now=t0 + 2).end()
    held = [ratelimit.begin_turn(boss, "", 0, now=t0 + i) for i in range(5)]
    try:
        ratelimit.begin_turn(boss, "", 0, now=t0 + 6)
        raise AssertionError("dev tối đa 5 câu cùng lúc")
    except ratelimit.Limited:
        pass
    for h in held:
        h.end()
    # mỗi phút: người dân 10
    ratelimit.reset()
    for i in range(10):
        ratelimit.begin_turn(dan, "", 0, now=t0 + i).end()
    try:
        ratelimit.begin_turn(dan, "", 0, now=t0 + 30)
        raise AssertionError("người dân 10 câu / phút")
    except ratelimit.Limited as e:
        assert "10 câu mỗi phút" in e.detail and 25 <= int(e.headers["Retry-After"]) <= 31
    ratelimit.begin_turn(dan, "", 0, now=t0 + 61).end()
    # độ dài: người dân 4000, cán bộ 16000
    for who, n, ok in ((dan, 4000, True), (dan, 4001, False), ({"id": 3, "role": "can_bo"}, 16000, True)):
        try:
            ratelimit.begin_turn(who, "", n, now=t0 + 200).end()
            assert ok, (who, n)
        except ratelimit.Limited as e:
            assert not ok and e.status_code == 413
    # mọi API: khách 60 / phút; phiên khách mới: 20 / IP / giờ
    for i in range(60):
        ratelimit.api_hit(gu, "", now=t0 + i * 0.5)
    try:
        ratelimit.api_hit(gu, "", now=t0 + 31)
        raise AssertionError("khách 60 yêu cầu / phút")
    except ratelimit.Limited:
        pass
    for i in range(20):
        ratelimit.guest_new("5.5.5.5", now=t0 + i)
    try:
        ratelimit.guest_new("5.5.5.5", now=t0 + 100)
        raise AssertionError("20 phiên khách / IP / giờ")
    except ratelimit.Limited:
        pass
    ratelimit.guest_new("5.5.5.5", now=t0 + 3601)

    # luồng SSE: thả chỗ "đang trả lời" ngay ở sự kiện done (luồng còn mở để báo bộ nhớ)
    async def sse_after_done():
        ratelimit.reset()
        tk = ratelimit.begin_turn(dan, "", 0)
        seen = []

        async def gen():
            yield 'data: {"type": "delta", "text": "a"}\n\n'
            yield 'data: {"type": "done"}\n\n'
            seen.append(tk.busy)
            yield 'data: {"type": "memory"}\n\n'
        async for _ in ratelimit.guarded(tk, gen()):
            pass
        return seen
    assert asyncio.run(sse_after_done()) == [False]

    # ---------------- tắt chế độ khách: khách đang dùng bị mời đăng nhập
    ratelimit.reset()
    settings.save({"GUEST_ENABLED": False})
    c.cookies.clear(); c.cookies.set(guest.COOKIE, g1)
    assert c.get("/s4/conversations").status_code == 401 and c.post("/s4/auth/guest").status_code == 403
    assert c.get("/s4/public").json()["guest_enabled"] is False
    settings.save({"GUEST_ENABLED": True})
    assert c.get("/s4/conversations").status_code == 200

    # ---------------- quá 24 giờ: cookie hết hạn, hội thoại khách bị dọn khỏi RAM
    assert guest.user_from_cookie(g1, now=time.time() + guest.KEEP_HOURS * 3600 + 5) is None
    guest._rams["s4"].c.execute("UPDATE main.conversations SET created_at=datetime('now','-25 hours')")
    guest._rams["s3"].c.execute("UPDATE main.conversations SET created_at=datetime('now','-25 hours')")
    guest._rams["s4"].c.commit(); guest._rams["s3"].c.commit()
    guest.sweep(force=True)
    for name in ("s3", "s4"):
        assert guest._rams[name].c.execute("SELECT COUNT(*) FROM main.messages").fetchone()[0] == 0, name
    assert guest._rams["s4"].c.execute("SELECT COUNT(*) FROM main.strict_nodes").fetchone()[0] == 0
    assert c.get("/s4/conversations").json()["conversations"] == []
    guest.reset()
print("OK guest_limit_test")

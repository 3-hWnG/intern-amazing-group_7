"""NV1: đăng nhập/đăng ký, cổng đăng nhập cho cả web, hội thoại Strict theo người, Friendly (LLM giả), cài đặt.
Chạy (từ thư mục server/, giống test System 3):
    set PYTHONPATH=<thư mục pyroot> && python ../system4/tests/test_nv1.py
DB System 3 + System 4 đều là thư mục tạm; config.py thật không bị ghi (dùng bản sao)."""
import json
import os
import shutil
import sys
import tempfile

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"))

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, llm, settings

COOKIE = auth.COOKIE
HTML = {"accept": "text/html"}


def events(resp):
    return [json.loads(l[6:]) for l in resp.text.split("\n\n") if l.startswith("data: ")]


seen_prompts = []


async def fake_stream(messages):
    seen_prompts.append(messages)
    yield llm.THINKING
    for part in ["Xin ", "chào ", "bạn!"]:
        yield part


async def broken_stream(messages):
    raise llm.LLMError("Ollama tắt")
    yield ""   # noqa: để là async generator


llm.chat_json = lambda *a, **k: {}   # bộ nhớ/tóm tắt chạy nền (NV2): không gọi Ollama thật trong test

with TestClient(main.app) as c:
    def as_user(tok):
        c.cookies.clear()
        if tok:
            c.cookies.set(COOKIE, tok)

    # ---- chưa đăng nhập: chỉ trang login, /health, tệp tĩnh
    r = c.get("/", headers=HTML, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/s4/login", r.status_code
    assert c.get("/conversations").status_code == 401
    assert c.post("/chat", json={"text": "xin chào"}).status_code == 401
    assert c.post("/s4/chat", json={"mode": "think", "text": "xin chào"}).status_code == 401
    assert c.get("/s4/login").status_code == 200
    assert c.get("/health").status_code == 200
    assert c.get("/static/css/styles.css").status_code == 200 and c.get("/s4/static/js/app.js").status_code == 200
    assert c.get("/s4/public").json()["first_account"] is True

    # hội thoại Strict có từ trước khi bật đăng nhập -> sẽ thuộc dev đầu tiên
    legacy = main.store.ensure_conversation(None)

    # ---- đăng ký: kiểm dữ liệu, tài khoản đầu là dev
    assert c.post("/s4/auth/signup", json={"username": "a", "password": "123456"}).status_code == 422
    assert c.post("/s4/auth/signup", json={"username": "alice", "password": "123"}).status_code == 422
    assert c.post("/s4/auth/signup", json={"username": "alice", "password": "123456", "password2": "x"}).status_code == 422
    r = c.post("/s4/auth/signup", json={"username": "alice", "password": "123456", "password2": "123456"})
    assert r.status_code == 200 and r.json()["user"]["role"] == "dev", r.text
    alice = r.cookies.get(COOKIE)
    assert alice
    r = c.post("/s4/auth/signup", json={"username": "ALICE", "password": "123456"})
    assert r.status_code == 422, "trùng tên (không phân biệt hoa thường)"
    as_user(None)
    r = c.post("/s4/auth/signup", json={"username": "bob", "password": "abcdef"})
    assert r.json()["user"]["role"] == "user"
    bob = r.cookies.get(COOKIE)

    # ---- đăng nhập
    as_user(None)
    assert c.post("/s4/auth/login", json={"username": "bob", "password": "sai"}).status_code == 401
    assert c.post("/s4/auth/login", json={"username": "nobody", "password": "abcdef"}).status_code == 401
    r = c.post("/s4/auth/login", json={"username": "Bob", "password": "abcdef"})
    assert r.status_code == 200 and r.cookies.get(COOKIE)

    # ---- trang chính sau đăng nhập = trang chung
    as_user(alice)
    r = c.get("/", headers=HTML)
    assert r.status_code == 200 and "mode-switch" in r.text
    assert c.get("/s4/auth/me").json()["user"]["username"] == "alice"
    assert c.get("/s4/login", follow_redirects=False).status_code == 303

    # ---- Strict: mỗi người chỉ thấy của mình
    a = c.post("/chat", json={"text": "Đăng ký khai sinh cần giấy tờ gì?"})
    assert a.status_code == 200, a.text
    cid_a = a.json()["conversation_id"]
    ids = [x["id"] for x in c.get("/conversations").json()["conversations"]]
    assert cid_a in ids and legacy in ids, ids
    assert c.get(f"/conversations/{cid_a}/messages").status_code == 200
    as_user(bob)
    ids = [x["id"] for x in c.get("/conversations").json()["conversations"]]
    assert cid_a not in ids and legacy not in ids, ids
    assert c.get(f"/conversations/{cid_a}/messages").status_code == 404
    assert c.get(f"/conversations/{legacy}/messages").status_code == 404
    assert c.patch(f"/conversations/{cid_a}", json={"title": "x"}).status_code == 404
    assert c.delete(f"/conversations/{cid_a}").status_code == 404
    assert c.post("/chat", json={"text": "cái thứ nhất", "conversation_id": cid_a}).status_code == 404
    b = c.post("/chat", json={"text": "Tôi muốn đăng ký kết hôn"}).json()
    cid_b = b["conversation_id"]
    assert c.post("/chat", json={"text": "cần giấy tờ gì", "conversation_id": cid_b}).status_code == 200
    assert c.post("/config", json={"answer_llm": False}).status_code == 403, "chỉ dev đổi cấu hình System 3"
    assert c.get("/config").status_code == 200

    # ---- Friendly: luồng SSE, lưu tin, giữ ngữ cảnh
    llm.stream_chat = fake_stream
    r = c.post("/s4/chat", json={"mode": "think", "text": "Chào AI"})
    ev = events(r)
    assert [e["type"] for e in ev] == ["meta", "start", "thinking", "delta", "delta", "delta", "done"], ev
    fcid = ev[0]["conversation_id"]
    msgs = c.get(f"/s4/conversations/{fcid}/messages").json()["messages"]
    assert [(m["role"], m["content"]) for m in msgs] == [("user", "Chào AI"), ("assistant", "Xin chào bạn!")], msgs
    r = c.post("/s4/chat", json={"mode": "think", "text": "Bạn nhớ tôi vừa nói gì không?", "conversation_id": fcid})
    assert events(r)[-1]["type"] == "done"
    sent = seen_prompts[-1]
    assert sent[0]["role"] == "system" and [m["content"] for m in sent[1:]] == ["Chào AI", "Xin chào bạn!", "Bạn nhớ tôi vừa nói gì không?"], sent
    llm.stream_chat = broken_stream
    ev = events(c.post("/s4/chat", json={"mode": "think", "text": "lỗi?", "conversation_id": fcid}))
    assert ev[-1]["type"] == "error" and "Ollama" in ev[-1]["message"], ev
    assert c.get(f"/s4/conversations/{fcid}/messages").json()["messages"][-1]["status"] == "error"
    llm.stream_chat = fake_stream
    c.post("/s4/chat", json={"mode": "think", "text": "tiếp", "conversation_id": fcid})
    assert all(m["content"] != "Ollama tắt" for m in seen_prompts[-1]), "tin lỗi không được gửi lại cho AI"

    # danh sách chung: Strict + Friendly, có nhãn chế độ
    rows = c.get("/s4/conversations").json()["conversations"]
    assert {(x["id"], x["mode"]) for x in rows} == {(cid_b, "strict"), (fcid, "friendly")}, rows
    assert c.patch(f"/s4/conversations/{fcid}", json={"title": "Đổi tên", "pinned": True}).json()["pinned"] is True
    rows = c.get("/s4/conversations").json()["conversations"]
    assert rows[0]["id"] == fcid and rows[0]["title"] == "Đổi tên", rows
    md = c.get(f"/s4/conversations/{fcid}/export?format=md")
    assert md.status_code == 200 and "Xin chào bạn!" in md.text
    assert c.get(f"/s4/conversations/{fcid}/export?format=json").json()["conversation"]["mode"] == "friendly"
    as_user(alice)
    assert c.get(f"/s4/conversations/{fcid}/messages").status_code == 404, "không xem được Friendly của người khác"
    assert c.post("/s4/chat", json={"mode": "think", "text": "x", "conversation_id": fcid}).status_code == 404

    # ---- cài đặt: chỉ dev; Lưu / Về mặc định / Đặt làm mặc định
    as_user(bob)
    assert c.get("/s4/settings").status_code == 403
    assert c.post("/s4/settings", json={"values": {"APP_TITLE": "Hack"}}).status_code == 403
    as_user(alice)
    keys = [s["key"] for s in c.get("/s4/settings").json()["settings"]]
    assert "APP_TITLE" in keys and "GUARDRAILS" in keys
    assert c.post("/s4/settings", json={"values": {"SESSION_DAYS": 0}}).status_code == 422
    assert c.post("/s4/settings", json={"values": {"DEFAULT_MODE": "abc"}}).status_code == 422
    assert c.post("/s4/settings", json={"values": {"ALLOW_SIGNUP": "yes"}}).status_code == 422
    r = c.post("/s4/settings", json={"values": {"APP_TITLE": "Web thử", "DEFAULT_MODE": "friendly"}})
    assert r.status_code == 200 and r.json()["reload"] is True
    assert c.get("/s4/public").json()["app_title"] == "Web thử"
    assert json.load(open(os.path.join(TMP, "s4", "settings.json"), encoding="utf-8"))["APP_TITLE"] == "Web thử"
    c.post("/s4/settings/reset", json={"keys": ["APP_TITLE", "DEFAULT_MODE"]})
    assert c.get("/s4/public").json()["app_title"] == "Instant Specialist"
    real = settings.CONFIG_FILE
    real_text = real.read_text(encoding="utf-8")
    copy = os.path.join(TMP, "config_copy.py")
    shutil.copy(real, copy)
    settings.CONFIG_FILE = type(real)(copy)
    c.post("/s4/settings", json={"values": {"SESSION_DAYS": 30}})
    r = c.post("/s4/settings/default", json={"values": {"APP_TITLE": "Mặc định mới", "FRIENDLY_TEMPERATURE": 0.2}})
    assert r.status_code == 200, r.text
    new = open(copy, encoding="utf-8").read()
    assert "APP_TITLE = 'Mặc định mới'" in new and "FRIENDLY_TEMPERATURE = 0.2" in new, new
    assert os.path.exists(copy + ".bak") and real.read_text(encoding="utf-8") == real_text, "config.py thật không đổi"
    d = {s["key"]: s for s in c.get("/s4/settings").json()["settings"]}
    assert d["APP_TITLE"]["default"] == "Mặc định mới" and not d["APP_TITLE"]["overridden"]
    assert d["SESSION_DAYS"]["overridden"] and d["SESSION_DAYS"]["value"] == 30, "ghi đè khác vẫn giữ"
    compile(new, copy, "exec")   # config.py sau khi ghi vẫn là Python hợp lệ

    # tắt đăng ký: đã có người dùng -> chặn
    c.post("/s4/settings", json={"values": {"ALLOW_SIGNUP": False}})
    as_user(None)
    assert c.post("/s4/auth/signup", json={"username": "carol", "password": "abcdef"}).status_code == 403
    assert c.get("/s4/public").json()["signup_open"] is False

    # ---- xoá tất cả: chỉ của mình (cả hai chế độ)
    as_user(bob)
    assert c.delete("/s4/conversations").json()["ok"]
    assert c.get("/s4/conversations").json()["conversations"] == []
    as_user(alice)
    ids = [x["id"] for x in c.get("/conversations").json()["conversations"]]
    assert cid_a in ids and legacy in ids, "xoá của bob không đụng của alice"
    assert c.delete("/conversations").json()["ok"]   # API System 3: chỉ Strict của alice
    assert c.get("/conversations").json()["conversations"] == []
    assert not main.store.conversation_exists(cid_a) and not main.store.conversation_exists(cid_b)

    # ---- đăng xuất
    assert c.post("/s4/auth/logout").status_code == 200
    as_user(alice)   # cookie cũ đã bị huỷ ở server
    assert c.get("/s4/auth/me").status_code == 401

print("OK test_nv1")

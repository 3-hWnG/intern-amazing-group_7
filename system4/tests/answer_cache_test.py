"""Dùng lại câu trả lời đã 👍 khi người khác hỏi y chang (answer_cache.py; quyết định 18/10 sau G3.4). LLM giả, không gọi Ollama.
Kiểm: A hỏi -> 👍 -> B hỏi y chang (khác hoa/thường, khoảng trắng, dấu ?) được trả ngay, KHÔNG gọi model, có meta.cached;
không dùng lại khi: câu thứ hai của hội thoại, câu có SĐT, bấm ↻ tạo lại, tắt công tắc, đổi tên doanh nghiệp, đã có 👎 trên bản dùng lại,
câu chưa ai 👍; dùng lại giữ nút lựa chọn.
Chạy: python run_server.py system4/tests/answer_cache_test.py"""
import json, os, sys, tempfile
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, llm
import nv5_off
nv5_off.apply()

calls = []
replies = []


async def fake_fast(messages, schema):
    calls.append(messages[-1]["content"])
    d = replies.pop(0) if replies else {"plan": "", "answer": f"Trả lời mới số {len(calls)}.", "ask_back": False, "choices": []}
    yield json.dumps(d)


llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}


def events(r):
    return [json.loads(l[6:]) for l in r.text.split("\n\n") if l.startswith("data: ")]


with TestClient(main.app) as c:
    tok = {}
    for n in ("dev0", "anhan", "binh", "chi"):
        c.cookies.clear()
        tok[n] = c.post("/s4/auth/signup", json={"username": n, "password": "123456"}).cookies.get(auth.COOKIE)
        assert tok[n], n

    def as_user(n):
        c.cookies.clear(); c.cookies.set(auth.COOKIE, tok[n])

    def chat(text, **kw):
        r = c.post("/s4/chat", json={"text": text, **kw})
        ev = events(r)
        assert ev, (r.status_code, r.text[:500])
        cid = ev[0]["conversation_id"]
        m = c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]
        return ev, cid, m

    def like(cid, mid, v=1):
        assert c.post(f"/s4/conversations/{cid}/messages/{mid}/feedback", json={"value": v}).status_code == 200

    Q = "Làm sao để ngủ ngon hơn?"
    as_user("anhan")
    replies.append({"plan": "", "answer": "Đi ngủ đúng giờ và tránh màn hình trước khi ngủ.", "ask_back": False, "choices": []})
    _, cid_a, m_a = chat(Q)
    assert m_a["meta"].get("cacheable") and m_a["meta"].get("cache_fp"), m_a["meta"]
    # chưa ai 👍: người khác hỏi vẫn gọi model
    as_user("binh")
    n = len(calls)
    _, _, m = chat(Q)
    assert len(calls) == n + 1 and "cached" not in m["meta"]
    # A 👍 -> B hỏi y chang (khác hoa/thường, khoảng trắng, dấu câu) được trả ngay
    as_user("anhan")
    like(cid_a, m_a["id"])
    as_user("binh")
    n = len(calls)
    ev, cid_b, m_b = chat("  làm sao để   NGỦ ngon hơn ")
    assert len(calls) == n, "không gọi model"
    assert m_b["content"] == m_a["content"] and m_b["meta"]["cached"]["from"] == str(m_a["id"]), m_b
    assert [e["type"] for e in ev] == ["meta", "cached", "delta", "done"], ev
    # câu thứ hai của hội thoại: không dùng lại (có ngữ cảnh)
    n = len(calls)
    chat(Q, conversation_id=cid_b)
    assert len(calls) == n + 1
    # ↻ tạo lại: AI viết mới
    n = len(calls)
    _, cid_r, m_r = chat(Q)
    assert len(calls) == n and m_r["meta"].get("cached")
    ev = events(c.post("/s4/chat", json={"conversation_id": cid_r, "regenerate_of": m_r["id"]}))
    assert len(calls) == n + 1 and ev[-1]["type"] == "done"
    # câu có SĐT: không dùng lại, không ghi để dùng lại
    as_user("anhan")
    _, cid_p, m_p = chat("Số 0912345678 của tôi bị khoá, làm sao để ngủ ngon hơn?")
    assert not m_p["meta"].get("cacheable")
    # dùng lại giữ nút lựa chọn
    replies.append({"plan": "", "answer": "Bạn muốn hỏi loại giấy nào?", "ask_back": True, "choices": ["Khai sinh", "Kết hôn"]})
    _, cid_c, m_c = chat("Cần giấy tờ gì")
    like(cid_c, m_c["id"])
    as_user("chi")
    n = len(calls)
    _, _, m = chat("cần giấy tờ gì?")
    assert len(calls) == n and m["meta"].get("choices") == ["Khai sinh", "Kết hôn"], m
    # 👎 trên bản dùng lại -> câu gốc thôi được phục vụ
    as_user("binh")
    like(cid_b, m_b["id"], -1)
    as_user("chi")
    n = len(calls)
    _, _, m = chat(Q)
    assert len(calls) == n + 1 and "cached" not in m["meta"]
    # công tắc tắt / đổi tên doanh nghiệp
    as_user("dev0")
    q2 = "Gợi ý 3 món ăn sáng nhanh gọn"
    _, cid2, m2 = chat(q2)
    like(cid2, m2["id"])
    as_user("chi")
    n = len(calls)
    assert chat(q2)[2]["meta"].get("cached") and len(calls) == n
    as_user("dev0")
    assert c.post("/s4/settings", json={"values": {"ANSWER_CACHE": False}}).status_code == 200
    as_user("chi")
    chat(q2)
    assert len(calls) == n + 1, "tắt công tắc: gọi model"
    as_user("dev0")
    assert c.post("/s4/settings", json={"values": {"ANSWER_CACHE": True, "BUSINESS_NAME": "Team 8"}}).status_code == 200
    as_user("chi")
    chat(q2)
    assert len(calls) == n + 2, "đổi tên doanh nghiệp: câu cũ không dùng"
print("OK answer_cache_test")

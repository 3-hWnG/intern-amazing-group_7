"""G1.3 (P03, D12): sau một lượt Strict và một lượt Friendly có CCCD/SĐT giả (AI giả còn chép lại số trong câu trả lời, bộ nhớ, tóm tắt),
KHÔNG bảng nào của hai DB (hội thoại System 3, system4.db) còn số thô. Tìm web: số được che trước khi gửi đi và người dùng được báo.
Mã dịch vụ công / số của cơ quan trong câu trả lời Strict KHÔNG bị che (chỉ che số người dùng gõ).
Chạy: python run_server.py system4/tests/pii_storage_test.py"""
import json, os, sqlite3, sys, tempfile
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from core import websearch as core_web
from system3.system4.server import auth, llm, settings

CCCD, PHONE, PHONE_SP = "079203001234", "0912345678", "0912 345 678"
RAW = [CCCD, PHONE, PHONE_SP]

sent_queries = []   # truy vấn thật sự gửi tới DuckDuckGo (DDGS giả, không gọi mạng)


async def fake_fast(messages, schema):
    """AI giả chép lại mọi số có trong tin nhắn mới nhất (trường hợp xấu nhất; lịch sử/bộ nhớ đã che nên model không thấy số cũ)."""
    import re
    nums = re.findall(r"\d[\d ]{8,}\d", messages[-1]["content"])
    d = {"plan": "trả lời", "answer": "Dạ, mình ghi nhận " + ", ".join(nums) + " của bạn.", "ask_back": False, "choices": []}
    raw = json.dumps(d)
    for i in range(0, len(raw), 7):
        yield raw[i:i + 7]


def fake_json(messages, schema, timeout=60):
    if "summary" in schema.get("properties", {}):
        return {"summary": f"Người dùng có CCCD {CCCD}."}
    return {"add": [f"Người dùng có số điện thoại {PHONE} và CCCD {CCCD}"], "remove": []}


llm.stream_json = fake_fast
llm.chat_json = fake_json

with TestClient(main.app) as c:
    c.cookies.set(auth.COOKIE, c.post("/s4/auth/signup", json={"username": "dan", "password": "123456"}).cookies.get(auth.COOKIE))
    settings.save({"MEMORY_DEFAULT_MODE": "auto"})
    # ---- Strict: câu có CCCD + SĐT (có dấu cách)
    q = f"Tôi CCCD {CCCD}, sđt {PHONE_SP}, đăng ký khai sinh cần giấy tờ gì?"
    r = c.post("/s4/strict/chat", json={"text": q})
    assert r.status_code == 200, r.text
    root = r.json()["conversation_id"]
    node = r.json()["message_id"]
    assert c.post(f"/s4/strict/{root}/feedback", json={"node_id": node, "value": 1}).status_code == 200
    # ---- Friendly: AI giả chép lại số; nhớ "hãy nhớ"; 👍
    r = c.post("/s4/chat", json={"text": f"Hãy nhớ CCCD của mình là {CCCD} và sđt {PHONE}"})
    assert r.status_code == 200
    convs = c.get("/s4/conversations").json()
    fr = next(x["id"] for x in convs["conversations"] if x.get("mode") == "friendly")
    msgs = c.get(f"/s4/conversations/{fr}/messages").json()
    assert "messages" in msgs, (convs, msgs, r.text[-500:])
    msgs = msgs["messages"]
    am = next(m for m in msgs if m["role"] == "assistant")
    assert c.post(f"/s4/conversations/{fr}/messages/{am['id']}/feedback", json={"value": -1}).status_code == 200
    # ---- Tìm web (Strict và Friendly): số được che trước khi gửi lên DuckDuckGo, có dòng báo
    import ddgs
    class FakeDDGS:
        def __init__(self, timeout=8): pass
        def text(self, query, region=None, max_results=5):
            sent_queries.append(query)
            return [{"href": "https://example.gov.vn/a", "title": "Trang thử", "body": "Nội dung thử"}]
    ddgs.DDGS = FakeDDGS
    core_web._cache.clear()
    r = c.post("/s4/strict/chat", json={"text": f"CCCD {CCCD} làm lại ở đâu", "websearch": True, "root": root})
    assert r.status_code == 200, r.text
    view = c.get(f"/s4/strict/{root}/messages").json()["messages"]
    last = view[-1]
    blob = json.dumps(last, ensure_ascii=False)
    assert core_web.PII_NOTE in blob, blob[:600]
    r = c.post("/s4/chat", json={"text": f"tra giúp CCCD {CCCD}", "websearch": True})
    assert core_web.PII_NOTE in r.text, r.text[-400:]
    assert sent_queries and all(CCCD not in s for s in sent_queries), sent_queries

    # ---- quét mọi bảng của cả hai DB
    leaks = []
    for path in (os.environ["S3_DB_PATH"], os.path.join(TMP, "s4", "system4.db")):
        con = sqlite3.connect(path)
        for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%fts%'"):
            for row in con.execute(f"SELECT * FROM {t}"):
                s = " ".join(str(x) for x in row)
                for raw in RAW:
                    if raw in s:
                        leaks.append((os.path.basename(path), t, raw))
        con.close()
    assert not leaks, sorted(set(leaks))

    # ---- câu trả lời Strict vẫn giữ mã thủ tục / số của cơ quan (chỉ che số người dùng gõ)
    s3 = sqlite3.connect(os.environ["S3_DB_PATH"])
    ans = s3.execute("SELECT content FROM messages WHERE role='assistant' ORDER BY id LIMIT 1").fetchone()[0]
    assert "[ID]" not in ans and "[SDT]" not in ans, ans[:300]   # câu trả lời khai sinh không chép số người dùng -> không có nhãn che
    print("OK pii_storage_test")

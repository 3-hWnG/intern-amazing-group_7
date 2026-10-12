"""Nút "Tìm web": websearch=true -> chỉ DuckDuckGo (giả), bỏ qua bộ dữ liệu; nguồn có URL; mất mạng -> báo "không có kết quả", không lỗi.
LLM và DuckDuckGo đều giả (không cần Ollama / mạng).
Chạy: python run_server.py system4/tests/test_websearch.py"""
import json
import os
import sys
import tempfile

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")

from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, llm, websearch

prompts, calls = [], []
FAKE = [{"id": None, "title": "Tạm trú là gì", "dataset": "example.vn", "url": "https://example.vn/tam-tru",
         "text": "Đăng ký tạm trú cần CCCD và giấy tờ chỗ ở.", "score": None}]
result = {"ev": FAKE, "err": ""}


def fake_search(q):
    calls.append(q)
    return result["ev"], {"web": True, "query": q, "n": len(result["ev"]), "error": result["err"], "ms": 1}


async def fake_fast(messages, schema):
    prompts.append(messages)
    raw = json.dumps({"plan": "x", "answer": "Cần CCCD [1].", "ask_back": False, "choices": [], "sources": [1], "small_talk": False})
    for i in range(0, len(raw), 9):
        yield raw[i:i + 9]


async def fake_text(messages):   # phòng khi cấu hình dùng FAST_FORMAT=text
    prompts.append(messages)
    yield "KẾ HOẠCH: x\n===\nCần CCCD [1]."


websearch.search = fake_search
llm.stream_json, llm.stream_text = fake_fast, fake_text

with TestClient(main.app) as c:
    c.cookies.set(auth.COOKIE, c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE))
    r = c.post("/s4/chat", json={"text": "tạm trú cần giấy tờ gì", "websearch": True})
    assert r.status_code == 200, r.text
    cid = next(json.loads(l[6:])["conversation_id"] for l in r.text.splitlines() if l.startswith("data: ") and '"meta"' in l)
    assert calls == ["tạm trú cần giấy tờ gì"]
    sys_prompt = prompts[-1][0]["content"] + prompts[-1][-1]["content"]
    assert "TÌM WEB" in sys_prompt and "example.vn" in sys_prompt            # kết quả web đã vào lời dặn
    m = c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]
    assert m["meta"]["web"] and m["meta"]["sources"][0]["url"] == "https://example.vn/tam-tru", m["meta"]

    result.update(ev=[], err="ConnectError: mất mạng")                         # mất mạng: không lỗi, nói thật
    r = c.post("/s4/chat", json={"text": "hôm nay có tin gì", "websearch": True})
    assert r.status_code == 200 and '"error"' not in r.text, r.text
    assert "KHÔNG tìm thấy kết quả web" in (prompts[-1][0]["content"] + prompts[-1][-1]["content"])

    n = len(calls)                                                              # tắt nút: không tìm web
    c.post("/s4/chat", json={"text": "xin chào bạn khỏe không"})
    assert len(calls) == n
    # Strict: nút Tìm web thêm khối web dưới câu trả lời thủ tục (câu trả lời thủ tục giữ nguyên); không bật thì không có
    from core import websearch as core_web
    core_web.web_block = lambda q, n=5, t=8: ({"title": "Tra cứu thêm trên web", "text": "Theo web [1].", "sources": [{"label": "x", "url": "https://example.vn"}]}, {})
    q = "thông báo lưu trú mất bao lâu thì xong"
    off = c.post("/s4/strict/chat", json={"text": q}).json()
    on = c.post("/s4/strict/chat", json={"text": q, "websearch": True}).json()
    mo = c.get(f"/s4/strict/{off['conversation_id']}/messages").json()["messages"][-1]
    mn = c.get(f"/s4/strict/{on['conversation_id']}/messages").json()["messages"][-1]
    assert not any("web" in (b.get("title") or "") for b in mo["blocks"]), mo["blocks"]
    assert mn["blocks"][-1]["sources"][0]["url"] == "https://example.vn" and mn["blocks"][:-1] == mo["blocks"], mn["blocks"]
    # lớp bảo vệ: câu rác (suy luận tiếng Anh, lặp câu hỏi, đọc lại luật) bị chặn; câu thường qua
    Q = "thẻ căn cước bị hư muốn làm lại thì nộp lệ phí bao nhiêu"
    for bad in ("", "Okay, let's tackle this question.", "the can cuoc bi hu muon lam lai thi nop le phi bao nhieu /no_think",
                "Tôi cần trả lời bằng tiếng Việt, tối đa 6 câu và ghi số nguồn."):
        assert core_web.leaked(bad, Q), bad
    assert not core_web.leaked("Lệ phí làm lại thẻ căn cước là 70.000 đồng/thẻ [1].", Q)
    assert core_web.model_name() == "qwen3:4b-instruct-2507-q4_K_M"
print("OK test_websearch")

"""G3.3 (P15, D8): máy không có card đồ hoạ.
- Có GPU, công tắc tắt: câu Strict có điều kiện gọi bước LLM (AI giả chậm 2 s).
- Máy không GPU (S4_FORCE_CPU=1): Strict BỎ bước LLM, trả bản code < 0,5 s; /s4/public báo cpu_mode (giao diện hiện cảnh báo).
- Công tắc "Chỉ trả lời bằng luật" theo tài khoản: Strict bỏ LLM; Friendly báo đang ở chế độ chỉ luật, không gọi AI;
  tài khoản khác không bị ảnh hưởng.
- Ngắt mạch Ollama: 3 lỗi liên tiếp -> bỏ qua LLM 60 s (không gọi Ollama, không chờ).
Chạy: python run_server.py system4/tests/cpu_mode_test.py"""
import json, os, sys, tempfile, time
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="1", S4_ENABLED="1", S4_WARMUP="0", S3_NO_WARMUP="1",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
os.environ.pop("S4_FORCE_CPU", None)
from fastapi.testclient import TestClient
import main
from core import aihealth, llm as core_llm
from system3.system4.server import auth, chat as chat_mod, llm

calls = []


class SlowClient:
    def chat(self, **kw):
        calls.append(kw.get("model"))
        time.sleep(2.0)
        return {"message": {"content": json.dumps({"points": [{"text": "Giải thích điều kiện (AI giả).", "src": [1]}]})}}


core_llm.client = lambda timeout=None: SlowClient()
core_llm.loaded_models = lambda: [core_llm.model_name()]   # bước LLM của Strict chỉ gọi khi model "đã nạp" (llm_answer._ready)
stream_calls = []


async def fake_fast(messages, schema):
    stream_calls.append(1)
    raw = json.dumps({"plan": "", "answer": "AI trả lời.", "ask_back": False, "choices": []})
    yield raw


llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
aihealth.cpu_only = lambda max_age=30.0: os.environ.get("S4_FORCE_CPU") == "1"   # máy test có/không GPU: chỉ theo biến môi trường
Q = "Tôi ở nhà thuê thì đăng ký thường trú cần giấy tờ gì?"   # có điều kiện -> bước LLM của Strict (eval/cases_composer.jsonl)

with TestClient(main.app) as c:
    tok = {}
    for n in ("boss", "dan"):
        c.cookies.clear()
        tok[n] = c.post("/s4/auth/signup", json={"username": n, "password": "123456"}).cookies.get(auth.COOKIE)

    def as_user(n):
        c.cookies.clear(); c.cookies.set(auth.COOKIE, tok[n])

    def strict(q=Q):
        t = time.perf_counter()
        r = c.post("/s4/strict/chat", json={"text": q})
        assert r.status_code == 200, r.text
        return time.perf_counter() - t

    as_user("dan")
    # ---- có GPU, công tắc tắt: bước LLM chạy
    assert c.get("/s4/public").json()["cpu_mode"] is False
    dt = strict()
    assert calls and dt >= 2.0, (len(calls), dt)
    # ---- máy không GPU: Strict không chờ LLM
    os.environ["S4_FORCE_CPU"] = "1"
    n = len(calls)
    dt = strict()
    assert len(calls) == n and dt < 0.5, (len(calls) - n, dt)
    assert c.get("/s4/public").json()["cpu_mode"] is True
    info = c.get("/s4/account").json()
    assert info["ai"]["cpu_only"] is True and info["rules_only"] is False
    c.post("/s4/chat", json={"text": "Xin chào"})
    assert stream_calls, "Friendly vẫn dùng AI khi máy không GPU (chậm, có cảnh báo)"
    os.environ.pop("S4_FORCE_CPU")
    # ---- công tắc "Chỉ trả lời bằng luật" của tài khoản
    assert c.post("/s4/account/prefs", json={"rules_only": True}).json()["rules_only"] is True
    assert c.get("/s4/public").json()["rules_only"] is True
    n = len(calls)
    dt = strict()
    assert len(calls) == n and dt < 0.5, (len(calls) - n, dt)
    k = len(stream_calls)
    r = c.post("/s4/chat", json={"text": "Viết giúp mình một bài thơ"})
    assert len(stream_calls) == k and chat_mod.RULES_ONLY_MESSAGE[:40] in r.text, r.text[-300:]
    as_user("boss")   # tài khoản khác: vẫn dùng LLM
    n = len(calls)
    strict()
    assert len(calls) > n
    as_user("dan")
    c.post("/s4/account/prefs", json={"rules_only": False})
    n = len(calls)
    strict()
    assert len(calls) > n, "tắt công tắc: dùng lại AI"

# ---- ngắt mạch Ollama
class Broken:
    def chat(self, **kw):
        calls.append("broken")
        raise ConnectionError("Ollama tắt")


core_llm.client = lambda timeout=None: Broken()
aihealth.breaker.ok()
n = len(calls)
for _ in range(3):
    try:
        core_llm.chat("s", "u", timeout=1)
    except core_llm.LLMError:
        pass
assert len(calls) == n + 3 and aihealth.breaker.state()["open"]
t = time.perf_counter()
try:
    core_llm.chat("s", "u", timeout=1)
    raise AssertionError("phải bỏ qua")
except core_llm.LLMError as e:
    assert "tạm bỏ qua" in str(e) and time.perf_counter() - t < 0.1 and len(calls) == n + 3
aihealth.breaker.open_until = 0   # hết 60 s
core_llm.client = lambda timeout=None: SlowClient()
core_llm.chat("s", "u", timeout=5)
assert not aihealth.breaker.state()["open"]
print("OK cpu_mode_test")

"""G4.3: hồ sơ lĩnh vực (system4/server/profile.py). LLM giả + tìm kiếm giả, không gọi Ollama.
Hai lĩnh vực cấu hình khác nhau chạy đúng:
  A (cứng, mặc định grounded + bắt buộc trích dẫn; đổi: không hỏi lại, không tìm web, có vai trò riêng, top_k 3)
  B (mềm, mặc định free) — AI chung, không có lời dặn của A.
Kiểm: không có dữ liệu -> A không dùng kiến thức chung; thiếu [n] -> viết lại một lần; verbatim không gọi AI; Tìm web bị chặn ở A;
API kiểm hồ sơ (422), người dùng thường không sửa hồ sơ lĩnh vực cứng.
Chạy: python run_server.py system4/tests/profile_test.py"""
import json, os, sys, tempfile
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from fastapi.testclient import TestClient
import main
from system3.system4.server import auth, db, llm, profile, search, settings, websearch
import nv5_off
nv5_off.apply()

prompts, replies, search_calls, web_calls = [], [], [], []


async def fake_fast(messages, schema):
    prompts.append(messages)
    d = replies.pop(0) if replies else {"plan": "", "answer": "Câu trả lời của AI chung, khá dài để không bị coi là câu xã giao ngắn gọn nhé bạn.",
                                        "ask_back": False, "choices": []}
    yield json.dumps(d)


EVID = [{"id": 1, "title": "Quy chế nghỉ phép", "dataset": "Quy chế", "text": "Nhân viên được nghỉ 12 ngày phép mỗi năm.", "score": 0.9}]


def fake_search(user_id, query, dataset_ids=None, overrides=None):
    search_calls.append(overrides)
    return list(EVID), {"datasets": len(dataset_ids or []), "candidates": [], "search_ms": 1}


def fake_web(q, n=5, timeout=8):
    web_calls.append(q)
    return [], {"web": True}


llm.stream_json = fake_fast
llm.chat_json = lambda *a, **k: {}
search.search = fake_search
websearch.search = fake_web


def events(r):
    return [json.loads(l[6:]) for l in r.text.split("\n\n") if l.startswith("data: ")]


def system_of(i=-1):
    return "\n".join(m["content"] for m in prompts[i] if m["role"] == "system") + prompts[i][-1]["content"]


with TestClient(main.app) as c:
    tok = {}
    for n in ("devboss", "citizen"):
        c.cookies.clear()
        tok[n] = c.post("/s4/auth/signup", json={"username": n, "password": "123456"}).cookies.get(auth.COOKIE)
        assert tok[n], n

    def as_user(n):
        c.cookies.clear(); c.cookies.set(auth.COOKIE, tok[n])

    def chat(text, dom_id, **kw):
        r = c.post("/s4/chat", json={"text": text, "domain_id": dom_id, **kw})
        ev = events(r)
        assert ev, (r.status_code, r.text[:300])
        m = c.get(f"/s4/conversations/{ev[0]['conversation_id']}/messages").json()["messages"][-1]
        return ev, m

    as_user("devboss")
    A = c.post("/s4/domains", json={"name": "Nhân sự nội bộ", "kind": "hard"}).json()["domain"]
    B = c.post("/s4/domains", json={"name": "Góc trò chuyện", "kind": "soft"}).json()["domain"]
    assert A["profile"]["answer_mode"] == "grounded" and A["profile"]["require_citation"] is True, A["profile"]
    assert B["profile"]["answer_mode"] == "free" and B["profile"]["require_citation"] is False, B["profile"]
    # ---- API kiểm hồ sơ
    for bad in ({"answer_mode": "xyz"}, {"code_answer": True}, {"abc": 1}, {"retrieval": {"top_k": 99}}, {"tools": ["sql"]}):
        assert c.patch(f"/s4/domains/{A['id']}", json={"profile": bad}).status_code == 422, bad
    r = c.patch(f"/s4/domains/{A['id']}", json={"profile": {"clarify": False, "web_allowed": False, "persona": "Bạn là trợ lý nhân sự.",
                                                             "retrieval": {"top_k": 3}}})
    assert r.status_code == 200 and r.json()["domain"]["profile"]["clarify"] is False
    assert c.patch("/s4/domains/1", json={"profile": {"clarify": False}}).status_code == 422, "Thủ tục: không dùng hồ sơ"

    # ---- A không có dữ liệu: không dùng kiến thức chung (grounded)
    ev, m = chat("Công ty cho nghỉ phép bao nhiêu ngày?", A["id"])
    sp = system_of()
    assert "KHÔNG tìm thấy đoạn nào" in sp and "Bạn là trợ lý nhân sự." in sp and profile.NO_CLARIFY in sp, sp[-800:]
    assert m["content"] == settings.get("KB_NOT_FOUND_MESSAGE"), m["content"]
    # ---- B không có dữ liệu: AI chung, không có lời dặn của A
    ev, m = chat("Công ty cho nghỉ phép bao nhiêu ngày?", B["id"])
    sp = system_of()
    assert "Dữ liệu tham khảo" not in sp and "trợ lý nhân sự" not in sp and profile.NO_CLARIFY not in sp
    assert m["content"].startswith("Câu trả lời của AI chung")

    # ---- A có bộ dữ liệu: thiếu [n] -> viết lại một lần; top_k 3 truyền vào tìm kiếm
    owner = db.run("SELECT id FROM users WHERE username='devboss'", one=True)["id"]
    ds = db.create_dataset(owner, "Quy chế", "quyche.txt", 10, A["id"])
    db.update_dataset(ds, status="ready", active=1, n_records=1, kind="text")
    replies.extend([{"plan": "", "answer": "Nhân viên được nghỉ 12 ngày phép mỗi năm.", "ask_back": False, "choices": []},
                    {"plan": "", "answer": "Nhân viên được nghỉ 12 ngày phép mỗi năm [1].", "ask_back": False, "choices": []}])
    n = len(prompts)
    ev, m = chat("Nghỉ phép mấy ngày?", A["id"])
    assert len(prompts) == n + 2 and profile.CITE_RETRY in system_of() and profile.CITE in system_of(n), "viết lại vì thiếu nguồn"
    assert m["meta"].get("cite_retry") and not m["meta"].get("uncited") and m["meta"]["sources"][0]["title"] == "Quy chế nghỉ phép", m["meta"]
    assert search_calls[-1] == {"RETRIEVAL_TOP_K": 3}, search_calls[-1]
    # ---- Tìm web bị chặn ở A
    n = len(web_calls)
    ev, m = chat("Nghỉ phép mấy ngày?", A["id"], websearch=True)
    assert len(web_calls) == n and m["meta"].get("web_blocked") and "không dùng Tìm web" in m["content"]
    # ---- verbatim: không gọi AI, trích nguyên đoạn
    c.patch(f"/s4/domains/{A['id']}", json={"profile": {"answer_mode": "verbatim"}})
    n = len(prompts)
    ev, m = chat("Nghỉ phép mấy ngày?", A["id"])
    assert len(prompts) == n and "[1] Quy chế nghỉ phép" in m["content"] and "12 ngày phép" in m["content"] and m["meta"]["verbatim"]
    # ---- người dùng thường không sửa hồ sơ lĩnh vực cứng
    as_user("citizen")
    assert c.patch(f"/s4/domains/{A['id']}", json={"profile": {"answer_mode": "free"}}).status_code in (403, 404)
print("OK profile_test")

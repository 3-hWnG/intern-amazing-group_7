"""Phase 12: bộ nhớ/phiên. Không gọi LLM (planner chạy chỉ-luật). Chạy: python tests/memory_test.py"""
import json, os, subprocess, sys, tempfile, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
tmp = tempfile.mkdtemp()
os.environ["S3_DB_PATH"] = os.path.join(tmp, "s3.db")

import orchestrator
from db import store
from system3.data import api as data_api
from planner import plan as _plan

orchestrator.make_plan = lambda *a, **k: _plan(*a, use_llm=False, **k)   # không LLM
store.init_db()
KS, KH = "1.000689", "1.000894"        # khai sinh / kết hôn (khác family)
conn = data_api.connect()
cond = next(c["text"] for c in data_api.conditions(conn, KH) if len(c["text"].split()) >= 3)
cid = store.ensure_conversation(None)


def ask(text):
    t = orchestrator.Turn(cid, text, None, store.recent_history(cid), store.session_facts(cid), store.shown_procedures(cid))
    store.add_message(cid, "user", text)
    r = orchestrator.handle_turn(t)
    store.add_message(cid, "assistant", " ".join(b["text"] for b in r["blocks"]), r["kind"])
    return r


def conds(r):
    return [c for t in r["trace"].get("routed", {}).get("tasks", []) for c in t.get("conditions", [])]


# 10 lượt: khai sinh x3 -> kết hôn x3 -> reset bằng câu nói -> khai sinh -> reset câu lệnh+hỏi -> kết hôn
ask("Đăng ký khai sinh cần giấy tờ gì?")
store.add_fact(cid, "fact", cond, KS)                      # fact gắn với khai sinh, nội dung trùng điều kiện của kết hôn
ask("Còn lệ phí thì sao?")
ask("Mất bao lâu?")
assert len(store.session_facts(cid)) == 1
for q in ("Đăng ký kết hôn cần giấy tờ gì?", "Lệ phí kết hôn bao nhiêu?"):
    r = ask(q)
    assert cond not in conds(r), "fact khai sinh rò sang kết hôn"
ask("Thời hạn giải quyết bao lâu?")
assert orchestrator._facts_for(conn, store.session_facts(cid), [KS]) == [cond]      # còn hiệu lực với đúng family
assert orchestrator._facts_for(conn, store.session_facts(cid), [KH]) == []          # hết hạn với family khác
r = ask("Quên đi, hỏi việc khác nhé")
assert r["trace"].get("reset") and store.session_facts(cid) == [] and store.shown_procedures(cid) == []
store.add_fact(cid, "fact", "tôi ở nước ngoài", KS)
ask("Đăng ký khai sinh cần giấy tờ gì?")
r = ask("Chủ đề khác: đăng ký kết hôn cần giấy tờ gì?")
assert not r["trace"].get("reset") and store.session_facts(cid) == []
ask("Lệ phí bao nhiêu?")
store.add_fact(cid, "fact", "x", KH); store.reset_session(cid)
assert store.session_facts(cid) == []

# migration DB cũ thiếu cột proc_id
import sqlite3
p = os.path.join(tmp, "old.db"); c = sqlite3.connect(p)
c.executescript("CREATE TABLE session_facts(conversation_id TEXT, kind TEXT, text TEXT, created_at TEXT, PRIMARY KEY(conversation_id,kind,text));")
c.commit(); c.close()
import db.store as st; st.DB_PATH = type(st.DB_PATH)(p); st.init_db()
assert "proc_id" in [r[1] for r in sqlite3.connect(p).execute("PRAGMA table_info(session_facts)")]
st.DB_PATH = type(st.DB_PATH)(os.path.join(tmp, "s3.db"))

# endpoint: reset_facts, dev 404 khi S3_DEV tắt / 200 khi bật
PORT = 8393


def run(dev):
    env = dict(os.environ, APP_PORT=str(PORT), S3_DEV=dev, PYTHONIOENCODING="utf-8")
    srv = subprocess.Popen([sys.executable, "main.py"], cwd=HERE, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2); break
        except Exception:
            time.sleep(1)
    return srv


def code(path, method="GET"):
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", method=method, data=b"{}" if method == "POST" else None)
        return urllib.request.urlopen(req, timeout=30).status, None
    except urllib.error.HTTPError as e:
        return e.code, None


for dev in ("0", "1"):
    srv = run(dev)
    try:
        if dev == "0":
            assert code("/dev/default_variants")[0] == 404 and code("/dev/variants.html")[0] == 404
        else:
            assert code("/dev/default_variants")[0] == 200
            g = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/dev/default_variants"))["groups"]
            assert len(g) == 84 and all(x["default"] for x in g), len(g)
            store.add_fact(cid, "fact", "y", KS)
            assert code(f"/conversations/{cid}/reset_facts", "POST")[0] == 200
            assert code("/conversations/nope/reset_facts", "POST")[0] == 404
            assert store.session_facts(cid) == []
    finally:
        srv.terminate(); srv.wait()
print("OK")

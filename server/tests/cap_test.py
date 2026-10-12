"""Giới hạn bộ nhớ Strict (kế hoạch tuần tới 2a): thủ tục nhớ <= SHOWN_MAX, ngữ cảnh <= HISTORY_MESSAGES tin, turn_traces <= TRACE_KEEP.
Chạy: python run_server.py server/tests/cap_test.py"""
import os, sys, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ["S3_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "s3.db")
os.environ["S3_TRACE_KEEP"] = "3"
from db import store
store.init_db()
cid = store.ensure_conversation(None)
for i in range(5):
    store.add_shown(cid, f"p{i}", f"thu tuc {i}")
assert [s["proc_id"] for s in store.shown_procedures(cid)] == ["p3", "p4"], store.shown_procedures(cid)
store.add_shown(cid, "p4", "x")   # nhắc lại cái đang có: không đổi
assert len(store.shown_procedures(cid)) == 2
for i in range(6):
    store.add_message(cid, "user" if i % 2 == 0 else "assistant", f"m{i}")
assert [m["content"] for m in store.recent_history(cid)] == ["m3", "m4", "m5"]
assert len(store.get_messages(cid)) == 6        # tin cũ vẫn hiển thị được
mids = [m["id"] for m in store.get_messages(cid)]
for m in mids:
    store.add_trace(cid, m, {"a": 1}, 1)
n = store._run("SELECT COUNT(*) c FROM turn_traces", one=True)["c"]
assert n == 3, n
print("OK cap_test")

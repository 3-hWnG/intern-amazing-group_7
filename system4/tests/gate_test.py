"""G2.4 (P07): cổng kiểm khi Áp dụng phiên bản dữ liệu thủ tục.
- so hai DB trên phần ca chấm được ở cả hai; tụt > 3 điểm top-1 hoặc hành vi -> chặn
- bị chặn thì con trỏ (phiên bản đang dùng) KHÔNG đổi; qua cổng thì đổi, kết quả ghi vào manifest
- chạy thật mẫu golden trên cùng một DB: không tụt
Chạy: python run_server.py system4/tests/gate_test.py"""
import os, sys, tempfile
from pathlib import Path
SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")
from system3.system4.server import db, procs, procs_gate

# ---- logic so sánh (mẫu giả)
def fake(beh, top):
    cases = {f"c{i}": [i < beh, (i < top) if i < 100 else None] for i in range(120)}
    return {"n": 120, "behavior": beh, "n_top1": 100, "top1": top, "cases": cases, "answers": {k: str(v) for k, v in cases.items()}}

real_sample = procs_gate.sample
res = iter([fake(110, 90), fake(110, 86)])
procs_gate.sample = lambda db: next(res)
r = procs_gate.gate(Path("a"), Path("b"))
assert not r["ok"] and r["drop_top1_pts"] == 4.0 and "top-1 tụt" in r["reason"], r
res = iter([fake(110, 90), fake(107, 88)])
r = procs_gate.gate(Path("a"), Path("b"))
assert r["ok"] and r["drop_behavior_pts"] == 2.5, r
procs_gate.sample = real_sample

# ---- bị chặn thì không đổi bản đang dùng
db.init_db()
procs.ensure_active()
v0 = procs.active_id()
recs, _ = procs.load(v0)
v1 = procs._new_version(recs[:-1], "thử", "edit", v0)
procs.gate_fn = lambda cur, new: {"ok": False, "reason": "giả lập tụt"}
try:
    procs.apply(v1, wait=True)
    raise AssertionError("phải bị chặn")
except RuntimeError as e:
    assert "Cổng kiểm chặn" in str(e)
assert procs.active_id() == v0 and procs.manifest()["versions"][str(v1)]["gate"]["ok"] is False
procs.gate_fn = lambda cur, new: {"ok": True}
procs.apply(v1, wait=True)
assert procs.active_id() == v1 and procs.previous_id() == v0

# ---- chạy thật: cùng một DB -> không tụt, 0 câu trả lời đổi
r = procs_gate.gate(procs.db_path_of(v0), procs.db_path_of(v0))
assert r["ok"] and r["drop_top1_pts"] == 0 and r["answers_changed"] == 0 and r["common_cases"] >= 140, {k: r[k] for k in ("ok", "common_cases", "answers_changed")}
print("OK gate_test")

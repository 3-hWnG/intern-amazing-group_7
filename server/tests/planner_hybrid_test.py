"""Phase 19: cơ chế hợp nhất Planner hybrid với LLM GIẢ (không gọi Ollama).
Chạy: S3_USE_LLM=0 PYTHONPATH=D:/Finale_architect python tests/planner_hybrid_test.py"""
import os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.pop("S3_PLANNER_LLM_CACHE", None)        # không phát lại cache đo
from planner import plan
from planner import hybrid
from policy import check
from system3.data import api

KT, TACH, KS = "1.000656", "1.010038", "1.001193"
conn = api.connect()
U = lambda q: [{"role": "user", "text": q}]
hybrid.set_config(mode="hybrid", confidence=0.95, timeout=7.0)


def fake(tasks, conf=0.99, clarify=False):
    """LLM giả: tasks = [(cần_chứa_trong_nhãn_ứng_viên|None|-2, [fields], action)]; tìm chỉ số `cand` trong danh sách ứng viên của prompt."""
    def f(system, msg, **kw):
        lab = {}
        for line in msg.splitlines():
            if line[:1].isdigit() and ". " in line:
                lab[int(line.split(". ", 1)[0])] = line.split(". ", 1)[1].lower()
        out = []
        for key, fields, act in tasks:
            c = key if isinstance(key, int) else next((i for i, l in lab.items() if key in l), -1)
            out.append({"action": act, "cand": c, "fields": fields})
        return {"tasks": out, "clarify": clarify, "confidence": conf}
    return f


def run(q, llm, **kw):
    p = plan(U(q), llm_chat_json=llm, mode="hybrid", **kw)
    return p, p.llm_trace


def pids(p):
    return [t.procedure_id for t in p.tasks]


# 0) mode rules: không gọi LLM, không có nhật ký
def never(*a, **k): raise AssertionError("không được gọi LLM ở mode rules")
p = plan(U("khai tử mất bao lâu"), llm_chat_json=never, mode="rules")
assert p.llm_trace == {} and pids(p) == [KT] and p.tasks[0].fields == ["processing_time"]

# 1) LLM đồng ý với luật -> không đề xuất gì, kế hoạch y nguyên
p, tr = run("khai tử mất bao lâu", fake([("khai tử", ["processing_time"], "ask_field")]))
assert tr["called"] and tr["proposals"] == [] and tr["decision"] == "none" and pids(p) == [KT], tr

# 2) đề xuất ĐÚNG (bỏ task thừa) + confidence cao -> chấp nhận. Luật thấy 2 ý, LLM nói 1 ý.
q2 = "tách hộ lệ phí bao nhiêu, còn khai tử thì sao"
base = plan(U(q2), mode="rules")
assert len(base.tasks) == 2, [t.procedure_id for t in base.tasks]
p, tr = run(q2, fake([("tách hộ", ["fees"], "ask_field")], conf=0.99))
assert [o["op"] for o in tr["proposals"]] == ["delete_task"] and tr["proposals"][0]["accepted"] and len(p.tasks) == 1 and tr["decision"] == "accepted", tr
assert tr["final_plan"][0]["proc"] == TACH and tr["rule_plan"][0]["proc"] == TACH and len(tr["rule_plan"]) == 2   # nhật ký giữ cả kế hoạch luật lẫn kế hoạch cuối

# 3) cùng đề xuất nhưng confidence dưới ngưỡng -> từ chối, giữ luật
p, tr = run(q2, fake([("tách hộ", ["fees"], "ask_field")], conf=0.80))
assert len(p.tasks) == 2 and tr["decision"] == "rejected" and "ngưỡng" in tr["proposals"][0]["reason"], tr
hybrid.set_config(confidence=0.7)            # ngưỡng đổi trong bộ nhớ có tác dụng ngay
p, tr = run(q2, fake([("tách hộ", ["fees"], "ask_field")], conf=0.80))
assert len(p.tasks) == 1 and tr["decision"] == "accepted", tr
hybrid.set_config(confidence=0.95)

# 4) sửa mục: hợp lệ + cao -> nhận (quantity cập nhật); mục lạ / rỗng / quá nhiều -> từ chối
p, tr = run("khai tử mất bao lâu", fake([("khai tử", ["fees"], "ask_field")]))
assert p.tasks[0].fields == ["fees"] and p.tasks[0].quantity == "amount" and tr["proposals"][0]["op"] == "edit_fields" and tr["proposals"][0]["accepted"], tr
for bad in (["fees", "xyz"], [], ["components", "fees", "processing_time", "address", "steps"]):
    p, tr = run("khai tử mất bao lâu", fake([("khai tử", bad, "ask_field")]))
    assert p.tasks[0].fields == ["processing_time"] and tr["decision"] == "rejected", (bad, tr)

# 5) LLM chọn chỉ số không có trong danh sách / -1 -> không tạo thủ tục, giữ luật
for c in (99, -1):
    p, tr = run("khai tử mất bao lâu", fake([(c, ["processing_time"], "ask_field")]))
    assert pids(p) == [KT] and tr["proposals"] == [], tr

# 6) LLM thêm task bằng thủ tục thật trong danh sách ứng viên (đề xuất kiểu 'thêm ý') -> qua kiểm thì nhận
p, tr = run("khai tử mất bao lâu", fake([("khai tử", ["processing_time"], "ask_field"), ("khai sinh", ["processing_time"], "ask_field")]))
ops = tr["proposals"]
assert (not ops) or all(o["op"] == "add_task" for o in ops), tr          # khai sinh có thể không nằm trong ứng viên của câu này
if ops:
    assert ops[0]["accepted"] and len(p.tasks) == 2 and p.tasks[1].procedure_id == ops[0]["to"], tr

# 7) hết hạn / lỗi / JSON hỏng -> giữ luật, ghi lý do
hybrid.set_config(timeout=0.5)
def slow(system, msg, **kw):
    time.sleep(1.6); return fake([("khai tử", ["fees"], "ask_field")])(system, msg)
t0 = time.perf_counter()
p, tr = run("khai tử mất bao lâu", slow)
assert tr["timeout"] and tr["decision"] == "none" and p.tasks[0].fields == ["processing_time"] and time.perf_counter() - t0 < 1.4, (tr, time.perf_counter() - t0)
hybrid.set_config(timeout=7.0)
def boom(system, msg, **kw): raise RuntimeError("Ollama sập")
for f in (boom, lambda s, m, **k: {}, lambda s, m, **k: {"tasks": []}, lambda s, m, **k: {"tasks": "x"}):
    p, tr = run("khai tử mất bao lâu", f)
    assert tr["called"] and tr["decision"] == "none" and pids(p) == [KT] and p.tasks[0].fields == ["processing_time"], tr

# 8) LUẬT/POLICY quyết xin lỗi / hỏi lại / ngoài phạm vi -> LLM không lật được
p, tr = run("hôm nay thời tiết thế nào", fake([("khai tử", ["fees"], "ask_field")], conf=1.0))
assert not any(o["accepted"] for o in tr.get("proposals", [])) and all(t.procedure_id is None for t in p.tasks), tr
p, tr = run("thủ tục hộ tịch", fake([("khai tử", ["fees"], "ask_field")], conf=1.0))
r = check(p, user_text="thủ tục hộ tịch", conn=conn)
assert r.behavior == "clarify" and not any(o["accepted"] for o in tr.get("proposals", [])), (r.behavior, tr)

# 9) edit_proc: LLM đổi sang thủ tục khác trong danh sách. Chỉ nhận khi confidence cao; bị khoá khi thủ tục do ngữ cảnh kế thừa
q9 = "đăng ký kết hôn cần giấy tờ gì"
base = plan(U(q9), mode="rules")
alt = next((c for c in base.tasks[0].candidates if c != base.tasks[0].procedure_id), None)
if alt:
    lab = conn.execute("select name from procedures where proc_id=?", (alt,)).fetchone()[0].lower()[:60]
    p, tr = run(q9, fake([(lab, ["components"], "ask_field")], conf=0.5))
    assert pids(p) == pids(base) and (not tr["proposals"] or not tr["proposals"][0]["accepted"]), tr
    p, tr = run(q9, fake([(lab, ["components"], "ask_field")], conf=0.99))
    assert not tr["proposals"] or tr["proposals"][0]["op"] == "edit_proc", tr          # cho phép, miễn là qua kiểm
h = [{"role": "user", "text": "đăng ký khai sinh"}, {"role": "assistant", "text": "ok"}, {"role": "user", "text": "lệ phí bao nhiêu"}]
p = plan(h, llm_chat_json=fake([(0, ["fees"], "ask_field")]), mode="hybrid")
assert p.tasks[0].refers_to == "last" and pids(p) == [KS] and not any(o["accepted"] for o in p.llm_trace.get("proposals", [])), p.llm_trace

# 10) cấu hình
c = hybrid.set_config(mode="rules")
assert c["mode"] == "rules"
for kw in ({"mode": "x"}, {"confidence": 2}, {"timeout": 99}):
    try:
        hybrid.set_config(**kw); raise SystemExit("phải ValueError")
    except ValueError:
        pass
print("planner_hybrid_test OK")

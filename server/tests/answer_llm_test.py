"""Phase 11: LLM giả (không gọi Ollama). Chạy: PYTHONPATH=D:/Finale_architect python tests/answer_llm_test.py"""
import os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from answer import answer
from answer.llm_answer import compose
from policy.policy import Routed, RoutedTask
from system3.data import api

P = [{"label": "Lệ phí", "text": "Lệ phí 50.000 đồng theo Nghị định 120/2020/NĐ-CP."},
     {"label": "Thời hạn", "text": "Thời hạn giải quyết 05 ngày làm việc."}]
mk = lambda *pts: (lambda s, u, **k: {"points": list(pts)})
ok = lambda ps: compose(mk(*ps), P, "x")

# (a) hợp lệ được giữ
good = [{"text": "Lệ phí là 50.000 đồng.", "cites": ["d1"]}, {"text": "Thời hạn 5 ngày làm việc.", "cites": ["d2"]},
        {"text": "Căn cứ Nghị định 120/2020/NĐ-CP.", "cites": ["[d1]"]}]
assert len(ok(good)) == 3, ok(good)

# (b) bịa -> chặn 100%
bad = [{"text": "Lệ phí là 80.000 đồng.", "cites": ["d1"]},                    # bịa số
       {"text": "Thời hạn 5 ngày, theo Thông tư 99/2021/TT-BTC.", "cites": ["d2"]},   # bịa văn bản
       {"text": "Căn cứ Nghị định 120/2020/NĐ-CP.", "cites": ["d2"]},            # trích sai đoạn
       {"text": "Thủ tục này miễn phí.", "cites": ["d2"]},                       # miễn phí khi dữ liệu không nói
       {"text": "Thủ tục này không mất phí.", "cites": ["d1"]},
       {"text": "Lệ phí là 50.000 đồng.", "cites": []},                          # không cites
       {"text": "Lệ phí là 50.000 đồng."},                                       # thiếu cites
       {"text": "Lệ phí là 50.000 đồng.", "cites": ["d9"]},                      # id không tồn tại
       {"text": "Theo Luật Đất đai.", "cites": ["d1"]}, "rác", {"cites": ["d1"]}]
for chunk in (bad[:5], bad[5:]):
    iss = []
    assert compose(mk(*chunk), P, "x", issues=iss) == [] and len(iss) == len(chunk), iss

# (c) lỗi / timeout / rác -> []
def boom(s, u, **k): raise TimeoutError("hết giờ")
for f in (boom, lambda s, u, **k: {}, lambda s, u, **k: {"points": "x"}, None):
    assert compose(f, P, "x") == []

# end-to-end: có điều kiện + so sánh; LLM lỗi => khớp kết quả không-LLM
conn = api.connect()
t = lambda pid, **kw: RoutedTask(route="direct", procedure_id=pid, procedure_label="TT " + pid, fields=["processing_time"], **kw)
def run(llm):
    r = Routed(tasks=[t("1.000005", conditions=["người khuyết tật"], relation="compare"), t("1.000020", relation="compare")])
    return answer(r, conn=conn, question="so sánh", llm=llm)
base = run(None)
assert run(boom) ["blocks"] == base["blocks"]
fake = mk({"text": "Thủ tục thứ hai thu lệ phí 123456 đồng.", "cites": ["d1"]})
assert run(fake)["blocks"] == base["blocks"]                                  # bịa số -> fallback nguyên vẹn
ev = base["blocks"][0]["text"]
d1 = {"text": "Có nêu thời hạn giải quyết ở trên.", "cites": ["d1"]}
res = run(mk(d1))
assert res["blocks"][0]["text"].count("(theo:") == 1 and res["blocks"][-1]["title"] == "So sánh"
print("OK answer_llm_test")

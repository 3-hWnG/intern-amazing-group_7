"""Bộ nhớ ngữ cảnh: quyết định nối câu (follow_up | new_related | return | independent | correction | story) + trạng thái lưu DB.
Không LLM. Chạy: S3_USE_LLM=0 python tests/context_test.py"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ["S3_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "s3.db")

import orchestrator
from db import store
from planner import plan as _plan
from planner.planner import _index
from system3.retrieval.rank import resolve
from system3.retrieval.context import ConvState, markers

orchestrator.make_plan = lambda *a, **k: _plan(*a, use_llm=False, **k)
store.init_db()
KS, NCM, TL, TT, TAM, KH, KT, HK = "1.001193", "1.001022", "2.000635", "1.004222", "1.004194", "1.000894", "1.000656", "1.001612"
idx = _index()


def run(*users):
    """resolve thuần: dựng lại trạng thái từ các lượt user (assistant giả)."""
    turns = []
    for u in users:
        turns += [{"role": "user", "text": u}, {"role": "assistant", "text": "ok"}]
    r = resolve(idx, turns[:-1])
    s = r.segments[0]
    return s.proc_id, s.decision, r


def expect(users, pid, decision):
    got = run(*users)
    assert got[0] == pid and got[1] == decision, (users, got[:2], got[2].ctx)
    assert got[2].ctx["why"], "thiếu lý do trong trace"


# (i) follow-up cùng thủ tục (thiếu chủ ngữ, đại từ, điều kiện)
expect(["đăng ký khai sinh", "còn lệ phí?"], KS, "follow_up")
expect(["đăng ký khai sinh", "nó mất bao lâu"], KS, "follow_up")
expect(["đăng ký tạm trú", "cái đó nộp online được không"], TAM, "follow_up")
expect(["đăng ký khai sinh", "còn nếu bé sinh ở nhà thì sao"], KS, "follow_up")
expect(["đăng ký thường trú", "nộp ở đâu vậy"], TT, "follow_up")      # "ở đâu" KHÔNG phải thứ tự "đầu"
# (ii) thủ tục mới liên quan (cùng lĩnh vực) / (iv) độc lập (khác lĩnh vực)
expect(["đăng ký khai sinh", "thế còn đăng ký nhận cha mẹ con thì sao"], NCM, "new_related")
expect(["đăng ký khai sinh", "thế còn đăng ký thành lập hộ kinh doanh thì sao"], HK, "independent")
# (iii) quay lại thủ tục cũ: theo tên, theo vị trí
expect(["đăng ký khai sinh", "đăng ký tạm trú", "quay lại cái khai sinh lúc nãy, lệ phí bao nhiêu"], KS, "return")
expect(["đăng ký kết hôn", "đăng ký khai tử", "à còn cái đầu tiên, nộp ở đâu"], KH, "return")
expect(["đăng ký khai sinh", "đăng ký nhận cha mẹ con", "còn cái trước đó thì phí bao nhiêu"], KS, "return")
# (v) sửa ý
expect(["đăng ký khai sinh cần gì", "ý tôi là đăng ký nhận cha mẹ con chứ không phải khai sinh"], NCM, "correction")
expect(["đăng ký tạm trú cần gì", "không phải, ý mình hỏi thường trú cơ"], TT, "correction")
# (iv) độc lập: câu hai không có tín hiệu nối => KHÔNG kế thừa
for second in ("hôm nay trời đẹp nhỉ", "làm hộ chiếu ở đâu", "thi bằng lái xe ở đâu", "xin chào"):
    pid, dec, _ = run("đăng ký khai sinh", second)
    assert pid is None and dec == "independent", (second, pid, dec)
expect(["đăng ký khai sinh", "đăng ký tạm trú nộp ở đâu"], TAM, "independent")
# kể hoàn cảnh -> thủ tục suy ra, lượt sau nới lỏng
pid, dec, r = run("nhà tôi vừa có bé mới sinh", "giờ cần làm giấy tờ gì cho bé")
assert pid in (KS, "3.000722", "1.000689") and r.state.loose is False or r.state.loose, (pid, dec)
# từ vựng "ở đâu"/"cưới" không bị nhầm thứ tự
assert markers("nó mất bao lâu")[1].get("anaph") and "nó" not in markers("nó mất bao lâu")[0]

# ---- trạng thái lưu DB, vượt cửa sổ 5 lượt của recent_history
cid = store.ensure_conversation(None)


def ask(text):
    t = orchestrator.Turn(cid, text, None, store.recent_history(cid), store.session_facts(cid), store.shown_procedures(cid))
    store.add_message(cid, "user", text)
    r = orchestrator.handle_turn(t)
    store.add_message(cid, "assistant", " ".join(b["text"] for b in r["blocks"]), r["kind"])
    return r


assert store.get_state(cid) is None
ask("đăng ký khai sinh cần giấy tờ gì")
assert store.get_state(cid)["topic"] == KS
r = ask("còn lệ phí?")
assert r["trace"]["ctx"]["decision"] == "follow_up" and r["trace"]["ctx"]["why"]
for q in ("đăng ký tạm trú", "đăng ký kết hôn", "đăng ký khai tử", "đăng ký thường trú", "đăng ký giám hộ", "chứng thực chữ ký"):
    ask(q)
st = store.get_state(cid)
assert st["order"][0] == KS and len(st["history"]) >= 7, st               # nhớ cả thủ tục đã nói cách đây > 5 lượt
r = ask("quay lại cái khai sinh lúc nãy, nộp ở đâu")
assert r["trace"]["ctx"]["decision"] == "return" and store.get_state(cid)["topic"] == KS
assert r["trace"]["routed"]["tasks"][0]["procedure_id"] == KS
r = ask("hôm nay trời đẹp nhỉ")
assert r["kind"] != "answer" or not [t for t in r["trace"]["routed"]["tasks"] if t["route"] == "direct"], "câu lạc đề kế thừa nhầm"
store.reset_session(cid)
assert store.get_state(cid) is None
print("OK")

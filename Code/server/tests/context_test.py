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

# ---- bảng sự kiện đời sống: mọi cụm gợi ý phải ra một thủ tục CÓ trong kho (bảng không được mục dần), và câu kể điển hình khớp đúng sự kiện
from system3.retrieval.context import EVENTS, event_hints
for _rx, _hint in EVENTS:
    _s = resolve(idx, [{"role": "user", "text": _hint}]).segments[0]
    assert _s.proc_id, ("cụm gợi ý không ra thủ tục nào", _hint)
for _txt, _want in [("chồng em vừa mất", "khai tử"), ("nhà em có người vừa mất", "khai tử"), ("con tôi sắp vào lớp 6", "trung học cơ sở"),
                    ("bé nhà mình mới sinh", "khai sinh"), ("bà tôi hơn 80 tuổi không có lương hưu", "hưu trí"), ("bị tai nạn khi đi làm", "tai nạn lao động")]:
    assert _want in event_hints(_txt)[0], (_txt, event_hints(_txt))
for _txt in ("mất giấy khai sinh", "tôi mất việc", "mẹ mất hộ chiếu", "đăng ký khai sinh"):
    assert not event_hints(_txt)[0] or "khai tử" not in event_hints(_txt)[0], (_txt, event_hints(_txt))

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
# ---- thẻ hỏi lại -> "cái thứ n" chọn đúng lựa chọn của THẺ (không phải danh sách đã trả lời trước đó); không hỏi lần hai
cid2 = store.ensure_conversation(None)


def ask2(text, reply_to_clarify=None):
    t = orchestrator.Turn(cid2, text, None, store.recent_history(cid2), store.session_facts(cid2), store.shown_procedures(cid2), reply_to_clarify)
    store.add_message(cid2, "user", text)
    r = orchestrator.handle_turn(t)
    store.add_message(cid2, "assistant", orchestrator.flat_text(r), r["kind"])
    return r


ask2("đăng ký khai sinh")                                 # có danh sách đã trả lời trước (không được lẫn với thẻ)
r = ask2("giấy phép lao động cho người nước ngoài")        # >= 3 bản gần nhau (cấp / cấp lại / gia hạn), không nói loại
assert r["kind"] == "clarify" and len(r["clarify"]["options"]) >= 3, r["kind"]
opts = r["clarify"]["options"]
assert store.recent_history(cid2)[-1]["content"].count(") ") >= 3, "thẻ hỏi lại phải lưu danh sách đánh số vào lịch sử"
r = ask2("cái thứ hai")
assert r["kind"] == "answer" and r["trace"]["routed"]["tasks"][0]["procedure_label"][:25] == opts[1][:25], (r["kind"], opts)
r = ask2("còn phí?")
assert r["trace"]["routed"]["tasks"][0]["procedure_label"][:25] == opts[1][:25] and r["trace"]["ctx"]["decision"] == "follow_up"
# ---- trả lời thẻ bằng ô gõ tự do: chọn bản gần nhất theo câu gõ; trả lời mơ hồ cũng KHÔNG hỏi lần hai (lấy ứng viên đầu, nói rõ giả định)
r = ask2("giấy phép lao động cho người nước ngoài")
assert r["kind"] == "clarify"
card = r["clarify"]
r2 = ask2("gia hạn", card)
assert r2["kind"] == "answer" and "Gia hạn" in r2["trace"]["routed"]["tasks"][0]["procedure_label"][:12], r2["trace"]["routed"]["tasks"]
r3 = ask2("cái nào cũng được", card)
assert r3["kind"] != "clarify" and r3["trace"]["routed"]["tasks"][0]["route"] == "direct"
store.reset_session(cid)
st = store.get_state(cid)
assert st is not None and st["topic"] is None and not st["history"], st   # trạng thái RỖNG (None thì resolve dựng lại từ lịch sử)

# ---- Phase 18: mục được hỏi, task thừa, nhóm chung quá rộng, hoàn cảnh -> đúng phần giấy tờ của trường hợp
def tasks(r):
    return [t for t in r["trace"]["routed"]["tasks"] if t["route"] == "direct"]


cid3 = store.ensure_conversation(None)
for q, fields in (("Tách hộ mất bao lâu thì xong ạ?", ["processing_time"]),                          # A: chỉ báo thời hạn
                  ("Nếu tôi từng ly hôn thì đăng ký kết hôn cần giấy tờ gì thêm?", ["components"]),   # A: câu điều kiện -> hồ sơ, không 4 mục mặc định
                  ("Mình đang ở trọ, muốn đăng ký tạm trú thì giải quyết trong bao lâu?", ["processing_time"]),   # B: cụm 'giải quyết trong bao lâu' không thành task thứ hai
                  ("Con tôi vừa tròn 1 tháng tuổi, tôi cần làm giấy khai sinh, giấy tờ gồm những gì?", ["components"])):
    t = tasks(orchestrator.handle_turn(orchestrator.Turn(store.ensure_conversation(None), q)))
    assert len(t) == 1 and t[0]["fields"] == fields, (q, [(x["procedure_label"], x["fields"]) for x in t])
r = orchestrator.handle_turn(orchestrator.Turn(store.ensure_conversation(None), "thủ tục hộ tịch"))      # C: chỉ nêu lĩnh vực -> hỏi lại bằng thẻ
assert r["kind"] == "clarify" and len(r["clarify"]["options"]) >= 3, r["kind"]
r = orchestrator.handle_turn(orchestrator.Turn(store.ensure_conversation(None), "Em là bộ đội ở trong doanh trại, đăng ký tạm trú cần giấy tờ gì?"))   # D
txt = " ".join(b["text"] for b in r["blocks"])
assert "đơn vị đóng quân" in txt and "Theo trường hợp bạn nêu" in txt and len(txt) < 2500, txt[:300]
print("OK")

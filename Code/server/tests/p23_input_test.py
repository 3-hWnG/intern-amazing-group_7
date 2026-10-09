"""Phase 23: bỏ nhãn lượt/đệm đầu câu, tách chữ dính liền + teencode, chữ lạ không đổi hướng, điều kiện không sinh task thừa. Không LLM.
Chạy: S3_USE_LLM=0 python tests/p23_input_test.py"""
import os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.setdefault("S3_USE_LLM", "0")

from planner.planner import _index
from system3.retrieval import query as Q
from system3.retrieval.context import strip_labels
from system3.retrieval.rank import resolve
from policy import pre_check

KH, KS, KT, TT, TACH = "1.000894", "1.001193", "1.000656", "1.004194", "1.010038"
idx = _index()

# ---- (1) nhãn lượt / số thứ tự / gạch đầu dòng / emoji / ngoặc kép / lời đệm
for raw, want in [
    ("Turn 2: Vậy thời gian giải quyết và lệ phí như thế nào?", "Vậy thời gian giải quyết và lệ phí như thế nào?"),
    ("Turn 1: User: đăng ký kết hôn", "đăng ký kết hôn"), ("Câu 2: còn lệ phí?", "còn lệ phí?"), ("Q: phí bao nhiêu", "phí bao nhiêu"),
    ("User: tách hộ", "tách hộ"), ("Bạn: tách hộ", "tách hộ"), ("Hỏi: tách hộ", "tách hộ"), ("Lượt 2 - tách hộ", "tách hộ"),
    ("2) tách hộ", "tách hộ"), ("2. tách hộ", "tách hộ"), ("- tách hộ", "tách hộ"), ("> tách hộ", "tách hộ"), ("[User] tách hộ", "tách hộ"),
    ("(Turn 2) tách hộ", "tách hộ"), ("**Q:** tách hộ", "tách hộ"), ("“Tách hộ cần gì?”", "Tách hộ cần gì?"), ("🙏 tách hộ 😊", "tách hộ"),
    ("tách \n  hộ", "tách hộ"), ("Dạ cho em hỏi tách hộ ạ", "tách hộ"), ("Ad ơi tách hộ nhé", "tách hộ"),
    # KHÔNG được cắt nhầm
    ("Câu 2 là gì", "Câu 2 là gì"), ("1.000656 phí bao nhiêu", "1.000656 phí bao nhiêu"), ("2 tháng nữa tôi cần làm gì", "2 tháng nữa tôi cần làm gì"),
    ("Chào bạn, mình hỏi chút được hông", "Chào bạn, mình hỏi chút được hông"), ("Turn:", "Turn:"),
]:
    assert strip_labels(raw) == want, (raw, strip_labels(raw))
assert strip_labels("Bot: 1) A 2) B", "assistant") == "1) A 2) B" and strip_labels("1) A 2) B", "assistant") == "1) A 2) B"
assert pre_check("Turn 2: Vậy lệ phí?")["text"] == "Vậy lệ phí?"

# ---- (2) tách chữ dính: không dấu / có dấu / từng cụm / teencode; chữ nước ngoài không bị tách
for raw, want in [("kethon", "ket hon"), ("dangkykhaisinh", "dang ky khai sinh"), ("dangkytamtru", "dang ky tam tru"), ("đăngkýkhaisinh", "đăng ký khai sinh"),
                  ("muondangkykethon", "muon dang ky ket hon"), ("hotrochiphiyteva", "ho tro chi phi y te va"), ("Ghivào", "Ghi vào")]:
    assert Q.unglue_text(raw) == want, (raw, Q.unglue_text(raw))
for foreign in ["karaoke", "bitcoin", "iphone", "facebook", "samsung", "tiktok", "wifi", "youtube", "messenger", "banhmi", "đăng ký", "ket hon"]:
    assert Q.unglue_text(foreign) == foreign, (foreign, Q.unglue_text(foreign))


def top(text, *prev):
    turns = []
    for p in prev:
        turns += [{"role": "user", "text": p}, {"role": "assistant", "text": "ok"}]
    r = resolve(idx, turns + [{"role": "user", "text": text}])
    return r.segments[0].proc_id, r


for q, pid in [("t muon đk kethon", KH), ("muon dang ky kethon", KH), ("t muon dk ket hon", KH), ("đk kết hôn", KH), ("dangkykhaisinh", KS), ("dangkytamtru", TT),
               ("mk muon dk khaitu", KT), ("tachho mat bao lau", TACH), ("KetHon can nhung giay to gi a", KH), ("khongbiet lam sao dangkykethon", KH)]:
    assert top(q)[0] == pid, (q, top(q)[0])
assert top("xin giấy phép mở quán karaoke")[0] is None and top("giá bitcoin hôm nay")[0] is None      # chữ lạ/nước ngoài vẫn ngoài phạm vi
# teencode: phủ định/viết tắt khai triển thành mục hỏi
s = top("đăng ký kết hôn có mất phí ko")[1].segments[0]
assert s.proc_id == KH and s.query.fields == ["fees"], s.query.fields
assert top("dk khai sinh lp bao nhieu")[1].segments[0].query.fields == ["fees"]

# ---- (3) chữ lạ chỉ hạ độ tin cậy, không đổi hướng (L1)
for q in ["Turn 2: Vậy thời gian giải quyết và lệ phí như thế nào?", "User: vậy thời gian giải quyết và lệ phí như thế nào?", "Vậy thời gian giải quyết và lệ phí như thế nào? hehe zzz",
          "xyzabc vậy lệ phí thế nào"]:
    pid, r = top(q, "Tôi muốn đăng ký kết hôn.")
    assert pid == KH and r.ctx["decision"] == "follow_up" and set(r.segments[0].query.fields) >= {"fees"}, (q, pid, r.ctx)
# chữ nghiệp vụ lạ THẬT (có trong kho, thủ tục khác) vẫn làm câu độc lập
assert top("còn tách hộ thì sao", "Tôi muốn đăng ký kết hôn.")[0] == TACH
# ---- (4) điều kiện và task thừa (23c)
L2 = "Nếu tôi đăng ký khai tử cho người đã chết nhưng người đó có hộ khẩu thường trú ở địa phương và được tổ chức tang lễ ở nơi khác thì tôi cần làm gì?"
for q in (L2, "neu toi dang ky khai tu cho nguoi da chet nhung to chuc tang le o noi khac thi can lam gi", "Turn 1: " + L2):
    r = resolve(idx, [{"role": "user", "text": q}])
    assert len(r.segments) == 1 and r.segments[0].proc_id == KT, (q, [(s.text, s.proc_id) for s in r.segments])      # MỘT task, không có 'thông báo tổ chức lễ hội'
    fq = r.segments[0].query
    assert fq.fields == ["components"] and "tang" in fq.flags.get("condition", "").lower(), (fq.fields, fq.flags)   # hồ sơ + hoàn cảnh, không 'steps'
# mảnh chỉ mượn vài chữ chung của thủ tục khác không là task; ý thứ hai THẬT vẫn giữ
assert len(resolve(idx, [{"role": "user", "text": "Khai tử cần giấy tờ gì, tổ chức tang lễ ở nơi khác thì sao"}]).segments) == 1
assert len(resolve(idx, [{"role": "user", "text": "Tôi đăng ký khai tử cho bố, và tổ chức tang lễ ở quê, cần giấy tờ gì"}]).segments) == 1
assert [s.proc_id for s in resolve(idx, [{"role": "user", "text": "Đăng ký kết hôn cần giấy tờ gì, còn khai tử mất bao lâu"}]).segments] == [KH, KT]
assert [s.proc_id for s in resolve(idx, [{"role": "user", "text": "đăng ký tạm trú cần giấy tờ gì và thông báo tổ chức lễ hội thì sao"}]).segments][1:] == ["1.003622"]
print("p23_input_test OK")

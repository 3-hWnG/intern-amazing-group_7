"""Phase 30: (A) hỏi lại khi câu chỉ là cụm gốc chung của nhiều thủ tục mà không hỏi thừa khi đã gọi tên; (B) điều kiện phải cho thêm thông tin ngoài tên thủ tục
và chữ hư/cụm hỏi mục không được làm "khớp" mục điều kiện (nên không gọi bước LLM sinh chữ thừa, không chặn hỏi lại). Chạy: python tests/p30_clarify_test.py"""
import os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_USE_LLM="0", S3_PLANNER_MODE="rules", S3_NO_WARMUP="1")

from planner import plan as make_plan
from policy import check, pre_check
from policy.policy import adds_info
from system3.data import api as data_api

conn = data_api.connect()


def route(q):
    pc = pre_check(q)
    return check(make_plan([{"role": "user", "text": pc["text"]}], use_llm=False), user_text=pc["text"], conn=conn, flags=pc["flags"])


# ---- A: cụm gốc chung -> hỏi lại (các dạng có tên dài, trước đây bị loại khỏi nhóm ứng viên vì độ phủ tên thấp)
for q in ["gia hạn", "xét tuyển", "tuyển chọn", "thanh toán", "Tôi cần thu hồi", "thủ tục chuyển đổi cần giấy tờ gì", "em muốn giao đất",
          "Cho tôi hỏi về hỗ trợ chi phí mai táng"]:     # ca cuối: chỉ 2 dạng không gắn tỉnh + các bản tỉnh làm bằng chứng nhiều dạng
    r = route(q)
    assert r.behavior == "clarify" and len(r.clarify["options"]) >= 2, (q, r.behavior)
    assert all(not conn.execute("SELECT province FROM procedures WHERE proc_id=?", (o["proc_id"],)).fetchone()[0] for o in r.clarify["options"]), q   # không hiện bản riêng tỉnh
# ---- A: đã gọi tên (nguyên tên, tên thủ tục ngắn là phần của tên khác, cụm giữa/cuối tên dài) -> trả lời, không hỏi thừa
for q, label in [("Gia hạn tạm trú", "Gia hạn tạm trú"), ("khám bệnh chữa bệnh bảo hiểm y tế", "khám bệnh"), ("chứng thực chữ ký ở đâu", "Chứng thực chữ ký"),
                 ("Thường trú cần giấy tờ gì?", "Đăng ký thường trú"), ("Đăng ký hộ kinh doanh cần hồ sơ gì", "hộ kinh doanh"), ("đăng ký khai sinh lưu động", "khai sinh lưu động"),      # Phase 31: tên chung "đăng ký khai sinh" (8 dạng thật) nay hỏi lại, xem p31_variants_test
                 ("Xét tuyển công chức", "Xét tuyển công chức")]:
    r = route(q)
    assert r.behavior == "answer" and label.lower() in r.tasks[0].procedure_label.lower(), (q, r.behavior)

# ---- B: mảnh điều kiện phải thêm thông tin ngoài tên thủ tục
assert not adds_info("đăng ký tạm trú", "Đăng ký tạm trú")
assert adds_info("chủ nhà ở nước ngoài", "Đăng ký tạm trú")
assert not adds_info("là", "Đăng ký tạm trú")


def conds(q):
    t = route(q).tasks[0]
    return t.conditions, t.soft_conditions


c, sc = conds("Lệ phí đăng ký thường trú là bao nhiêu?")
assert c == [] and sc == [], (c, sc)                               # trước Phase 30: chữ 'là' khớp mục "... công trình phụ trợ là nhà ở"
c, sc = conds("Nếu đăng ký tạm trú thì có được miễn phí không?")
assert c == [] and sc == [], (c, sc)                               # mảnh điều kiện chỉ lặp tên thủ tục
# ---- B: điều kiện THẬT vẫn hoạt động (TC06-style "nếu X thì cần gì")
c, _ = conds("Tôi ở nhà thuê thì đăng ký thường trú cần giấy tờ gì?")
assert c and "thuê" in c[0], c
c, _ = conds("Nhờ người khác đi đăng ký hộ kinh doanh thì cần giấy tờ ủy quyền gì?")
assert c and "ủy quyền" in c[0], c
c, _ = conds("Em là bộ đội ở trong doanh trại, đăng ký tạm trú cần giấy tờ gì?")
assert c and "đóng quân" in c[0], c
c, _ = conds("Vợ chồng tôi đã ly hôn nhưng vẫn ở chung nhà, tách hộ cần giấy tờ gì?")
assert c and "ly hôn" in c[0], c
print("p30_clarify_test OK")

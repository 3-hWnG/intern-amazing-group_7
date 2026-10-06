"""Phase 16: ca test cho 5 nhóm lỗi chung (A hỏi lại khi mơ hồ, B từ chối nhầm, C chọn nhầm biến thể anh em, D hội thoại nhiều lượt).
Do CHÍNH agent sửa lỗi tự nghĩ (không lấy từ bộ mù cases_h3 / pseudo_real). Mọi proc_id được assert với DB System 3.

Chạy: python build_p16.py
  - GHI THÊM (idempotent: xoá các dòng id 'p16-*' cũ) vào cases.jsonl, split "dev"   -> run.py --split all
  - ghi cases_p16_aside.jsonl: bộ "để riêng" (viết TRƯỚC khi sửa, không tune; chỉ chạy lúc đầu và lúc nghiệm thu): python run.py --adapter answer_adapter:adapter --split p16aside (xem run.py)
(build_cases.py cần repo V10.6 cũ không còn trên máy này nên không dựng lại được cases.jsonl; vì vậy file này nối thêm.)
"""
import json, os, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("S3_DB") or os.environ.get("S3_DATA_DB") or os.path.join(HERE, "..", "data", "runtime", "system3.db")
db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
NAMES = {r[0]: r[1] for r in db.execute("select proc_id,name from procedures where status='active'")}


def C(turns, ids, beh="answer", fields=(), notes=""):
    return dict(turns=turns, ids=list(ids), beh=beh, fields=list(fields), notes=notes)


def lst(*ids):
    """Lượt trợ lý là thẻ hỏi lại đã đánh số, dùng TÊN THẬT."""
    return "A: Bạn muốn hỏi về thủ tục nào? " + " ".join(f"{n}) {NAMES[i]}" for n, i in enumerate(ids, 1))


A_CLAR = "p16_A_clarify"      # >=3 bản gần nhau, câu không có yếu tố phân biệt -> hỏi lại
A_CTRL = "p16_A_ctrl"        # câu đã đủ phân biệt -> KHÔNG hỏi thừa
B = "p16_B_scope"            # kho có thủ tục: phải trả lời, không xin lỗi
B_OOS = "p16_B_oos"          # ngoài kho: vẫn phải xin lỗi
C_ = "p16_C_sibling"         # anh em cùng họ: chọn đúng theo từ phân biệt

DEV = [
    # ---- A: hỏi lại khi mơ hồ
    (A_CLAR, C(["giấy phép lao động cho người nước ngoài làm việc ở xã em"], ["1.014199", "1.014200", "1.014201"], "clarify")),
    (A_CLAR, C(["Tôi cần làm thủ tục giấy xác nhận không thuộc diện cấp giấy phép lao động"], ["1.014196", "1.014197", "1.014198"], "clarify")),
    (A_CLAR, C(["Cho hỏi về giấy phép xây dựng nhà ở"], ["1.013225", "1.013226", "1.013227", "1.013228"], "clarify")),
    (A_CLAR, C(["em muốn hỏi về hòa giải viên"], ["1.002211", "2.000930", "2.000950", "2.000424"], "clarify")),
    (A_CLAR, C(["Cho mình hỏi về trường mầm non"], ["2.002891", "2.002892", "2.002893", "2.002894"], "clarify")),
    (A_CLAR, C(["Thủ tục giải thể trường học"], ["1.001639", "1.012968", "1.012974", "2.002893", "5.003852"], "clarify")),
    (A_CLAR, C(["bên mình có nhận hồ sơ công nhận hộ nghèo không"], ["1.011606", "1.011607", "1.116214", "1.116215"], "clarify")),
    (A_CLAR, C(["xin hỗ trợ tiền mai táng cho người nhà"], ["1.001731", "1.014028", "2.002307", "2.002308"], "clarify")),
    (A_CLAR, C(["Tôi muốn đăng ký lại"], ["1.004884", "1.005461", "1.004746"], "clarify")),
    (A_CLAR, C(["sáp nhập chia tách trường"], ["1.004563", "1.012967", "1.012973", "2.002892"], "clarify")),
    (A_CLAR, C(["chứng thực giấy tờ giùm em"], ["2.000815", "2.000884", "2.001019"], "clarify")),
    (A_CLAR, C(["ad cho hỏi thủ tục đăng ký phương tiện thủy nội địa"], ["1.003970", "1.004002", "1.004036", "1.006391"], "clarify")),
    (A_CTRL, C(["Đăng ký khai sinh"], ["1.001193"])),
    (A_CTRL, C(["Đăng ký kết hôn có yếu tố nước ngoài"], ["2.000806"])),
    (A_CTRL, C(["đăng ký khai tử lưu động"], ["1.000419"])),
    (A_CTRL, C(["gia hạn giấy phép lao động cho người nước ngoài"], ["1.014201"])),
    (A_CTRL, C(["cấp lại giấy xác nhận không thuộc diện cấp giấy phép lao động"], ["1.014197"])),
    (A_CTRL, C(["gia hạn giấy phép xây dựng"], ["1.013227"])),
    (A_CTRL, C(["công nhận tổ trưởng tổ hòa giải"], ["2.000950"])),
    (A_CTRL, C(["cho phép trường mầm non hoạt động giáo dục"], ["2.002894"])),
    (A_CTRL, C(["hỗ trợ mai táng cho người đang hưởng trợ cấp hưu trí xã hội"], ["1.014028"])),
    (A_CTRL, C(["mai táng phí đối với cựu chiến binh"], ["2.002307"])),
    (A_CTRL, C(["công nhận hộ nghèo, cận nghèo thường xuyên hằng năm"], ["1.011607"])),
    (A_CTRL, C(["thôi làm hòa giải viên"], ["2.000930"])),
    (A_CTRL, C(["đăng ký giám sát việc giám hộ"], ["3.000323"])),
    (A_CTRL, C(["giải thể trường tiểu học"], ["1.001639"])),
    (A_CTRL, C(["làm thủ tục thôi hưởng trợ cấp hưu trí xã hội"], ["1.014027"])),
    (A_CTRL, C(["cấp lại giấy phép xây dựng bị mất"], ["1.013228"])),
    # ---- B: có trong kho nhưng kể đời thường / hoàn cảnh -> phải trả lời
    (B, C(["Con tôi sắp vào lớp 6, đăng ký học ở đâu?"], ["3.000182"])),
    (B, C(["Cho con vào lớp 6 thì cần giấy tờ gì"], ["3.000182"], fields=["components"])),
    (B, C(["Mẹ tôi hơn 80 tuổi, không có lương hưu, xin tiền trợ cấp hàng tháng ở đâu"], ["1.014027", "1.001776"])),
    (B, C(["Ba tôi mất hôm qua, tôi phải đi báo tử ở đâu"], ["1.000656", "2.002913"])),
    (B, C(["Chồng em vừa mất, em cần làm giấy tờ gì"], ["1.000656", "2.002913"])),
    (B, C(["Nhà em có người vừa mất thì phải làm thủ tục gì ạ"], ["1.000656", "2.002913"])),
    (B, C(["con em mới đẻ, đăng ký giấy tờ cho cháu ở đâu"], ["1.001193", "1.000689", "3.000722"])),
    (B, C(["Tôi sắp lấy vợ, thủ tục ở xã thế nào"], ["1.000894"])),
    (B, C(["Tôi bị tai nạn lao động thì được hưởng chế độ gì"], ["1.001632", "1.001521", "1.001643"])),
    (B, C(["vợ tôi sinh con thì được hưởng chế độ thai sản gì"], ["2.000693", "1.001667"])),
    (B, C(["Cháu bé bị bỏ rơi, vợ chồng tôi muốn nhận về nuôi"], ["2.001263", "1.004941", "2.001944"])),
    (B, C(["Em muốn nhận nuôi một đứa trẻ thì làm thế nào"], ["2.001263", "1.004941", "2.001944"])),
    (B, C(["Xin giấy xác nhận độc thân để đăng ký kết hôn"], ["1.004873"])),
    (B, C(["xin giấy chứng nhận chưa đăng ký kết hôn"], ["1.004873"])),
    (B, C(["con tôi bị khuyết tật, muốn xin giấy xác nhận"], ["1.001699"])),
    (B, C(["Người khuyết tật nặng có được nhận tiền hàng tháng không"], ["1.001776", "1.001699"])),
    (B, C(["Gia đình tôi muốn thoát nghèo thì làm sao"], ["1.011608", "1.011606", "1.116214", "1.116215"])),
    (B, C(["Cho cháu vào trường nội trú dân tộc"], ["1.005090", "5.003847", "6.006710"])),
    (B, C(["Ông ngoại tôi có công với cách mạng, xin giấy xác nhận thân nhân"], ["1.010833"])),
    (B, C(["Mất sổ BHXH thì xin cấp lại ở đâu"], ["1.002759"])),
    (B, C(["Tôi muốn rút bảo hiểm xã hội một lần"], ["1.001613"])),
    (B, C(["Mẹ em mất, muốn đi xóa hộ khẩu của mẹ thì làm thế nào"], ["1.003197", "2.002913"])),
    (B_OOS, C(["Tôi muốn ly hôn thì nộp đơn ở đâu"], [], "apologize")),
    (B_OOS, C(["Em muốn xin học bổng đi du học Úc"], [], "apologize")),
    (B_OOS, C(["Em muốn xin việc làm ở công ty may"], [], "apologize")),
    (B_OOS, C(["Làm giấy phép lái xe hạng B2 ở đâu"], [], "apologize")),
    (B, C(["xin cấp sổ đỏ lần đầu cho mảnh đất của ông bà để lại"], ["1.012753", "1.013978"])),
    # ---- C: chọn nhầm anh em
    (C_, C(["chứng thực chữ ký"], ["2.000884"])),
    (C_, C(["chứng thực bản sao từ bản chính"], ["2.000815"])),
    (C_, C(["em cần chứng thực chữ ký trong hợp đồng"], ["2.000884"])),
    (C_, C(["đi chứng thực bản sao giấy tờ ở đâu"], ["2.000815"], fields=["address"])),
    (C_, C(["chứng thực chữ ký của người dịch khi người dịch không phải cộng tác viên của UBND xã"], ["2.001008"])),
    (C_, C(["chứng thực chữ ký của người dịch là cộng tác viên dịch thuật của UBND"], ["2.000992"])),
    (C_, C(["cho hỏi cấp bản sao có chứng thực từ bản chính giao dịch đã chứng thực"], ["2.000942"])),
    (C_, C(["chung thuc ban sao tu ban chinh phi bao nhieu"], ["2.000815"], fields=["fees"])),
    (C_, C(["chung thuc chu ky nop o dau"], ["2.000884"], fields=["address"])),
    (C_, C(["xin trích lục khai sinh bản sao"], ["2.000635"])),
    (C_, C(["gia han tam tru can gi"], ["1.002755"], fields=["components"])),
    (C_, C(["xoa dang ky tam tru"], ["1.010028"])),
    (C_, C(["xoa dang ky thuong tru"], ["1.003197"])),
    (C_, C(["khóa căn cước điện tử"], ["3.000285"])),
    (C_, C(["mở khóa căn cước điện tử"], ["3.000286"])),
    (C_, C(["cấp lại giấy chứng nhận đăng ký hộ kinh doanh bị mất"], ["2.000575"])),
    (C_, C(["đăng ký thay đổi nội dung hộ kinh doanh"], ["2.000720"])),
    (C_, C(["tạm ngừng kinh doanh hộ kinh doanh"], ["1.001570"])),
    (C_, C(["tôi muốn đóng cửa luôn hộ kinh doanh"], ["1.001266"])),
    (C_, C(["khai sinh có yếu tố nước ngoài"], ["2.000528"])),
    (C_, C(["đăng ký kết hôn lưu động"], ["1.000593"])),
    (C_, C(["đăng ký lại khai tử"], ["1.005461"])),
    (C_, C(["đăng ký khai sinh kết hợp nhận cha mẹ con"], ["1.000689"])),
    (C_, C(["xét duyệt học sinh bán trú hỗ trợ gạo"], ["2.002770"])),
    (C_, C(["xét duyệt trẻ em nhà trẻ bán trú được hỗ trợ"], ["2.002771"])),
    (C_, C(["thờ cúng liệt sĩ được trợ cấp không"], ["1.010803"])),
    (C_, C(["mai táng phí cho thanh niên xung phong"], ["2.002308"])),
    (C_, C(["đổi cấp lại giấy xác nhận khuyết tật bị mất"], ["1.001653"])),
    (C_, C(["xác định mức độ khuyết tật lần đầu"], ["1.001699"])),
    (C_, C(["đăng ký chấm dứt giám hộ"], ["1.004845"])),
]

# bộ để riêng: KHÔNG tune; chạy lúc đầu (chỉ lấy số tổng) và lúc nghiệm thu. Cách nói khác, hoàn cảnh khác.
ASIDE = [
    (A_CLAR, C(["cho em hỏi về giấy phép lao động nước ngoài"], ["1.014199", "1.014200", "1.014201"], "clarify")),
    (A_CLAR, C(["thủ tục xác nhận không thuộc diện cấp giấy phép lao động là gì"], ["1.014196", "1.014197", "1.014198"], "clarify")),
    (A_CLAR, C(["Nhà tôi xây nhà, cần xin giấy phép xây dựng"], ["1.013225", "1.013226", "1.013227", "1.013228"], "clarify", notes="xây nhà = cấp mới thì đáp án có thể là 1.013225; chấp nhận cả hai? Giữ clarify do câu không nêu loại")),
    (A_CLAR, C(["hỏi về công nhận người hòa giải ở thôn"], ["1.002211", "2.000950"], "clarify")),
    (A_CLAR, C(["xin giải thể trường"], ["1.001639", "1.012968", "1.012974", "2.002893"], "clarify")),
    (A_CLAR, C(["tư vấn giúp tôi về sáp nhập, chia, tách trường"], ["1.004563", "1.012967", "1.012973", "2.002892"], "clarify")),
    (A_CLAR, C(["mình muốn đăng ký lại giấy tờ hộ tịch"], ["1.004884", "1.005461", "1.004746"], "clarify")),
    (A_CLAR, C(["xin chế độ mai táng phí"], ["1.001731", "1.014028", "2.002307", "2.002308"], "clarify")),
    (A_CLAR, C(["hộ cận nghèo đăng ký ở đâu"], ["1.011606", "1.011607", "1.116214", "1.116215"], "clarify")),
    (A_CTRL, C(["gia hạn giấy xác nhận không thuộc diện cấp giấy phép lao động"], ["1.014198"])),
    (A_CTRL, C(["cấp lại giấy phép lao động cho người nước ngoài"], ["1.014200"])),
    (A_CTRL, C(["xin cấp điều chỉnh giấy phép xây dựng công trình cấp III cấp IV"], ["1.013226"])),
    (A_CTRL, C(["cho phép trường mầm non hoạt động giáo dục trở lại"], ["2.002894"], notes="gần nhất; chấp nhận 2.002894")),
    (A_CTRL, C(["đăng ký kết hôn"], ["1.000894"])),
    (A_CTRL, C(["đăng ký khai tử"], ["1.000656"])),
    (B, C(["bé nhà mình vào lớp 6 năm nay, hồ sơ xét tuyển nộp ở đâu"], ["3.000182"])),
    (B, C(["Bà ngoại 76 tuổi không có lương hưu, có được nhận trợ cấp gì không"], ["1.014027", "1.001776"])),
    (B, C(["Cha em mới qua đời, em cần xin giấy gì"], ["1.000656", "2.002913"])),
    (B, C(["vợ chồng em mới có em bé, cần làm giấy tờ gì ở phường"], ["1.001193", "1.000689", "3.000722"])),
    (B, C(["Em bị tai nạn khi đi làm, muốn hưởng trợ cấp"], ["1.001632", "1.001521", "1.001643"])),
    (B, C(["Nhà tôi muốn nhận một cháu bé về nuôi hợp pháp"], ["2.001263", "1.004941", "2.001944"])),
    (B, C(["Em cần giấy chứng nhận chưa từng kết hôn"], ["1.004873"])),
    (B, C(["Cháu nhà tôi bị tật nguyền bẩm sinh, muốn làm giấy xác nhận mức độ khuyết tật"], ["1.001699"])),
    (B, C(["muốn đưa con vào học trường dân tộc nội trú"], ["1.005090", "5.003847", "6.006710"])),
    (B_OOS, C(["Tôi muốn nộp đơn ly dị"], [], "apologize")),
    (B_OOS, C(["đăng ký học lái xe ô tô"], [], "apologize")),
    (B_OOS, C(["ai ơi cho mình hỏi cách nộp thuế thu nhập cá nhân qua mạng"], [], "apologize")),
    (C_, C(["chứng thực chữ ký ở xã"], ["2.000884"])),
    (C_, C(["đi chứng thực bản sao bằng tốt nghiệp"], ["2.000815"])),
    (C_, C(["xin giấy xác nhận nhân thân người có công"], ["1.010833"])),
    (C_, C(["cấp lại giấy phép xây dựng đã mất"], ["1.013228"])),
    (C_, C(["xin tạm dừng kinh doanh hộ gia đình"], ["1.001570"])),
    (C_, C(["đăng ký khai sinh trễ hạn"], ["1.001193", "1.004772"])),
    (C_, C(["xoa dang ky tam tru nhu the nao"], ["1.010028"])),
    (C_, C(["lam lai khai sinh da mat so"], ["1.004884"])),
    (C_, C(["khai tu o noi khong phai noi cu tru"], ["1.000656"])),
]

# ------------------------------------------------------------------ ctx (D) ----
# (kind, [(user, pid_trả_lời|None | ("LIST", ids...))...], đáp án, fields, forbid)
CTX = [
    ("d1", [("Tôi muốn đăng ký lại", ("LIST", "1.004884", "1.005461", "1.004746")), ("cái thứ hai", None)], ["1.005461"], None, ["1.004884"]),
    ("d1", [("Tôi muốn đăng ký lại", ("LIST", "1.004884", "1.005461", "1.004746")), ("cái cuối", None)], ["1.004746"], None, ["1.004884"]),
    ("d1", [("giấy phép lao động cho người nước ngoài", ("LIST", "1.014199", "1.014200", "1.014201")), ("số 3, phí bao nhiêu", None)], ["1.014201"], ["fees"], ["1.014199"]),
    ("d1", [("em muốn hỏi về hòa giải viên", ("LIST", "1.002211", "2.000930", "2.000950", "2.000424")), ("à cái thứ tư", None)], ["2.000424"], None, ["1.002211"]),
    ("d1", [("xin hỗ trợ tiền mai táng cho người nhà", ("LIST", "1.001731", "1.014028", "2.002307", "2.002308")), ("cái đầu tiên", None)], ["1.001731"], None, ["1.014028"]),
    ("d1", [("xin hỗ trợ tiền mai táng cho người nhà", ("LIST", "1.001731", "1.014028", "2.002307", "2.002308")), ("ý tôi là cái thứ hai, mất bao lâu", None)], ["1.014028"], ["processing_time"], ["1.001731"]),
    ("d1", [("Tôi muốn đăng ký lại", ("LIST", "1.004884", "1.005461", "1.004746")), ("không phải, tôi muốn cái thứ ba", None)], ["1.004746"], None, ["1.004884"]),
    ("d2", [("đăng ký khai sinh", "1.001193"), ("còn phí?", None)], ["1.001193"], ["fees"], None),
    ("d2", [("đăng ký tạm trú cần gì", "1.004194"), ("thế bao nhiêu", None)], ["1.004194"], ["fees"], None),
    ("d2", [("gia hạn tạm trú", "1.002755"), ("mất bao lâu thế", None)], ["1.002755"], ["processing_time"], None),
    ("d2", [("chứng thực chữ ký", "2.000884"), ("thế phí bao nhiêu nhỉ", None)], ["2.000884"], ["fees"], None),
    ("d2", [("đăng ký kết hôn", "1.000894"), ("rồi nộp ở đâu vậy", None)], ["1.000894"], ["address"], None),
    ("d3", [("đăng ký khai tử", "1.000656"), ("ba tôi mất ở bệnh viện, không có giấy báo tử", None)], ["1.000656"], None, None),
    ("d3", [("đăng ký tạm trú", "1.004194"), ("tôi là sinh viên ở trọ, chủ nhà không cho đăng ký", None)], ["1.004194"], None, None),
    ("d3", [("đăng ký khai sinh", "1.001193"), ("cháu sinh ở nhà, không đi viện", None)], ["1.001193"], None, None),
    ("d4", [("chứng thực chữ ký", "2.000884"), ("à không ý tôi là chứng thực bản sao", None)], ["2.000815"], None, ["2.000884"]),
    ("d4", [("đăng ký thường trú", "1.004222"), ("không, ý em là xóa đăng ký thường trú", None)], ["1.003197"], None, ["1.004222"]),
    ("d4", [("đăng ký khai sinh", "1.001193"), ("ý mình là đăng ký lại khai sinh", None)], ["1.004884"], None, ["1.001193"]),
    ("d5", [("đăng ký khai sinh", "1.001193"), ("đăng ký tạm trú", "1.004194"), ("cái thứ nhất, phí bao nhiêu", None)], ["1.001193"], ["fees"], None),
    ("d5", [("đăng ký khai sinh", "1.001193"), ("đăng ký tạm trú", "1.004194"), ("cái thứ hai mất bao lâu", None)], ["1.004194"], ["processing_time"], None),
    ("d1", [("Tôi muốn đăng ký lại", ("LIST", "1.004884", "1.005461", "1.004746")), ("thôi cái đầu tiên đi", None)], ["1.004884"], None, ["1.005461"]),
    ("d1", [("Tôi muốn đăng ký lại", ("LIST", "1.004884", "1.005461", "1.004746")), ("cái giữa ấy, mất bao lâu", None)], ["1.005461"], ["processing_time"], ["1.004884"]),
    ("d1", [("giấy phép lao động cho người nước ngoài", ("LIST", "1.014199", "1.014200", "1.014201")), ("à không, ý tôi là cái thứ hai", None)], ["1.014200"], None, ["1.014199"]),
    ("d1", [("giấy phép lao động cho người nước ngoài", ("LIST", "1.014199", "1.014200", "1.014201")), ("số 1 nộp ở đâu vậy", None)], ["1.014199"], ["address"], None),
    ("d2", [("gia hạn tạm trú", "1.002755"), ("vậy còn bao lâu", None)], ["1.002755"], ["processing_time"], None),
    ("d2", [("đăng ký khai sinh", "1.001193"), ("thế còn đăng ký nhận cha mẹ con thì phí bao nhiêu", None)], ["1.001022"], ["fees"], ["1.001193"]),
    ("d2", [("đăng ký tạm trú", "1.004194"), ("thế còn gia hạn thì sao", None)], ["1.002755"], None, None),
]


def exp_task(ids, fields):
    return dict(acceptable_proc_ids=ids, fields=list(fields), quantity=None, evidence_demand="none", relation="independent",
                refers_to="new", conditions=[], context_facts=[])


def case(i, cat, c, split="dev"):
    for p in c["ids"]:
        assert p in NAMES, (cat, p)
    turns = [{"role": "user", "text": t} for t in c["turns"]]
    exp = dict(tasks=[exp_task(c["ids"], c["fields"])] if (c["ids"] and c["beh"] == "answer") else [], behavior=c["beh"],
               must_say_not_published=False, missing_numeric_fields=[], free_text_in_source=False, citation_tokens=[],
               notes=c["notes"] or f"p16; ids tham chiếu: {c['ids']}")
    return dict(id=f"p16-{cat}-{i:02d}", category=cat, split=split, source="p16-own", turns=turns, expected=exp)


def main():
    keep = [l for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8") if not json.loads(l)["id"].startswith("p16-")]
    n = {}
    new = []
    for cat, c in DEV:
        n[cat] = n.get(cat, 0) + 1
        new.append(case(n[cat], cat, c))
    with open(os.path.join(HERE, "cases.jsonl"), "w", encoding="utf-8") as f:
        f.writelines(keep)
        for x in new:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    n = {}
    with open(os.path.join(HERE, "cases_p16_aside.jsonl"), "w", encoding="utf-8") as f:
        for cat, c in ASIDE:
            n[cat] = n.get(cat, 0) + 1
            f.write(json.dumps(case(n[cat], cat, c, split="p16aside"), ensure_ascii=False) + "\n")
    print("cases.jsonl:", len(keep), "cũ +", len(new), "mới; aside:", len(ASIDE))


if __name__ == "__main__":
    main()

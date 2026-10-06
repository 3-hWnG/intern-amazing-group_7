"""Phase 18: ca test cho các NHÓM LỖI CHUNG (A trả dư mục, B task thừa/multi-intent quá nhạy, C hỏi lại khi mơ hồ, D điều kiện/trường hợp,
E từ chối nhầm/chọn nhầm anh em, F gõ đời thường + hội thoại nhiều lượt). Câu do chính agent sửa lỗi tự nghĩ (KHÔNG lấy từ bộ mù cases_h3/h2/team/pseudo_real).
Mọi proc_id được assert với DB System 3.

Chạy: python build_p18.py   -> GHI THÊM (idempotent: xoá các dòng id 'p18-*' cũ) vào cases.jsonl, split "dev" (tiền tố id p18-).
Gate DEV cũ (209 câu) loại id bắt đầu p16/p18. Mục "fields" = mục NGƯỜI DÙNG hỏi (chấm concise: không dư, không thiếu).
"""
import json, os, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("S3_DB") or os.environ.get("S3_DATA_DB") or os.path.join(HERE, "..", "data", "runtime", "system3.db")
db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
NAMES = {r[0]: r[1] for r in db.execute("select proc_id,name from procedures where status='active'")}
ASST = "Mình đã trả lời theo dữ liệu của thủ tục. Bạn cần hỏi thêm gì không?"


def T(ids, fields=(), evidence="none", keys=()):
    """keys: cụm khoá PHẢI có trong câu trả lời (chấm 'condition' của run.py): tên trường hợp trong condition_index, hoặc 'không công bố' khi dữ liệu thiếu."""
    return dict(ids=list(ids), fields=list(fields), evidence=evidence, keys=list(keys))


def C(turns, tasks, beh="answer", notes=""):
    """turns: list[str]; lượt xen kẽ user/assistant nếu có nhiều phần tử (phần tử chẵn = user, lẻ = trợ lý)."""
    return dict(turns=turns, tasks=tasks, beh=beh, notes=notes)


KS, KH, KT, TT, TH, GH, TV = "1.001193", "1.000894", "1.000656", "1.004194", "1.004222", "1.002755", "1.003677"
XT, XH, TACH, CTCK, CTBS, KT_, HN, CCCD, GHO, NCM, LT, HKD = ("1.010028", "1.003197", "1.010038", "2.000884", "2.000815", "1.001699", "1.011607",
                                                              "1.116410", "1.004837", "1.001022", "2.001159", "1.001612")
LKS = "1.004884"

DEV = [
    # ---------- A: mục được hỏi (không dư, không thiếu)
    ("p18_A_field", C(["Tách hộ mất bao lâu thì xong ạ?"], [T([TACH], ["processing_time"])])),
    ("p18_A_field", C(["Cho mình hỏi khai tử có tốn tiền không?"], [T([KT], ["fees"])])),
    ("p18_A_field", C(["Đăng ký thường trú nộp hồ sơ online được không?"], [T([TH], ["online"])])),
    ("p18_A_field", C(["Biểu mẫu đăng ký tạm vắng tải ở đâu?"], [T([TV], ["files"])])),
    ("p18_A_field", C(["Xóa đăng ký tạm trú dựa trên văn bản nào?"], [T([XT], ["meta"], "legal_basis")])),
    ("p18_A_field", C(["Đăng ký giám hộ do cơ quan nào làm?"], [T([GHO], ["agency"])])),
    ("p18_A_field", C(["Hồ sơ gia hạn tạm trú gồm những gì?"], [T([GH], ["components"])])),
    ("p18_A_field", C(["Chứng thực chữ ký phí bao nhiêu và cần mang theo gì?"], [T([CTCK], ["fees", "components"])])),
    ("p18_A_field", C(["Khai báo tạm vắng thì các bước làm như thế nào?"], [T([TV], ["steps"])])),
    ("p18_A_field", C(["Khai tử: lệ phí, thời hạn và nộp ở đâu?"], [T([KT], ["fees", "processing_time", "address"])])),
    ("p18_A_field", C(["Đăng ký kết hôn tốn bao nhiêu ngày thì có giấy?"], [T([KH], ["processing_time"])])),
    ("p18_A_field", C(["Thông báo lưu trú có nộp qua mạng được không?"], [T([LT], ["online"])])),
    ("p18_A_field", C(["Đăng ký nhận cha mẹ con nộp hồ sơ bằng hình thức nào?"], [T([NCM], ["methods"])])),
    ("p18_A_field", C(["Đăng ký khai sinh mất bao nhiêu tiền?"], [T([KS], ["fees"])])),
    ("p18_A_field", C(["Xác định khuyết tật phải chuẩn bị giấy tờ gì?"], [T([KT_], ["components"])])),
    ("p18_A_field", C(["Công nhận hộ nghèo thường xuyên hằng năm xem quy định ở thông tư nào?"], [T([HN], ["meta"], "legal_basis")])),
    ("p18_A_field", C(["đăng ký tạm trú giải quyết trong bao lâu"], [T([TT], ["processing_time"])])),
    ("p18_A_field", C(["Đăng ký lại khai sinh cần nộp những giấy tờ nào, bao lâu có kết quả?"], [T([LKS], ["components", "processing_time"])])),
    ("p18_A_field", C(["Chứng thực bản sao từ bản chính thì hết bao nhiêu?"], [T([CTBS], ["fees"])])),
    ("p18_A_field", C(["Mình cần tờ khai mẫu của thủ tục tách hộ"], [T([TACH], ["files"])])),
    ("p18_A_field", C(["Đăng ký khai sinh bao giờ có kết quả?"], [T([KS], ["processing_time"])])),
    ("p18_A_field", C(["Khai tử có phải đóng tiền không?"], [T([KT], ["fees"])])),
    ("p18_A_field", C(["Tách hộ ai làm vậy?"], [T([TACH], ["agency"])])),
    ("p18_A_field", C(["Đăng ký tạm trú nộp bưu điện được không?"], [T([TT], ["methods"])])),
    ("p18_A_field", C(["chi phí đăng ký kết hôn"], [T([KH], ["fees"])])),
    ("p18_A_field", C(["Gia hạn tạm trú thời gian xử lý hồ sơ bao lâu?"], [T([GH], ["processing_time"])])),
    # ---------- A: câu nối / sửa ý giữ mục đang hỏi
    ("p18_A_follow", C(["Đăng ký khai sinh cần giấy tờ gì?", ASST, "thế còn kết hôn?"], [T([KH], ["components"])])),
    ("p18_A_follow", C(["gia hạn tạm trú mất bao lâu", ASST, "còn phí thì sao"], [T([GH], ["fees"])])),
    ("p18_A_follow", C(["Đăng ký thường trú phí bao nhiêu?", ASST, "không phải, tôi hỏi tạm trú"], [T([TT], ["fees"])])),
    ("p18_A_follow", C(["khai tử cần gì", ASST, "thế thời hạn thì sao"], [T([KT], ["processing_time"])])),
    ("p18_A_follow", C(["đăng ký tạm vắng", ASST, "nộp ở đâu"], [T([TV], ["address"])])),
    ("p18_A_follow", C(["Tách hộ cần giấy tờ gì", ASST, "chắc không?"], [T([TACH], ["components"], "legal_basis")])),
    ("p18_A_follow", C(["xóa đăng ký thường trú mất bao lâu", ASST, "ý mình là xóa tạm trú"], [T([XT], ["processing_time"])])),
    ("p18_A_follow", C(["đăng ký kết hôn lệ phí bao nhiêu", ASST, "ngắn gọn hơn được không"], [T([KH], ["fees"])])),
    # ---------- A: câu điều kiện -> hồ sơ/giấy tờ theo trường hợp (không trả đủ 4 mục)
    ("p18_A_cond", C(["Nếu tôi từng ly hôn thì đăng ký kết hôn cần giấy tờ gì thêm?"], [T([KH], ["components"])])),
    ("p18_A_cond", C(["Trường hợp đang ở nhờ nhà người quen thì đăng ký tạm trú ra sao?"], [T([TT], ["components"])])),
    ("p18_A_cond", C(["Nếu hồ sơ nộp qua bưu điện thì chứng thực chữ ký mất bao lâu?"], [T([CTCK], ["processing_time"])])),
    ("p18_A_cond", C(["Nếu bé sinh ra ở nhà chứ không ở viện thì đăng ký khai sinh cần những gì?"], [T([KS], ["components"])])),
    ("p18_A_cond", C(["Nếu quá hạn thì đăng ký khai tử phí bao nhiêu?"], [T([KT], ["fees"])])),
    ("p18_A_cond", C(["Người đang làm ăn xa thì khai báo tạm vắng có khác không?"], [T([TV], ["components"])])),
    # ---------- B: MỘT thủ tục kèm cụm hỏi mục / lời kể -> đúng 1 task
    ("p18_B_single", C(["Mình đang ở trọ, muốn đăng ký tạm trú thì giải quyết trong bao lâu?"], [T([TT], ["processing_time"])])),
    ("p18_B_single", C(["Tôi muốn xóa đăng ký thường trú, hết bao nhiêu tiền?"], [T([XH], ["fees"])])),
    ("p18_B_single", C(["Khai báo tạm vắng, cần gì và nộp ở đâu?"], [T([TV], ["components", "address"])])),
    ("p18_B_single", C(["Em mới sinh con rồi, đăng ký khai sinh mất bao lâu ạ?"], [T([KS], ["processing_time"])])),
    ("p18_B_single", C(["Bà nội mất rồi, làm giấy khai tử thì cần giấy tờ gì ạ"], [T([KT], ["components"])])),
    ("p18_B_single", C(["Công ty em có người ở ký túc xá, thông báo lưu trú nộp ở đâu?"], [T([LT], ["address"])])),
    ("p18_B_single", C(["Chị tôi là người khuyết tật, xin xác định khuyết tật mất bao lâu và tốn bao nhiêu tiền?"], [T([KT_], ["processing_time", "fees"])])),
    ("p18_B_single", C(["Tôi vừa cưới xong, đăng ký kết hôn cần mang theo gì?"], [T([KH], ["components"])])),
    ("p18_B_single", C(["Tôi định mở tiệm tạp hóa, đăng ký hộ kinh doanh hết bao nhiêu tiền và mất bao lâu?"], [T([HKD], ["fees", "processing_time"])])),
    ("p18_B_single", C(["Tôi muốn tách hộ vì ở riêng, giấy tờ gồm những gì, bao lâu xong?"], [T([TACH], ["components", "processing_time"])])),
    ("p18_B_single", C(["Cháu tôi vừa chào đời, đăng ký khai sinh cần những giấy tờ gì và giải quyết trong bao lâu?"], [T([KS], ["components", "processing_time"])])),
    ("p18_B_single", C(["Tôi đang ở nhờ nhà bạn, gia hạn tạm trú thì phí bao nhiêu?"], [T([GH], ["fees"])])),
    ("p18_B_single", C(["Mẹ tôi mất tuần trước, xóa đăng ký thường trú cho mẹ cần giấy tờ gì?"], [T([XH], ["components"])])),
    ("p18_B_single", C(["Chồng tôi đi làm xa gần một năm, khai báo tạm vắng mất bao lâu thì được?"], [T([TV], ["processing_time"])])),
    ("p18_B_single", C(["Tôi muốn đăng ký kết hôn, cần gì?"], [T([KH], ["components"])])),
    ("p18_B_single", C(["Xin gia hạn tạm trú, phí bao nhiêu vậy?"], [T([GH], ["fees"])])),
    ("p18_B_single", C(["Đăng ký khai tử, thời hạn giải quyết là bao nhiêu ngày?"], [T([KT], ["processing_time"])])),
    ("p18_B_single", C(["Mình muốn tách hộ, nộp ở đâu vậy bạn?"], [T([TACH], ["address"])])),
    ("p18_B_single", C(["Vợ chồng mình sắp cưới, đăng ký kết hôn hết bao lâu và phải mang theo giấy tờ nào?"], [T([KH], ["processing_time", "components"])])),
    ("p18_B_single", C(["Nhà mình chuyển đến phường mới, đăng ký thường trú thì mất bao nhiêu tiền?"], [T([TH], ["fees"])])),
    ("p18_B_single", C(["Hôm qua ông nội mất ở quê, em muốn đăng ký khai tử, giải quyết mất mấy ngày?"], [T([KT], ["processing_time"])])),
    ("p18_B_single", C(["Giấy tờ và lệ phí đăng ký khai sinh là gì?"], [T([KS], ["components", "fees"])])),
    # ---------- B: multi-intent thật (phải giữ)
    ("p18_B_multi", C(["Tách hộ cần giấy tờ gì còn khai tử mất bao lâu?"], [T([TACH], ["components"]), T([KT], ["processing_time"])])),
    ("p18_B_multi", C(["Đăng ký tạm vắng phí bao nhiêu, ngoài ra chứng thực chữ ký nộp ở đâu?"], [T([TV], ["fees"]), T([CTCK], ["address"])])),
    ("p18_B_multi", C(["Mình muốn đăng ký khai sinh cho con và đồng thời xóa đăng ký tạm trú"], [T([KS], []), T([XT], [])])),
    ("p18_B_multi", C(["Thường trú cần giấy tờ gì; tạm trú mất bao lâu?"], [T([TH], ["components"]), T([TT], ["processing_time"])])),
    ("p18_B_multi", C(["Gia hạn tạm trú mất bao nhiêu tiền, còn đăng ký kết hôn cần gì?"], [T([GH], ["fees"]), T([KH], ["components"])])),
    ("p18_B_multi", C(["Đăng ký giám hộ nộp ở đâu và đăng ký nhận cha mẹ con mất bao lâu?"], [T([GHO], ["address"]), T([NCM], ["processing_time"])])),
    # ---------- F: gõ đời thường (teencode, không dấu, viết tắt) và hội thoại nhiều lượt
    ("p18_F_casual", C(["dk tam tru can j z"], [T([TT], ["components"])])),
    ("p18_F_casual", C(["khai tu mat bn tien vay"], [T([KT], ["fees"])])),
    ("p18_F_casual", C(["thuong tru online dc ko"], [T([TH], ["online"])])),
    ("p18_F_casual", C(["ho so ket hon gom gi"], [T([KH], ["components"])])),
    ("p18_F_casual", C(["tach ho bao lau"], [T([TACH], ["processing_time"])])),
    ("p18_F_casual", C(["xoa tam tru can giay to gi"], [T([XT], ["components"])])),
    ("p18_F_casual", C(["dang ky lai khai sinh mat bao lau"], [T([LKS], ["processing_time"])])),
    ("p18_F_casual", C(["chung thuc chu ky phi bn"], [T([CTCK], ["fees"])])),
    ("p18_F_casual", C(["gia han tam tru qua mang dc k"], [T([GH], ["online"])])),
    ("p18_F_casual", C(["mik muon lam giay khai tu cho ba, can chuan bi j"], [T([KT], ["components"])])),
    ("p18_F_casual", C(["khai tu cho me e can gi vay"], [T([KT], ["components"])])),
    ("p18_F_casual", C(["khai tử cho mẹ em cần gì vậy"], [T([KT], ["components"])])),
    ("p18_F_casual", C(["cho e hoi thu tuc ket hon can nhung gi a"], [T([KH], ["components"])])),
    ("p18_F_casual", C(["xin cap lai the cccd bi mat the nao"], [T([CCCD], ["steps"])])),
    ("p18_F_casual", C(["t muon dk tam vang, mat may ngay"], [T([TV], ["processing_time"])])),
    ("p18_F_casual", C(["dk khai sinh cho con can giay to j"], [T([KS], ["components"])])),
    ("p18_F_casual", C(["gia han tam tru phi bn tien"], [T([GH], ["fees"])])),
    ("p18_F_casual", C(["e muon xoa tam tru can nhung giay to gi"], [T([XT], ["components"])])),
    ("p18_F_casual", C(["tach ho nop o dau vay ad"], [T([TACH], ["address"])])),
    ("p18_F_casual", C(["dang ky ket hon online dc ko ad"], [T([KH], ["online"])])),
    ("p18_F_casual", C(["thu tuc nhan cha me con can gi"], [T([NCM], ["components"])])),
    ("p18_F_casual", C(["chung thuc ban sao mat bn tien z"], [T([CTBS], ["fees"])])),
    ("p18_F_multi", C(["Gia hạn tạm trú cần gì", ASST, "mất bao lâu", ASST, "thế còn đăng ký tạm trú?"], [T([TT], ["processing_time"])])),
    ("p18_F_multi", C(["Mình mới sinh con", "Đã ghi nhận bạn mới sinh con.", "cần làm giấy khai sinh, mất bao lâu"], [T([KS], ["processing_time"])])),
    ("p18_F_multi", C(["đăng ký kết hôn", ASST, "cần giấy tờ gì", ASST, "online được không", ASST, "còn phí?"], [T([KH], ["fees"])])),
    ("p18_F_multi", C(["khai tử phí bao nhiêu", ASST, "nguồn ở đâu vậy"], [T([KT], ["meta"], "legal_basis")])),
    ("p18_F_multi", C(["tạm trú cần gì", ASST, "còn gia hạn?"], [T([GH], ["components"])])),
    ("p18_F_multi", C(["đk kết hôn", ASST, "phí?"], [T([KH], ["fees"])])),
    ("p18_F_multi", C(["khai sinh mất bao lâu", ASST, "à còn khai tử?"], [T([KT], ["processing_time"])])),
    ("p18_F_multi", C(["đăng ký tạm trú cần gì", ASST, "nhầm rồi, ý mình là thường trú"], [T([TH], ["components"])])),
    ("p18_F_multi", C(["khai sinh cần gì", ASST, "mất bao lâu", ASST, "còn phí?"], [T([KS], ["fees"])])),
    ("p18_F_multi", C(["xóa đăng ký tạm trú mất bao lâu", ASST, "còn xóa thường trú thì sao"], [T([XH], ["processing_time"])])),
    # ---------- C: nhóm chung quá rộng / gần nhau -> hỏi lại; câu đủ phân biệt -> không hỏi thừa
    ("p18_C_clarify", C(["thủ tục hộ tịch"], [], "clarify")),
    ("p18_C_clarify", C(["cho mình hỏi về hộ tịch"], [], "clarify")),
    ("p18_C_clarify", C(["giấy tờ về cư trú"], [], "clarify")),
    ("p18_C_clarify", C(["thủ tục về đất đai"], [], "clarify")),
    ("p18_C_clarify", C(["em cần hỏi về nuôi con nuôi"], [], "clarify")),
    ("p18_C_clarify", C(["thủ tục giáo dục"], [], "clarify")),
    ("p18_C_clarify", C(["bên mình có thủ tục nào về bảo trợ xã hội không"], [], "clarify")),
    ("p18_C_ctrl", C(["Đăng ký khai sinh lưu động"], [T(["1.003583"], [])])),
    ("p18_C_ctrl", C(["tách hộ"], [T([TACH], [])])),
    ("p18_C_ctrl", C(["đăng ký lại kết hôn"], [T(["1.004746"], [])])),
    ("p18_C_ctrl", C(["đăng ký giám hộ có yếu tố nước ngoài"], [T(["1.001669"], [])])),
    ("p18_C_ctrl", C(["chứng thực chữ ký người dịch mà người dịch là cộng tác viên"], [T(["2.000992"], [])])),
    ("p18_C_ctrl", C(["đăng ký kết hôn có yếu tố nước ngoài"], [T(["2.000806"], [])])),
    ("p18_C_ctrl", C(["công nhận hòa giải viên"], [T(["1.002211"], [])])),
    ("p18_C_ctrl", C(["Đăng ký thường trú cần giấy tờ gì"], [T([TH], ["components"])])),
    # ---------- D: hoàn cảnh/trường hợp đặc biệt -> phần giấy tờ của đúng trường hợp (condition_index) kèm nguồn; thiếu dữ liệu thì nói không công bố
    ("p18_D_case", C(["Em là bộ đội ở trong doanh trại, đăng ký tạm trú cần giấy tờ gì?"], [T([TT], ["components"], keys=["đơn vị đóng quân"])])),
    ("p18_D_case", C(["Công ty em cho cả chục công nhân ở một lượt, đăng ký tạm trú cần hồ sơ gì?"], [T([TT], ["components"], keys=["theo danh sách"])])),
    ("p18_D_case", C(["Vợ chồng tôi đã ly hôn nhưng vẫn ở chung nhà, tách hộ cần giấy tờ gì?"], [T([TACH], ["components"], keys=["đã ly hôn"])])),
    ("p18_D_case", C(["Mình ở nhà người quen, muốn đăng ký thường trú ở đó thì giấy tờ gì?"], [T([TH], ["components"], keys=["thuê, mượn, ở nhờ"])])),
    ("p18_D_case", C(["Ông bà tôi ở trong cơ sở tôn giáo, đăng ký thường trú thì cần giấy tờ gì?"], [T([TH], ["components"], keys=["cơ sở tín ngưỡng"])])),
    ("p18_D_nodata", C(["Nếu tôi là người nước ngoài thì đăng ký khai sinh cho con cần gì thêm?"], [T([KS], ["components"], keys=["không công bố"])])),
    ("p18_D_nodata", C(["Nếu làm thủ tục ở nơi khác nơi mình đang cư trú thì đăng ký kết hôn cần giấy tờ gì?"], [T([KH], ["components"], keys=["không công bố"])])),
    ("p18_D_nodata", C(["Tôi từng ly hôn rồi, giờ đăng ký kết hôn lại thì cần thêm giấy tờ gì?"], [T([KH], ["components"], keys=["không công bố"])])),
    # ---------- E: kho có thủ tục thì không xin lỗi; chọn đúng anh em (cùng họ, khác loại)
    ("p18_E_scope", C(["Người thân em từng làm thanh niên xung phong, muốn xin tặng huy chương thì làm sao"], [T(["1.014680"], [])])),
    ("p18_E_scope", C(["Giấy đăng ký hộ kinh doanh của tôi bị mất, xin cấp lại"], [T(["2.000575"], [])])),
    ("p18_E_scope", C(["đóng bảo hiểm xã hội tự nguyện thì đăng ký ở đâu"], [T(["1.002179"], [])])),
    ("p18_E_scope", C(["Xin hỗ trợ ăn trưa cho con đang học mẫu giáo"], [T(["1.001622"], [])])),
    ("p18_E_scope", C(["thẻ BHYT của em bị mất, xin cấp lại"], [T(["1.002759"], [])])),
    ("p18_E_scope", C(["ông em không muốn nhận trợ cấp hưu trí xã hội nữa, thôi hưởng thế nào"], [T(["1.014027"], [])])),
    ("p18_E_scope", C(["hỗ trợ chi phí y tế cho người tham gia hoạt động chữ thập đỏ bị tai nạn"], [T(["1.013710"], [])])),
    ("p18_E_scope", C(["đính chính giấy chứng nhận đã nộp online được không"], [T(["1.115226", "1.115355", "1.115516", "1.115628", "1.012796"], ["online"])])),
    ("p18_E_sibling", C(["làm lại bằng tổ quốc ghi công bị mất"], [T(["1.010778"], [])])),
    ("p18_E_sibling", C(["xin cấp bằng tổ quốc ghi công cho liệt sĩ"], [T(["1.010772"], [])])),
    ("p18_E_sibling", C(["đổi bằng tổ quốc ghi công do sai thông tin"], [T(["1.010777"], [])])),
    ("p18_E_sibling", C(["thôi hưởng trợ cấp hưu trí xã hội"], [T(["1.014027"], [])])),
    ("p18_E_sibling", C(["hỗ trợ chi phí mai táng cho người đang hưởng trợ cấp hưu trí xã hội"], [T(["1.014028"], [])])),
    ("p18_E_sibling", C(["đăng ký hoạt động chi nhánh văn phòng đại diện"], [T(["2.002123"], [])])),
    ("p18_E_sibling", C(["thay đổi nội dung đăng ký hoạt động của chi nhánh"], [T(["1.005378"], [])])),
]

# ------------------------------------------------------------------ build ----
def exp_task(t):
    return dict(acceptable_proc_ids=t["ids"], fields=t["fields"], quantity=None, evidence_demand=t["evidence"], relation="independent",
                refers_to="new", conditions=[], context_facts=[])


def case(i, cat, c):
    for t in c["tasks"]:
        for p in t["ids"]:
            assert p in NAMES, (cat, p)
    turns = [{"role": "user" if k % 2 == 0 else "assistant", "text": t} for k, t in enumerate(c["turns"])]
    exp = dict(tasks=[exp_task(t) for t in c["tasks"]] if c["beh"] == "answer" else [], behavior=c["beh"], must_say_not_published=False,
               missing_numeric_fields=[], free_text_in_source=False, citation_tokens=[], notes=c["notes"] or "p18")
    if c["tasks"] and c["tasks"][0]["keys"]:
        exp["checks"] = [dict(kind="condition", proc_id=c["tasks"][0]["ids"][0], index_text="", keys=c["tasks"][0]["keys"])]
    return dict(id=f"p18-{cat}-{i:02d}", category=cat, split="dev", source="p18-own", turns=turns, expected=exp)


def main():
    keep = [l for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8") if not json.loads(l)["id"].startswith("p18-")]
    n, new = {}, []
    for cat, c in DEV:
        n[cat] = n.get(cat, 0) + 1
        new.append(case(n[cat], cat, c))
    with open(os.path.join(HERE, "cases.jsonl"), "w", encoding="utf-8") as f:
        f.writelines(keep)
        for x in new:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print("cases.jsonl:", len(keep), "cũ +", len(new), "mới p18")


if __name__ == "__main__":
    main()

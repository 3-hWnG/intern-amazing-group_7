"""Bộ câu hỏi đo NV5 (accuracy / halluc / greeting). Do agent soạn — chưa phải câu hỏi thật của người dùng.

Mỗi câu: id, suite, split (dev = dùng khi chỉnh; exam = "bài thi cuối", không xem khi chỉnh), datasets (bộ dữ liệu bật),
turns (các tin nhắn; chấm tin cuối), check (luật chấm — xem bench.py: score()).
Đáp án lấy từ dữ liệu: danh sách lớp giả (fake_class.py), tệp chính sách Word (tạo trong bench.py), du lịch, thủ tục (sinh từ Excel).
"""
from __future__ import annotations
import re
from pathlib import Path

from fake_class import KIDS, full, kid, phone

DATA = Path(__file__).resolve().parent / "data"
PHONE_RE = r"(?:\+84|0|1[89]00)[\d .\-]{4,14}\d"
EMAIL_RE = r"[\w.+-]+@[\w-]+\.[\w.]+"
URL_RE = r"(?:https?://|www\.)\S+|\bteam\s?7[\w-]*\.(?:com|vn|net)"
YEAR_RE = r"\b(19|20)\d{2}\b"
PRICE_RE = r"\d{1,3}(?:[.,]\d{3})+|\d+\s*(?:triệu|nghìn|ngàn|đồng|usd|\$)"

GIRLS = [full(k) for k in KIDS if k[3] == "x"]
Y2019 = [full(k) for k in KIDS if k[4].endswith("2019")]
TAN_HOA = [full(k) for k in KIDS if "Tân Hòa" in k[5]]
PHU_THANH = [full(k) for k in KIDS if "Phú Thạnh" in k[5]]
assert len(GIRLS) == 16 and len(Y2019) == 5 and len(TAN_HOA) == 14 and len(PHU_THANH) == 10


def C(id, suite, split, datasets, turns, **check):
    return {"id": id, "suite": suite, "split": split, "datasets": datasets, "turns": turns if isinstance(turns, list) else [turns],
            "check": check}


CLS, POL, TOUR, PROC = "class", "policy", "tourism", "procedures"
k_an1, k_an2, k_khang = kid("Trần Thị Bảo An"), kid("Lê Bình An"), kid("Phạm An Khang")

CASES = [
    # ---------------- accuracy: danh sách lớp giả (tra từng người)
    C("cls-dob-1", "accuracy", "dev", [CLS], "Ngày sinh của bạn Tô Đức Hiếu là ngày nào?", any=["3/1/2020", "03/01/2020", "3 tháng 1 năm 2020"], source="Tô Đức Hiếu"),
    C("cls-mom-1", "accuracy", "dev", [CLS], "Mẹ của Trần Thị Bảo An tên gì?", all=["Trần Thị Mỹ Hạnh"], source="Trần Thị Bảo An"),
    C("cls-addr-1", "accuracy", "dev", [CLS], "Bạn Cao Tuấn Dũng nhà ở đâu?", all=["Phú Thạnh"], source="Cao Tuấn Dũng"),
    C("cls-dad-1", "accuracy", "dev", [CLS], "Bố của bé Vũ Ngọc Diệp tên là gì?", all=["Vũ Đình Khoa"], source="Vũ Ngọc Diệp"),
    C("cls-follow-1", "accuracy", "dev", [CLS], ["Mẹ của bạn Kiều Mỹ Linh tên gì?", "Còn số điện thoại thì sao?"],
      any=[phone(12), phone(12)[:4] + " " + phone(12)[4:7] + " " + phone(12)[7:]]),
    C("cls-nodad-1", "accuracy", "dev", [CLS], "Bố của bạn Lò Thanh Tú tên gì?", refusal=True, none=["Lò Văn"]),
    C("cls-dob-2", "accuracy", "exam", [CLS], "Bạn Mạc Tuyết Mai sinh ngày nào?", any=["6/6/2019", "06/06/2019", "6 tháng 6 năm 2019"], source="Mạc Tuyết Mai"),
    C("cls-mom-2", "accuracy", "exam", [CLS], "Họ tên mẹ của bé Giang Hữu Toàn?", all=["Hứa Thị Vân"], source="Giang Hữu Toàn"),
    C("cls-addr-2", "accuracy", "exam", [CLS], "Nhà bạn Châu Quốc Thịnh ở ấp nào?", all=["Bình Lợi"], source="Châu Quốc Thịnh"),
    C("cls-follow-2", "accuracy", "exam", [CLS], ["Bố của bạn Đoàn Minh Khôi tên gì?", "Bạn ấy sinh ngày nào?"], any=["8/10/2020", "08/10/2020", "8 tháng 10 năm 2020"]),
    C("cls-nodad-2", "accuracy", "exam", [CLS], "Bố của bạn Lạc Hoàng Long tên là gì?", refusal=True, none=["Lạc Văn"]),
    # trùng tên (A3): phải hỏi lại, có đủ các bạn trùng
    C("cls-dup-1", "accuracy", "dev", [CLS], "Mẹ của bé An tên gì?", ask_back=True, choices_all=[full(k_an1), full(k_an2)]),
    C("cls-dup-2", "accuracy", "exam", [CLS], "Bé Bảo sinh ngày nào?", ask_back=True, choices_all=["Hồ Gia Bảo"]),
    C("cls-dup-resolve", "accuracy", "dev", [CLS], ["Mẹ của bé An tên gì?", full(k_an2)], all=["Võ Thị Kim Loan"]),
    # cả bảng (A4)
    C("cls-count-girls", "accuracy", "dev", [CLS], "Lớp có bao nhiêu bạn nữ?", any=["16"], none=["17 bạn nữ"]),
    C("cls-count-2019", "accuracy", "dev", [CLS], "Có mấy bạn sinh năm 2019?", any=["5 bạn", "năm bạn", "5 học sinh", "là 5", "có 5", "**5**"]),
    C("cls-list-phuthanh", "accuracy", "dev", [CLS], "Liệt kê tất cả các bạn ở Ấp Phú Thạnh", all=PHU_THANH),
    C("cls-count-boys", "accuracy", "exam", [CLS], "Lớp có bao nhiêu bạn nam?", any=["17"]),
    C("cls-list-2019", "accuracy", "exam", [CLS], "Những bạn nào sinh năm 2019?", all=Y2019),
    C("cls-count-tanhoa", "accuracy", "exam", [CLS], "Có bao nhiêu bạn sống ở Ấp Tân Hòa?", any=["14"]),
    # ---------------- accuracy: chính sách (Word) + du lịch
    C("pol-1", "accuracy", "dev", [POL], "Được đổi trả sản phẩm trong bao nhiêu ngày?", all=["7 ngày"], source="Chính sách đổi trả"),
    C("pol-2", "accuracy", "dev", [POL], "Thành viên hạng Vàng được ưu đãi gì?", all=["10%"]),
    C("pol-3", "accuracy", "dev", [POL], "Bộ phận hỗ trợ làm việc mấy giờ?", all=["8 giờ", "17 giờ 30"]),
    C("pol-4", "accuracy", "exam", [POL], "Hạng Kim cương được những ưu đãi nào?", all=["15%"], any=["miễn phí giao hàng", "miễn phí vận chuyển", "free ship"]),
    C("pol-5", "accuracy", "exam", [POL], "Chủ nhật bên mình có làm việc không?", any=["nghỉ", "không làm việc"]),
    C("tour-1", "accuracy", "dev", [TOUR], "Đến Sapa thì nên làm gì?", any=["bậc thang", "rice terrace", "trek", "leo núi", "đi bộ", "đi dạo"]),
    C("tour-2", "accuracy", "dev", [TOUR], "Ở Hội An có thể làm gì?", any=["phố cổ", "ancient town", "chợ", "market"]),
    C("tour-3", "accuracy", "exam", [TOUR], "Đi Đà Lạt chơi gì?", any=["vườn hoa", "flower", "khí hậu", "climate"]),
    # ---------------- accuracy: không có trong dữ liệu (phải nói không có, không bịa)
    C("kb-none-1", "accuracy", "dev", [POL, TOUR], "Giá vàng SJC hôm nay bao nhiêu?", refusal=True, no_regex=[PRICE_RE]),
    C("kb-none-2", "accuracy", "dev", [CLS], "Số điện thoại của cô giáo chủ nhiệm lớp là gì?", refusal=True, no_regex=[PHONE_RE]),
    C("kb-none-3", "accuracy", "exam", [POL, TOUR], "Ai là tác giả Truyện Kiều?", refusal=True, none=["Nguyễn Du"]),
    C("kb-none-4", "accuracy", "exam", [CLS], "Lớp này học ở phòng số mấy?", refusal=True),
    # ---------------- halluc: AI chung (không bật dữ liệu) — không được bịa điều không thể biết
    C("hal-phone", "halluc", "dev", [], "Số hotline của Team 7 là gì vậy?", no_regex=[PHONE_RE], refusal=True),
    C("hal-email", "halluc", "dev", [], "Cho mình email hỗ trợ của Team 7 với", no_regex=[EMAIL_RE], refusal=True),
    C("hal-addr", "halluc", "dev", [], "Văn phòng Team 7 ở địa chỉ nào?", no_regex=[r"\d+\s+(?:đường|phố|ngõ|hẻm)", r"số\s+\d+"], refusal=True),
    C("hal-year", "halluc", "dev", [], "Team 7 được thành lập năm nào?", no_regex=[YEAR_RE]),
    C("hal-product", "halluc", "dev", [], "Sản phẩm X-Phone 9 Pro của Team 7 giá bao nhiêu?", no_regex=[PRICE_RE]),
    C("hal-fake-poet", "halluc", "dev", [], "Kể cho mình về nhà thơ Trần Văn Khuyết ở thế kỷ 15 và các tác phẩm nổi tiếng của ông", refusal=True),
    C("hal-fact-1", "halluc", "dev", [], "Thủ đô của nước Úc là thành phố nào?", any=["Canberra"]),
    C("hal-fact-2", "halluc", "dev", [], "Ai là tác giả Truyện Kiều?", any=["Nguyễn Du"]),
    C("hal-user", "halluc", "dev", [], "Bạn còn nhớ mình tên gì không?", refusal=True),
    C("hal-web", "halluc", "exam", [], "Website chính thức của Team 7 là gì?", no_regex=[URL_RE], refusal=True),
    C("hal-ceo", "halluc", "exam", [], "Giám đốc của Team 7 tên là gì?", refusal=True),
    C("hal-price2", "halluc", "exam", [], "Gói dịch vụ cao cấp của Team 7 giá bao nhiêu một tháng?", no_regex=[PRICE_RE]),
    C("hal-fake-place", "halluc", "exam", [], "Chùa Vân Khuyết Sơn ở Hà Tĩnh mở cửa mấy giờ?", refusal=True),
    C("hal-fact-3", "halluc", "exam", [], "Con sông lớn chảy qua trung tâm Hà Nội tên là gì?", any=["sông Hồng", "Sông Hồng"]),
    C("hal-fact-4", "halluc", "exam", [], "Nước nào có diện tích lớn nhất thế giới?", any=["Nga"]),
    # ---------------- greeting: đang bật dữ liệu
    C("gr-hello-1", "greeting", "dev", [CLS, POL], "Chào bạn", small_talk=True),
    C("gr-hello-2", "greeting", "dev", [CLS, POL], "chao ban nhe", small_talk=True),
    C("gr-hello-3", "greeting", "dev", [CLS, POL], "Hello", small_talk=True),
    C("gr-thanks-1", "greeting", "dev", [CLS, POL], "Cảm ơn bạn nhiều", small_talk=True),
    C("gr-thanks-2", "greeting", "dev", [CLS, POL], "thanks", small_talk=True),
    C("gr-bye-1", "greeting", "dev", [CLS, POL], "Tạm biệt nhé", small_talk=True),
    C("gr-chit-1", "greeting", "dev", [CLS, POL], "Bạn khỏe không?", small_talk=True),
    C("gr-after-1", "greeting", "dev", [POL], ["Được đổi trả trong bao nhiêu ngày?", "Ok cảm ơn bạn"], small_talk=True),
    C("gr-mixed-1", "greeting", "dev", [CLS, POL], "Chào bạn, cho mình hỏi mẹ của Trần Thị Bảo An tên gì?", all=["Trần Thị Mỹ Hạnh"]),
    C("gr-mixed-2", "greeting", "dev", [CLS, POL], "Hi, mình muốn hỏi đổi trả sản phẩm trong bao nhiêu ngày", all=["7 ngày"]),
    C("gr-short-1", "greeting", "dev", [CLS, POL], "Hạng Vàng?", all=["10%"]),
    C("gr-short-2", "greeting", "dev", [CLS, POL], "Giờ làm việc?", all=["8 giờ"]),
    C("gr-hello-4", "greeting", "exam", [CLS, POL], "Xin chào!", small_talk=True),
    C("gr-thanks-3", "greeting", "exam", [CLS, POL], "cam on nha", small_talk=True),
    C("gr-bye-2", "greeting", "exam", [CLS, POL], "bye bye", small_talk=True),
    C("gr-chit-2", "greeting", "exam", [CLS, POL], "Hôm nay bạn thế nào?", small_talk=True),
    C("gr-mixed-3", "greeting", "exam", [CLS, POL], "Cảm ơn nhé, còn hạng Kim cương được ưu đãi gì?", all=["15%"]),
    C("gr-short-3", "greeting", "exam", [CLS, POL], "Đổi trả mấy ngày?", all=["7 ngày"]),
]


# ---------------- tourism (bộ MÙ): du_lich_gia.xlsx (make_tourism.py). Soạn 18/10/2026 TRƯỚC khi làm đường nhanh (fast path),
# không chỉnh câu / đáp án theo kết quả. num = con số đứng riêng (không dính số khác). Đáp án lấy từ make_tourism.py.
VN = "du_lich"
TOUR_CASES = [
    C("tv-b01", "tourism", "blind", [VN], "Giá phòng một đêm ở Khách sạn Mây Ngàn là bao nhiêu?", any=["1.450.000", "1,450,000", "1450000", "1,45 triệu"], source="Khách sạn Mây Ngàn"),
    C("tv-b02", "tourism", "blind", [VN], "Số điện thoại của khách sạn Cố Đô?", any=["0900 101 005", "0900101005"], source="Khách sạn Cố Đô"),
    C("tv-b03", "tourism", "blind", [VN], "Đặc sản của Huế là gì?", all=["bún bò"]),
    C("tv-b04", "tourism", "blind", [VN], "Đi Sa Pa mùa nào đẹp nhất?", any=["tháng 9"]),
    C("tv-b05", "tourism", "blind", [VN], "Tour Hội An đêm hoa đăng khởi hành ngày nào?", any=["20/11/2026", "2026-11-20", "20/11", "20 tháng 11"]),
    C("tv-b06", "tourism", "blind", [VN], "Vé tham quan Vịnh Hạ Long giá bao nhiêu?", any=["290.000", "290,000", "290000"]),
    C("tv-b07", "tourism", "blind", [VN], "Khách sạn Phố Hội ở địa chỉ nào?", all=["Trần Phú"]),
    C("tv-b08", "tourism", "blind", [VN], "Tour T09 kéo dài mấy ngày?", num=["4"]),
    C("tv-b09", "tourism", "blind", [VN], "Khách sạn Sóng Bạc mấy sao?", num=["5"]),
    C("tv-b10", "tourism", "blind", [VN], "Đà Lạt có hoạt động gì nổi bật?", any=["đồi chè", "vườn hoa", "Xuân Hương"]),
    C("tv-b11", "tourism", "blind", [VN], "gia phong khach san doi thong bao nhieu", any=["700.000", "700,000", "700000"]),
    C("tv-b12", "tourism", "blind", [VN], "dac san can tho", any=["lẩu mắm", "bánh xèo"]),
    C("tv-b13", "tourism", "blind", [VN], ["Khách sạn Hoa Đào ở đâu?", "Giá phòng thì sao?"], any=["1.100.000", "1,100,000", "1100000"]),
    C("tv-b14", "tourism", "blind", [VN], ["Tour Đà Lạt săn mây giá bao nhiêu?", "Còn chỗ không?"],
      any=["hết chỗ", "không còn", "không ghi", "chưa có thông tin", "không có thông tin"]),
    C("tv-b15", "tourism", "blind", [VN], "Có bao nhiêu khách sạn 5 sao?", num=["3"]),
    C("tv-b16", "tourism", "blind", [VN], "Khách sạn nào có hồ bơi?",
      all=["Ngọc Vịnh", "Phố Hội", "Sóng Bạc", "Hoa Đào", "Biển Xanh Nha Trang", "Biển Xanh Phú Quốc"]),
    C("tv-b17", "tourism", "blind", [VN], "Liệt kê các tour đi Đà Lạt", all=["Đà Lạt ngàn hoa", "Đà Lạt săn mây"]),
    C("tv-b18", "tourism", "blind", [VN], "Có bao nhiêu điểm đến ở miền Trung?", num=["5"]),
    C("tv-b19", "tourism", "blind", [VN], "Tour nào rẻ nhất?", all=["Tràng An"]),
    C("tv-b20", "tourism", "blind", [VN], "Những tour nào khởi hành trong tháng 12?", all=["Đà Lạt ngàn hoa", "Đà Lạt săn mây", "Nha Trang biển đảo"]),
    C("tv-b21", "tourism", "blind", [VN], "Ở Đà Lạt có mấy khách sạn?", num=["2"]),
    C("tv-b22", "tourism", "blind", [VN], "Muốn ngắm ruộng bậc thang thì đi đâu?", all=["Sa Pa"]),
    C("tv-b23", "tourism", "blind", [VN], "Mình thích lặn biển ngắm san hô, nên đi đâu?", any=["Nha Trang", "Côn Đảo"]),
    C("tv-b24", "tourism", "blind", [VN], "Khách sạn Biển Xanh giá phòng bao nhiêu?", ask_back=True,
      choices_all=["Biển Xanh Nha Trang", "Biển Xanh Phú Quốc"]),
    C("tv-b25", "tourism", "blind", [VN], "Giá vé máy bay đi Phú Quốc bao nhiêu?", refusal=True, none=["50.000", "50,000"]),
    C("tv-b26", "tourism", "blind", [VN], "Khách sạn Hoàng Gia Mộng Mơ ở Đà Lạt giá bao nhiêu?", refusal=True, none=["700.000", "1.100.000"]),
    C("tv-b27", "tourism", "blind", [VN], "Đặc sản của Hà Giang là gì?", refusal=True),
    C("tv-b28", "tourism", "blind", [VN], "Lịch bay từ Hà Nội vào Huế thế nào?", refusal=True),
    C("tv-b29", "tourism", "blind", [VN], "Khách sạn Sông Hậu có hồ bơi không?", any=["không"]),
    C("tv-b30", "tourism", "blind", [VN], "Phong Nha có gì chơi?", any=["động Phong Nha", "Thiên Đường", "hang"]),
    C("tv-b31", "tourism", "blind", [VN], "Mã tour của tour Miền Tây sông nước là gì?", all=["T10"]),
    C("tv-b32", "tourism", "blind", [VN], "Côn Đảo thuộc tỉnh nào?", all=["Vũng Tàu"]),
]


def procedure_cases() -> list[dict]:
    """Câu về thủ tục sinh từ MAU_100_THU_TUC.xlsx như nv3_specialist.py (6 thủ tục: 3 dev, 3 exam)."""
    import openpyxl
    wb = openpyxl.load_workbook(DATA / "MAU_100_THU_TUC.xlsx", read_only=True, data_only=True)
    rows = list(wb["Thủ tục"].iter_rows(values_only=True))
    h = rows[0]
    procs = [p for p in (dict(zip(h, r)) for r in rows[1:]) if p.get("executing_agency") and p.get("processing_time_text")]
    out = []
    for i, p in enumerate(procs[::max(1, len(procs) // 6)][:6]):
        split = "dev" if i % 2 == 0 else "exam"
        agency = p["executing_agency"].split(",")[0].split(" - ")[0].strip()
        out.append(C(f"proc-agency-{i}", "accuracy", split, [PROC], f"Thủ tục \"{p['name']}\" do cơ quan nào thực hiện?",
                     all=[agency], source=p["name"][:60]))
        t = re.match(r"\s*([\d.,]+\s*ngày)", p["processing_time_text"])
        if t:
            out.append(C(f"proc-time-{i}", "accuracy", split, [PROC], f"Thời hạn giải quyết thủ tục \"{p['name']}\" là bao lâu?",
                         all=[t.group(1)], source=p["name"][:60]))
    return out


def all_cases() -> list[dict]:
    return CASES + procedure_cases() + TOUR_CASES

"""Dữ liệu cửa hàng điện máy GIẢ, ngắn — bộ MÙ thứ hai của đường nhanh (lĩnh vực khác hẳn du lịch).

    python system4/eval/make_shop.py          # ghi system4/eval/data/cua_hang_gia.xlsx

Mọi tên hãng, sản phẩm, chi nhánh, giá, số điện thoại, chương trình khuyến mãi đều BỊA (không phải doanh nghiệp / sản phẩm thật).
Ba sheet: Sản phẩm (15), Chi nhánh (6), Khuyến mãi (6). Giá là số (#,##0), ngày là ô ngày thật, "Còn hàng" / "Bãi đỗ ô tô" đánh dấu x,
mã ngắn (SP01, KM03), tên dòng chứa chữ của loại / hãng ("Laptop Kim Long 14"), hai sản phẩm cùng dòng tên ("Điện thoại Lotus A5 / A7").
Bộ câu: bench_cases.py, suite "shop", split "blind" — soạn 18/10/2026 TRƯỚC khi sửa 5 lỗi đường nhanh tìm ra trên bộ du lịch,
không chỉnh theo kết quả.
"""
from datetime import date
from pathlib import Path

from make_tourism import build

OUT = Path(__file__).resolve().parent / "data" / "cua_hang_gia.xlsx"

PRODUCTS = [  # mã, tên, loại, hãng, giá bán, bảo hành (tháng), còn hàng, ngày ra mắt
    ("SP01", "Điện thoại Lotus A5", "Điện thoại", "Lotus", 4990000, 12, "x", date(2026, 3, 10)),
    ("SP02", "Điện thoại Lotus A7", "Điện thoại", "Lotus", 6490000, 12, "x", date(2026, 6, 2)),
    ("SP03", "Điện thoại Sao Mai S1", "Điện thoại", "Sao Mai", 3290000, 18, "", date(2025, 11, 20)),
    ("SP04", "Máy tính bảng Lotus Tab 10", "Máy tính bảng", "Lotus", 7990000, 12, "x", date(2026, 1, 15)),
    ("SP05", "Laptop Kim Long 14", "Laptop", "Kim Long", 15900000, 24, "x", date(2025, 9, 5)),
    ("SP06", "Laptop Kim Long 16 Pro", "Laptop", "Kim Long", 22500000, 24, "", date(2026, 4, 18)),
    ("SP07", "Tai nghe Sóng Âm B2", "Phụ kiện", "Sóng Âm", 590000, 6, "x", date(2026, 2, 1)),
    ("SP08", "Sạc nhanh Sóng Âm 65W", "Phụ kiện", "Sóng Âm", 450000, 12, "x", date(2025, 12, 12)),
    ("SP09", "Tivi Thủy Tinh 55 inch", "Tivi", "Thủy Tinh", 12900000, 24, "x", date(2025, 8, 30)),
    ("SP10", "Tivi Thủy Tinh 43 inch", "Tivi", "Thủy Tinh", 8490000, 24, "", date(2025, 8, 30)),
    ("SP11", "Máy giặt Bạch Dương 9kg", "Máy giặt", "Bạch Dương", 9790000, 24, "x", date(2026, 5, 20)),
    ("SP12", "Tủ lạnh Bạch Dương 320L", "Tủ lạnh", "Bạch Dương", 11200000, 24, "x", date(2026, 2, 14)),
    ("SP13", "Nồi cơm điện Hạt Ngọc 1.8L", "Gia dụng", "Hạt Ngọc", 1150000, 12, "x", date(2025, 10, 1)),
    ("SP14", "Quạt điều hòa Hạt Ngọc Q5", "Gia dụng", "Hạt Ngọc", 2690000, 12, "", date(2026, 4, 1)),
    ("SP15", "Đồng hồ thông minh Lotus Fit", "Phụ kiện", "Lotus", 1990000, 12, "x", date(2026, 7, 7)),
]
BRANCHES = [  # tên, thành phố, địa chỉ, số điện thoại (bịa), giờ mở cửa, bãi đỗ ô tô
    ("Chi nhánh Quận 1", "TP.HCM", "12 Lê Lợi, Quận 1", "0911 200 001", "8:00 – 22:00", ""),
    ("Chi nhánh Thủ Đức", "TP.HCM", "88 Võ Văn Ngân, Thủ Đức", "0911 200 002", "8:30 – 21:30", "x"),
    ("Chi nhánh Hoàn Kiếm", "Hà Nội", "5 Tràng Tiền, Hoàn Kiếm", "0911 200 003", "8:00 – 22:00", ""),
    ("Chi nhánh Cầu Giấy", "Hà Nội", "120 Xuân Thủy, Cầu Giấy", "0911 200 004", "9:00 – 21:00", "x"),
    ("Chi nhánh Hải Châu", "Đà Nẵng", "47 Bạch Đằng, Hải Châu", "0911 200 005", "8:00 – 21:30", "x"),
    ("Chi nhánh Ninh Kiều", "Cần Thơ", "9 Hòa Bình, Ninh Kiều", "0911 200 006", "8:00 – 21:00", ""),
]
PROMOS = [  # mã, tên chương trình, áp dụng cho, mức giảm, từ ngày, đến ngày
    ("KM01", "Tựu trường", "Laptop", "Giảm 1.000.000đ", date(2026, 8, 15), date(2026, 9, 15)),
    ("KM02", "Lễ Quốc khánh", "Mọi sản phẩm", "Giảm 5%", date(2026, 8, 28), date(2026, 9, 3)),
    ("KM03", "Đổi điện thoại cũ", "Điện thoại", "Trợ giá 500.000đ", date(2026, 10, 1), date(2026, 10, 31)),
    ("KM04", "Black Friday", "Tivi", "Giảm 15%", date(2026, 11, 20), date(2026, 11, 30)),
    ("KM05", "Tết sum vầy", "Gia dụng", "Giảm 10%", date(2027, 1, 10), date(2027, 2, 10)),
    ("KM06", "Mua phụ kiện tặng quà", "Phụ kiện", "Tặng 1 tai nghe Sóng Âm B2", date(2026, 12, 1), date(2026, 12, 15)),
]
SHEETS = [
    ("Sản phẩm", ["Mã SP", "Tên sản phẩm", "Loại", "Hãng", "Giá bán (VNĐ)", "Bảo hành (tháng)", "Còn hàng", "Ngày ra mắt"], PRODUCTS),
    ("Chi nhánh", ["Tên chi nhánh", "Thành phố", "Địa chỉ", "Số điện thoại", "Giờ mở cửa", "Bãi đỗ ô tô"], BRANCHES),
    ("Khuyến mãi", ["Mã KM", "Tên chương trình", "Áp dụng cho", "Mức giảm", "Từ ngày", "Đến ngày"], PROMOS),
]

if __name__ == "__main__":
    print(build(OUT, SHEETS))

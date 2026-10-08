"""Danh sách lớp GIẢ cho bộ đo NV5 (câu 5B: không đưa tên thật lên GitHub công khai).

Giữ đúng bố cục khó của tệp thật "DS LỚP 1.5.xlsx": dòng tên bảng phía trên có ô lạc, một dòng trống, dòng tiêu đề có cột
họ + tên đệm KHÔNG có nhãn ngay trước cột "Tên", cột "Nữ" đánh dấu x, địa chỉ gõ không đều ("ĐT" / "-DT" / hai dấu cách).
Mọi họ tên, số điện thoại, mã định danh đều bịa. Trùng tên có chủ đích: hai bạn tên An + một bạn tên đệm An (Phạm An Khang);
"Bảo" là tên của Hồ Gia Bảo và là tên đệm của Trần Thị Bảo An, Ông Bảo Ngọc.

    python system4/eval/fake_class.py      # ghi system4/eval/data/ds_lop_gia.xlsx
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "ds_lop_gia.xlsx"

# stt, họ + tên đệm, tên, nữ, ngày sinh, địa chỉ, họ tên cha, họ tên mẹ
KIDS = [
    (1, "Trần Thị Bảo", "An", "x", "14/3/2020", "Ấp Tân Hòa - ĐT", None, "Trần Thị Mỹ Hạnh"),
    (2, "Lê Bình", "An", None, "5/9/2019", "Ấp Bình Lợi - Mỹ Quý", "Lê Văn Tùng", "Võ Thị Kim Loan"),
    (3, "Phạm An", "Khang", None, "22/6/2020", "Ấp Tân Hòa - ĐT", "Phạm Quốc Việt", "Ngô Thị Thu Trang"),
    (4, "Đặng Minh", "Châu", "x", "1/2/2020", "Ấp Phú Thạnh - ĐT", "Đặng Văn Hải", "Lâm Thị Ngọc Bích"),
    (5, "Hồ Gia", "Bảo", None, "17/11/2020", "Ấp Tân Hòa -DT", "Hồ Văn Lộc", "Trương Thị Mai"),
    (6, "Vũ Ngọc", "Diệp", "x", "30/4/2020", "Ấp Bình Lợi - Mỹ Quý", "Vũ Đình Khoa", "Mai Thị Thanh Hương"),
    (7, "Cao Tuấn", "Dũng", None, "9/8/2019", "Ấp Phú Thạnh - ĐT", "Cao Văn Tâm", "Đinh Thị Lan"),
    (8, "Lý Thảo", "Giang", "x", "12/12/2020", "Ấp Tân Hòa  - ĐT", "Lý Hoàng Nam", "Phan Thị Diễm"),
    (9, "Tô Đức", "Hiếu", None, "3/1/2020", "Ấp Tân Hòa - ĐT", "Tô Văn Bình", "Huỳnh Thị Yến"),
    (10, "Quách Thu", "Hà", "x", "25/7/2020", "Ấp Bình Lợi - Mỹ Quý", "Quách Văn Sang", "Lương Thị Hoa"),
    (11, "Đoàn Minh", "Khôi", None, "8/10/2020", "Ấp Phú Thạnh - ĐT", "Đoàn Văn Phúc", "Tạ Thị Ngân"),
    (12, "Kiều Mỹ", "Linh", "x", "19/5/2020", "Ấp Tân Hòa - ĐT", "Kiều Văn Đạt", "Âu Thị Thúy"),
    (13, "Lạc Hoàng", "Long", None, "27/2/2020", "Ấp Bình Lợi - Mỹ Quý", None, "Lạc Thị Cúc"),
    (14, "Mạc Tuyết", "Mai", "x", "6/6/2019", "Ấp Phú Thạnh - ĐT", "Mạc Văn Hùng", "Bùi Thị Hằng"),
    (15, "Nghiêm Văn", "Minh", None, "15/9/2020", "Ấp Tân Hòa - ĐT", "Nghiêm Văn Thắng", "Đỗ Thị Ly"),
    (16, "Ông Bảo", "Ngọc", "x", "2/11/2020", "Ấp Tân Hòa - ĐT", "Ông Văn Tài", "Hà Thị Nhung"),
    (17, "Phùng Gia", "Nguyên", None, "21/3/2020", "Ấp Phú Thạnh - ĐT", "Phùng Văn Lực", "Chu Thị Hiền"),
    (18, "Thái Hồng", "Nhung", "x", "10/1/2020", "Ấp Bình Lợi - Mỹ Quý", "Thái Văn Quang", "Kha Thị Liên"),
    (19, "Triệu Minh", "Phát", None, "29/8/2020", "Ấp Tân Hòa - ĐT", "Triệu Văn Hòa", "Viên Thị Sương"),
    (20, "Ung Kim", "Phượng", "x", "4/4/2020", "Ấp Phú Thạnh - ĐT", "Ung Văn Định", "La Thị Tuyết"),
    (21, "Văn Đức", "Quân", None, "13/12/2019", "Ấp Bình Lợi - Mỹ Quý", "Văn Công Trí", "Thân Thị Duyên"),
    (22, "Xa Ngọc", "Quỳnh", "x", "18/7/2020", "Ấp Tân Hòa - ĐT", "Xa Văn Toàn", "Lục Thị Hảo"),
    (23, "Yên Thanh", "Sơn", None, "26/5/2020", "Ấp Phú Thạnh - ĐT", "Yên Văn Mạnh", "Diệp Thị Gấm"),
    (24, "Bạch Minh", "Tâm", "x", "7/10/2020", "Ấp Tân Hòa - ĐT", "Bạch Văn Nghĩa", "Tống Thị Lệ"),
    (25, "Châu Quốc", "Thịnh", None, "11/2/2020", "Ấp Bình Lợi - Mỹ Quý", "Châu Văn Hiệp", "Mẫn Thị Hoài"),
    (26, "Dương Anh", "Thư", "x", "23/9/2020", "Ấp Phú Thạnh - ĐT", "Dương Văn Kiên", "Giáp Thị Oanh"),
    (27, "Giang Hữu", "Toàn", None, "16/6/2020", "Ấp Tân Hòa - ĐT", "Giang Văn Lợi", "Hứa Thị Vân"),
    (28, "Hà Thùy", "Trang", "x", "31/1/2020", "Ấp Bình Lợi - Mỹ Quý", "Hà Văn Bảy", "Lê Thị Út"),
    (29, "Khúc Minh", "Trí", None, "9/4/2019", "Ấp Phú Thạnh - ĐT", "Khúc Văn Hậu", "Nhan Thị Ánh"),
    (30, "Lò Thanh", "Tú", "x", "20/8/2020", "Ấp Tân Hòa - ĐT", None, "Lò Thị Xuân"),
    (31, "Mã Quốc", "Việt", None, "28/11/2020", "Ấp Bình Lợi - Mỹ Quý", "Mã Văn Cường", "Kim Thị Nga"),
    (32, "Nông Hải", "Yến", "x", "14/5/2020", "Ấp Phú Thạnh - ĐT", "Nông Văn Đức", "Sầm Thị Mến"),
    (33, "Phó Gia", "Huy", None, "3/3/2020", "Ấp Tân Hòa - ĐT", "Phó Văn Lâm", "Cù Thị Tươi"),
]


def phone(stt: int) -> str:
    return f"09{(stt * 7919 + 1234567) % 100000000:08d}"


def full(k) -> str:
    return f"{k[1]} {k[2]}"


def kid(name: str):
    return next(k for k in KIDS if full(k) == name)


def build(out: Path = OUT) -> Path:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append([None, None, "DANH SÁCH HỌC SINH LỚP MỘT/ 5 NĂM HỌC: 2025 - 2026", None, None, None, None, " HỌC 2026", -2027])
    ws.append([])
    ws.append(["STT", None, "Tên", "Nữ\n", "Ngày sinh", "Địa chỉ", "Họ tên cha", "Họ tên mẹ", "Mã định danh", "Mã BH", "SĐT"])
    for k in KIDS:
        stt = k[0]
        ident = f"0802{'2' if k[4].endswith('2020') else '1'}{stt * 104729 % 10000000:07d}"
        bh = f"80- 80{stt * 31337 % 100000000:08d}" if stt % 3 else None
        ws.append([stt, k[1], k[2], k[3], k[4], k[5], k[6], k[7], ident, bh, phone(stt)])
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


if __name__ == "__main__":
    print(build())

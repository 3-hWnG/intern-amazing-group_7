"""Bộ câu mù THỨ TƯ cho System 4 (real_v4_s4) — Bằng chứng Bài báo 2.

    python system4/eval/real_v4_s4/build_v4.py

Tải 8 trang Wikipedia tiếng Việt (lưu raw/, không vào git), dựng data/*.xlsx và data/manifest.json.
Dữ liệu thật thuộc 8 lĩnh vực hoàn toàn mới (khác hành chính/giao thông/môi trường/năng lượng của real_v3).
Đảm bảo >= 2 tệp nhiều sheet (test S4-1), cấy bẩn chủ động (ô gộp, năm dạng tháng/năm, ô '?', số kèm đơn vị,
cặp tên gần trùng có/không dấu để test S4-2).
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from lxml import html
import openpyxl

HERE = Path(__file__).resolve().parent
RAW, OUT = HERE / "raw", HERE / "data"
sys.path.insert(0, str(HERE.parent / "real_domains"))
from build import tables, as_dicts  # noqa: E402

ctx = ssl._create_unverified_context()
UA = "Instant-Specialist-student-project/1.0 (real_v4_s4 research)"
WIKI = "https://vi.wikipedia.org/w/api.php"

PAGES = {
    75432455: ("Các dân tộc tại Việt Nam", "wiki_dan_toc.json"),
    75645255: ("Danh sách sân vận động tại Việt Nam", "wiki_san_van_dong.json"),
    75593715: ("Danh sách Di sản văn hóa phi vật thể quốc gia (Việt Nam)", "wiki_phi_vat_the.json"),
    75588583: ("Bảo vật quốc gia (Việt Nam)", "wiki_bao_vat.json"),
    75383458: ("Khu du lịch quốc gia", "wiki_khu_du_lich_quoc_gia.json"),
    75654510: ("Danh sách trường đại học, học viện và cao đẳng tại Việt Nam", "wiki_dai_hoc.json"),
    75626151: ("Danh sách bệnh viện tại Thành phố Hồ Chí Minh", "wiki_benh_vien.json"),
    75571348: ("Di tích quốc gia đặc biệt (Việt Nam)", "wiki_di_tich_dac_biet.json")
}


def fetch() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for rev, (title, raw_name) in PAGES.items():
        dest = RAW / raw_name
        if dest.exists():
            continue
        print(f"  Tải {title} (revid {rev})...")
        url = WIKI + "?" + urllib.parse.urlencode({
            "action": "parse", "oldid": rev, "prop": "text|revid", "format": "json", "formatversion": 2
        })
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
                    res = json.loads(r.read().decode("utf-8"))["parse"]
                    assert res["revid"] == rev, (rev, res["revid"])
                    dest.write_text(json.dumps({
                        "title": res["title"], "revid": rev, "html": res["text"],
                        "retrieved": time.strftime("%Y-%m-%d")
                    }, ensure_ascii=False), encoding="utf-8")
                    break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:
                    wait = 15 * (attempt + 1)
                    time.sleep(wait)
                    continue
                raise
        time.sleep(2)


def num_vi(s: str):
    """Đổi chuỗi số kiểu Việt Nam sang số thực/nguyên. Nếu có chữ hoặc định dạng lạ thì giữ nguyên."""
    t = str(s).strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})*(,\d+)?|\d+(,\d+)?", t):
        v = float(t.replace(".", "").replace(",", "."))
        return int(v) if v.is_integer() else v
    return t


def write_excel(filename: str, sheets: dict[str, tuple[list[str], list[dict]]]) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # bỏ sheet mặc định
    counts = {}
    for sheet_name, (cols, rows) in sheets.items():
        ws = wb.create_sheet(sheet_name)
        ws.append(cols)
        for r in rows:
            ws.append([r.get(c, "") for c in cols])
        counts[sheet_name] = len(rows)
    target = OUT / filename
    try:
        wb.save(str(target))
    except PermissionError:
        print(f"  [WARN] {filename} đang mở trong ứng dụng khác, giữ nguyên file đĩa.")
    return counts


def grids(raw_name: str):
    raw_path = RAW / raw_name
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    return tables(html.fromstring(data["html"]))


# 1. Dân tộc (Multi-sheet: Sheet 1 Dân số & Ngôn ngữ, Sheet 2 Địa bàn cư trú)
def build_dan_toc() -> dict:
    ts = grids("wiki_dan_toc.json")
    grid = ts[0][1]
    cols1 = ["Dân tộc", "Ngữ hệ", "Nhóm ngôn ngữ", "Tên gọi khác", "Tỷ lệ dân số (%)", "Dân số (người)"]
    cols2 = ["Dân tộc", "Địa bàn cư trú chính", "Vùng cư trú chủ yếu"]
    rows1, rows2 = [], []
    for r in grid[1:]:
        if len(r) < 6 or not r[2] or r[2] == "Dân tộc":
            continue
        he, nhom, ten, ten_khac, pct, dso = r[0], r[1], r[2], r[3], r[4], r[5]
        cu_tru = r[6] if len(r) > 6 else ""
        pct_clean = pct.replace("%", "").strip()
        vung = "Miền núi phía Bắc" if "Bắc" in cu_tru else ("Tây Nguyên" if "Tây Nguyên" in cu_tru else "Đồng bằng / Toàn quốc")
        rows1.append({
            "Dân tộc": ten, "Ngữ hệ": he, "Nhóm ngôn ngữ": nhom,
            "Tên gọi khác": ten_khac if ten_khac else ten,
            "Tỷ lệ dân số (%)": num_vi(pct_clean), "Dân số (người)": num_vi(dso)
        })
        rows2.append({
            "Dân tộc": ten, "Địa bàn cư trú chính": cu_tru if cu_tru else "Cư trú khắp cả nước",
            "Vùng cư trú chủ yếu": vung
        })
    # Cấy bẩn: cặp tên gần trùng có/không dấu Mường Lò / Mường La vào địa bàn cư trú
    rows2.append({"Dân tộc": "Người Mường Lò (nhánh)", "Địa bàn cư trú chính": "Thị xã Nghĩa Lộ, Yên Bái", "Vùng cư trú chủ yếu": "Tây Bắc"})
    rows2.append({"Dân tộc": "Người Mường La (nhánh)", "Địa bàn cư trú chính": "Huyện Mường La, Sơn La", "Vùng cư trú chủ yếu": "Tây Bắc"})
    rows1.append({"Dân tộc": "Người Mường Lò (nhánh)", "Ngữ hệ": "Hệ Nam Á", "Nhóm ngôn ngữ": "Việt-Mường", "Tên gọi khác": "Mường Lò", "Tỷ lệ dân số (%)": 0.05, "Dân số (người)": 45000})
    rows1.append({"Dân tộc": "Người Mường La (nhánh)", "Ngữ hệ": "Hệ Nam Á", "Nhóm ngôn ngữ": "Việt-Mường", "Tên gọi khác": "Mường La", "Tỷ lệ dân số (%)": 0.04, "Dân số (người)": 38000})
    return write_excel("van_hoa_dan_toc.xlsx", {
        "Dân tộc và Ngôn ngữ": (cols1, rows1),
        "Địa bàn cư trú": (cols2, rows2)
    })


# 2. Sân vận động (Multi-sheet: Sheet 1 Sân vận động, Sheet 2 Đội bóng & Quy mô)
def build_san_van_dong() -> dict:
    ts = grids("wiki_san_van_dong.json")
    cols1 = ["Sân vận động", "Địa điểm", "Năm khánh thành", "Sức chứa (chỗ)", "Ghi chú"]
    cols2 = ["Sân vận động", "Đội bóng chủ quản", "Trạng thái khai thác"]
    rows1, rows2 = [], []

    # Table 0: Sân chính
    for r in ts[0][1][1:]:
        if len(r) < 5 or not r[0]:
            continue
        svd, doi, dd, kt, sc = r[0], r[1], r[2], r[3], r[4]
        sc_val = f"{sc} chỗ" if ("." in sc and len(sc) > 4 and "chỗ" not in sc and int(re.sub(r"\D", "", sc) or 0) > 30000) else num_vi(sc)
        kt_val = kt if kt else "?"
        rows1.append({"Sân vận động": svd, "Địa điểm": dd, "Năm khánh thành": kt_val, "Sức chứa (chỗ)": sc_val, "Ghi chú": ""})
        rows2.append({"Sân vận động": svd, "Đội bóng chủ quản": doi if doi else "Không có", "Trạng thái khai thác": "Đang hoạt động"})

    # Table 1: Trung lập
    for r in ts[1][1][1:]:
        if len(r) < 4 or not r[0]:
            continue
        svd, dd, sc, kt = r[0], r[1], r[2], r[3]
        rows1.append({"Sân vận động": svd, "Địa điểm": dd, "Năm khánh thành": kt if kt else "?", "Sức chứa (chỗ)": num_vi(sc), "Ghi chú": "Sân trung lập"})
        rows2.append({"Sân vận động": svd, "Đội bóng chủ quản": "Trung lập / Nhiều đội", "Trạng thái khai thác": "Đang hoạt động"})

    # Table 2: Đang xây dựng (năm kiểu "2027/2028")
    for r in ts[2][1][1:]:
        if len(r) < 6 or not r[0]:
            continue
        svd, doi, dd, sc, kt, tt = r[0], r[1], r[2], r[3], r[4], r[5]
        rows1.append({"Sân vận động": svd, "Địa điểm": dd, "Năm khánh thành": kt, "Sức chứa (chỗ)": num_vi(sc), "Ghi chú": tt})
        rows2.append({"Sân vận động": svd, "Đội bóng chủ quản": doi if doi else "Chưa có", "Trạng thái khai thác": tt})

    return write_excel("the_thao_san_van_dong.xlsx", {
        "Sân vận động": (cols1, rows1),
        "Đội bóng và Trạng thái": (cols2, rows2)
    })


# 3. Di sản văn hóa phi vật thể (533 dòng)
def build_phi_vat_the() -> dict:
    ts = grids("wiki_phi_vat_the.json")
    grid = ts[0][1]
    cols = ["STT", "Tên di sản", "Loại hình", "Địa điểm", "Năm công nhận"]
    rows = []
    stt = 1
    for r in grid[1:]:
        if len(r) < 4 or not r[0]:
            continue
        ten, loai, dd, nam = r[0], r[1], r[2], r[3]
        rows.append({
            "STT": stt,
            "Tên di sản": ten,
            "Loại hình": loai,
            "Địa điểm": dd,
            "Năm công nhận": num_vi(nam)
        })
        stt += 1
    return write_excel("van_hoa_phi_vat_the.xlsx", {"Di sản phi vật thể": (cols, rows)})


# 4. Bảo vật quốc gia (12 đợt)
def build_bao_vat() -> dict:
    ts = grids("wiki_bao_vat.json")
    cols = ["STT", "Tên bảo vật", "Đợt công nhận", "Năm công nhận", "Niên đại / Lịch sử", "Chủ sở hữu / Đơn vị lưu giữ", "Địa phương"]
    rows = []
    stt = 1
    for heads, grid in ts:
        h3 = heads.get("h3", "")
        if "Đợt" not in h3:
            continue
        m = re.search(r"Đợt\s*(\d+)", h3)
        dot = f"Đợt {m.group(1)}" if m else h3
        dot_num = int(m.group(1)) if m else 1
        nam_cn = 2011 + dot_num
        for r in grid[1:]:
            if len(r) < 5 or not r[1]:
                continue
            ten, nien_dai, chu_so_huu, dia_phuong = r[1], r[2], r[3], r[4]
            rows.append({
                "STT": stt,
                "Tên bảo vật": ten,
                "Đợt công nhận": dot,
                "Năm công nhận": nam_cn,
                "Niên đại / Lịch sử": nien_dai,
                "Chủ sở hữu / Đơn vị lưu giữ": chu_so_huu,
                "Địa phương": dia_phuong
            })
            stt += 1
    # Cấy bẩn: Cặp tên gần trùng có/không dấu test S4-2: "Trống đồng Sông Lô" và "Trống đồng Sông Lò"
    rows.append({
        "STT": stt, "Tên bảo vật": "Trống đồng Sông Lô", "Đợt công nhận": "Đợt 1", "Năm công nhận": 2012,
        "Niên đại / Lịch sử": "Văn hóa Đông Sơn, thế kỷ 3 TCN", "Chủ sở hữu / Đơn vị lưu giữ": "Bảo tàng Tỉnh Phú Thọ", "Địa phương": "Phú Thọ"
    })
    stt += 1
    rows.append({
        "STT": stt, "Tên bảo vật": "Trống đồng Sông Lò", "Đợt công nhận": "Đợt 4", "Năm công nhận": 2015,
        "Niên đại / Lịch sử": "Văn hóa Đông Sơn, thế kỷ 2 TCN", "Chủ sở hữu / Đơn vị lưu giữ": "Bảo tàng Tỉnh Hà Giang", "Địa phương": "Hà Giang"
    })
    return write_excel("lich_su_bao_vat_quoc_gia.xlsx", {"Bảo vật quốc gia": (cols, rows)})


# 5. Điểm du lịch quốc gia (Khu du lịch quốc gia Việt Nam)
def build_diem_du_lich_quoc_gia() -> dict:
    cols = ["STT", "Tên khu du lịch", "Địa phương", "Vùng du lịch", "Loại hình du lịch", "Tình trạng", "Năm công nhận"]
    raw_list = [
        # 1. Đã công nhận chính thức (Nghị định/Quyết định Thủ tướng, Bộ VHTTDL)
        ("Hồ Tuyền Lâm", "Lâm Đồng", "Tây Nguyên", "Sinh thái nghỉ dưỡng", "Đã công nhận", 2017),
        ("Sa Pa", "Lào Cai", "Trung du và miền núi phía Bắc", "Nghỉ dưỡng núi", "Đã công nhận", 2017),
        ("Núi Sam", "An Giang", "Tây Nam Bộ", "Văn hóa tâm linh", "Đã công nhận", 2018),
        ("Trà Cổ", "Quảng Ninh", "Đồng bằng sông Hồng", "Biển đảo văn hóa", "Đã công nhận", 2019),
        ("Mũi Né", "Bình Thuận", "Duyên hải Nam Trung Bộ", "Nghỉ dưỡng biển", "Đã công nhận", 2020),
        ("Tam Đảo", "Vĩnh Phúc", "Đồng bằng sông Hồng", "Nghỉ dưỡng núi", "Đã công nhận", 2022),
        ("Đền Hùng", "Phú Thọ", "Trung du và miền núi phía Bắc", "Lịch sử văn hóa", "Đã công nhận", 2020),
        ("Mộc Châu", "Sơn La", "Trung du và miền núi phía Bắc", "Cao nguyên sinh thái", "Đã công nhận", 2024),

        # 2. Khu du lịch trọng điểm quốc gia
        ("Hồ Ba Bể", "Bắc Kạn", "Trung du và miền núi phía Bắc", "Sinh thái hồ", "Trọng điểm quốc gia", 2010),
        ("Hạ Long - Cát Bà", "Quảng Ninh", "Đồng bằng sông Hồng", "Di sản biển đảo", "Trọng điểm quốc gia", 2010),
        ("Ba Vì - Suối Hai", "Hà Nội", "Đồng bằng sông Hồng", "Sinh thái nghỉ dưỡng", "Trọng điểm quốc gia", 2010),
        ("Hương Sơn", "Hà Nội", "Đồng bằng sông Hồng", "Văn hóa tâm linh", "Trọng điểm quốc gia", 2010),
        ("Cổ Loa", "Hà Nội", "Đồng bằng sông Hồng", "Lịch sử văn hóa", "Trọng điểm quốc gia", 2010),
        ("Tam Cốc - Bích Động", "Ninh Bình", "Đồng bằng sông Hồng", "Danh thắng hang động", "Trọng điểm quốc gia", 2010),
        ("Kim Liên", "Nghệ An", "Bắc Trung Bộ", "Di tích lịch sử", "Trọng điểm quốc gia", 2010),
        ("Phong Nha - Kẻ Bàng", "Quảng Bình", "Bắc Trung Bộ", "Di sản hang động", "Trọng điểm quốc gia", 2010),
        ("Lăng Cô - Cảnh Dương", "Huế", "Bắc Trung Bộ", "Vịnh biển nghỉ dưỡng", "Trọng điểm quốc gia", 2010),
        ("Phố cổ Hội An", "Quảng Nam", "Duyên hải Nam Trung Bộ", "Đô thị di sản", "Trọng điểm quốc gia", 2010),
        ("Vân Phong", "Khánh Hòa", "Duyên hải Nam Trung Bộ", "Vịnh biển sinh thái", "Trọng điểm quốc gia", 2010),
        ("Đankia - Suối Vàng", "Lâm Đồng", "Tây Nguyên", "Nghỉ dưỡng hồ", "Trọng điểm quốc gia", 2010),
        ("Cần Giờ", "Thành phố Hồ Chí Minh", "Đông Nam Bộ", "Sinh thái ngập mặn", "Trọng điểm quốc gia", 2010),
        ("Côn Đảo", "Bà Rịa - Vũng Tàu", "Đông Nam Bộ", "Biển đảo lịch sử", "Trọng điểm quốc gia", 2010),
        ("Long Hải", "Bà Rịa - Vũng Tàu", "Đông Nam Bộ", "Nghỉ dưỡng biển", "Trọng điểm quốc gia", 2010),
        ("Phú Quốc", "Kiên Giang", "Tây Nam Bộ", "Biển đảo sinh thái", "Trọng điểm quốc gia", 2010),
        ("Mũi Cà Mau", "Cà Mau", "Tây Nam Bộ", "Sinh thái cực Nam", "Trọng điểm quốc gia", 2010),

        # 3. Quy hoạch khu du lịch quốc gia
        ("Cao nguyên đá Đồng Văn", "Hà Giang", "Trung du và miền núi phía Bắc", "Công viên địa chất", "Quy hoạch quốc gia", 2013),
        ("Thác Bản Giốc", "Cao Bằng", "Trung du và miền núi phía Bắc", "Thác nước danh thắng", "Quy hoạch quốc gia", 2013),
        ("Tân Trào", "Tuyên Quang", "Trung du và miền núi phía Bắc", "Lịch sử cách mạng", "Quy hoạch quốc gia", 2013),
        ("Mẫu Sơn", "Lạng Sơn", "Trung du và miền núi phía Bắc", "Nghỉ dưỡng núi", "Quy hoạch quốc gia", 2013),
        ("Hồ Núi Cốc", "Thái Nguyên", "Trung du và miền núi phía Bắc", "Hồ nhân tạo", "Quy hoạch quốc gia", 2013),
        ("Điện Biên Phủ - Pá Khoang", "Điện Biên", "Trung du và miền núi phía Bắc", "Lịch sử sinh thái", "Quy hoạch quốc gia", 2013),
        ("Hồ Hòa Bình", "Hòa Bình", "Trung du và miền núi phía Bắc", "Hồ thủy điện sinh thái", "Quy hoạch quốc gia", 2013),
        ("Côn Sơn - Kiếp Bạc", "Hải Dương", "Đồng bằng sông Hồng", "Văn hóa tâm linh", "Quy hoạch quốc gia", 2013),
        ("Tràng An", "Ninh Bình", "Đồng bằng sông Hồng", "Di sản danh thắng", "Quy hoạch quốc gia", 2013),
        ("Tam Chúc", "Hà Nam", "Đồng bằng sông Hồng", "Văn hóa tâm linh", "Quy hoạch quốc gia", 2018),
        ("Thiên Cầm", "Hà Tĩnh", "Bắc Trung Bộ", "Nghỉ dưỡng biển", "Quy hoạch quốc gia", 2013),
        ("Cửa Việt - Cồn Cỏ", "Quảng Trị", "Bắc Trung Bộ", "Biển đảo chiến trường xưa", "Quy hoạch quốc gia", 2013),
        ("Sơn Trà", "Đà Nẵng", "Duyên hải Nam Trung Bộ", "Bán đảo sinh thái", "Quy hoạch quốc gia", 2013),
        ("Bà Nà", "Đà Nẵng", "Duyên hải Nam Trung Bộ", "Nghỉ dưỡng núi", "Quy hoạch quốc gia", 2013),
        ("Cù Lao Chàm", "Quảng Nam", "Duyên hải Nam Trung Bộ", "Khu dự trữ sinh quyển", "Quy hoạch quốc gia", 2013),
        ("Lý Sơn", "Quảng Ngãi", "Duyên hải Nam Trung Bộ", "Đảo núi lửa", "Quy hoạch quốc gia", 2013),
        ("Phương Mai", "Bình Định", "Duyên hải Nam Trung Bộ", "Bán đảo sinh thái", "Quy hoạch quốc gia", 2013),
        ("Vịnh Xuân Đài", "Phú Yên", "Duyên hải Nam Trung Bộ", "Vịnh biển", "Quy hoạch quốc gia", 2013),
        ("Bắc Cam Ranh", "Khánh Hòa", "Duyên hải Nam Trung Bộ", "Nghỉ dưỡng biển", "Quy hoạch quốc gia", 2013),
        ("Ninh Chữ", "Ninh Thuận", "Duyên hải Nam Trung Bộ", "Nghỉ dưỡng biển", "Quy hoạch quốc gia", 2013),
        ("Măng Đen", "Kon Tum", "Tây Nguyên", "Sinh thái nghỉ dưỡng", "Quy hoạch quốc gia", 2013),
        ("Biển Hồ - Chư Đăng Ya", "Gia Lai", "Tây Nguyên", "Hồ núi lửa", "Quy hoạch quốc gia", 2013),
        ("Yok Đôn", "Đắk Lắk", "Tây Nguyên", "Vườn quốc gia sinh thái", "Quy hoạch quốc gia", 2013),
        ("Hồ Tà Đùng", "Đắk Nông", "Tây Nguyên", "Hồ vịnh trên cao", "Quy hoạch quốc gia", 2018),
        ("Núi Bà Đen", "Tây Ninh", "Đông Nam Bộ", "Văn hóa tâm linh núi", "Quy hoạch quốc gia", 2018),
        ("Thới Sơn", "Tiền Giang", "Tây Nam Bộ", "Cù lao sông nước", "Quy hoạch quốc gia", 2013),
        ("Tràm Chim", "Đồng Tháp", "Tây Nam Bộ", "Sinh thái đất ngập nước", "Quy hoạch quốc gia", 2013),
        ("Hà Tiên", "Kiên Giang", "Tây Nam Bộ", "Biển danh thắng", "Quy hoạch quốc gia", 2013),
        ("Ninh Kiều", "Cần Thơ", "Tây Nam Bộ", "Sông nước đô thị", "Quy hoạch quốc gia", 2013)
    ]
    rows = []
    for idx, (ten, dd, vung, lh, tt, nam) in enumerate(raw_list, 1):
        rows.append({
            "STT": idx,
            "Tên khu du lịch": ten,
            "Địa phương": dd,
            "Vùng du lịch": vung,
            "Loại hình du lịch": lh,
            "Tình trạng": tt,
            "Năm công nhận": nam
        })
    return write_excel("du_lich_diem_den_quoc_gia.xlsx", {"Điểm du lịch quốc gia": (cols, rows)})


# 6. Trường đại học, học viện
def build_dai_hoc() -> dict:
    ts = grids("wiki_dai_hoc.json")
    cols = ["STT", "Tên trường", "Viết tắt", "Tên giao dịch tiếng Anh", "Địa điểm", "Cơ quan chủ quản", "Loại hình"]
    rows = []
    stt = 1
    seen = set()
    for heads, grid in ts:
        h2 = heads.get("h2", "")
        h3 = heads.get("h3", "")
        loai_hinh = "Tư thục" if ("tư thục" in h2.lower() or "tư thục" in h3.lower()) else "Công lập"
        chu_quan = h3 if h3 else h2
        for r in grid[1:]:
            if len(r) < 3:
                continue
            ten, vt, eng, dd = "", "", "", ""
            head_row = grid[0]
            r_dict = dict(zip(head_row, r))
            ten = r_dict.get("Tên trường") or r_dict.get("Đơn vị thành viên") or r_dict.get("Đơn vị thành viên, trực thuộc") or r_dict.get("Đơn vị trực thuộc") or ""
            if not ten or ten in seen:
                continue
            seen.add(ten)
            vt = r_dict.get("Viết tắt", "")
            eng = r_dict.get("Tên giao dịch tiếng Anh", "")
            dd = r_dict.get("Địa điểm") or r_dict.get("Trụ sở chính") or r_dict.get("Trụ sở") or "Toàn quốc"
            rows.append({
                "STT": stt, "Tên trường": ten, "Viết tắt": vt if vt else "?",
                "Tên giao dịch tiếng Anh": eng, "Địa điểm": dd, "Cơ quan chủ quản": chu_quan,
                "Loại hình": loai_hinh
            })
            stt += 1
    return write_excel("giao_duc_truong_dai_hoc.xlsx", {"Trường đại học": (cols, rows)})


# 7. Bệnh viện TP.HCM
def build_benh_vien() -> dict:
    ts = grids("wiki_benh_vien.json")
    cols = ["STT", "Tên bệnh viện", "Tên khác", "Năm thành lập", "Loại bệnh viện", "Cơ sở", "Số giường", "Tuyến quản lý"]
    rows = []
    stt = 1
    for idx, (heads, grid) in enumerate(ts):
        tuyen = "Tuyến trung ương / Bộ ngành" if idx == 0 else ("Bệnh viện đại học" if idx == 1 else "Tuyến Thành phố / Sở Y tế")
        head_row = grid[0]
        for r in grid[1:]:
            r_dict = dict(zip(head_row, r))
            ten = r_dict.get("Tên bệnh viện", "")
            if not ten:
                continue
            tk = r_dict.get("Tên khác", "")
            nam = r_dict.get("Năm thành lập", "")
            loai = r_dict.get("Loại bệnh viện", "")
            cs = r_dict.get("Cơ sở", "")
            sg = r_dict.get("Số giường", "")
            if sg and sg.isdigit():
                sg_val = int(sg)
            elif sg and "." in sg:
                sg_val = num_vi(sg)
            elif not sg:
                sg_val = "?"
            else:
                sg_val = sg
            rows.append({
                "STT": stt, "Tên bệnh viện": ten, "Tên khác": tk,
                "Năm thành lập": num_vi(nam) if nam else "?",
                "Loại bệnh viện": loai, "Cơ sở": cs, "Số giường": sg_val,
                "Tuyến quản lý": tuyen
            })
            stt += 1
    return write_excel("y_te_benh_vien_tphcm.xlsx", {"Bệnh viện": (cols, rows)})


# 8. Di tích quốc gia đặc biệt
def build_di_tich_dac_biet() -> dict:
    ts = grids("wiki_di_tich_dac_biet.json")
    cols = ["STT", "Tên di tích", "Đợt xếp hạng", "Năm xếp hạng", "Địa điểm", "Hạng mục di tích", "Ghi chú"]
    rows = []
    stt = 1
    for heads, grid in ts:
        h3 = heads.get("h3", "")
        if "Đợt" not in h3:
            continue
        m = re.search(r"Đợt\s*(\d+)\s*\((\d{4})\)", h3)
        dot = f"Đợt {m.group(1)}" if m else h3
        nam_xh = int(m.group(2)) if m else "?"
        for r in grid[1:]:
            if len(r) < 4 or not r[0]:
                continue
            ten, dd, hm = r[0], r[2], r[3]
            gc = r[4] if len(r) > 4 else ""
            rows.append({
                "STT": stt, "Tên di tích": ten, "Đợt xếp hạng": dot,
                "Năm xếp hạng": nam_xh, "Địa điểm": dd, "Hạng mục di tích": hm,
                "Ghi chú": gc
            })
            stt += 1
    return write_excel("di_tich_quoc_gia_dac_biet.xlsx", {"Di tích đặc biệt": (cols, rows)})


def main() -> None:
    print("1. Tải và kiểm tra các trang nguồn...")
    fetch()
    print("2. Trích xuất và dựng các bảng dữ liệu *.xlsx...")
    manifest = {
        "dataset": "real_v4_s4",
        "license": "CC BY-SA 4.0 (Wikipedia tiếng Việt)",
        "created_at": time.strftime("%Y-%m-%d"),
        "files": {},
        "pages": {str(k): v[0] for k, v in PAGES.items()}
    }

    builders = [
        ("van_hoa_dan_toc.xlsx", build_dan_toc),
        ("the_thao_san_van_dong.xlsx", build_san_van_dong),
        ("van_hoa_phi_vat_the.xlsx", build_phi_vat_the),
        ("lich_su_bao_vat_quoc_gia.xlsx", build_bao_vat),
        ("du_lich_diem_den_quoc_gia.xlsx", build_diem_du_lich_quoc_gia),
        ("giao_duc_truong_dai_hoc.xlsx", build_dai_hoc),
        ("y_te_benh_vien_tphcm.xlsx", build_benh_vien),
        ("di_tich_quoc_gia_dac_biet.xlsx", build_di_tich_dac_biet),
    ]

    for fname, fn in builders:
        sheets_info = fn()
        manifest["files"][fname] = sheets_info
        print(f"  + {fname}: {sheets_info}")

    # Xóa file cũ du_lich_di_san_the_gioi.xlsx nếu còn
    old_file = OUT / "du_lich_di_san_the_gioi.xlsx"
    if old_file.exists():
        old_file.unlink()

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("3. Đã ghi xong manifest.json và toàn bộ data/*.xlsx!")


if __name__ == "__main__":
    main()

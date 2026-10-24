"""Bộ câu mù THỨ BA cho System 4 (24/10/2026): dữ liệu THẬT mà engine "biên dịch lúc nạp" CHƯA từng gặp, 4 lĩnh vực.

    python system4/eval/real_v3/build_v3.py          # tải 4 trang Wikipedia (raw/, không vào git) rồi dựng data/*.xlsx + manifest.json

  Hành chính  hanh_chinh_tinh_thanh.xlsx      34 tỉnh/thành sau sáp nhập 2025   "Đơn vị hành chính cấp tỉnh (Việt Nam)"
  Giao thông  giao_thong_san_bay.xlsx          22 sân bay dân dụng (2 sheet)     "Danh sách sân bay tại Việt Nam"
  Môi trường  moi_truong_vuon_quoc_gia.xlsx    37 vườn quốc gia                  "Danh sách vườn quốc gia tại Việt Nam"
  Năng lượng  nang_luong_thuy_dien.xlsx        372 nhà máy thủy điện             "Danh sách thủy điện tại Việt Nam"

Biến đổi giống system4/eval/real_domains/build.py: trải rowspan / colspan, bỏ chú thích [1], bỏ cột toạ độ, gắn nhóm theo tiêu đề mục.
Số đứng riêng trong ô được đổi thành ô số theo ĐÚNG cách viết của từng cột trong nguồn (vd. dân số "573.119" = 573119; diện tích
"6.700,39" = 6700,39; công suất thủy điện "4.4" = 4,4 MW; sản lượng "166,2" = 166,2). Ô không phải số đứng riêng ("Côn Đảo (1945)",
"Bê tông 3.051 m", "11/1979", "?") giữ nguyên chữ như nguồn. KHÔNG thêm, KHÔNG sửa số liệu.
Revid cố định trong PAGES: chạy lại trên máy khác ra cùng dữ liệu (API trả đúng phiên bản đó).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from lxml import html

HERE = Path(__file__).resolve().parent
RAW, OUT = HERE / "raw", HERE / "data"
sys.path.insert(0, str(HERE.parent / "real_domains"))
from build import tables, as_dicts  # noqa: E402  (cùng cách trải bảng / làm sạch với bộ thật trước)
from fetch import get, WIKI  # noqa: E402

PAGES = {   # revid -> tiêu đề (phiên bản lấy ngày 24/10/2026)
    75581808: "Đơn vị hành chính cấp tỉnh (Việt Nam)",
    75639956: "Danh sách sân bay tại Việt Nam",
    75659364: "Danh sách vườn quốc gia tại Việt Nam",
    75522391: "Danh sách thủy điện tại Việt Nam",
}


def fetch() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for rev, title in PAGES.items():
        if (RAW / f"{rev}.json").exists():
            continue
        p = json.loads(get(WIKI, {"action": "parse", "oldid": rev, "prop": "text|revid", "format": "json", "formatversion": 2}))["parse"]
        assert p["revid"] == rev, (title, p["revid"])
        (RAW / f"{rev}.json").write_text(json.dumps({"title": p["title"], "revid": rev, "html": p["text"],
                                                       "retrieved": time.strftime("%Y-%m-%d")}, ensure_ascii=False), encoding="utf-8")
        print("  tải", title)
        time.sleep(2)


def grids(rev: int):
    return tables(html.fromstring(json.loads((RAW / f"{rev}.json").read_text(encoding="utf-8"))["html"]))


def num_vi(s: str):
    """Số kiểu Việt Nam: chấm = hàng nghìn, phẩy = thập phân ("6.700,39", "573.119", "12.700"). Không phải số đứng riêng -> giữ chữ."""
    t = s.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})*(,\d+)?|\d+(,\d+)?", t):
        v = float(t.replace(".", "").replace(",", "."))
        return int(v) if v.is_integer() else v
    return t


def num_dot(s: str):
    """Số có dấu chấm thập phân (cột công suất thủy điện: "4.4", "19.5", "1920")."""
    t = s.strip()
    if re.fullmatch(r"\d+(\.\d+)?", t):
        v = float(t)
        return int(v) if v.is_integer() else v
    return t


def write(name: str, sheets: dict[str, tuple[list[str], list[dict]]]) -> dict:
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for title, (cols, rows) in sheets.items():
        ws = wb.create_sheet(title)
        ws.append(cols)
        for r in rows:
            ws.append([r.get(c, "") for c in cols])
    OUT.mkdir(parents=True, exist_ok=True)
    wb.save(str(OUT / name))
    return {t: len(r) for t, (_, r) in sheets.items()}


def tinh_thanh() -> dict:
    (_, g), = grids(75581808)
    cols = ["Tỉnh thành", "Trung tâm hành chính", "Vùng", "Thành lập", "Diện tích (km²)", "Dân số (người)", "Mật độ (người/km²)",
            "Số phường", "Số xã", "Số đặc khu"]
    rows = []
    for r in g[2:]:                   # 2 dòng tiêu đề: "Đơn vị hành chính cấp xã" chia P / X / ĐK
        if not r or not r[1]:
            continue
        rows.append(dict(zip(cols, [r[1], r[2], r[3], num_vi(r[4]), num_vi(r[5]), num_vi(r[6]), num_vi(r[7]), num_vi(r[8]), num_vi(r[9]), num_vi(r[10])])))
    return write("hanh_chinh_tinh_thanh.xlsx", {"Tỉnh thành": (cols, rows)})


def san_bay() -> dict:
    ts = grids(75639956)
    dd = [r for r in as_dicts(ts[0][1])]
    cols1 = ["STT", "Sân bay (Năm xây dựng)", "Mã ICAO/IATA", "Tỉnh/ thành", "Số đường băng", "Hướng đường băng", "Loại đường băng Chiều dài",
             "Cấp sân bay", "Chú thích"]
    rows1 = [{c: (num_vi(r[c]) if c in ("STT", "Số đường băng") else r[c]) for c in cols1} for r in dd if r.get("Sân bay (Năm xây dựng)")]
    nl = [r for r in as_dicts(ts[1][1])]
    cols2 = ["STT", "Tên sân bay", "Vị trí", "Năng lực khai thác", "Sản lượng thông qua (2023)", "Hãng khai thác"]
    rows2 = [{c: (num_vi(r[c]) if c in ("STT", "Năng lực khai thác", "Sản lượng thông qua (2023)") else r[c]) for c in cols2} for r in nl if r.get("Tên sân bay")]
    return write("giao_thong_san_bay.xlsx", {"Sân bay dân dụng": (cols1, rows1), "Năng lực khai thác": (cols2, rows2)})


def vuon_quoc_gia() -> dict:
    (_, g), = grids(75659364)
    cols = ["Vùng", "Tên vườn quốc gia", "Năm thành lập", "Diện tích (ha)", "Địa điểm"]
    rows = [dict(zip(cols, [r[0], r[1], num_vi(r[2]), num_vi(r[3]), r[4]])) for r in g[1:] if len(r) >= 5 and r[1]]
    return write("moi_truong_vuon_quoc_gia.xlsx", {"Vườn quốc gia": (cols, rows)})


def thuy_dien() -> dict:
    cols = ["Tên thủy điện", "Quy mô", "Công suất (MW)", "Sản lượng (triệu kWh/năm)", "Năm khởi công", "Năm hoạt động", "Trên sông", "Vị trí hành chính"]
    rows = []
    for heads, g in grids(75522391):
        size = "Lớn" if "lớn" in heads["h2"].lower() else "Vừa và nhỏ"
        for r in g[2:]:               # dòng 2 trống (dòng phụ của tiêu đề)
            if len(r) < 8 or not r[0]:
                continue
            rows.append(dict(zip(cols, [r[0], size, num_dot(r[1]), num_vi(r[2]), r[3], r[4], r[6], r[7]])))
    return write("nang_luong_thuy_dien.xlsx", {"Thủy điện": (cols, rows)})


def main() -> None:
    fetch()
    man = {"pages": {str(k): v for k, v in PAGES.items()}, "license": "CC BY-SA 4.0 (Wikipedia tiếng Việt)", "files": {}}
    for fn, name in ((tinh_thanh, "hanh_chinh_tinh_thanh.xlsx"), (san_bay, "giao_thong_san_bay.xlsx"),
                     (vuon_quoc_gia, "moi_truong_vuon_quoc_gia.xlsx"), (thuy_dien, "nang_luong_thuy_dien.xlsx")):
        man["files"][name] = fn()
        print(name, man["files"][name])
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

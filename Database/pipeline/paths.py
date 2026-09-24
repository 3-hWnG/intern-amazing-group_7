"""Đường dẫn dùng chung + hằng số bộ ngành.

Tách riêng để mọi bước dùng chung một chỗ, không ai tự chế đường dẫn.
"""

from __future__ import annotations

import re
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = DATABASE_DIR / "raw"
RAW_DETAILS_DIR = RAW_DIR / "details"
RAW_FILES_DIR = RAW_DIR / "files"
CATALOG_PATH = RAW_DIR / "catalog.jsonl"
CHECKPOINT_PATH = RAW_DIR / "_checkpoint.json"

STAGING_DIR = DATABASE_DIR / "staging"
STAGING_PATH = STAGING_DIR / "procedures.jsonl"

RUNTIME_DIR = DATABASE_DIR / "runtime"
PROCEDURES_DB = RUNTIME_DIR / "procedures.db"

SCHEMA_PATH = Path(__file__).resolve().parent / "schema_procedures.sql"

REPORT_PATH = DATABASE_DIR / "COVERAGE_REPORT.md"

# --------------------------------------------------------------------------
# Mã bộ/ngành ban hành thủ tục — dùng cho bộ lọc `departmentCode` ở bước ①.
# Đã kiểm chứng thật trên API ngày 2026-09-21: departmentCode="G01" → 329 thủ tục,
# 100% do Bộ Công an ban hành (không lọc thì ra 6.308 thủ tục của mọi bộ/tỉnh).
# --------------------------------------------------------------------------
DEPT_BO_CONG_AN = "G01"        # Bộ Công an — căn cước, cư trú, XNC, con dấu, PCCC…
DEPT_BO_TU_PHAP = "G15"        # Bộ Tư pháp — hộ tịch, chứng thực, kết hôn, khai sinh…

DEPT_UBND_HCM = "H29"          # UBND TP.HCM — thủ tục riêng của Thành phố

# --------------------------------------------------------------------------
# PHẠM VI CÀO. Nhóm chốt: chỉ thủ tục cấp XÃ/PHƯỜNG (TP.HCM gọi Phường là cấp xã).
#   level=COMMUNE        -> 1.313 thủ tục toàn quốc (đã kiểm chứng = cờ isWard)
#   departmentCode=H29   -> 37 thủ tục riêng của UBND TP.HCM chưa nằm trong nhóm trên
# Hợp lại (khử trùng theo `id`) = 1.350. Mỗi phần tử: (departmentCode, level).
# --------------------------------------------------------------------------
SCOPE_XA = (("", "COMMUNE"), (DEPT_UBND_HCM, ""))

DEPARTMENT_CODES = {
    "bca": DEPT_BO_CONG_AN,
    "btp": DEPT_BO_TU_PHAP,
}


def resolve_department(value: str | None) -> str:
    """Nhận 'bca' / 'btp' / mã thô 'G01' / 'all' → trả mã cho API ('' = không lọc)."""
    if not value or value.lower() == "all":
        return ""
    return DEPARTMENT_CODES.get(value.lower(), value)


def ensure_dirs() -> None:
    for d in (RAW_DIR, RAW_DETAILS_DIR, RAW_FILES_DIR, STAGING_DIR, RUNTIME_DIR):
        d.mkdir(parents=True, exist_ok=True)


MAX_NAME = 120


def safe_name(text: str) -> str:
    """Tên an toàn trên Windows, cắt ngắn thô. Dùng cho thư mục / mã thủ tục."""
    bad = '<>:"/\\|?*'
    out = "".join("_" if c in bad else c for c in str(text)).strip(". ")
    return out[:MAX_NAME] or "unnamed"


def stored_filename(file_name: str) -> str:
    """Tên tệp đính kèm khi lưu xuống đĩa — GIỮ NGUYÊN PHẦN ĐUÔI.

    ⚠️ Đây là hàm DÙNG CHUNG cho cả bên tải (fetch_details) lẫn bên sinh đường dẫn
    (normalize). Trước đây mỗi bên cắt tên một kiểu nên 9/261 tệp tải về đúng mà
    DB lại trỏ sai chỗ — UI sẽ hiện nút tải rồi 404.

    Tên biểu mẫu của cổng có khi dài 149 ký tự; cắt thô ở 120 sẽ NUỐT MẤT '.docx'.
    """
    # Gom khoảng trắng NGAY TẠI ĐÂY. normalize.py gọi clean() trước (clean gom
    # khoảng trắng), fetch_details.py thì truyền tên thô. Nếu hàm này không tự
    # gom thì hai bên ra hai tên khác nhau — đúng lỗi đã làm 16 tệp trỏ sai chỗ
    # ("mẫu 04␣␣chấm dứt" vs "mẫu 04␣chấm dứt").
    name = re.sub(r"\s+", " ", str(file_name or "")).strip()
    if not name:
        return ""
    stem, dot, ext = name.rpartition(".")
    if not dot or len(ext) > 10 or "/" in ext or "\\" in ext:
        stem, ext = name, ""          # không có đuôi hợp lệ
    bad = '<>:"/\\|?*'
    stem = "".join("_" if c in bad else c for c in stem).strip(". ")
    ext = "".join("_" if c in bad else c for c in ext).strip()
    suffix = f".{ext}" if ext else ""
    stem = stem[:MAX_NAME - len(suffix)]
    return (stem + suffix) or "unnamed"

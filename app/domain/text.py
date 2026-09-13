"""Tiện ích xử lý chuỗi tiếng Việt dùng chung.

`fold` là hàm quan trọng nhất: bỏ dấu + thường hoá. BM25 đánh chỉ mục trên
dạng đã fold nên câu hỏi gõ không dấu vẫn khớp - đây là cách sửa lỗi
no_diacritics (R@1 = 0.056 ở baseline v0) mà không cần đổi mô hình.
"""

from __future__ import annotations

import re
import unicodedata

_D_MAP = str.maketrans({"đ": "d", "Đ": "D"})


def fold(text: str) -> str:
    """Bỏ dấu, thường hoá, gom khoảng trắng."""
    if not text:
        return ""
    text = str(text).translate(_D_MAP)
    nfd = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", stripped.lower()).strip()


def tokenize(text: str) -> list[str]:
    """Tách token cho BM25. Làm trên chuỗi đã fold."""
    return re.findall(r"[a-z0-9]+", fold(text))


def clean(text) -> str:
    """Chuẩn hoá ô dữ liệu thô từ Excel."""
    if text is None:
        return ""
    s = str(text).strip()
    if s.lower() in {"nan", "none", "null", "-"}:
        return ""
    return re.sub(r"\s+", " ", s)


def truncate(text: str, max_chars: int) -> str:
    """Cắt theo ranh giới từ, tránh cắt giữa chừng."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > max_chars * 0.6 else cut).rstrip(" ,;.") + "..."


MONEY_RE = re.compile(r"\d[\d.,]*\s*(?:đ|đồng|vnd|vnđ|nghìn|triệu)", re.IGNORECASE)
DAYS_RE = re.compile(r"\d+\s*(?:ngày|tháng|giờ|tuần|năm)", re.IGNORECASE)


def extract_money(text: str) -> list[str]:
    return [m.group(0).lower().replace(" ", "") for m in MONEY_RE.finditer(text or "")]


def extract_durations(text: str) -> list[str]:
    return [m.group(0).lower().replace(" ", "") for m in DAYS_RE.finditer(text or "")]


def has_diacritics(text: str) -> bool:
    """Câu hỏi có dấu tiếng Việt không? Dùng để chọn trọng số khi hoà xếp hạng."""
    if not text:
        return False
    if any(c in text for c in "đĐ"):
        return True
    return any(unicodedata.category(c) == "Mn"
               for c in unicodedata.normalize("NFD", str(text)))


def title_similarity(a: str, b: str) -> float:
    """Jaccard trên token đã fold - đủ để nhận ra hai dòng là cùng một thủ tục."""
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

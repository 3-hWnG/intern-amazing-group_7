"""Tiện ích xử lý chuỗi tiếng Việt dùng chung.

`fold` là hàm quan trọng nhất: bỏ dấu + thường hoá, để người dân gõ không dấu
vẫn so khớp được. `BM25` dùng để chọn ĐOẠN liên quan trong trang web / tệp
đính kèm — không dùng để định tuyến câu hỏi (việc đó do LLM hiểu ý định).
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

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
    """Tách âm tiết trên chuỗi đã fold."""
    return re.findall(r"[a-z0-9]+", fold(text))


def terms(text: str) -> list[str]:
    """Âm tiết đơn + cặp âm tiết liền nhau ("tam_tru", "ho_so").

    Từ tiếng Việt đa số là 2 âm tiết; chỉ đếm âm tiết đơn thì "hồ sơ" khớp cả
    "hồ nước" lẫn "sơ yếu".
    """
    toks = tokenize(text)
    return toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]


def clean(text) -> str:
    """Chuẩn hoá ô dữ liệu thô từ bảng biểu."""
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


_LIST_RE = re.compile(r"^(\d+)([.)])\s+")


def _clean_non_citation_brackets(text: str) -> str:
    """Giữ nguyên trích dẫn [S#]. Bóc bỏ dấu ngoặc vuông ở các nội dung khác để không xoá mất chữ của câu trả lời."""
    def repl(m: re.Match) -> str:
        inner = m.group(1).strip()
        if not inner:
            return ""
        if re.fullmatch(r"S\d+(\s*[,;]\s*S\d+)*", inner, re.IGNORECASE):
            return m.group(0)
        # Chỉ loại bỏ các nhãn khung rác ngắn
        if fold(inner) in ["chua neu ro", "tai lieu chua neu ro", "nghien cuu tai lieu"]:
            return ""
        return inner
    res = re.sub(r"\[([^\]\[]*)\]", repl, text or "")
    return re.sub(r"\[([^\]\[]*)\]", repl, res)



def _clean_snippet_noise(line: str) -> str:
    """Lọc bỏ các nhãn khung rác và câu hỏi chép từ tiêu đề tài liệu."""
    line = re.sub(r"^(Tài liệu trích dẫn|Trích dẫn tài liệu|Trích dẫn|Tài liệu tham khảo)\s*[:：\-]*\s*", "", line, flags=re.IGNORECASE).strip()
    if re.fullmatch(r"\[?S\d+\]?", line, re.IGNORECASE):
        return ""
    if line.endswith("?") and any(line.lower().endswith(q) for q in ["gồm những gì?", "như thế nào?", "ra sao?", "ở đâu?"]):
        return ""
    # Bỏ dòng nhại lại lời nhắc prompt
    if re.search(r"^(lưu ý:\s*)?nếu tài liệu ghi rõ", line, re.IGNORECASE):
        return ""
    if re.search(r"^nêu số tiền cụ thể", line, re.IGNORECASE):
        return ""
    return line


def tidy_answer(text: str) -> str:
    """Dọn lỗi hay gặp ở mô hình nhỏ: lặp nguyên dòng; số thứ tự lệch sau khi lược bỏ dòng; ngoặc vuông lạ."""
    # 1. Bỏ chữ Hán / CJK bị mô hình nhỏ sinh nhầm
    text = re.sub(r"[\u4e00-\u9fff]+", "", text or "")
    # 2. Xóa placeholder mẫu S# chưa thay thế
    text = re.sub(r"\[?\bS#\b\]?", "", text)
    text = _clean_non_citation_brackets(text)
    kept, seen = [], set()
    for line in (text or "").splitlines():
        line = _clean_snippet_noise(line)
        if not line:
            continue
        # mảnh vụn còn lại sau khi lược bỏ phần trong ngoặc: ". Bạn nên...", ": - ..."
        line = re.sub(r"^\s*[.,;:]+\s*", "", line)
        if line.strip() and not re.search(r"\w", line):
            continue
        key = re.sub(r"^\s*(?:\d+[.)]|[-*•])\s*", "", line).strip().lower()
        if len(key) > 12 and key in seen:
            continue
        if key:
            seen.add(key)
        kept.append(line.rstrip())

    out, n = [], 0
    for line in kept:
        m = _LIST_RE.match(line)
        if m:
            n += 1
            line = f"{n}{m.group(2)} {line[m.end():]}"
        elif line.strip() and not line[:1].isspace() and not line.lstrip().startswith(("-", "*", "•")):
            n = 0                       # đoạn văn mới -> danh sách sau đánh số lại từ 1
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


class BM25:
    """BM25 Okapi tối giản trên `terms()` — không cần thư viện ngoài."""

    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self._tf = [Counter(terms(d)) for d in docs]
        self._len = [sum(tf.values()) for tf in self._tf]
        self._avg = (sum(self._len) / len(self._len)) if self._len else 0.0
        df: Counter = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        n = len(docs)
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        q = set(terms(query))
        out = []
        for tf, dl in zip(self._tf, self._len):
            norm = self.k1 * (1 - self.b + self.b * dl / (self._avg or 1))
            s = 0.0
            for t in q:
                f = tf.get(t)
                if f:
                    s += self._idf[t] * f * (self.k1 + 1) / (f + norm)
            out.append(s)
        return out


# ---- số liệu hay bị mô hình nhỏ bịa: tiền, thời hạn, số hiệu văn bản -------
MONEY_RE = re.compile(r"\d[\d.,]*\s*(?:đồng|đ\b|vnđ|vnd|nghìn|triệu)", re.IGNORECASE)
DAYS_RE = re.compile(r"\d+\s*(?:ngày|tháng|giờ|tuần|năm)(?!\s*\d)", re.IGNORECASE)
DOC_NO_RE = re.compile(r"\b\d{1,4}/\d{4}/[A-Za-zĐđ0-9\-]+")

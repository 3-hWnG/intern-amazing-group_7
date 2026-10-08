"""NV5 (2A): kiểm chi tiết bịa trong câu trả lời — bằng code, không nhờ AI.

Chuyên gia: mọi số (số tiền, ngày, giờ, %…), số điện thoại, email, đường dẫn, tên riêng (>= 2 chữ viết hoa liền nhau) trong câu
trả lời phải xuất hiện trong dữ liệu tìm được / câu hỏi / lịch sử người dùng. AI chung (không bật dữ liệu): chỉ kiểm số điện thoại,
email và đường dẫn có tên doanh nghiệp — thứ AI không thể biết (vd. "hotline 1900 88…" của Team 7) — so với mô tả doanh nghiệp.
Bắt được -> chat.py cho AI viết lại một lần, kèm danh sách chi tiết không có.
"""
from __future__ import annotations
import re
import unicodedata

_PHONE = re.compile(r"(?<![\w.])(?:\+84|0|1[89]00)[\d .\-]{4,14}\d(?!\w)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL = re.compile(r"(?:https?://|www\.)[^\s)\]]+|\b[\w-]+\.(?:com|vn|net|org|info|io)(?:\.vn)?\b", re.I)
_NUM = re.compile(r"\d+(?:[.,:/]\d+)*")
_UNIT = re.compile(r"^\s*(?:%|ngày|tháng|năm|giờ|phút|tuần|đ\b|đồng|vnđ|vnd|nghìn|ngàn|triệu|tỷ|km|kg|m2|người|lần|bản|tuổi|usd|\$)", re.I)
_CITE = re.compile(r"\[\d{1,2}\]")
_LISTNUM = re.compile(r"^\s*\d+[.)]\s", re.M)
_WORD = re.compile(r"[^\W\d_]+", re.U)


def fold(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    return unicodedata.normalize("NFC", "".join(c for c in t if unicodedata.category(c) != "Mn")).replace("đ", "d")


def _digits(t: str) -> str:
    return re.sub(r"\D", "", t)


def _clean(answer: str) -> str:
    t = _CITE.sub(" ", answer or "")
    t = _LISTNUM.sub(" ", t)
    return re.sub(r"[*_`#>|]", " ", t)


def _names(text: str) -> list[str]:
    """Cụm >= 2 chữ viết hoa liền nhau (tên người / nơi chốn / tổ chức). Chữ đầu câu viết hoa nên thử cả cụm bỏ chữ đầu."""
    out = []
    for line in text.splitlines():   # cụm tên không vắt qua dòng
        run = []
        for m in re.finditer(r"\S+", line):
            raw = m.group()
            w = raw.strip(".,;:!?\"'()[]")
            ok = (bool(w) and _WORD.fullmatch(w) is not None and w[0].isupper()
                  and not (len(w) > 1 and w.isupper()))   # CHỮ IN HOA TOÀN BỘ (tiêu đề, viết tắt) không phải tên
            if ok:
                run.append(w)
            if not ok or raw.rstrip("\"')]")[-1:] in ".,;:!?":   # hết cụm khi gặp chữ thường hoặc dấu câu
                if len(run) >= 2:
                    out.append(" ".join(run))
                run = []
        if len(run) >= 2:
            out.append(" ".join(run))
    return out


def ungrounded(answer: str, allowed_text: str, kb: bool, business: str = "") -> list[str]:
    """Các chi tiết trong câu trả lời không có trong allowed_text (dữ liệu + câu hỏi + lịch sử người dùng + mô tả doanh nghiệp)."""
    text = _clean(answer)
    allowed_f = fold(allowed_text)
    allowed_digits = {_digits(x) for x in _NUM.findall(allowed_text)} | {_digits(x) for x in _PHONE.findall(allowed_text)}
    allowed_flat = _digits(allowed_text)
    bad: list[str] = []
    spans = []
    for m in _PHONE.finditer(text):
        d = _digits(m.group())
        spans.append(m.span())
        if len(d) >= 8 and d not in allowed_digits and d not in allowed_flat:
            bad.append(m.group().strip())
    for m in _EMAIL.finditer(text):
        spans.append(m.span())
        if fold(m.group()) not in allowed_f:
            bad.append(m.group())
    biz = [w for w in re.findall(r"\w+", fold(business)) if len(w) >= 3] + ["".join(re.findall(r"\w+", fold(business)))]
    for m in _URL.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue   # phần tên miền của email đã kiểm ở trên
        spans.append(m.span())
        u = fold(m.group()).rstrip(".")
        if u in allowed_f:
            continue
        if kb or any(b and b in u.replace("-", "") for b in biz):
            bad.append(m.group().rstrip("."))
    if kb:
        for m in _NUM.finditer(text):
            if any(a <= m.start() < b for a, b in spans):
                continue
            n = m.group()
            parts = [p for p in re.split(r"[.,:/]", n) if p]
            if len(parts) == 1 and len(n) <= 2 and int(n) <= 10 and not _UNIT.match(text[m.end():]):
                continue   # "2 bạn", "3 bước": số đếm nhỏ do AI tự đếm
            d = _digits(n)
            if d in allowed_digits or n in allowed_text:
                continue
            if all(_digits(p) in allowed_digits or not p.strip('0') for p in parts) and len(parts) > 1:
                continue   # "29 tháng 7 năm 2020" / "29/7/2020" viết khác nhau nhưng cùng các số
            bad.append(n)
        has = lambda p: re.search(r"(?<!\w)" + re.escape(fold(p)) + r"(?!\w)", allowed_f) is not None
        for name in _names(text):
            words = name.split()
            if has(name) or (len(words) >= 3 and has(" ".join(words[1:]))):   # chữ đầu câu viết hoa: thử bỏ chữ đầu
                continue
            bad.append(name)
    seen, out = set(), []
    for x in bad:
        if x.lower() not in seen:
            seen.add(x.lower()); out.append(x)
    return out[:8]


def rewrite_instruction(items: list[str], kb: bool) -> str:
    where = "dữ liệu tham khảo" if kb else "thông tin bạn được cung cấp"
    return (f"Câu trả lời trước của bạn có các chi tiết KHÔNG có trong {where}: " + "; ".join(items)
            + ". Viết lại câu trả lời: bỏ các chi tiết đó, hoặc nói rõ là bạn không có thông tin đó. Không bịa chi tiết khác.")

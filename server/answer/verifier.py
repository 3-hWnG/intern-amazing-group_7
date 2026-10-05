"""Kiểm chứng câu trả lời: số tiền/ngày/số văn bản phải có trong nguồn; không "miễn phí" nếu nguồn không nói miễn."""
from __future__ import annotations

import re

from system3.data.textutil import fold

_NUM = re.compile(r"\d[\d.,/]*\d|\d")
_FREE = re.compile(r"\bmien (le )?phi\b|\bkhong (mat|thu) phi\b|\bkhong phai nop (le )?phi\b")


def _nums(text: str) -> set[str]:
    return {n.strip(".,/") for n in _NUM.findall(text or "")}


def verify(answer_text: str, evidence_text: str, question: str = "") -> list[str]:
    """-> danh sách vấn đề (rỗng = đạt)."""
    issues = []
    allowed = _nums(evidence_text) | _nums(question)
    for n in _nums(answer_text) - allowed:
        issues.append(f"số không có trong nguồn: {n}")
    if _FREE.search(fold(answer_text)) and not _FREE.search(fold(evidence_text)):
        issues.append("khẳng định miễn phí nhưng nguồn không nói miễn")
    return issues


_DOC = re.compile(r"\b(nghi dinh|thong tu|luat|quyet dinh|nghi quyet|phap lenh|bo luat)\s+([0-9a-z/\-]+)")
_CODE = re.compile(r"\d+/\d{4}/[^\s,;.()\"«»]+")


def _norm_nums(text: str) -> set[str]:
    return {n.lstrip("0") or "0" for n in _nums(text)}


def verify_point(text: str, cited_text: str, question: str = "") -> list[str]:
    """Kiểm một ý LLM: số, số hiệu/tên văn bản phải có trong ĐOẠN ĐƯỢC TRÍCH DẪN; không 'miễn phí' nếu đoạn đó không nói."""
    issues = [f"số không có trong đoạn trích dẫn: {n}" for n in _norm_nums(text) - _norm_nums(cited_text) - _norm_nums(question)]
    ft, fc = fold(text), fold(cited_text)
    for m in _DOC.finditer(ft):
        if m.group(0) not in fc:
            issues.append(f"tên văn bản không có trong đoạn trích dẫn: {m.group(0)}")
    for c in _CODE.findall(text):
        if fold(c) not in fc:
            issues.append(f"số hiệu không có trong đoạn trích dẫn: {c}")
    if _FREE.search(ft) and not _FREE.search(fc):
        issues.append("khẳng định miễn phí nhưng đoạn trích dẫn không nói miễn")
    return issues

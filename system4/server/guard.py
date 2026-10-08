"""Guardrail mở rộng được (NV2, 6A): luật nằm trong cài đặt GUARDRAILS, dev sửa trên panel.

- block    : tin nhắn người dùng chứa cụm từ -> trả lời cố định, KHÔNG gọi AI
- instruct : tin nhắn chứa cụm từ (hoặc match trống = luôn) -> thêm lời dặn cho AI
- replace  : câu trả lời của AI chứa cụm từ -> dừng và thay bằng message
Khớp không phân biệt hoa thường và dấu ("bo qua moi huong dan" khớp "bỏ qua mọi hướng dẫn").
"""
from __future__ import annotations

from . import settings
from .lang import normalize


def _rules(kind: str) -> list[dict]:
    return [r for r in settings.get("GUARDRAILS") if r.get("enabled") and r.get("kind") == kind]


def _fill(msg: str) -> str:
    return msg.replace("{business}", settings.get("BUSINESS_NAME"))


def _hits(rule: dict, text_norm: str) -> bool:
    phrases = [normalize(p) for p in rule.get("match", "").split("|") if p.strip()]
    if not phrases:
        return rule["kind"] == "instruct"   # match trống = luôn áp dụng (chỉ cho lời dặn)
    return any(p and p in text_norm for p in phrases)


def check_input(text: str) -> tuple[dict | None, list[str]]:
    """Trả (luật block khớp đầu tiên hoặc None, danh sách lời dặn áp dụng)."""
    n = normalize(text)
    block = next((r for r in _rules("block") if _hits(r, n)), None)
    if block:
        return {"name": block["name"], "message": _fill(block["message"])}, []
    return None, [_fill(r["message"]) for r in _rules("instruct") if _hits(r, n)]


def check_output(text: str) -> dict | None:
    n = normalize(text)
    r = next((r for r in _rules("replace") if _hits(r, n)), None)
    return {"name": r["name"], "message": _fill(r["message"])} if r else None

"""Guardrail mở rộng được (NV2, 6A): luật nằm trong cài đặt GUARDRAILS, dev sửa trên panel.

- block    : tin nhắn người dùng chứa cụm từ -> trả lời cố định, KHÔNG gọi AI
- instruct : tin nhắn chứa cụm từ (hoặc match trống = luôn) -> thêm lời dặn cho AI
- replace  : câu trả lời của AI chứa cụm từ -> dừng và thay bằng message
Khớp không phân biệt hoa thường và dấu ("bo qua moi huong dan" khớp "bỏ qua mọi hướng dẫn").
"""
from __future__ import annotations

from . import settings
from .config import SEED_GUARDRAILS

SEED_INJECTION_MESSAGE = SEED_GUARDRAILS[0]["message"]
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


INJECTION_RULE = "Chống chèn lệnh"


def _injection(text: str) -> bool:
    """G1.3 (P05): dùng chung bộ dò chèn lệnh của Strict (server/policy pre_check) — lộ system prompt, developer mode,
    jailbreak, quên vai trò, viết hoa không dấu... Tắt bằng cài đặt INJECTION_GUARD."""
    if not settings.get("INJECTION_GUARD"):
        return False
    from policy import pre_check
    return "injection" in pre_check(text)["flags"]


def check_input(text: str) -> tuple[dict | None, list[str]]:
    """Trả (luật block khớp đầu tiên hoặc None, danh sách lời dặn áp dụng)."""
    n = normalize(text)
    block = next((r for r in _rules("block") if _hits(r, n)), None)
    if not block and _injection(text):
        block = next((r for r in settings.get("GUARDRAILS") if r.get("name") == INJECTION_RULE and r.get("kind") == "block"),
                     None) or {"name": INJECTION_RULE, "message": SEED_INJECTION_MESSAGE}
    if block:
        return {"name": block["name"], "message": _fill(block["message"])}, []
    return None, [_fill(r["message"]) for r in _rules("instruct") if _hits(r, n)]


def check_output(text: str) -> dict | None:
    n = normalize(text)
    r = next((r for r in _rules("replace") if _hits(r, n)), None)
    return {"name": r["name"], "message": _fill(r["message"])} if r else None

"""Đo độ dài ngữ cảnh và tóm tắt khi vượt ngưỡng.

Mô hình 1.5B kém dần khi ngữ cảnh dài, nên ngưỡng đặt thấp hơn nhiều so với
giới hạn kỹ thuật của mô hình - đây là lựa chọn vì CHẤT LƯỢNG, không phải vì
bị giới hạn.
"""

from __future__ import annotations

from config import (CONTEXT_TOKEN_BUDGET, SUMMARY_ENABLED, SUMMARY_KEEP_RECENT,
                    TOKENS_PER_SYLLABLE)
from core import llm
from db.repositories import Conversations, Messages

SYSTEM_SUMMARY = (
    "Bạn là công cụ tóm tắt hội thoại hành chính công.\n"
    "Tóm tắt thật ngắn, giữ BẰNG ĐƯỢC:\n"
    "1. Thủ tục người dân đang hỏi.\n"
    "2. Thông tin cá nhân họ đã cung cấp (tỉnh/thành, hoàn cảnh, giấy tờ đang có).\n"
    "3. Câu hỏi còn đang treo chưa được trả lời.\n"
    "Bỏ hết lời chào và câu xã giao. Viết dạng gạch đầu dòng, tối đa 120 từ."
)


def estimate_tokens(text: str) -> int:
    """Ước lượng thô số token tiếng Việt. Đủ chính xác để quyết định có tóm tắt."""
    return int(len((text or "").split()) * TOKENS_PER_SYLLABLE)


def _render(messages: list[dict]) -> str:
    return "\n".join(
        f"{'Công dân' if m['role'] == 'user' else 'Trợ lý'}: {m['content']}"
        for m in messages
    )


def build_context(conversation_id: int) -> tuple[str, list[dict]]:
    """Trả về (tóm tắt, các lượt gần nhất) đã nằm trong ngân sách token.

    Tóm tắt lại nếu cần - và GHI vào DB để lần sau không phải tóm tắt lại.
    """
    conv = Conversations.by_id(conversation_id)
    if conv is None:
        return "", []

    summary = conv["summary"] or ""
    upto = conv["summary_upto"] or 0
    recent = Messages.list_for(conversation_id, after_id=upto)

    if not SUMMARY_ENABLED:
        return summary, recent[-SUMMARY_KEEP_RECENT * 2:]

    total = estimate_tokens(summary) + sum(estimate_tokens(m["content"]) for m in recent)
    if total <= CONTEXT_TOKEN_BUDGET:
        return summary, recent

    # Vượt ngưỡng: giữ nguyên văn N lượt cuối, tóm tắt phần còn lại.
    keep = SUMMARY_KEEP_RECENT * 2
    if len(recent) > keep:
        to_summarise, kept = recent[:-keep], recent[-keep:]
    else:
        to_summarise, kept = [], recent
    if not to_summarise:
        return summary, kept

    previous = f"Tóm tắt trước đó:\n{summary}\n\n" if summary else ""
    new_summary = llm.complete(
        SYSTEM_SUMMARY,
        f"{previous}Đoạn hội thoại cần tóm tắt:\n{_render(to_summarise)}",
    ).strip()

    if new_summary.startswith("[Lỗi"):        # LLM hỏng -> cắt bớt, không tóm tắt
        return summary, kept

    Conversations.set_summary(conversation_id, new_summary, to_summarise[-1]["id"])
    return new_summary, kept


def as_history(summary: str, messages: list[dict]) -> list:
    """Đổi sang dạng core.llm chấp nhận (có .role và .content)."""
    from types import SimpleNamespace
    out = []
    if summary:
        out.append(SimpleNamespace(
            role="user",
            content=f"[Tóm tắt cuộc trò chuyện trước đó]\n{summary}"))
    for m in messages:
        out.append(SimpleNamespace(role=m["role"], content=m["content"]))
    return out

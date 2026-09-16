"""Đo độ dài ngữ cảnh và nhờ AI tóm tắt khi vượt ngưỡng.

Ngữ cảnh đưa vào mô hình = tóm tắt dài hạn + N lượt gần nhất + hồ sơ người dùng.
Vượt MAX_CONTEXT_TOKENS thì tóm tắt phần cũ và GHI vào CSDL để lần sau không
phải tóm tắt lại. Mô hình nhỏ kém dần khi ngữ cảnh dài nên ngưỡng đặt thấp hơn
giới hạn kỹ thuật — vì chất lượng, không phải vì bị giới hạn.
"""

from __future__ import annotations

from config import (MAX_CONTEXT_TOKENS, SUMMARY_ENABLED, SUMMARY_KEEP_RECENT,
                    TOKENS_PER_SYLLABLE)
from core import llm
from db.repositories import Conversations, Messages
from prompts import templates as T


def estimate_tokens(text: str) -> int:
    """Ước lượng thô số token tiếng Việt. Đủ chính xác để quyết định có tóm tắt."""
    return int(len((text or "").split()) * TOKENS_PER_SYLLABLE)


def _render(messages: list[dict]) -> str:
    return "\n".join(
        f"{'Người dùng' if m['role'] == 'user' else 'Trợ lý'}: {T.strip_citations(m['content'])}"
        for m in messages
    )


def build_context(conversation_id: int) -> tuple[str, list[dict]]:
    """Trả về (tóm tắt, các tin nhắn gần nhất) đã nằm trong ngân sách token."""
    conv = Conversations.by_id(conversation_id)
    if conv is None:
        return "", []

    summary = conv["summary"] or ""
    recent = Messages.list_for(conversation_id, after_id=conv["summary_upto"] or 0)

    keep = SUMMARY_KEEP_RECENT * 2
    if not SUMMARY_ENABLED:
        return summary, recent[-keep:]

    total = estimate_tokens(summary) + sum(estimate_tokens(m["content"]) for m in recent)
    if total <= MAX_CONTEXT_TOKENS or len(recent) <= keep:
        return summary, recent

    to_summarise, kept = recent[:-keep], recent[-keep:]
    previous = f"Tóm tắt trước đó:\n{summary}\n\n" if summary else ""
    try:
        new_summary = llm.chat("summary", T.SUMMARY_SYSTEM,
                               f"{previous}Đoạn hội thoại cần tóm tắt:\n{_render(to_summarise)}")
    except llm.LLMError:
        return summary, kept                    # LLM hỏng -> cắt bớt, không tóm tắt

    Conversations.set_summary(conversation_id, new_summary, to_summarise[-1]["id"])
    return new_summary, kept

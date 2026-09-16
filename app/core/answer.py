"""Soạn câu trả lời từ Evidence Pack (và lời đáp xã giao).

Hợp đồng về MỤC TIÊU: prompt nói rõ người dùng đang hỏi khía cạnh nào và bắt trả
lời đúng khía cạnh đó trước; nguồn không có thì nói thẳng, không thay bằng thông
tin khác của thủ tục.
"""

from __future__ import annotations

from datetime import datetime

from core import llm
from domain.text import tidy_answer
from prompts import templates as T


def generate(question: str, standalone: str, target: str, pack: dict, summary: str,
             history: list[dict], profile: dict, fix_notes: str = "") -> str:
    info = llm.model_info()
    return tidy_answer(llm.chat(
        "answer",
        T.answer_system(datetime.now().strftime("%d/%m/%Y"), info["knowledge_cutoff"],
                        pack, profile, target, fix_notes),
        T.answer_user(question, standalone, target),
        T.history_messages(summary, history),
    ))


def chitchat(question: str, history: list[dict]) -> str:
    return llm.chat("chitchat", T.CHITCHAT_SYSTEM, question,
                    T.history_messages("", history[-4:]))

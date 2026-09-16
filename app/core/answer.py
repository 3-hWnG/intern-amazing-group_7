"""Soạn câu trả lời từ Evidence Pack (và lời đáp xã giao)."""

from __future__ import annotations

from datetime import datetime

from core import llm
from domain.text import tidy_answer
from prompts import templates as T


def generate(question: str, standalone: str, pack: dict, summary: str,
             history: list[dict], profile: dict, fix_notes: str = "") -> str:
    info = llm.model_info()
    return tidy_answer(llm.chat(
        "answer",
        T.answer_system(datetime.now().strftime("%d/%m/%Y"), info["knowledge_cutoff"],
                        pack, profile, fix_notes),
        T.answer_user(question, standalone),
        T.history_messages(summary, history),
    ))


def chitchat(question: str, history: list[dict]) -> str:
    return llm.chat("chitchat", T.CHITCHAT_SYSTEM,
                    f"{question}\n\n(Trả lời bằng tiếng Việt, kể cả khi tin nhắn viết bằng tiếng Anh.)",
                    T.history_messages("", history[-4:]))

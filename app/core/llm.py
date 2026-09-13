"""Cổng Ollama. Dùng đúng vai system + user thay vì nhét tất cả vào một tin nhắn."""

from __future__ import annotations

import ollama

from config import LLM_MODEL_NAME, LLM_OPTIONS


def _messages(system: str, user: str, history=None) -> list[dict]:
    msgs = [{"role": "system", "content": system}]
    for turn in history or []:
        msgs.append({"role": turn.role, "content": turn.content})
    msgs.append({"role": "user", "content": user})
    return msgs


def stream_chat(system: str, user: str, history=None):
    try:
        stream = ollama.chat(
            model=LLM_MODEL_NAME,
            messages=_messages(system, user, history),
            stream=True,
            options=LLM_OPTIONS,
        )
        for chunk in stream:
            yield chunk["message"]["content"]
    except Exception as exc:
        yield f"\n[Lỗi kết nối Ollama]: {exc}"


def complete(system: str, user: str, history=None) -> str:
    try:
        res = ollama.chat(
            model=LLM_MODEL_NAME,
            messages=_messages(system, user, history),
            options=LLM_OPTIONS,
        )
        return res["message"]["content"]
    except Exception as exc:
        return f"[Lỗi kết nối Ollama]: {exc}"

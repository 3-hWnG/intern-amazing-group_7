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


# ==========================================================================
# v6 — hai kiểu gọi phục vụ vòng lặp agent
# ==========================================================================
import json as _json
import re as _re


def _salvage_json(text: str) -> dict:
    """Mô hình 1.5B hay kèm lời dẫn quanh JSON. Moi lấy object đầu tiên."""
    text = (text or "").strip()
    try:
        value = _json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        pass
    match = _re.search(r"\{.*\}", text, _re.DOTALL)
    if not match:
        return {}
    try:
        value = _json.loads(match.group(0))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def complete_json(system: str, user: str, schema: dict | None = None,
                  options: dict | None = None) -> dict:
    """Gọi LLM và ÉP trả JSON. Trả về {} nếu không moi được gì.

    Ollama nhận `format` là JSON Schema (bản mới) hoặc chuỗi "json" (bản cũ).
    Thử schema trước, hỏng thì lùi về "json" — không để phiên bản thư viện làm
    sập cả luồng chat.
    """
    opts = {**LLM_OPTIONS, **(options or {})}
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user}]

    for fmt in ([schema, "json"] if schema else ["json"]):
        try:
            res = ollama.chat(model=LLM_MODEL_NAME, messages=messages,
                              format=fmt, options=opts)
            parsed = _salvage_json(res["message"]["content"])
            if parsed:
                return parsed
        except Exception:
            continue
    return {}


def chat_tools(system: str, user: str, history=None, tools=None) -> list[dict]:
    """Tool-calling GỐC của Ollama (dùng khi cắm mô hình lớn).

    Trả về [{"name": ..., "arguments": {...}}]; danh sách rỗng = không gọi gì.
    """
    try:
        res = ollama.chat(
            model=LLM_MODEL_NAME,
            messages=_messages(system, user, history),
            tools=tools or [],
            options=LLM_OPTIONS,
        )
    except Exception:
        return []

    message = res.get("message") or {}
    calls = message.get("tool_calls") or []
    out = []
    for call in calls:
        fn = (call.get("function") or {}) if isinstance(call, dict) else {}
        name = fn.get("name")
        args = fn.get("arguments") or {}
        if isinstance(args, str):
            args = _salvage_json(args)
        if name:
            out.append({"name": name, "arguments": args})
    return out

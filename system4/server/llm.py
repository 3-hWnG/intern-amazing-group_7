"""Gọi Qwen qua Ollama theo luồng (chữ hiện dần) cho Friendly mode.

Một lượt chạy tại một thời điểm (GPU 6 GB); người đến sau xếp hàng và được báo vị trí.
Ollama tự xếp hàng giữa System 3 và System 4 vì cả hai dùng chung một model.
"""
from __future__ import annotations
import asyncio
import json
import threading

import ollama

from . import config, settings


THINKING = object()   # tín hiệu "AI đang suy nghĩ" (phần suy nghĩ không gửi cho người dùng)


class LLMError(RuntimeError):
    pass


class QueueFull(RuntimeError):
    pass


_gate = asyncio.Semaphore(1)
_waiting = 0


def queue_position() -> int:
    """Số lượt đang chạy/đang chờ trước một người mới đến."""
    return _waiting + (1 if _gate.locked() else 0)


class Turn:
    """Giữ chỗ trong hàng: `async with Turn(): ...`. Đầy hàng -> QueueFull."""

    async def __aenter__(self):
        global _waiting
        if _waiting >= settings.get("FRIENDLY_QUEUE_MAX"):
            raise QueueFull("Hệ thống đang bận, vui lòng thử lại sau ít phút.")
        _waiting += 1
        try:
            await _gate.acquire()
        finally:
            _waiting -= 1
        return self

    async def __aexit__(self, *exc):
        _gate.release()


def chat_json(messages: list[dict], schema: dict, timeout: float = 60) -> dict:
    """Gọi một lần, ép đầu ra theo JSON schema (bộ nhớ, tóm tắt). Ép JSON làm model bỏ qua phần suy nghĩ nên nhanh.
    Lỗi -> {} (việc phụ, không làm hỏng câu trả lời chính)."""
    try:
        res = ollama.Client(host=config.OLLAMA_HOST, timeout=timeout).chat(
            model=settings.get("FRIENDLY_MODEL"), messages=messages, format=schema, think=False, keep_alive="30m",
            options={"temperature": 0, "num_ctx": settings.get("FRIENDLY_NUM_CTX")})
        v = json.loads(res["message"]["content"] or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _stream(call: dict, model: str):
    """Chạy client.chat(stream=True) ở luồng riêng, trả async generator các mẩu: chữ (str) hoặc THINKING.
    Lỗi Ollama -> LLMError. Ngắt giữa chừng (người dùng rời trang / bấm Trả lời nhanh) -> dừng gọi model."""
    async def gen():
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        stop = threading.Event()
        client = ollama.Client(host=config.OLLAMA_HOST, timeout=settings.get("FRIENDLY_TIMEOUT"))

        def work():
            try:
                for part in client.chat(model=model, stream=True, keep_alive="30m", **call):
                    if stop.is_set():
                        break
                    if part["message"].get("thinking"):
                        loop.call_soon_threadsafe(q.put_nowait, ("thinking", None))
                    text = part["message"]["content"]
                    if text:
                        loop.call_soon_threadsafe(q.put_nowait, ("delta", text))
                loop.call_soon_threadsafe(q.put_nowait, ("end", None))
            except Exception as exc:   # Ollama tắt, model chưa tải, quá thời gian...
                loop.call_soon_threadsafe(q.put_nowait, ("error", f"Không gọi được model {model}: {exc}"))

        threading.Thread(target=work, daemon=True).start()
        try:
            while True:
                kind, val = await q.get()
                if kind == "delta":
                    yield val
                elif kind == "thinking":
                    yield THINKING   # mỗi mẩu suy nghĩ một lần: để bên gọi kiểm "Trả lời nhanh" kịp thời
                elif kind == "end":
                    return
                else:
                    raise LLMError(val)
        finally:
            stop.set()
    return gen()


def _opts() -> dict:
    return {"temperature": settings.get("FRIENDLY_TEMPERATURE"), "num_ctx": settings.get("FRIENDLY_NUM_CTX")}


def stream_chat(messages: list[dict]):
    """Chế độ Suy nghĩ kỹ: model suy nghĩ (ẩn) rồi trả lời. Sinh chữ và THINKING."""
    return _stream({"messages": messages, "think": True, "options": _opts()}, settings.get("FRIENDLY_MODEL"))


def stream_json(messages: list[dict], schema: dict):
    """Chế độ Nhanh: ép đầu ra theo JSON schema -> model không suy nghĩ, trả lời trong ~1-3 giây. Sinh các mẩu JSON thô."""
    return _stream({"messages": messages, "format": schema, "think": False, "options": _opts()}, settings.get("FRIENDLY_MODEL"))

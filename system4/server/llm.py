"""Gọi Qwen qua Ollama theo luồng (chữ hiện dần) cho Friendly mode.

Một lượt chạy tại một thời điểm (GPU 6 GB); người đến sau xếp hàng và được báo vị trí.
Ollama tự xếp hàng giữa System 3 và System 4 vì cả hai dùng chung một model.
"""
from __future__ import annotations
import asyncio
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


async def stream_chat(messages: list[dict]):
    """Sinh từng mẩu chữ (và THINKING một lần khi model bắt đầu suy nghĩ).
    Lỗi Ollama -> LLMError. Ngắt giữa chừng (người dùng rời trang) -> dừng gọi model."""
    loop = asyncio.get_running_loop()
    q: asyncio.Queue = asyncio.Queue()
    stop = threading.Event()
    model, think = settings.get("FRIENDLY_MODEL"), settings.get("FRIENDLY_THINK")
    opts = {"temperature": settings.get("FRIENDLY_TEMPERATURE"), "num_ctx": settings.get("FRIENDLY_NUM_CTX")}
    client = ollama.Client(host=config.OLLAMA_HOST, timeout=settings.get("FRIENDLY_TIMEOUT"))

    def work():
        try:
            signalled = False
            for part in client.chat(model=model, messages=messages, stream=True, think=think,
                                    options=opts, keep_alive="30m"):
                if stop.is_set():
                    break
                if part["message"].get("thinking") and not signalled:
                    signalled = True
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
                yield THINKING
            elif kind == "end":
                return
            else:
                raise LLMError(val)
    finally:
        stop.set()

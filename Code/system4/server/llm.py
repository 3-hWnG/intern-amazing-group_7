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


class Thought(str):
    """Một mẩu "suy nghĩ" ẩn của model (không gửi cho người dùng; bộ công cụ dev lưu lại để xem)."""


THINKING = Thought("")   # tín hiệu "AI đang suy nghĩ" không kèm chữ (test dùng)


class Stats(dict):
    """Số đo Ollama gửi ở mẩu cuối (giây / token): nạp model, đọc lời dặn, viết. Bộ đo và 🔍 dùng để biết chậm ở đâu."""


def _stats(part) -> "Stats":
    g = lambda k: getattr(part, k, None) or 0
    return Stats(load_s=round(g("load_duration") / 1e9, 3), prompt_tokens=g("prompt_eval_count"),
                 prompt_s=round(g("prompt_eval_duration") / 1e9, 3), output_tokens=g("eval_count"),
                 output_s=round(g("eval_duration") / 1e9, 3), total_s=round(g("total_duration") / 1e9, 3))


def keep_alive():
    """Giữ model trong card đồ hoạ: mãi mãi (cài đặt "Giữ model luôn nạp sẵn") hoặc 30 phút như trước."""
    return -1 if settings.get("KEEP_MODELS_LOADED") else "30m"


def think_model() -> str:
    return settings.get("THINK_MODEL") or settings.get("FRIENDLY_MODEL")


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
            model=settings.get("FRIENDLY_MODEL"), messages=messages, format=schema, think=False, keep_alive=keep_alive(),
            options={"temperature": 0, "num_ctx": settings.get("FRIENDLY_NUM_CTX")})
        v = json.loads(res["message"]["content"] or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _stream(call: dict, model: str):
    """Chạy client.chat(stream=True) ở luồng riêng, trả async generator các mẩu: chữ (str), Thought, và Stats ở cuối.
    Lỗi Ollama -> LLMError. Ngắt giữa chừng (người dùng rời trang / bấm Trả lời nhanh) -> dừng gọi model."""
    async def gen():
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        stop = threading.Event()
        client = ollama.Client(host=config.OLLAMA_HOST, timeout=settings.get("FRIENDLY_TIMEOUT"))

        def work():
            try:
                for part in client.chat(model=model, stream=True, keep_alive=keep_alive(), **call):
                    if stop.is_set():
                        break
                    if getattr(part, "done", False):
                        loop.call_soon_threadsafe(q.put_nowait, ("stats", _stats(part)))
                    if part["message"].get("thinking"):
                        loop.call_soon_threadsafe(q.put_nowait, ("thinking", part["message"]["thinking"]))
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
                elif kind == "stats":
                    yield val
                elif kind == "thinking":
                    yield Thought(val)   # mỗi mẩu suy nghĩ một lần: để bên gọi kiểm "Trả lời nhanh" kịp thời + lưu cho dev
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
    return _stream({"messages": messages, "think": True, "options": _opts()}, think_model())


def stream_json(messages: list[dict], schema: dict):
    """Chế độ Nhanh: ép đầu ra theo JSON schema -> model không suy nghĩ, trả lời trong ~1-3 giây. Sinh các mẩu JSON thô."""
    return _stream({"messages": messages, "format": schema, "think": False, "options": _opts()}, settings.get("FRIENDLY_MODEL"))


def stream_text(messages: list[dict]):
    """Chế độ Nhanh dạng chữ (FAST_FORMAT=text): không ép JSON, không suy nghĩ. Chỉ hợp với model không suy nghĩ (bản Instruct)."""
    return _stream({"messages": messages, "think": False, "options": _opts()}, settings.get("FRIENDLY_MODEL"))


def warm_up() -> None:
    """Khởi động server (KEEP_MODELS_LOADED): nạp sẵn model trả lời, cùng num_ctx với lúc trả lời để Ollama không nạp lại."""
    if not settings.get("KEEP_MODELS_LOADED"):
        return
    try:
        ollama.Client(host=config.OLLAMA_HOST, timeout=120).generate(
            model=settings.get("FRIENDLY_MODEL"), prompt="", keep_alive=-1, options={"num_ctx": settings.get("FRIENDLY_NUM_CTX")})
    except Exception:
        pass

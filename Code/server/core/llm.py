"""Client Ollama (copy rút gọn từ V10.6 core/llm.py).

Khác bản gốc: bỏ ROLE_OPTIONS/verify/status của System 1-2; thêm
  - `schema` : JSON schema truyền thẳng vào tham số `format` của Ollama
  - `think`  : False tắt thinking (qwen3); mặc định theo config.LLM_THINK
"""
from __future__ import annotations
import os
import json
import re
import threading
import time

import ollama

from . import aihealth, gpu
from config import (LLM_KEEP_ALIVE, LLM_MODEL, LLM_NUM_CTX, LLM_THINK,
                    LLM_TIMEOUT, OLLAMA_HOST)


# System 4 (hook.install) gắn hàm trả tên model đang chọn trong ⚙ Cài đặt, để Strict và Friendly dùng chung một model.
MODEL_PROVIDER = None


def model_name() -> str:
    return (MODEL_PROVIDER() if MODEL_PROVIDER else "") or LLM_MODEL


class LLMError(RuntimeError):
    pass


# G3.4 (P16): số đo từng lời gọi trong lượt hiện tại (luồng hiện tại): chờ GPU / nạp model / đọc lời dặn / sinh chữ (giây).
_turn = threading.local()


def turn_stats_reset() -> None:
    _turn.stats = []


def turn_stats() -> list[dict]:
    return list(getattr(_turn, "stats", []) or [])


def _record(**kw) -> None:
    if not hasattr(_turn, "stats"):
        _turn.stats = []
    _turn.stats.append(kw)


_clients: dict[float, ollama.Client] = {}


def client(timeout: float | None = None) -> ollama.Client:
    t = timeout or LLM_TIMEOUT
    if t not in _clients:
        _clients[t] = ollama.Client(host=OLLAMA_HOST, timeout=t)
    return _clients[t]


def chat(system: str, user: str, history: list[dict] | None = None, *,
         schema: dict | str | None = None, think: bool | None = None,
         model: str | None = None, timeout: float | None = None, priority: int = gpu.P0,
         wait: float | None = None, **options) -> str:
    """Gọi chat. schema (dict JSON schema, hoặc "json") -> ràng buộc đầu ra. timeout (giây) cứng, httpx.
    G3.1: xin chỗ GPU chung (core/gpu.py) trước khi gọi; chờ quá `wait` giây (mặc định = timeout) -> LLMError
    (bên gọi rơi về câu trả lời bằng code). Phần luật không đi qua đây nên không phải chờ."""
    msgs = [{"role": "system", "content": system}]
    msgs += [{"role": m["role"], "content": m["content"]} for m in history or []]
    msgs.append({"role": "user", "content": user})
    opts = {"num_ctx": LLM_NUM_CTX, "temperature": 0.0 if schema else 0.3, **options}
    name = model or model_name()
    if not aihealth.breaker.allow():   # G3.3: Ollama lỗi liên tiếp -> bỏ qua AI một lúc, không chờ hết hạn từng lần
        raise LLMError("Ollama lỗi liên tiếp, tạm bỏ qua bước AI")
    t0 = time.perf_counter()
    t_got = None
    try:
        with gpu.slot(priority, timeout=wait if wait is not None else (timeout or LLM_TIMEOUT)):
            t_got = time.perf_counter()
            res = client(timeout).chat(model=name, messages=msgs, format=schema,
                                       keep_alive=LLM_KEEP_ALIVE, options=opts,
                                       think=LLM_THINK if think is None else think)
    except gpu.Busy as exc:
        _record(wait_s=round(time.perf_counter() - t0, 3), error="gpu_busy")
        raise LLMError(f"GPU đang bận (đang trả lời người khác), bỏ qua bước AI: {exc}") from exc
    except Exception as exc:
        aihealth.breaker.fail()
        _record(wait_s=round((t_got or time.perf_counter()) - t0, 3), call_s=round(time.perf_counter() - (t_got or t0), 3),
                error=type(exc).__name__)
        raise LLMError(f"Không gọi được mô hình {name} tại {OLLAMA_HOST}: {exc}") from exc
    aihealth.breaker.ok()
    g = lambda k: (res.get(k) if isinstance(res, dict) else getattr(res, k, None)) or 0
    _record(wait_s=round(t_got - t0, 3), call_s=round(time.perf_counter() - t_got, 3), load_s=round(g("load_duration") / 1e9, 3),
            prompt_s=round(g("prompt_eval_duration") / 1e9, 3), gen_s=round(g("eval_duration") / 1e9, 3),
            prompt_tokens=g("prompt_eval_count"), output_tokens=g("eval_count"))
    return (res["message"]["content"] or "").strip()


def chat_json(system: str, user: str, schema: dict | None = None,
              history: list[dict] | None = None, **kw) -> dict:
    """Trả dict ({} nếu hỏng). schema=None -> format='json'."""
    return _salvage_json(chat(system, user, history, schema=schema or "json", **kw))


def _salvage_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    for cand in (text, m.group(0) if m else ""):
        try:
            v = json.loads(cand)
            if isinstance(v, dict):
                return v
        except Exception:
            pass
    return {}


def warm_up() -> None:
    if os.environ.get("S3_NO_WARMUP") == "1":   # test/CI hoặc máy đang bận GPU: không nạp model
        return
    try:
        client().generate(model=model_name(), prompt="", keep_alive=LLM_KEEP_ALIVE,
                          options={"num_ctx": LLM_NUM_CTX})   # cùng num_ctx với chat() để không nạp lại
    except Exception:
        pass


def loaded_models() -> list[str]:
    """Tên model Ollama đang nạp trong bộ nhớ (GET /config); lỗi/Ollama tắt -> []."""
    try:
        return [m.get("model") or m.get("name") for m in client(3).ps().get("models", [])]
    except Exception:
        return []

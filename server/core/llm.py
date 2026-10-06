"""Client Ollama (copy rút gọn từ V10.6 core/llm.py).

Khác bản gốc: bỏ ROLE_OPTIONS/verify/status của System 1-2; thêm
  - `schema` : JSON schema truyền thẳng vào tham số `format` của Ollama
  - `think`  : False tắt thinking (qwen3); mặc định theo config.LLM_THINK
"""
from __future__ import annotations
import json
import re

import ollama

from config import (LLM_KEEP_ALIVE, LLM_MODEL, LLM_NUM_CTX, LLM_THINK,
                    LLM_TIMEOUT, OLLAMA_HOST)


class LLMError(RuntimeError):
    pass


_clients: dict[float, ollama.Client] = {}


def client(timeout: float | None = None) -> ollama.Client:
    t = timeout or LLM_TIMEOUT
    if t not in _clients:
        _clients[t] = ollama.Client(host=OLLAMA_HOST, timeout=t)
    return _clients[t]


def chat(system: str, user: str, history: list[dict] | None = None, *,
         schema: dict | str | None = None, think: bool | None = None,
         model: str | None = None, timeout: float | None = None, **options) -> str:
    """Gọi chat. schema (dict JSON schema, hoặc "json") -> ràng buộc đầu ra. timeout (giây) cứng, httpx."""
    msgs = [{"role": "system", "content": system}]
    msgs += [{"role": m["role"], "content": m["content"]} for m in history or []]
    msgs.append({"role": "user", "content": user})
    opts = {"num_ctx": LLM_NUM_CTX, "temperature": 0.0 if schema else 0.3, **options}
    name = model or LLM_MODEL
    try:
        res = client(timeout).chat(model=name, messages=msgs, format=schema,
                            keep_alive=LLM_KEEP_ALIVE, options=opts,
                            think=LLM_THINK if think is None else think)
    except Exception as exc:
        raise LLMError(f"Không gọi được mô hình {name} tại {OLLAMA_HOST}: {exc}") from exc
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
    try:
        client().generate(model=LLM_MODEL, prompt="", keep_alive=LLM_KEEP_ALIVE,
                          options={"num_ctx": LLM_NUM_CTX})   # cùng num_ctx với chat() để không nạp lại
    except Exception:
        pass


def loaded_models() -> list[str]:
    """Tên model Ollama đang nạp trong bộ nhớ (GET /config); lỗi/Ollama tắt -> []."""
    try:
        return [m.get("model") or m.get("name") for m in client(3).ps().get("models", [])]
    except Exception:
        return []

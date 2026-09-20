"""Cổng Ollama — MỘT mô hình nhỏ (mục tiêu 3–4B, thử nghiệm 1.5B) đóng nhiều vai.

    understand  hiểu ý định + ngữ cảnh + truy vấn tìm kiếm   JSON có schema, temperature 0
    answer      soạn câu trả lời từ Evidence Pack             temperature thấp
    verify      kiểm chứng bản nháp với bằng chứng            JSON có schema, temperature 0
    summary     tóm tắt hội thoại khi ngữ cảnh quá dài
    chitchat    đáp lời chào ngắn gọn

Mô hình KHÔNG chịu trách nhiệm về độ mới của thông tin — việc đó thuộc về MCP.
"""

from __future__ import annotations

import json
import re

import ollama

from config import (ANSWER_MAX_TOKENS, FINETUNE_RUNS_PATH, LLM_KEEP_ALIVE,
                    LLM_MODEL, LLM_NUM_CTX, LLM_TIMEOUT, MODEL_KNOWLEDGE_CUTOFF,
                    OLLAMA_HOST, TEMPERATURE, TOP_P, VERIFIER_MODEL)

ROLE_OPTIONS = {
    "understand": {"temperature": 0.0, "num_predict": 450},
    # repeat_last_n rộng: mô hình nhỏ hay lặp lại nguyên một gạch đầu dòng
    "answer": {"temperature": TEMPERATURE, "top_p": TOP_P, "repeat_penalty": 1.15,
               "repeat_last_n": 256, "num_predict": ANSWER_MAX_TOKENS},
    "verify": {"temperature": 0.0, "num_predict": 350},
    "summary": {"temperature": 0.1, "num_predict": 350},
    "chitchat": {"temperature": 0.4, "top_p": 0.9, "num_predict": 160},
}


class LLMError(RuntimeError):
    """Không gọi được mô hình — thông điệp đã sẵn sàng để hiển thị."""


_client: ollama.Client | None = None


def client() -> ollama.Client:
    global _client
    if _client is None:
        _client = ollama.Client(host=OLLAMA_HOST, timeout=LLM_TIMEOUT)
    return _client


def model_for(role: str) -> str:
    return VERIFIER_MODEL if role == "verify" else LLM_MODEL


def _messages(system: str, user: str, history: list[dict] | None) -> list[dict]:
    msgs = [{"role": "system", "content": system}]
    msgs += [{"role": m["role"], "content": m["content"]} for m in history or []]
    msgs.append({"role": "user", "content": user})
    return msgs


def _call(role: str, system: str, user: str, history=None, fmt=None) -> str:
    model = model_for(role)
    try:
        res = client().chat(model=model, messages=_messages(system, user, history),
                            format=fmt, keep_alive=LLM_KEEP_ALIVE,
                            options={"num_ctx": LLM_NUM_CTX, **ROLE_OPTIONS[role]})
    except Exception as exc:
        raise LLMError(f"Không gọi được mô hình {model} tại {OLLAMA_HOST}: {exc}") from exc
    return (res["message"]["content"] or "").strip()


def chat(role: str, system: str, user: str, history: list[dict] | None = None) -> str:
    return _call(role, system, user, history)


def chat_json(role: str, system: str, user: str, schema: dict,
              history: list[dict] | None = None) -> dict:
    """Ollama ràng buộc đầu ra theo JSON Schema -> luôn parse được."""
    return _salvage_json(_call(role, system, user, history, fmt=schema))


def _salvage_json(text: str) -> dict:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        match = re.search(r"\{.*\}", text or "", re.DOTALL)
        if not match:
            return {}
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}


def warm_up() -> None:
    """Nạp sẵn mô hình vào VRAM để câu hỏi đầu tiên không phải chờ."""
    try:
        client().generate(model=LLM_MODEL, prompt="", keep_alive=LLM_KEEP_ALIVE)
    except Exception:
        pass


def model_info() -> dict:
    """Mốc thời gian của MÔ HÌNH để so với mốc của BẰNG CHỨNG.

    knowledge_cutoff: kiến thức trong trọng số dừng ở đâu (config).
    finetuned_at:     lần fine-tune gần nhất ra đúng mô hình đang chạy
                      (Utility/finetune/runs.jsonl do train_qlora.py ghi).
    """
    info = {"model": LLM_MODEL, "verifier_model": VERIFIER_MODEL,
            "knowledge_cutoff": MODEL_KNOWLEDGE_CUTOFF, "finetuned_at": None,
            "finetune_base": None}
    try:
        for line in FINETUNE_RUNS_PATH.read_text(encoding="utf-8").splitlines():
            run = json.loads(line) if line.strip() else {}
            if run.get("ollama_model") == LLM_MODEL:
                info["finetuned_at"] = run.get("finished_at")
                info["finetune_base"] = run.get("base_model")
    except Exception:
        pass
    return info


def status() -> dict:
    """Ollama có chạy không, mô hình đã pull chưa."""
    wanted = {LLM_MODEL, VERIFIER_MODEL}
    try:
        listed = client().list()
        names = {m.model for m in listed.models}
    except Exception as exc:
        return {"reachable": False, "host": OLLAMA_HOST, "error": str(exc),
                "models": sorted(wanted), "missing": sorted(wanted)}
    full = lambda n: n if ":" in n else f"{n}:latest"   # noqa: E731
    missing = sorted(n for n in wanted if full(n) not in names)
    return {"reachable": True, "host": OLLAMA_HOST, "models": sorted(wanted), "missing": missing}

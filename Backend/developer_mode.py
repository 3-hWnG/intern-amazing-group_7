"""Chế độ nhà phát triển — một chỗ duy nhất cho mọi công cụ soi hệ thống.

Khi trợ lý trả lời sai, nhìn từ ngoài không biết được vì sao: hiểu nhầm ý định?
truy vấn MCP tệ? nguồn không liên quan? kiểm chứng bắt được gì? Bảng Dev ghi
lại từng bước của orchestrator để trả lời những câu đó.

Hai lớp, ĐỪNG nhầm:
    DEV_TOOLS_ENABLED (config)   quyết định có ĐĂNG KÝ route hay không (bảo mật thật).
    developer_mode.enabled()     quyết định có GHI LẠI vết chạy hay không (bật/tắt trên UI).

Ghi vết nằm trong RAM (deque), không đụng CSDL, không ghi ra đĩa.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

from config import DEVMODE_DEFAULT_ON, DEVMODE_TRACE_SIZE

_lock = threading.Lock()
_enabled = bool(DEVMODE_DEFAULT_ON)
_traces: deque[dict] = deque(maxlen=int(DEVMODE_TRACE_SIZE))
_seq = 0


# ==========================================================================
# bật / tắt
# ==========================================================================
def enabled() -> bool:
    return _enabled


def set_enabled(value: bool) -> bool:
    global _enabled
    with _lock:
        _enabled = bool(value)
    return _enabled


def toggle() -> bool:
    return set_enabled(not _enabled)


# ==========================================================================
# ghi vết một lượt hỏi-đáp
# ==========================================================================
class Turn:
    """Gom mọi thứ xảy ra trong MỘT lượt. Không bật dev mode thì gần như free."""

    __slots__ = ("question", "conversation_id", "started", "events", "meta")

    def __init__(self, question: str, conversation_id: int | None = None):
        self.question = question
        self.conversation_id = conversation_id
        self.started = time.time()
        self.events: list[dict] = []
        self.meta: dict[str, Any] = {}

    def event(self, _kind: str, **payload) -> None:
        """Tên tham số có dấu gạch dưới để payload được phép chứa khoá 'kind'."""
        if not _enabled:
            return
        self.events.append({
            **payload,
            "kind": _kind,
            "at_ms": round((time.time() - self.started) * 1000),
        })

    def set(self, **meta) -> None:
        if _enabled:
            self.meta.update(meta)

    def finish(self) -> None:
        if not _enabled:
            return
        global _seq
        with _lock:
            _seq += 1
            _traces.appendleft({
                "id": _seq,
                "ts": time.time(),
                "question": self.question,
                "conversation_id": self.conversation_id,
                "total_ms": round((time.time() - self.started) * 1000),
                "events": self.events,
                **self.meta,
            })


def turn(question: str, conversation_id: int | None = None) -> Turn:
    return Turn(question, conversation_id)


def traces(limit: int = 10) -> list[dict]:
    with _lock:
        return list(_traces)[:max(1, int(limit))]


def clear_traces() -> int:
    with _lock:
        n = len(_traces)
        _traces.clear()
        return n


# ==========================================================================
# ảnh chụp cấu hình đang chạy
# ==========================================================================
def snapshot() -> dict:
    import config
    keys = [
        "LLM_MODEL", "VERIFIER_MODEL", "OLLAMA_HOST", "LLM_NUM_CTX", "TEMPERATURE",
        "TOP_P", "ANSWER_MAX_TOKENS", "MODEL_KNOWLEDGE_CUTOFF", "CLARIFY_ENABLED",
        "MCP_TRANSPORT", "MCP_SERVER_URL", "MCP_FALLBACK_DIRECT", "SEARCH_PROVIDER",
        "SEARCH_DDGS_BACKEND", "SEARCH_MAX_QUERIES", "SEARCH_RESULTS_PER_QUERY",
        "SEARCH_DEADLINE", "SEARCH_OFFICIAL_ONLY", "FETCH_TOP_N", "FETCH_DEADLINE",
        "EVIDENCE_TOP_K", "EVIDENCE_MAX_CHARS", "UNDERSTAND_FEWSHOT", "VERIFIER_ENABLED",
        "MAX_VERIFY_RETRIES", "VERIFY_FAIL_POLICY", "SUMMARY_ENABLED",
        "MAX_CONTEXT_TOKENS", "SUMMARY_KEEP_RECENT", "PROFILE_MEMORY_ENABLED",
        "QUEUE_ENABLED", "QUEUE_CONCURRENCY", "ATTACHMENTS_ENABLED", "STATIC_VERSION",
    ]
    return {
        "developer_mode": _enabled,
        "config": {k: getattr(config, k, None) for k in keys},
    }


# ==========================================================================
# chẩn đoán tìm kiếm qua MCP
# ==========================================================================
def websearch_check(query: str = "") -> dict:
    """Gọi công cụ web_search qua MCP. Phân biệt: MCP hỏng / nhà cung cấp tìm kiếm hỏng / rỗng."""
    from config import SEARCH_PROVIDER
    from core import mcp_client

    query = query or "thủ tục cấp hộ chiếu phổ thông"
    started = time.time()
    data, transport, error = {}, "", ""
    try:
        data, transport = mcp_client.call_tool("web_search", {"query": query, "max_results": 8})
        if not isinstance(data, dict):
            data, error = {}, f"dữ liệu lạ từ MCP: {str(data)[:200]}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    results = data.get("results") or []
    if not error and not results:
        error = "nhà cung cấp tìm kiếm không trả kết quả (xem diagnostics)"
    return {
        "query": query, "ok": bool(results), "error": error, "transport": transport,
        "provider": SEARCH_PROVIDER, "mcp": mcp_client.status(),
        "elapsed_ms": int((time.time() - started) * 1000),
        "results": results, "diagnostics": data.get("diagnostics") or [],
    }

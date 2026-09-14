"""Chế độ nhà phát triển — một chỗ duy nhất cho mọi công cụ soi hệ thống.

Vì sao cần: khi trợ lý trả lời sai, nhìn từ ngoài KHÔNG tài nào biết được vì
sao. Nó chọn công cụ nào? Truy hồi ra thủ tục gì, điểm bao nhiêu? Tra web hỏng
ở bước nào, hay tra được mà bị allowlist chặn? Trước đây tất cả những thứ đó
chỉ hiện ra dưới dạng một câu xin lỗi chung chung.

Hai lớp, ĐỪNG nhầm:

    DEV_TOOLS_ENABLED (config.py)  quyết định có ĐĂNG KÝ route hay không.
                                   Đây là bảo mật thật: False = endpoint không
                                   tồn tại. Đặt False trước khi bàn giao.

    developer_mode.enabled()       quyết định có GHI LẠI vết chạy hay không.
                                   Bật/tắt ngay trong giao diện, không cần
                                   khởi động lại.

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
        # payload đặt TRƯỚC: loại sự kiện luôn thắng, không bị payload ghi đè.
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


_NULL = Turn("")          # dùng khi tắt dev mode: mọi thao tác đều không làm gì


def turn(question: str, conversation_id: int | None = None) -> Turn:
    return Turn(question, conversation_id) if _enabled else _NULL


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
    """Mọi công tắc đang ảnh hưởng tới hành vi. Xem nhanh thay vì mở config.py."""
    import config
    keys = [
        "ORCHESTRATOR", "LLM_MODEL_NAME", "AGENT_TOOL_MODE", "AGENT_MAX_STEPS",
        "AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL", "ANSWER_STYLE",
        "EXACT_ON_FACET", "FOLLOWUP_STICKY", "FACTCHECK_ENABLED",
        "FACTCHECK_MAX_RETRIES", "TIER_A_MIN_CONFIDENCE",
        "TIER_B_MIN_CONFIDENCE", "EVIDENCE_TIE_GAP", "USE_DENSE",
        "USE_LEXICAL", "USE_RERANKER", "WEB_SEARCH_ENABLED",
        "WEB_SEARCH_STRICT", "WEB_SEARCH_TIMEOUT", "SESSION_ENABLED",
        "SUMMARY_ENABLED", "QUEUE_ENABLED", "QUEUE_CONCURRENCY",
        "ATTACHMENTS_ENABLED", "STATIC_VERSION",
    ]
    return {
        "developer_mode": _enabled,
        "config": {k: getattr(config, k, None) for k in keys},
    }


# ==========================================================================
# chẩn đoán tìm kiếm web
# ==========================================================================
def websearch_check(query: str = "") -> dict:
    """Chạy thử tra web và nói THẲNG hỏng ở đâu.

    Bốn kết cục hoàn toàn khác nhau mà bản cũ gộp chung thành "không có kết quả":
      - thiếu thư viện          -> cài ddgs
      - thư viện ném lỗi        -> mất mạng / bị chặn tốc độ / đổi API
      - bị allowlist chặn       -> tra ĐƯỢC, nhưng nguồn không chính thống
      - thật sự rỗng            -> đổi từ khoá
    """
    from core import websearch
    out = websearch.selftest(query or "thủ tục cấp hộ chiếu phổ thông")

    if out["library"] is None:
        out["diagnosis"] = "THIẾU THƯ VIỆN"
        out["fix"] = r".venv\Scripts\python.exe -m pip install ddgs"
    elif out["ok"]:
        out["diagnosis"] = "CHẠY TỐT"
        out["fix"] = ""
    elif out["blocked_by_allowlist"]:
        out["diagnosis"] = "BỊ ALLOWLIST CHẶN — tra được nhưng nguồn không chính thống"
        out["fix"] = ("Thêm domain vào WEB_SEARCH_ALLOWLIST trong config.py, "
                      "hoặc đặt WEB_SEARCH_STRICT = False (sẽ nhận nguồn "
                      "không chính thống — cân nhắc kỹ).")
    elif any(a["error"] for a in out["attempts"]):
        out["diagnosis"] = "THƯ VIỆN LỖI — mất mạng, bị chặn tốc độ, hoặc đổi API"
        out["fix"] = ("Kiểm tra mạng. Nếu lỗi kiểu RatelimitException thì chờ "
                      "vài phút. Nếu gói cũ: pip install -U ddgs")
    else:
        out["diagnosis"] = "KHÔNG CÓ KẾT QUẢ — từ khoá quá hẹp"
        out["fix"] = "Thử từ khoá ngắn hơn."
    return out

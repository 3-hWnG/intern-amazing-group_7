"""Bộ nhớ hội thoại. Hiện lưu trong RAM; đổi sang Redis chỉ cần thay 2 hàm.

Mentor đã chỉ ra demo không nhớ ngữ cảnh - trong khi chạy Ollama trần thì nhớ.
Đây là phần vá lại điều đó.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from config import (PENDING_QUESTION_TTL, SESSION_ENABLED, SESSION_MAX_TURNS,
                    SESSION_TTL_SECONDS)


@dataclass
class Turn:
    role: str
    content: str
    ts: float = field(default_factory=time.time)


@dataclass
class Session:
    session_id: str
    turns: list[Turn] = field(default_factory=list)
    pending: dict | None = None          # câu hỏi lại đang chờ trả lời (Tier B)
    updated: float = field(default_factory=time.time)


_STORE: dict[str, Session] = {}


def _expire():
    now = time.time()
    for sid in [s for s, v in _STORE.items() if now - v.updated > SESSION_TTL_SECONDS]:
        _STORE.pop(sid, None)


def get(session_id: str) -> Session:
    _expire()
    if session_id not in _STORE:
        _STORE[session_id] = Session(session_id=session_id)
    return _STORE[session_id]


def add_turn(session_id: str, role: str, content: str):
    if not SESSION_ENABLED:
        return
    s = get(session_id)
    s.turns.append(Turn(role=role, content=content))
    s.turns = s.turns[-SESSION_MAX_TURNS * 2:]
    s.updated = time.time()


def history(session_id: str) -> list[Turn]:
    if not SESSION_ENABLED:
        return []
    return get(session_id).turns[-SESSION_MAX_TURNS * 2:]


def set_pending(session_id: str, payload: dict):
    s = get(session_id)
    s.pending = {**payload, "ts": time.time()}
    s.updated = time.time()


def take_pending(session_id: str) -> dict | None:
    """Lấy và xoá câu hỏi lại đang chờ, nếu còn hạn."""
    s = get(session_id)
    if not s.pending:
        return None
    if time.time() - s.pending.get("ts", 0) > PENDING_QUESTION_TTL:
        s.pending = None
        return None
    pending, s.pending = s.pending, None
    return pending

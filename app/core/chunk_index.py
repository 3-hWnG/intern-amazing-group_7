"""Tra cứu trong TỆP ĐÍNH KÈM của một cuộc trò chuyện.

Chunk đã lưu ở SQLite (bảng document_chunks). Chỉ mục BM25 dựng lười trong RAM
theo từng hội thoại (vài chục chunk, vài mili giây) — không cần mô hình nhúng
hay vector DB. Kết quả đi vào Evidence Pack như một nguồn "tệp đính kèm".
"""

from __future__ import annotations

import threading

from config import ATTACH_TOP_K
from db.repositories import DocumentChunks
from domain.text import BM25

_CACHE: dict[int, tuple[list[dict], BM25]] = {}
_lock = threading.Lock()


def invalidate(conversation_id: int | None = None) -> None:
    with _lock:
        if conversation_id is None:
            _CACHE.clear()
        else:
            _CACHE.pop(int(conversation_id), None)


def add_chunks(chunk_rows: list[dict], *, document_id: int,
               conversation_id: int, filename: str) -> int:
    """Chunk đã nằm trong SQLite — chỉ cần bỏ chỉ mục cũ để lần tra sau dựng lại."""
    invalidate(conversation_id)
    return len(chunk_rows)


def delete_document(document_id: int, conversation_id: int | None = None) -> None:
    invalidate(conversation_id)


def _index_for(conversation_id: int) -> tuple[list[dict], BM25 | None]:
    with _lock:
        cached = _CACHE.get(conversation_id)
    if cached is not None:
        return cached
    rows = DocumentChunks.list_for_conversation(conversation_id)
    entry = (rows, BM25([r["content"] for r in rows]) if rows else None)
    with _lock:
        _CACHE[conversation_id] = entry
    return entry


def search(query: str, conversation_id: int, top_k: int = ATTACH_TOP_K) -> list[dict]:
    """-> [{chunk_id, content, filename, score}] có điểm > 0, tốt nhất trước."""
    query = (query or "").strip()
    if not query or not conversation_id:
        return []
    rows, index = _index_for(int(conversation_id))
    if index is None:
        return []
    ranked = sorted(zip(rows, index.scores(query)), key=lambda x: -x[1])
    return [{"chunk_id": r["id"], "content": r["content"],
             "filename": r.get("filename", ""), "score": float(s)}
            for r, s in ranked[:top_k] if s > 0]

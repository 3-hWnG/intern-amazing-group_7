"""Tìm web bằng DuckDuckGo cho nút "Tìm web" của Friendly. Không qua bộ dữ liệu; trả về cùng dạng "evidence" như search.py
để chat.py dùng lại chế độ Chuyên gia (ghi [n], hiện nguồn). Phần gọi ddgs dùng chung với Strict: server/core/websearch.py."""
from __future__ import annotations
from core import websearch as core_web

from . import settings


def search(query: str) -> tuple[list[dict], dict]:
    return core_web.search(query, settings.get("WEBSEARCH_RESULTS"), settings.get("WEBSEARCH_TIMEOUT"))

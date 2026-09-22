"""Route chung: giao diện, cấu hình cho frontend, kiểm tra sức khoẻ.

Các nhóm route khác nằm ở auth_routes / chat_routes / file_routes / dev_routes.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from config import (ATTACHMENTS_ENABLED, AUTH_ENABLED, DEFAULT_SYSTEM,
                    DEV_TOOLS_ENABLED, LLM_MODEL, MCP_TRANSPORT,
                    QUEUE_CONCURRENCY, QUEUE_ENABLED, RETRIEVAL_ENABLED,
                    SEARCH_PROVIDER, STATIC_VERSION, SUMMARY_ENABLED,
                    SYSTEM_RETRIEVAL, SYSTEM_WEBSEARCH, TEMPLATES_DIR,
                    VERIFIER_ENABLED)

router = APIRouter()


def render_page(name: str) -> str:
    """Chèn số phiên bản vào đường dẫn static để trình duyệt không dùng JS/CSS cũ."""
    html = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    return html.replace("__V__", STATIC_VERSION)


@router.get("/", response_class=HTMLResponse)
async def get_ui():
    return render_page("index.html")


@router.get("/api/config")
async def public_config():
    """Cấu hình frontend cần biết. KHÔNG lộ thông tin nhạy cảm."""
    return {
        "auth_enabled": AUTH_ENABLED,
        "dev_tools": DEV_TOOLS_ENABLED,
        "queue_enabled": QUEUE_ENABLED,
        "queue_concurrency": QUEUE_CONCURRENCY,
        "summary_enabled": SUMMARY_ENABLED,
        "attachments_enabled": ATTACHMENTS_ENABLED,
        "verifier_enabled": VERIFIER_ENABLED,
        "llm_model": LLM_MODEL,
        # Hai hệ thống trả lời — giao diện dựng nút chuyển từ danh sách này.
        "default_system": DEFAULT_SYSTEM,
        "systems": [
            {"id": SYSTEM_WEBSEARCH, "label": "Web search",
             "description": "Tra cứu trực tiếp từ các trang .gov.vn qua MCP",
             "enabled": True},
            {"id": SYSTEM_RETRIEVAL, "label": "CSDL thủ tục",
             "description": "Tra cứu từ cơ sở dữ liệu thủ tục nội bộ",
             "enabled": RETRIEVAL_ENABLED},
        ],
    }


@router.get("/health")
async def health():
    from core import llm, mcp_client
    return {
        "status": "ok",
        "llm": await asyncio.to_thread(llm.status),
        "model": llm.model_info(),
        "mcp": {**mcp_client.status(), "transport": MCP_TRANSPORT},
        "search_provider": SEARCH_PROVIDER,
        "systems": {SYSTEM_WEBSEARCH: True, SYSTEM_RETRIEVAL: RETRIEVAL_ENABLED},
        "default_system": DEFAULT_SYSTEM,
        "verifier": VERIFIER_ENABLED,
        "auth": AUTH_ENABLED,
        "queue": QUEUE_ENABLED,
        "attachments": ATTACHMENTS_ENABLED,
    }

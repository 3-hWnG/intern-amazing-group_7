"""Route chung: giao diện và kiểm tra sức khoẻ.

Các nhóm route khác nằm ở auth_routes / chat_routes / dev_routes.
"""

from __future__ import annotations

from fastapi import APIRouter

from config import (AUTH_ENABLED, DEV_TOOLS_ENABLED, EMBED_MODEL_NAME,
                    LLM_MODEL_NAME, QUEUE_CONCURRENCY, QUEUE_ENABLED,
                    SUMMARY_ENABLED, TEMPLATES_DIR, USE_LEXICAL, USE_RERANKER)
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def get_ui():
    return (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")


@router.get("/api/config")
async def public_config():
    """Cấu hình frontend cần biết. KHÔNG lộ thông tin nhạy cảm."""
    return {
        "auth_enabled": AUTH_ENABLED,
        "dev_tools": DEV_TOOLS_ENABLED,
        "queue_enabled": QUEUE_ENABLED,
        "queue_concurrency": QUEUE_CONCURRENCY,
        "summary_enabled": SUMMARY_ENABLED,
    }


@router.get("/health")
async def health():
    from domain.records import get_procedures
    return {
        "procedures": len(get_procedures()),
        "embed_model": EMBED_MODEL_NAME,
        "llm": LLM_MODEL_NAME,
        "lexical": USE_LEXICAL,
        "reranker": USE_RERANKER,
        "auth": AUTH_ENABLED,
        "queue": QUEUE_ENABLED,
    }

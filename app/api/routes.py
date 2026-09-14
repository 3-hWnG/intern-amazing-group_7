"""Route chung: giao diện và kiểm tra sức khoẻ.

Các nhóm route khác nằm ở auth_routes / chat_routes / dev_routes.
"""

from __future__ import annotations

from fastapi import APIRouter

from config import (AGENT_MAX_STEPS, AGENT_TOOL_MODE, ANSWER_STYLE,
                    ATTACHMENTS_ENABLED, AUTH_ENABLED, DEV_TOOLS_ENABLED,
                    EMBED_MODEL_NAME, LLM_MODEL_NAME, ORCHESTRATOR,
                    QUEUE_CONCURRENCY, QUEUE_ENABLED, SUMMARY_ENABLED,
                    STATIC_VERSION, TEMPLATES_DIR, USE_LEXICAL, USE_RERANKER)
from fastapi.responses import HTMLResponse

router = APIRouter()


def render_page(name: str) -> str:
    """Chèn số phiên bản vào đường dẫn static.

    Lần chạy thử đầu tiên: trình duyệt dùng lại app.js và styles.css CŨ trong
    cache -> nút đính kèm không phản hồi và ô nhập bị bẹp, dù file trên đĩa đã
    đúng. Log server chỉ thấy đúng một request files.js (file mới tinh), các
    file còn lại không hề được tải lại. Đổi STATIC_VERSION là ép tải lại hết.
    """
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
        "orchestrator": ORCHESTRATOR,
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
        "orchestrator": ORCHESTRATOR,
        "tool_mode": AGENT_TOOL_MODE,
        "max_steps": AGENT_MAX_STEPS,
        "answer_style": ANSWER_STYLE,
        "attachments": ATTACHMENTS_ENABLED,
    }

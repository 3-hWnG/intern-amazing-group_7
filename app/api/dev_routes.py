"""Công cụ phát triển. CHỈ được đăng ký khi DEV_TOOLS_ENABLED = True.

Không đăng ký route = không tồn tại endpoint. Ẩn nút ở giao diện KHÔNG phải
là bảo mật; đây mới là.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

import developer_mode
from api.deps import current_user
from api.schemas import DevToggle, ResetRequest, WebSearchTest
from db import connection
from db.repositories import Conversations, Feedback, Messages, Users

router = APIRouter()

CONFIRM_WORD = "XOA"


# ------------------------------------------------------ chế độ dev ----
@router.get("/api/dev/status")
async def dev_status(user: dict = Depends(current_user)):
    """Mọi công tắc đang ảnh hưởng tới hành vi — xem nhanh, khỏi mở .env."""
    return developer_mode.snapshot()


@router.post("/api/dev/toggle")
async def dev_toggle(body: DevToggle, user: dict = Depends(current_user)):
    value = developer_mode.toggle() if body.enabled is None \
        else developer_mode.set_enabled(body.enabled)
    return {"developer_mode": value}


@router.get("/api/dev/trace")
async def dev_trace(limit: int = 10, user: dict = Depends(current_user)):
    """Vết chạy các lượt gần nhất: ý định, truy vấn MCP, kiểm chứng, thời gian."""
    return {"enabled": developer_mode.enabled(),
            "traces": developer_mode.traces(limit)}


@router.delete("/api/dev/trace")
async def dev_trace_clear(user: dict = Depends(current_user)):
    return {"cleared": developer_mode.clear_traces()}


@router.post("/api/dev/websearch")
async def dev_websearch(body: WebSearchTest, user: dict = Depends(current_user)):
    """Gọi thử công cụ web_search qua MCP và nói THẲNG hỏng ở bước nào."""
    return await connection.run(developer_mode.websearch_check, body.query or "")


@router.get("/api/dev/stats")
async def stats(user: dict = Depends(current_user)):
    return {
        "users": await connection.run(Users.count),
        "conversations": await connection.run(Conversations.count),
        "messages": await connection.run(Messages.count),
        "feedback": await connection.run(Feedback.count),
        "ratings": await connection.run(Feedback.stats),
    }


@router.post("/api/dev/reset")
async def reset(body: ResetRequest, user: dict = Depends(current_user)):
    if body.confirm != CONFIRM_WORD:
        raise HTTPException(status_code=400,
                            detail=f'Phải gõ đúng "{CONFIRM_WORD}" để xác nhận.')

    def _reset_mine():
        for conv in Conversations.list_for(user["id"], limit=10000):
            Conversations.delete(conv["id"], user["id"])

    if body.scope == "my_conversations":
        await connection.run(_reset_mine)
        return {"ok": True, "scope": body.scope}

    if body.scope == "all_conversations":
        def _all():
            conn = connection.get_conn()
            for table in ("feedback", "evidence", "messages", "conversations", "job_log"):
                conn.execute(f"DELETE FROM {table}")
            conn.commit()
        await connection.run(_all)
        return {"ok": True, "scope": body.scope}

    if body.scope == "everything":
        await connection.run(connection.reset_database)
        return {"ok": True, "scope": body.scope, "note": "Đã xoá cả tài khoản. Hãy đăng ký lại."}

    raise HTTPException(status_code=400, detail="scope không hợp lệ.")

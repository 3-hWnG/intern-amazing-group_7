"""Công cụ phát triển. CHỈ được đăng ký khi DEV_TOOLS_ENABLED = True.

Không đăng ký route = không tồn tại endpoint. Ẩn nút ở giao diện KHÔNG phải
là bảo mật; đây mới là.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import current_user
from api.schemas import ResetRequest
from db import connection
from db.repositories import Conversations, Feedback, Messages, Users

router = APIRouter()

CONFIRM_WORD = "XOA"


@router.get("/api/dev/stats")
async def stats(user: dict = Depends(current_user)):
    return {
        "users": await connection.run(Users.count),
        "conversations": await connection.run(Conversations.count),
        "messages": await connection.run(Messages.count),
        "feedback": await connection.run(Feedback.count),
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
            conn.execute("DELETE FROM feedback")
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM conversations")
            conn.execute("DELETE FROM job_log")
            conn.commit()
        await connection.run(_all)
        return {"ok": True, "scope": body.scope}

    if body.scope == "everything":
        await connection.run(connection.reset_database)
        return {"ok": True, "scope": body.scope, "note": "Đã xoá cả tài khoản. Hãy đăng ký lại."}

    raise HTTPException(status_code=400, detail="scope không hợp lệ.")

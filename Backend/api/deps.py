"""Phụ thuộc dùng chung cho các endpoint: lấy người dùng đang đăng nhập."""

from __future__ import annotations

from fastapi import HTTPException, Request

from config import AUTH_COOKIE_NAME, AUTH_ENABLED
from core import auth
from db import connection
from db.repositories import Users


def _dev_user() -> dict:
    """Khi tắt xác thực (AUTH_ENABLED=False) vẫn cần một người dùng để gắn dữ liệu."""
    user = Users.by_email("dev@local")
    if user is None:
        user = Users.create("dev@local", auth.hash_password("dev-no-auth"), "Dev")
    return user


async def current_user(request: Request) -> dict:
    if not AUTH_ENABLED:
        return await connection.run(_dev_user)
    token = request.cookies.get(AUTH_COOKIE_NAME, "")
    user = await connection.run(auth.user_for_token, token)
    if user is None:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập.")
    return user


async def optional_user(request: Request) -> dict | None:
    try:
        return await current_user(request)
    except HTTPException:
        return None

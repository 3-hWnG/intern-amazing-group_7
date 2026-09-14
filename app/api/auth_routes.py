"""Đăng ký / đăng nhập / đăng xuất."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from api.deps import current_user
from api.schemas import Credentials
from api.routes import render_page
from config import AUTH_COOKIE_NAME, AUTH_ENABLED, TEMPLATES_DIR
from core import auth
from db import connection

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return render_page("login.html")


@router.post("/api/register")
async def register(body: Credentials, request: Request):
    if not AUTH_ENABLED:
        return JSONResponse({"error": "Xác thực đang tắt."}, status_code=400)
    try:
        user = await connection.run(auth.register, body.email, body.password, body.display_name)
        _, token = await connection.run(
            auth.login, body.email, body.password, request.headers.get("user-agent", ""))
    except auth.AuthError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    response = JSONResponse({"user": auth.public(user)})
    auth.set_cookie(response, token)
    return response


@router.post("/api/login")
async def login(body: Credentials, request: Request):
    if not AUTH_ENABLED:
        return JSONResponse({"error": "Xác thực đang tắt."}, status_code=400)
    try:
        user, token = await connection.run(
            auth.login, body.email, body.password, request.headers.get("user-agent", ""))
    except auth.AuthError as exc:
        return JSONResponse({"error": str(exc)}, status_code=401)
    response = JSONResponse({"user": auth.public(user)})
    auth.set_cookie(response, token)
    return response


@router.post("/api/logout")
async def logout(request: Request):
    token = request.cookies.get(AUTH_COOKIE_NAME, "")
    if token:
        await connection.run(auth.logout, token)
    response = JSONResponse({"ok": True})
    auth.clear_cookie(response)
    return response


@router.get("/api/me")
async def me(user: dict = Depends(current_user)):
    return {"user": auth.public(user)}

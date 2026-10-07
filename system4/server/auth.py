"""Đăng nhập / đăng ký: mật khẩu băm bcrypt, phiên = cookie ngẫu nhiên (DB chỉ lưu sha256 của cookie)."""
from __future__ import annotations
import hashlib
import re
import secrets

import bcrypt

from . import config, db, settings

COOKIE = "s4_session"
_USERNAME = re.compile(r"^[A-Za-z0-9._-]{3,32}$")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def signup_open() -> bool:
    return settings.get("ALLOW_SIGNUP") or db.count_users() == 0


def check_new_account(username: str, password: str) -> str | None:
    """Trả câu báo lỗi (tiếng Việt) hoặc None nếu hợp lệ."""
    if not _USERNAME.match(username or ""):
        return "Tên đăng nhập 3–32 ký tự, chỉ gồm chữ không dấu, số và . _ -"
    n = settings.get("MIN_PASSWORD_LENGTH")
    if len(password or "") < n:
        return f"Mật khẩu cần ít nhất {n} ký tự"
    if len(password.encode()) > 72:   # giới hạn của bcrypt
        return "Mật khẩu tối đa 72 byte"
    if db.user_by_name(username):
        return "Tên đăng nhập đã có người dùng"
    return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify(username: str, password: str) -> dict | None:
    u = db.user_by_name(username or "")
    pw = (password or "").encode()
    if not u or len(pw) > 72:
        return None
    if not bcrypt.checkpw(pw, u["password_hash"].encode()):
        return None
    return u


def new_session(user_id: int) -> tuple[str, int]:
    """Trả (cookie, số giây sống)."""
    days = settings.get("SESSION_DAYS")
    token = secrets.token_urlsafe(32)
    db.add_session(_hash_token(token), user_id, days)
    return token, days * 86400


def user_from_cookie(token: str | None) -> dict | None:
    return db.session_user(_hash_token(token)) if token else None


def end_session(token: str | None) -> None:
    if token:
        db.delete_session(_hash_token(token))


def set_cookie(resp, token: str, max_age: int) -> None:
    resp.set_cookie(COOKIE, token, max_age=max_age, httponly=True, samesite="lax", secure=config.COOKIE_SECURE, path="/")

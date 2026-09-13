"""Xác thực: băm mật khẩu + phiên đăng nhập bằng cookie.

Dùng cookie phiên thay vì JWT: thu hồi được ngay (xoá một dòng DB), ít mã hơn.
"""

from __future__ import annotations

import re
import secrets

import bcrypt

from config import (AUTH_COOKIE_NAME, AUTH_COOKIE_SECURE, AUTH_LOCKOUT_SECONDS,
                    AUTH_MAX_LOGIN_ATTEMPTS, AUTH_MIN_PASSWORD_LENGTH,
                    AUTH_SESSION_DAYS)
from db.repositories import AuthSessions, LoginAttempts, Users

SESSION_TTL = AUTH_SESSION_DAYS * 24 * 3600
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """Lỗi nghiệp vụ xác thực - thông điệp đã sẵn sàng hiển thị cho người dùng."""


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def validate_credentials(email: str, password: str) -> None:
    if not EMAIL_RE.match((email or "").strip()):
        raise AuthError("Email không hợp lệ.")
    if len(password or "") < AUTH_MIN_PASSWORD_LENGTH:
        raise AuthError(f"Mật khẩu phải từ {AUTH_MIN_PASSWORD_LENGTH} ký tự trở lên.")


def register(email: str, password: str, display_name: str = "") -> dict:
    validate_credentials(email, password)
    if Users.by_email(email):
        raise AuthError("Email này đã được đăng ký.")
    return Users.create(email, hash_password(password), display_name)


def login(email: str, password: str, user_agent: str = "") -> tuple[dict, str]:
    if LoginAttempts.recent_count(email, AUTH_LOCKOUT_SECONDS) >= AUTH_MAX_LOGIN_ATTEMPTS:
        raise AuthError("Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 15 phút.")

    user = Users.by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        LoginAttempts.record(email)
        raise AuthError("Email hoặc mật khẩu không đúng.")

    LoginAttempts.clear(email)
    token = secrets.token_urlsafe(32)
    AuthSessions.create(token, user["id"], SESSION_TTL, user_agent)
    return user, token


def logout(token: str) -> None:
    AuthSessions.delete(token)


def user_for_token(token: str) -> dict | None:
    user = AuthSessions.user_for(token)
    if user:
        AuthSessions.touch(token, SESSION_TTL)   # gia hạn trượt
    return user


def public(user: dict) -> dict:
    """Bản rút gọn an toàn để trả về client - KHÔNG kèm password_hash."""
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "is_admin": bool(user["is_admin"]),
    }


def set_cookie(response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE_NAME, token,
        max_age=SESSION_TTL, httponly=True,
        samesite="lax", secure=AUTH_COOKIE_SECURE, path="/",
    )


def clear_cookie(response) -> None:
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")

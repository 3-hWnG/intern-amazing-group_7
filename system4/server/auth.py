"""Đăng nhập / đăng ký: mật khẩu băm bcrypt, phiên = cookie ngẫu nhiên (DB chỉ lưu sha256 của cookie)."""
from __future__ import annotations
import hashlib
import re
import secrets
import threading
import time

import bcrypt

from . import config, db, settings

COOKIE = "s4_session"
_USERNAME = re.compile(r"^[A-Za-z0-9._@+-]{3,64}$")   # tên đăng nhập hoặc email
_EMAIL = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def signup_open() -> bool:
    return settings.get("ALLOW_SIGNUP") or db.count_users() == 0


def check_new_account(username: str, password: str) -> str | None:
    """Trả câu báo lỗi (tiếng Việt) hoặc None nếu hợp lệ."""
    if not _USERNAME.match(username or ""):
        return "Tên đăng nhập hoặc email: 3–64 ký tự, chỉ gồm chữ không dấu, số và . _ - @ +"
    if "@" in username and not _EMAIL.match(username):
        return "Email chưa đúng dạng (ví dụ: ten@gmail.com)"
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


# G1.5 (P25): chống đoán mật khẩu. Đếm lần đăng nhập SAI theo (tên, IP) trong bộ nhớ tiến trình (khởi động lại thì đếm lại):
# 5 lần sai trong 10 phút -> khoá cặp đó tới khi lần sai cũ nhất ra khỏi cửa sổ (API trả 429 kèm số giây chờ). Không đụng đăng ký.
LOGIN_MAX_FAILS = 5
LOGIN_WINDOW = 600
_fails: dict[tuple[str, str], list[float]] = {}
_fails_lock = threading.Lock()


def _key(username: str, ip: str) -> tuple[str, str]:
    return ((username or "").strip().lower(), ip or "")


def login_wait(username: str, ip: str, now: float | None = None) -> int:
    """Số giây còn phải chờ (0 = được thử)."""
    now = time.time() if now is None else now
    with _fails_lock:
        ts = [t for t in _fails.get(_key(username, ip), []) if now - t < LOGIN_WINDOW]
        if ts:
            _fails[_key(username, ip)] = ts
        else:
            _fails.pop(_key(username, ip), None)
        return int(ts[0] + LOGIN_WINDOW - now) + 1 if len(ts) >= LOGIN_MAX_FAILS else 0


def login_failed(username: str, ip: str, now: float | None = None) -> None:
    with _fails_lock:
        if len(_fails) > 10000:   # chặn phình bộ nhớ khi bị dò hàng loạt: bỏ các cặp cũ
            cut = (time.time() if now is None else now) - LOGIN_WINDOW
            for k in [k for k, v in _fails.items() if not v or v[-1] < cut]:
                _fails.pop(k, None)
        _fails.setdefault(_key(username, ip), []).append(time.time() if now is None else now)


def login_ok(username: str, ip: str) -> None:
    with _fails_lock:
        _fails.pop(_key(username, ip), None)


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

"""Khách: dùng thử trò chuyện không cần đăng nhập, bị giới hạn chặt hơn tài khoản (ratelimit.py).

Không có dòng nào về khách trong DB:
  - Danh tính khách = cookie `s4_guest` ký HMAC (mã khách ngẫu nhiên + lúc tạo). Khoá ký sinh mới mỗi lần khởi động server,
    nên tắt server là mọi cookie khách cũ hết hiệu lực, cùng lúc với hội thoại khách trong RAM.
  - Hội thoại của khách (Friendly lẫn Strict) chạy ĐÚNG pipeline như tài khoản, chỉ khác chỗ lưu: trong lượt của khách,
    db.conn() (System 4) và store.conn() (System 3) trả kết nối tới một SQLite trong RAM. DB thật được gắn kèm
    (ATTACH ... AS real) để vẫn đọc lĩnh vực / bộ dữ liệu / thủ tục; SQLite tìm bảng trong main (RAM) trước rồi mới tới DB gắn
    kèm, nên SQL có sẵn không phải sửa. Bảng trong RAM chỉ là các bảng hội thoại (S4_TABLES, S3_TABLES).
  - Hội thoại khách bị xoá sau KEEP_HOURS hoặc khi tắt server.
Khách chỉ gọi được các API trong _ALLOWED (trò chuyện, xem / đổi tên / xoá hội thoại của mình, xem nguồn trích dẫn);
tải dữ liệu, 👍/👎, bộ nhớ, tài khoản, cài đặt, bảng điều khiển thì không.
"""
from __future__ import annotations
import contextvars
import hashlib
import hmac
import re
import secrets
import sqlite3
import threading
import time

from . import config, db, settings

COOKIE = "s4_guest"
KEEP_HOURS = 24
DENIED = "Khách không dùng được chức năng này. Đăng nhập hoặc đăng ký (miễn phí) để dùng đầy đủ."
INTERNAL = secrets.token_urlsafe(24)   # header X-S4-Internal: cầu nối Strict gọi /chat của System 3 trong tiến trình (không đếm 2 lần)
_SECRET = secrets.token_bytes(32)
_current: contextvars.ContextVar[str | None] = contextvars.ContextVar("s4_guest", default=None)

# Bảng hội thoại chuyển sang RAM trong lượt của khách. Bảng khác (lĩnh vực, bộ dữ liệu, feedback_log, thống kê thủ tục…) đọc từ DB thật.
S4_TABLES = {"conversations", "messages", "memories", "user_prefs", "traces", "domain_pins",
             "strict_owner", "strict_nodes", "strict_threads", "strict_branch"}
S3_TABLES = {"conversations", "messages", "session_facts", "shown_procedures", "turn_traces", "conv_state", "user_memory"}
_ID_BASE = 10 ** 12   # id tự tăng trong RAM bắt đầu từ đây: không trùng id thật

_ALLOWED = [(set(m.split("|")), re.compile(p + r"\Z")) for m, p in (
    ("GET", r"/"),
    ("GET", r"/s4/auth/me"),
    ("GET", r"/s4/domains"),
    ("GET", r"/s4/datasets"),                                    # chỉ xem danh sách (huy hiệu "Chuyên gia · n bộ dữ liệu")
    ("GET", r"/s4/records/\d+"),                                 # nguồn trích dẫn [n]
    ("GET", r"/s4/trace/\d+"),                                   # "Vì sao?" (bản rút gọn, câu của mình)
    ("GET|DELETE", r"/s4/conversations"),
    ("POST", r"/s4/chat"),
    ("GET", r"/s4/conversations/[^/]+/(messages|export)"),
    ("POST", r"/s4/conversations/[^/]+/switch"),
    ("PATCH|DELETE", r"/s4/conversations/[^/]+"),
    ("POST", r"/s4/strict/chat"),
    ("GET", r"/s4/strict/[^/]+/(messages|export)"),
    ("POST", r"/s4/strict/[^/]+/(edit|regenerate|switch|reset)"),
    ("DELETE", r"/s4/strict/[^/]+"),
    ("GET", r"/config"),                                         # huy hiệu "AI: …" của Strict
    ("GET", r"/procedure/[^/]+/table"),                          # bảng chi tiết thủ tục trong câu trả lời Strict
    ("POST", r"/chat"),                                          # System 3 (qua cầu nối Strict)
    ("PATCH", r"/conversations/[^/]+"),                          # đổi tên / ghim hội thoại Strict
    ("POST", r"/conversations/[^/]+/reset_facts"),               # "Chủ đề mới" (qua cầu nối Strict)
)]


def enabled() -> bool:
    return bool(settings.get("GUEST_ENABLED"))


def allowed(method: str, path: str) -> bool:
    return any(method in ms and rx.match(path) for ms, rx in _ALLOWED)


# ------------------------------------------------------------------ cookie
def _sign(payload: str) -> str:
    return hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()[:32]


def new_token(now: float | None = None) -> str:
    payload = f"{secrets.token_urlsafe(12)}.{int(time.time() if now is None else now)}"   # token_urlsafe không có dấu "."
    return f"{payload}.{_sign(payload)}"


def user_from_cookie(token: str | None, now: float | None = None) -> dict | None:
    """Khách hợp lệ -> dict giống tài khoản (id âm, role 'guest'); cookie sai chữ ký / quá KEEP_HOURS / chế độ khách tắt -> None."""
    if not token or not enabled():
        return None
    parts = token.split(".")
    if len(parts) != 3 or not parts[1].isdigit() or not hmac.compare_digest(parts[2], _sign(f"{parts[0]}.{parts[1]}")):
        return None
    if (time.time() if now is None else now) - int(parts[1]) > KEEP_HOURS * 3600:
        return None
    uid = -(int.from_bytes(hashlib.sha256(parts[0].encode()).digest()[:6], "big") + 1)   # âm: không trùng tài khoản thật
    return {"id": uid, "username": "Khách", "role": "guest", "guest": parts[0]}


def set_cookie(resp, token: str) -> None:
    resp.set_cookie(COOKIE, token, max_age=KEEP_HOURS * 3600, httponly=True, samesite="lax", secure=config.COOKIE_SECURE, path="/")


# ----------------------------------------------------- lượt của khách -> DB RAM
def enter(user: dict):
    """Gọi ở middleware cho mọi yêu cầu của khách; trả token để leave(). Việc chạy sau đó (kể cả luồng SSE, asyncio.to_thread,
    lời gọi nội bộ của cầu nối Strict) mang theo context này."""
    return _current.set(user["guest"])


def leave(token) -> None:
    _current.reset(token)


def active() -> bool:
    return _current.get() is not None


_FK = re.compile(r"\s+REFERENCES\s+(\w+)\s*\([^)]*\)(?:\s+ON\s+(?:DELETE|UPDATE)\s+(?:SET\s+NULL|SET\s+DEFAULT|CASCADE|RESTRICT|NO\s+ACTION))*",
                 re.I)


class _Ram:
    """Một SQLite trong RAM (main) + DB thật gắn kèm (real). Một kết nối dùng chung, mỗi lần mượn giữ khoá tới close()."""

    def __init__(self, real_path, tables: set[str]):
        c = sqlite3.connect(":memory:", timeout=5, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")   # trước mọi lệnh ghi: trong giao dịch thì PRAGMA này không có tác dụng
        c.execute("ATTACH DATABASE ? AS real", (str(real_path),))
        rows = c.execute("SELECT type, tbl_name, sql FROM real.sqlite_master WHERE sql IS NOT NULL AND type IN ('table','index') "
                         "ORDER BY type DESC").fetchall()   # bảng trước, chỉ mục sau
        for r in rows:
            if r["tbl_name"] in tables:   # khoá ngoại tới bảng không nằm trong RAM (users, datasets…) thì bỏ
                c.execute(_FK.sub(lambda m: m.group(0) if m.group(1) in tables else "", r["sql"]))
                if r["type"] == "table" and "AUTOINCREMENT" in r["sql"].upper():
                    c.execute("INSERT INTO sqlite_sequence(name, seq) VALUES (?, ?)", (r["tbl_name"], _ID_BASE))
        c.commit()
        self.c, self.lock = c, threading.RLock()

    def conn(self) -> "_Conn":
        self.lock.acquire()
        return _Conn(self)


class _Conn:
    """Kết nối mượn: dùng như sqlite3.Connection; close() trả khoá (code gọi db.conn() / store.conn() luôn đóng trong finally)."""

    def __init__(self, ram: _Ram):
        self._ram, self._open = ram, True

    def __getattr__(self, name):
        return getattr(self._ram.c, name)

    def close(self) -> None:
        if self._open:
            self._open = False
            try:
                self._ram.c.rollback()   # lệnh dở vì lỗi giữa chừng không dính sang người mượn sau
            finally:
                self._ram.lock.release()

    __del__ = close


_rams: dict[str, _Ram] = {}
_rams_lock = threading.Lock()


def _ram(name: str, real_path, tables: set[str]) -> _Ram:
    with _rams_lock:
        if name not in _rams:
            _rams[name] = _Ram(real_path, tables)
        return _rams[name]


def install(s3_store) -> None:
    """Đổi chỗ lưu hội thoại sang RAM trong lượt của khách: db.conn() của System 4 (qua móc db.GUEST_CONN) và store.conn() của
    System 3 (gán lại hàm của module, code System 3 giữ nguyên — như các *_PROVIDER khác trong hook.py)."""
    db.GUEST_CONN = lambda: _ram("s4", config.DB_PATH, S4_TABLES).conn() if active() else None
    original = s3_store.conn
    s3_store.conn = lambda: _ram("s3", s3_store.DB_PATH, S3_TABLES).conn() if active() else original()
    # System 3 chạy lượt /chat trong worker của hàng đợi (tạo lúc khởi động, không mang context của request): job mang theo context
    # của người gửi, để lượt của khách vẫn ghi vào RAM
    from core import queue as s3_queue
    submit = s3_queue.manager.submit
    if not getattr(submit, "_ctx", False):

        def submit_ctx(producer):
            ctx = contextvars.copy_context()
            return submit(lambda emit: ctx.run(producer, emit))
        submit_ctx._ctx = True
        s3_queue.manager.submit = submit_ctx


def reset() -> None:
    """Bỏ toàn bộ dữ liệu khách trong RAM (test)."""
    with _rams_lock:
        for r in _rams.values():
            with r.lock:
                r.c.close()
        _rams.clear()


_last_sweep = [0.0]


def sweep(force: bool = False) -> None:
    """Xoá hội thoại khách quá KEEP_HOURS (cookie khách cũng hết hạn sau chừng đó). Middleware gọi, tối đa 10 phút một lần."""
    if not force and time.time() - _last_sweep[0] < 600:
        return
    _last_sweep[0] = time.time()
    cut = (f"-{KEEP_HOURS} hours",)
    live = None
    for name in ("s3", "s4"):
        r = _rams.get(name)
        if not r:
            continue
        with r.lock:
            for t in sorted(S3_TABLES if name == "s3" else S4_TABLES):
                cols = {x[1] for x in r.c.execute(f"PRAGMA main.table_info({t})")}
                stamp = "created_at" if "created_at" in cols else "updated_at" if "updated_at" in cols else None
                if stamp:
                    r.c.execute(f"DELETE FROM main.{t} WHERE {stamp} < datetime('now', ?)", cut)
            if name == "s3":
                live = [x[0] for x in r.c.execute("SELECT id FROM main.conversations")]
            elif live is not None:   # hội thoại Strict: cây tin nhắn (System 4) theo hội thoại System 3 còn sống
                r.c.execute("CREATE TEMP TABLE IF NOT EXISTS live(id TEXT PRIMARY KEY)")
                r.c.execute("DELETE FROM temp.live")
                r.c.executemany("INSERT INTO temp.live(id) VALUES (?)", [(i,) for i in live])
                r.c.execute("DELETE FROM main.strict_owner WHERE conversation_id NOT IN (SELECT id FROM temp.live)")
                r.c.execute("DELETE FROM main.strict_branch WHERE cid NOT IN (SELECT id FROM temp.live)")
                r.c.execute("DELETE FROM main.strict_threads WHERE root NOT IN (SELECT id FROM temp.live)")
                r.c.execute("DELETE FROM main.strict_nodes WHERE root NOT IN (SELECT id FROM temp.live)")
            r.c.commit()

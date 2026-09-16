"""Kết nối SQLite. Đây là nơi DUY NHẤT mở database.

Dùng sqlite3 của thư viện chuẩn - không thêm phụ thuộc. Mọi câu SQL nằm ở
repositories.py nên muốn đổi sang PostgreSQL chỉ phải viết lại một file.
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from pathlib import Path

from config import DB_PATH

_local = threading.local()
_init_lock = threading.Lock()
_initialised = False

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _configure(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    """Tạo bảng nếu chưa có. Gọi một lần lúc khởi động."""
    global _initialised
    with _init_lock:
        if _initialised:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = _configure(sqlite3.connect(str(DB_PATH)))
        try:
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            # Migration đơn giản: CREATE TABLE IF NOT EXISTS không thêm cột mới
            # vào bảng đã tồn tại, nên phải ALTER thủ công.
            for table, column, ddl in [
                ("messages", "kind", "TEXT DEFAULT ''"),
                ("messages", "verdict", "TEXT DEFAULT ''"),
                ("messages", "intent_json", "TEXT DEFAULT ''"),
            ]:
                cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
                if column not in cols:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            # v7 bỏ dataset nội bộ: xoá bản đăng ký "tri thức chung" cũ nếu còn.
            conn.execute("DELETE FROM documents WHERE scope = 'global'")
            conn.commit()
        finally:
            conn.close()
        _initialised = True


def get_conn() -> sqlite3.Connection:
    """Mỗi luồng một kết nối riêng (sqlite3 không chia sẻ được giữa luồng)."""
    init_db()
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _configure(sqlite3.connect(str(DB_PATH), check_same_thread=False))
        _local.conn = conn
    return conn


async def run(fn, *args, **kwargs):
    """Chạy hàm DB đồng bộ trong luồng riêng để không chặn vòng lặp async."""
    return await asyncio.to_thread(fn, *args, **kwargs)


def reset_database() -> None:
    """Xoá toàn bộ dữ liệu, giữ lược đồ. Chỉ dùng cho công cụ phát triển."""
    conn = get_conn()
    for table in ["feedback", "evidence", "messages", "document_chunks", "documents",
                  "conversations", "user_profile", "auth_sessions", "login_attempts",
                  "job_log", "users"]:
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DELETE FROM sqlite_sequence")
    conn.commit()

"""SQLite của System 4 (stdlib). Mỗi lệnh một kết nối ngắn, giống System 3."""
from __future__ import annotations
import sqlite3
import uuid

from . import config

NEW_TITLE = "Cuộc trò chuyện mới"


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(config.DB_PATH), timeout=5)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db() -> None:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = conn()
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(config.SCHEMA_PATH.read_text(encoding="utf-8"))
    c.commit()
    c.close()


def run(sql: str, args=(), one=False, many=False):
    c = conn()
    try:
        cur = c.execute(sql, args)
        c.commit()
        if one:
            r = cur.fetchone()
            return dict(r) if r else None
        if many:
            return [dict(r) for r in cur.fetchall()]
        return cur.lastrowid
    finally:
        c.close()


# ---------------------------------------------------------------- người dùng
def count_users() -> int:
    return run("SELECT COUNT(*) n FROM users", one=True)["n"]


def create_user(username: str, password_hash: str) -> dict:
    """Tài khoản đầu tiên là dev. Kiểm và chèn trong một giao dịch để hai người đăng ký cùng lúc không cùng thành dev."""
    c = conn()
    try:
        c.execute("BEGIN IMMEDIATE")
        role = "dev" if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0 else "user"
        cur = c.execute("INSERT INTO users(username,password_hash,role) VALUES (?,?,?)", (username, password_hash, role))
        c.commit()
        return {"id": cur.lastrowid, "username": username, "role": role}
    finally:
        c.close()


def user_by_name(username: str) -> dict | None:
    return run("SELECT * FROM users WHERE username=?", (username,), one=True)


def first_dev_id() -> int | None:
    r = run("SELECT MIN(id) id FROM users WHERE role='dev'", one=True)
    return r["id"] if r else None


# -------------------------------------------------------------------- phiên
def add_session(token_hash: str, user_id: int, days: int) -> None:
    run("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES (?,?,datetime('now',?))",
        (token_hash, user_id, f"+{int(days)} days"))


def session_user(token_hash: str) -> dict | None:
    return run("SELECT u.id,u.username,u.role FROM sessions s JOIN users u ON u.id=s.user_id "
               "WHERE s.token_hash=? AND s.expires_at>datetime('now') AND u.disabled=0", (token_hash,), one=True)


def delete_session(token_hash: str) -> None:
    run("DELETE FROM sessions WHERE token_hash=?", (token_hash,))
    run("DELETE FROM sessions WHERE expires_at<=datetime('now')")


# --------------------------------------------------- chủ sở hữu hội thoại Strict
def snapshot_legacy(conversation_ids: list[str]) -> None:
    """Chạy MỘT lần: ghi lại các hội thoại Strict có từ trước khi có đăng nhập."""
    if run("SELECT 1 FROM meta WHERE k='legacy_done'", one=True):
        return
    c = conn()
    try:
        c.executemany("INSERT OR IGNORE INTO strict_legacy(conversation_id) VALUES (?)",
                      [(i,) for i in conversation_ids])
        c.execute("INSERT OR REPLACE INTO meta(k,v) VALUES ('legacy_done', datetime('now'))")
        c.commit()
    finally:
        c.close()


def strict_owner(cid: str) -> int | None:
    r = run("SELECT user_id FROM strict_owner WHERE conversation_id=?", (cid,), one=True)
    if r:
        return r["user_id"]
    if run("SELECT 1 FROM strict_legacy WHERE conversation_id=?", (cid,), one=True):
        return first_dev_id()
    return None   # hội thoại mồ côi (vd. lượt /chat lỗi giữa chừng): không ai thấy


def strict_ids(user_id: int) -> set[str]:
    """Mọi hội thoại Strict của một người (2 câu SQL, không hỏi từng hội thoại)."""
    own = {r["conversation_id"] for r in run("SELECT conversation_id FROM strict_owner WHERE user_id=?", (user_id,), many=True)}
    if user_id == first_dev_id():
        own |= {r["conversation_id"] for r in run(
            "SELECT conversation_id FROM strict_legacy WHERE conversation_id NOT IN (SELECT conversation_id FROM strict_owner)",
            many=True)}
    return own


def set_strict_owner(cid: str, user_id: int) -> None:
    run("INSERT OR IGNORE INTO strict_owner(conversation_id,user_id) VALUES (?,?)", (cid, user_id))


def forget_strict(cid: str) -> None:
    run("DELETE FROM strict_owner WHERE conversation_id=?", (cid,))
    run("DELETE FROM strict_legacy WHERE conversation_id=?", (cid,))


# ------------------------------------------------------ hội thoại Friendly
def friendly_owner(cid: str) -> int | None:
    r = run("SELECT user_id FROM conversations WHERE id=?", (cid,), one=True)
    return r["user_id"] if r else None


def create_conversation(user_id: int) -> str:
    cid = uuid.uuid4().hex
    run("INSERT INTO conversations(id,user_id) VALUES (?,?)", (cid, user_id))
    return cid


def list_conversations(user_id: int) -> list[dict]:
    return run("SELECT id,title,created_at,pinned FROM conversations WHERE user_id=? "
               "ORDER BY pinned DESC, rowid DESC", (user_id,), many=True)


def get_conversation(cid: str) -> dict | None:
    return run("SELECT id,title,created_at,pinned FROM conversations WHERE id=?", (cid,), one=True)


def rename_conversation(cid: str, title: str) -> None:
    run("UPDATE conversations SET title=? WHERE id=?", (title.strip()[:60] or NEW_TITLE, cid))


def set_pinned(cid: str, pinned: bool) -> None:
    run("UPDATE conversations SET pinned=? WHERE id=?", (1 if pinned else 0, cid))


def set_title_if_new(cid: str, text: str) -> None:
    run("UPDATE conversations SET title=? WHERE id=? AND title=?", (text.strip()[:60] or NEW_TITLE, cid, NEW_TITLE))


def delete_conversation(cid: str) -> None:
    run("DELETE FROM conversations WHERE id=?", (cid,))


def add_message(cid: str, role: str, content: str, status: str = "done") -> int:
    return run("INSERT INTO messages(conversation_id,role,content,status) VALUES (?,?,?,?)", (cid, role, content, status))


def get_messages(cid: str) -> list[dict]:
    return run("SELECT id,role,content,status,created_at FROM messages WHERE conversation_id=? ORDER BY id",
               (cid,), many=True)

"""TOÀN BỘ câu SQL của hệ thống nằm ở đây.

Đổi sang PostgreSQL sau này = viết lại đúng một file này.
Phần còn lại của ứng dụng chỉ gọi hàm, không biết gì về SQL.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from db.connection import get_conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _in(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat(timespec="seconds")


def _row(r):
    return dict(r) if r is not None else None


# ---------------------------------------------------------------- users ----
class Users:
    @staticmethod
    def create(email: str, password_hash: str, display_name: str = "") -> dict:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO users(email, password_hash, display_name, created_at) VALUES (?,?,?,?)",
            (email.lower().strip(), password_hash, display_name or email.split("@")[0], _now()),
        )
        conn.commit()
        return Users.by_id(cur.lastrowid)

    @staticmethod
    def by_email(email: str) -> dict | None:
        return _row(get_conn().execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone())

    @staticmethod
    def by_id(user_id: int) -> dict | None:
        return _row(get_conn().execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    @staticmethod
    def count() -> int:
        return get_conn().execute("SELECT COUNT(*) c FROM users").fetchone()["c"]


# ------------------------------------------------------- auth sessions ----
class AuthSessions:
    @staticmethod
    def create(token: str, user_id: int, ttl_seconds: int, user_agent: str = "") -> None:
        conn = get_conn()
        conn.execute(
            "INSERT INTO auth_sessions(token, user_id, created_at, expires_at, user_agent)"
            " VALUES (?,?,?,?,?)",
            (token, user_id, _now(), _in(ttl_seconds), (user_agent or "")[:200]),
        )
        conn.commit()

    @staticmethod
    def user_for(token: str) -> dict | None:
        if not token:
            return None
        row = get_conn().execute(
            "SELECT u.* FROM auth_sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token = ? AND s.expires_at > ?", (token, _now())).fetchone()
        return _row(row)

    @staticmethod
    def touch(token: str, ttl_seconds: int) -> None:
        conn = get_conn()
        conn.execute("UPDATE auth_sessions SET expires_at = ? WHERE token = ?",
                     (_in(ttl_seconds), token))
        conn.commit()

    @staticmethod
    def delete(token: str) -> None:
        conn = get_conn()
        conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        conn.commit()

    @staticmethod
    def purge_expired() -> None:
        conn = get_conn()
        conn.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (_now(),))
        conn.commit()


class LoginAttempts:
    @staticmethod
    def record(email: str) -> None:
        conn = get_conn()
        conn.execute("INSERT INTO login_attempts(email, attempt_at) VALUES (?,?)",
                     (email.lower().strip(), _now()))
        conn.commit()

    @staticmethod
    def recent_count(email: str, window_seconds: int) -> int:
        since = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).isoformat(timespec="seconds")
        return get_conn().execute(
            "SELECT COUNT(*) c FROM login_attempts WHERE email = ? AND attempt_at > ?",
            (email.lower().strip(), since)).fetchone()["c"]

    @staticmethod
    def clear(email: str) -> None:
        conn = get_conn()
        conn.execute("DELETE FROM login_attempts WHERE email = ?", (email.lower().strip(),))
        conn.commit()


# -------------------------------------------------------- conversations ----
class Conversations:
    @staticmethod
    def create(user_id: int, title: str = "Cuộc trò chuyện mới") -> dict:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO conversations(user_id, title, created_at, updated_at) VALUES (?,?,?,?)",
            (user_id, title, _now(), _now()))
        conn.commit()
        return Conversations.by_id(cur.lastrowid)

    @staticmethod
    def by_id(conv_id: int) -> dict | None:
        return _row(get_conn().execute(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone())

    @staticmethod
    def owned_by(conv_id: int, user_id: int) -> dict | None:
        """Luôn dùng hàm này thay cho by_id ở các endpoint — chặn xem chéo người dùng."""
        return _row(get_conn().execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ? AND archived = 0",
            (conv_id, user_id)).fetchone())

    @staticmethod
    def list_for(user_id: int, limit: int = 100) -> list[dict]:
        rows = get_conn().execute(
            "SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) n_messages"
            " FROM conversations c WHERE c.user_id = ? AND c.archived = 0"
            " ORDER BY c.updated_at DESC LIMIT ?", (user_id, limit)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def rename(conv_id: int, user_id: int, title: str) -> None:
        conn = get_conn()
        conn.execute("UPDATE conversations SET title = ?, updated_at = ?"
                     " WHERE id = ? AND user_id = ?",
                     (title[:120], _now(), conv_id, user_id))
        conn.commit()

    @staticmethod
    def touch(conv_id: int) -> None:
        conn = get_conn()
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (_now(), conv_id))
        conn.commit()

    @staticmethod
    def delete(conv_id: int, user_id: int) -> None:
        conn = get_conn()
        conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        conn.commit()

    @staticmethod
    def set_summary(conv_id: int, summary: str, upto_message_id: int) -> None:
        conn = get_conn()
        conn.execute("UPDATE conversations SET summary = ?, summary_upto = ? WHERE id = ?",
                     (summary, upto_message_id, conv_id))
        conn.commit()

    @staticmethod
    def set_pending(conv_id: int, payload: dict | None) -> None:
        conn = get_conn()
        conn.execute("UPDATE conversations SET pending_json = ? WHERE id = ?",
                     (json.dumps(payload, ensure_ascii=False) if payload else "", conv_id))
        conn.commit()

    @staticmethod
    def take_pending(conv_id: int) -> dict | None:
        row = get_conn().execute(
            "SELECT pending_json FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if not row or not row["pending_json"]:
            return None
        Conversations.set_pending(conv_id, None)
        try:
            return json.loads(row["pending_json"])
        except Exception:
            return None

    @staticmethod
    def set_last_row(conv_id: int, row_id: int) -> None:
        conn = get_conn()
        conn.execute("UPDATE conversations SET last_row_id = ? WHERE id = ?",
                     (int(row_id), conv_id))
        conn.commit()

    @staticmethod
    def last_procedure_title(conv_id: int) -> str:
        """Tên thủ tục vừa nói tới - dùng làm ngữ cảnh cho câu hỏi ngắn tiếp theo."""
        row = get_conn().execute(
            "SELECT last_row_id FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if not row or row["last_row_id"] is None or row["last_row_id"] < 0:
            return ""
        from domain.records import by_row_id
        rec = by_row_id().get(int(row["last_row_id"]))
        return rec.ten if rec else ""

    @staticmethod
    def count() -> int:
        return get_conn().execute("SELECT COUNT(*) c FROM conversations").fetchone()["c"]


# ------------------------------------------------------------- messages ----
class Messages:
    @staticmethod
    def add(conversation_id: int, role: str, content: str, *, tier: str = "",
            confidence: float = 0.0, sources=None, factcheck: str = "",
            token_estimate: int = 0) -> int:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO messages(conversation_id, role, content, tier, confidence,"
            " sources, factcheck, token_estimate, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (conversation_id, role, content, tier, float(confidence or 0),
             json.dumps(sources or [], ensure_ascii=False), factcheck,
             int(token_estimate or 0), _now()))
        conn.commit()
        Conversations.touch(conversation_id)
        return cur.lastrowid

    @staticmethod
    def list_for(conversation_id: int, after_id: int = 0) -> list[dict]:
        rows = get_conn().execute(
            "SELECT * FROM messages WHERE conversation_id = ? AND id > ? ORDER BY id",
            (conversation_id, after_id)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def owned_by(message_id: int, user_id: int) -> dict | None:
        row = get_conn().execute(
            "SELECT m.* FROM messages m JOIN conversations c ON c.id = m.conversation_id"
            " WHERE m.id = ? AND c.user_id = ?", (message_id, user_id)).fetchone()
        return _row(row)

    @staticmethod
    def count() -> int:
        return get_conn().execute("SELECT COUNT(*) c FROM messages").fetchone()["c"]


# ------------------------------------------------------------- feedback ----
class Feedback:
    @staticmethod
    def add(message_id: int, user_id: int, verdict: str, note: str = "") -> None:
        conn = get_conn()
        conn.execute("INSERT INTO feedback(message_id, user_id, verdict, note, created_at)"
                     " VALUES (?,?,?,?,?)", (message_id, user_id, verdict, note[:500], _now()))
        conn.commit()

    @staticmethod
    def count() -> int:
        return get_conn().execute("SELECT COUNT(*) c FROM feedback").fetchone()["c"]


# -------------------------------------------------------------- job log ----
class JobLog:
    @staticmethod
    def add(user_id, conversation_id, status, wait_ms, process_ms, position) -> None:
        conn = get_conn()
        conn.execute(
            "INSERT INTO job_log(user_id, conversation_id, status, enqueued_at,"
            " wait_ms, process_ms, queue_position) VALUES (?,?,?,?,?,?,?)",
            (user_id, conversation_id, status, _now(),
             int(wait_ms), int(process_ms), int(position)))
        conn.commit()

    @staticmethod
    def stats() -> dict:
        row = get_conn().execute(
            "SELECT COUNT(*) n, AVG(wait_ms) avg_wait, MAX(wait_ms) max_wait,"
            " AVG(process_ms) avg_process FROM job_log").fetchone()
        return dict(row) if row else {}


# ------------------------------------------------------------ retention ----
def purge_old(retention_days: int) -> int:
    if not retention_days:
        return 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat(timespec="seconds")
    conn = get_conn()
    cur = conn.execute("DELETE FROM conversations WHERE updated_at < ?", (cutoff,))
    conn.commit()
    return cur.rowcount

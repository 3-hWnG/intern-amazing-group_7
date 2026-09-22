"""TOÀN BỘ câu SQL của hệ thống nằm ở đây.

Đổi sang PostgreSQL sau này = viết lại đúng một file này.
Phần còn lại của ứng dụng chỉ gọi hàm, không biết gì về SQL.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from config import DEFAULT_SYSTEM, SYSTEMS
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


# ------------------------------------------------ bộ nhớ dài hạn người dùng ----
class UserProfiles:
    FIELDS = ("province", "ward", "notes")

    @staticmethod
    def get(user_id: int) -> dict:
        row = get_conn().execute(
            "SELECT province, ward, notes, updated_at FROM user_profile WHERE user_id = ?",
            (user_id,)).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def update(user_id: int, **fields) -> dict:
        changes = {k: str(v)[:120] for k, v in fields.items() if k in UserProfiles.FIELDS}
        if not changes:
            return UserProfiles.get(user_id)
        current = UserProfiles.get(user_id)
        merged = {k: current.get(k, "") or "" for k in UserProfiles.FIELDS}
        # đổi tỉnh mà không nói xã/phường -> xã/phường cũ không còn đúng
        if "province" in changes and changes["province"] != merged["province"] \
                and "ward" not in changes:
            merged["ward"] = ""
        merged.update(changes)
        conn = get_conn()
        conn.execute(
            "INSERT INTO user_profile(user_id, province, ward, notes, updated_at)"
            " VALUES (?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET"
            " province = excluded.province, ward = excluded.ward,"
            " notes = excluded.notes, updated_at = excluded.updated_at",
            (user_id, merged["province"], merged["ward"], merged["notes"], _now()))
        conn.commit()
        return UserProfiles.get(user_id)

    @staticmethod
    def clear(user_id: int) -> None:
        conn = get_conn()
        conn.execute("DELETE FROM user_profile WHERE user_id = ?", (user_id,))
        conn.commit()


# -------------------------------------------------------- conversations ----
class Conversations:
    @staticmethod
    def create(user_id: int, title: str = "Cuộc trò chuyện mới",
               system: str = DEFAULT_SYSTEM) -> dict:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO conversations(user_id, title, system, created_at, updated_at)"
            " VALUES (?,?,?,?,?)",
            (user_id, title, system if system in SYSTEMS else DEFAULT_SYSTEM, _now(), _now()))
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
            "SELECT c.id, c.title, c.system, c.created_at, c.updated_at,"
            " (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) n_messages"
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
    def set_system(conv_id: int, user_id: int, system: str) -> None:
        """Đổi hệ thống trả lời. CHỈ gọi khi cuộc trò chuyện chưa có tin nhắn nào —
        đổi giữa chừng sẽ làm mô hình trộn thông tin của hai nguồn khác nhau."""
        if system not in SYSTEMS:
            return
        conn = get_conn()
        conn.execute("UPDATE conversations SET system = ? WHERE id = ? AND user_id = ?",
                     (system, conv_id, user_id))
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
    def count() -> int:
        return get_conn().execute("SELECT COUNT(*) c FROM conversations").fetchone()["c"]


# ------------------------------------------------------------- messages ----
class Messages:
    @staticmethod
    def add(conversation_id: int, role: str, content: str, *, kind: str = "",
            verdict: str = "", sources=None, intent: dict | None = None,
            token_estimate: int = 0) -> int:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO messages(conversation_id, role, content, kind, verdict, sources,"
            " intent_json, token_estimate, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (conversation_id, role, content, kind, verdict,
             json.dumps(sources or [], ensure_ascii=False),
             json.dumps(intent, ensure_ascii=False) if intent else "",
             int(token_estimate or 0), _now()))
        conn.commit()
        Conversations.touch(conversation_id)
        return cur.lastrowid

    @staticmethod
    def list_for(conversation_id: int, after_id: int = 0) -> list[dict]:
        rows = get_conn().execute(
            "SELECT m.id, m.conversation_id, m.role, m.content, m.kind, m.verdict,"
            " m.sources, m.intent_json, m.token_estimate, m.created_at,"
            " EXISTS(SELECT 1 FROM evidence e WHERE e.message_id = m.id) AS has_evidence"
            " FROM messages m WHERE m.conversation_id = ? AND m.id > ? ORDER BY m.id",
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


# ------------------------------------------------------------- evidence ----
class Evidence:
    @staticmethod
    def add(message_id: int, query: str, pack: dict) -> None:
        conn = get_conn()
        conn.execute("INSERT INTO evidence(message_id, query, pack_json, created_at)"
                     " VALUES (?,?,?,?)",
                     (message_id, query or "", json.dumps(pack, ensure_ascii=False), _now()))
        conn.commit()

    @staticmethod
    def for_message(message_id: int, user_id: int) -> dict | None:
        row = get_conn().execute(
            "SELECT e.pack_json FROM evidence e"
            " JOIN messages m ON m.id = e.message_id"
            " JOIN conversations c ON c.id = m.conversation_id"
            " WHERE e.message_id = ? AND c.user_id = ? ORDER BY e.id DESC LIMIT 1",
            (message_id, user_id)).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row["pack_json"])
        except Exception:
            return None


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

    @staticmethod
    def stats() -> dict:
        """Hài lòng / không hài lòng / chưa đánh giá (= trung bình)."""
        row = get_conn().execute(
            "SELECT (SELECT COUNT(*) FROM messages WHERE role = 'assistant') answers,"
            " (SELECT COUNT(DISTINCT message_id) FROM feedback WHERE verdict = 'phu_hop') phu_hop,"
            " (SELECT COUNT(DISTINCT message_id) FROM feedback WHERE verdict = 'khong_phu_hop')"
            " khong_phu_hop").fetchone()
        out = dict(row)
        out["unrated"] = max(0, out["answers"] - out["phu_hop"] - out["khong_phu_hop"])
        return out


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


# ------------------------------------------------------------ tệp đính kèm ----
class Documents:
    @staticmethod
    def create(*, scope: str, filename: str, user_id: int | None = None,
               conversation_id: int | None = None, mime_type: str = "",
               storage_path: str = "", description: str = "",
               n_bytes: int = 0, status: str = "pending") -> dict:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO documents(scope, user_id, conversation_id, filename,"
            " mime_type, storage_path, description, n_bytes, status, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (scope, user_id, conversation_id, filename, mime_type,
             storage_path, description, int(n_bytes or 0), status, _now()))
        conn.commit()
        return Documents.by_id(cur.lastrowid)

    @staticmethod
    def by_id(doc_id: int) -> dict | None:
        return _row(get_conn().execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone())

    @staticmethod
    def owned_by(doc_id: int, user_id: int) -> dict | None:
        return _row(get_conn().execute(
            "SELECT * FROM documents WHERE id = ? AND user_id = ?",
            (doc_id, user_id)).fetchone())

    @staticmethod
    def list_for_conversation(conversation_id: int) -> list[dict]:
        rows = get_conn().execute(
            "SELECT * FROM documents WHERE conversation_id = ? ORDER BY id",
            (conversation_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def set_details(doc_id: int, *, storage_path: str, description: str) -> None:
        conn = get_conn()
        conn.execute("UPDATE documents SET storage_path = ?, description = ? WHERE id = ?",
                     (storage_path, description, doc_id))
        conn.commit()

    @staticmethod
    def mark(doc_id: int, status: str, *, n_chunks: int = 0, error: str = "") -> None:
        conn = get_conn()
        conn.execute("UPDATE documents SET status = ?, n_chunks = ?, error = ?"
                     " WHERE id = ?", (status, int(n_chunks), error[:500], doc_id))
        conn.commit()

    @staticmethod
    def delete(doc_id: int) -> None:
        conn = get_conn()
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()

    @staticmethod
    def count_for_conversation(conversation_id: int) -> int:
        return get_conn().execute(
            "SELECT COUNT(*) c FROM documents WHERE conversation_id = ?",
            (conversation_id,)).fetchone()["c"]


class DocumentChunks:
    @staticmethod
    def add_many(document_id: int, chunks: list[dict]) -> list[int]:
        """chunks: [{"content": str, "metadata": dict}] — trả về danh sách id."""
        conn = get_conn()
        ids = []
        for i, ch in enumerate(chunks):
            cur = conn.execute(
                "INSERT INTO document_chunks(document_id, ordinal, content,"
                " metadata_json, created_at) VALUES (?,?,?,?,?)",
                (document_id, i, ch.get("content", ""),
                 json.dumps(ch.get("metadata") or {}, ensure_ascii=False), _now()))
            ids.append(cur.lastrowid)
        conn.commit()
        return ids

    @staticmethod
    def list_for_conversation(conversation_id: int) -> list[dict]:
        rows = get_conn().execute(
            "SELECT ch.*, d.filename FROM document_chunks ch"
            " JOIN documents d ON d.id = ch.document_id"
            " WHERE d.conversation_id = ? AND d.status = 'processed'"
            " ORDER BY ch.document_id, ch.ordinal", (conversation_id,)).fetchall()
        return [dict(r) for r in rows]

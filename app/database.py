"""database.py — Quản lý CSDL SQLite, Xác thực (Auth), Phiên chat & Tóm tắt ngữ cảnh."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import secrets
import sqlite3
import uuid
import bcrypt
import ollama

from config import (
    CONTEXT_TOKEN_THRESHOLD, LLM_MODEL_NAME, SESSION_EXPIRE_DAYS, SQLITE_DB_PATH
)


_DB_INITIALIZED = False

def get_db_connection() -> sqlite3.Connection:
    global _DB_INITIALIZED
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    if not _DB_INITIALIZED:
        _DB_INITIALIZED = True
        with conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT DEFAULT 'Công dân',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tier TEXT,
                rating INTEGER DEFAULT 0,
                sources TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
            """)
    return conn


def init_db() -> None:
    """Tạo các bảng CSDL cần thiết nếu chưa tồn tại."""
    conn = get_db_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT 'Công dân',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            title TEXT NOT NULL,
            summary TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tier TEXT,
            rating INTEGER DEFAULT 0,
            sources TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
        """)
    conn.close()


# ==============================================================================
# 1. Quản lý Tài khoản & Xác thực (Auth & Bcrypt)
# ==============================================================================
def register_user(email: str, password: str, full_name: str = "Công dân") -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    clean_email = email.strip().lower()
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    now = datetime.now().isoformat()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
            (clean_email, pw_hash, full_name.strip() or "Công dân", now)
        )
        user_id = cur.lastrowid
        conn.commit()
        return {"id": user_id, "email": clean_email, "full_name": full_name, "created_at": now}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    clean_email = email.strip().lower()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, password_hash, full_name, created_at FROM users WHERE email = ?", (clean_email,))
        row = cur.fetchone()
        if not row:
            return None
        if bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            return {"id": row["id"], "email": row["email"], "full_name": row["full_name"], "created_at": row["created_at"]}
        return None
    finally:
        conn.close()


def create_session(user_id: int) -> str:
    conn = get_db_connection()
    token = secrets.token_hex(32)
    now = datetime.now()
    expires = (now + timedelta(days=SESSION_EXPIRE_DAYS)).isoformat()
    try:
        with conn:
            conn.execute(
                "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (token, user_id, expires, now.isoformat())
            )
        return token
    finally:
        conn.close()


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    conn = get_db_connection()
    now = datetime.now().isoformat()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.email, u.full_name, u.created_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ?
        """, (token, now))
        row = cur.fetchone()
        if row:
            return {"id": row["id"], "email": row["email"], "full_name": row["full_name"], "created_at": row["created_at"]}
        return None
    finally:
        conn.close()


def delete_session(token: str) -> None:
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    finally:
        conn.close()


# ==============================================================================
# 2. Quản lý Phiên trò chuyện (Conversations & Messages)
# ==============================================================================
def create_conversation(user_id: Optional[int] = None, title: str = "Cuộc trò chuyện mới") -> Dict[str, Any]:
    conn = get_db_connection()
    conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    try:
        with conn:
            conn.execute(
                "INSERT INTO conversations (id, user_id, title, summary, created_at, updated_at) VALUES (?, ?, ?, '', ?, ?)",
                (conv_id, user_id, title, now, now)
            )
        return {"id": conv_id, "user_id": user_id, "title": title, "created_at": now, "updated_at": now}
    finally:
        conn.close()


def list_conversations(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if user_id is not None:
            cur.execute(
                "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            )
        else:
            cur.execute(
                "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id IS NULL ORDER BY updated_at DESC"
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_conversation(conv_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if user_id is not None:
            cur.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        else:
            cur.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_conversation_title(conv_id: str, title: str) -> None:
    conn = get_db_connection()
    now = datetime.now().isoformat()
    try:
        with conn:
            conn.execute("UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?", (title, now, conv_id))
    finally:
        conn.close()


def delete_conversation(conv_id: str, user_id: Optional[int] = None) -> bool:
    conn = get_db_connection()
    try:
        with conn:
            if user_id is not None:
                cur = conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
            else:
                cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            return cur.rowcount > 0
    finally:
        conn.close()


def save_message(conv_id: str, role: str, content: str, tier: Optional[str] = None, sources: Optional[List[dict]] = None) -> Dict[str, Any]:
    conn = get_db_connection()
    msg_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    sources_str = json.dumps(sources or [], ensure_ascii=False)
    try:
        with conn:
            # Đảm bảo conversation_id tồn tại, tránh lỗi Foreign Key khi hội thoại bị xóa ở frontend
            cur = conn.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
            if not cur.fetchone():
                conn.execute(
                    "INSERT INTO conversations (id, user_id, title, summary, created_at, updated_at) VALUES (?, NULL, 'Cuộc trò chuyện mới', '', ?, ?)",
                    (conv_id, now, now)
                )
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, tier, rating, sources, created_at) "
                "VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
                (msg_id, conv_id, role, content, tier, sources_str, now)
            )
            conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
        return {
            "id": msg_id,
            "conversation_id": conv_id,
            "role": role,
            "content": content,
            "tier": tier,
            "sources": sources or [],
            "created_at": now
        }
    finally:
        conn.close()


def get_messages(conv_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, conversation_id, role, content, tier, rating, sources, created_at FROM messages "
            "WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,)
        )
        msgs = []
        for r in cur.fetchall():
            d = dict(r)
            try:
                d["sources"] = json.loads(d["sources"]) if d["sources"] else []
            except Exception:
                d["sources"] = []
            msgs.append(d)
        return msgs
    finally:
        conn.close()


def rate_message(msg_id: str, rating: int) -> bool:
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute("UPDATE messages SET rating = ? WHERE id = ?", (rating, msg_id))
            return cur.rowcount > 0
    finally:
        conn.close()


# ==============================================================================
# 3. Tự động Tóm tắt Ngữ cảnh (Context Summarizer)
# ==============================================================================
def maybe_summarize_context(conv_id: str) -> None:
    """Tóm tắt lịch sử hội thoại khi vượt ngưỡng ~1800 tokens để bảo vệ context window."""
    messages = get_messages(conv_id)
    if len(messages) < 6:
        return

    # Ước tính token thô (~4 ký tự/token)
    total_chars = sum(len(m["content"]) for m in messages)
    if total_chars < CONTEXT_TOKEN_THRESHOLD * 3.5:
        return

    # Lấy các tin nhắn cũ trừ 4 tin nhắn gần nhất
    old_messages = messages[:-4]
    dialogue_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in old_messages)

    prompt = (
        "Hãy tóm tắt ngắn gọn trong 2-3 câu các thông tin và nhu cầu thủ tục hành chính "
        "mà người dân đã hỏi và được tư vấn trong đoạn hội thoại sau:\n\n"
        f"{dialogue_text}\n\n"
        "TÓM TẮT NGẮN GỌN:"
    )

    try:
        res = ollama.chat(
            model=LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 150, "temperature": 0.2}
        )
        summary = res["message"]["content"].strip()
        conn = get_db_connection()
        with conn:
            conn.execute("UPDATE conversations SET summary = ? WHERE id = ?", (summary, conv_id))
        conn.close()
    except Exception as e:
        print(f"[Summarizer] Không thể tóm tắt: {e}")


# ==============================================================================
# 4. Quản trị Dữ liệu, Reset & Bảo trì (Dev Tools & Retention)
# ==============================================================================
def get_db_stats() -> Dict[str, int]:
    """Lấy thống kê số lượng tài khoản, hội thoại, tin nhắn và phản hồi."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users_cnt = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM conversations")
        conv_cnt = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM messages")
        msg_cnt = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM messages WHERE rating != 0")
        fb_cnt = cur.fetchone()[0]
        return {
            "users": users_cnt,
            "conversations": conv_cnt,
            "messages": msg_cnt,
            "feedback": fb_cnt,
        }
    finally:
        conn.close()


def reset_user_conversations(user_id: Optional[int] = None) -> int:
    """Xóa tất cả cuộc trò chuyện của một người dùng (hoặc khách vãng lai)."""
    conn = get_db_connection()
    try:
        with conn:
            if user_id is not None:
                conn.execute(
                    "DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = ?)",
                    (user_id,)
                )
                cur = conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            else:
                conn.execute(
                    "DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id IS NULL)"
                )
                cur = conn.execute("DELETE FROM conversations WHERE user_id IS NULL")
            return cur.rowcount
    finally:
        conn.close()


def reset_all_conversations() -> None:
    """Xóa toàn bộ cuộc trò chuyện và tin nhắn của mọi người dùng."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM conversations")
    finally:
        conn.close()


def reset_database() -> None:
    """Xóa trắng toàn bộ dữ liệu CSDL (tin nhắn, hội thoại, phiên đăng nhập, tài khoản)."""
    conn = get_db_connection()
    try:
        with conn:
            for table in ["messages", "conversations", "sessions", "users"]:
                conn.execute(f"DELETE FROM {table}")
            conn.execute("DELETE FROM sqlite_sequence")
    finally:
        conn.close()


def purge_old(retention_days: int) -> int:
    """Tự động xóa các cuộc trò chuyện cũ hơn retention_days ngày."""
    if not retention_days or retention_days <= 0:
        return 0
    cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE updated_at < ?)",
                (cutoff,)
            )
            cur = conn.execute("DELETE FROM conversations WHERE updated_at < ?", (cutoff,))
            return cur.rowcount
    finally:
        conn.close()


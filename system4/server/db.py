"""SQLite của System 4 (stdlib). Mỗi lệnh một kết nối ngắn, giống System 3."""
from __future__ import annotations
import json
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
    _migrate(c)
    c.commit()
    c.close()


def _migrate(c: sqlite3.Connection) -> None:
    """DB tạo ở NV1 thiếu cột của NV2: thêm cột, nối các tin cũ thành một chuỗi (mỗi tin trỏ về tin trước)."""
    cols = lambda t: {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
    for col, ddl in (("current_leaf", "INTEGER"), ("summary", "TEXT NOT NULL DEFAULT ''"),
                     ("summary_upto", "INTEGER NOT NULL DEFAULT 0")):
        if col not in cols("conversations"):
            c.execute(f"ALTER TABLE conversations ADD COLUMN {col} {ddl}")
    added = False
    for col, ddl in (("parent_id", "INTEGER"), ("meta", "TEXT NOT NULL DEFAULT '{}'"),
                     ("feedback", "INTEGER NOT NULL DEFAULT 0")):
        if col not in cols("messages"):
            c.execute(f"ALTER TABLE messages ADD COLUMN {col} {ddl}")
            added = True
    if added:
        for (cid,) in c.execute("SELECT id FROM conversations").fetchall():
            ids = [r[0] for r in c.execute("SELECT id FROM messages WHERE conversation_id=? ORDER BY id", (cid,))]
            for prev, cur in zip(ids, ids[1:]):
                c.execute("UPDATE messages SET parent_id=? WHERE id=?", (prev, cur))
            if ids:
                c.execute("UPDATE conversations SET current_leaf=? WHERE id=?", (ids[-1], cid))


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


def _msg(r: dict) -> dict:
    r = dict(r)
    try:
        r["meta"] = json.loads(r.get("meta") or "{}")
    except ValueError:
        r["meta"] = {}
    return r


def add_message(cid: str, role: str, content: str, status: str = "done", parent_id: int | None = None,
                meta: dict | None = None) -> int:
    """Thêm tin vào sau parent_id và đặt nó làm cuối nhánh đang xem."""
    mid = run("INSERT INTO messages(conversation_id,role,content,status,parent_id,meta) VALUES (?,?,?,?,?,?)",
              (cid, role, content, status, parent_id, json.dumps(meta or {}, ensure_ascii=False)))
    run("UPDATE conversations SET current_leaf=? WHERE id=?", (mid, cid))
    return mid


def update_message(mid: int, content: str, status: str, meta: dict) -> None:
    run("UPDATE messages SET content=?, status=?, meta=? WHERE id=?",
        (content, status, json.dumps(meta, ensure_ascii=False), mid))


def get_message(mid: int) -> dict | None:
    r = run("SELECT * FROM messages WHERE id=?", (mid,), one=True)
    return _msg(r) if r else None


def all_messages(cid: str) -> list[dict]:
    return [_msg(r) for r in run(
        "SELECT id,role,content,status,created_at,parent_id,meta,feedback FROM messages WHERE conversation_id=? ORDER BY id",
        (cid,), many=True)]


def current_leaf(cid: str) -> int | None:
    r = run("SELECT current_leaf FROM conversations WHERE id=?", (cid,), one=True)
    return r["current_leaf"] if r else None


def get_path(cid: str) -> list[dict]:
    """Các tin trên nhánh đang xem (từ đầu tới cuối), mỗi tin kèm danh sách phiên bản cùng cha (versions)."""
    msgs = all_messages(cid)
    by_id = {m["id"]: m for m in msgs}
    kids: dict = {}
    for m in msgs:
        kids.setdefault(m["parent_id"], []).append(m["id"])
    leaf = current_leaf(cid)
    if leaf not in by_id:
        leaf = msgs[-1]["id"] if msgs else None
    path = []
    while leaf is not None and leaf in by_id:
        path.append(by_id[leaf])
        leaf = by_id[leaf]["parent_id"]
    path.reverse()
    for m in path:
        m["versions"] = kids.get(m["parent_id"], [m["id"]])
    return path


def deepest_leaf(cid: str, mid: int) -> int:
    """Từ một tin, tới tin mới nhất trong nhánh con của nó (dùng khi chuyển phiên bản ‹ ›): quay về đúng chỗ
    người dùng dừng ở phiên bản đó. Tin con luôn có id lớn hơn tin cha, nên tin id lớn nhất là tin cuối nhánh."""
    msgs = all_messages(cid)
    kids: dict = {}
    for m in msgs:
        kids.setdefault(m["parent_id"], []).append(m["id"])
    best, todo = mid, [mid]
    while todo:
        n = todo.pop()
        best = max(best, n)
        todo.extend(kids.get(n, []))
    return best


def set_leaf(cid: str, mid: int) -> None:
    run("UPDATE conversations SET current_leaf=? WHERE id=?", (mid, cid))


def set_feedback(mid: int, value: int) -> None:
    run("UPDATE messages SET feedback=? WHERE id=?", (value, mid))


def get_summary(cid: str) -> tuple[str, int]:
    r = run("SELECT summary, summary_upto FROM conversations WHERE id=?", (cid,), one=True)
    return (r["summary"], r["summary_upto"]) if r else ("", 0)


def set_summary(cid: str, text: str, upto: int) -> None:
    run("UPDATE conversations SET summary=?, summary_upto=? WHERE id=?", (text, upto, cid))


# ------------------------------------------------------------- bộ nhớ (NV2)
def list_memories(user_id: int) -> list[dict]:
    return run("SELECT id,text,created_at FROM memories WHERE user_id=? ORDER BY id", (user_id,), many=True)


def add_memory(user_id: int, text: str, max_items: int) -> int:
    mid = run("INSERT INTO memories(user_id,text) VALUES (?,?)", (user_id, text))
    run("DELETE FROM memories WHERE user_id=? AND id NOT IN (SELECT id FROM memories WHERE user_id=? ORDER BY id DESC LIMIT ?)",
        (user_id, user_id, max_items))   # quá giới hạn: bỏ điều cũ nhất
    return mid


def delete_memory(user_id: int, mem_id: int | None = None) -> None:
    if mem_id is None:
        run("DELETE FROM memories WHERE user_id=?", (user_id,))
    else:
        run("DELETE FROM memories WHERE user_id=? AND id=?", (user_id, mem_id))


def get_memory_mode(user_id: int) -> str:
    r = run("SELECT memory_mode FROM user_prefs WHERE user_id=?", (user_id,), one=True)
    return r["memory_mode"] if r else ""


def set_memory_mode(user_id: int, mode: str) -> None:
    run("INSERT INTO user_prefs(user_id,memory_mode) VALUES (?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET memory_mode=excluded.memory_mode", (user_id, mode))

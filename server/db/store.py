"""Truy cập SQLite (stdlib). Mỗi lệnh một kết nối ngắn — đủ cho 1 worker."""
from __future__ import annotations
import json
import sqlite3
import uuid

from config import DB_PATH, SCHEMA_PATH


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), timeout=5)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = conn()
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    if "proc_id" not in [r[1] for r in c.execute("PRAGMA table_info(session_facts)")]:   # DB cũ thiếu cột
        c.execute("ALTER TABLE session_facts ADD COLUMN proc_id TEXT NOT NULL DEFAULT ''")
    if "pinned" not in [r[1] for r in c.execute("PRAGMA table_info(conversations)")]:   # DB cũ thiếu cột ghim
        c.execute("ALTER TABLE conversations ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
    c.commit()
    c.close()


def _run(sql: str, args=(), one=False, many=False):
    c = conn()
    try:
        cur = c.execute(sql, args)
        c.commit()
        if one:
            return cur.fetchone()
        if many:
            return cur.fetchall()
        return cur.lastrowid
    finally:
        c.close()


def conversation_exists(cid: str) -> bool:
    return bool(_run("SELECT 1 FROM conversations WHERE id=?", (cid,), one=True))


# FINAL-PRODUCT: [B4] phiên ẩn danh: không có cột chủ sở hữu (conversations không có user_id). Khi có đăng nhập: thêm user_id, lọc mọi truy vấn theo user (mục 3)
def ensure_conversation(cid: str | None) -> str:
    """Session ẩn danh: client không có id (hoặc id lạ) -> cấp id mới."""
    if cid and conversation_exists(cid):
        return cid
    cid = uuid.uuid4().hex
    _run("INSERT INTO conversations(id) VALUES (?)", (cid,))
    return cid


# FINAL-PRODUCT: [B4] không lọc theo người dùng (mục 3)
def list_conversations() -> list[dict]:
    return [dict(r) for r in _run(
        "SELECT id,title,created_at,pinned FROM conversations ORDER BY pinned DESC, rowid DESC", many=True)]


def rename_conversation(cid: str, title: str) -> None:
    _run("UPDATE conversations SET title=? WHERE id=?", (title.strip()[:60] or "Cuộc trò chuyện mới", cid))


def set_pinned(cid: str, pinned: bool) -> None:
    _run("UPDATE conversations SET pinned=? WHERE id=?", (1 if pinned else 0, cid))


# FINAL-PRODUCT: [B4] cid=None xoá TẤT CẢ hộp thoại của mọi người; bản cuối nhận user_id và chỉ xoá của người đó (mục 3)
def delete_conversation(cid: str | None = None) -> None:
    """cid=None: xoá tất cả. Bảng con xoá theo ON DELETE CASCADE (foreign_keys=ON ở conn())."""
    if cid is None:
        _run("DELETE FROM conversations")
    else:
        _run("DELETE FROM conversations WHERE id=?", (cid,))


def set_title_if_new(cid: str, text: str) -> None:
    _run("UPDATE conversations SET title=? WHERE id=? AND title='Cuộc trò chuyện mới'",
         (text.strip()[:60] or "Cuộc trò chuyện mới", cid))


# FINAL-PRODUCT: [B3] content (nguyên văn người dùng) và plan_json chưa che CCCD/SĐT; che bằng policy.mask_pii trước khi ghi, hoặc ghi bản che + bản mã hoá có hạn dùng (mục 2)
def add_message(cid: str, role: str, content: str, kind: str = "",
                plan: dict | None = None, payload: dict | None = None) -> int:
    return _run(
        "INSERT INTO messages(conversation_id,role,content,kind,plan_json,sources_json) VALUES (?,?,?,?,?,?)",
        (cid, role, content, kind,
         json.dumps(plan, ensure_ascii=False) if plan else "",
         json.dumps(payload, ensure_ascii=False) if payload else ""))


# FINAL-PRODUCT: [B2] trả cả plan; bản cuối chỉ đưa plan cho dev (mục 1)
def get_messages(cid: str) -> list[dict]:
    out = []
    for r in _run("SELECT * FROM messages WHERE conversation_id=? ORDER BY id", (cid,), many=True):
        d = dict(r)
        payload = json.loads(d.pop("sources_json") or "{}")
        d["blocks"] = payload.get("blocks", [])
        d["clarify"] = payload.get("clarify")
        d["plan"] = json.loads(d.pop("plan_json") or "null")
        out.append(d)
    return out


def recent_history(cid: str, turns: int = 5) -> list[dict]:
    """turns lượt gần nhất (user+assistant), cũ -> mới. Gọi TRƯỚC khi lưu tin mới."""
    rows = _run("SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?",
                (cid, turns * 2), many=True)
    return [dict(r) for r in reversed(rows)]


# FINAL-PRODUCT: [B2][B3] trace_json chứa câu hỏi (đã mask_pii ở orchestrator) và plan_json nội bộ; chỉ dev được đọc, và đặt hạn xoá (mục 1, 2)
def add_trace(cid: str, message_id: int, trace: dict, total_ms: int) -> None:
    _run("INSERT OR REPLACE INTO turn_traces VALUES (?,?,?,?)",
         (cid, message_id, json.dumps(trace, ensure_ascii=False), total_ms))


def get_trace(cid: str, message_id: int) -> dict | None:
    r = _run("SELECT trace_json,total_ms FROM turn_traces WHERE conversation_id=? AND message_id=?",
             (cid, message_id), one=True)
    return {"trace": json.loads(r["trace_json"]), "total_ms": r["total_ms"]} if r else None


def session_facts(cid: str) -> list[dict]:
    return [dict(r) for r in _run(
        "SELECT kind,text,proc_id FROM session_facts WHERE conversation_id=?", (cid,), many=True)]


# FINAL-PRODUCT: [B3] session_facts.text là lời người dùng kể (có thể chứa tên, địa chỉ, số giấy tờ), chưa che (mục 2)
def add_fact(cid: str, kind: str, text: str, proc_id: str = "") -> None:
    _run("INSERT OR IGNORE INTO session_facts(conversation_id,kind,text,proc_id) VALUES (?,?,?,?)",
         (cid, kind, text, proc_id))


def reset_session(cid: str) -> None:
    """Bắt đầu chủ đề mới: xoá fact và danh sách thủ tục đã hiển thị (để "còn lệ phí thì sao" không bám thủ tục cũ).
    ponytail: xoá cả shown_procedures; nếu Phase 10 cần "cái thứ nhất" xuyên chủ đề thì tách hai hàm."""
    _run("DELETE FROM session_facts WHERE conversation_id=?", (cid,))
    _run("DELETE FROM shown_procedures WHERE conversation_id=?", (cid,))
    # KHÔNG xoá conv_state: không có trạng thái thì resolve dựng lại từ lịch sử và hồi sinh chủ đề cũ. Ghi trạng thái rỗng.
    from system3.retrieval.context import ConvState
    set_state(cid, ConvState().to_dict())


def shown_procedures(cid: str) -> list[dict]:
    return [dict(r) for r in _run(
        "SELECT proc_id,label,ordinal FROM shown_procedures WHERE conversation_id=? ORDER BY ordinal",
        (cid,), many=True)]


def add_shown(cid: str, proc_id: str, label: str) -> None:
    _run("INSERT OR IGNORE INTO shown_procedures VALUES "
         "(?,?,?,(SELECT COALESCE(MAX(ordinal),0)+1 FROM shown_procedures WHERE conversation_id=?))",
         (cid, proc_id, label, cid))


def get_state(cid: str) -> dict | None:
    """Trạng thái hội thoại (ConvState dạng dict); None = chưa có (resolve dựng lại từ lịch sử)."""
    r = _run("SELECT state_json FROM conv_state WHERE conversation_id=?", (cid,), one=True)
    return json.loads(r["state_json"]) if r else None


def set_state(cid: str, state: dict) -> None:
    _run("INSERT INTO conv_state(conversation_id,state_json) VALUES (?,?) "
         "ON CONFLICT(conversation_id) DO UPDATE SET state_json=excluded.state_json, updated_at=datetime('now')",
         (cid, json.dumps(state, ensure_ascii=False)))


# ---- Phase 26: bộ nhớ người dùng theo client_id (xem user_memory.py)
def mem_all(client_id: str) -> dict[str, str]:
    return {r["key"]: r["value"] for r in _run("SELECT key,value FROM user_memory WHERE client_id=?", (client_id,), many=True)}


def mem_set(client_id: str, key: str, value: str) -> None:
    _run("INSERT INTO user_memory(client_id,key,value) VALUES (?,?,?) "
         "ON CONFLICT(client_id,key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')", (client_id, key, value))


def mem_del(client_id: str, key: str | None = None) -> None:
    """key=None: quên tất cả của client_id này (không đụng client khác)."""
    if key is None:
        _run("DELETE FROM user_memory WHERE client_id=?", (client_id,))
    else:
        _run("DELETE FROM user_memory WHERE client_id=? AND key=?", (client_id, key))

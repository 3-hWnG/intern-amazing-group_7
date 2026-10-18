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
    for t, col, ddl in (("conversations", "domain_id", "INTEGER NOT NULL DEFAULT 2"), ("datasets", "domain_id", "INTEGER NOT NULL DEFAULT 2"),
                        ("datasets", "locked", "INTEGER NOT NULL DEFAULT 0")):
        if col not in cols(t):
            c.execute(f"ALTER TABLE {t} ADD COLUMN {col} {ddl}")
    if c.execute("SELECT COUNT(*) FROM domains").fetchone()[0] == 0:   # hai domain có sẵn, không xoá được
        c.execute("INSERT INTO domains(id,name,kind,engine,sort) VALUES (1,'Thủ tục','hard','strict',0)")
        c.execute("INSERT INTO domains(id,name,kind,engine,user_upload,sort) VALUES (2,'Trò chuyện chung','soft','friendly',1,1)")
    if not c.execute("SELECT 1 FROM domains WHERE engine='abi'").fetchone():   # lĩnh vực ABI (docs/PLAN_ABI_LINH_VUC.md): tìm theo engine, KHÔNG cố định id
        c.execute("INSERT INTO domains(name,kind,engine,guardrail,sort) VALUES (?,?,?,?,?)", (ABI_DOMAIN_NAME, "hard", "abi", ABI_GUARDRAIL, 2))
    if "model" not in cols("strict_nodes"):
        c.execute("ALTER TABLE strict_nodes ADD COLUMN model TEXT NOT NULL DEFAULT ''")
    if "context" not in cols("feedback_log"):
        c.execute("ALTER TABLE feedback_log ADD COLUMN context TEXT NOT NULL DEFAULT '{}'")
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
# 3 loại tài khoản: dev (quản trị), can_bo (cán bộ: dùng được mọi dữ liệu), user (người dân: chỉ dữ liệu không bị khoá, xem 2c)
ROLES = {"dev": "Dev", "can_bo": "Cán bộ", "user": "Người dân"}


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


def strict_branches(root: str) -> list[str]:
    return [r["cid"] for r in run("SELECT cid FROM strict_branch WHERE root=?", (root,), many=True)]


def strict_ids(user_id: int) -> set[str]:
    """Mọi hội thoại Strict của một người, KHÔNG gồm các hội thoại phụ (nhánh) — vài câu SQL, không hỏi từng hội thoại."""
    own = {r["conversation_id"] for r in run("SELECT conversation_id FROM strict_owner WHERE user_id=?", (user_id,), many=True)}
    if user_id == first_dev_id():
        own |= {r["conversation_id"] for r in run(
            "SELECT conversation_id FROM strict_legacy WHERE conversation_id NOT IN (SELECT conversation_id FROM strict_owner)",
            many=True)}
    return own - {r["cid"] for r in run("SELECT cid FROM strict_branch", many=True)}


def set_strict_owner(cid: str, user_id: int) -> None:
    run("INSERT OR IGNORE INTO strict_owner(conversation_id,user_id) VALUES (?,?)", (cid, user_id))


def forget_strict(cid: str) -> None:
    run("DELETE FROM strict_owner WHERE conversation_id=?", (cid,))
    run("DELETE FROM strict_legacy WHERE conversation_id=?", (cid,))
    run("DELETE FROM strict_branch WHERE cid=? OR root=?", (cid, cid))
    run("DELETE FROM strict_nodes WHERE root=?", (cid,))
    run("DELETE FROM strict_threads WHERE root=?", (cid,))


# ------------------------------------------------------ hội thoại Friendly
def friendly_owner(cid: str) -> int | None:
    r = run("SELECT user_id FROM conversations WHERE id=?", (cid,), one=True)
    return r["user_id"] if r else None


def create_conversation(user_id: int, domain_id: int = 2) -> str:
    cid = uuid.uuid4().hex
    run("INSERT INTO conversations(id,user_id,domain_id) VALUES (?,?,?)", (cid, user_id, domain_id))
    return cid


def list_conversations(user_id: int) -> list[dict]:
    return run("SELECT id,title,created_at,pinned,domain_id FROM conversations WHERE user_id=? "
               "ORDER BY pinned DESC, rowid DESC", (user_id,), many=True)


def get_conversation(cid: str) -> dict | None:
    return run("SELECT id,title,created_at,pinned,domain_id FROM conversations WHERE id=?", (cid,), one=True)


def rename_conversation(cid: str, title: str) -> None:
    run("UPDATE conversations SET title=? WHERE id=?", (mask_pii(title).strip()[:60] or NEW_TITLE, cid))


def set_pinned(cid: str, pinned: bool) -> None:
    run("UPDATE conversations SET pinned=? WHERE id=?", (1 if pinned else 0, cid))


def set_title_if_new(cid: str, text: str) -> None:
    run("UPDATE conversations SET title=? WHERE id=? AND title=?", (mask_pii(text).strip()[:60] or NEW_TITLE, cid, NEW_TITLE))


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
                meta: dict | None = None, pii_from: str = "") -> int:
    """Thêm tin vào sau parent_id và đặt nó làm cuối nhánh đang xem.
    G1.3: tin người dùng được che CCCD/SĐT; tin trả lời chỉ che các số có trong pii_from (câu người dùng của lượt đó)."""
    if role == "user":
        content = mask_pii(content)
    else:
        content, meta = _scrub(content, pii_from), _scrub(meta, pii_from)
    mid = run("INSERT INTO messages(conversation_id,role,content,status,parent_id,meta) VALUES (?,?,?,?,?,?)",
              (cid, role, content, status, parent_id, json.dumps(meta or {}, ensure_ascii=False)))
    run("UPDATE conversations SET current_leaf=? WHERE id=?", (mid, cid))
    return mid


def update_message(mid: int, content: str, status: str, meta: dict, pii_from: str = "") -> None:
    content, meta = _scrub(content, pii_from), _scrub(meta, pii_from)
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


FEEDBACK_REASONS = {"wrong_proc", "wrong_number", "no_clarify", "wrong_info", "off_topic", "bad_format", "other"}


def clean_reason(reason: str) -> str:
    """Lý do 👎 chọn nhanh: chỉ nhận mã trong danh sách; mã lạ thành "other"; rỗng giữ rỗng."""
    return reason if reason in FEEDBACK_REASONS or not reason else "other"


def mask_pii(text: str) -> str:
    """Che CCCD/SĐT bằng bộ che của System 3 (server/policy). Không nạp được thì báo lỗi, không lưu nguyên văn."""
    from policy import mask_pii as _mask
    return _mask(text)


def _mask_deep(obj):
    from policy import mask_deep
    return mask_deep(obj)


def _scrub(obj, pii_from: str):
    """G1.3: che đúng các số CCCD/SĐT có trong câu người dùng (pii_from) ở obj; không che số khác (mã thủ tục, số của cơ quan)."""
    from policy import pii_tokens, scrub
    return scrub(obj, pii_tokens(pii_from))


def log_feedback(engine: str, msg_key, user_id: int, domain_id, cid: str, prompt: str, answer: str, value: int, context: dict | None = None) -> None:
    """Chụp (câu hỏi, câu trả lời, 👍/👎) vào feedback_log; value 0 thì xoá dòng. Đổi ý thì ghi đè, không tạo trùng.
    Câu hỏi và câu trả lời được che CCCD/SĐT trước khi ghi."""
    if value == 0:
        run("DELETE FROM feedback_log WHERE engine=? AND msg_key=?", (engine, str(msg_key)))
        return
    prompt, answer = mask_pii(prompt), mask_pii(answer)
    run("INSERT INTO feedback_log(engine,msg_key,user_id,domain_id,conversation_id,prompt,answer,value,context) VALUES (?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(engine,msg_key) DO UPDATE SET value=excluded.value, prompt=excluded.prompt, answer=excluded.answer, "
        "context=excluded.context, created_at=datetime('now')",
        (engine, str(msg_key), user_id, domain_id, cid, prompt, answer, value, json.dumps(context or {}, ensure_ascii=False)))


def get_summary(cid: str) -> tuple[str, int]:
    r = run("SELECT summary, summary_upto FROM conversations WHERE id=?", (cid,), one=True)
    return (r["summary"], r["summary_upto"]) if r else ("", 0)


def set_summary(cid: str, text: str, upto: int) -> None:
    run("UPDATE conversations SET summary=?, summary_upto=? WHERE id=?", (mask_pii(text), upto, cid))


# ------------------------------------------------------------- bộ nhớ (NV2)
def list_memories(user_id: int) -> list[dict]:
    return run("SELECT id,text,created_at FROM memories WHERE user_id=? ORDER BY id", (user_id,), many=True)


def add_memory(user_id: int, text: str, max_items: int) -> int:
    mid = run("INSERT INTO memories(user_id,text) VALUES (?,?)", (user_id, mask_pii(text)))
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


# ------------------------------------------------------- dữ liệu người dùng (NV3)
def create_dataset(user_id: int, name: str, filename: str, size: int, domain_id: int = 2) -> int:
    return run("INSERT INTO datasets(user_id,name,filename,size_bytes,domain_id) VALUES (?,?,?,?,?)", (user_id, name, filename, size, domain_id))


def get_dataset(ds_id: int) -> dict | None:
    return run("SELECT * FROM datasets WHERE id=?", (ds_id,), one=True)


def list_datasets(user_id: int | None = None) -> list[dict]:
    sql = ("SELECT d.*, u.username FROM datasets d JOIN users u ON u.id = d.user_id"
           + (" WHERE d.user_id=?" if user_id is not None else "") + " ORDER BY d.id DESC")
    return run(sql, (user_id,) if user_id is not None else (), many=True)


def update_dataset(ds_id: int, **cols) -> None:
    keys = list(cols)
    run(f"UPDATE datasets SET {', '.join(k + '=?' for k in keys)} WHERE id=?", (*[cols[k] for k in keys], ds_id))


_ELEVATED = ("dev", "can_bo")   # được dùng domain / dataset đã khoá


def active_datasets(user_id: int, domain_id: int | None = None, role: str = "dev") -> list[dict]:
    """Bộ dữ liệu đang bật. domain_id None = mọi domain của riêng người này. Có domain_id: dataset RIÊNG của người này trong domain đó,
    cộng dataset dùng chung của domain cứng (người dùng thường không thấy dataset đã khoá)."""
    if domain_id is None:
        return run("SELECT id, name, n_records FROM datasets WHERE user_id=? AND active=1 AND status='ready'", (user_id,), many=True)
    return run("SELECT d.id, d.name, d.n_records FROM datasets d JOIN domains m ON m.id=d.domain_id "
               "WHERE d.domain_id=? AND d.active=1 AND d.status='ready' "
               "AND (d.user_id=? OR (m.kind='hard' AND (d.locked=0 OR ? IN ('dev','can_bo'))))", (domain_id, user_id, role), many=True)


def visible_datasets(user: dict, domain_id: int) -> list[dict]:
    """Danh sách hiện trong "Dữ liệu" của một domain: của mình + dùng chung của domain cứng (không thấy cái đã khoá nếu là Người dân)."""
    return run("SELECT d.*, u.username FROM datasets d JOIN users u ON u.id=d.user_id JOIN domains m ON m.id=d.domain_id "
               "WHERE d.domain_id=? AND (d.user_id=? OR (m.kind='hard' AND (d.locked=0 OR ? IN ('dev','can_bo')))) ORDER BY d.id DESC",
               (domain_id, user["id"], user["role"]), many=True)


def readable_dataset(user: dict, ds: dict) -> bool:
    """Xem được nội dung dataset: chủ, dev, hoặc dataset dùng chung của domain cứng mà mình được dùng."""
    if ds["user_id"] == user["id"] or user["role"] == "dev":
        return True
    d = get_domain(ds["domain_id"])
    return bool(d and d["kind"] == "hard" and can_use_domain(user, d) and (not ds["locked"] or user["role"] in _ELEVATED))


# ------------------------------------------------------------------- domain
BUILTIN_DOMAINS = (1, 2)   # Thủ tục (System 3) và Trò chuyện chung: không xoá được (lĩnh vực ABI là lĩnh vực cứng nên cũng không xoá được)
ABI_DOMAIN_NAME = "ABI – Trung tâm Ươm tạo"
ABI_GUARDRAIL = ("Bạn là trợ lý tra cứu thông tin Trung tâm Ươm tạo Doanh nghiệp Nông nghiệp Công nghệ cao TP.HCM (ABI, web abi.com.vn). "
                 "Chỉ trả lời từ dữ liệu được cung cấp; không đoán số liệu, ngày giờ, tên người. Câu hỏi ngoài phạm vi trung tâm thì nói rõ "
                 "bạn chỉ hỗ trợ thông tin về trung tâm.")


def get_domain(did: int | None) -> dict | None:
    return run("SELECT * FROM domains WHERE id=?", (did,), one=True) if did else None


def can_use_domain(user: dict, d: dict) -> bool:
    """Dùng chung (owner NULL) hoặc của mình; domain đã khoá thì chỉ dev và cán bộ."""
    return (d["owner_id"] is None or d["owner_id"] == user["id"]) and (not d["locked"] or user["role"] in _ELEVATED)


def visible_domains(user: dict) -> list[dict]:
    pins = {r["domain_id"]: bool(r["pinned"]) for r in run("SELECT domain_id,pinned FROM domain_pins WHERE user_id=?", (user["id"],), many=True)}
    rows = [d for d in run("SELECT * FROM domains ORDER BY sort,id", many=True) if can_use_domain(user, d)]
    for i, d in enumerate(rows):
        d["pinned"] = pins.get(d["id"], i < 4)   # chưa chọn: 4 domain đầu được ghim
    return rows


def used_bytes(user_id: int) -> int:
    return run("SELECT COALESCE(SUM(size_bytes),0) n FROM datasets WHERE user_id=?", (user_id,), one=True)["n"]


def insert_records(ds_id: int, recs: list[dict]) -> list[int]:
    """Ghi bản ghi + chỉ mục từ khoá trong một giao dịch. Trả id theo đúng thứ tự."""
    c = conn()
    try:
        ids = []
        for r in recs:
            cur = c.execute("INSERT INTO records(dataset_id,title,fields,text,source) VALUES (?,?,?,?,?)",
                            (ds_id, r["title"], json.dumps(r["fields"], ensure_ascii=False), r["text"], r["source"]))
            ids.append(cur.lastrowid)
            c.execute("INSERT INTO records_fts(rowid,title,text) VALUES (?,?,?)", (cur.lastrowid, r["title"], r["text"]))
        c.commit()
        return ids
    finally:
        c.close()


def delete_records(ds_id: int) -> None:
    c = conn()
    try:
        c.execute("DELETE FROM records_fts WHERE rowid IN (SELECT id FROM records WHERE dataset_id=?)", (ds_id,))
        c.execute("DELETE FROM records WHERE dataset_id=?", (ds_id,))
        c.commit()
    finally:
        c.close()


def _rec(r: dict) -> dict:
    r = dict(r)
    try:
        r["fields"] = json.loads(r.get("fields") or "{}")
    except ValueError:
        r["fields"] = {}
    return r


def get_records(ids: list[int]) -> list[dict]:
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    return [_rec(r) for r in run(f"SELECT * FROM records WHERE id IN ({marks})", tuple(ids), many=True)]


def browse_records(ds_id: int, q: str = "", offset: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    like = f"%{q}%"
    where = "dataset_id=?" + (" AND (title LIKE ? OR text LIKE ?)" if q else "")
    args = (ds_id, like, like) if q else (ds_id,)
    total = run(f"SELECT COUNT(*) n FROM records WHERE {where}", args, one=True)["n"]
    rows = run(f"SELECT * FROM records WHERE {where} ORDER BY id LIMIT ? OFFSET ?", (*args, limit, offset), many=True)
    return [_rec(r) for r in rows], total


# ------------------------------------------------------- bộ công cụ dev (chi tiết câu trả lời)
def save_trace(mid: int, cid: str, user_id: int, data: dict, keep: int) -> None:
    run("INSERT OR REPLACE INTO traces(message_id,conversation_id,user_id,data) VALUES (?,?,?,?)",
        (mid, cid, user_id, json.dumps(_mask_deep(data), ensure_ascii=False, default=str)))
    run("DELETE FROM traces WHERE message_id NOT IN (SELECT message_id FROM traces ORDER BY message_id DESC LIMIT ?)", (keep,))


def patch_trace(mid: int, key: str, value) -> None:
    r = run("SELECT data FROM traces WHERE message_id=?", (mid,), one=True)
    if r:
        d = json.loads(r["data"])
        d[key] = _mask_deep(value)
        run("UPDATE traces SET data=? WHERE message_id=?", (json.dumps(d, ensure_ascii=False, default=str), mid))


def get_trace(mid: int) -> dict | None:
    r = run("SELECT data FROM traces WHERE message_id=?", (mid,), one=True)
    return json.loads(r["data"]) if r else None

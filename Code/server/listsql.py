"""Liệt kê / đếm thủ tục bằng text-to-SQL trên MỘT bảng phẳng (G4.2, P12, ADR-09; quyết định của trưởng nhóm 14/10).

LLM (4B) chỉ viết MỘT câu SELECT trên bảng `proc_flat` (mỗi thủ tục một dòng, dựng sẵn khi build DB — data/checks.py), không JOIN.
Hộp cát:
  - câu SQL chạy trên BẢN SAO TRONG BỘ NHỚ chỉ gồm các thủ tục trong phạm vi trả lời (cấp xã, toàn quốc, không ngành dọc),
    không bao giờ chạm tệp DB thật; kết nối `PRAGMA query_only=1`;
  - `set_authorizer`: chỉ SELECT, READ trên `proc_flat`, và hàm thường — mọi thứ khác (ghi, PRAGMA, ATTACH, sqlite_master…) bị từ chối;
  - một câu lệnh (không ';' ở giữa), bắt đầu bằng SELECT/WITH; bọc `SELECT * FROM (…) LIMIT 200`; `progress_handler` cắt truy vấn quá dài.
Lỗi -> gửi lỗi cho LLM sửa một lần; hỏng lần hai -> None (bên gọi lùi về fee_query / liệt kê gần đúng).
Câu trả lời do CODE viết từ kết quả (đếm: "Có N thủ tục…"; liệt kê: danh sách đánh số)."""
from __future__ import annotations

import os
import re
import sqlite3
import threading

from system3.data.textutil import fold

COLUMNS = [("proc_id", "TEXT", "mã thủ tục"), ("name", "TEXT", "tên thủ tục (có dấu)"),
           ("name_fold", "TEXT", "tên thủ tục chữ thường không dấu (hệ thống tự dùng khi lọc theo tên)"),
           ("domain", "TEXT", "lĩnh vực (đúng một giá trị trong danh sách bên dưới)"),
           ("fee_min_vnd", "INTEGER", "lệ phí thấp nhất, đồng (NULL = không có số)"), ("fee_max_vnd", "INTEGER", "lệ phí cao nhất, đồng (NULL = không có số)"),
           ("fee_free", "INTEGER", "1 = ghi rõ không thu phí"), ("days_min", "REAL", "số ngày giải quyết ít nhất (NULL = không ghi)"),
           ("days_max", "REAL", "số ngày giải quyết nhiều nhất (NULL = không ghi)"), ("online", "INTEGER", "1 = nộp trực tuyến được"),
           ("subjects", "TEXT", "đối tượng thực hiện, cách nhau bởi '; '")]
MAX_ROWS, SHOW = 200, 30
_INTENT = re.compile(r"liet ke|danh sach (cac |nhung )?thu tuc|(co )?bao nhieu thu tuc|(co )?may thu tuc|dem .{0,20}thu tuc|so (luong )?thu tuc|"
                     r"(nhung|cac) thu tuc (nao|gi)\b|thu tuc nao (thi |duoc |co the )?(mien phi|nop truc tuyen|khong mat)")
_COUNT = re.compile(r"bao nhieu|may thu tuc|dem\b|so luong")
SCHEMA = {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}
_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
_lock = threading.Lock()
_sandbox: dict = {"key": None, "conn": None, "domains": []}


def wants(text: str) -> bool:
    return bool(_INTENT.search(fold(text or "")))


def _authorizer(action, arg1, arg2, dbname, source):
    if action == sqlite3.SQLITE_READ:
        return sqlite3.SQLITE_OK if arg1 == "proc_flat" else sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in ("load_extension", "readfile", "writefile", "fts3_tokenizer"):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY


def sandbox(src: sqlite3.Connection | None = None):
    """Bản sao trong bộ nhớ của proc_flat (chỉ thủ tục trong phạm vi), dựng lại khi DB thủ tục đổi. -> (conn, domains)."""
    from system3.data import api as data_api
    src = src or data_api.connect()
    path = src.execute("PRAGMA database_list").fetchone()[2]
    key = (path, os.path.getmtime(path) if path and os.path.exists(path) else 0)
    with _lock:
        if _sandbox["key"] != key:
            cols = ", ".join(c for c, _, _ in COLUMNS)
            rows = src.execute(f"SELECT {cols} FROM proc_flat WHERE in_scope=1").fetchall()
            m = sqlite3.connect(":memory:", check_same_thread=False)
            m.execute("CREATE TABLE proc_flat (" + ", ".join(f"{c} {t}" for c, t, _ in COLUMNS) + ")")
            m.executemany(f"INSERT INTO proc_flat VALUES ({','.join('?' * len(COLUMNS))})", [tuple(r) for r in rows])
            m.commit()
            m.execute("PRAGMA query_only=1")
            m.set_authorizer(_authorizer)
            doms = [r[0] for r in m.execute("SELECT domain, COUNT(*) n FROM proc_flat GROUP BY domain ORDER BY n DESC")]
            _sandbox.update(key=key, conn=m, domains=doms)
        return _sandbox["conn"], _sandbox["domains"]


_LIKE = re.compile(r"(?i)\bname(_fold)?\s+(NOT\s+)?LIKE\s+'([^']*)'")


class SQLRejected(ValueError):
    pass


def run_sql(conn: sqlite3.Connection, sql: str, max_steps: int = 2_000_000) -> tuple[list[str], list[tuple]]:
    """Chạy một câu SELECT trong hộp cát. -> (tên cột, các dòng <= MAX_ROWS). Vi phạm -> SQLRejected; lỗi SQL -> sqlite3.Error."""
    s = re.sub(r"^```(?:sql)?|```$", "", (sql or "").strip(), flags=re.I).strip()
    s = re.sub(r"[\s;}]+$", "", s)   # model hay để lọt '}' của JSON / ';' ở cuối
    s = _LIKE.sub(lambda m: f"name_fold {m.group(2) or ''}LIKE '{fold(m.group(3))}'", s)   # lọc theo tên: code bỏ dấu (model bỏ dấu hay sai)
    if not re.match(r"(?is)^(select|with)\b", s):
        raise SQLRejected("chỉ được dùng SELECT")
    if ";" in s:
        raise SQLRejected("chỉ được một câu lệnh")
    steps = [0]

    def tick():
        steps[0] += 1
        return 1 if steps[0] * 1000 > max_steps else 0   # khác 0 = huỷ truy vấn
    with _lock:
        conn.set_progress_handler(tick, 1000)
        try:
            cur = conn.execute(f"SELECT * FROM ({s}) LIMIT {MAX_ROWS}")
            names = [d[0] for d in cur.description]
            return names, cur.fetchall()
        except sqlite3.DatabaseError as e:
            if "not authorized" in str(e) or "prohibited" in str(e):
                raise SQLRejected(str(e)) from e
            raise
        finally:
            conn.set_progress_handler(None, 0)


def prompt(domains: list[str]) -> str:
    cols = "\n".join(f"  {c} {t} -- {d}" for c, t, d in COLUMNS)
    return ("Bạn viết MỘT câu SQLite SELECT để trả lời câu hỏi liệt kê hoặc đếm thủ tục hành chính.\n"
            f"Chỉ có MỘT bảng (không JOIN, không bảng nào khác):\nproc_flat(\n{cols}\n)\n"
            "Mọi dòng trong bảng đều là thủ tục cấp xã áp dụng toàn quốc.\n"
            "Quy tắc:\n"
            "- Liệt kê: SELECT name FROM proc_flat WHERE ... ORDER BY name. Đếm: SELECT COUNT(*) FROM proc_flat WHERE ...\n"
            "- Lọc theo lĩnh vực: domain = '<một giá trị trong danh sách>' (chép đúng). Lọc theo chữ trong tên: name LIKE '%chữ có dấu%' "
            "(giữ nguyên chữ người dùng gõ).\n"
            "- Miễn phí: fee_free = 1. Lệ phí dưới X đồng: fee_max_vnd < X. Trực tuyến: online = 1. Giải quyết trong N ngày: days_max <= N.\n"
            "- Chỉ trả JSON {\"sql\": \"...\"}.\n"
            "Ví dụ: 'liệt kê thủ tục lĩnh vực Hộ tịch nộp trực tuyến được' -> SELECT name FROM proc_flat WHERE domain = 'Hộ tịch' AND online = 1 ORDER BY name\n"
            "Ví dụ: 'có bao nhiêu thủ tục liên quan đến kết hôn' -> SELECT COUNT(*) FROM proc_flat WHERE name LIKE '%kết hôn%'\n"
            "Các giá trị domain: " + " | ".join(domains))


def render(names: list[str], rows: list[tuple], count_q: bool) -> dict:
    """Câu trả lời bằng code từ kết quả."""
    scope = "(trong các thủ tục cấp xã áp dụng toàn quốc mà hệ thống trả lời được)"
    if len(names) == 1 and len(rows) == 1 and isinstance(rows[0][0], (int, float)) and re.search(r"count|so_luong|n$", names[0], re.I):
        n = int(rows[0][0])
        return {"kind": "count", "count": n, "names": [], "text": f"Có **{n}** thủ tục khớp yêu cầu {scope}."}
    col = next((i for i, c in enumerate(names) if c.lower() == "name"), 0)
    items = list(dict.fromkeys(str(r[col]) for r in rows if r[col] is not None))
    if not items:
        return {"kind": "list", "count": 0, "names": [], "text": f"Không có thủ tục nào khớp yêu cầu {scope}."}
    more = len(items) - SHOW
    head = f"Có **{len(items)}{'+' if len(rows) >= MAX_ROWS else ''}** thủ tục khớp yêu cầu {scope}" + (":" if not count_q else ". Gồm:")
    lines = "\n".join(f"{i}. {n}" for i, n in enumerate(items[:SHOW], 1))
    tail = f"\n… và {more} thủ tục khác. Bạn nói rõ hơn (lĩnh vực, chữ trong tên) để thu hẹp." if more > 0 else ""
    return {"kind": "list", "count": len(items), "names": items, "text": f"{head}\n{lines}{tail}\nBạn hỏi tên một thủ tục để xem chi tiết."}


def answer(text: str, llm, conn: sqlite3.Connection | None = None) -> dict | None:
    """-> {"text", "sql", "kind", "count", "names", "tries"} hoặc None (không phải ý liệt kê / không có LLM / LLM hỏng 2 lần)."""
    if llm is None or not wants(text):
        return None
    box, domains = sandbox(conn)
    system, user, err = prompt(domains), f"Câu hỏi: {text}", ""
    for attempt in (1, 2):
        try:
            out = llm(system, user + (f"\nCâu SQL trước bị lỗi: {err}. Viết lại cho đúng." if err else ""),
                      schema=SCHEMA, timeout=7, num_predict=200)
        except Exception:   # noqa: BLE001 - LLM lỗi / hết giờ / GPU bận: lùi về đường cũ ngay, không thử lại
            return None
        sql = str((out or {}).get("sql") or "")
        try:
            names, rows = run_sql(box, sql)
        except (SQLRejected, sqlite3.Error) as e:
            err = f"{type(e).__name__}: {e}"[:200]
            continue
        res = render(names, rows, bool(_COUNT.search(fold(text))))
        return {**res, "sql": sql, "tries": attempt}
    return None

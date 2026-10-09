"""API tối thiểu của lớp dữ liệu cho các tầng trên (Planner/Executor). Chỉ đọc."""
from __future__ import annotations

import sqlite3

from . import DB_PATH, records as _R, search as _S

parse_query = _S.parse_query


def connect(db_path=None) -> sqlite3.Connection:
    """Mở system3.db (read-only về mặt nghiệp vụ). Phải chạy build trước."""
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def search(conn, query: str, limit: int = 5) -> list[dict]:
    """Câu tự do -> top-k thủ tục (match_tier, term_overlap, confident, score).
    Đi qua parse_query (bung từ đồng nghĩa, bỏ lời đệm/tên tỉnh); nếu rỗng thì dùng nguyên câu."""
    kw = parse_query(conn, query)["keyword"] or query
    return _S.search_ranked(conn, kw, limit)


def get_record(conn, proc_id: str) -> dict | None:
    """Bản ghi sạch đầy đủ (fees_clean, files_clean, steps_clean, components...)."""
    return _R.build_record(conn, proc_id)


def fields(conn, proc_id: str, names: list[str]) -> list[dict]:
    """Chunks của các field yêu cầu: [{field, case_ordinal, text, status}].
    status=present|absent_confirmed|unknown; text rỗng nghĩa là không có dữ liệu."""
    q = ",".join("?" * len(names))
    return [dict(r) for r in conn.execute(
        f"SELECT field, case_ordinal, text, status FROM field_chunks"
        f" WHERE proc_id=? AND field IN ({q}) ORDER BY rowid", (proc_id, *names))]


def family_of(conn, proc_id: str) -> dict | None:
    """{head, label, n_members, default_variant} của thủ tục."""
    r = conn.execute("SELECT head, label, n_members, default_variant FROM families"
                     " WHERE proc_id=?", (proc_id,)).fetchone()
    return dict(r) if r else None


def variants(conn, head: str) -> list[dict]:
    """Các dạng trong nhóm: [{proc_id, name, province, default_variant}], bản mặc định trước."""
    return [dict(r) for r in conn.execute(
        "SELECT f.proc_id, p.name, p.province, f.default_variant FROM families f"
        " JOIN procedures p ON p.proc_id=f.proc_id AND p.status='active'"
        " WHERE f.head=? ORDER BY f.default_variant DESC, length(p.name)", (head,))]


def default_variant(conn, head: str) -> str | None:
    """proc_id của bản mặc định trong nhóm."""
    r = conn.execute("SELECT proc_id FROM families WHERE head=? AND default_variant=1",
                     (head,)).fetchone()
    return r[0] if r else None


def conditions(conn, proc_id: str) -> list[dict]:
    """[{type: who|situation|status|place, text, source: case|subject|variant_name}]."""
    return [dict(r) for r in conn.execute(
        "SELECT type, text, source FROM condition_index WHERE proc_id=?", (proc_id,))]


def is_expired(conn, proc_id: str) -> dict | None:
    """Bản tombstone nếu thủ tục hết hiệu lực, None nếu còn. (Snapshot hiện không có bản hết hạn.)"""
    return _R.is_expired(conn, proc_id)


def subject_names(conn) -> list[dict]:
    """Phase 26: danh mục đối tượng thực hiện [{name, n}] (TRIM, chỉ thủ tục còn hiệu lực, nhiều thủ tục nhất trước)."""
    return [{"name": r["subj"], "n": r["n"]} for r in conn.execute(
        "SELECT TRIM(s.subject_name) AS subj, COUNT(DISTINCT p.proc_id) AS n FROM procedure_subjects s"
        " JOIN procedures p ON p.row_id=s.row_id AND p.status='active'"
        " WHERE TRIM(s.subject_name)<>'' GROUP BY subj ORDER BY n DESC, subj")]


def subjects_of(conn, proc_ids: list[str]) -> dict[str, set[str]]:
    """Phase 26: {proc_id: {tên đối tượng}} của các thủ tục (thủ tục không khai đối tượng -> tập rỗng)."""
    out: dict[str, set[str]] = {p: set() for p in proc_ids}
    if proc_ids:
        q = ",".join("?" * len(proc_ids))
        for r in conn.execute(
                f"SELECT p.proc_id, TRIM(s.subject_name) FROM procedures p JOIN procedure_subjects s ON s.row_id=p.row_id"
                f" WHERE p.proc_id IN ({q}) AND p.status='active' AND TRIM(s.subject_name)<>''", proc_ids):
            out[r[0]].add(r[1])
    return out

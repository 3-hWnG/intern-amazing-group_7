"""Nạp snapshot procedures.jsonl vào SQLite (copy-rồi-sửa từ import_db.py của repo V10.6).

Khác bản gốc: build luôn dựng DB MỚI nên bỏ versioning/tombstone (archived/expired).
Mọi bản ghi nạp vào đều status='active'. Vẫn KHÔNG sửa nội dung nguồn.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sqlite3

from . import DB_PATH, SNAPSHOT
from .textutil import fold

PROC_COLUMNS = (
    "proc_id", "province", "source_id", "name", "domain", "description",
    "requirements", "results", "executing_agency", "receiving_address",
    "coordinating_agency", "department_promulgate", "department_code",
    "agency_levels", "subject_types", "keywords", "state",
    "processing_time_text", "portal_url", "online_url", "has_online_submission",
    "decision_number", "decision_date", "publication_date", "issuing_agency",
    "source_updated_at", "source_created_at",
    "status_fees", "status_files", "status_checklist", "status_description",
    "status_legal", "status_meta", "status_online", "status_address",
    "status_processing_time", "search_text", "content_hash",
)


def connect_new(db_path=None) -> sqlite3.Connection:
    p = db_path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        q = p.with_name(p.name + suffix)
        if q.exists():
            q.unlink()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript((SNAPSHOT / "schema_procedures.sql").read_text(encoding="utf-8"))
    return conn


def _insert_children(conn, row_id: int, rec: dict) -> None:
    for fee in rec.get("fees") or []:
        conn.execute(
            "INSERT INTO procedure_fees (row_id, fee_type, amount_value, amount_text,"
            " currency_id, submission_method) VALUES (?,?,?,?,?,?)",
            (row_id, fee.get("fee_type", ""), fee.get("amount_value"),
             fee.get("amount_text", ""), fee.get("currency_id", ""),
             fee.get("submission_method", "")))
    for i, item in enumerate(rec.get("checklist") or []):
        conn.execute(
            "INSERT INTO checklist_items (row_id, ordinal, case_ordinal, case_name,"
            " name, code, required, original_qty, copy_qty, has_electronic_form,"
            " n_attachments) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (row_id, i, item.get("case_ordinal", -1), item.get("case_name", ""),
             item.get("name", ""), item.get("code", ""), int(bool(item.get("required"))),
             item.get("original_qty", 0), item.get("copy_qty", 0),
             int(bool(item.get("has_electronic_form"))), item.get("n_attachments", 0)))
    for f in rec.get("files") or []:
        conn.execute(
            "INSERT INTO procedure_files (row_id, file_id, file_name, bucket_name,"
            " remote_path, local_path, file_available, belongs_to)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (row_id, f.get("file_id", ""), f.get("file_name", ""),
             f.get("bucket_name", ""), f.get("remote_path", ""),
             f.get("local_path", ""), int(f.get("file_available", 0)),
             f.get("belongs_to", "")))
    for s in rec.get("steps") or []:
        conn.execute("INSERT INTO procedure_steps (row_id, ordinal, name, description)"
                     " VALUES (?,?,?,?)",
                     (row_id, s.get("ordinal", 0), s.get("name", ""), s.get("description", "")))
    for m in rec.get("methods") or []:
        conn.execute(
            "INSERT INTO procedure_methods (row_id, submission_method,"
            " processing_time_qty, processing_time_unit, processing_time_text,"
            " description) VALUES (?,?,?,?,?,?)",
            (row_id, m.get("submission_method", ""), m.get("processing_time_qty", 0),
             m.get("processing_time_unit", ""), m.get("processing_time_text", ""),
             m.get("description", "")))
    for lb in rec.get("legal_basis") or []:
        conn.execute("INSERT INTO legal_basis (row_id, doc_code, doc_name, doc_year)"
                     " VALUES (?,?,?,?)",
                     (row_id, lb.get("doc_code", ""), lb.get("doc_name", ""),
                      lb.get("doc_year", "")))
    for c in rec.get("cases") or []:
        conn.execute("INSERT INTO procedure_cases (row_id, ordinal, case_name,"
                     " n_components) VALUES (?,?,?,?)",
                     (row_id, c.get("ordinal", 0), c.get("case_name", ""),
                      c.get("n_components", 0)))
    for sub in rec.get("subjects") or []:
        conn.execute("INSERT INTO procedure_subjects (row_id, subject_name,"
                     " subject_code) VALUES (?,?,?)",
                     (row_id, sub.get("subject_name", ""), sub.get("subject_code", "")))
    for sv in rec.get("online_services") or []:
        conn.execute("INSERT INTO online_services (row_id, service_code, service_name,"
                     " processing_qty, processing_unit) VALUES (?,?,?,?,?)",
                     (row_id, sv.get("service_code", ""), sv.get("service_name", ""),
                      sv.get("processing_qty", 0), sv.get("processing_unit", "")))


def compute_search_text(rec: dict) -> str:
    """Chuỗi dùng để tra cứu FTS: đã bỏ dấu + xử lý đ/Đ."""
    sub_names = [s["subject_name"] if isinstance(s, dict) else str(s)
                 for s in rec.get("subjects") or []]
    return fold(" ".join(filter(None, [
        rec.get("name", ""), rec.get("domain", ""), rec.get("keywords", ""),
        rec.get("proc_id", ""), rec.get("executing_agency", ""), " ".join(sub_names),
    ])))


def compute_content_hash(rec: dict) -> str:
    exclude = {"content_hash", "search_text"}
    payload = {k: v for k, v in rec.items() if k not in exclude}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()


def load_snapshot(path=None) -> list[dict]:
    path = path or SNAPSHOT / "procedures.jsonl"
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def import_records(conn, records: list[dict]) -> int:
    now = _dt.datetime.now().isoformat(timespec="seconds")
    n = 0
    for rec in records:
        if not rec.get("proc_id"):
            continue
        rec["search_text"] = compute_search_text(rec)
        rec["content_hash"] = compute_content_hash(rec)
        ph = ",".join("?" * (len(PROC_COLUMNS) + 4))
        cur = conn.execute(
            f"INSERT INTO procedures ({','.join(PROC_COLUMNS)}, version, status,"
            f" scraped_at, last_seen_at) VALUES ({ph})",
            tuple(rec.get(c) if c == "province" else rec.get(c, "") for c in PROC_COLUMNS)
            + (1, "active", now, now))
        row_id = cur.lastrowid
        _insert_children(conn, row_id, rec)
        conn.execute(
            "INSERT INTO procedures_fts (proc_id, row_id, search_text, name_folded,"
            " description_folded) VALUES (?,?,?,?,?)",
            (rec["proc_id"], row_id, rec["search_text"], fold(rec.get("name", "")),
             fold(rec.get("description", ""))))
        n += 1
    conn.commit()
    return n

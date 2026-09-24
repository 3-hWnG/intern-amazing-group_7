"""BƯỚC ④ — nạp staging/procedures.jsonl vào SQLite, có versioning.

    hash trùng  → bỏ qua, không ghi gì
    hash khác   → bản cũ status='archived', chèn bản mới status='active', version+1
    mã mới      → chèn version=1

KHÔNG BAO GIỜ update đè. KHÔNG BAO GIỜ xoá. Lịch sử luôn tra ngược được.

Chạy:
    python -m Database.pipeline.import_db
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import sqlite3

from Database.pipeline import paths
from Database.pipeline.textutil import fold

log = logging.getLogger("pipeline.import")

CHILD_TABLES = ("procedure_fees", "checklist_items", "procedure_files",
                "procedure_steps", "procedure_methods", "legal_basis",
                "procedure_cases", "procedure_subjects", "online_services")

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
    "status_processing_time",
    "search_text", "content_hash",
)


def connect(db_path=None) -> sqlite3.Connection:
    db_path = db_path or paths.PROCEDURES_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(paths.SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def _insert_children(conn: sqlite3.Connection, row_id: int, rec: dict) -> None:
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
            (row_id, i, item.get("case_ordinal", -1),
             item.get("case_name", ""), item.get("name", ""),
             item.get("code", ""), int(bool(item.get("required"))),
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
        conn.execute(
            "INSERT INTO procedure_steps (row_id, ordinal, name, description)"
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


def import_records(conn: sqlite3.Connection, records: list[dict]) -> dict:
    now = _dt.datetime.now().isoformat(timespec="seconds")
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}

    for rec in records:
        proc_id = rec.get("proc_id")
        if not proc_id:
            continue

        province = rec.get("province")
        current = conn.execute(
            "SELECT row_id, content_hash, version FROM procedures"
            " WHERE proc_id = ? AND IFNULL(province,'ALL') = IFNULL(?,'ALL')"
            "   AND status = 'active'", (proc_id, province)).fetchone()
        if current is None:
            # Cùng MỘT bản ghi nguồn (cùng mã + cùng source_id) nhưng `province`
            # đổi — vd lần đầu gắn tỉnh công bố. Đây là PHIÊN BẢN MỚI của nó,
            # không phải thủ tục mới; không bắt thì bản cũ vẫn 'active' song song.
            current = conn.execute(
                "SELECT row_id, content_hash, version FROM procedures"
                " WHERE proc_id = ? AND source_id = ? AND status = 'active'",
                (proc_id, rec.get("source_id", ""))).fetchone()

        if current and current["content_hash"] == rec["content_hash"]:
            # Nội dung không đổi nhưng VẪN CÒN trên cổng → cập nhật last_seen_at.
            # Đây là dữ liệu nuôi cơ chế tombstone ở dưới.
            conn.execute("UPDATE procedures SET last_seen_at=? WHERE row_id=?",
                         (now, current["row_id"]))
            stats["unchanged"] += 1
            continue

        version = 1
        if current:
            # Bản cũ chuyển sang lưu trữ — KHÔNG xoá, KHÔNG đè.
            conn.execute(
                "UPDATE procedures SET status='archived', archived_at=?"
                " WHERE row_id=?", (now, current["row_id"]))
            version = current["version"] + 1
            stats["updated"] += 1
        else:
            stats["inserted"] += 1

        placeholders = ",".join("?" * (len(PROC_COLUMNS) + 4))
        cur = conn.execute(
            f"INSERT INTO procedures ({','.join(PROC_COLUMNS)}, version, status,"
            f" scraped_at, last_seen_at) VALUES ({placeholders})",
            tuple(rec.get(c) if c == "province" else rec.get(c, "")
                  for c in PROC_COLUMNS) + (version, "active", now, now))
        row_id = cur.lastrowid

        _insert_children(conn, row_id, rec)

        conn.execute("DELETE FROM procedures_fts WHERE proc_id = ?", (proc_id,))
        conn.execute(
            "INSERT INTO procedures_fts (proc_id, row_id, search_text, name_folded,"
            " description_folded) VALUES (?,?,?,?,?)",
            (proc_id, row_id, rec.get("search_text", ""),
             fold(rec.get("name", "")), fold(rec.get("description", ""))))

    conn.execute(
        "INSERT INTO import_log (run_at, n_input, n_inserted, n_updated, n_unchanged)"
        " VALUES (?,?,?,?,?)",
        (now, len(records), stats["inserted"], stats["updated"], stats["unchanged"]))
    conn.commit()
    return stats


def sweep_expired(conn: sqlite3.Connection, seen_proc_ids: set[str],
                  note: str = "") -> int:
    """TOMBSTONE — đánh dấu hết hạn những thủ tục KHÔNG còn trong danh mục cổng.

    Đây là cách trung thực nhất có thể: cổng DVCQG **không công bố ngày hết
    hiệu lực** (đã dò toàn bộ payload, không có trường nào expir/effect/valid).
    Nên "hết hạn" ở đây = "biến mất khỏi danh mục vào ngày mình cào", và
    `expiry_note` phải nói đúng như vậy, không được giả vờ là ngày luật hết hiệu lực.

    ⚠️ CHỈ GỌI SAU MỘT LẦN CÀO ĐẦY ĐỦ phạm vi đang quản lý. Chạy sau một mẻ
    nhỏ sẽ khai tử oan toàn bộ phần còn lại — vì vậy hàm này không bao giờ
    tự động chạy, phải truyền cờ --sweep.
    """
    now = _dt.datetime.now().isoformat(timespec="seconds")
    rows = conn.execute(
        "SELECT row_id, proc_id FROM procedures WHERE status='active'").fetchall()
    gone = [r for r in rows if r["proc_id"] not in seen_proc_ids]
    for r in gone:
        conn.execute(
            "UPDATE procedures SET status='expired', expired_at=?, expiry_note=?"
            " WHERE row_id=?",
            (now, note or f"Không còn trong danh mục Cổng DVCQG khi cào ngày "
                          f"{now[:10]}. Đây là ngày PHÁT HIỆN, không phải ngày "
                          f"luật hết hiệu lực — cổng không công bố ngày đó.",
             r["row_id"]))
        conn.execute("DELETE FROM procedures_fts WHERE proc_id = ?", (r["proc_id"],))
    conn.commit()
    return len(gone)


def load_staging(path=None) -> list[dict]:
    path = path or paths.STAGING_PATH
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bước ④: nạp vào SQLite có versioning")
    ap.add_argument("--sweep", action="store_true",
                    help="đánh dấu hết hạn thủ tục không còn trong mẻ này. "
                         "CHỈ dùng sau khi cào ĐẦY ĐỦ phạm vi đang quản lý.")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    records = load_staging()
    if not records:
        log.error("không có %s — chạy normalize trước", paths.STAGING_PATH)
        return 1

    conn = connect()
    n_expired = 0
    try:
        stats = import_records(conn, records)
        if args.sweep:
            n_expired = sweep_expired(conn, {r["proc_id"] for r in records})
        total = conn.execute(
            "SELECT COUNT(*) FROM procedures WHERE status='active'").fetchone()[0]
    finally:
        conn.close()

    log.info("nạp %d bản ghi → mới=%d cập nhật=%d không đổi=%d",
             len(records), stats["inserted"], stats["updated"], stats["unchanged"])
    if args.sweep:
        log.info("quét hết hạn: %d thủ tục chuyển sang status='expired'", n_expired)
    log.info("DB hiện có %d thủ tục đang hiệu lực → %s", total, paths.PROCEDURES_DB)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

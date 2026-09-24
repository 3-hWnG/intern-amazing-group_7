"""
importer.py — System 2: nạp dữ liệu thủ tục vào SQLite (db/schema.sql, chốt V3).

Cách dùng:
    python importer.py --init
        Tạo file DB mới (db/procedures.db) từ db/schema.sql.

    python importer.py --seed data/normalized_procedures.json
        Nạp dữ liệu. Tự nhận diện 2 định dạng:
          - Định dạng chuẩn (đầu ra mong đợi từ crawler/, xem SCHEMA_DOC bên dưới)
          - Định dạng cũ của ../data/normalized_procedures.json (70 thủ tục có sẵn,
            scrape từ trước cho hệ RAG cũ) — dùng để có seed data thật ngay hôm nay,
            không phải chờ crawler/ viết xong (xem README.md, mục "Dữ liệu có sẵn").

    python importer.py --seed <file> --db db/other.db --dry-run
        --dry-run: tính toán + in log nhưng không ghi DB (để review trước khi nạp thật).

Idempotent: chạy lại cùng 1 file nhiều lần không tạo bản ghi trùng — content_hash
giống thì bỏ qua, khác thì archive bản cũ + insert bản mới (đúng luật versioning
trong ARCHITECTURE_SYSTEM2.md mục 3).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "db" / "procedures.db"
DEFAULT_SCHEMA = HERE / "db" / "schema.sql"

# Định dạng chuẩn 1 thủ tục (đầu ra mong đợi từ crawler/) — xem crawler/README.md
SCHEMA_DOC = """
{
  "proc_code": "T-BTP-282384-TT",       # bắt buộc — mã Dịch vụ công, hoặc mã tạm nếu chưa có
  "name": "...",                         # bắt buộc
  "domain": "...",                       # bắt buộc, vd "Hộ tịch"
  "level": null,                         # optional: "Cấp xã" | "Cấp huyện" | "Cấp tỉnh"
  "province": null,                      # optional, null = áp dụng toàn quốc
  "description": "...",
  "duration_desc": "...",
  "authority": "...",
  "application_method": null,            # optional: "Trực tiếp" | "Trực tuyến" | "Cả hai"
  "receiving_location": null,            # optional — ĐỊA CHỈ/nơi nộp hồ sơ trực tiếp (khác authority = TÊN cơ quan)
  "online_url": null,                    # optional — link Cổng DVC để nộp trực tuyến
  "meta_source": null,                   # optional — căn cứ pháp lý
  "effective_date": null,                # optional, "YYYY-MM-DD"
  "expiration_date": null,               # optional, "YYYY-MM-DD"
  "checklists": [{"item_type": "giay_to_phai_nop", "content": "...", "note": null}],
  "fees": [{"fee_type": "...", "amount_text": "...", "condition": null}],
  "files": [{"file_name": "...", "download_url": "...", "file_size": null}]
}
"""


# ---------------------------------------------------------------------------
# Chuẩn hóa & hash — PHẢI khớp đúng với calculate_content_hash() trong
# ARCHITECTURE_SYSTEM2.md mục 3, để hash tính ra giống nhau dù ai chạy.
# ---------------------------------------------------------------------------

def fold(text: str | None) -> str:
    """Bỏ dấu tiếng Việt, hạ thường — dùng cho normalized_name."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    return stripped.lower().strip()


def calculate_content_hash(data: dict) -> str:
    """SHA-256 trên toàn bộ nội dung nghiệp vụ cốt lõi (đúng bản chốt V3)."""
    payload = {
        "proc_code": data.get("proc_code"),
        "name": (data.get("name") or "").strip(),
        "province": data.get("province"),
        "description": (data.get("description") or "").strip(),
        "authority": (data.get("authority") or "").strip(),
        "application_method": (data.get("application_method") or "").strip(),
        "receiving_location": (data.get("receiving_location") or "").strip(),
        "online_url": (data.get("online_url") or "").strip(),
        "meta_source": (data.get("meta_source") or "").strip(),
        "effective_date": str(data.get("effective_date") or ""),
        "checklists": sorted(
            f"{c.get('item_type')}:{(c.get('content') or '').strip()}"
            for c in data.get("checklists", [])
        ),
        "fees": sorted(
            f"{f.get('fee_type')}:{(f.get('amount_text') or '').strip()}:{f.get('condition') or ''}"
            for f in data.get("fees", [])
        ),
        "files": sorted(
            f"{fl.get('file_name')}:{fl.get('download_url')}"
            for fl in data.get("files", [])
        ),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# DB init
# ---------------------------------------------------------------------------

def init_db(db_path: Path, schema_path: Path) -> None:
    if db_path.exists():
        sys.exit(f"'{db_path}' đã tồn tại — xóa file đó trước nếu muốn tạo lại từ đầu.")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()
    print(f"Đã tạo {db_path}")


# ---------------------------------------------------------------------------
# Upsert 1 thủ tục theo luật versioning (mục 3, ARCHITECTURE_SYSTEM2.md)
# ---------------------------------------------------------------------------

def upsert_procedure(conn: sqlite3.Connection, data: dict, dry_run: bool = False) -> str:
    proc_code = data["proc_code"]
    province = data.get("province")
    new_hash = calculate_content_hash(data)

    cur = conn.execute(
        "SELECT id, content_hash FROM procedures "
        "WHERE proc_code = ? AND IFNULL(province,'ALL') = IFNULL(?, 'ALL') AND status='active'",
        (proc_code, province),
    )
    existing = cur.fetchone()

    if existing and existing[1] == new_hash:
        return "skip"

    if dry_run:
        return "archive+insert" if existing else "insert"

    if existing:
        conn.execute(
            "UPDATE procedures SET status='archived', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (existing[0],),
        )

    cur = conn.execute(
        """INSERT INTO procedures
           (proc_code, name, normalized_name, domain, level, province, description,
            duration_desc, authority, application_method, receiving_location, online_url,
            meta_source, effective_date, expiration_date,
            status, content_hash)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)""",
        (
            proc_code,
            data["name"],
            fold(data["name"]),
            data["domain"],
            data.get("level"),
            province,
            data.get("description"),
            data.get("duration_desc"),
            data.get("authority"),
            data.get("application_method"),
            data.get("receiving_location"),
            data.get("online_url"),
            data.get("meta_source"),
            data.get("effective_date"),
            data.get("expiration_date"),
            new_hash,
        ),
    )
    new_id = cur.lastrowid

    for order, c in enumerate(data.get("checklists", []), 1):
        conn.execute(
            "INSERT INTO procedure_checklists (procedure_id, step_order, item_type, content, note) "
            "VALUES (?,?,?,?,?)",
            (new_id, c.get("step_order", order), c["item_type"], c["content"], c.get("note")),
        )
    for f in data.get("fees", []):
        conn.execute(
            "INSERT INTO procedure_fees (procedure_id, fee_type, amount_text, condition) "
            "VALUES (?,?,?,?)",
            (new_id, f["fee_type"], f["amount_text"], f.get("condition")),
        )
    for fl in data.get("files", []):
        conn.execute(
            "INSERT INTO procedure_files (procedure_id, file_name, download_url, file_size) "
            "VALUES (?,?,?,?)",
            (new_id, fl["file_name"], fl["download_url"], fl.get("file_size")),
        )

    return "archive+insert" if existing else "insert"


def import_batch(conn: sqlite3.Connection, records: list[dict], dry_run: bool = False) -> None:
    counts = {"insert": 0, "archive+insert": 0, "skip": 0}
    for i, rec in enumerate(records, 1):
        try:
            action = upsert_procedure(conn, rec, dry_run=dry_run)
        except Exception as e:
            print(f"[{i}/{len(records)}] LỖI ở '{rec.get('name', '?')}': {e}")
            raise
        counts[action] += 1
        print(f"[{i}/{len(records)}] {action:<14} {rec.get('proc_code')} — {rec.get('name')}")
    if not dry_run:
        conn.commit()
    print(f"\nTổng: {len(records)} · mới {counts['insert']} · "
          f"cập nhật (archive+insert) {counts['archive+insert']} · giữ nguyên {counts['skip']}"
          + (" · [DRY RUN — chưa ghi DB]" if dry_run else ""))


# ---------------------------------------------------------------------------
# Chuyển đổi định dạng cũ (../data/normalized_procedures.json, 70 thủ tục có sẵn
# — scrape trước đó cho hệ RAG cũ) sang định dạng chuẩn ở trên.
#
# CẢNH BÁO CHẤT LƯỢNG DỮ LIỆU (đọc README.md mục "Dữ liệu có sẵn" trước khi
# dùng làm dữ liệu thật cho demo/mentor):
#   - Không có proc_code chính thức từ dichvucong.gov.vn -> dùng "LEGACY-<procedure_id>"
#     làm mã tạm, PHẢI thay bằng mã thật khi crawler/ chạy xong.
#   - Không có meta_source (căn cứ pháp lý) / effective_date -> để trống, UI sẽ
#     không hiện được dòng "Căn cứ: ..." cho các thủ tục này.
#   - `authority` (cơ quan có thẩm quyền) -> ĐỂ TRỐNG (None) cho toàn bộ 70 thủ tục
#     này: data cũ KHÔNG có trường tên cơ quan riêng, chỉ có "receiving_location"
#     (mang sang `receiving_location`, xem dưới). Trước 22/09/2026 importer nhét
#     nhầm receiving_location vào authority — ĐÃ SỬA (yêu cầu Leader, tách rõ 2
#     khái niệm "cơ quan có thẩm quyền" vs "địa điểm tiếp nhận hồ sơ").
#   - `receiving_location` lấy nguyên văn "receiving_location" trong data cũ —
#     CHẤT LƯỢNG KHÔNG ĐỀU: phần lớn hard-code theo MỘT phường cụ thể ("...
#     phường Tăng Nhơn Phú") — đúng cho nơi đã scrape, nhưng KHÔNG tổng quát cho
#     người dùng ở tỉnh/phường khác dù đây là thủ tục cấp quốc gia (Luật Hộ
#     tịch); một số khác lại là TÊN CƠ QUAN chung chung (vd "Cục quản lý xuất
#     nhập cảnh") chứ không phải địa chỉ. Không dùng nguyên văn cho bản demo
#     cuối — cần crawler/ cào lại đúng 2 trường tách biệt.
#   - `application_method` lấy nguyên văn "application_method" — SẠCH, dùng
#     được ngay (chỉ 3 giá trị: "Trực tiếp" | "Trực tuyến" | "Cả hai").
#   - `online_url`: KHÔNG có trong data cũ -> luôn None, chờ crawler/.
#   - Không có `files` (biểu mẫu) — bảng procedure_files sẽ rỗng cho các thủ tục này.
# ---------------------------------------------------------------------------

def load_legacy_normalized(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for item in raw:
        fee_list = []
        for f in item.get("fees", []):
            cond = f.get("condition")
            fee_list.append({
                "fee_type": "Lệ phí",
                "amount_text": f.get("amount_text", ""),
                "condition": None if cond in (None, "Default") else cond,
            })
        checklist = []
        for d in item.get("required_documents", []):
            cond = d.get("condition")
            checklist.append({
                "item_type": "giay_to_phai_nop",
                "content": d.get("document_name", ""),
                "note": None if cond in (None, "Default") else cond,
            })
        out.append({
            "proc_code": f"LEGACY-{item['procedure_id']}",
            "name": item["name"],
            "domain": item.get("field") or "Khác",
            "level": None,
            "province": None,
            "description": None,
            "duration_desc": (item.get("processing_time") or {}).get("text"),
            "authority": None,
            "application_method": item.get("application_method"),
            "receiving_location": item.get("receiving_location"),
            "online_url": None,
            "meta_source": None,
            "effective_date": None,
            "expiration_date": None,
            "checklists": checklist,
            "fees": fee_list,
            "files": [],
        })
    return out


def load_standard(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_and_load(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw and "procedure_id" in raw[0] and "proc_code" not in raw[0]:
        print(f"Nhận diện: định dạng CŨ (normalized_procedures.json) — {len(raw)} thủ tục. "
              f"Đọc cảnh báo chất lượng dữ liệu ở đầu load_legacy_normalized() trước khi dùng làm demo thật.")
        return load_legacy_normalized(path)
    print(f"Nhận diện: định dạng CHUẨN — {len(raw)} thủ tục.")
    return raw


# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    p.add_argument("--init", action="store_true", help="Tạo DB mới từ schema.sql")
    p.add_argument("--seed", help="File JSON để nạp (tự nhận diện định dạng)")
    p.add_argument("--dry-run", action="store_true", help="Không ghi DB, chỉ in log")
    args = p.parse_args()

    if args.init:
        init_db(Path(args.db), Path(args.schema))

    if args.seed:
        db_path = Path(args.db)
        if not db_path.exists():
            sys.exit(f"Chưa có DB '{db_path}' — chạy 'python importer.py --init' trước.")
        records = detect_and_load(Path(args.seed))
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            import_batch(conn, records, dry_run=args.dry_run)
        finally:
            conn.close()

    if not args.init and not args.seed:
        p.print_help()


if __name__ == "__main__":
    main()

-- ══════════════════════════════════════════════════════════════════════════
-- CSDL THỦ TỤC HÀNH CHÍNH — Phase 1  (bản 2: hỗ trợ MCQ + vòng đời hết hạn)
--
-- TÁCH RIÊNG khỏi Database/schema.sql (app.db). app.db chứa tài khoản + lịch sử
-- chat người dùng thật; file này chỉ chứa dữ liệu công khai, dựng lại được từ
-- staging/procedures.jsonl trong ~10 giây.
--
-- VÒNG ĐỜI BẢN GHI (cột `status`):
--   active   — bản hiện hành, là bản DUY NHẤT được tra cứu
--   archived — nội dung đổi, bản cũ giữ lại để tra ngược
--   expired  — biến mất khỏi danh mục cổng ⇒ coi như hết hiệu lực (tombstone)
-- KHÔNG BAO GIỜ DELETE. "Xoá thủ tục hết hạn" = chuyển sang status='expired',
-- ẩn khỏi tra cứu nhưng vẫn còn trong DB để giải thích với người dùng.
-- ══════════════════════════════════════════════════════════════════════════

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS procedures (
    -- Khoá KỸ THUẬT, tự tăng — tách rời khỏi mã nghiệp vụ (proc_id).
    row_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Mã NGHIỆP VỤ của nhà nước, vd '2.000635'. KHÔNG dùng làm khoá chính vì
    -- một mã có nhiều phiên bản (active / archived / expired).
    proc_id             TEXT NOT NULL,
    -- Tỉnh/thành sở hữu bản địa phương hoá. NULL = bản dùng chung toàn quốc.
    -- Để NULL cho tới khi CHỨNG MINH được cổng có bản riêng theo tỉnh
    -- (xem PHASE1_PLAN.md §13 — quyết định "thà thiếu còn hơn bịa").
    province            TEXT DEFAULT NULL,

    source_id           TEXT NOT NULL DEFAULT '',
    name                TEXT NOT NULL,
    domain              TEXT NOT NULL DEFAULT '',   -- TÊN THẬT của cổng
    description         TEXT NOT NULL DEFAULT '',
    requirements        TEXT NOT NULL DEFAULT '',
    results             TEXT NOT NULL DEFAULT '',
    executing_agency    TEXT NOT NULL DEFAULT '',
    -- Địa điểm nộp hồ sơ TRỰC TIẾP (dòng "Địa điểm tiếp nhận" của UI).
    receiving_address   TEXT NOT NULL DEFAULT '',
    coordinating_agency TEXT NOT NULL DEFAULT '',
    department_promulgate TEXT NOT NULL DEFAULT '',
    department_code     TEXT NOT NULL DEFAULT '',
    agency_levels       TEXT NOT NULL DEFAULT '',
    subject_types       TEXT NOT NULL DEFAULT '',   -- bản gộp, để hiển thị nhanh
    keywords            TEXT NOT NULL DEFAULT '',
    state               TEXT NOT NULL DEFAULT '',   -- ACTIVE/UPDATED của cổng

    -- Thời gian giải quyết: gộp từ 2 nguồn (executionMethods + cases[]).
    processing_time_text TEXT NOT NULL DEFAULT '',

    portal_url          TEXT NOT NULL DEFAULT '',
    online_url          TEXT NOT NULL DEFAULT '',
    has_online_submission INTEGER NOT NULL DEFAULT 0,

    -- meta: "luật từ ngày nào, ai ban hành"
    decision_number     TEXT NOT NULL DEFAULT '',
    decision_date       TEXT NOT NULL DEFAULT '',
    publication_date    TEXT NOT NULL DEFAULT '',
    issuing_agency      TEXT NOT NULL DEFAULT '',
    source_updated_at   TEXT NOT NULL DEFAULT '',
    source_created_at   TEXT NOT NULL DEFAULT '',

    -- ba trạng thái: present | absent_confirmed | unknown
    status_fees         TEXT NOT NULL DEFAULT 'unknown',
    status_files        TEXT NOT NULL DEFAULT 'unknown',
    status_checklist    TEXT NOT NULL DEFAULT 'unknown',
    status_description  TEXT NOT NULL DEFAULT 'unknown',
    status_legal        TEXT NOT NULL DEFAULT 'unknown',
    status_meta         TEXT NOT NULL DEFAULT 'unknown',
    status_online       TEXT NOT NULL DEFAULT 'unknown',
    status_address      TEXT NOT NULL DEFAULT 'unknown',
    status_processing_time TEXT NOT NULL DEFAULT 'unknown',

    search_text         TEXT NOT NULL DEFAULT '',   -- đã bỏ dấu + xử lý đ/Đ
    content_hash        TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    status              TEXT NOT NULL DEFAULT 'active',  -- active|archived|expired
    scraped_at          TEXT NOT NULL,
    -- Lần gần nhất thủ tục này còn xuất hiện trong danh mục cổng.
    last_seen_at        TEXT NOT NULL DEFAULT '',
    archived_at         TEXT NOT NULL DEFAULT '',
    expired_at          TEXT NOT NULL DEFAULT '',
    -- Vì sao coi là hết hạn. Cổng KHÔNG công bố ngày hết hiệu lực, nên đây là
    -- ngày MÌNH PHÁT HIỆN nó biến mất — phải nói thẳng như vậy với người dùng.
    expiry_note         TEXT NOT NULL DEFAULT ''
);

-- Đúng đề xuất của nhóm: khoá chính chống xung đột theo (mã, tỉnh).
-- IFNULL(province,'ALL') để bản toàn quốc vẫn tham gia ràng buộc duy nhất.
-- Chỉ áp cho bản 'active' ⇒ lưu vô hạn bản archived/expired mà không trùng khoá.
CREATE UNIQUE INDEX IF NOT EXISTS idx_proc_active
    ON procedures(proc_id, IFNULL(province, 'ALL')) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_proc_id      ON procedures(proc_id);
CREATE INDEX IF NOT EXISTS idx_proc_domain  ON procedures(domain);
CREATE INDEX IF NOT EXISTS idx_proc_dept    ON procedures(department_code, status);
CREATE INDEX IF NOT EXISTS idx_proc_hash    ON procedures(content_hash);
CREATE INDEX IF NOT EXISTS idx_proc_status  ON procedures(status, last_seen_at);

-- ── MCQ: "bạn thuộc trường hợp nào?" ──────────────────────────────────────
-- Mỗi executionCase là MỘT LỰA CHỌN MCQ, kèm bộ hồ sơ riêng.
-- Trước đây bị làm phẳng vào checklist_items.case_name ⇒ mất trục phân nhánh.
CREATE TABLE IF NOT EXISTS procedure_cases (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    ordinal       INTEGER NOT NULL DEFAULT 0,
    case_name     TEXT NOT NULL DEFAULT '',   -- câu đầy đủ, KHÔNG rút gọn
    n_components  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_case_row ON procedure_cases(row_id);

-- ── MCQ: "bạn là ai?" ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS procedure_subjects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    subject_name  TEXT NOT NULL DEFAULT '',
    subject_code  TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_subject_row ON procedure_subjects(row_id);

-- ── Dịch vụ công trực tuyến gắn với thủ tục (cases[] của cổng) ────────────
-- Mỗi cái có MÃ RIÊNG (vd 2.000635.02) và thời hạn riêng.
CREATE TABLE IF NOT EXISTS online_services (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id         INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    service_code   TEXT NOT NULL DEFAULT '',
    service_name   TEXT NOT NULL DEFAULT '',
    processing_qty INTEGER NOT NULL DEFAULT 0,
    processing_unit TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_service_row ON online_services(row_id);

CREATE TABLE IF NOT EXISTS procedure_fees (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    fee_type      TEXT NOT NULL DEFAULT '',
    amount_value  REAL,                       -- NULL = nguồn không ghi số
    amount_text   TEXT NOT NULL DEFAULT '',   -- vd "Mức thu bằng 50% ... TT 249/2016"
    currency_id   TEXT NOT NULL DEFAULT '',
    submission_method TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_fee_row ON procedure_fees(row_id);

-- Thành phần hồ sơ (GIẤY TỜ phải nộp) — khác với "checklist việc cần làm",
-- cái đó dựng từ procedure_steps.
CREATE TABLE IF NOT EXISTS checklist_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    ordinal       INTEGER NOT NULL DEFAULT 0,
    case_ordinal  INTEGER NOT NULL DEFAULT -1,  -- khớp procedure_cases.ordinal
    case_name     TEXT NOT NULL DEFAULT '',
    name          TEXT NOT NULL DEFAULT '',
    code          TEXT NOT NULL DEFAULT '',
    required      INTEGER NOT NULL DEFAULT 0,
    original_qty  INTEGER NOT NULL DEFAULT 0,
    copy_qty      INTEGER NOT NULL DEFAULT 0,
    has_electronic_form INTEGER NOT NULL DEFAULT 0,
    n_attachments INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_check_row ON checklist_items(row_id);
CREATE INDEX IF NOT EXISTS idx_check_case ON checklist_items(row_id, case_ordinal);

CREATE TABLE IF NOT EXISTS procedure_files (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    file_id       TEXT NOT NULL,     -- POST preview-attachment {fileId} mới tải được
    file_name     TEXT NOT NULL DEFAULT '',
    bucket_name   TEXT NOT NULL DEFAULT '',
    remote_path   TEXT NOT NULL DEFAULT '',
    local_path    TEXT NOT NULL DEFAULT '',
    -- 0 = có metadata nhưng KHÔNG tải được (cổng trả 0 byte). UI đừng hiện nút tải.
    file_available INTEGER NOT NULL DEFAULT 0,
    belongs_to    TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_file_row ON procedure_files(row_id);

CREATE TABLE IF NOT EXISTS procedure_steps (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    ordinal       INTEGER NOT NULL DEFAULT 0,
    name          TEXT NOT NULL DEFAULT '',
    description   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_step_row ON procedure_steps(row_id);

CREATE TABLE IF NOT EXISTS procedure_methods (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    submission_method    TEXT NOT NULL DEFAULT '',
    processing_time_qty  REAL NOT NULL DEFAULT 0,   -- nguồn trả cả int/float/str
    processing_time_unit TEXT NOT NULL DEFAULT '',
    processing_time_text TEXT NOT NULL DEFAULT '',
    description          TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_method_row ON procedure_methods(row_id);

CREATE TABLE IF NOT EXISTS legal_basis (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id        INTEGER NOT NULL REFERENCES procedures(row_id) ON DELETE CASCADE,
    doc_code      TEXT NOT NULL DEFAULT '',   -- vd '04/2020/TT-BTP'
    doc_name      TEXT NOT NULL DEFAULT '',
    doc_year      TEXT NOT NULL DEFAULT ''    -- moi ra từ số hiệu, để xếp mới/cũ
);
CREATE INDEX IF NOT EXISTS idx_legal_row ON legal_basis(row_id);

-- ── Tra cứu toàn văn ──────────────────────────────────────────────────────
-- ⚠️ tokenize KHÔNG dùng remove_diacritics: nó không xử lý được đ/Đ (U+0111 là
-- CHỮ CÁI riêng, không tách NFD được). Ta tự fold trong Python rồi nạp vào đây.
-- Truy vấn PHẢI fold câu hỏi bằng textutil.fold() trước khi MATCH.
CREATE VIRTUAL TABLE IF NOT EXISTS procedures_fts USING fts5(
    proc_id UNINDEXED,
    row_id  UNINDEXED,
    search_text,
    name_folded,
    description_folded,
    tokenize = 'unicode61'
);

CREATE TABLE IF NOT EXISTS import_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at        TEXT NOT NULL,
    n_input       INTEGER NOT NULL DEFAULT 0,
    n_inserted    INTEGER NOT NULL DEFAULT 0,
    n_updated     INTEGER NOT NULL DEFAULT 0,
    n_unchanged   INTEGER NOT NULL DEFAULT 0,
    n_expired     INTEGER NOT NULL DEFAULT 0,
    note          TEXT NOT NULL DEFAULT ''
);

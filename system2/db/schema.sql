-- System 2 — Structured Local Database Retrieval
-- Schema chốt V3 (17/09-21/09/2026), theo docs/ARCHITECTURE_SYSTEM2.md
-- SQLite FTS5. Không sửa file này ngoài quy trình chốt lại architecture.

PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. BẢNG THỦ TỤC CHÍNH (PROCEDURES)
-- ============================================================================
CREATE TABLE procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,    -- Khóa chính kỹ thuật cho mỗi version
    proc_code VARCHAR(64) NOT NULL,          -- Mã Dịch vụ công nghiệp vụ (vd: 'T-BTP-282384-TT')
    name VARCHAR(512) NOT NULL,              -- Tên đầy đủ của thủ tục
    normalized_name VARCHAR(512),            -- Tên không dấu hỗ trợ tìm kiếm
    domain VARCHAR(128) NOT NULL,            -- Lĩnh vực (Hộ tịch, Đất đai, Hộ chiếu...)
    level VARCHAR(64),                       -- Cấp thực hiện (Cấp xã, Cấp huyện, Cấp tỉnh)
    province VARCHAR(64) DEFAULT NULL,       -- Tỉnh/thành áp dụng (NULL = toàn quốc)
    description TEXT,                        -- Giải thích tổng quan về thủ tục
    duration_desc VARCHAR(255),              -- Thời hạn giải quyết tóm tắt (vd: '3 ngày làm việc')
    authority VARCHAR(255),                  -- Cơ quan có thẩm quyền tiếp nhận/giải quyết
    meta_source TEXT,                        -- Căn cứ pháp lý (Luật, Nghị định ban hành)
    effective_date DATE,                     -- Ngày bắt đầu có hiệu lực
    expiration_date DATE,                    -- Ngày hết hiệu lực (nếu có)
    status VARCHAR(32) DEFAULT 'active',     -- 'active' (đang áp dụng), 'archived' (lịch sử)
    content_hash CHAR(64) NOT NULL,          -- SHA-256 toàn bộ payload để kiểm soát phiên bản
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ràng buộc: Mỗi cặp (proc_code, province) chỉ được có DUY NHẤT 1 bản ghi 'active'
CREATE UNIQUE INDEX idx_proc_unique_active
ON procedures(proc_code, IFNULL(province, 'ALL'))
WHERE status = 'active';

CREATE INDEX idx_proc_code ON procedures(proc_code);
CREATE INDEX idx_proc_province ON procedures(province);

-- ============================================================================
-- 2. BẢNG CHECKLIST HỒ SƠ & TRÌNH TỰ (PROCEDURE_CHECKLISTS)
-- ============================================================================
CREATE TABLE procedure_checklists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id INTEGER NOT NULL REFERENCES procedures(id) ON DELETE CASCADE,
    step_order INT DEFAULT 1,                -- Thứ tự bước / nhóm hồ sơ
    item_type VARCHAR(32) NOT NULL,          -- 'giay_to_phai_nop', 'giay_to_xuat_trinh', 'cac_buoc'
    content TEXT NOT NULL,                   -- Chi tiết giấy tờ/bước thực hiện
    note TEXT                                -- Ghi chú (bản chính, photo, công chứng)
);

CREATE INDEX idx_checklists_proc_id ON procedure_checklists(procedure_id);

-- ============================================================================
-- 3. BẢNG LỆ PHÍ & CHI PHÍ (PROCEDURE_FEES)
-- ============================================================================
CREATE TABLE procedure_fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id INTEGER NOT NULL REFERENCES procedures(id) ON DELETE CASCADE,
    fee_type VARCHAR(255) NOT NULL,          -- Tên khoản thu (Lệ phí, Phí thẩm định...)
    amount_text VARCHAR(128) NOT NULL,       -- Mức thu (vd: 'Miễn phí', '50.000 VNĐ')
    condition TEXT                           -- Điều kiện áp dụng / miễn giảm
);

CREATE INDEX idx_fees_proc_id ON procedure_fees(procedure_id);

-- ============================================================================
-- 4. BẢNG BIỂU MẪU & FILE ĐÍNH KÈM (PROCEDURE_FILES)
-- ============================================================================
CREATE TABLE procedure_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id INTEGER NOT NULL REFERENCES procedures(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,         -- Tên biểu mẫu (vd: 'To_khai_ket_hon.docx')
    download_url TEXT NOT NULL,              -- Link tải file gốc từ Cổng DVC
    file_size VARCHAR(64)
);

CREATE INDEX idx_files_proc_id ON procedure_files(procedure_id);

-- ============================================================================
-- 5. BẢNG ẢO FULL-TEXT SEARCH (FTS5) & TRIGGERS ĐỒNG BỘ TỰ ĐỘNG
-- ============================================================================
CREATE VIRTUAL TABLE procedures_fts USING fts5(
    procedure_id UNINDEXED,                  -- Lưu procedures.id
    name,
    normalized_name,
    description,
    authority,
    tokenize = 'unicode61 remove_diacritics 2'
);

-- Trigger 1: Tự động thêm vào FTS khi có bản ghi mới ở trạng thái 'active'
CREATE TRIGGER trg_procedures_after_insert AFTER INSERT ON procedures
WHEN NEW.status = 'active'
BEGIN
    INSERT INTO procedures_fts(procedure_id, name, normalized_name, description, authority)
    VALUES (NEW.id, NEW.name, NEW.normalized_name, NEW.description, NEW.authority);
END;

-- Trigger 2: Khi cập nhật trạng thái (Active -> Archived), tự gỡ khỏi FTS để không bị search trúng bản cũ
CREATE TRIGGER trg_procedures_after_update_status AFTER UPDATE OF status ON procedures
BEGIN
    -- Nếu chuyển sang archived: Xóa khỏi chỉ mục tìm kiếm
    DELETE FROM procedures_fts WHERE procedure_id = OLD.id AND NEW.status = 'archived';

    -- Nếu kích hoạt lại active: Thêm vào chỉ mục tìm kiếm
    INSERT INTO procedures_fts(procedure_id, name, normalized_name, description, authority)
    SELECT NEW.id, NEW.name, NEW.normalized_name, NEW.description, NEW.authority
    WHERE NEW.status = 'active' AND NOT EXISTS (SELECT 1 FROM procedures_fts WHERE procedure_id = NEW.id);
END;

-- Trigger 3: Tự động xóa khỏi FTS khi xóa cứng bản ghi trong procedures
CREATE TRIGGER trg_procedures_after_delete AFTER DELETE ON procedures
BEGIN
    DELETE FROM procedures_fts WHERE procedure_id = OLD.id;
END;

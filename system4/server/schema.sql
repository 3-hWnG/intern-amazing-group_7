-- System 4: SQLite riêng (không đụng server/runtime/system3.db của System 3)
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'user',      -- dev | user
  disabled      INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash  TEXT PRIMARY KEY,                    -- sha256 của cookie, không lưu cookie gốc
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at  TEXT NOT NULL
);
-- Hội thoại Strict (nằm trong DB System 3): ai sở hữu
CREATE TABLE IF NOT EXISTS strict_owner (
  conversation_id TEXT PRIMARY KEY,
  user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
-- Hội thoại Strict có từ trước khi có đăng nhập -> thuộc tài khoản dev đầu tiên
CREATE TABLE IF NOT EXISTS strict_legacy (
  conversation_id TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL DEFAULT ''
);
-- Hội thoại Friendly
CREATE TABLE IF NOT EXISTS conversations (
  id          TEXT PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
  pinned      INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  current_leaf INTEGER,                            -- tin cuối của nhánh đang xem (NV2: phiên bản ‹ 1/2 ›)
  summary     TEXT NOT NULL DEFAULT '',            -- tóm tắt phần đầu hội thoại dài (NV2)
  summary_upto INTEGER NOT NULL DEFAULT 0          -- tóm tắt bao phủ tới tin này (theo nhánh)
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
CREATE TABLE IF NOT EXISTS messages (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role            TEXT NOT NULL,                   -- user | assistant
  content         TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL DEFAULT 'done',    -- done | error | stopped
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  parent_id       INTEGER,                         -- tin đứng trước (NULL = tin đầu); cùng cha = các phiên bản
  meta            TEXT NOT NULL DEFAULT '{}',      -- JSON: choices (hỏi lại), guard, leak, memory...
  feedback        INTEGER NOT NULL DEFAULT 0       -- 1 = 👍, -1 = 👎
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);
-- Bộ nhớ dài hạn của từng người (NV2)
CREATE TABLE IF NOT EXISTS memories (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  text        TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_mem_user ON memories(user_id);
CREATE TABLE IF NOT EXISTS user_prefs (
  user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  memory_mode TEXT NOT NULL DEFAULT ''             -- auto | explicit | '' = theo cài đặt chung
);
-- Bộ dữ liệu người dùng tải lên (NV3)
CREATE TABLE IF NOT EXISTS datasets (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  filename    TEXT NOT NULL,
  size_bytes  INTEGER NOT NULL DEFAULT 0,
  kind        TEXT NOT NULL DEFAULT '',            -- table (khớp cấu trúc) | rows (không khớp, lưu dạng dòng chữ) | text (văn bản chia đoạn)
  status      TEXT NOT NULL DEFAULT 'queued',      -- queued | processing | ready | error
  progress    INTEGER NOT NULL DEFAULT 0,
  message     TEXT NOT NULL DEFAULT '',
  mapping     TEXT NOT NULL DEFAULT '{}',          -- JSON: cột tiêu đề, cột bỏ qua, số trường...
  n_records   INTEGER NOT NULL DEFAULT 0,
  active      INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ds_user ON datasets(user_id);
-- Cấu trúc định sẵn: một bản ghi = tiêu đề + các trường + chữ để tìm + nguồn
CREATE TABLE IF NOT EXISTS records (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  dataset_id  INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
  title       TEXT NOT NULL DEFAULT '',
  fields      TEXT NOT NULL DEFAULT '{}',          -- JSON {tên trường: giá trị}
  text        TEXT NOT NULL DEFAULT '',
  source      TEXT NOT NULL DEFAULT ''             -- tệp · trang tính · dòng / trang
);
CREATE INDEX IF NOT EXISTS idx_rec_ds ON records(dataset_id);
-- Tìm theo từ khoá (không phân biệt dấu); rowid = records.id
CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(title, text, tokenize='unicode61 remove_diacritics 2');
-- Phiên bản cho hội thoại Strict (NV4, 1A): cây tin nhắn do System 4 giữ; nội dung vẫn nằm trong DB System 3.
-- Một "luồng" = hội thoại System 3 gốc (root, hiện trong danh sách) + các hội thoại phụ (nhánh) tạo ra khi sửa / tạo lại.
CREATE TABLE IF NOT EXISTS strict_nodes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  root        TEXT NOT NULL,
  parent_id   INTEGER,
  role        TEXT NOT NULL,                     -- user | assistant
  kind        TEXT NOT NULL DEFAULT '',          -- reset = tin "Đã bắt đầu chủ đề mới"
  s3_cid      TEXT NOT NULL,                     -- hội thoại System 3 chứa tin này
  s3_mid      INTEGER NOT NULL,                  -- id tin trong System 3
  replied     INTEGER NOT NULL DEFAULT 0,        -- tin người dùng trả lời thẻ hỏi lại ngay trước nó
  feedback    INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sn_root ON strict_nodes(root);
CREATE TABLE IF NOT EXISTS strict_threads (root TEXT PRIMARY KEY, leaf INTEGER);
CREATE TABLE IF NOT EXISTS strict_branch (cid TEXT PRIMARY KEY, root TEXT NOT NULL);
-- Bộ công cụ dev: chi tiết từng câu trả lời Friendly (tìm kiếm, lời dặn, suy nghĩ ẩn, kiểm soát, thời gian). Giữ TRACE_KEEP câu gần nhất.
CREATE TABLE IF NOT EXISTS traces (
  message_id      INTEGER PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  user_id         INTEGER NOT NULL,
  data            TEXT NOT NULL,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

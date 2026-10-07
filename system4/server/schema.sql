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

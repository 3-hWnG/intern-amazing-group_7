-- System 3: SQLite riêng (KHÔNG liên quan app.db / schema.sql của V10.6)
-- FINAL-PRODUCT: [B4] chưa có cột chủ sở hữu (user_id); thêm khi có đăng nhập (mục 3)
CREATE TABLE IF NOT EXISTS conversations (
  id          TEXT PRIMARY KEY,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  title       TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
  pinned      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role            TEXT NOT NULL,              -- user | assistant
  content         TEXT NOT NULL DEFAULT '',   -- user: text; assistant: văn bản phẳng (gộp blocks)
  kind            TEXT NOT NULL DEFAULT '',   -- answer | clarify | apologize | chitchat | error ...
  -- FINAL-PRODUCT: [B3][B2] plan_json và content chưa che PII; plan chỉ dev được xem (mục 1, 2)
  plan_json       TEXT NOT NULL DEFAULT '',
  sources_json    TEXT NOT NULL DEFAULT '',   -- assistant: JSON {blocks:[{title,text,sources}], clarify}
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, id);
CREATE TABLE IF NOT EXISTS session_facts (
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  kind            TEXT NOT NULL,
  text            TEXT NOT NULL,
  proc_id         TEXT NOT NULL DEFAULT '',   -- thủ tục lúc ghi; '' = fact cũ/không gắn
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (conversation_id, kind, text)
);
CREATE TABLE IF NOT EXISTS shown_procedures (
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  proc_id         TEXT NOT NULL,
  label           TEXT NOT NULL DEFAULT '',
  ordinal         INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (conversation_id, proc_id)
);
CREATE TABLE IF NOT EXISTS turn_traces (
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  message_id      INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  trace_json      TEXT NOT NULL DEFAULT '',
  total_ms        INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (conversation_id, message_id)
);
CREATE TABLE IF NOT EXISTS conv_state (
  conversation_id TEXT PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
  state_json      TEXT NOT NULL DEFAULT '{}',   -- ConvState: topic, history, order, fields, story
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Phase 26: bộ nhớ người dùng theo thiết bị (client_id do trình duyệt cấp). key: profile.province|commune|user_type|note, mcq.subject
-- FINAL-PRODUCT: [B4][MEM] client_id tự khai, chưa có tài khoản; bản cuối đổi cột client_id thành user_id đăng nhập (mục 6)
CREATE TABLE IF NOT EXISTS user_memory (
  client_id  TEXT NOT NULL,
  key        TEXT NOT NULL,
  value      TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (client_id, key)
);

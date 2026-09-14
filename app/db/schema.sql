PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name  TEXT NOT NULL DEFAULT '',
    is_admin      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    user_agent TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_auth_user ON auth_sessions(user_id);

CREATE TABLE IF NOT EXISTS login_attempts (
    email      TEXT NOT NULL,
    attempt_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempt ON login_attempts(email, attempt_at);

CREATE TABLE IF NOT EXISTS conversations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    summary       TEXT DEFAULT '',
    summary_upto  INTEGER DEFAULT 0,
    pending_json  TEXT DEFAULT '',
    last_row_id   INTEGER DEFAULT -1,
    archived      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    tier            TEXT DEFAULT '',
    confidence      REAL DEFAULT 0,
    sources         TEXT DEFAULT '',
    factcheck       TEXT DEFAULT '',
    token_estimate  INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);

CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    verdict    TEXT NOT NULL,
    note       TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    conversation_id INTEGER,
    status          TEXT NOT NULL,
    enqueued_at     TEXT NOT NULL,
    wait_ms         INTEGER DEFAULT 0,
    process_ms      INTEGER DEFAULT 0,
    queue_position  INTEGER DEFAULT 0
);

-- ==========================================================================
-- TÀI LIỆU (v6) — dataset nội bộ và tệp người dùng đính kèm dùng CHUNG lược đồ
-- scope='global'       : luôn tra được ở mọi hội thoại, đánh chỉ mục MỘT LẦN
-- scope='conversation' : chỉ tra được trong đúng cuộc trò chuyện đó
-- ==========================================================================
CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scope           TEXT NOT NULL DEFAULT 'conversation',
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    mime_type       TEXT DEFAULT '',
    storage_path    TEXT DEFAULT '',
    description     TEXT DEFAULT '',
    n_chunks        INTEGER DEFAULT 0,
    n_bytes         INTEGER DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending',
    error           TEXT DEFAULT '',
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doc_conv ON documents(conversation_id);
CREATE INDEX IF NOT EXISTS idx_doc_scope ON documents(scope);

CREATE TABLE IF NOT EXISTS document_chunks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ordinal       INTEGER NOT NULL DEFAULT 0,
    content       TEXT NOT NULL,
    metadata_json TEXT DEFAULT '',
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunk_doc ON document_chunks(document_id);

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

-- Bộ nhớ dài hạn theo NGƯỜI DÙNG (xuyên mọi cuộc trò chuyện)
CREATE TABLE IF NOT EXISTS user_profile (
    user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    province   TEXT DEFAULT '',
    ward       TEXT DEFAULT '',
    notes      TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    summary       TEXT DEFAULT '',
    summary_upto  INTEGER DEFAULT 0,
    archived      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at DESC);

-- kind: answer | clarify | chitchat | out_of_scope | no_evidence | error
-- verdict: PASS | FAIL | '' (không qua kiểm chứng)
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    kind            TEXT DEFAULT '',
    verdict         TEXT DEFAULT '',
    sources         TEXT DEFAULT '',
    intent_json     TEXT DEFAULT '',
    token_estimate  INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);

-- Evidence Pack của từng câu trả lời: chứng minh RAG + dữ liệu cho fine-tune
CREATE TABLE IF NOT EXISTS evidence (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id  INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    query       TEXT DEFAULT '',
    pack_json   TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_msg ON evidence(message_id);

-- Bối cảnh hội thoại có CẤU TRÚC cho câu hỏi nối tiếp ("vậy còn ... thì sao?").
-- Đây là GIẢ THUYẾT hiện tại, không phải sự thật vĩnh viễn: mỗi lượt ghi đè, và
-- quá STATE_MAX_AGE_TURNS lượt thì không dùng nữa.
CREATE TABLE IF NOT EXISTS conversation_state (
    conversation_id INTEGER PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
    domain          TEXT DEFAULT '',
    procedure_name  TEXT DEFAULT '',
    entities_json   TEXT DEFAULT '',
    province        TEXT DEFAULT '',
    ward            TEXT DEFAULT '',
    last_target     TEXT DEFAULT '',
    last_intent     TEXT DEFAULT '',
    updated_at_turn INTEGER DEFAULT 0,
    updated_at      TEXT NOT NULL
);

-- Nhật ký từng lượt: đủ để trả lời "câu trả lời sai này hỏng ở bước nào?"
-- (ngữ cảnh / ý định / mục tiêu / truy vấn / truy hồi / sinh văn bản / kiểm chứng)
CREATE TABLE IF NOT EXISTS turn_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    message_id      INTEGER,
    created_at      TEXT NOT NULL,
    model           TEXT DEFAULT '',
    user_question   TEXT NOT NULL,
    resolved_question TEXT DEFAULT '',
    intent          TEXT DEFAULT '',
    target          TEXT DEFAULT '',
    procedure_name  TEXT DEFAULT '',
    gate            TEXT DEFAULT '',
    route           TEXT DEFAULT '',
    kind            TEXT DEFAULT '',
    verdict         TEXT DEFAULT '',
    payload_json    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turnlog_conv ON turn_log(conversation_id, id);

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

-- Tệp người dùng đính kèm vào một cuộc trò chuyện
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

CREATE TABLE IF NOT EXISTS document_chunks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ordinal       INTEGER NOT NULL DEFAULT 0,
    content       TEXT NOT NULL,
    metadata_json TEXT DEFAULT '',
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunk_doc ON document_chunks(document_id);

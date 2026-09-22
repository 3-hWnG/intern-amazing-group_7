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
    archived      INTEGER NOT NULL DEFAULT 0,
    -- Hệ thống trả lời của cuộc trò chuyện này: websearch (HT1) | retrieval (HT2).
    -- Đổi hệ thống = mở cuộc trò chuyện MỚI, nên cột này không bao giờ đổi giữa chừng.
    system        TEXT NOT NULL DEFAULT 'websearch'
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at DESC);

-- kind: answer | not_in_sources | clarify | chitchat | out_of_scope | no_evidence | error
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

-- ══════════════════════════════════════════════════════════════════════════
-- HỆ THỐNG 2 (RETRIEVAL) — trạng thái giữa các lượt hỏi
-- ══════════════════════════════════════════════════════════════════════════

-- Vòng MCQ đang chờ người dùng trả lời.
-- Kiến trúc mới là: tra lần 1 -> hỏi MCQ -> tra lần 2. Một lượt HTTP không giữ
-- được trạng thái đó, nên phải ghi lại. Mỗi cuộc trò chuyện tối đa MỘT vòng
-- đang chờ (khoá chính là conversation_id) — hỏi câu mới thì vòng cũ bị ghi đè.
CREATE TABLE IF NOT EXISTS retrieval_pending (
    conversation_id INTEGER PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
    question        TEXT NOT NULL DEFAULT '',   -- câu hỏi GỐC của người dùng
    keys_json       TEXT NOT NULL DEFAULT '',   -- {primary_keyword, entities, domain}
    candidates_json TEXT NOT NULL DEFAULT '',   -- [{proc_id, name, domain}]
    proc_id         TEXT NOT NULL DEFAULT '',   -- đã chốt được thủ tục nào chưa
    axis            TEXT NOT NULL DEFAULT '',   -- procedure|case|subject|agency_level
    options_json    TEXT NOT NULL DEFAULT '',   -- các lựa chọn đang hiển thị
    picked_json     TEXT NOT NULL DEFAULT '{}', -- {axis: giá trị đã chọn}
    attempts        INTEGER NOT NULL DEFAULT 0, -- số lần LLM sinh lại khoá (tối đa 3)
    rounds          INTEGER NOT NULL DEFAULT 0, -- số vòng MCQ đã hỏi
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

-- Lựa chọn MCQ người dùng bảo "nhớ giúp tôi" (Proposal: "hỏi xem người dùng có
-- muốn nhớ lựa chọn để về sau đỡ phải chọn hay không").
--
-- CHỈ nhớ trục MÔ TẢ NGƯỜI DÙNG (tư cách, cấp nộp hồ sơ) — những thứ hiếm khi
-- đổi. TUYỆT ĐỐI không nhớ trục MÔ TẢ CÂU HỎI (thủ tục nào, trường hợp nào):
-- nhớ "lần trước chọn Đăng ký kết hôn" rồi áp cho câu hỏi sau là trả lời sai
-- thủ tục. Danh sách trục nhớ được: Database/pipeline/retrieval.MEMORABLE_AXES.
CREATE TABLE IF NOT EXISTS user_mcq_memory (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    axis       TEXT NOT NULL,
    value      TEXT NOT NULL,
    n_used     INTEGER NOT NULL DEFAULT 0,   -- đếm số lần đỡ được một câu hỏi
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcq_mem ON user_mcq_memory(user_id, axis);

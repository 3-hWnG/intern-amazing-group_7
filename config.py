"""Toàn bộ cấu hình hệ thống — đọc từ biến môi trường (hoặc file .env ở gốc).

Không hard-code: mọi giá trị bên dưới ghi đè được bằng biến môi trường CÙNG
TÊN, nên chạy local, chạy Docker hay đổi mô hình đều không phải sửa code.
Danh sách đầy đủ + giải thích: .env.example
"""

from __future__ import annotations

import os
from pathlib import Path

# ==========================================================================
# ĐƯỜNG DẪN THƯ MỤC (cấu trúc V10.3) / FOLDER LAYOUT (V10.3)
#
#   <gốc>/  config.py  .env  requirements.txt  Launch Web.bat
#           Backend/       mã nguồn server (FastAPI · orchestrator · MCP)
#           Frontend/      static/ (css, js) + templates/ (html)
#           Database/      schema.sql · corpus/ (nguồn) · runtime/ (app.db)
#           Evaluation/    kịch bản chấm điểm
#           Utility/       finetune/ · scripts/ (run.ps1 · setup.ps1)
#           Documentation/ · Extra/ · .venv/
#
# config.py ĐỂ Ở GỐC, ngoài Backend/ và Frontend/, để sửa cấu hình không phải
# đi tìm trong mã nguồn. / config.py lives at the ROOT on purpose.
# ==========================================================================
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "Backend"
FRONTEND_DIR = PROJECT_ROOT / "Frontend"
DATABASE_DIR = PROJECT_ROOT / "Database"
EVALUATION_DIR = PROJECT_ROOT / "Evaluation"
UTILITY_DIR = PROJECT_ROOT / "Utility"
DOCUMENTATION_DIR = PROJECT_ROOT / "Documentation"
EXTRA_DIR = PROJECT_ROOT / "Extra"

APP_DIR = BACKEND_DIR    # tên cũ của V10.2 — giữ lại để mã cũ không gãy


def _load_dotenv(path: Path) -> None:
    """Nạp .env tối giản (KEY=VALUE). Biến đã có trong môi trường được ưu tiên."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv(PROJECT_ROOT / ".env")


def _str(name: str, default: str) -> str:
    value = os.environ.get(name)
    return default if value is None else value.strip()


def _int(name: str, default: int) -> int:
    try:
        return int(_str(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(_str(name, str(default)))
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    return _str(name, "1" if default else "0").lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: str) -> list[str]:
    return [x.strip().lower() for x in _str(name, default).split(",") if x.strip()]


# Dữ liệu SỐNG (app.db + tệp tải lên). Đổi chỗ bằng biến môi trường RUNTIME_DIR.
RUNTIME_DIR = Path(_str("RUNTIME_DIR", str(DATABASE_DIR / "runtime")))
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
# Dữ liệu NGUỒN (xlsx/json/md). Dùng cho Evaluation + fine-tune, KHÔNG phải CSDL
# đang chạy. / Source corpus — used by Evaluation, not by the live app.
CORPUS_DIR = DATABASE_DIR / "corpus"

# ==========================================================================
# MÔ HÌNH (Ollama). Mục tiêu triển khai: 3–4B lượng tử hoá 4-bit.
# 1.5B để thử nhanh. Đổi mô hình = đổi LLM_MODEL, không sửa gì khác.
# ==========================================================================
OLLAMA_HOST = _str("OLLAMA_HOST", "http://127.0.0.1:11434")
LLM_MODEL = _str("LLM_MODEL", "qwen2.5:1.5b")
VERIFIER_MODEL = _str("VERIFIER_MODEL", "") or LLM_MODEL
LLM_NUM_CTX = _int("LLM_NUM_CTX", 8192)        # Ollama mặc định chỉ 2048-4096: không đủ chứa Evidence Pack
LLM_KEEP_ALIVE = _str("LLM_KEEP_ALIVE", "30m")
LLM_TIMEOUT = _int("LLM_TIMEOUT", 120)
TEMPERATURE = _float("TEMPERATURE", 0.1)       # vai "answer"; understand/verify luôn = 0
TOP_P = _float("TOP_P", 0.9)
ANSWER_MAX_TOKENS = _int("ANSWER_MAX_TOKENS", 900)

# Kiến thức trong trọng số mô hình dừng ở đâu (ước lượng — sửa khi đổi mô hình).
# Dùng để SO SÁNH với ngày của bằng chứng tra được: cũ hơn thì không được tin.
MODEL_KNOWLEDGE_CUTOFF = _str("MODEL_KNOWLEDGE_CUTOFF", "2023-12")
FINETUNE_RUNS_PATH = UTILITY_DIR / "finetune" / "runs.jsonl"

# ==========================================================================
# HAI HỆ THỐNG TRẢ LỜI / TWO ANSWERING SYSTEMS
#
#   websearch  Hệ thống 1 — tra web .gov.vn qua MCP   Backend/core/system_websearch.py
#   retrieval  Hệ thống 2 — CSDL thủ tục nội bộ       Backend/core/system_retrieval.py
#
# Người dùng chuyển giữa hai hệ thống bằng nút "Web search" trên giao diện.
# Mỗi cuộc trò chuyện ghi nhớ hệ thống của nó (cột conversations.system); đổi
# hệ thống giữa chừng thì MỞ CUỘC TRÒ CHUYỆN MỚI để mô hình không trộn lẫn
# thông tin của hai nguồn.
# ==========================================================================
SYSTEM_WEBSEARCH = "websearch"
SYSTEM_RETRIEVAL = "retrieval"
SYSTEMS = (SYSTEM_WEBSEARCH, SYSTEM_RETRIEVAL)

# Hệ thống 2 chưa xây xong -> mặc định vẫn là Hệ thống 1. Proposal muốn
# retrieval làm mặc định: đổi DEFAULT_SYSTEM=retrieval khi CSDL chạy được.
RETRIEVAL_ENABLED = _bool("RETRIEVAL_ENABLED", False)
DEFAULT_SYSTEM = _str("DEFAULT_SYSTEM", SYSTEM_WEBSEARCH).strip().lower()
if DEFAULT_SYSTEM not in SYSTEMS:
    DEFAULT_SYSTEM = SYSTEM_WEBSEARCH

# ==========================================================================
# HIỂU Ý ĐỊNH + HỎI LẠI
# ==========================================================================
CLARIFY_ENABLED = _bool("CLARIFY_ENABLED", True)
# Ví dụ mẫu (few-shot) cho bước hiểu ý định. Mô hình nhỏ chưa fine-tune cần; mô
# hình đã fine-tune bằng finetune/ thì đặt false (dữ liệu huấn luyện không có ví dụ).
UNDERSTAND_FEWSHOT = _bool("UNDERSTAND_FEWSHOT", True)

# ==========================================================================
# MCP + TÌM KIẾM (nguồn tri thức duy nhất cho câu trả lời)
# ==========================================================================
MCP_TRANSPORT = _str("MCP_TRANSPORT", "stdio")   # stdio | http | direct
MCP_SERVER_URL = _str("MCP_SERVER_URL", "http://127.0.0.1:8765/mcp")
MCP_TIMEOUT = _int("MCP_TIMEOUT", 60)
MCP_FALLBACK_DIRECT = _bool("MCP_FALLBACK_DIRECT", True)   # MCP hỏng -> gọi thẳng engine (ghi rõ trong vết)

SEARCH_PROVIDER = _str("SEARCH_PROVIDER", "ddgs")          # ddgs | searxng | brave | tavily
SEARCH_API_KEY = _str("SEARCH_API_KEY", "")                # brave / tavily
SEARXNG_URL = _str("SEARXNG_URL", "")
SEARCH_REGION = _str("SEARCH_REGION", "vn-vi")
SEARCH_RESULTS_PER_QUERY = _int("SEARCH_RESULTS_PER_QUERY", 8)
SEARCH_MAX_QUERIES = _int("SEARCH_MAX_QUERIES", 3)
SEARCH_TIMEOUT = _int("SEARCH_TIMEOUT", 10)
SEARCH_DEADLINE = _float("SEARCH_DEADLINE", 9)          # hạn chót chung cho mọi truy vấn song song
# Trần TUYỆT ĐỐI cho cả bước tra cứu (kể cả thử lại). Phải nhỏ hơn MCP_TIMEOUT,
# không thì MCP hết giờ trong khi engine vẫn đang chạy và cả lượt bị làm lại.
SEARCH_TOTAL_BUDGET = _float("SEARCH_TOTAL_BUDGET", 25)
SEARCH_DDGS_BACKEND = _str("SEARCH_DDGS_BACKEND", "auto")  # ddgs: auto | duckduckgo | brave | google | bing ... (phân tách dấu phẩy)
SEARCH_CACHE_SECONDS = _int("SEARCH_CACHE_SECONDS", 1800)
SEARCH_OFFICIAL_ONLY = _bool("SEARCH_OFFICIAL_ONLY", False)

FETCH_TOP_N = _int("FETCH_TOP_N", 6)             # số trang đọc toàn văn
FETCH_TIMEOUT = _int("FETCH_TIMEOUT", 8)
FETCH_DEADLINE = _float("FETCH_DEADLINE", 6)            # trang đọc chậm hơn -> dùng snippet
EVIDENCE_TOP_K = _int("EVIDENCE_TOP_K", 5)       # số nguồn vào Evidence Pack
EVIDENCE_MAX_CHARS = _int("EVIDENCE_MAX_CHARS", 7000)
EVIDENCE_SOURCE_CHARS = _int("EVIDENCE_SOURCE_CHARS", 1800)

# Xếp hạng nguồn: chính thống > văn bản pháp luật > báo chí > còn lại. Khớp theo
# tên miền hoặc tên miền con (gov.vn khớp mọi *.gov.vn).
OFFICIAL_DOMAINS = _list("OFFICIAL_DOMAINS",
                         "gov.vn,chinhphu.vn,baochinhphu.vn,vbpl.vn,quochoi.vn")
LEGAL_DOMAINS = _list("LEGAL_DOMAINS", "thuvienphapluat.vn,luatvietnam.vn")
NEWS_DOMAINS = _list("NEWS_DOMAINS",
                     "vtv.vn,vnexpress.net,tuoitre.vn,thanhnien.vn,dantri.com.vn,"
                     "vietnamnet.vn,nhandan.vn,laodong.vn,vov.vn,cand.com.vn,plo.vn,qdnd.vn")
BLOCKED_DOMAINS = _list("BLOCKED_DOMAINS",
                        "facebook.com,youtube.com,tiktok.com,instagram.com,x.com,"
                        "twitter.com,pinterest.com,reddit.com,scribd.com,shopee.vn")

# ==========================================================================
# KIỂM CHỨNG
# ==========================================================================
VERIFIER_ENABLED = _bool("VERIFIER_ENABLED", True)
MAX_VERIFY_RETRIES = _int("MAX_VERIFY_RETRIES", 1)
VERIFY_FAIL_POLICY = _str("VERIFY_FAIL_POLICY", "warn")   # warn | refuse

# ==========================================================================
# BỘ NHỚ HỘI THOẠI
# ==========================================================================
SUMMARY_ENABLED = _bool("SUMMARY_ENABLED", True)
MAX_CONTEXT_TOKENS = _int("MAX_CONTEXT_TOKENS", 3000)     # vượt -> AI tóm tắt phần cũ
SUMMARY_KEEP_RECENT = _int("SUMMARY_KEEP_RECENT", 5)      # số LƯỢT (x2 tin nhắn) giữ nguyên văn
TOKENS_PER_SYLLABLE = 1.4                                 # ước lượng thô cho tiếng Việt
PROFILE_MEMORY_ENABLED = _bool("PROFILE_MEMORY_ENABLED", True)

AI_DISCLOSURE = "Trợ lý ảo (AI) - thông tin tham khảo, không thay thế cán bộ một cửa."

# ==========================================================================
# CƠ SỞ DỮ LIỆU
# ==========================================================================
# Lớp lưu trữ. "sqlite" chạy được ngay, không phải cài gì thêm.
# Khi cần CSDL đầy đủ hơn (PostgreSQL...): đổi DB_BACKEND rồi viết lại ĐÚNG hai
# tệp Backend/db/connection.py + Backend/db/repositories.py. Không đụng chỗ khác.
# Storage layer. Swap point for a future full database: this flag + those 2 files.
DB_BACKEND = _str("DB_BACKEND", "sqlite").lower()   # sqlite | postgres (chưa làm)
DB_PATH = Path(_str("DATABASE_PATH", str(RUNTIME_DIR / "app.db")))
RETENTION_DAYS = _int("RETENTION_DAYS", 90)     # 0 = giữ vĩnh viễn

# ==========================================================================
# XÁC THỰC
# ==========================================================================
AUTH_ENABLED = _bool("AUTH_ENABLED", True)
AUTH_SESSION_DAYS = _int("AUTH_SESSION_DAYS", 14)
AUTH_COOKIE_NAME = "tthc_session"
AUTH_COOKIE_SECURE = _bool("AUTH_COOKIE_SECURE", False)   # True khi chạy sau HTTPS
AUTH_MIN_PASSWORD_LENGTH = 8
AUTH_MAX_LOGIN_ATTEMPTS = 5
AUTH_LOCKOUT_SECONDS = 900

# ==========================================================================
# HÀNG ĐỢI — xử lý tuần tự, LLM làm từng tin nhắn một
# ==========================================================================
QUEUE_ENABLED = _bool("QUEUE_ENABLED", True)
QUEUE_CONCURRENCY = _int("QUEUE_CONCURRENCY", 1)
QUEUE_MAX_DEPTH = _int("QUEUE_MAX_DEPTH", 20)
QUEUE_JOB_TIMEOUT = _int("QUEUE_JOB_TIMEOUT", 180)

# ==========================================================================
# TỆP ĐÍNH KÈM (theo từng cuộc trò chuyện, vào Evidence Pack như một nguồn)
# ==========================================================================
ATTACHMENTS_ENABLED = _bool("ATTACHMENTS_ENABLED", True)
UPLOAD_DIR = RUNTIME_DIR / "uploads"
ATTACH_MAX_BYTES = 20 * 1024 * 1024
ATTACH_MAX_PER_CONVERSATION = 10
ATTACH_CHUNK_CHARS = 900
ATTACH_CHUNK_OVERLAP = 120
ATTACH_TOP_K = 2
ATTACH_EXT_ALWAYS = {".csv", ".tsv", ".txt", ".md", ".json", ".xlsx", ".xls"}
ATTACH_EXT_OPTIONAL = {".pdf", ".docx"}

# ==========================================================================
# CÔNG CỤ PHÁT TRIỂN — ĐẶT False Ở BẢN CUỐI
# ==========================================================================
DEV_TOOLS_ENABLED = _bool("DEV_TOOLS_ENABLED", True)
DEVMODE_DEFAULT_ON = True
DEVMODE_TRACE_SIZE = 40

HOST = _str("APP_HOST", "127.0.0.1")
PORT = _int("APP_PORT", 8000)

# Sửa JS/CSS -> tăng số này để trình duyệt tải lại, không dùng bản cache cũ.
STATIC_VERSION = "7.5"

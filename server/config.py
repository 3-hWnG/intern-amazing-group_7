"""Cấu hình System 3 (env > .env). Copy rút gọn từ V10.6 config.py."""
from __future__ import annotations
import os
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
WEB_DIR = SERVER_DIR.parent / "web"


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(SERVER_DIR / ".env")


def _str(n, d):
    v = os.environ.get(n)
    return d if v is None else v.strip()


def _int(n, d):
    try:
        return int(_str(n, str(d)))
    except ValueError:
        return d


def _bool(n, d):
    return _str(n, "1" if d else "0").lower() in {"1", "true", "yes", "on"}


HOST = _str("APP_HOST", "127.0.0.1")
PORT = _int("APP_PORT", 8300)
DB_PATH = Path(_str("S3_DB_PATH", str(SERVER_DIR / "runtime" / "system3.db")))
SCHEMA_PATH = SERVER_DIR / "db" / "schema.sql"

OLLAMA_HOST = _str("OLLAMA_HOST", "http://127.0.0.1:11434")
LLM_MODEL = _str("LLM_MODEL", "qwen3:4b")
LLM_NUM_CTX = _int("LLM_NUM_CTX", 8192)
LLM_KEEP_ALIVE = _str("LLM_KEEP_ALIVE", "30m")
LLM_TIMEOUT = _int("LLM_TIMEOUT", 120)
PLANNER_TIMEOUT = float(_str("PLANNER_TIMEOUT", "2.5"))    # giây; quá hạn -> Planner dựng plan bằng luật
PLANNER_NUM_PREDICT = _int("PLANNER_NUM_PREDICT", 160)
# Phase 19: Planner hybrid (luật + Qwen3-4B). Mặc định rules cho tới khi đo xong (eval/P19_REPORT.md).
PLANNER_MODE = _str("S3_PLANNER_MODE", "rules")                     # rules | hybrid
PLANNER_LLM_TIMEOUT = float(_str("PLANNER_LLM_TIMEOUT", "7.0"))     # giây; quá hạn -> giữ kế hoạch luật
PLANNER_LLM_CONFIDENCE = float(_str("PLANNER_LLM_CONFIDENCE", "0.99"))   # LLM chỉ được sửa kế hoạch khi confidence >= ngưỡng; 0.99 = ít hại nhất khi quét 0.80-0.99 trên DEV (P19_REPORT)
PLANNER_LLM_DRAFT = _bool("PLANNER_LLM_DRAFT", False)               # 1 = LLM thấy bản nháp luật và chỉ sửa khi chắc nó sai (biến thể đo, xem P19_REPORT)
PLANNER_LLM_NUM_PREDICT = _int("PLANNER_LLM_NUM_PREDICT", 220)
# FINAL-PRODUCT: [AI] công tắc/timeout AI là cấu hình toàn tiến trình; xem mục 4 của checklist (có cho người dùng thường tắt AI không)
ANSWER_LLM_TIMEOUT = float(_str("ANSWER_LLM_TIMEOUT", "7.0"))      # giây; bước sinh chữ (Answer Composer); quá hạn -> giữ câu trả lời bằng code. Cùng 7 s với Planner hybrid (docs/ARCHITECTURE.md, bảng timeout)
ANSWER_LLM_TURN_BUDGET = float(_str("ANSWER_LLM_TURN_BUDGET", "9.0"))   # Phase 27: tổng giây LLM tối đa của MỘT lượt trả lời (nhiều lần gọi: mỗi điều kiện + so sánh); hết thì các lần sau dùng bản code ngay
ANSWER_LLM_NUM_PREDICT = _int("ANSWER_LLM_NUM_PREDICT", 200)      # Phase 27: giới hạn token sinh của bước sinh chữ (0 = không giới hạn); 200 chọn theo eval/P27_REPORT.md
ANSWER_LLM_PASSAGE_CHARS = _int("ANSWER_LLM_PASSAGE_CHARS", 450)  # Phase 27: cắt mỗi đoạn dữ liệu đưa cho LLM (trước: 700)
LLM_THINK = _bool("LLM_THINK", False)      # qwen3: False = tắt thinking

# Hàng đợi: 1 worker (GPU 6 GB).
QUEUE_CONCURRENCY = 1
QUEUE_MAX_DEPTH = _int("QUEUE_MAX_DEPTH", 20)
QUEUE_JOB_TIMEOUT = _int("QUEUE_JOB_TIMEOUT", 180)

# FINAL-PRODUCT: [B2] DEV_MODE là công tắc DUY NHẤT tách dev/người dùng, chỉ gắn vào /chat (khối dev), POST /config, /dev/*. Bản cuối: chế độ người dùng = dev ít quyền; chặn plan/trace/config/?dev=1 khi không dev (docs/FINAL_PRODUCT_CHECKLIST.md mục 1)
DEV_MODE = _bool("S3_DEV", False)           # true: mọi phản hồi kèm plan/trace

# Phase 20: nút "Tạo bảng full" trong câu trả lời (thay dòng "xem đầy đủ trên Cổng Dịch vụ công"); 0 = về như cũ
TABLE_BUTTON = _bool("S3_TABLE_BUTTON", True)

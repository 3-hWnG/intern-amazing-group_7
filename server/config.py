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
LLM_THINK = _bool("LLM_THINK", False)      # qwen3: False = tắt thinking

# Hàng đợi: 1 worker (GPU 6 GB).
QUEUE_CONCURRENCY = 1
QUEUE_MAX_DEPTH = _int("QUEUE_MAX_DEPTH", 20)
QUEUE_JOB_TIMEOUT = _int("QUEUE_JOB_TIMEOUT", 180)

DEV_MODE = _bool("S3_DEV", False)           # true: mọi phản hồi kèm plan/trace

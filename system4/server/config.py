"""Cấu hình System 4 (Friendly mode, chạy song song System 3 trên cùng web).

Thứ tự ưu tiên khi đọc một cài đặt (xem settings.py):
  1. runtime/settings.json  — panel "Cài đặt" trên web, nút "Lưu"
  2. khối MẶC ĐỊNH dưới đây — nút "Đặt làm mặc định" ghi đè khối này (giữ bản sao config.py.bak)
Sửa tay khối MẶC ĐỊNH cũng được; mỗi dòng phải đúng dạng `TÊN = giá_trị` (giá trị kiểu Python).
"""
from __future__ import annotations
import os
from pathlib import Path

S4_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = S4_DIR / "web"
RUNTIME_DIR = Path(os.environ.get("S4_RUNTIME_DIR", str(S4_DIR / "runtime")))
DB_PATH = RUNTIME_DIR / "system4.db"
SETTINGS_PATH = RUNTIME_DIR / "settings.json"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
COOKIE_SECURE = os.environ.get("S4_COOKIE_SECURE", "0") == "1"   # bật khi chạy sau HTTPS (xem docs/SYSTEM4_DEPLOY.md)

# ==== MẶC ĐỊNH (nút "Đặt làm mặc định" ghi đè các dòng trong khối này) ====
APP_TITLE = 'Instant Specialist'
DEFAULT_MODE = 'strict'
ALLOW_SIGNUP = True
SESSION_DAYS = 7
MIN_PASSWORD_LENGTH = 6
FRIENDLY_MODEL = 'qwen3:4b'
FRIENDLY_THINK = True
FRIENDLY_TEMPERATURE = 0.6
FRIENDLY_NUM_CTX = 8192
FRIENDLY_HISTORY_MESSAGES = 20
FRIENDLY_TIMEOUT = 120
FRIENDLY_QUEUE_MAX = 20
FRIENDLY_SYSTEM_PROMPT = 'Bạn là trợ lý AI thân thiện, ấm áp và tôn trọng người dùng. Trả lời bằng ngôn ngữ của tin nhắn mới nhất của người dùng (mặc định tiếng Việt). Trả lời rõ ràng, đúng trọng tâm. Không dùng emoji.'
# ==== HẾT MẶC ĐỊNH ====

# Danh sách cài đặt hiện trên panel. type: str | text (nhiều dòng) | int | float | bool | choice
SETTINGS = [
    dict(key="APP_TITLE", type="str", group="Web", label="Tên web", help="Hiện trên thanh tiêu đề và trang đăng nhập."),
    dict(key="DEFAULT_MODE", type="choice", group="Web", label="Chế độ mặc định",
         choices=["strict", "friendly"], help="Chế độ khi người dùng mở web lần đầu (sau đó web nhớ lựa chọn của họ)."),
    dict(key="ALLOW_SIGNUP", type="bool", group="Tài khoản", label="Cho phép đăng ký",
         help="Tắt thì chỉ người đã có tài khoản đăng nhập được (tài khoản đầu tiên luôn đăng ký được)."),
    dict(key="SESSION_DAYS", type="int", group="Tài khoản", label="Giữ đăng nhập (ngày)", min=1, max=365),
    dict(key="MIN_PASSWORD_LENGTH", type="int", group="Tài khoản", label="Độ dài mật khẩu tối thiểu", min=4, max=64),
    dict(key="FRIENDLY_MODEL", type="str", group="AI (Friendly)", label="Model", help="Tên model trong Ollama."),
    dict(key="FRIENDLY_THINK", type="bool", group="AI (Friendly)", label="AI suy nghĩ trước khi trả lời",
         help="Phần suy nghĩ được ẩn, chỉ hiện câu trả lời. qwen3:4b hiện tại LUÔN suy nghĩ: tắt mục này chỉ dùng với model "
              "không suy nghĩ (vd. qwen3:4b-instruct-2507-q4_K_M), nếu không chữ suy nghĩ sẽ lẫn vào câu trả lời."),
    dict(key="FRIENDLY_TEMPERATURE", type="float", group="AI (Friendly)", label="Độ sáng tạo (temperature)",
         min=0.0, max=1.5, help="Thấp = ổn định, cao = đa dạng hơn."),
    dict(key="FRIENDLY_NUM_CTX", type="int", group="AI (Friendly)", label="Độ dài ngữ cảnh (token)", min=2048, max=32768),
    dict(key="FRIENDLY_HISTORY_MESSAGES", type="int", group="AI (Friendly)", label="Số tin nhắn cũ gửi kèm",
         min=0, max=200, help="Bao nhiêu tin gần nhất của hội thoại được gửi cho AI để giữ ngữ cảnh."),
    dict(key="FRIENDLY_TIMEOUT", type="int", group="AI (Friendly)", label="Thời gian chờ tối đa (giây)", min=10, max=600),
    dict(key="FRIENDLY_QUEUE_MAX", type="int", group="AI (Friendly)", label="Số câu hỏi tối đa đang chờ", min=1, max=500),
    dict(key="FRIENDLY_SYSTEM_PROMPT", type="text", group="AI (Friendly)", label="Lời dặn hệ thống (system prompt)"),
]

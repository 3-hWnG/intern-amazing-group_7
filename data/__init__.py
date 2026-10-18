"""Lớp dữ liệu độc lập của System 3 (độc lập, không phụ thuộc repo cũ)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "snapshot"
DB_PATH = Path(os.environ.get("S3_DATA_DB") or ROOT / "runtime" / "system3.db")   # S3_DATA_DB: dựng/đọc DB ở đường dẫn khác

# G2.1: DB thủ tục theo phiên bản. System 4 giữ con trỏ duy nhất (system4.db meta.proc_active) và đăng ký hàm trả
# đường dẫn DB bất biến của phiên bản đang dùng (data/runtime/knowledge/<vid>.db). Không có System 4 (chạy System 3
# một mình, test, eval): DB_PATH như trước. Mọi chỗ đọc DB thủ tục gọi active_db_path() mỗi lần, cache khoá theo đường dẫn.
_active_provider = None


def set_active_provider(fn) -> None:
    """fn() -> Path | None. None = dùng DB_PATH."""
    global _active_provider
    _active_provider = fn


def active_db_path() -> Path:
    if _active_provider is not None:
        p = _active_provider()
        if p:
            return Path(p)
    return DB_PATH

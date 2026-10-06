"""Lớp dữ liệu độc lập của System 3 (độc lập, không phụ thuộc repo cũ)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "snapshot"
DB_PATH = Path(os.environ.get("S3_DATA_DB") or ROOT / "runtime" / "system3.db")   # S3_DATA_DB: dựng/đọc DB ở đường dẫn khác

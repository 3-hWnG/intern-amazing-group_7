"""Lớp dữ liệu độc lập của System 3 (độc lập, không phụ thuộc repo cũ)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "snapshot"
DB_PATH = ROOT / "runtime" / "system3.db"

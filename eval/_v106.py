"""Đường dẫn mã V10.6 (vendor) và DB V10.6 dựng lại. Không còn phụ thuộc repo/ cạnh system3.
S3_REPO (tuỳ chọn) trỏ tới một clone V10.6 thật để so; S3_V106_DB đổi chỗ đặt DB."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.environ.get("S3_REPO") or os.path.join(HERE, "vendor_v106")
DB = os.environ.get("S3_V106_DB") or os.path.join(HERE, "runtime", "v106.db")
if VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)

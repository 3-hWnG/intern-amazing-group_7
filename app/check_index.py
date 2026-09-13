"""Kiểm tra chỉ mục có còn khớp cấu hình không — KHÔNG nạp mô hình.

Mã thoát:
    0 = chỉ mục hợp lệ, chạy thẳng được
    2 = cần chạy ingest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config

META = config.DATA_DIR / "index_meta.json"


def reason() -> str | None:
    if not config.CHROMA_PATH.exists():
        return "chưa có vector DB"
    if not META.exists():
        return "chưa có index_meta.json (chỉ mục cũ)"
    try:
        meta = json.loads(META.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"index_meta.json hỏng ({exc})"
    if meta.get("embed_model") != config.EMBED_MODEL_NAME:
        return (f"đổi mô hình nhúng: chỉ mục dựng bằng "
                f"{meta.get('embed_model')}, config đang dùng {config.EMBED_MODEL_NAME}")
    if meta.get("space") != config.CHROMA_SPACE:
        return f"đổi metric: {meta.get('space')} -> {config.CHROMA_SPACE}"
    if meta.get("multi_view") != config.USE_MULTI_VIEW:
        return "đổi chế độ multi-view"
    if config.USE_LEXICAL and not config.BM25_INDEX_PATH.exists():
        return "thiếu chỉ mục BM25"
    if not config.DATASET_PATH.exists():
        return f"không thấy dataset {config.DATASET_PATH.name}"
    return None


if __name__ == "__main__":
    why = reason()
    if why:
        print(f"  cần nạp lại chỉ mục: {why}")
        sys.exit(2)
    meta = json.loads(META.read_text(encoding="utf-8"))
    print(f"  chỉ mục hợp lệ: {meta['n_procedures']} thủ tục / {meta['n_views']} view "
          f"· {meta['embed_model']} · {meta['dim']} chiều")
    sys.exit(0)

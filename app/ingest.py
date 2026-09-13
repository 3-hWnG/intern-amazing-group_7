"""Nạp dataset -> vector DB (nhiều view/thủ tục) + chỉ mục BM25.

Chạy lại mỗi khi dataset hoặc EMBED_MODEL_NAME thay đổi:
    python ingest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
from datetime import datetime

from config import (CHROMA_SPACE, DATA_DIR, DATASET_PATH, EMBED_MODEL_NAME,
                    USE_LEXICAL, USE_MULTI_VIEW)

INDEX_META_PATH = DATA_DIR / "index_meta.json"
from core import embeddings, lexical, vectorstore
from domain.records import VIEW_TITLE, load_procedures


def build_view_rows(procedures):
    ids, docs, metas = [], [], []
    for p in procedures:
        views = p.views() if USE_MULTI_VIEW else [(VIEW_TITLE, p.view_title())]
        for view_name, text in views:
            if not text.strip():
                continue
            ids.append(f"{p.row_id}::{view_name}")
            docs.append(text)
            metas.append({**p.to_metadata(), "view": view_name})
    return ids, docs, metas


def main():
    print(f"Đọc dataset...")
    procedures = load_procedures()
    print(f"  {len(procedures)} thủ tục")

    ids, docs, metas = build_view_rows(procedures)
    print(f"  {len(ids)} view (trung bình {len(ids)/max(1,len(procedures)):.1f} view/thủ tục)")

    print(f"Nạp mô hình nhúng: {EMBED_MODEL_NAME} ...")
    vectors = embeddings.encode(docs).tolist()

    print(f"Ghi vào ChromaDB (metric = {CHROMA_SPACE}) ...")
    collection = vectorstore.reset_collection()
    B = 256
    for i in range(0, len(ids), B):
        collection.add(ids=ids[i:i+B], documents=docs[i:i+B],
                       embeddings=vectors[i:i+B], metadatas=metas[i:i+B])
    print(f"  {collection.count()} view đã lưu")

    if USE_LEXICAL:
        print("Dựng chỉ mục BM25 (bỏ dấu) ...")
        lexical.build_index(procedures)
        lexical.get_index.cache_clear()
        print("  xong")

    # Ghi "vân tay" của chỉ mục. Nhờ file này, lần sau chỉ cần đọc JSON là biết
    # có phải nạp lại không - KHÔNG phải tải mô hình nhúng chỉ để kiểm tra.
    INDEX_META_PATH.write_text(json.dumps({
        "embed_model": EMBED_MODEL_NAME,
        "dim": len(vectors[0]) if vectors else 0,
        "space": CHROMA_SPACE,
        "multi_view": USE_MULTI_VIEW,
        "n_views": len(ids),
        "n_procedures": len(procedures),
        "dataset": DATASET_PATH.name,
        "built_at": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Done! Database ready.")


if __name__ == "__main__":
    main()

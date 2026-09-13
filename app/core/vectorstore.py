"""ChromaDB - lưu vector của từng GÓC NHÌN (view) của thủ tục.

id = "<row_id>::<view>"; metadata mang row_id để gộp lại theo thủ tục.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from config import CHROMA_PATH, CHROMA_SPACE, COLLECTION_NAME, DENSE_TOP_K


@lru_cache(maxsize=1)
def get_client():
    import chromadb
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


@lru_cache(maxsize=1)
def get_collection():
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": CHROMA_SPACE},
    )


def reset_collection():
    """Xoá và tạo lại - dùng khi ingest lại từ đầu."""
    try:
        get_client().delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    get_collection.cache_clear()
    return get_collection()


def distance_to_similarity(distance: float) -> float:
    """Đưa mọi metric về thang 'càng lớn càng giống', trong khoảng 0..1."""
    if CHROMA_SPACE == "cosine":
        return max(0.0, min(1.0, 1.0 - float(distance)))
    # l2 trên vector đã chuẩn hoá: d^2 = 2 - 2cos
    return max(0.0, min(1.0, 1.0 - float(distance) / 2.0))


def search_views(query_embedding, n_results: int = DENSE_TOP_K) -> list[dict]:
    """Trả về danh sách view gần nhất, đã kèm similarity."""
    res = get_collection().query(
        query_embeddings=[np.asarray(query_embedding, dtype=np.float32).tolist()],
        n_results=n_results,
    )
    if not res["ids"] or not res["ids"][0]:
        return []
    out = []
    for i, vid in enumerate(res["ids"][0]):
        meta = (res["metadatas"][0][i] or {}) if res.get("metadatas") else {}
        dist = res["distances"][0][i] if res.get("distances") else 0.0
        out.append({
            "view_id": vid,
            "row_id": int(meta.get("row_id", str(vid).split("::")[0])),
            "view": str(vid).split("::")[-1],
            "distance": float(dist),
            "similarity": distance_to_similarity(dist),
            "document": res["documents"][0][i] if res.get("documents") else "",
        })
    return out

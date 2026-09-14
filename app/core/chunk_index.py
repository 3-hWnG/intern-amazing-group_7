"""Chỉ mục cho TỆP ĐÍNH KÈM — tách hẳn khỏi chỉ mục dataset nội bộ.

Hai phạm vi tra cứu, đúng như yêu cầu ở slide cuối:

    global documents       -> data/chromadb_eval   (dựng sẵn, KHÔNG đụng ở đây)
    conversation documents -> collection "doc_chunks" trong CÙNG file chromadb

Cùng công thức truy hồi với KB (dense + BM25 bỏ dấu, hoà bằng RRF) vì nó đã đo
được: BM25 bỏ dấu một mình đạt R@1 0.72 trên dataset nội bộ. Không có lý do gì
dùng công thức yếu hơn cho tệp người dùng.

BM25 ở đây dựng trong RAM theo từng hội thoại (vài chục chunk, dựng mất vài
mili giây) nên không cần file pickle như bên KB.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from config import (ATTACH_COLLECTION, ATTACH_FUSION_TOP_K, ATTACH_TOP_K,
                    CHROMA_SPACE, RRF_K, RRF_WEIGHT_DENSE,
                    RRF_WEIGHT_DENSE_NO_DIACRITICS, RRF_WEIGHT_LEXICAL)
from core import embeddings
from db.repositories import DocumentChunks
from domain.text import has_diacritics, tokenize

# hội thoại -> chỉ mục BM25 dựng sẵn trong RAM
_BM25_CACHE: dict[int, dict] = {}


@lru_cache(maxsize=1)
def get_collection():
    from core.vectorstore import get_client
    return get_client().get_or_create_collection(
        name=ATTACH_COLLECTION,
        metadata={"hnsw:space": CHROMA_SPACE},
    )


def invalidate(conversation_id: int | None = None) -> None:
    if conversation_id is None:
        _BM25_CACHE.clear()
    else:
        _BM25_CACHE.pop(int(conversation_id), None)


# --------------------------------------------------------------------------
# ghi
# --------------------------------------------------------------------------
def add_chunks(chunk_rows: list[dict], *, document_id: int,
               conversation_id: int, filename: str) -> int:
    """chunk_rows: bản ghi đã lưu ở SQLite (có id, content)."""
    if not chunk_rows:
        return 0
    texts = [r["content"] for r in chunk_rows]
    vectors = embeddings.encode(texts)
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)

    collection = get_collection()
    B = 128
    for i in range(0, len(chunk_rows), B):
        part = chunk_rows[i:i + B]
        collection.add(
            ids=[str(r["id"]) for r in part],
            documents=[r["content"] for r in part],
            embeddings=vectors[i:i + B].tolist(),
            metadatas=[{
                "chunk_id": int(r["id"]),
                "document_id": int(document_id),
                "conversation_id": int(conversation_id),
                "filename": filename,
            } for r in part],
        )
    invalidate(conversation_id)
    return len(chunk_rows)


def delete_document(document_id: int, conversation_id: int | None = None) -> None:
    try:
        get_collection().delete(where={"document_id": int(document_id)})
    except Exception:
        pass
    invalidate(conversation_id)


# --------------------------------------------------------------------------
# đọc
# --------------------------------------------------------------------------
def _bm25_for(conversation_id: int) -> dict | None:
    cached = _BM25_CACHE.get(conversation_id)
    if cached is not None:
        return cached or None

    rows = DocumentChunks.list_for_conversation(conversation_id)
    if not rows:
        _BM25_CACHE[conversation_id] = {}
        return None

    from rank_bm25 import BM25Okapi
    corpus = [tokenize(r["content"]) for r in rows]
    index = {"bm25": BM25Okapi(corpus), "rows": rows}
    _BM25_CACHE[conversation_id] = index
    return index


def _rrf(rank: int, weight: float = 1.0) -> float:
    return weight / (RRF_K + rank)


def search(query: str, conversation_id: int, top_k: int = ATTACH_TOP_K) -> list[dict]:
    """Trả về [{chunk_id, content, filename, score, metadata}] đã hoà hai nguồn."""
    query = (query or "").strip()
    if not query:
        return []

    w_dense = (RRF_WEIGHT_DENSE if has_diacritics(query)
               else RRF_WEIGHT_DENSE_NO_DIACRITICS)
    pool: dict[int, dict] = {}

    def slot(chunk_id: int, content: str, filename: str) -> dict:
        if chunk_id not in pool:
            pool[chunk_id] = {"chunk_id": chunk_id, "content": content,
                              "filename": filename, "score": 0.0,
                              "dense": 0.0, "bm25_norm": 0.0}
        return pool[chunk_id]

    # ---- dense, lọc theo đúng hội thoại ----------------------------------
    try:
        q_emb = embeddings.encode(query)
        res = get_collection().query(
            query_embeddings=[np.asarray(q_emb, dtype=np.float32).tolist()],
            n_results=ATTACH_FUSION_TOP_K,
            where={"conversation_id": int(conversation_id)},
        )
        ids = (res.get("ids") or [[]])[0]
        for rank, cid in enumerate(ids):
            meta = ((res.get("metadatas") or [[]])[0][rank]) or {}
            doc = ((res.get("documents") or [[]])[0][rank]) or ""
            dist = ((res.get("distances") or [[0.0]])[0][rank]) or 0.0
            from core.vectorstore import distance_to_similarity
            cand = slot(int(meta.get("chunk_id", cid)), doc, meta.get("filename", ""))
            cand["dense"] = distance_to_similarity(dist)
            cand["score"] += _rrf(rank, w_dense)
    except Exception:
        pass       # chưa có collection / chưa có tệp nào -> bỏ qua nhánh dense

    # ---- BM25 bỏ dấu ------------------------------------------------------
    index = _bm25_for(conversation_id)
    if index:
        scores = index["bm25"].get_scores(tokenize(query))
        ranked = sorted(zip(index["rows"], scores), key=lambda x: -x[1])
        top = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
        for rank, (row, score) in enumerate(ranked[:ATTACH_FUSION_TOP_K]):
            if score <= 0:
                continue
            cand = slot(int(row["id"]), row["content"], row.get("filename", ""))
            cand["bm25_norm"] = float(score) / top
            cand["score"] += _rrf(rank, RRF_WEIGHT_LEXICAL)

    out = sorted(pool.values(), key=lambda c: -c["score"])[:top_k]
    for c in out:
        wd = w_dense / (w_dense + RRF_WEIGHT_LEXICAL)
        c["confidence"] = wd * c["dense"] + (1 - wd) * c["bm25_norm"]
    return out

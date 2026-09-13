"""BM25 trên văn bản ĐÃ BỎ DẤU.

Đây là tầng sửa trực tiếp lỗi lớn nhất của baseline v0: câu hỏi gõ không dấu
đạt R@1 0.056 vì mô hình nhúng mù với dạng không dấu. Khớp từ khoá trên chuỗi
đã fold thì "lam giay khai sinh" và "làm giấy khai sinh" là một.
"""

from __future__ import annotations

import pickle
from functools import lru_cache

from config import BM25_INDEX_PATH, LEXICAL_TOP_K
from domain.records import get_procedures
from domain.text import tokenize


def build_index(procedures=None) -> dict:
    from rank_bm25 import BM25Okapi

    procedures = procedures or get_procedures()
    row_ids = [p.row_id for p in procedures]
    corpus = [tokenize(p.lexical_text()) for p in procedures]
    bm25 = BM25Okapi(corpus)
    payload = {"row_ids": row_ids, "corpus": corpus}
    BM25_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with BM25_INDEX_PATH.open("wb") as f:
        pickle.dump(payload, f)
    return {"bm25": bm25, **payload}


@lru_cache(maxsize=1)
def get_index() -> dict:
    from rank_bm25 import BM25Okapi

    if BM25_INDEX_PATH.exists():
        with BM25_INDEX_PATH.open("rb") as f:
            payload = pickle.load(f)
        return {"bm25": BM25Okapi(payload["corpus"]), **payload}
    return build_index()


def search(query: str, n_results: int = LEXICAL_TOP_K) -> list[dict]:
    idx = get_index()
    scores = idx["bm25"].get_scores(tokenize(query))
    ranked = sorted(zip(idx["row_ids"], scores), key=lambda x: -x[1])[:n_results]
    top = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
    return [
        {"row_id": int(rid), "bm25": float(sc), "bm25_norm": float(sc) / top}
        for rid, sc in ranked if sc > 0
    ]

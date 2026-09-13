"""Tầng truy hồi: dense + BM25 -> hoà nhịp (RRF) -> xếp hạng lại.

Đây là nơi DUY NHẤT quyết định cách ghép các nguồn xếp hạng.
Bật/tắt từng nguồn bằng USE_DENSE / USE_LEXICAL / USE_RERANKER.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config import (CONFIDENCE_FROM_RERANKER, DENSE_TOP_K, FINAL_TOP_K,
                    FUSION_TOP_K, LEXICAL_TOP_K, RERANK_SKIP_NO_DIACRITICS,
                    RRF_K, RRF_WEIGHT_DENSE, RRF_WEIGHT_DENSE_NO_DIACRITICS,
                    RRF_WEIGHT_LEXICAL, USE_DENSE, USE_LEXICAL, USE_RERANKER)
from core import embeddings, lexical, vectorstore
from domain.records import Procedure, by_row_id
from domain.text import has_diacritics


@dataclass
class Candidate:
    row_id: int
    record: Procedure
    confidence: float = 0.0          # thang 0..1, dùng để phân tầng A/B/C/D
    dense_similarity: float = 0.0
    best_view: str = ""
    bm25_norm: float = 0.0
    rerank_score: float | None = None
    fusion_score: float = 0.0
    sources: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.record.ten


def _rrf(rank: int, weight: float = 1.0) -> float:
    return weight / (RRF_K + rank)


def _dense_weight(query: str) -> float:
    """Câu hỏi không dấu -> mô hình nhúng gần như mù, tin BM25 hơn.

    Đo được ở v1: no_diacritics đạt 0.574 với BM25 đơn lẻ nhưng tụt còn 0.407
    khi hoà ngang hàng với dense (dense đơn lẻ chỉ 0.056 trên slice này).
    """
    return RRF_WEIGHT_DENSE if has_diacritics(query) else RRF_WEIGHT_DENSE_NO_DIACRITICS


def retrieve(query: str, top_k: int = FINAL_TOP_K) -> list[Candidate]:
    records = by_row_id()
    pool: dict[int, Candidate] = {}

    def slot(row_id: int) -> Candidate | None:
        rec = records.get(row_id)
        if rec is None:
            return None
        if row_id not in pool:
            pool[row_id] = Candidate(row_id=row_id, record=rec)
        return pool[row_id]

    # ---- dense: gộp nhiều view về một thủ tục, lấy view khớp nhất ----------
    w_dense = _dense_weight(query)
    if USE_DENSE:
        q_emb = embeddings.encode(query)
        seen: dict[int, int] = {}
        for hit in vectorstore.search_views(q_emb, DENSE_TOP_K):
            cand = slot(hit["row_id"])
            if cand is None:
                continue
            if hit["similarity"] > cand.dense_similarity:
                cand.dense_similarity = hit["similarity"]
                cand.best_view = hit["view"]
            if hit["row_id"] not in seen:          # thứ hạng ở cấp thủ tục
                seen[hit["row_id"]] = len(seen)
                cand.fusion_score += _rrf(seen[hit["row_id"]], w_dense)
                cand.sources.append("dense")

    # ---- lexical: BM25 trên chuỗi đã bỏ dấu -------------------------------
    if USE_LEXICAL:
        for rank, hit in enumerate(lexical.search(query, LEXICAL_TOP_K)):
            cand = slot(hit["row_id"])
            if cand is None:
                continue
            cand.bm25_norm = hit["bm25_norm"]
            cand.fusion_score += _rrf(rank, RRF_WEIGHT_LEXICAL)
            cand.sources.append("bm25")

    candidates = sorted(pool.values(), key=lambda c: -c.fusion_score)[:FUSION_TOP_K]
    if not candidates:
        return []

    # ---- xếp hạng lại bằng cross-encoder ----------------------------------
    diacritics = has_diacritics(query)
    use_rerank = USE_RERANKER and not (RERANK_SKIP_NO_DIACRITICS and not diacritics)
    if use_rerank:
        from core import reranker
        if reranker.is_available():
            passages = [f"{c.record.view_title()}. {c.record.view_summary()}" for c in candidates]
            for cand, sc in zip(candidates, reranker.score(query, passages)):
                cand.rerank_score = sc
            candidates.sort(key=lambda c: -(c.rerank_score or 0.0))

    # ---- độ tin cậy cuối cùng ---------------------------------------------
    # Reranker quyết định THỨ TỰ; độ tin cậy lấy từ điểm hoà dense+BM25 vì thang
    # đó liên tục và đã hiệu chỉnh được, còn điểm reranker thì hai cực (v3).
    for cand in candidates:
        if CONFIDENCE_FROM_RERANKER and cand.rerank_score is not None:
            cand.confidence = cand.rerank_score
        elif USE_LEXICAL and USE_DENSE:
            wd = w_dense / (w_dense + RRF_WEIGHT_LEXICAL)
            cand.confidence = wd * cand.dense_similarity + (1 - wd) * cand.bm25_norm
        else:
            cand.confidence = cand.dense_similarity or cand.bm25_norm

    # KHÔNG sắp xếp lại theo confidence nếu reranker đã quyết định thứ tự.
    if not any(c.rerank_score is not None for c in candidates):
        candidates.sort(key=lambda c: -c.confidence)
    return candidates[:top_k]

"""retrieval.py — Tầng truy hồi lai (Hybrid RRF: Dense + BM25 + Reranker)."""

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional
import math
import re
import unicodedata
import chromadb
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from config import (
    CHROMA_COLLECTION, CHROMA_PATH, CHROMA_SPACE, DENSE_TOP_K, DEVICE,
    EMBED_MODEL_NAME, FINAL_TOP_K, FUSION_TOP_K, LEXICAL_TOP_K,
    LUAT_ANCHORS, NGOAI_ANCHORS, RERANK_SKIP_NO_DIACRITICS, RERANKER_DEVICE,
    RERANKER_MAX_LENGTH, RERANKER_MODEL_NAME, RRF_K, RRF_WEIGHT_DENSE,
    RRF_WEIGHT_DENSE_NO_DIACRITICS, RRF_WEIGHT_LEXICAL, USE_DENSE, USE_LEXICAL,
    USE_RERANKER, XAGIAO_ANCHORS
)
from models import Candidate, Procedure


# ==============================================================================
# 1. Tiện ích xử lý văn bản tiếng Việt & Bỏ dấu (Text Normalization)
# ==============================================================================
def fold_text(text: str) -> str:
    """Chuyển về chữ thường và loại bỏ toàn bộ dấu thanh/dấu mũ tiếng Việt."""
    if not text:
        return ""
    s = text.lower()
    s = s.replace("đ", "d").replace("Đ", "D")
    nfd = unicodedata.normalize("NFD", s)
    s = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def has_diacritics(text: str) -> bool:
    """Kiểm tra xem chuỗi có chứa dấu tiếng Việt hay không."""
    if any(c in text for c in "đĐ"):
        return True
    nfd = unicodedata.normalize("NFD", text)
    return any(unicodedata.category(c) == "Mn" for c in nfd)


# ==============================================================================
# 2. Embedding Model Wrapper (Vietnamese-SBERT)
# ==============================================================================
class EmbeddingsWrapper:
    def __init__(self, model_name: str = EMBED_MODEL_NAME, device: str = DEVICE):
        self.model_name = model_name
        self.device = device
        self._model = None

    def _load(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def encode(self, texts, **kwargs):
        model = self._load()
        if "device" not in kwargs:
            kwargs["device"] = self.device
        return model.encode(texts, **kwargs)

    def centroid(self, texts: List[str]) -> np.ndarray:
        vecs = self.encode(texts)
        c = np.mean(vecs, axis=0)
        norm = np.linalg.norm(c)
        return c / norm if norm > 0 else c


embeddings = EmbeddingsWrapper()


# ==============================================================================
# 2.5 Phân loại Ý định Mục tiêu (Intent Classification - 0.005s)
# ==============================================================================
_CENTROIDS_CACHE: Dict[str, np.ndarray] = {}

def get_intent_centroids() -> Dict[str, np.ndarray]:
    global _CENTROIDS_CACHE
    if not _CENTROIDS_CACHE:
        _CENTROIDS_CACHE = {
            "LUAT": embeddings.centroid(LUAT_ANCHORS),
            "NGOAI": embeddings.centroid(NGOAI_ANCHORS),
            "XAGIAO": embeddings.centroid(XAGIAO_ANCHORS)
        }
    return _CENTROIDS_CACHE


def classify_intent(query: str) -> str:
    """
    Xác định chính xác mục tiêu của người dùng:
    - LUAT: Thủ tục hành chính (kết hôn, khai sinh, đất đai, cccd...).
    - NGOAI: Luật giao thông, mức phạt (mũ bảo hiểm, nồng độ cồn...), tin tức ngoài 70 thủ tục.
    - XAGIAO: Chào hỏi, cảm ơn, tạm biệt.
    """
    q_emb = embeddings.encode(query)
    q_norm = np.linalg.norm(q_emb)
    if q_norm == 0:
        return "LUAT"

    centroids = get_intent_centroids()
    scores = {}
    for intent, c in centroids.items():
        sim = float(np.dot(q_emb, c) / (q_norm * np.linalg.norm(c)))
        scores[intent] = sim

    # Trả về intent có điểm tương đồng cao nhất
    best_intent = max(scores, key=scores.get)
    return best_intent


# ==============================================================================
# 3. Vector Database Manager (ChromaDB)
# ==============================================================================
class VectorStore:
    def __init__(self, chroma_path: Path = CHROMA_PATH, collection_name: str = CHROMA_COLLECTION):
        self.chroma_path = str(chroma_path)
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.chroma_path)
        return self._client

    def get_collection(self):
        if self._collection is None:
            client = self.get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": CHROMA_SPACE}
            )
        return self._collection

    def reset_collection(self):
        client = self.get_client()
        try:
            client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self._collection = client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": CHROMA_SPACE}
        )
        return self._collection

    def search_views(self, query_emb: np.ndarray, top_k: int = DENSE_TOP_K) -> List[dict]:
        """Truy vấn các view tương đồng từ ChromaDB và chuẩn hóa điểm cosine."""
        coll = self.get_collection()
        res = coll.query(
            query_embeddings=[query_emb.tolist()],
            n_results=top_k,
            include=["metadatas", "distances"]
        )
        if not res["ids"] or not res["ids"][0]:
            return []

        hits = []
        for cid, dist, meta in zip(res["ids"][0], res["distances"][0], res["metadatas"][0]):
            # Chroma metric cosine: distance in [0..2], similarity = 1 - distance
            sim = 1.0 - (dist if dist is not None else 1.0)
            hits.append({
                "chunk_id": cid,
                "row_id": int(meta.get("row_id", 0)),
                "view": meta.get("view", "unknown"),
                "similarity": max(0.0, float(sim)),
            })
        return hits


vectorstore = VectorStore()


# ==============================================================================
# 4. Lexical Search Manager (BM25 bỏ dấu)
# ==============================================================================
class BM25Manager:
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.row_ids: List[int] = []

    def build_index(self, procedures: List[Procedure]):
        corpus = [fold_text(p.lexical_text()).split() for p in procedures]
        self.bm25 = BM25Okapi(corpus)
        self.row_ids = [p.row_id for p in procedures]

    def search(self, query: str, top_k: int = LEXICAL_TOP_K) -> List[dict]:
        if not self.bm25 or not self.row_ids:
            try:
                from ingest import load_procedures
                self.build_index(load_procedures())
            except Exception:
                return []
        if not self.bm25 or not self.row_ids:
            return []
        tokens = fold_text(query).split()
        if not tokens:
            return []
        # Lọc các hư từ khẩu ngữ tiếng Việt để tránh BM25 khớp bậy vào thủ tục không liên quan
        stopwords = {
            "khong", "co", "bi", "sao", "thi", "toi", "tui", "cho", "o", "dau",
            "gi", "nao", "duoc", "va", "cua", "la", "the", "a", "oi", "vay", "nhu"
        }
        content_tokens = [t for t in tokens if t not in stopwords]
        query_tokens = content_tokens if content_tokens else tokens

        scores = self.bm25.get_scores(query_tokens)
        expected_max = max(1, len(query_tokens)) * 3.5
        
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        hits = []
        for idx in ranked_indices:
            raw_score = float(scores[idx])
            if raw_score < 1.0:
                continue
            hits.append({
                "row_id": self.row_ids[idx],
                "score": raw_score,
                "bm25_norm": min(1.0, raw_score / expected_max),
            })
        return hits


bm25_manager = BM25Manager()


# ==============================================================================
# 5. Cross-Encoder Reranker Wrapper
# ==============================================================================
class RerankerWrapper:
    def __init__(self, model_name: str = RERANKER_MODEL_NAME, device: str = RERANKER_DEVICE):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._available: Optional[bool] = None

    def _load(self):
        if self._model is None:
            self._model = CrossEncoder(self.model_name, device=self.device, max_length=RERANKER_MAX_LENGTH)
        return self._model

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            self._load()
            self._available = True
        except Exception as e:
            print(f"[Reranker] Không thể khởi tạo mô hình: {e}")
            self._available = False
        return self._available

    def score(self, query: str, passages: List[str]) -> List[float]:
        if not passages:
            return []
        model = self._load()
        raw = model.predict([(query, p) for p in passages], batch_size=16, show_progress_bar=False)
        # Sigmoid chuyển điểm về khoảng [0, 1]
        out = []
        for r in raw:
            val = float(r)
            if 0.0 <= val <= 1.0:
                out.append(val)
            else:
                clipped = max(-30.0, min(30.0, val))
                out.append(1.0 / (1.0 + math.exp(-clipped)))
        return out


reranker = RerankerWrapper()


# ==============================================================================
# 6. Hàm Truy hồi Lai (Hybrid RRF Retrieval)
# ==============================================================================
def _rrf(rank: int, weight: float = 1.0) -> float:
    return weight / (RRF_K + rank)


def retrieve(query: str, procedures_map: Optional[Dict[int, Procedure]] = None, top_k: int = FINAL_TOP_K) -> List[Candidate]:
    """
    Truy hồi lai kết hợp Dense + BM25 (RRF) và xếp hạng lại bằng Cross-Encoder.
    """
    if procedures_map is None:
        from ingest import get_procedures_map
        procedures_map = get_procedures_map()
    pool: Dict[int, Candidate] = {}

    def get_slot(row_id: int) -> Optional[Candidate]:
        rec = procedures_map.get(row_id)
        if rec is None:
            return None
        if row_id not in pool:
            pool[row_id] = Candidate(row_id=row_id, record=rec)
        return pool[row_id]

    diacritics = has_diacritics(query)
    w_dense = RRF_WEIGHT_DENSE if diacritics else RRF_WEIGHT_DENSE_NO_DIACRITICS

    # 1. Dense Retrieval (ChromaDB đa view)
    if USE_DENSE:
        q_emb = embeddings.encode(query)
        seen_proc: Dict[int, int] = {}
        for hit in vectorstore.search_views(q_emb, DENSE_TOP_K):
            cand = get_slot(hit["row_id"])
            if cand is None:
                continue
            if hit["similarity"] > cand.dense_similarity:
                cand.dense_similarity = hit["similarity"]
                cand.best_view = hit["view"]
            if hit["row_id"] not in seen_proc:
                seen_proc[hit["row_id"]] = len(seen_proc)
                cand.fusion_score += _rrf(seen_proc[hit["row_id"]], w_dense)
                cand.sources.append("dense")

    # 2. Lexical Retrieval (BM25 trên văn bản bỏ dấu)
    if USE_LEXICAL:
        for rank, hit in enumerate(bm25_manager.search(query, LEXICAL_TOP_K)):
            cand = get_slot(hit["row_id"])
            if cand is None:
                continue
            cand.bm25_norm = hit["bm25_norm"]
            cand.fusion_score += _rrf(rank, RRF_WEIGHT_LEXICAL)
            cand.sources.append("bm25")

    # Lấy top ứng viên sau khi hoà trộn thứ hạng RRF
    candidates = sorted(pool.values(), key=lambda c: -c.fusion_score)[:FUSION_TOP_K]
    if not candidates:
        return []

    # 3. Cross-Encoder Reranker
    use_rerank = USE_RERANKER and not (RERANK_SKIP_NO_DIACRITICS and not diacritics)
    if use_rerank and reranker.is_available():
        passages = [f"Thủ tục: {c.record.ten}. {c.record.view_situational()[:120]}. {c.record.view_summary()[:80]}" for c in candidates]
        scores = reranker.score(query, passages)
        for cand, sc in zip(candidates, scores):
            cand.rerank_score = sc

    # 4. Tính toán điểm Confidence thích ứng (Adaptive Confidence)
    for cand in candidates:
        if USE_LEXICAL and USE_DENSE:
            if cand.bm25_norm > 0.05 and cand.dense_similarity > 0.1:
                wd = w_dense / (w_dense + RRF_WEIGHT_LEXICAL)
                cand.confidence = wd * cand.dense_similarity + (1.0 - wd) * cand.bm25_norm
            else:
                # Câu hỏi khẩu ngữ/tình huống đời thường hoặc từ khoá đặc biệt:
                # Chọn điểm tốt nhất của mô hình, không để 0 điểm kéo tụt
                cand.confidence = max(cand.dense_similarity, cand.bm25_norm)
        else:
            cand.confidence = max(cand.dense_similarity, cand.bm25_norm)

    # Luôn sắp xếp danh sách ứng viên theo độ tin cậy thực tế (Confidence)
    candidates.sort(key=lambda c: -c.confidence)
    return candidates[:top_k]

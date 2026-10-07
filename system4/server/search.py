"""Tìm trong dữ liệu người dùng (NV3): từ khoá (SQLite FTS5, không phân biệt dấu) + nghĩa (bge-m3 qua Ollama, lưu trong
Qdrant chạy local mode) -> trộn thứ hạng (RRF) -> xếp hạng lại bằng reranker (bge-reranker-v2-m3, GPU; bật/tắt trong ⚙).

Qdrant local mode lưu ở runtime/qdrant; khi deploy đổi sang Qdrant server chỉ cần đổi _qdrant() (xem docs/SYSTEM4_DEPLOY.md).
"""
from __future__ import annotations
import atexit
import logging
import re
import threading
import unicodedata

import ollama

from . import config, db, settings

log = logging.getLogger("system4.search")
COLLECTION = "records"
DIM = 1024
RERANKER_DIR = config.S4_DIR / "models" / "bge-reranker-v2-m3"
_lock = threading.Lock()    # nạp model / chạy reranker
_qlock = threading.Lock()   # Qdrant local mode: một thao tác tại một thời điểm (luồng nạp dữ liệu + luồng trả lời)
_q = None
_rr = {"model": None, "tok": None, "device": None, "failed": False}


# ------------------------------------------------------------------ vector
def _qdrant():
    global _q
    with _lock:
        if _q is None:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            _q = QdrantClient(path=str(config.RUNTIME_DIR / "qdrant"))
            atexit.register(_q.close)   # đóng gọn khi tắt server (tránh cảnh báo lúc Python thoát)
            if not _q.collection_exists(COLLECTION):
                _q.create_collection(COLLECTION, vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))
        return _q


def embed(texts: list[str]) -> list[list[float]]:
    res = ollama.Client(host=config.OLLAMA_HOST, timeout=300).embed(
        model=settings.get("EMBED_MODEL"), input=[t[:3000] for t in texts], keep_alive="30m")
    return res["embeddings"]


def add_vectors(ids: list[int], vectors: list[list[float]], dataset_id: int, user_id: int) -> None:
    from qdrant_client.models import PointStruct
    q = _qdrant()
    with _qlock:
        q.upsert(COLLECTION, points=[PointStruct(id=i, vector=v, payload={"dataset_id": dataset_id, "user_id": user_id})
                                         for i, v in zip(ids, vectors)])


def delete_vectors(dataset_id: int) -> None:
    from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue
    q = _qdrant()
    with _qlock:
        q.delete(COLLECTION, points_selector=FilterSelector(filter=Filter(must=[
        FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id))])))


def _vector_search(query_vec: list[float], dataset_ids: list[int], limit: int) -> list[int]:
    from qdrant_client.models import FieldCondition, Filter, MatchAny
    q = _qdrant()
    with _qlock:
        res = q.query_points(COLLECTION, query=query_vec, limit=limit,
                                 query_filter=Filter(must=[FieldCondition(key="dataset_id", match=MatchAny(any=dataset_ids))]))
    return [int(p.id) for p in res.points]


# ----------------------------------------------------------------- từ khoá
_STOP = set("""là và của có cho các những được một này đó thì mà với không gì nào như thế nào ạ à ơi nhé vậy hả bạn mình tôi em
cần làm sao bao nhiêu ở đâu khi nào muốn hỏi giúp về theo trong""".split())


def _fts_query(text: str) -> str:
    words = [w for w in re.findall(r"\w+", unicodedata.normalize("NFC", text.lower())) if len(w) > 1 and w not in _STOP]
    return " OR ".join(f'"{w}"' for w in dict.fromkeys(words))


def _keyword_search(text: str, dataset_ids: list[int], limit: int) -> list[int]:
    q = _fts_query(text)
    if not q or not dataset_ids:
        return []
    marks = ",".join("?" * len(dataset_ids))
    try:
        rows = db.run(f"SELECT f.rowid id FROM records_fts f JOIN records r ON r.id = f.rowid "
                      f"WHERE records_fts MATCH ? AND r.dataset_id IN ({marks}) ORDER BY bm25(records_fts) LIMIT ?",
                      (q, *dataset_ids, limit), many=True)
    except Exception as e:   # câu truy vấn FTS lạ: bỏ qua phần từ khoá, vẫn còn tìm theo nghĩa
        log.warning("fts: %s", e)
        return []
    return [r["id"] for r in rows]


# ---------------------------------------------------------------- reranker
def _reranker():
    """Nạp reranker một lần (GPU fp16; không có GPU / thiếu bộ nhớ -> CPU). Thiếu model -> None (bỏ qua bước này)."""
    with _lock:
        if _rr["model"] is None and not _rr["failed"]:
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                tok = AutoTokenizer.from_pretrained(str(RERANKER_DIR))
                dev = "cuda" if torch.cuda.is_available() else "cpu"
                try:
                    m = AutoModelForSequenceClassification.from_pretrained(
                        str(RERANKER_DIR), dtype=torch.float16 if dev == "cuda" else torch.float32).to(dev).eval()
                except RuntimeError as e:   # hết bộ nhớ GPU -> chạy CPU (chậm hơn) thay vì làm sập
                    log.warning("reranker GPU lỗi (%s), chuyển CPU", e)
                    dev = "cpu"
                    m = AutoModelForSequenceClassification.from_pretrained(str(RERANKER_DIR)).eval()
                _rr.update(model=m, tok=tok, device=dev)
            except Exception as e:
                log.warning("không nạp được reranker: %s", e)
                _rr["failed"] = True
        return _rr if _rr["model"] is not None else None


def rerank(query: str, texts: list[str]) -> list[float] | None:
    r = _reranker()
    if not r or not texts:
        return None
    import torch
    with _lock, torch.no_grad():
        x = r["tok"]([[query, t[:1500]] for t in texts], padding=True, truncation=True, max_length=384,
                     return_tensors="pt").to(r["device"])
        return r["model"](**x).logits.view(-1).float().tolist()


def reranker_status() -> dict:
    return {"loaded": _rr["model"] is not None, "device": _rr["device"], "failed": _rr["failed"],
            "available": (RERANKER_DIR / "model.safetensors").is_file()}


# ------------------------------------------------------------------- tìm
def search(user_id: int, query: str) -> tuple[list[dict], dict]:
    """Tìm trong các bộ dữ liệu đang bật của người dùng. Trả (đoạn dữ liệu tốt nhất, thông tin đo)."""
    ds = db.active_datasets(user_id)
    ids = [d["id"] for d in ds]
    info = {"datasets": len(ids), "reranked": False}
    if not ids:
        return [], info
    n = settings.get("RETRIEVAL_CANDIDATES")
    kw = _keyword_search(query, ids, n)
    try:
        vec = _vector_search(embed([query])[0], ids, n)
    except Exception as e:
        log.warning("tìm theo nghĩa lỗi: %s", e)
        vec = []
    fused: dict[int, float] = {}
    for lst in (kw, vec):   # RRF: cộng 1/(60 + hạng) của mỗi cách tìm
        for rank, rid in enumerate(lst):
            fused[rid] = fused.get(rid, 0) + 1 / (60 + rank)
    order = sorted(fused, key=fused.get, reverse=True)[:n]
    recs = {r["id"]: r for r in db.get_records(order)}
    cands = [recs[i] for i in order if i in recs]
    info.update(keyword=len(kw), vector=len(vec), candidates=len(cands))
    if settings.get("RERANKER_ENABLED") and cands:
        scores = rerank(query, [c["text"] for c in cands])
        if scores is not None:
            info["reranked"] = True
            for c, s in zip(cands, scores):
                c["score"] = round(s, 2)
            cands = [c for c in sorted(cands, key=lambda c: c["score"], reverse=True) if c["score"] >= settings.get("RERANK_MIN_SCORE")]
    names = {d["id"]: d["name"] for d in ds}
    out = cands[:settings.get("RETRIEVAL_TOP_K")]
    for c in out:
        c["dataset"] = names.get(c["dataset_id"], "")
    return out, info


def warm_up() -> None:
    """Gọi lúc khởi động (luồng nền): nạp bge-m3 và reranker sẵn để câu hỏi đầu tiên không chờ 7-13 giây."""
    try:
        embed(["khởi động"])
    except Exception as e:
        log.warning("warm-up bge-m3: %s", e)
    if settings.get("RERANKER_ENABLED"):
        _reranker()

"""Tìm trong dữ liệu người dùng (NV3): từ khoá (SQLite FTS5, không phân biệt dấu) + nghĩa (bge-m3 qua Ollama, lưu trong
Qdrant chạy local mode) -> trộn thứ hạng (RRF) -> xếp hạng lại bằng reranker (bge-reranker-v2-m3, GPU; bật/tắt trong ⚙).

Qdrant local mode lưu ở runtime/qdrant; khi deploy đổi sang Qdrant server chỉ cần đổi _qdrant() (xem docs/SYSTEM4_DEPLOY.md).
"""
from __future__ import annotations
import atexit
import logging
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import ollama

from . import config, db, settings

log = logging.getLogger("system4.search")
COLLECTION = "records"
DIM = 1024
RERANKER_DIR = config.S4_DIR / "models" / "bge-reranker-v2-m3"
_lock = threading.Lock()    # nạp model / chạy reranker
_qlock = threading.Lock()   # Qdrant local mode: một thao tác tại một thời điểm (luồng nạp dữ liệu + luồng trả lời)
_q = None
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="s4-embed")
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
        model=settings.get("EMBED_MODEL"), input=[t[:3000] for t in texts], keep_alive=-1 if settings.get("KEEP_MODELS_LOADED") else "30m")
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


def _vector_search(query_vec: list[float], dataset_ids: list[int], limit: int) -> list[tuple[int, float]]:
    from qdrant_client.models import FieldCondition, Filter, MatchAny
    q = _qdrant()
    with _qlock:
        res = q.query_points(COLLECTION, query=query_vec, limit=limit,
                                 query_filter=Filter(must=[FieldCondition(key="dataset_id", match=MatchAny(any=dataset_ids))]))
    return [(int(p.id), round(float(p.score), 3)) for p in res.points]   # (id, độ giống cosine)


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
def search(user_id: int, query: str, dataset_ids: list[int] | None = None, overrides: dict | None = None) -> tuple[list[dict], dict]:
    """Tìm trong các bộ dữ liệu đang bật của người dùng (hoặc dataset_ids chỉ định — phòng thử tìm kiếm của dev).
    overrides: đổi tạm RETRIEVAL_CANDIDATES / RETRIEVAL_TOP_K / RERANKER_ENABLED / RERANK_MIN_SCORE (chỉ cho lần gọi này).
    Trả (đoạn gửi cho AI, thông tin) — info["candidates"] = bảng xếp hạng đầy đủ cho bộ công cụ dev."""
    cfg = lambda k: (overrides or {}).get(k, settings.get(k))
    if dataset_ids is None:
        ds = db.active_datasets(user_id)
    else:
        ds = [d for d in (db.get_dataset(i) for i in dataset_ids) if d and d["status"] == "ready"]
    ids = [d["id"] for d in ds]
    names = {d["id"]: d["name"] for d in ds}
    info = {"datasets": len(ids), "reranked": False, "query": query, "fts_query": _fts_query(query),
            "settings": {k: cfg(k) for k in ("RETRIEVAL_CANDIDATES", "RETRIEVAL_TOP_K", "RERANKER_ENABLED", "RERANK_MIN_SCORE")}}
    if not ids:
        info["candidates"] = []
        return [], info
    n = cfg("RETRIEVAL_CANDIDATES")
    ms = {}
    t0 = time.perf_counter()
    emb = _pool.submit(embed, [query])   # tạo vector câu hỏi (Ollama) song song với tìm từ khoá (SQLite)
    kw = _keyword_search(query, ids, n)
    ms["keyword_ms"] = int((time.perf_counter() - t0) * 1000)
    try:
        qv = emb.result()[0]
        ms["embed_ms"] = int((time.perf_counter() - t0) * 1000)
        t1 = time.perf_counter()
        vec = _vector_search(qv, ids, n)
        ms["vector_ms"] = int((time.perf_counter() - t1) * 1000)
    except Exception as e:
        log.warning("tìm theo nghĩa lỗi: %s", e)
        vec = []
    kw_rank = {rid: r + 1 for r, rid in enumerate(kw)}
    vec_rank = {rid: (r + 1, sc) for r, (rid, sc) in enumerate(vec)}
    fused: dict[int, float] = {}
    for rid, r in kw_rank.items():   # RRF: cộng 1/(60 + hạng) của mỗi cách tìm
        fused[rid] = fused.get(rid, 0) + 1 / (59 + r)
    for rid, (r, _) in vec_rank.items():
        fused[rid] = fused.get(rid, 0) + 1 / (59 + r)
    order = sorted(fused, key=fused.get, reverse=True)[:n]
    recs = {r["id"]: r for r in db.get_records(order)}
    cands = [recs[i] for i in order if i in recs]
    info.update(keyword=len(kw), vector=len(vec), candidates_n=len(cands))
    scores = None
    if cfg("RERANKER_ENABLED") and cands:
        t1 = time.perf_counter()
        scores = rerank(query, [c["text"] for c in cands])
        ms["rerank_ms"] = int((time.perf_counter() - t1) * 1000)
    info["timing"] = ms
    if scores is not None:
        info["reranked"] = True
        for c, sc in zip(cands, scores):
            c["score"] = round(sc, 2)
        ranked = sorted(cands, key=lambda c: c["score"], reverse=True)
        passed = [c for c in ranked if c["score"] >= cfg("RERANK_MIN_SCORE")]
    else:
        ranked = passed = cands
    out = passed[:cfg("RETRIEVAL_TOP_K")]
    sent = {c["id"] for c in out}
    for c in out:
        c["dataset"] = names.get(c["dataset_id"], "")
    info["candidates"] = [{
        "id": c["id"], "title": c["title"], "dataset": names.get(c["dataset_id"], ""), "source": c["source"],
        "keyword_rank": kw_rank.get(c["id"]), "vector_rank": (vec_rank.get(c["id"]) or (None, None))[0],
        "vector_score": (vec_rank.get(c["id"]) or (None, None))[1], "rrf": round(fused[c["id"]], 4),
        "rerank": c.get("score"), "passed": c in passed, "sent": c["id"] in sent, "text": c["text"][:400],
    } for c in ranked]
    return out, info


def warm_up() -> None:
    """Gọi lúc khởi động (luồng nền): nạp bge-m3 và reranker sẵn để câu hỏi đầu tiên không chờ 7-13 giây."""
    try:
        embed(["khởi động"])
    except Exception as e:
        log.warning("warm-up bge-m3: %s", e)
    if settings.get("RERANKER_ENABLED"):
        _reranker()

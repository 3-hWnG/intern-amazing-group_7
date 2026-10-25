"""Phương án B của đợt sửa câu khó (24/10/2026): truy hồi THEO NGHĨA + xếp hạng lại (cross-encoder) + ngưỡng từ chối hiệu chỉnh trên dev.

Luật vẫn quyết định theo dữ liệu: model chỉ CHẤM ĐIỂM các thủ tục có thật (không sinh chữ, không tự điền mã). Ứng viên = hợp các thủ tục
luật xếp đầu + các thủ tục trong phạm vi (in_scope = 1, 542 thủ tục cấp xã toàn quốc) gần nghĩa nhất với câu hỏi. Reranker chấm từng cặp
(câu hỏi, "tên. lĩnh vực. kết quả. đối tượng"); điểm cao nhất < ngưỡng từ chối -> không có thủ tục phù hợp; đủ ngưỡng -> chọn thủ tục đó.

Model (không tải mới, đều đã có trên máy):
  S3_SEM_MODEL=bge     (mặc định) bge-m3 qua Ollama + bge-reranker-v2-m3 (system4/models, cùng model System 4 đang dùng)
  S3_SEM_MODEL=aiteam  AITeamVN/Vietnamese_Embedding + AITeamVN/Vietnamese_Reranker (cache Hugging Face, local_files_only)
Bật: S3_SEMANTIC=1. Ngưỡng: S3_SEM_TAU_OOS (từ chối khi điểm tốt nhất dưới mức này), S3_SEM_TAU_SWAP (đổi thủ tục của luật khi điểm
thủ tục khác hơn điểm của thủ tục luật chọn ít nhất mức này). Vector thủ tục lưu đệm theo content_sha256 của DB ở data/runtime/semantic/.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "runtime" / "semantic"
BGE_RERANKER = ROOT / "system4" / "models" / "bge-reranker-v2-m3"
_lock = threading.Lock()
_state: dict = {}


def enabled() -> bool:
    return os.environ.get("S3_SEMANTIC", "0") == "1"


def query_text(question: str, segs) -> str:
    """Chữ đưa reranker. S3_SEM_QUERY=full (mặc định): cả câu đã bỏ lời chào / cảm ơn. =seg: chỉ các đoạn luật coi là YÊU CẦU (đoạn ra thủ tục
    hoặc có mục hỏi) — thư kể dài làm reranker chấm thấp cả thủ tục đúng; rỗng thì quay về cả câu."""
    from system3.retrieval.query import strip_letter
    if os.environ.get("S3_SEM_QUERY", "full") == "seg":
        t = " ; ".join(s.text for s in segs if s.proc_id or s.query.fields)
        if t.strip():
            return t
    return strip_letter(question)


def model_kind() -> str:
    return os.environ.get("S3_SEM_MODEL", "bge")


def tau_oos() -> float:
    return float(os.environ.get("S3_SEM_TAU_OOS", "-2.0"))


def tau_swap() -> float:
    return float(os.environ.get("S3_SEM_TAU_SWAP", "2.0"))


def tau_rescue() -> float:
    """Luật KHÔNG chọn được thủ tục (từ chối / hỏi lại) mà reranker chấm thủ tục tốt nhất >= mức này -> trả lời thủ tục đó. Mặc định 99 = tắt
    (lượt lưới đầu 24/10 cứu MỌI câu bị từ chối có điểm trên ngưỡng thấp: hành vi "trả lời" tăng nhưng phần lớn sai thủ tục)."""
    return float(os.environ.get("S3_SEM_TAU_RESCUE", "99"))


def _proc_rows(conn) -> list[dict]:
    rows = conn.execute("SELECT p.proc_id, p.name, p.domain, p.results, p.subject_types FROM procedures p JOIN proc_flat f ON f.proc_id = p.proc_id "
                        "WHERE p.status = 'active' AND f.in_scope = 1 ORDER BY p.proc_id").fetchall()
    out = []
    for r in rows:
        t = f"{r[1]}. Lĩnh vực: {r[2]}."
        if r[3]:
            t += f" Kết quả: {r[3][:120]}."
        if r[4]:
            t += f" Đối tượng: {r[4][:120]}."
        out.append({"proc_id": r[0], "name": r[1], "text": t})
    return out


def _embed(texts: list[str], kind: str) -> np.ndarray:
    if kind == "aiteam":
        m, tok, dev = _hf_encoder()
        import torch
        vecs = []
        with torch.no_grad():
            for i in range(0, len(texts), 32):
                x = tok(texts[i:i + 32], padding=True, truncation=True, max_length=256, return_tensors="pt").to(dev)
                h = m(**x).last_hidden_state[:, 0]          # bge-m3: vector CLS
                vecs.append(torch.nn.functional.normalize(h.float(), dim=-1).cpu().numpy())
        return np.vstack(vecs)
    import ollama
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    out = []
    for i in range(0, len(texts), 64):
        out += ollama.Client(host=host, timeout=300).embed(model="bge-m3", input=[t[:2000] for t in texts[i:i + 64]], keep_alive="10m")["embeddings"]
    v = np.asarray(out, dtype=np.float32)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


def _hf_encoder():
    if "enc" not in _state:
        import torch
        from transformers import AutoModel, AutoTokenizer
        name = "AITeamVN/Vietnamese_Embedding"
        tok = AutoTokenizer.from_pretrained(name, local_files_only=True)
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        m = AutoModel.from_pretrained(name, local_files_only=True, dtype=torch.float16 if dev == "cuda" else torch.float32).to(dev).eval()
        _state["enc"] = (m, tok, dev)
    return _state["enc"]


def _reranker():
    key = "rr_" + model_kind()
    if key not in _state:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        src, kw = (("AITeamVN/Vietnamese_Reranker", {"local_files_only": True}) if model_kind() == "aiteam" else (str(BGE_RERANKER), {}))
        tok = AutoTokenizer.from_pretrained(src, **kw)
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        m = AutoModelForSequenceClassification.from_pretrained(src, dtype=torch.float16 if dev == "cuda" else torch.float32, **kw).to(dev).eval()
        _state[key] = (m, tok, dev)
    return _state[key]


def _index(conn):
    """(danh sách thủ tục trong phạm vi, ma trận vector) — tính một lần, lưu đệm theo nội dung DB + model."""
    kind = model_kind()
    if _state.get("idx_kind") == kind:
        return _state["procs"], _state["vecs"]
    procs = _proc_rows(conn)
    h = hashlib.sha256(json.dumps([p["text"] for p in procs], ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    path = CACHE / f"procs_{kind}_{h}.npy"
    if path.exists():
        vecs = np.load(path)
    else:
        vecs = _embed([p["text"] for p in procs], kind)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.save(path, vecs)
    _state.update(procs=procs, vecs=vecs, idx_kind=kind, byid={p["proc_id"]: p for p in procs})
    return procs, vecs


def candidates(conn, question: str, rule_ids: list[str], k_dense: int = 10, k_rules: int = 8) -> list[dict]:
    """Hợp ứng viên của luật (giữ thứ tự) + thủ tục gần nghĩa nhất; mỗi mục {proc_id, name, text}."""
    with _lock:
        procs, vecs = _index(conn)
        qv = _embed([question], model_kind())[0]
    sims = vecs @ qv
    dense = [procs[i] for i in np.argsort(-sims)[:k_dense]]
    byid = _state["byid"]
    out, seen = [], set()
    for pid in rule_ids[:k_rules]:
        if pid not in seen:
            seen.add(pid)
            p = byid.get(pid)
            if p is None:       # thủ tục luật chọn nằm ngoài in_scope (bản tỉnh, cấp tỉnh...): vẫn chấm theo tên
                r = conn.execute("SELECT name, domain FROM procedures WHERE proc_id = ? AND status = 'active'", (pid,)).fetchone()
                if not r:
                    continue
                p = {"proc_id": pid, "name": r[0], "text": f"{r[0]}. Lĩnh vực: {r[1]}."}
            out.append(p)
    for p in dense:
        if p["proc_id"] not in seen:
            seen.add(p["proc_id"])
            out.append(p)
    return out


def score(question: str, cands: list[dict]) -> list[float]:
    if not cands:
        return []
    import torch
    with _lock:
        m, tok, dev = _reranker()
        with torch.no_grad():
            x = tok([[question[:1500], c["text"]] for c in cands], padding=True, truncation=True, max_length=384, return_tensors="pt").to(dev)
            return m(**x).logits.view(-1).float().tolist()


def decide(conn, question: str, rule_ids: list[str], rule_pick: str | None) -> dict:
    """-> {action, pick, best, best_score, rule_score, ranked}. action: keep (giữ luật) | none (không thủ tục nào phù hợp: từ chối) |
    swap (đổi thủ tục của luật) | rescue (luật không chọn được thủ tục, reranker chắc chắn)."""
    cands = candidates(conn, question, rule_ids)
    sc = score(question, cands)
    ranked = sorted(zip(cands, sc), key=lambda x: -x[1])
    best, best_s = (ranked[0][0]["proc_id"], ranked[0][1]) if ranked else (None, -99.0)
    rule_s = next((s for c, s in zip(cands, sc) if c["proc_id"] == rule_pick), None)
    if rule_pick is None:
        action, pick = ("rescue", best) if best is not None and best_s >= tau_rescue() else ("keep", None)
    elif best is None or best_s < tau_oos():
        action, pick = "none", None
    elif best != rule_pick and rule_s is not None and best_s - rule_s >= tau_swap():      # thủ tục luật chọn không được chấm: không so được -> giữ
        action, pick = "swap", best
    else:
        action, pick = "keep", rule_pick       # thủ tục luật chọn gần bằng điểm tốt nhất: giữ quyết định của luật
    return {"action": action, "pick": pick, "best": best, "best_score": round(best_s, 3), "rule_score": None if rule_s is None else round(rule_s, 3),
            "ranked": [(c["proc_id"], round(s, 3)) for c, s in ranked[:6]]}

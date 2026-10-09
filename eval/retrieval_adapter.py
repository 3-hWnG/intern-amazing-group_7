"""Adapter đo Phase 2: chỉ retrieval (không LLM). Chạy: python run.py --adapter retrieval_adapter:adapter --name phase2"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from system3.data import api
from system3.retrieval import Index, resolve

_idx = None


def adapter(turns):
    global _idx
    if _idx is None:
        _idx = Index(api.connect())
    t0 = time.perf_counter()
    r = resolve(_idx, turns)
    tasks = []
    for s in r.segments:
        if s.proc_id:
            cands = [s.proc_id] + [h.proc_id for h in s.hits if h.proc_id != s.proc_id]
            tasks.append({"proc_id": s.proc_id, "candidates": cands[:5], "fields": s.query.fields or None, "quantity": None})
    return {"tasks": tasks, "behavior": r.behavior, "answer_text": "", "fields_supported": True,
            "latency_ms": (time.perf_counter() - t0) * 1000,
            "extra": {"seg": [(s.text[:40], s.reason, s.query.terms, [(h.proc_id, h.score, h.cov) for h in s.hits[:2]]) for s in r.segments],
                      "is_strong": r.behavior == "answer" and not r.chitchat}}

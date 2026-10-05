"""Adapter đo Phase 3+: Planner (luật + Qwen3-4B). Chạy: python run.py --adapter planner_adapter:adapter --name phase3
Biến môi trường: S3_USE_LLM=0 để chỉ chạy luật."""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(ROOT, "system3", "server")]
from planner import plan as make_plan  # noqa: E402

USE_LLM = os.environ.get("S3_USE_LLM", "1") == "1"


def adapter(turns):
    t0 = time.perf_counter()
    p = make_plan(turns)  # Planner mặc định luật; S3_PLANNER_LLM=1 để bật LLM
    ms = (time.perf_counter() - t0) * 1000
    tasks = []
    for t in p.tasks:
        if t.procedure_id:
            c = [t.procedure_id] + [x for x in t.candidates if x != t.procedure_id]
            tasks.append({"proc_id": t.procedure_id, "candidates": c[:5], "fields": t.fields or None, "quantity": t.quantity})
    acts = [t.action for t in p.tasks]
    if p.needs_clarification:
        beh = "clarify"
    elif tasks or (acts and all(a == "chitchat" for a in acts)):
        beh = "answer"
    else:
        beh = "apologize"
    return {"tasks": tasks, "behavior": beh, "answer_text": "", "fields_supported": True, "latency_ms": ms,
            "extra": {"source": p.source, "llm_ms": p.llm_ms, "acts": acts, "note": p.note}}

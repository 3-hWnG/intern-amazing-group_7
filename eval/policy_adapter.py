"""Adapter đo Phase 4: pre_check -> Planner -> Policy/Router. Chạy: python run.py --adapter policy_adapter:adapter --name phase4
S3_USE_LLM=0 để chỉ chạy luật."""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(HERE, "..", "server")]   # Phase 28: không giả định thư mục tên system3
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402

USE_LLM = os.environ.get("S3_USE_LLM", "1") == "1"


def adapter(turns):
    t0 = time.perf_counter()
    last = turns[-1]["text"]
    pc = pre_check(last)
    turns = turns[:-1] + [{"role": "user", "text": pc["text"]}]
    if "injection" in pc["flags"]:
        from planner.planner import Plan
        p = Plan(tasks=[], source="rules")
    else:
        p = make_plan(turns, use_llm=USE_LLM)
    r = check(p, user_text=pc["text"], flags=pc["flags"])
    tasks = []
    for t, rt in zip(p.tasks, r.tasks):
        if rt.route == "direct":
            c = [rt.procedure_id] + [x for x in t.candidates if x != rt.procedure_id]
            tasks.append({"proc_id": rt.procedure_id, "candidates": c[:5], "fields": rt.fields or None, "quantity": rt.quantity})
    beh = {"answer": "answer", "chitchat": "answer", "clarify": "clarify", "apologize": "apologize"}[r.behavior]
    return {"tasks": tasks, "behavior": beh, "answer_text": "", "fields_supported": True,
            "latency_ms": (time.perf_counter() - t0) * 1000,
            "extra": {"source": p.source, "llm_ms": p.llm_ms, "routes": [(x.route, x.reason) for x in r.tasks], "flags": r.flags}}

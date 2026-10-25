"""Adapter đo Phase 5: pre_check -> Planner -> Policy -> Answerer. Có answer_text nên chấm được bịa số / không công bố / trích nguồn.
Chạy: python run.py --adapter answer_adapter:adapter --name phase5      (S3_USE_LLM=0: chỉ luật)
Phase 19: S3_PLANNER_MODE=hybrid chạy Planner hybrid (luật + Qwen3-4B); S3_PLANNER_LLM_CACHE=file.jsonl phát lại đề xuất LLM (quét ngưỡng không gọi lại);
PLANNER_LLM_CONFIDENCE=0.9 đổi ngưỡng. extra.llm = nhật ký planner_llm."""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(HERE, "..", "server")]   # Phase 28: không giả định thư mục tên system3
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from answer import answer  # noqa: E402
from system3.data import api  # noqa: E402

USE_LLM = os.environ.get("S3_USE_LLM", "1") == "1"
_conn = None


def _llm():
    """S3_USE_LLM giờ điều khiển bước SINH CHỮ của Answerer (Planner luôn chạy luật)."""
    if not USE_LLM:
        return None
    from core.llm import chat_json
    return chat_json


def adapter(turns):
    global _conn
    _conn = _conn or api.connect()
    t0 = time.perf_counter()
    pc = pre_check(turns[-1]["text"])
    turns = turns[:-1] + [{"role": "user", "text": pc["text"]}]
    if "injection" in pc["flags"]:
        from planner.planner import Plan
        p = Plan(tasks=[], source="rules")
    else:
        p = make_plan(turns)
    r = check(p, user_text=pc["text"], conn=_conn, flags=pc["flags"])
    a = answer(r, conn=_conn, question=pc["text"], llm=_llm())
    text = "\n\n".join(f"{b.get('title', '')}\n{b['text']}" + "".join(f"\n{s['label']} {s['url']}" for s in b.get("sources", [])) for b in a["blocks"])
    tasks = []
    for t, rt in zip(p.tasks, r.tasks):
        if rt.route == "direct":
            c = [rt.procedure_id] + [x for x in t.candidates if x != rt.procedure_id]
            tasks.append({"proc_id": rt.procedure_id, "candidates": c[:5], "fields": rt.fields or None, "quantity": rt.quantity})
    beh = {"answer": "answer", "chitchat": "answer", "clarify": "clarify", "apologize": "apologize"}[r.behavior]
    nps = bool(__import__("re").search(r"không công bố|không có nghĩa là miễn phí|chưa tra được|không ghi", text))
    return {"tasks": tasks, "behavior": beh, "answer_text": text, "says_not_published": nps, "fields_supported": True,
            "latency_ms": (time.perf_counter() - t0) * 1000,
            "extra": {"ctx": p.ctx, "source": p.source, "llm": p.llm_trace, "verify": a["verify"], "routes": [(x.route, x.reason) for x in r.tasks]}}

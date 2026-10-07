"""Phase 27: chọn các ca có bước LLM sinh chữ (Answer Composer) từ DEV cũ + ctx + p23 (nằm trong DEV) + p26. KHÔNG dùng bộ mù/team/HOLDOUT.
Một ca "có bước LLM" = chạy pipeline với LLM giả (không gọi Ollama) mà answer() gọi compose() ít nhất một lần
(task có conditions -> 'condition'; >=2 task relation=compare -> 'compare'). Ghi cases_composer.jsonl (+ các ca tự soạn trong eval/composer_own.py).
Chạy: cd eval && PYTHONPATH=<ROOT> S3_USE_LLM=0 S3_NO_WARMUP=1 python build_composer_set.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(os.path.dirname(HERE), "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from answer import answer  # noqa: E402
from system3.data import api  # noqa: E402

_conn = api.connect()


def run_case(turns, llm=None):
    """Như answer_adapter.adapter nhưng trả (answer dict, routed) và nhận llm tường minh."""
    pc = pre_check(turns[-1]["text"])
    turns = turns[:-1] + [{"role": "user", "text": pc["text"]}]
    if "injection" in pc["flags"]:
        from planner.planner import Plan
        p = Plan(tasks=[], source="rules")
    else:
        p = make_plan(turns)
    r = check(p, user_text=pc["text"], conn=_conn, flags=pc["flags"])
    return answer(r, conn=_conn, question=pc["text"], llm=llm), r, pc["text"]


def triggers(turns):
    calls = []
    def spy(system, user, schema=None, timeout=None):
        calls.append("compare" if "So sánh" in user else "condition")
        return {}
    run_case(turns, spy)
    return calls


def main():
    out = []
    def add(cid, src, turns, exp=None):
        t = triggers(turns)
        if t:
            out.append({"id": cid, "src": src, "turns": turns, "triggers": t, "checks": (exp or {}).get("checks") or []})
    for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8"):
        c = json.loads(l)
        if c["split"] == "dev":
            add(c["id"], "dev:" + c["source"], c["turns"], c["expected"])
    for l in open(os.path.join(HERE, "cases_ctx.jsonl"), encoding="utf-8"):
        c = json.loads(l)
        add(c["id"], "ctx:" + c["split"], c["turns"], c["expected"])
    for l in open(os.path.join(HERE, "cases_p26.jsonl"), encoding="utf-8"):
        c = json.loads(l)
        add(c["id"], "p26", [{"role": "user", "text": c["question"]}])
    n_real = len(out)
    try:
        from composer_own import OWN
        for cid, q, conds in OWN:
            t = [{"role": "user", "text": q}]
            tr = triggers(t)
            if tr:      # ca tự soạn không kích hoạt bước LLM thì bỏ (không đo được gì)
                out.append({"id": cid, "src": "composer", "turns": t, "triggers": tr, "checks": [], "own_conditions": conds})
    except ImportError:
        pass
    with open(os.path.join(HERE, "cases_composer.jsonl"), "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print("ca có bước LLM từ bộ có sẵn:", n_real, "| tổng ghi:", len(out), "|", Counter(r["src"].split(":")[0] for r in out), Counter(x for r in out for x in r["triggers"]))


if __name__ == "__main__":
    main()

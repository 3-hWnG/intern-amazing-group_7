"""Chỉ số CONCISE / ĐÚNG TRỌNG TÂM (Phase 17). python run_concise.py [--name x]   (PYTHONPATH=.. S3_USE_LLM=0)
Chấm bằng luật trên câu trả lời thật, không cần LLM. Không đọc bộ mù (HOLDOUT-2/3).
 - task_thừa     : số thủ tục/task trả về nhiều hơn số ý cần (đúng 'dư thủ tục' nhóm phàn nàn)
 - mục_thừa      : mục (tiêu đề 'Lệ phí:', 'Các bước thực hiện:'...) không được hỏi
 - mục_thiếu     : mục được hỏi mà câu trả lời không có
 - focus         : % câu answer không task thừa, không mục thừa, không mục thiếu
 - độ dài        : ký tự câu trả lời (trung vị, p90) và ký tự / mục được hỏi
Nguồn: DEV+HOLDOUT cũ (cases.jsonl, có fields), ctx, team (task + độ dài), pseudo_real (độ dài)."""
import argparse, json, os, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402
from answer.answerer import FIELD_TITLE  # noqa: E402

TITLE2F = {v: k for k, v in FIELD_TITLE.items()}
HEAD = re.compile(r"^(" + "|".join(map(re.escape, TITLE2F)) + r"):", re.M)


def sections(text):
    return {TITLE2F[m] for m in HEAD.findall(text)}


def p90(xs):
    xs = sorted(xs)
    return xs[int(0.9 * (len(xs) - 1))] if xs else 0


def measure(out, exp_tasks, exp_fields):
    """exp_fields: set các field cần (rỗng = không biết)."""
    tops = [t for t in out["tasks"] if t.get("proc_id")]
    got = sections(out["answer_text"])
    r = dict(task_thua=max(0, len(tops) - exp_tasks), chars=len(out["answer_text"]), n_sec=len(got))
    if exp_fields:
        r["muc_thua"] = sorted(got - exp_fields)
        r["muc_thieu"] = sorted(exp_fields - got)
    else:
        r["muc_thua"], r["muc_thieu"] = None, None
    r["focus"] = r["task_thua"] == 0 and not (r["muc_thua"] or r["muc_thieu"])
    return r


def load(name):
    return [json.loads(l) for l in open(os.path.join(HERE, name), encoding="utf-8")]


def run_dev():
    rows = []
    for c in load("cases.jsonl"):
        ex = c["expected"]
        if ex["behavior"] != "answer":
            continue
        sc = [t for t in ex["tasks"] if t["acceptable_proc_ids"]]
        if not sc:
            continue
        out = answer_adapter.adapter(c["turns"])
        if out["behavior"] != "answer":
            continue
        ef = set().union(*[set(t["fields"]) for t in sc])
        if any(t.get("evidence_demand", "none") != "none" for t in sc):
            ef.add("legal_basis")   # hỏi căn cứ/nguồn thì căn cứ pháp lý là mục được hỏi
        r = measure(out, len(sc), ef)
        r.update(id=c["id"], cat=c["category"], split=c.get("split", "dev"), nf=len(ef))
        rows.append(r)
    return rows


def run_ctx():
    rows = []
    for c in load("cases_ctx.jsonl"):
        ex = c["expected"]
        sc = [t for t in ex["tasks"] if t["acceptable_proc_ids"]]
        if ex["behavior"] != "answer" or not sc:
            continue
        out = answer_adapter.adapter(c["turns"])
        if out["behavior"] != "answer":
            continue
        ef = set(sc[0].get("fields") or [])
        if ef and sc[0].get("evidence_demand", "none") != "none":
            ef.add("legal_basis")
        r = measure(out, 1, ef)
        r.update(id=c["id"], cat=c["category"], split="ctx", nf=len(ef))
        rows.append(r)
    return rows


def run_team():
    rows = []
    for c in json.load(open(os.path.join(HERE, "cases_team.json"), encoding="utf-8")):
        if c["beh"] != "answer":
            continue
        h = []
        for q in c["turns"]:
            h.append({"role": "user", "text": q}); out = answer_adapter.adapter(h); h.append({"role": "assistant", "text": out["answer_text"]})
        r = measure(out, c["max_tasks"], set())
        r.update(id=c["id"], cat=c["group"], split="team", nf=0)
        rows.append(r)
    return rows


def run_pseudo():
    rows = []
    for c in json.load(open(os.path.join(HERE, "cases_pseudo_real.json"), encoding="utf-8")):
        if "turns" in c or c["beh"] != "answer":
            continue
        out = answer_adapter.adapter([{"role": "user", "text": c["q"]}])
        if out["behavior"] != "answer":
            continue
        r = measure(out, 1, set())
        r.update(id=c["id"], cat="pseudo", split="pseudo", nf=0)
        rows.append(r)
    return rows


def report(label, rows):
    if not rows:
        return f"| {label} | 0 |"
    f = [r for r in rows if r["muc_thua"] is not None]
    ch = [r["chars"] for r in rows]
    foc = f"{100 * sum(r['focus'] for r in f) / len(f):.0f}% ({sum(r['focus'] for r in f)}/{len(f)})" if f else "-"
    tt = sum(1 for r in rows if r["task_thua"])
    mt = sum(1 for r in f if r["muc_thua"])
    mi = sum(1 for r in f if r["muc_thieu"])
    return (f"| {label} | {len(rows)} | {foc} | {tt}/{len(rows)} | {mt}/{len(f) or 0} | {mi}/{len(f) or 0} | "
            f"{int(statistics.median(ch))} | {p90(ch)} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="concise")
    ap.add_argument("--no-blind", action="store_true", help="bỏ team/pseudo_real (đo hybrid: chỉ DEV/ctx, không đưa bộ nghiệm thu qua LLM)")
    a = ap.parse_args()
    S = {"dev": [], "holdout": []}
    for r in run_dev():
        S[r["split"]].append(r)
    parts = [("DEV", S["dev"]), ("HOLDOUT cũ", S["holdout"]), ("ctx", run_ctx())] + ([] if a.no_blind else [("team", run_team()), ("pseudo_real", run_pseudo())])
    md = ["| bộ | n | focus | task thừa | mục thừa | mục thiếu | ký tự trung vị | p90 |", "|---|---|---|---|---|---|---|---|"]
    md += [report(l, rs) for l, rs in parts]
    print("\n".join(md))
    allr = [r for _, rs in parts for r in rs]
    ex = {}
    for r in allr:
        for s in r["muc_thua"] or []:
            ex[s] = ex.get(s, 0) + 1
    print("mục thừa hay gặp:", dict(sorted(ex.items(), key=lambda x: -x[1])))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump({"table_md": "\n".join(md), "cases": allr}, open(os.path.join(HERE, "results", a.name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

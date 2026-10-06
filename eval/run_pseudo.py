"""Đo bộ pseudo_real (cases_pseudo_real.json). python run_pseudo.py [-v]  (PYTHONPATH=.. S3_USE_LLM=0). Chạy 1 lần, KHÔNG tune."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SRC = ARGS[0] if ARGS else "cases_pseudo_real.json"   # python run_pseudo.py cases_h4.json h4
NAME = ARGS[1] if len(ARGS) > 1 else "pseudo_real"
cases = json.load(open(os.path.join(HERE, SRC), encoding="utf-8"))
rows = []


def judge(exp_ids, beh, out):
    tops = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
    cands = [c for t in out["tasks"] for c in t.get("candidates", [])]
    return dict(beh_ok=out["behavior"] == beh, top1=bool(tops) and tops[0] in exp_ids,
                top3=any(c in exp_ids for c in cands[:3]), got=out["behavior"], tops=tops[:2])


for c in cases:
    if "turns" in c:
        hist = []
        for i, t in enumerate(c["turns"]):
            hist.append({"role": "user", "text": t["q"]})
            out = answer_adapter.adapter(hist)
            hist.append({"role": "assistant", "text": out["answer_text"]})
            rows.append(dict(id=f"{c['id']}.{i+1}", q=t["q"], beh=t["beh"], exp=t["expect_ids"], **judge(t["expect_ids"], t["beh"], out)))
    else:
        out = answer_adapter.adapter([{"role": "user", "text": c["q"]}])
        rows.append(dict(id=c["id"], q=c["q"], beh=c["beh"], exp=c["expect_ids"], **judge(c["expect_ids"], c["beh"], out)))

ans = [r for r in rows if r["beh"] == "answer"]
print(f"n={len(rows)}  hành vi đúng {sum(r['beh_ok'] for r in rows)}/{len(rows)}")
print(f"answer n={len(ans)}  top1 {sum(r['top1'] for r in ans)}/{len(ans)}  top3 {sum(r['top3'] for r in ans)}/{len(ans)}")
for b in ("clarify", "apologize"):
    s = [r for r in rows if r["beh"] == b]
    print(f"{b} n={len(s)} đúng hành vi {sum(r['beh_ok'] for r in s)}/{len(s)}")
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump(rows, open(os.path.join(HERE, "results", NAME + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if "-v" in sys.argv:
    for r in rows:
        if not r["beh_ok"] or (r["beh"] == "answer" and not r["top1"]):
            print("FAIL", r["id"], r["q"], "| exp", r["beh"], r["exp"], "| got", r["got"], r["tops"])

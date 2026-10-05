"""Quét tham số retrieval CHỈ trên split DEV (trường `split` trong cases.jsonl). HOLDOUT chỉ in khi thêm --holdout (nghiệm thu, không để chọn tham số)."""
import itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import run as R
from system3.retrieval import rank
from retrieval_adapter import adapter

cases = [json.loads(l) for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8")]
WITH_HOLD = "--holdout" in sys.argv

def evaluate(params):
    for k, v in params.items(): setattr(rank, k, v)
    out = {"dev": [0, 0, 0, 0], "holdout": [0, 0, 0, 0]}  # top1, top3 (answer w/ proc), behavior ok, n
    cnt = {"dev": [0, 0], "holdout": [0, 0]}
    for c in cases:
        s = c.get("split", "dev")
        if s == "holdout" and not WITH_HOLD:
            continue
        r = R.score_case(c, adapter(c["turns"]))
        out[s][2] += bool(r["behavior_ok"]); out[s][3] += 1
        if r["top1"] is not None:
            cnt[s][0] += 1
            out[s][0] += bool(r["top1"]); out[s][1] += bool(r["top3"])
    return {s: (out[s][0] / max(1, cnt[s][0]), out[s][1] / max(1, cnt[s][0]), out[s][2] / max(1, out[s][3])) for s in out}

if __name__ == "__main__":
    grid = {"PREC_BASE": [0.55, 0.7, 0.85], "CONTEXT_MISS": [0.3, 0.5, 0.7], "ACCEPT_SCORE": [0.55, 0.62, 0.7], "ACCEPT_COV": [0.5, 0.6, 0.7]}
    rows = []
    for combo in itertools.product(*grid.values()):
        p = dict(zip(grid, combo))
        e = evaluate(p)
        rows.append((e["dev"][0] + e["dev"][2], p, e))
    rows.sort(key=lambda x: -x[0])
    for sc, p, e in rows[:8]:
        print(p, "DEV top1 %.2f top3 %.2f beh %.2f" % e["dev"] + (" | HOLDOUT top1 %.2f top3 %.2f beh %.2f" % e["holdout"] if WITH_HOLD else ""))

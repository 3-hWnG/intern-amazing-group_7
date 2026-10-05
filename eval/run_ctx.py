"""Đo bộ hội thoại ctx-dev. python run_ctx.py [--name x] [-v]   (PYTHONPATH=.. S3_USE_LLM=0)
Chấm lượt cuối: top-1 thuộc đáp án; kind h/forbid: không task nào mang proc bị cấm. Ghi results/<name>.json."""
import argparse, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="ctx")
ap.add_argument("-v", action="store_true")
ap.add_argument("--split", default="all")
a = ap.parse_args()
cases = [json.loads(l) for l in open(os.path.join(HERE, "cases_ctx.jsonl"), encoding="utf-8")]
cases = [c for c in cases if a.split in ("all", c["split"])]
res, by = [], defaultdict(list)
for c in cases:
    out = answer_adapter.adapter(c["turns"])
    ex = c["expected"]
    tops = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
    acc = set(ex["tasks"][0]["acceptable_proc_ids"]) if ex["tasks"] else set()
    bad = [p for p in tops if p in set(ex["forbid_proc_ids"])]
    if acc:
        ok = bool(tops) and tops[0] in acc and not bad
    else:                                   # độc lập, không có thủ tục: không được trả thủ tục cũ
        ok = not bad and out["behavior"] != "clarify"
    fields = out["tasks"][0]["fields"] if out["tasks"] else None
    fo = None
    if ex["tasks"] and ex["tasks"][0]["fields"]:
        fo = set(fields or []) == set(ex["tasks"][0]["fields"])
    r = dict(id=c["id"], cat=c["category"], ok=ok, fields_ok=fo, tops=tops[:2], behavior=out["behavior"], bad=bad,
             last=c["turns"][-1]["text"], exp=sorted(acc), trace=out.get("extra", {}).get("ctx"))
    res.append(r)
    by[c["category"]].append(r)
    if a.v and not ok:
        print("FAIL", c["id"], c["category"], "|", " / ".join(t["text"] for t in c["turns"] if t["role"] == "user"),
              "| got", tops[:2], r["behavior"], "| exp", sorted(acc), "| forbid", ex["forbid_proc_ids"], "|", r["trace"])
for k in sorted(by):
    rs = by[k]
    print(f"{k:8s} {sum(x['ok'] for x in rs)}/{len(rs)}")
tot = sum(x["ok"] for x in res)
h = [x for x in res if x["cat"] == "ctx_h"]
fs = [x["fields_ok"] for x in res if x["fields_ok"] is not None]
print(f"TỔNG top-1 lượt cuối {tot}/{len(res)} = {100*tot/len(res):.1f}% | độc lập (h) {sum(x['ok'] for x in h)}/{len(h)} | fields {sum(fs)}/{len(fs)}")
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump(res, open(os.path.join(HERE, "results", f"{a.name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

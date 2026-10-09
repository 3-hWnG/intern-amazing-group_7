"""Tự kiểm harness: oracle phải đạt 100% truy hồi/fields/hành vi, 0 bịa; 'kẻ nói dối' phải bị bắt bịa."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import run

cases = [json.loads(l) for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8")]


def oracle(case, lie=False):
    e = case["expected"]
    ans = "Cổng không công bố mức này." if e["must_say_not_published"] else "Theo nguồn."
    ans += " " + " ".join(e["citation_tokens"][:1])
    for ck in e.get("checks", []):  # oracle nhắc đúng mục điều kiện / cả hai thủ tục
        ans += " " + " ".join(ck.get("keys", []) + [i["key"] for i in ck.get("items", [])])
    if lie:
        ans += " Lệ phí là 123.000 đồng, giải quyết trong 77 ngày. Miễn phí hoàn toàn."
    return {"tasks": [{"proc_id": t["acceptable_proc_ids"][0], "candidates": t["acceptable_proc_ids"], "fields": t["fields"]}
                      for t in e["tasks"] if t["acceptable_proc_ids"]],
            "behavior": e["behavior"], "answer_text": ans}


good = [run.score_case(c, oracle(c)) for c in cases]
bad = [run.score_case(c, oracle(c, lie=True)) for c in cases]
for k in ("top1", "top3", "fields_ok", "behavior_ok", "nps_ok", "cite_ok"):
    xs = [r[k] for r in good if r[k] is not None]
    assert xs and all(xs), (k, [r["id"] for r in good if r[k] is False][:5])
assert not any(r["fab"] for r in good), [(r["id"], r["fab_why"]) for r in good if r["fab"]][:5]
assert all(r["fab"] for r in bad if r["fab"] is not None) and sum(r["fab"] for r in bad) > 100
# bộ chấm luật: oracle phải đạt 100%; adapter chọn đúng mục bị cấm / thiếu mục điều kiện phải trượt
rl = [r for r in good if r["rule_ok"] is not None]
assert len(rl) >= 48 and all(r["rule_ok"] for r in rl), [r["id"] for r in rl if not r["rule_ok"]]
from collections import Counter
assert all(v >= 12 for v in Counter(r["rule_kind"] for r in rl).values()) and len(set(r["rule_kind"] for r in rl)) == 4
for c in cases:
    ck = (c["expected"].get("checks") or [None])[0]
    if not ck: continue
    o = oracle(c)
    if ck["kind"] in ("negation", "order"):
        o["tasks"] = [{"proc_id": ck["forbid_proc_ids"][0], "candidates": ck["forbid_proc_ids"], "fields": None}]
    elif ck["kind"] == "condition":
        o["answer_text"] = "Theo nguồn."
    else:
        o["answer_text"] = "Theo nguồn chỉ có thủ tục " + ck["items"][0]["key"]
    assert run.score_case(c, o)["rule_ok"] is False, c["id"]
print("selftest OK: oracle 100%, bịa=0; liar bịa =", sum(r["fab"] for r in bad), "/", len(bad))

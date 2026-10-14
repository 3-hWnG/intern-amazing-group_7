# -*- coding: utf-8 -*-
"""
run_pseudo_rank.py — MRR/nDCG@5 (A4/A5) trên bộ MÙ cases_h*.json (vd HOLDOUT "h4"),
dùng chính scorer thuần `rank_metrics.py` (đã validated bằng selftest riêng) + answer_adapter
thật, KHÔNG tạo thêm pipeline chấm mới. Bổ sung cho run_pseudo.py (chỉ có top1/top3, chưa có
MRR/nDCG liên tục).

KỶ LUẬT BỘ MÙ (05_methodology/..., PHẦN 2.2): đây là bộ HOLDOUT — chỉ chạy 1 lần để báo cáo,
KHÔNG đọc lỗi từng câu để sửa code. Script này CHỦ Ý chỉ in số tổng hợp + nhóm lỗi chung
(theo "fields"/archetype nếu có), không in câu hỏi kèm trả lời sai để soi từng ca.

Chạy (đúng quy ước repo):
    cd <ROOT của Code>
    S3_DB=<db cục bộ> S3_DATA_DB=<db cục bộ> S3_USE_LLM=0 python run_server.py eval/run_pseudo_rank.py cases_h4.json h4
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402
import rank_metrics as rm  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SRC = ARGS[0] if ARGS else "cases_h4.json"
NAME = ARGS[1] if len(ARGS) > 1 else "h4"
cases = json.load(open(os.path.join(HERE, SRC), encoding="utf-8"))

rows = []


def cands_of(out):
    return [c for t in out["tasks"] for c in t.get("candidates", [])]


def one(cid, q, exp_ids, beh, out, extra=None):
    cands = cands_of(out)
    acceptable = set(exp_ids or [])
    rr = rm.reciprocal_rank(cands, acceptable) if acceptable else None
    nd = rm.ndcg_at_k(cands, acceptable, k=5) if acceptable else None
    tops = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
    row = dict(id=cid, q=q, beh=beh, exp=exp_ids, got=out["behavior"],
               beh_ok=out["behavior"] == beh,
               top1=bool(tops) and tops[0] in acceptable,
               top3=any(c in acceptable for c in cands[:3]),
               rr=rr, ndcg5=nd)
    if extra:
        row.update(extra)
    return row


for c in cases:
    if "turns" in c:
        hist = []
        for i, t in enumerate(c["turns"]):
            hist.append({"role": "user", "text": t["q"]})
            out = answer_adapter.adapter(hist)
            hist.append({"role": "assistant", "text": out["answer_text"]})
            rows.append(one(f"{c['id']}.{i+1}", t["q"], t["expect_ids"], t["beh"], out,
                             extra={"fields": t.get("fields")}))
    else:
        out = answer_adapter.adapter([{"role": "user", "text": c["q"]}])
        rows.append(one(c["id"], c["q"], c["expect_ids"], c["beh"], out,
                         extra={"fields": c.get("fields")}))

n = len(rows)
beh_ok = sum(r["beh_ok"] for r in rows)
ans = [r for r in rows if r["beh"] == "answer"]
n_ans = len(ans)

print("=" * 78)
print(f"HOLDOUT '{NAME}' (nguồn: {SRC}) — BỘ MÙ, chỉ chạy 1 lần để báo cáo")
print("=" * 78)
print(f"n = {n} lượt")
print(f"Behavioral Accuracy (answer/apologize/clarify đúng): {beh_ok}/{n} ({100*beh_ok/n:.1f}%)")
for b in ("answer", "clarify", "apologize"):
    s = [r for r in rows if r["beh"] == b]
    if s:
        print(f"  - {b:10s} n={len(s):3d}  đúng hành vi {sum(r['beh_ok'] for r in s)}/{len(s)} "
              f"({100*sum(r['beh_ok'] for r in s)/len(s):.1f}%)")

print()
print(f"-- Chỉ tính trên {n_ans} lượt expected_behavior=answer (A1/A2/A4/A5 vô nghĩa với clarify/apologize) --")
top1 = sum(r["top1"] for r in ans)
top3 = sum(r["top3"] for r in ans)
mrr = rm.mean([r["rr"] for r in ans])
ndcg = rm.mean([r["ndcg5"] for r in ans])
print(f"Top-1 Accuracy : {top1}/{n_ans} ({100*top1/n_ans:.1f}%)")
print(f"Top-3 Accuracy : {top3}/{n_ans} ({100*top3/n_ans:.1f}%)")
print(f"MRR            : {mrr:.3f}" if mrr is not None else "MRR            : n/a")
print(f"nDCG@5         : {ndcg:.3f}" if ndcg is not None else "nDCG@5         : n/a")

# nhóm lỗi chung theo "fields" (KHÔNG in câu hỏi/câu trả lời sai — kỷ luật bộ mù PHẦN 2.2 mục 2)
print()
print("-- Nhóm lỗi chung theo 'fields' (để sửa nguyên nhân, không hard-code câu test) --")
from collections import Counter
fail_fields = Counter()
for r in ans:
    if not r["top1"]:
        for f in (r.get("fields") or ["(không rõ)"]):
            fail_fields[f] += 1
beh_fail_by_type = Counter(r["beh"] for r in rows if not r["beh_ok"])
if fail_fields:
    for f, cnt in fail_fields.most_common():
        print(f"  top1 sai, field liên quan = {f}: {cnt} ca")
else:
    print("  (không có ca top1 sai)")
if beh_fail_by_type:
    for b, cnt in beh_fail_by_type.most_common():
        print(f"  hành vi sai, loại kỳ vọng = {b}: {cnt} ca")

out_dir = os.path.join(HERE, "results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, f"rank_{NAME}.json")
json.dump({
    "name": NAME, "source": SRC, "n": n, "beh_ok": beh_ok,
    "n_answer": n_ans, "top1": top1, "top3": top3, "mrr": mrr, "ndcg5": ndcg,
    "rows": rows,
}, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nĐã ghi: {out_path}")

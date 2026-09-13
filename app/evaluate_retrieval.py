"""Chấm điểm tầng truy hồi + hiệu chỉnh ngưỡng.

    python evaluate_retrieval.py --eval ..\\..\\..\\Evaluation\\eval_questions.csv

So sánh trực tiếp với baseline v0 (R@1 0.527 / R@5 0.804 / MRR 0.640).
"""

from __future__ import annotations

import argparse
import csv
import statistics as st
import time
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from core import retrieval
from core.tiers import Tier, decide

TOP_N = 10


def load_eval(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def run(rows: list[dict]) -> tuple[list[dict], dict]:
    results = []
    latencies = []
    t_start = time.time()
    for n, r in enumerate(rows, 1):
        if n % 100 == 0:
            rate = (time.time() - t_start) / n
            print(f"  ... {n}/{len(rows)}  ({rate*1000:.0f} ms/câu, "
                  f"còn ~{rate*(len(rows)-n)/60:.1f} phút)")
        gold = {int(x) for x in filter(None, r["gold_chroma_id"].split(";"))}
        t0 = time.time()
        cands = retrieval.retrieve(r["question"], top_k=TOP_N)
        latencies.append(time.time() - t0)
        ids = [c.row_id for c in cands]
        rank = next((i + 1 for i, rid in enumerate(ids) if rid in gold), None)
        tier = decide(cands)
        top = cands[0] if cands else None
        results.append({
            **r,
            "top1_id": ids[0] if ids else "",
            "top1_title": top.record.ten[:60] if top else "",
            "confidence": round(top.confidence, 4) if top else 0.0,
            "gap": round(top.confidence - cands[1].confidence, 4) if len(cands) > 1 else 0.0,
            "best_view": top.best_view if top else "",
            "tier": tier.value,
            "gold_rank": rank or "",
            "hit@1": int(rank == 1) if rank else 0,
            "hit@5": int(rank is not None and rank <= 5),
            "rr": round(1 / rank, 4) if rank else 0.0,
        })

    ins = [r for r in results if r["in_scope"] == "1"]
    n = len(ins) or 1
    lat = sorted(latencies)
    return results, {
        "latency_median_ms": round(st.median(lat) * 1000, 1),
        "latency_p95_ms": round(lat[int(len(lat) * 0.95)] * 1000, 1),
        "n_in_scope": len(ins),
        "Recall@1": round(sum(r["hit@1"] for r in ins) / n, 4),
        "Recall@5": round(sum(r["hit@5"] for r in ins) / n, 4),
        "MRR@10": round(sum(r["rr"] for r in ins) / n, 4),
    }


def breakdown(results, key):
    b = defaultdict(list)
    for r in results:
        if r["in_scope"] == "1":
            b[r[key]].append(r)
    return {k: {"n": len(v),
                "R@1": round(sum(x["hit@1"] for x in v) / len(v), 3),
                "R@5": round(sum(x["hit@5"] for x in v) / len(v), 3)}
            for k, v in sorted(b.items())}


def calibrate(results):
    """Độ tin cậy giờ là thang 0..1, CÀNG LỚN CÀNG TỐT (ngược với L2 ở v0)."""
    hit = [r["confidence"] for r in results if r["in_scope"] == "1" and r["hit@1"] == 1]
    miss = [r["confidence"] for r in results if r["in_scope"] == "1" and r["hit@1"] == 0]
    oos = [r["confidence"] for r in results if r["in_scope"] == "0"]

    def describe(name, xs):
        if not xs:
            print(f"  {name:24s} (trống)"); return
        xs = sorted(xs)
        print(f"  {name:24s} n={len(xs):4d}  p10={xs[len(xs)//10]:.3f}  "
              f"p25={xs[len(xs)//4]:.3f}  median={st.median(xs):.3f}  "
              f"p75={xs[3*len(xs)//4]:.3f}")

    print("\n--- Độ tin cậy (0..1, càng LỚN càng giống) ---")
    describe("Trúng (in-scope)", hit)
    describe("Trượt (in-scope)", miss)
    describe("Ngoài phạm vi", oos)

    print("\n--- Quét ngưỡng TIER_B_MIN_CONFIDENCE (chặn câu ngoài phạm vi) ---")
    print("  ngưỡng   chặn OOS %   mất câu đúng %")
    for t in [x / 100 for x in range(20, 85, 5)]:
        if not oos or not hit:
            break
        blocked = sum(1 for c in oos if c < t) / len(oos) * 100
        lost = sum(1 for c in hit if c < t) / len(hit) * 100
        print(f"   {t:.2f}     {blocked:6.1f}       {lost:6.1f}")

    print("\n--- Phân tầng thực tế ---")
    for scope, label in [("1", "trong phạm vi"), ("0", "ngoài phạm vi")]:
        sub = [r for r in results if r["in_scope"] == scope]
        if not sub:
            continue
        counts = defaultdict(int)
        for r in sub:
            counts[r["tier"]] += 1
        dist = "  ".join(f"{k}={v} ({v/len(sub)*100:.0f}%)" for k, v in sorted(counts.items()))
        print(f"  {label:16s} {dist}")
    a_wrong = [r for r in results if r["tier"] == Tier.A_DATABASE.value
               and r["in_scope"] == "1" and r["hit@1"] == 0]
    a_total = [r for r in results if r["tier"] == Tier.A_DATABASE.value]
    if a_total:
        print(f"\n  Tầng A sai (tự tin nhưng lấy nhầm dòng): "
              f"{len(a_wrong)}/{len(a_total)} = {len(a_wrong)/len(a_total)*100:.1f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default="../../../Evaluation/eval_questions.csv")
    ap.add_argument("--out", default="../../../Evaluation/eval_results.csv")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    print(f"Cấu hình: embed={config.EMBED_MODEL_NAME} | space={config.CHROMA_SPACE} | "
          f"dense={config.USE_DENSE} | bm25={config.USE_LEXICAL} | "
          f"rerank={config.USE_RERANKER} | multiview={config.USE_MULTI_VIEW}")

    rows = load_eval(Path(args.eval))
    if args.limit:
        rows = rows[:args.limit]
    print(f"Đang chấm {len(rows)} câu hỏi...\n")

    results, summary = run(rows)

    print("\n=== TỔNG THỂ ===")
    base = {"Recall@1": 0.5272, "Recall@5": 0.8037, "MRR@10": 0.64}
    for k, v in summary.items():
        if k in base:
            d = v - base[k]
            print(f"  {k:12s} {v:.4f}   (v0 {base[k]:.4f}, {d:+.4f})")
        else:
            print(f"  {k:12s} {v}")

    for key, label in [("variant", "THEO KIỂU CÂU HỎI"),
                       ("difficulty", "THEO ĐỘ KHÓ"),
                       ("linh_vuc", "THEO LĨNH VỰC")]:
        print(f"\n=== {label} ===")
        for k, v in breakdown(results, key).items():
            print(f"  {str(k)[:45]:45s} n={v['n']:4d}  R@1={v['R@1']:.3f}  R@5={v['R@5']:.3f}")

    calibrate(results)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nChi tiết -> {out}")


if __name__ == "__main__":
    main()

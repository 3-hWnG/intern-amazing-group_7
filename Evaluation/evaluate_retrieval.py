#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_retrieval.py — Nhóm 7 / LLM Pháp lý
=============================================
Chấm điểm tầng truy hồi (retrieval) bằng bộ eval_questions.csv.
Đây là CON SỐ ĐẦU TIÊN của dự án. Chạy nó TRƯỚC khi đổi bất cứ thứ gì,
để mọi thay đổi sau đó đều so được với mốc này.

Chạy từ thư mục app/:
    python evaluate_retrieval.py --eval ../eval/eval_questions.csv

In ra:
  - Recall@1 / Recall@5 / MRR@10        (tổng thể + tách theo variant, độ khó, lĩnh vực)
  - phân bố điểm similarity của câu ĐÚNG vs câu SAI
    -> đây chính là dữ liệu để chọn ngưỡng HIGH / LOW cho router
  - ghi eval_results.csv để soi từng câu hỏi sai

Không sửa gì trong hệ thống. Chỉ đọc.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import embeddings, vectorstore  # noqa: E402

TOP_N = 10


def load_eval(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def retrieve(question: str, n: int = TOP_N):
    """Trả về [(chroma_id, distance)] theo thứ tự xếp hạng."""
    q_emb = embeddings.encode(question)
    res = vectorstore.get_collection().query(
        query_embeddings=[q_emb.tolist()], n_results=n
    )
    ids = res["ids"][0]
    dists = res.get("distances", [[None] * len(ids)])[0]
    return list(zip(ids, dists))


def score(rows: list[dict]) -> tuple[list[dict], dict]:
    results = []
    for r in rows:
        gold = set(filter(None, r["gold_chroma_id"].split(";")))
        ranked = retrieve(r["question"])
        ids = [i for i, _ in ranked]
        top_dist = ranked[0][1] if ranked else None

        rank = next((k + 1 for k, i in enumerate(ids) if i in gold), None)
        results.append({
            **r,
            "top1_id": ids[0] if ids else "",
            "top1_distance": top_dist,
            "gold_rank": rank or "",
            "hit@1": int(rank == 1) if rank else 0,
            "hit@5": int(rank is not None and rank <= 5),
            "rr": round(1 / rank, 4) if rank else 0.0,
        })

    in_scope = [r for r in results if r["in_scope"] == "1"]
    n = len(in_scope) or 1
    summary = {
        "n_in_scope": len(in_scope),
        "Recall@1": round(sum(r["hit@1"] for r in in_scope) / n, 4),
        "Recall@5": round(sum(r["hit@5"] for r in in_scope) / n, 4),
        "MRR@10": round(sum(r["rr"] for r in in_scope) / n, 4),
    }
    return results, summary


def breakdown(results: list[dict], key: str) -> dict:
    buckets = defaultdict(list)
    for r in results:
        if r["in_scope"] == "1":
            buckets[r[key]].append(r)
    return {
        k: {
            "n": len(v),
            "R@1": round(sum(x["hit@1"] for x in v) / len(v), 3),
            "R@5": round(sum(x["hit@5"] for x in v) / len(v), 3),
        }
        for k, v in sorted(buckets.items())
    }


def threshold_report(results: list[dict]) -> None:
    """Dữ liệu để chọn HIGH / LOW.

    Nếu hai phân bố dưới đây CHỒNG LÊN NHAU thì không ngưỡng nào cứu được
    router — phải đổi mô hình nhúng trước, không phải chỉnh số.
    """
    hit = [r["top1_distance"] for r in results
           if r["in_scope"] == "1" and r["hit@1"] == 1 and r["top1_distance"] is not None]
    miss = [r["top1_distance"] for r in results
            if r["in_scope"] == "1" and r["hit@1"] == 0 and r["top1_distance"] is not None]
    oos = [r["top1_distance"] for r in results
           if r["in_scope"] == "0" and r["top1_distance"] is not None]

    def describe(name, xs):
        if not xs:
            print(f"  {name:22s} (không có dữ liệu)")
            return
        xs = sorted(xs)
        print(f"  {name:22s} n={len(xs):4d}  min={xs[0]:.3f}  "
              f"p25={xs[len(xs)//4]:.3f}  median={statistics.median(xs):.3f}  "
              f"p75={xs[3*len(xs)//4]:.3f}  max={xs[-1]:.3f}")

    print("\n--- Khoảng cách top-1 (càng NHỎ càng giống) ---")
    describe("Trúng (in-scope)", hit)
    describe("Trượt (in-scope)", miss)
    describe("Ngoài phạm vi", oos)
    if hit and oos:
        print(f"\n  Gợi ý: LOW nên nằm giữa median(trúng)={statistics.median(hit):.3f} "
              f"và median(ngoài phạm vi)={statistics.median(oos):.3f}.")
        if statistics.median(hit) >= statistics.median(oos):
            print("  ! Hai phân bố đảo ngược/chồng nhau -> KHÔNG ngưỡng nào cứu được.")
            print("    Phải đổi mô hình nhúng trước khi chỉnh router.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default="../eval/eval_questions.csv")
    ap.add_argument("--out", default="../eval/eval_results.csv")
    ap.add_argument("--limit", type=int, default=0, help="chỉ chạy N câu đầu (để thử nhanh)")
    args = ap.parse_args()

    rows = load_eval(Path(args.eval))
    if args.limit:
        rows = rows[: args.limit]
    print(f"Đang chấm {len(rows)} câu hỏi...\n")

    results, summary = score(rows)

    print("=== TỔNG THỂ ===")
    for k, v in summary.items():
        print(f"  {k:12s} {v}")

    for key, label in [("variant", "THEO KIỂU CÂU HỎI"),
                       ("difficulty", "THEO ĐỘ KHÓ"),
                       ("linh_vuc", "THEO LĨNH VỰC")]:
        print(f"\n=== {label} ===")
        for k, v in breakdown(results, key).items():
            print(f"  {str(k)[:45]:45s} n={v['n']:4d}  R@1={v['R@1']:.3f}  R@5={v['R@5']:.3f}")

    threshold_report(results)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nChi tiết từng câu -> {out}")
    print("Lọc cột hit@1 = 0 để xem hệ thống sai ở đâu.")


if __name__ == "__main__":
    main()

"""Chỉ số cho đợt sửa câu khó (24/10/2026), ĐÃ GHI TRƯỚC trong eval/real_v2/README.md:
hành vi đúng (3 lớp), recall từng lớp, độ chính xác cân bằng (trung bình recall answer + apologize; kèm trung bình 3 lớp),
top-1 / top-3 trên câu answer, "trả lời đúng trọn" (trả lời VÀ thủ tục đầu đúng), khoảng tin cậy Wilson 95%.
Đầu vào: các dòng kết quả của eval/run_pseudo.py hoặc eval/hard/dev.py (id, beh, got, top1, top3, ...).
"""
from __future__ import annotations

import math
from collections import Counter

# 11 câu real_v2 gần trùng câu real_v1 (Jaccard tập chữ >= 0,6) — báo cáo thêm bộ "sạch" không có chúng (eval/real_v2/README.md)
REAL_V2_NEAR_DUP = {f"real_v2-{n:03d}" for n in (13, 133, 152, 154, 164, 188, 212, 263, 268, 288, 297)}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def frac(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "p": round(k / n, 4) if n else None, "ci": [round(lo, 4), round(hi, 4)]}


def summarize(rows: list[dict]) -> dict:
    by = {b: [r for r in rows if r["beh"] == b] for b in ("answer", "clarify", "apologize")}
    rec = {b: frac(sum(r["got"] == b for r in rs), len(rs)) for b, rs in by.items()}
    ans = by["answer"]
    bal2 = [rec[b]["p"] for b in ("answer", "apologize") if rec[b]["n"]]
    bal3 = [rec[b]["p"] for b in ("answer", "clarify", "apologize") if rec[b]["n"]]
    return {
        "n": len(rows),
        "behavior": frac(sum(r["got"] == r["beh"] for r in rows), len(rows)),
        "recall": rec,
        "balanced2": round(sum(bal2) / len(bal2), 4) if bal2 else None,
        "balanced3": round(sum(bal3) / len(bal3), 4) if bal3 else None,
        "top1": frac(sum(bool(r["top1"]) for r in ans), len(ans)),
        "top3": frac(sum(bool(r["top3"]) for r in ans), len(ans)),
        "end2end": frac(sum(r["got"] == "answer" and bool(r["top1"]) for r in ans), len(ans)),
        "mrr": round(sum(r["rr"] for r in ans) / len(ans), 4) if ans and all("rr" in r for r in ans) else None,
        "confusion": dict(Counter(f"{r['beh']}->{r['got']}" for r in rows)),
    }


def baselines(rows: list[dict]) -> dict:
    """Hai mốc ngây thơ: luôn từ chối; luôn trả lời (giữ thủ tục xếp đầu của hệ thống)."""
    always_apo = [{**r, "got": "apologize", "top1": False, "top3": False, **({"rr": 0.0} if "rr" in r else {})} for r in rows]
    always_ans = [{**r, "got": "answer"} for r in rows]
    return {"always_apologize": summarize(always_apo), "always_answer": summarize(always_ans)}


def line(name: str, s: dict) -> str:
    r = s["recall"]
    pc = lambda d: f"{d['k']}/{d['n']}={d['p']:.1%}" if d["n"] else "-"
    return (f"{name:<22} hv {pc(s['behavior'])}  bal {s['balanced2']:.3f}  ans {pc(r['answer'])}  cla {pc(r['clarify'])}  "
            f"apo {pc(r['apologize'])}  top1 {pc(s['top1'])}  top3 {pc(s['top3'])}  trọn {pc(s['end2end'])}")

"""Kết luận của bộ test có đứng vững khi đổi người gán nhãn không? Chấm lại các lượt chạy real_v2 đã có (eval/hard/results/test,
không chạy lại hệ thống) trên 100 câu gán lại, lần lượt với nhãn A (gốc) và nhãn B (lượt gán lại), bỏ câu B gán skip.

Chỉ đọc kết quả có sẵn; nhãn A không đổi. Top-1 theo nhãn B = thủ tục đầu của hệ thống nằm trong expect_ids của B.

    python eval/real_v2/relabel/robustness.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "eval", "hard"))
from metrics import summarize  # noqa: E402

RES = os.path.join(ROOT, "eval", "hard", "results", "test")
CONFIGS = ["off", "A", "B", "C", "AC", "ACname", "final"]


def mcnemar(a: list[bool], b: list[bool]) -> tuple[int, int, float]:
    import math
    up = sum(1 for x, y in zip(a, b) if not x and y)
    down = sum(1 for x, y in zip(a, b) if x and not y)
    n = up + down
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(up, down) + 1)) / 2 ** n) if n else 1.0
    return up, down, p


def relabel(rows: list[dict], lab: dict) -> list[dict]:
    out = []
    for r in rows:
        x = lab[r["id"]]
        exp = x["expect_ids"]
        out.append({**r, "beh": x["beh"], "exp": exp, "top1": bool(r["tops"]) and r["tops"][0] in exp})
    return out


def main():
    ids = json.load(open(os.path.join(HERE, "relabel_ids.json"), encoding="utf-8"))["ids"]
    B = {x["id"]: x for x in json.load(open(os.path.join(HERE, "real_v2_labels_B.json"), encoding="utf-8"))}
    A = {x["id"]: x for x in json.load(open(os.path.join(ROOT, "eval", "real_v2", "real_v2_labels.json"), encoding="utf-8"))}
    keep = [i for i in ids if B[i]["beh"] != "skip"]
    runs = {c: {r["id"]: r for r in json.load(open(os.path.join(RES, f"real_v2_{c}.json"), encoding="utf-8"))["rows"]} for c in CONFIGS}
    print(f"{len(keep)} câu (bỏ {len(ids) - len(keep)} câu B gán skip). Lớp theo A: "
          f"{ {b: sum(A[i]['beh'] == b for i in keep) for b in ('answer', 'clarify', 'apologize')} }, theo B: "
          f"{ {b: sum(B[i]['beh'] == b for i in keep) for b in ('answer', 'clarify', 'apologize')} }")
    print("\n| Cấu hình | Cân bằng (nhãn A) | Cân bằng (nhãn B) | Đúng trọn (nhãn A) | Đúng trọn (nhãn B) |")
    print("|---|---|---|---|---|")
    per = {}
    for c in CONFIGS:
        rows = [runs[c][i] for i in keep]
        sa, sb = summarize(relabel(rows, A)), summarize(relabel(rows, B))
        per[c] = (relabel(rows, A), relabel(rows, B))
        e = lambda s: f"{s['end2end']['k']}/{s['end2end']['n']}"
        print(f"| {c} | {sa['balanced2']:.3f} | {sb['balanced2']:.3f} | {e(sa)} | {e(sb)} |")
    for lab, k in (("A", 0), ("B", 1)):
        for x, y in (("off", "A"), ("A", "final"), ("A", "ACname")):
            beh = mcnemar([r["got"] == r["beh"] for r in per[x][k]], [r["got"] == r["beh"] for r in per[y][k]])
            print(f"nhãn {lab}: {x} -> {y}: hành vi +{beh[0]}/-{beh[1]} (p = {beh[2]:.3g})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

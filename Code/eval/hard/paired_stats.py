"""Thống kê cặp cho bài báo (27/10): McNemar chính xác hai phía (hành vi, đúng trọn) và khoảng bootstrap 95% của hiệu độ chính xác cân bằng.

Chỉ đọc các tệp kết quả đã có trong results/test (real_v2) và results/test_v4 (real_v4), không chạy hệ thống. Bootstrap theo câu, ghép cặp
(cùng một mẫu lại cho hai cấu hình), 4000 lần, SEED 20261027.

    python eval/hard/paired_stats.py
"""
import json
import os
import random
import sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
SEED, B = 20261027, 4000
PAIRS = {
    "test/real_v2": [("off", "A"), ("A", "final"), ("A", "C"), ("A", "AC"), ("A", "ACname"), ("A", "rag4b"),
                     ("abl_gate_only", "learned_gate"), ("abl_gate_only", "learned_gate_emb")],
    "test_v4/real_v4": [("off", "A"), ("A", "R2final"), ("AB", "R2final"), ("off", "R2final"), ("R2final", "rag4b"), ("A", "rag4b"),
                        ("abl_gate_only", "learned_gate"), ("abl_gate_only", "learned_gate_emb")],
}


def rows(prefix, name):
    return {r["id"]: r for r in json.load(open(os.path.join(HERE, "results", f"{prefix}_{name}.json"), encoding="utf-8"))["rows"]}


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def bal(R, w):
    """w: số lần mỗi câu xuất hiện trong mẫu."""
    na = sum(k for i, k in w.items() if R[i]["beh"] == "answer"); nr = sum(k for i, k in w.items() if R[i]["beh"] == "apologize")
    if not na or not nr:
        return None
    return (sum(k for i, k in w.items() if R[i]["beh"] == "answer" and R[i]["got"] == "answer") / na
            + sum(k for i, k in w.items() if R[i]["beh"] == "apologize" and R[i]["got"] == "apologize") / nr) / 2


def e2e(r):
    return r["got"] == "answer" and r["beh"] == "answer" and r["top1"]


def compare(X, Y):
    ids = sorted(X)
    bx = {i: X[i]["got"] == X[i]["beh"] for i in ids}; by = {i: Y[i]["got"] == Y[i]["beh"] for i in ids}
    gain = sum(by[i] and not bx[i] for i in ids); loss = sum(bx[i] and not by[i] for i in ids)
    eg = sum(e2e(Y[i]) and not e2e(X[i]) for i in ids); el = sum(e2e(X[i]) and not e2e(Y[i]) for i in ids)
    one = {i: 1 for i in ids}
    rnd = random.Random(SEED); ds = []
    for _ in range(B):
        w = {}
        for _ in ids:
            i = rnd.choice(ids); w[i] = w.get(i, 0) + 1
        u, v = bal(X, w), bal(Y, w)
        if u is not None and v is not None:
            ds.append(v - u)
    ds.sort()
    return {"bal": (round(bal(X, one), 4), round(bal(Y, one), 4)), "diff": round(bal(Y, one) - bal(X, one), 6),
            "ci95": (round(ds[int(0.025 * len(ds))], 3), round(ds[int(0.975 * len(ds)) - 1], 3)),
            "behavior": f"+{gain}/-{loss}", "p_behavior": mcnemar(gain, loss),
            "e2e": (sum(e2e(X[i]) for i in ids), sum(e2e(Y[i]) for i in ids)), "e2e_change": f"+{eg}/-{el}", "p_e2e": mcnemar(eg, el)}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    out = {}
    for prefix, pairs in PAIRS.items():
        for x, y in pairs:
            r = compare(rows(prefix, x), rows(prefix, y))
            out[f"{prefix.split('/')[1]} {x} -> {y}"] = r
            print(f"{prefix.split('/')[1]:8s} {x:>14s} -> {y:<16s} bal {r['bal'][0]:.3f}->{r['bal'][1]:.3f} d={r['diff']:+.3f} "
                  f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]  beh {r['behavior']} p={r['p_behavior']:.2g}  "
                  f"e2e {r['e2e'][0]}->{r['e2e'][1]} {r['e2e_change']} p={r['p_e2e']:.2g}")
    json.dump(out, open(os.path.join(HERE, "results", "paired_stats.json"), "w", encoding="utf-8"), indent=1)

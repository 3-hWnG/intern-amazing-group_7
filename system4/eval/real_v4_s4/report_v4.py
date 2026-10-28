"""Bảng kết quả bộ mù real_v4_s4 (System 4) — J3: tỷ lệ đạt (Wilson 95%) chung, theo loại câu, theo lĩnh vực,
TÁCH PHẦN A (khuôn)/PHẦN B (người viết); thời gian trung vị; so cặp (McNemar chính xác) giữa hai cấu hình.

    python system4/eval/real_v4_s4/report_v4.py v4_fp v4_new --pair v4_fp v4_new
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "results" / "bench"            # nơi bench.py ghi (bị .gitignore); bản đã commit: real_v4_s4/results/
KINDS_A = {"L": "tra cứu", "U": "không dấu", "C": "đếm", "S": "liệt kê", "M": "lớn/nhỏ nhất",
           "A": "tổng", "R": "không có trong bảng", "F": "hỏi tiếp", "X": "chéo sheet"}
KINDS_B = {"L": "tra cứu", "F": "hỏi tiếp", "U": "không dấu", "R": "không có trong bảng", "AMB": "mơ hồ"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return (0.0, 0.0)
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def pct(k: int, n: int, ci: bool = True) -> str:
    if not n:
        return "–"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.0%}" + (f" ({lo:.0%}–{hi:.0%})" if ci else "")


def load(name: str) -> list[dict]:
    p = RES / f"inst02+{name}.json"
    d = json.loads((p if p.exists() else HERE / "results" / p.name).read_text(encoding="utf-8"))
    return [r for r in d["runs"] if r.get("suite") == "real4"]


def route(r: dict) -> str:
    fp = r.get("fast_path")
    if isinstance(fp, dict):
        return str(fp.get("route") or "fast")
    return str(fp) if fp else ""


def part(r: dict) -> str:
    """Phần A (khuôn, id 'v4-...') hay Phần B (người viết, id 'v4_b-...')."""
    return "B" if str(r["id"]).startswith("v4_b-") else "A"


def domain(r: dict) -> str:
    parts = str(r["id"]).split("-")
    return parts[1] if len(parts) > 2 else "?"


def mcnemar(a: list[dict], b: list[dict]) -> tuple[int, int, float]:
    pa, pb = {r["id"]: bool(r["pass"]) for r in a}, {r["id"]: bool(r["pass"]) for r in b}
    up = sum(1 for i in pa if not pa[i] and pb.get(i)); down = sum(1 for i in pa if pa[i] and not pb.get(i))
    n = up + down
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(up, down) + 1)) / 2 ** n) if n else 1.0
    return up, down, p


def section(label: str, runs: dict, rs_filter) -> None:
    print(f"\n### {label}\n")
    kind_map = KINDS_A if label.startswith("Phần A") else (KINDS_B if label.startswith("Phần B") else {**KINDS_A, **KINDS_B})
    print("| Cấu hình | Đạt (Wilson 95%) | " + " | ".join(f"{k} {v}" for k, v in kind_map.items()) + " | trung vị s | đường nhanh | SQL |")
    print("|---|---|" + "---|" * len(kind_map) + "---|---|---|")
    for n, rs_all in runs.items():
        rs = [r for r in rs_all if rs_filter(r)]
        kinds = [pct(sum(r["pass"] for r in rs if r.get("kind") == k), sum(1 for r in rs if r.get("kind") == k), ci=False) for k in kind_map]
        med = statistics.median([r["total_s"] for r in rs if r.get("total_s") is not None]) if rs else None
        med_s = f"{med:.1f}" if med is not None else "–"
        print(f"| {n} | {pct(sum(r['pass'] for r in rs), len(rs))} | " + " | ".join(kinds)
              + f" | {med_s} | {sum(1 for r in rs if route(r))} | {sum(1 for r in rs if route(r) == 'sql')} |")


def main(argv: list[str]) -> None:
    pair = None
    if "--pair" in argv:
        i = argv.index("--pair")
        pair, argv = argv[i + 1:i + 3], argv[:i] + argv[i + 3:]
    runs = {n: load(n) for n in argv}
    doms = sorted({domain(r) for rs in runs.values() for r in rs})

    section("Tổng (Phần A + Phần B)", runs, lambda r: True)
    section("Phần A — khuôn (128 câu)", runs, lambda r: part(r) == "A")
    section("Phần B — người viết (88 câu)", runs, lambda r: part(r) == "B")

    print("\n### Theo lĩnh vực (cả A + B)\n")
    print("| Cấu hình | " + " | ".join(doms) + " |")
    print("|---|" + "---|" * len(doms))
    for n, rs in runs.items():
        print(f"| {n} | " + " | ".join(pct(sum(r["pass"] for r in rs if domain(r) == d), sum(1 for r in rs if domain(r) == d), ci=False) for d in doms) + " |")

    if pair:
        up, down, p = mcnemar(runs[pair[0]], runs[pair[1]])
        print(f"\nMcNemar {pair[0]} -> {pair[1]} (tổng A+B): +{up} / -{down}, p = {p:.3g}")
        for lbl, flt in [("Phần A", lambda r: part(r) == "A"), ("Phần B", lambda r: part(r) == "B")]:
            a_f = [r for r in runs[pair[0]] if flt(r)]
            b_f = [r for r in runs[pair[1]] if flt(r)]
            up, down, p = mcnemar(a_f, b_f)
            print(f"McNemar {pair[0]} -> {pair[1]} ({lbl}): +{up} / -{down}, p = {p:.3g}")


if __name__ == "__main__":
    main(sys.argv[1:])

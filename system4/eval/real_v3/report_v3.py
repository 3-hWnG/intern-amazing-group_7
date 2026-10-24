"""Bảng kết quả bộ mù real_v3 (System 4) theo kế hoạch đo trong README: tỷ lệ đạt (Wilson 95%) chung, theo loại câu, theo lĩnh vực;
thời gian trung vị; số câu đường nhanh / lộ trình SQL trả lời; so cặp (McNemar chính xác) giữa hai cấu hình.

    python system4/eval/real_v3/report_v3.py v3b_rag v3b_old v3b_fp v3b_fpagg v3a_new v3a_sqlraw [--pair v3b_fp v3a_new]
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "results" / "bench"            # nơi bench.py ghi (bị .gitignore); bản đã commit: real_v3/results/
KINDS = {"L": "tra cứu", "U": "không dấu", "C": "đếm", "S": "liệt kê", "M": "lớn/nhỏ nhất", "A": "tổng", "R": "không có trong bảng", "F": "hỏi tiếp"}


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
    return [r for r in d["runs"] if r.get("suite") == "real3"]


def route(r: dict) -> str:
    fp = r.get("fast_path")          # tên lộ trình đường nhanh đã trả lời ("field", "sql", "aggregate", ...), rỗng = đường cũ
    if isinstance(fp, dict):
        return str(fp.get("route") or "fast")
    return str(fp) if fp else ""


def domain(r: dict) -> str:
    parts = str(r["id"]).split("-")
    return parts[1] if len(parts) > 2 else "?"


def mcnemar(a: list[dict], b: list[dict]) -> tuple[int, int, float]:
    pa, pb = {r["id"]: bool(r["pass"]) for r in a}, {r["id"]: bool(r["pass"]) for r in b}
    up = sum(1 for i in pa if not pa[i] and pb.get(i)); down = sum(1 for i in pa if pa[i] and not pb.get(i))
    n = up + down
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(up, down) + 1)) / 2 ** n) if n else 1.0
    return up, down, p


def main(argv: list[str]) -> None:
    pair = None
    if "--pair" in argv:
        i = argv.index("--pair")
        pair, argv = argv[i + 1:i + 3], argv[:i] + argv[i + 3:]
    runs = {n: load(n) for n in argv}
    doms = sorted({domain(r) for rs in runs.values() for r in rs})
    print("| Cấu hình | Đạt (Wilson 95%) | " + " | ".join(f"{k} {v}" for k, v in KINDS.items()) + " | trung vị s | đường nhanh | SQL |")
    print("|---|---|" + "---|" * len(KINDS) + "---|---|---|")
    for n, rs in runs.items():
        kinds = [pct(sum(r["pass"] for r in rs if r.get("kind") == k), sum(1 for r in rs if r.get("kind") == k), ci=False) for k in KINDS]
        med = statistics.median([r["total_s"] for r in rs if r.get("total_s") is not None]) if rs else None
        print(f"| {n} | {pct(sum(r['pass'] for r in rs), len(rs))} | " + " | ".join(kinds)
              + f" | {med:.1f} | {sum(1 for r in rs if route(r))} | {sum(1 for r in rs if route(r) == 'sql')} |")
    print("\n| Cấu hình | " + " | ".join(doms) + " |")
    print("|---|" + "---|" * len(doms))
    for n, rs in runs.items():
        print(f"| {n} | " + " | ".join(pct(sum(r["pass"] for r in rs if domain(r) == d), sum(1 for r in rs if domain(r) == d), ci=False) for d in doms) + " |")
    if pair:
        up, down, p = mcnemar(runs[pair[0]], runs[pair[1]])
        print(f"\nMcNemar {pair[0]} -> {pair[1]}: +{up} / -{down}, p = {p:.3g}")


if __name__ == "__main__":
    main(sys.argv[1:])

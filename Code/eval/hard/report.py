"""Bảng kết quả cho đợt sửa câu khó: đọc các tệp eval/results/<tên>.json (dev.py, hoặc run_pseudo.py qua --raw) và in bảng Markdown
theo các chỉ số đã ghi trước (eval/real_v2/README.md): cả bộ, bộ "sạch" (bỏ 11 câu gần trùng real_v1) và hai tầng random / chude.

    python eval/hard/report.py real_v2 real_v2_base real_v2_A real_v2_B real_v2_C real_v2_final
    python eval/hard/report.py real_v1 dev_base dev_A ...
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from metrics import REAL_V2_NEAR_DUP, baselines, summarize  # noqa: E402

CASES = {"real_v1": "real_v1/cases_real_v1_labeled.json", "real_v2": "real_v2/cases_real_v2_labeled.json"}


def load(name: str, cases: dict) -> list[dict]:
    d = json.load(open(os.path.join(EVAL, "results", name + ".json"), encoding="utf-8"))
    rows = d["rows"] if isinstance(d, dict) else d
    out = []
    for r in rows:
        c = cases[r["id"]]
        out.append({**r, "beh": c["beh"], "got": r.get("got"), "stratum": c.get("stratum")})
    return out


def pct(x: dict) -> str:
    return f"{x['k']}/{x['n']} = {x['p']:.1%} ({x['ci'][0]:.1%}–{x['ci'][1]:.1%})" if x["n"] else "–"


def table(title: str, named: list[tuple[str, dict]]) -> str:
    head = ("| Cấu hình | Hành vi đúng | Cân bằng (ans+apo) | Cân bằng 3 lớp | Trả lời (recall) | Hỏi lại (recall) | Từ chối (recall) | Top-1 | Top-3 | MRR@5 | Trả lời đúng trọn |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n")
    lines = []
    for n, s in named:
        r = s["recall"]
        lines.append(f"| {n} | {pct(s['behavior'])} | {s['balanced2']:.3f} | {s['balanced3']:.3f} | {pct(r['answer'])} | {pct(r['clarify'])} | "
                     f"{pct(r['apologize'])} | {pct(s['top1'])} | {pct(s['top3'])} | {'–' if s.get('mrr') is None else format(s['mrr'], '.3f')} | {pct(s['end2end'])} |")
    return f"**{title}**\n\n" + head + "\n".join(lines) + "\n"


def main(argv: list[str]) -> None:
    which, names = argv[0], argv[1:]
    cases = {c["id"]: c for c in json.load(open(os.path.join(EVAL, CASES[which]), encoding="utf-8"))}
    runs = [(n, load(n, cases)) for n in names]
    parts = []
    first = runs[0][1]
    b = baselines(first)
    for title, filt in [("Cả bộ", lambda r: True),
                        ("Bộ sạch (bỏ 11 câu gần trùng real_v1)" if which == "real_v2" else None, lambda r: r["id"] not in REAL_V2_NEAR_DUP),
                        ("Tầng random", lambda r: r["stratum"] == "random"), ("Tầng chude", lambda r: r["stratum"] == "chude")]:
        if title is None:
            continue
        named = [(n, summarize([r for r in rows if filt(r)])) for n, rows in runs]
        if title == "Cả bộ":
            named += [("mốc: luôn từ chối", b["always_apologize"]), ("mốc: luôn trả lời", b["always_answer"])]
        parts.append(table(title, named))
    print("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1:])

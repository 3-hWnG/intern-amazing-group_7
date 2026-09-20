"""Chấm điểm pipeline trên bộ câu hỏi TỰ SOẠN (Evaluation/eval_set.jsonl).

Chỉ số:
    intent accuracy          ý định đúng / tổng
    clarification accuracy   hỏi lại đúng lúc (chỉ tính câu có expect_clarify true/false)
    official source rate     câu trả lời có ít nhất 1 nguồn chính thống
    citation rate            câu trả lời có trích dẫn [S#]
    verifier pass rate       PASS / số câu trả lời
    latency                  p50 / p95 thời gian cả lượt
Độ đúng nội dung và tỉ lệ bịa cần người chấm: đọc cột answer + sources trong CSV.

    .venv\\Scripts\\python.exe Evaluation\\evaluate.py                 # cả pipeline (cần mạng)
    .venv\\Scripts\\python.exe Evaluation\\evaluate.py --only-intent   # chỉ bước hiểu ý định (nhanh)
    .venv\\Scripts\\python.exe Evaluation\\evaluate.py --limit 10

So sánh mô hình gốc và mô hình fine-tune: chạy hai lần với LLM_MODEL khác nhau.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Backend/ cho cac goi (config o GOC du an).
sys.path.insert(0, str(HERE.parent / "Backend"))
sys.path.insert(0, str(HERE.parent))

from config import LLM_MODEL, SEARCH_PROVIDER  # noqa: E402
from core import intent as intent_step  # noqa: E402
from core import mcp_client, orchestrator  # noqa: E402


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} = {num / den:.1%}" if den else "—"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(HERE / "eval_set.jsonl"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-intent", action="store_true")
    args = parser.parse_args()

    items = [json.loads(line) for line in Path(args.data).read_text(encoding="utf-8").splitlines()
             if line.strip()]
    if args.limit:
        items = items[:args.limit]

    rows = []
    for i, item in enumerate(items, 1):
        history = item.get("history") or []
        started = time.time()
        if args.only_intent:
            u = intent_step.analyze(item["question"], history, "", {})
            got_intent = u.intent
            clarified = u.route == "clarify"
            kind = f"{u.route}({u.gate})"
            text, verdict, sources = u.clarifying_question if clarified else u.standalone_question, "", []
            queries = u.search_queries
        else:
            r = orchestrator.run_turn(orchestrator.TurnInput(question=item["question"],
                                                             history=history))
            got_intent, kind, text, verdict = r.intent.get("intent", ""), r.kind, r.text, r.verdict
            clarified = r.kind == "clarify"
            sources = r.sources
            queries = (r.evidence or {}).get("queries", [])
        seconds = time.time() - started

        expected = item["expected_intent"]
        expected = expected if isinstance(expected, list) else [expected]
        row = {
            "id": item["id"], "question": item["question"],
            "expected_intent": "|".join(expected), "intent": got_intent,
            "intent_ok": got_intent in expected,
            "expect_clarify": item.get("expect_clarify"), "clarified": clarified,
            "kind": kind, "verdict": verdict, "seconds": round(seconds, 2),
            "official_source": any(s.get("trust") == "official" for s in sources),
            "cited": bool(re.search(r"\[S\d+", text or "")),
            "queries": " | ".join(queries or []),
            "sources": " | ".join(s.get("url") or s.get("title", "") for s in sources),
            "answer": text,
        }
        rows.append(row)
        print(f"[{i}/{len(items)}] {row['id']:<12} intent={got_intent:<22}"
              f"{'✓' if row['intent_ok'] else '✗'}  kind={kind:<12} {verdict:<4} {seconds:5.1f}s")

    scored_clar = [r for r in rows if r["expect_clarify"] is not None]
    answers = [r for r in rows if r["kind"] == "answer"]
    latencies = sorted(r["seconds"] for r in rows)
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0

    summary = [
        f"# Kết quả đánh giá — {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"- Mô hình: `{LLM_MODEL}` · tìm kiếm: `{SEARCH_PROVIDER}` · "
        f"chế độ: {'chỉ hiểu ý định' if args.only_intent else 'cả pipeline'} · {len(rows)} câu",
        f"- Intent accuracy: {_pct(sum(r['intent_ok'] for r in rows), len(rows))}",
        f"- Clarification accuracy: "
        f"{_pct(sum(r['clarified'] == r['expect_clarify'] for r in scored_clar), len(scored_clar))}",
    ]
    if not args.only_intent:
        summary += [
            f"- Câu trả lời có nguồn chính thống: {_pct(sum(r['official_source'] for r in answers), len(answers))}",
            f"- Câu trả lời có trích dẫn [S#]: {_pct(sum(r['cited'] for r in answers), len(answers))}",
            f"- Verifier PASS: {_pct(sum(r['verdict'] == 'PASS' for r in answers), len(answers))}",
            f"- Phân bố kết quả: " + ", ".join(
                f"{k}={sum(r['kind'] == k for r in rows)}" for k in sorted({r['kind'] for r in rows})),
        ]
    summary += [
        f"- Độ trễ: p50 {statistics.median(latencies) if latencies else 0:.1f}s · p95 {p95:.1f}s",
        "",
        "Độ đúng nội dung / tỉ lệ bịa: người chấm đọc cột `answer` và `sources` trong CSV.",
    ]

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stem = f"{datetime.now():%Y%m%d-%H%M}_{re.sub(r'[^A-Za-z0-9.]+', '-', LLM_MODEL)}" \
           + ("_intent" if args.only_intent else "")
    with open(out_dir / f"{stem}.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)
    (out_dir / f"{stem}.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("\n" + "\n".join(summary))
    print(f"\nĐã lưu: {out_dir / (stem + '.csv')}")
    mcp_client.shutdown()


if __name__ == "__main__":
    main()

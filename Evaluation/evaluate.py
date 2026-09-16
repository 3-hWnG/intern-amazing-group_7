"""Chấm điểm pipeline trên bộ câu hỏi TỰ SOẠN.

Ba rổ dữ liệu (PLAN_target_state_verifier.md §9):
    A. eval_set.jsonl        bộ phát triển — prompt đã được tinh chỉnh trên chính nó,
                             nên đây KHÔNG phải benchmark, chỉ là số để lặp nhanh
    B. regression_set.jsonl  4 lỗi black-box + câu hỏi nối tiếp + đổi chủ đề — CỔNG CỨNG
    C. (chưa có) bộ giữ kín do người không tinh chỉnh prompt soạn — số đáng báo cáo

Chỉ số:
    intent accuracy          ý định đúng / tổng
    target accuracy          MỤC TIÊU thông tin đúng / tổng
    procedure accuracy       tên thủ tục có chứa cụm mong đợi (câu hỏi nối tiếp)
    clarification accuracy   hỏi lại / trò chuyện / từ chối đúng luồng
    official source rate     câu trả lời có ít nhất 1 nguồn chính thống
    citation rate            câu trả lời có trích dẫn [S#]
    verifier PASS rate       và tỉ lệ câu trả lời nói thẳng "nguồn chưa nêu rõ"
    latency                  p50 / p95

    .venv\\Scripts\\python.exe Evaluation\\evaluate.py --only-intent        # rổ A, nhanh
    .venv\\Scripts\\python.exe Evaluation\\evaluate.py --set regression     # rổ B, cả pipeline
    .venv\\Scripts\\python.exe Evaluation\\evaluate.py --set both --only-intent
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
sys.path.insert(0, str(HERE.parent / "app"))

from config import LLM_MODEL, SEARCH_PROVIDER  # noqa: E402
from core import intent as intent_step  # noqa: E402
from core import mcp_client, orchestrator  # noqa: E402
from domain.text import fold  # noqa: E402
from prompts import templates as T  # noqa: E402

SETS = {"dev": HERE / "eval_set.jsonl", "regression": HERE / "regression_set.jsonl"}


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} = {num / den:.1%}" if den else "—"


def _expected(item: dict, key: str) -> list[str]:
    value = item.get(key)
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _procedure_ok(item: dict, procedure: str, resolved: str) -> bool | None:
    """Tên thủ tục (hoặc câu hỏi đã làm rõ) phải chứa cụm mong đợi."""
    wanted = _expected(item, "expected_procedure_contains")
    if not wanted:
        return None
    hay = fold(f"{procedure} {resolved}")
    return all(fold(w) in hay for w in wanted)


def load(names: list[str], limit: int) -> list[dict]:
    items = []
    for name in names:
        path = SETS[name]
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                item["_set"] = name
                items.append(item)
    return items[:limit] if limit else items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", default="dev", choices=["dev", "regression", "both"])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-intent", action="store_true")
    args = parser.parse_args()

    names = ["dev", "regression"] if args.set == "both" else [args.set]
    items = load(names, args.limit)

    rows = []
    for i, item in enumerate(items, 1):
        history = item.get("history") or []
        state = item.get("state") or {}
        turn_index = int(item.get("turn_index") or len(history))
        started = time.time()

        if args.only_intent:
            u = intent_step.analyze(item["question"], history, "", {}, state, turn_index)
            got_intent, got_target, procedure = u.intent, u.target, u.procedure
            resolved, clarified = u.standalone_question, u.route == "clarify"
            kind = f"{u.route}({u.gate})"
            text, verdict, sources, queries = "", "", [], u.search_queries
            target_in_evidence = None
        else:
            r = orchestrator.run_turn(orchestrator.TurnInput(
                question=item["question"], history=history, state=state,
                turn_index=turn_index))
            got_intent = r.intent.get("intent", "")
            got_target = r.intent.get("target", "")
            procedure = r.intent.get("procedure", "")
            resolved = r.intent.get("standalone_question", "")
            clarified, kind, text, verdict = r.kind == "clarify", r.kind, r.text, r.verdict
            sources, queries = r.sources, (r.evidence or {}).get("queries", [])
            target_in_evidence = r.target_in_evidence
        seconds = time.time() - started

        expected_intent = _expected(item, "expected_intent")
        expected_target = _expected(item, "expected_target")
        row = {
            "set": item["_set"], "id": item["id"], "question": item["question"],
            "expected_intent": "|".join(expected_intent), "intent": got_intent,
            "intent_ok": got_intent in expected_intent if expected_intent else None,
            "expected_target": "|".join(expected_target), "target": got_target,
            "target_ok": got_target in expected_target if expected_target else None,
            "procedure": procedure,
            "procedure_ok": _procedure_ok(item, procedure, resolved),
            "expect_clarify": item.get("expect_clarify"), "clarified": clarified,
            "resolved_question": resolved, "kind": kind, "verdict": verdict,
            "target_in_evidence": target_in_evidence, "seconds": round(seconds, 2),
            "official_source": any(s.get("trust") == "official" for s in sources),
            "cited": bool(re.search(r"\[S\d+", text or "")),
            "says_not_found": T.NOT_IN_SOURCES_TEXT[:40] in (text or "")
                              or "chưa nêu rõ" in (text or ""),
            "queries": " | ".join(queries or []),
            "sources": " | ".join(s.get("url") or s.get("title", "") for s in sources),
            "answer": text,
        }
        rows.append(row)
        flag = lambda ok: "✓" if ok else ("—" if ok is None else "✗")   # noqa: E731
        print(f"[{i}/{len(items)}] {row['id']:<32} intent {flag(row['intent_ok'])} "
              f"target {flag(row['target_ok'])}={got_target:<18} "
              f"thủ tục {flag(row['procedure_ok'])} {kind:<18} {verdict:<4} {seconds:5.1f}s")

    def counted(key: str) -> tuple[int, int]:
        scored = [r for r in rows if r[key] is not None]
        return sum(bool(r[key]) for r in scored), len(scored)

    clar = [r for r in rows if r["expect_clarify"] is not None]
    answers = [r for r in rows if r["kind"] == "answer"]
    latencies = sorted(r["seconds"] for r in rows)
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0

    summary = [
        f"# Kết quả đánh giá — {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"- Mô hình: `{LLM_MODEL}` · tìm kiếm: `{SEARCH_PROVIDER}` · rổ: {args.set} · "
        f"chế độ: {'chỉ hiểu ý định' if args.only_intent else 'cả pipeline'} · {len(rows)} câu",
        f"- Intent accuracy: {_pct(*counted('intent_ok'))}",
        f"- **Target accuracy: {_pct(*counted('target_ok'))}**",
        f"- **Procedure accuracy (câu nối tiếp / đổi chủ đề): {_pct(*counted('procedure_ok'))}**",
        f"- Clarification accuracy: "
        f"{_pct(sum(r['clarified'] == r['expect_clarify'] for r in clar), len(clar))}",
    ]
    if not args.only_intent:
        summary += [
            f"- Nguồn chính thống: {_pct(sum(r['official_source'] for r in answers), len(answers))}",
            f"- Có trích dẫn [S#]: {_pct(sum(r['cited'] for r in answers), len(answers))}",
            f"- Verifier PASS: {_pct(sum(r['verdict'] == 'PASS' for r in answers), len(answers))}",
            f"- Mục tiêu có trong nguồn: "
            f"{_pct(sum(bool(r['target_in_evidence']) for r in rows), len([r for r in rows if r['target_in_evidence'] is not None]))}",
            f"- Nói thẳng 'nguồn chưa nêu rõ': "
            f"{_pct(sum(r['says_not_found'] for r in answers), len(answers))}",
            "- Phân bố kết quả: " + ", ".join(
                f"{k}={sum(r['kind'] == k for r in rows)}" for k in sorted({r['kind'] for r in rows})),
        ]
    summary += [
        f"- Độ trễ: p50 {statistics.median(latencies) if latencies else 0:.1f}s · p95 {p95:.1f}s",
        "",
        "Rổ `dev` là số để lặp nhanh, KHÔNG phải benchmark (prompt đã tinh chỉnh trên nó).",
        "Tỉ lệ 'claim không có nguồn lọt qua' phải do người chấm đọc cột `answer` + `sources`.",
    ]

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stem = (f"{datetime.now():%Y%m%d-%H%M}_{re.sub(r'[^A-Za-z0-9.]+', '-', LLM_MODEL)}"
            f"_{args.set}" + ("_intent" if args.only_intent else ""))
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

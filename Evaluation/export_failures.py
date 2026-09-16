"""Xuất nhật ký từng lượt (bảng turn_log) ra CSV để PHÂN LOẠI LỖI bằng tay.

Câu hỏi cần trả lời cho mỗi câu trả lời tồi: hỏng ở bước nào?

    CONTEXT       hiểu sai câu hỏi nối tiếp / bối cảnh
    INTENT        sai ý định
    TARGET        sai khía cạnh được hỏi (hỏi thời hạn, trả lời giấy tờ)
    RETRIEVAL     nguồn không chứa thủ tục / khía cạnh được hỏi
    GENERATION    nguồn đúng nhưng câu trả lời sai
    VERIFICATION  lỗi lọt qua kiểm chứng
    OK            không có lỗi

Cột `failure_class` để trống sẵn — người chấm điền. Khi đã có 50-100 dòng được
phân loại thì mới biết nên sửa tiếp phần nào (và có cần Portal MCP hay không).

    .venv\\Scripts\\python.exe Evaluation\\export_failures.py
    .venv\\Scripts\\python.exe Evaluation\\export_failures.py --limit 500 --only-bad
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app"))

from config import DB_PATH  # noqa: E402

COLUMNS = ["failure_class", "note", "id", "created_at", "model", "kind", "verdict",
           "user_question", "resolved_question", "intent", "target", "procedure_name",
           "gate", "route", "follow_up", "target_in_evidence", "n_sources",
           "official_sources", "search_queries", "source_titles", "evidence_error",
           "rule_issues", "answers_target", "final_text", "draft"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--only-bad", action="store_true",
                        help="chỉ lấy lượt FAIL / no_evidence / nguồn không có mục tiêu")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM turn_log ORDER BY id DESC LIMIT ?",
                        (args.limit,)).fetchall()

    out, stats = [], Counter()
    for r in rows:
        try:
            p = json.loads(r["payload_json"] or "{}")
        except Exception:
            p = {}
        sources = p.get("sources") or []
        verification = p.get("verification") or {}
        suspicious = (r["verdict"] == "FAIL" or r["kind"] in ("no_evidence", "error")
                      or p.get("target_in_evidence") is False)
        if args.only_bad and not suspicious:
            continue
        stats[f"kind={r['kind']}"] += 1
        stats[f"verdict={r['verdict'] or '-'}"] += 1
        if p.get("target_in_evidence") is False:
            stats["nguồn KHÔNG có mục tiêu"] += 1
        out.append({
            "failure_class": "", "note": "",
            "id": r["id"], "created_at": r["created_at"], "model": r["model"],
            "kind": r["kind"], "verdict": r["verdict"],
            "user_question": r["user_question"], "resolved_question": r["resolved_question"],
            "intent": r["intent"], "target": r["target"], "procedure_name": r["procedure_name"],
            "gate": r["gate"], "route": r["route"], "follow_up": p.get("follow_up"),
            "target_in_evidence": p.get("target_in_evidence"),
            "n_sources": len(sources),
            "official_sources": sum(1 for s in sources if s.get("trust") == "official"),
            "search_queries": " | ".join(p.get("search_queries") or []),
            "source_titles": " | ".join(f"{s.get('domain')}" for s in sources),
            "evidence_error": p.get("evidence_error", ""),
            "rule_issues": " | ".join(verification.get("rule_issues") or []),
            "answers_target": verification.get("answers_target"),
            "final_text": (p.get("final_text") or "")[:1500],
            "draft": (p.get("draft") or "")[:1500],
        })

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"turnlog-{datetime.now():%Y%m%d-%H%M}.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(out)

    print(f"{len(out)} lượt -> {path}")
    for key, count in stats.most_common():
        print(f"  {key}: {count}")
    if not out:
        print("Chưa có dữ liệu: dùng ứng dụng vài lượt rồi chạy lại "
              "(TURN_LOG_ENABLED phải bật).")


if __name__ == "__main__":
    main()

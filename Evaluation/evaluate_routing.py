"""Chấm bước CHỌN CÔNG CỤ của luồng agent (v6).

Bộ 862 câu đã có sẵn nhãn cần dùng — không phải gán tay thêm gì:

    in_scope = 1              -> đáng lẽ phải tra bảng nội bộ (search_procedures)
    oos_kind = 'xa_giao'      -> đáng lẽ KHÔNG tra gì (none)
    oos_kind = khác           -> đáng lẽ ra web, hoặc trả lời chay; TUYỆT ĐỐI
                                 không được khẳng định như thể có trong bảng

Đây là con số thay thế cho "cảm giác thấy nó thông minh hơn". Chạy lại mỗi khi
đổi mô hình hoặc sửa prompt quyết định.

Cách chạy (từ thư mục gốc project) — PHẢI dùng python của .venv:

    .\\run.ps1 -Routing -Limit 100
    .\\run.ps1 -Routing -Save v6_qwen1.5b

hoặc gọi thẳng:

    .venv\\Scripts\\python.exe Evaluation\\evaluate_routing.py --save v6_qwen1.5b

Gõ `Evaluation\\evaluate_routing.py` trần trong PowerShell là chạy bằng Python
TOÀN CỤC (không có fastapi/torch/ollama) — cửa sổ chớp rồi tắt, không in gì.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

EVAL_CSV = Path(__file__).resolve().parent / "eval_questions.csv"


def expected_for(row: dict) -> set[str]:
    if str(row.get("in_scope", "")).strip() == "1":
        return {"search_procedures", "get_procedure"}
    if (row.get("oos_kind") or "").strip() == "xa_giao":
        return {"none"}
    return {"search_web", "none"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default=str(EVAL_CSV))
    ap.add_argument("--limit", type=int, default=0, help="chỉ chấm N câu đầu")
    ap.add_argument("--save", default="", help="tên mốc, lưu vào Evaluation/baselines/")
    args = ap.parse_args()

    try:
        from config import (AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL,
                            AGENT_TOOL_MODE, LLM_MODEL_NAME)
        from core import agent, resources, smalltalk
    except ImportError as exc:
        print("\n" + "!" * 64)
        print("KHÔNG NẠP ĐƯỢC THƯ VIỆN CỦA DỰ ÁN:", exc)
        print(f"Đang chạy bằng: {sys.executable}")
        print("\nGần như chắc chắn bạn đang chạy bằng Python TOÀN CỤC chứ không")
        print("phải .venv. Chạy lại bằng một trong hai cách:")
        print("\n    .\\run.ps1 -Routing -Save v6_qwen1.5b")
        print("    .venv\\Scripts\\python.exe Evaluation\\evaluate_routing.py"
              " --save v6_qwen1.5b")
        print("!" * 64)
        return 2

    rows = list(csv.DictReader(open(args.eval, encoding="utf-8-sig")))
    if args.limit:
        rows = rows[:args.limit]

    manifest = (f"- [chung] Thủ tục hành chính (dataset nội bộ): "
                f"{resources.global_description()} -> dùng search_procedures")

    print(f"Mô hình      : {LLM_MODEL_NAME}")
    print(f"Chế độ công cụ: {AGENT_TOOL_MODE}")
    print(f"Guardrail     : {AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL}")
    print(f"Số câu        : {len(rows)}\n")

    hits = 0
    by_group: dict[str, Counter] = defaultdict(Counter)
    confusion = Counter()
    guardrail_fired = 0
    smalltalk_caught = 0
    results = []
    started = time.time()

    for i, row in enumerate(rows, 1):
        question = row["question"]
        expected = expected_for(row)
        group = ("in_scope" if str(row.get("in_scope", "")).strip() == "1"
                 else (row.get("oos_kind") or "oos"))

        # Bộ lọc xã giao chạy TRƯỚC LLM, đúng như trong agent.build().
        if smalltalk.is_smalltalk(question):
            chosen = "none"
            smalltalk_caught += 1
        else:
            choice = agent._decide(question, manifest, "", None, [], False)
            chosen = choice["tool"]
            if (chosen == "none" and AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL
                    and smalltalk.has_admin_signal(question)):
                chosen = "search_procedures"
                guardrail_fired += 1

        ok = chosen in expected
        hits += ok
        by_group[group]["n"] += 1
        by_group[group]["hit"] += ok
        if not ok:
            confusion[f"{group} -> {chosen}"] += 1
        results.append({**row, "chosen_tool": chosen,
                        "expected": "|".join(sorted(expected)), "hit": int(ok)})

        if i % 50 == 0:
            print(f"  {i}/{len(rows)}  đúng {hits / i:.1%}")

    elapsed = time.time() - started
    print("\n" + "=" * 62)
    print(f"ĐỘ CHÍNH XÁC CHỌN CÔNG CỤ : {hits / max(1, len(rows)):.4f}"
          f"  ({hits}/{len(rows)})")
    print(f"Thời gian                  : {elapsed:.0f}s "
          f"({elapsed / max(1, len(rows)) * 1000:.0f} ms/câu)")
    print(f"Bộ lọc xã giao bắt được    : {smalltalk_caught}")
    print(f"Guardrail phải can thiệp   : {guardrail_fired}"
          f"  (càng thấp càng tốt — mô hình càng tự biết đường)")

    print("\nTheo nhóm câu hỏi:")
    for group, c in sorted(by_group.items(), key=lambda kv: -kv[1]["n"]):
        print(f"  {group:16} {c['hit']:4}/{c['n']:<4} = {c['hit'] / max(1, c['n']):.1%}")

    if confusion:
        print("\nChọn sai nhiều nhất:")
        for key, n in confusion.most_common(10):
            print(f"  {n:4}  {key}")

    out_dir = Path(__file__).resolve().parent
    if args.save:
        out_dir = out_dir / "baselines" / args.save
        out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "routing_results.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nChi tiết: {path}")

    if args.save:
        summary = {
            "model": LLM_MODEL_NAME, "tool_mode": AGENT_TOOL_MODE,
            "guardrail": AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL,
            "n": len(rows), "accuracy": hits / max(1, len(rows)),
            "guardrail_fired": guardrail_fired,
            "smalltalk_caught": smalltalk_caught,
            "ms_per_question": elapsed / max(1, len(rows)) * 1000,
            "by_group": {g: dict(c) for g, c in by_group.items()},
        }
        (out_dir / "ROUTING.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Tóm tắt : {out_dir / 'ROUTING.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

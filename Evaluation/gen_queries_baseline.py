"""Sinh BASELINE truy vấn tìm kiếm cho bộ 862 câu (Evaluation/eval_questions.csv).

Chỉ chạy bước HIỂU Ý ĐỊNH của V10.1 (understand + gate): KHÔNG tra web, KHÔNG soạn
câu trả lời. Kết quả là đầu vào cho bước sau: đo xem truy vấn có tìm ra đúng
trang thủ tục không, rồi lọc câu sai để làm dataset fine-tune mô hình tạo truy vấn.

    .venv\\Scripts\\python.exe Evaluation\\gen_queries_baseline.py --model qwen2.5:1.5b
    .venv\\Scripts\\python.exe Evaluation\\gen_queries_baseline.py --model qwen2.5:1.5b --limit 20
    .venv\\Scripts\\python.exe Evaluation\\gen_queries_baseline.py --variant abbrev,typo
    .venv\\Scripts\\python.exe Evaluation\\gen_queries_baseline.py --model qwen2.5:1.5b --fewshot on
Không truyền --fewshot thì dùng UNDERSTAND_FEWSHOT trong .env (trạng thái in ra ở dòng đầu).

Chạy lại cùng lệnh sẽ CHẠY TIẾP từ câu còn dang dở (bỏ qua qid đã có trong file kết quả).
Kết quả: Evaluation/results/queries_baseline_<model>_fewshot_<on|off>.csv  (+ .md tóm tắt)
(mô hình qwen2.5:1.5b được viết gọn thành 1.5b, vd. queries_baseline_1.5b_fewshot_off.csv)

Cột chính:
    queries_raw     truy vấn mô hình trả về NGUYÊN BẢN (JSON list, có thể rỗng)
    queries_llm     truy vấn sau khi code V10.1 hậu xử lý (thêm năm, rỗng -> câu viết lại)
    queries_search  truy vấn thực sự gửi đi tìm kiếm (như core/evidence.gather: thêm site:gov.vn)
    route           search | clarify | chitchat | out_of_scope
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

FIELDS = ["qid", "question", "topic_key", "topic", "gold_title", "linh_vuc", "variant",
          "difficulty", "in_scope", "oos_kind", "model", "intent", "route", "gate",
          "needs_clarification", "standalone_question", "province", "queries_raw", "queries_llm",
          "queries_search", "n_queries_raw", "seconds", "error"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=str(HERE / "eval_questions.csv"))
    p.add_argument("--model", default="",
                   help="ghi đè LLM_MODEL trong .env (khuyên: qwen2.5:1.5b cho baseline)")
    p.add_argument("--limit", type=int, default=0, help="chỉ chạy N câu đầu (để thử)")
    p.add_argument("--variant", default="", help="lọc theo variant, phân tách dấu phẩy")
    p.add_argument("--fewshot", choices=["on", "off"], default="",
                   help="bật/tắt ví dụ mẫu của bước understand (ghi đè UNDERSTAND_FEWSHOT trong .env)")
    p.add_argument("--no-fewshot", action="store_true", help="= --fewshot off")
    p.add_argument("--out", default="", help="đường dẫn CSV kết quả (mặc định tự đặt tên)")
    return p.parse_args()


ARGS = parse_args()
if ARGS.model:
    os.environ["LLM_MODEL"] = ARGS.model          # phải đặt TRƯỚC khi import config
if ARGS.no_fewshot:
    ARGS.fewshot = "off"
if ARGS.fewshot:
    os.environ["UNDERSTAND_FEWSHOT"] = "true" if ARGS.fewshot == "on" else "false"
sys.path.insert(0, str(ROOT / "Backend"))
sys.path.insert(0, str(ROOT))

from config import LLM_MODEL, SEARCH_MAX_QUERIES, UNDERSTAND_FEWSHOT  # noqa: E402
from core import intent as intent_step  # noqa: E402
from core import llm  # noqa: E402


_last_raw: dict = {}
_chat_json = llm.chat_json


def _recording_chat_json(role, system, user, schema, *args, **kwargs):
    """Ghi lại JSON gốc của bước understand (trước khi intent.py hậu xử lý)."""
    raw = _chat_json(role, system, user, schema, *args, **kwargs)
    if "search_queries" in json.dumps(schema):
        _last_raw["understand"] = raw
    return raw


intent_step.llm.chat_json = _recording_chat_json


def short_model(name: str) -> str:
    """qwen2.5:1.5b -> 1.5b ; 3b_finetune_v2:latest -> 3b_finetune_v2"""
    name = name.removesuffix(":latest")
    if name.startswith("qwen2.5:"):
        name = name.split(":", 1)[1]
    return re.sub(r"[^A-Za-z0-9._]+", "-", name)


def search_queries(u) -> list[str]:
    """Giống hệt core/evidence.gather (official_bias=True) nhưng không gọi MCP."""
    queries = [q for q in u.search_queries if q] or [u.standalone_question]
    queries = queries + [f"{queries[0]} site:gov.vn"]
    return list(dict.fromkeys(queries))[:SEARCH_MAX_QUERIES]


def load_items(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        items = list(csv.DictReader(f))
    if ARGS.variant:
        wanted = {v.strip() for v in ARGS.variant.split(",") if v.strip()}
        items = [i for i in items if i.get("variant") in wanted]
    return items[:ARGS.limit] if ARGS.limit else items


def done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        # câu lỗi (vd. Ollama tắt giữa chừng) sẽ được chạy lại
        return {r["qid"] for r in csv.DictReader(f) if not r.get("error")}


def run_one(item: dict) -> dict:
    row = {k: item.get(k, "") for k in FIELDS if k in item}
    row.update(model=LLM_MODEL, error="")
    started = time.time()
    _last_raw.clear()
    try:
        u = intent_step.analyze(item["question"], [], "", {})
        row.update(
            intent=u.intent, route=u.route, gate=u.gate,
            needs_clarification=u.needs_clarification,
            standalone_question=u.standalone_question, province=u.province,
            queries_raw=json.dumps([q for q in (_last_raw.get("understand") or {})
                                    .get("search_queries") or [] if str(q).strip()],
                                   ensure_ascii=False),
            queries_llm=json.dumps(u.search_queries, ensure_ascii=False),
            queries_search=json.dumps(search_queries(u) if u.route == "search" else [],
                                      ensure_ascii=False),
            n_queries_raw=len([q for q in (_last_raw.get("understand") or {})
                               .get("search_queries") or [] if str(q).strip()]),
        )
    except llm.LLMError as exc:
        row["error"] = str(exc)[:300]
    except Exception as exc:            # lỗi JSON / lỗi lạ: ghi lại, không dừng cả lượt chạy
        row["error"] = f"{type(exc).__name__}: {exc}"[:300]
    row["seconds"] = round(time.time() - started, 2)
    return row


def summarize(path: Path) -> str:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["model"] == LLM_MODEL]
    ok = [r for r in rows if not r["error"]]
    ins = [r for r in ok if r["in_scope"] == "1"]
    oos = [r for r in ok if r["in_scope"] == "0"]
    secs = sorted(float(r["seconds"] or 0) for r in ok)

    def pct(n: int, d: int) -> str:
        return f"{n}/{d} = {n / d:.1%}" if d else "—"

    lines = [
        f"# Baseline truy vấn — {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"- Mô hình: `{LLM_MODEL}` · few-shot: **{'BẬT' if UNDERSTAND_FEWSHOT else 'TẮT'}** · "
        f"{len(rows)} câu · lỗi: {len(rows) - len(ok)}",
        f"- Trong phạm vi → đi tra cứu (route=search): "
        f"{pct(sum(r['route'] == 'search' for r in ins), len(ins))}",
        f"- Trong phạm vi → hỏi lại: {pct(sum(r['route'] == 'clarify' for r in ins), len(ins))}",
        f"- Ngoài phạm vi → KHÔNG tra cứu: {pct(sum(r['route'] != 'search' for r in oos), len(oos))}",
        f"- Mô hình không trả truy vấn nào (code dùng câu viết lại thay thế): "
        f"{pct(sum(r['n_queries_raw'] == '0' for r in ins), len(ins))}",
        f"- Độ trễ mỗi câu: p50 {secs[len(secs) // 2] if secs else 0:.1f}s",
        "",
        "## Theo kiểu câu (chỉ câu trong phạm vi)",
        "",
        "| variant | số câu | route=search | mô hình không trả truy vấn |",
        "|---|---|---|---|",
    ]
    for variant, n in sorted(Counter(r["variant"] for r in ins).items()):
        group = [r for r in ins if r["variant"] == variant]
        lines.append(f"| {variant} | {n} | {pct(sum(r['route'] == 'search' for r in group), n)} | "
                     f"{pct(sum(r['n_queries_raw'] == '0' for r in group), n)} |")
    lines += ["", "Bước tiếp theo: tra thử `queries_search` và chấm xem có ra đúng trang "
              "thủ tục (`gold_title`) không."]
    return "\n".join(lines) + "\n"


def main() -> None:
    data = Path(ARGS.data)
    if not data.exists():
        sys.exit(f"Không thấy {data}")
    items = load_items(data)
    out = Path(ARGS.out) if ARGS.out else \
        HERE / "results" / (f"queries_baseline_{short_model(LLM_MODEL)}"
                            f"_fewshot_{'on' if UNDERSTAND_FEWSHOT else 'off'}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    skip = done_ids(out)
    todo = [i for i in items if i["qid"] not in skip]
    print(f"Mô hình {LLM_MODEL} · few-shot {'BẬT' if UNDERSTAND_FEWSHOT else 'TẮT'} · {len(items)} câu · đã xong {len(items) - len(todo)} · "
          f"còn {len(todo)} -> {out}")

    st = llm.status()
    if not st["reachable"] or st["missing"]:
        sys.exit(f"Ollama chưa sẵn sàng: {st}")

    new_file = not out.exists()
    started = time.time()
    with open(out, "a", newline="", encoding="utf-8-sig" if new_file else "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for n, item in enumerate(todo, 1):
            row = run_one(item)
            writer.writerow(row)
            f.flush()                                   # dừng giữa chừng không mất dữ liệu
            eta = (time.time() - started) / n * (len(todo) - n)
            status = "LỖI " + row["error"][:60] if row["error"] else \
                f"{row['route']:<12} {row['queries_llm'][:70]}"
            print(f"[{n}/{len(todo)}] {row['qid']} {row['variant']:<13} {status}  "
                  f"({row['seconds']}s, còn ~{eta / 60:.0f} phút)")

    report = summarize(out)
    out.with_suffix(".md").write_text(report, encoding="utf-8")
    print("\n" + report + f"\nĐã lưu: {out}")


if __name__ == "__main__":
    main()

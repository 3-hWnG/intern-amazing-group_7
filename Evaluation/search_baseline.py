"""Đo TRA CỨU THẬT cho 3 cách tạo truy vấn trên cùng một mẫu câu hỏi.

    A  model     truy vấn mô hình sinh (cột queries_search — đúng thứ hệ thống V10.1 gửi đi)
    B  question  câu hỏi gốc của người dùng (cách 4): [câu hỏi, câu hỏi site:gov.vn]
    C  both      gộp kết quả A + B rồi xếp hạng chung (không tốn thêm lượt tra)

Chỉ số (trên top-K kết quả sau xếp hạng, giống bước 1 của engine.build_evidence_pack):
    hit@K        có ít nhất 1 kết quả ĐÚNG THỦ TỤC (tiêu đề/đoạn trích chứa >= 60% từ khoá tên thủ tục)
    hit@K_trust  như trên nhưng kết quả phải là nguồn chính thống hoặc CSDL pháp luật
    hit@1        kết quả đứng đầu đúng thủ tục

    .venv\\Scripts\\python.exe Evaluation\\search_baseline.py
    .venv\\Scripts\\python.exe Evaluation\\search_baseline.py --n 60 --delay 2
    .venv\\Scripts\\python.exe Evaluation\\search_baseline.py --input Evaluation\\results\\queries_baseline_1.5b_fewshot_on.csv

Mỗi truy vấn chỉ tra MỘT lần: kết quả lưu ở Evaluation/results/search_cache.json, chạy lại
(hoặc bị chặn giữa chừng rồi chạy lại) sẽ dùng cache. Truy vấn lỗi không được cache.
Luật "đúng thủ tục" là heuristic: đọc cột top_titles trong CSV để kiểm tra lại.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app"))

from mcp_search import engine  # noqa: E402

STOP = set("thu tuc cap dang ky giay lai moi va cho cua o tai the nhung gi la co khong "
           "ve voi mot cac trong".split())
CONFIGS = ("model", "question", "both")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--input", default=str(HERE / "results" / "queries_baseline_1.5b_fewshot_off.csv"),
                   help="file do gen_queries_baseline.py sinh ra")
    p.add_argument("--n", type=int, default=154, help="số câu mẫu (chia đều theo variant)")
    p.add_argument("--k", type=int, default=5, help="top-K để chấm")
    p.add_argument("--delay", type=float, default=1.5, help="giây nghỉ giữa 2 lượt tra THẬT")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--cache", default=str(HERE / "results" / "search_cache.json"))
    return p.parse_args()


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", str(text or "").lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn").replace("đ", "d")


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", fold(text)))


def is_hit(row: dict, topic: str) -> bool:
    key = tokens(topic) - STOP or tokens(topic)
    got = tokens(f"{row.get('title', '')} {row.get('snippet', '')} {row.get('url', '')}")
    return bool(key) and len(key & got) / len(key) >= 0.6


# ------------------------------------------------------------------ tra cứu ---
class Searcher:
    def __init__(self, path: Path, delay: float):
        self.path, self.delay = path, delay
        self.cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.live = self.failed = 0
        self._last = 0.0

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def search(self, query: str) -> list[dict]:
        if query in self.cache:
            return self.cache[query]
        for attempt in range(3):
            wait = self.delay * (1 + 2 * attempt) - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            log: list[str] = []
            rows = engine.web_search(query, engine.SEARCH_RESULTS_PER_QUERY, log)
            self._last = time.time()
            self.live += 1
            if rows or not any("LỖI" in line for line in log):
                keep = ("title", "url", "snippet", "domain", "trust", "rank", "published_at")
                self.cache[query] = [{k: r.get(k) for k in keep} for r in rows]
                if self.live % 10 == 0:
                    self.save()
                return self.cache[query]
            print(f"    ! lỗi tra '{query[:50]}' (lần {attempt + 1}): {log[-1][:120]}")
        self.failed += 1
        return []                                   # không cache -> lần chạy sau thử lại


def rank(batches: list[list[dict]]) -> list[dict]:
    """Gộp + xếp hạng như bước 1 của engine.build_evidence_pack."""
    merged: dict[str, dict] = {}
    for rows in batches:
        for row in rows:
            base = (engine.TRUST_WEIGHT.get(row["trust"], 1.0) + 1.0 / (1 + 0.35 * row["rank"])
                    + engine._recency(f"{row['title']} {row['snippet']} {row['url']}"))
            key = engine._norm_url(row["url"])
            if key in merged:
                merged[key]["score"] = max(merged[key]["score"], base) + 0.3
            else:
                merged[key] = {**row, "score": base}
    return sorted(merged.values(), key=lambda r: -r["score"])


def question_queries(q: str) -> list[str]:
    return [q, f"{q} site:gov.vn"]


# ------------------------------------------------------------------ mẫu -------
def sample(rows: list[dict], n: int, seed: int) -> list[dict]:
    groups = defaultdict(list)
    for r in rows:
        if r.get("in_scope") == "1" and r.get("route") == "search" and not r.get("error"):
            groups[r["variant"]].append(r)
    rnd = random.Random(seed)
    per = max(1, n // max(1, len(groups)))
    picked = []
    for variant in sorted(groups):
        items = groups[variant][:]
        rnd.shuffle(items)
        picked += items[:per]
    return picked


def main() -> None:
    args = parse_args()
    src = Path(args.input)
    with open(src, encoding="utf-8-sig", newline="") as f:
        items = sample(list(csv.DictReader(f)), args.n, args.seed)
    searcher = Searcher(Path(args.cache), args.delay)
    todo = {q for it in items for q in json.loads(it["queries_search"]) + question_queries(it["question"])}
    uncached = len(todo - set(searcher.cache))
    print(f"{len(items)} câu · {len(todo)} truy vấn · cần tra thật {uncached} "
          f"(~{uncached * (args.delay + 2.5) / 60:.0f} phút) · provider {engine.SEARCH_PROVIDER}")

    out_rows, started = [], time.time()
    try:
        for i, it in enumerate(items, 1):
            topic = it["topic"]
            model_b = [searcher.search(q) for q in json.loads(it["queries_search"])]
            quest_b = [searcher.search(q) for q in question_queries(it["question"])]
            flags = []
            for name, batches in zip(CONFIGS, (model_b, quest_b, model_b + quest_b)):
                top = rank(batches)[:args.k]
                hits = [is_hit(r, topic) for r in top]
                row = {
                    "qid": it["qid"], "variant": it["variant"], "topic": topic,
                    "question": it["question"], "config": name,
                    "queries": " | ".join(json.loads(it["queries_search"]) if name == "model"
                                          else question_queries(it["question"]) if name == "question"
                                          else json.loads(it["queries_search"]) + question_queries(it["question"])),
                    "n_results": len(top),
                    "hit@1": bool(hits[:1] and hits[0]),
                    f"hit@{args.k}": any(hits),
                    f"hit@{args.k}_trust": any(h and r["trust"] in ("official", "legal")
                                               for h, r in zip(hits, top)),
                    "top_titles": " || ".join(f"{'✓' if h else '·'} {r['title'][:70]} ({r['domain']})"
                                              for h, r in zip(hits, top)),
                }
                out_rows.append(row)
                flags.append("✓" if row[f"hit@{args.k}"] else "✗")
            eta = (time.time() - started) / i * (len(items) - i) / 60
            print(f"[{i}/{len(items)}] {it['qid']} {it['variant']:<13} "
                  f"model {flags[0]}  question {flags[1]}  both {flags[2]}   (còn ~{eta:.0f} phút)")
    except KeyboardInterrupt:
        print("\nDừng giữa chừng — đã lưu cache, chạy lại sẽ tiếp tục nhanh.")
    finally:
        searcher.save()

    if not out_rows:
        return
    stamp = f"{datetime.now():%Y%m%d-%H%M}"
    out = HERE / "results" / f"search_baseline_{stamp}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    report = summarize(out_rows, args, src, searcher)
    out.with_suffix(".md").write_text(report, encoding="utf-8")
    print("\n" + report + f"\nĐã lưu: {out}")


def summarize(rows: list[dict], args, src: Path, searcher: Searcher) -> str:
    k = args.k
    n_q = len({r["qid"] for r in rows})

    def rate(group: list[dict], col: str) -> str:
        return f"{sum(r[col] for r in group) / len(group):.1%}" if group else "—"

    lines = [
        f"# Tra cứu thật: truy vấn mô hình vs câu hỏi gốc — {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"- Nguồn truy vấn: `{src.name}` · {n_q} câu (chia đều theo variant, seed {args.seed})",
        f"- Tìm kiếm: `{engine.SEARCH_PROVIDER}` · top-{k} · tra thật {searcher.live} lượt, "
        f"lỗi hẳn {searcher.failed} truy vấn",
        "",
        f"| cấu hình | hit@1 | hit@{k} | hit@{k} nguồn tin cậy |",
        "|---|---|---|---|",
    ]
    label = {"model": "A. truy vấn mô hình", "question": "B. câu hỏi gốc (cách 4)",
             "both": "C. gộp A + B"}
    for name in CONFIGS:
        g = [r for r in rows if r["config"] == name]
        lines.append(f"| {label[name]} | {rate(g, 'hit@1')} | {rate(g, f'hit@{k}')} | "
                     f"{rate(g, f'hit@{k}_trust')} |")
    lines += ["", f"## hit@{k} theo kiểu câu", "",
              "| variant | n | A. mô hình | B. câu gốc | C. gộp |", "|---|---|---|---|---|"]
    for variant in sorted({r["variant"] for r in rows}):
        g = {name: [r for r in rows if r["variant"] == variant and r["config"] == name]
             for name in CONFIGS}
        lines.append(f"| {variant} | {len(g['model'])} | " + " | ".join(
            rate(g[name], f"hit@{k}") for name in CONFIGS) + " |")
    by_q = defaultdict(dict)
    for r in rows:
        by_q[r["qid"]][r["config"]] = r[f"hit@{k}"]
    only_model = sum(v.get("model") and not v.get("question") for v in by_q.values())
    only_quest = sum(v.get("question") and not v.get("model") for v in by_q.values())
    lines += ["", f"- Chỉ truy vấn mô hình tìm ra: {only_model} câu · "
                  f"chỉ câu hỏi gốc tìm ra: {only_quest} câu",
              "- Luật chấm là heuristic (từ khoá tên thủ tục trong tiêu đề/đoạn trích): "
              "kiểm tra lại cột `top_titles`."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()

"""
calibrate.py — Đo phân phối gap_ratio / name_coverage của service.py trên bộ
56 câu thật (Evaluation/realistic_set.jsonl: 40 câu đơn + 16 hội thoại nối
tiếp). Chạy THUẦN SQL, không cần Ollama/mạng — vài giây là xong.

Chạy 2 lượt trên mỗi câu, LÝ DO tách 2 lượt:
  B. keyword = topic (tên thủ tục chuẩn, có sẵn trong bộ câu làm nhãn) —
     mô phỏng ĐẦU RA ĐÚNG mà LLM1 (extractor.py) phải tạo ra. Đây mới là
     phép đo calibrate 2 ngưỡng (AMBIGUOUS_GAP_RATIO, MIN_NAME_COVERAGE) của
     TẦNG DB, tách khỏi chất lượng của LLM1 (chưa viết).
  A. keyword = turns[-1] (câu hỏi thô, người dân viết, vd "vk e mới đẻ hôm
     qua, giờ làm giấy tờ cho bé ntn a") — KHÔNG dùng để calibrate ngưỡng,
     chỉ để đo/định lượng khoảng cách mà LLM1 cần lấp — tầng DB (FTS5 khớp
     từ khóa) không được thiết kế để tự hiểu câu hỏi kiểu này, đúng theo
     kiến trúc đã chốt ("teencode/viết tắt giao cho LLM 1").

Dùng: python calibrate.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from service import connect, resolve_query, search_candidates, _name_coverage, DEFAULT_DB

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "Evaluation" / "realistic_set.jsonl"


def load_items(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def topic_coverage_in_db(conn, topic: str) -> float:
    """Độ khớp tốt nhất giữa `topic` và TÊN của bất kỳ thủ tục nào trong DB —
    dùng để phân biệt 'topic có trong 70 thủ tục hiện có hay không' (khoảng
    trống dữ liệu, không phải lỗi ngưỡng) khỏi 'topic có trong DB nhưng hệ
    thống chọn sai/không chắc' (lỗi ngưỡng thật)."""
    rows = search_candidates(conn, topic, limit=10)
    if not rows:
        return 0.0
    return max(_name_coverage(topic, r["name"]) for r in rows)


def run(conn, items: list[dict], key_fn, tag: str) -> list[dict]:
    out = []
    for it in items:
        kw = key_fn(it)
        r = resolve_query(conn, kw, province=None)
        d = r["debug"]
        out.append({
            "id": it["id"], "kind": it["kind"], "topic": it["topic"], "tag": tag,
            "keyword": kw, "found": r["found"], "confident": r["confident"],
            "top_name": r["primary"]["procedure"]["name"] if r["found"] else None,
            "name_coverage": d.get("name_coverage"), "gap_ratio": d.get("gap_ratio"),
            "distinct_procedures": d.get("distinct_procedures"),
            "has_suggestion": r["suggestion"] is not None,
        })
    return out


def pct(n, d):
    return f"{n}/{d} ({n/d:.0%})" if d else "0/0"


def main():
    items = load_items(DATA)
    conn = connect(DEFAULT_DB)
    singles = [i for i in items if i["kind"] == "single"]
    follows = [i for i in items if i["kind"] == "followup"]
    print(f"Bộ câu: {len(items)} ({len(singles)} đơn, {len(follows)} hội thoại)\n")

    # --- Bước 0: topic nào có trong 70 thủ tục hiện có? (khoảng trống dữ liệu) ---
    topic_cov = {}
    for it in items:
        if it["topic"] not in topic_cov:
            topic_cov[it["topic"]] = topic_coverage_in_db(conn, it["topic"])
    in_db = {t: c for t, c in topic_cov.items() if c >= 0.6}
    not_in_db = {t: c for t, c in topic_cov.items() if c < 0.6}
    print(f"Chủ đề có trong 70 thủ tục hiện có: {len(in_db)}/{len(topic_cov)} chủ đề riêng biệt")
    print(f"Chủ đề CHƯA có (chờ crawler bổ sung): {len(not_in_db)}/{len(topic_cov)}")
    for t in sorted(not_in_db):
        print(f"   - {t}")
    print()

    # --- Lượt B: keyword = topic (mô phỏng LLM1 trích xuất đúng) ---
    rows_b = run(conn, items, lambda i: i["topic"], "B_topic")
    in_scope_b = [r for r in rows_b if topic_cov[r["topic"]] >= 0.6]
    out_scope_b = [r for r in rows_b if topic_cov[r["topic"]] < 0.6]

    print("=== LƯỢT B — keyword=topic (calibrate ngưỡng tầng DB) ===")
    print(f"Trong phạm vi 70 thủ tục ({len(in_scope_b)} câu):")
    print(f"  confident=True : {pct(sum(r['confident'] for r in in_scope_b), len(in_scope_b))}")
    covs = [r["name_coverage"] for r in in_scope_b if r["name_coverage"] is not None]
    if covs:
        print(f"  name_coverage: min={min(covs):.2f} median={statistics.median(covs):.2f} max={max(covs):.2f}")
        low = [r for r in in_scope_b if r["name_coverage"] is not None and r["name_coverage"] < 0.5]
        if low:
            print(f"  ⚠️ {len(low)} câu TRONG phạm vi DB nhưng coverage < 0.5 (bị chấm confident=False oan, cần xem):")
            for r in low:
                print(f"     {r['id']}: topic='{r['topic']}' -> top='{r['top_name']}' cov={r['name_coverage']:.2f}")

    gaps = [r["gap_ratio"] for r in in_scope_b if r["gap_ratio"] is not None]
    if gaps:
        print(f"  gap_ratio (khi có >=2 thủ tục ứng viên), n={len(gaps)}: "
              f"min={min(gaps):.1%} median={statistics.median(gaps):.1%} max={max(gaps):.1%}")
        under_20 = sum(1 for g in gaps if g < 0.20)
        print(f"  -> {under_20}/{len(gaps)} câu có gap < 20% (sẽ hiện gợi ý 'Có thể bạn quan tâm')")
        for r in sorted((r for r in in_scope_b if r["gap_ratio"] is not None),
                         key=lambda r: r["gap_ratio"])[:8]:
            print(f"     {r['id']} '{r['topic']}' gap={r['gap_ratio']:.1%} top='{r['top_name']}'")

    print(f"\nNgoài phạm vi 70 thủ tục ({len(out_scope_b)} câu) — kỳ vọng confident=False, KHÔNG tính vào calibrate:")
    print(f"  confident=True dù ngoài phạm vi (đáng ngờ, nên xem): "
          f"{pct(sum(r['confident'] for r in out_scope_b), len(out_scope_b))}")
    false_pos = [r for r in out_scope_b if r["confident"]]
    for r in false_pos:
        print(f"     {r['id']}: topic='{r['topic']}' -> top='{r['top_name']}' cov={r['name_coverage']:.2f} (SAI DƯƠNG)")

    # --- Lượt A: keyword = câu hỏi thô (định lượng khoảng cách cần LLM1 lấp) ---
    rows_a = run(conn, items, lambda i: i["turns"][-1], "A_raw")
    in_scope_a = [r for r in rows_a if topic_cov[r["topic"]] >= 0.6]
    print(f"\n=== LƯỢT A — keyword=câu hỏi thô (KHÔNG dùng để calibrate, chỉ định lượng) ===")
    print(f"Trong phạm vi 70 thủ tục ({len(in_scope_a)} câu):")
    print(f"  confident=True : {pct(sum(r['confident'] for r in in_scope_a), len(in_scope_a))}")
    a_single = [r for r in in_scope_a if r["kind"] == "single"]
    a_follow = [r for r in in_scope_a if r["kind"] == "followup"]
    print(f"    câu đơn     : {pct(sum(r['confident'] for r in a_single), len(a_single))}")
    print(f"    câu nối tiếp: {pct(sum(r['confident'] for r in a_follow), len(a_follow))}"
          " (câu cuối cùng thường thiếu ngữ cảnh, ví dụ 'cái đó nộp ở đâu' -> đúng là sẽ trượt)")
    print(f"\n=> Chênh lệch confident B ({pct(sum(r['confident'] for r in in_scope_b), len(in_scope_b))}) "
          f"vs A ({pct(sum(r['confident'] for r in in_scope_a), len(in_scope_a))}) "
          f"= giá trị thật mà extractor.py (LLM1) cần tạo ra.")


if __name__ == "__main__":
    main()

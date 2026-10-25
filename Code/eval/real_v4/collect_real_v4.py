"""Bộ TEST real_v4 cho System 3 (25/10/2026): bộ test thứ hai, cho vòng cải thiện trước khi nộp bài báo 1.

Vì sao: real_v2 đã mở (kết quả ngày 25/10), từ nay nó là DEV cùng real_v1. Muốn báo số "sau cải thiện" thì phải có bộ test mới, khoá
TRƯỚC mọi thay đổi code của vòng này.

Nguồn: phần còn lại của cùng pool sạch (research/clarify/pool_real_v1.jsonl, 1.490 câu, đã che thông tin cá nhân). Loại:
  - câu đã vào real_v1 / real_v2 (theo `source`) và 4 dòng đầu pool (đã thấy khi xem định dạng);
  - câu gần trùng một câu real_v1 / real_v2 (Jaccard tập chữ bỏ dấu >= 0,6, cùng ngưỡng eval/hard/metrics.py REAL_V2_NEAR_DUP).
Tầng "chude" đã hết (còn 1 câu), nên chỉ có một tầng ngẫu nhiên = phân phối ngoài đời.
Toàn bộ phần còn lại được XÁO một lần theo SEED rồi đánh số; bộ test = N câu ĐẦU của thứ tự này, N do người gán nhãn chọn theo sức
gán (quyết định trước khi chạy hệ thống, không nhìn kết quả). Người sửa hệ thống (Claude) KHÔNG đọc câu hỏi real_v4: script chỉ in số đếm.

    python run_server.py eval/real_v4/collect_real_v4.py      # ghi eval/real_v4/cases_real_v4.json (cùng SEED -> cùng tệp)
"""
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
POOL = os.path.join(ROOT, "research", "clarify", "pool_real_v1.jsonl")
USED = [os.path.join(ROOT, "eval", "real_v1", "cases_real_v1.json"), os.path.join(ROOT, "eval", "real_v2", "cases_real_v2.json")]
OUT = os.path.join(HERE, "cases_real_v4.json")
sys.path[:0] = [ROOT, os.path.join(ROOT, "eval", "real_v1")]
from collect_real_v1 import fold  # noqa: E402

SEED = 20261026
SEEN_BY_DEV = 4
NEAR_DUP = 0.6
COLLECTED_ON = "2026-10-25"
COLLECTOR = "script collect_real_v4.py (pool của real_v1)"


def words(t: str) -> set:
    return set(re.findall(r"\w+", fold(t)))


def main():
    pool = [json.loads(l) for l in open(POOL, encoding="utf-8")]
    used = [c for f in USED for c in json.load(open(f, encoding="utf-8"))]
    used_src = {c["source"] for c in used}
    rest = [p for i, p in enumerate(pool) if i >= SEEN_BY_DEV and p["source"] not in used_src]
    used_w = [words(c["text"]) for c in used]
    keep, dup = [], 0
    for p in rest:
        w = words(p["text"])
        if any(len(w & u) / max(len(w | u), 1) >= NEAR_DUP for u in used_w):
            dup += 1
            continue
        keep.append(p)
    random.Random(SEED).shuffle(keep)
    out = [{"id": f"real_v4-{n:03d}", "text": p["text"], "source": p["source"], "collected_on": COLLECTED_ON, "collector": COLLECTOR,
            "stratum": "random", "seed": SEED, "order": n} for n, p in enumerate(keep, 1)]
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pool {len(pool)}; đã dùng (real_v1 + real_v2) {len(used_src)}; đã thấy {SEEN_BY_DEV}; còn {len(rest)}; gần trùng bỏ {dup}; "
          f"ghi {len(out)} câu theo thứ tự xáo (SEED {SEED}) -> {OUT}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

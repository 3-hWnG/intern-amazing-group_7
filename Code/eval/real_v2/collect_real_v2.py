"""Bộ TEST real_v2 cho System 3 (24/10/2026). Chỉ câu hỏi, CHƯA có nhãn, chưa chạy hệ thống.

Vì sao có bộ này: real_v1 (282 câu) đã chạy một lần và đã xem từng câu sai (eval/saved_results/2026-10-22_real_v1/report.md), nên từ 24/10
real_v1 chỉ còn là bộ DEV để sửa luật. Số báo cáo cuối (và cho bài báo) lấy trên real_v2: câu hệ thống và người sửa luật chưa dùng để sửa.

Nguồn: cùng pool sạch của real_v1 (research/clarify/pool_real_v1.jsonl, 1.490 câu, đã che CCCD/SĐT/email/tên; có trong git), cùng cách lọc.
Loại thêm:
  - 300 câu đã vào real_v1 (so theo `source`);
  - 4 dòng đầu của pool (dvc row0, row2, row3, row4): người sửa luật đã thấy chúng ngày 24/10 khi xem thử định dạng pool.
Hai tầng như real_v1, cùng từ khoá KEYWORDS (lấy nguyên từ collect_real_v1.py, viết từ 20/10):
  random : ngẫu nhiên trong phần còn lại      -> phân phối ngoài đời (đo từ chối đúng)
  chude  : ngẫu nhiên trong các câu có từ khoá chủ đề cấp xã -> đo top-1 / top-3 (lấy nhiều hơn real_v1 để có thêm câu `answer`)
SEED khác real_v1. Không chọn câu theo nội dung nào khác.

    python run_server.py eval/real_v2/collect_real_v2.py      # ghi eval/real_v2/cases_real_v2.json (cùng SEED -> cùng tệp)
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
POOL = os.path.join(ROOT, "research", "clarify", "pool_real_v1.jsonl")
V1 = os.path.join(ROOT, "eval", "real_v1", "cases_real_v1.json")
OUT = os.path.join(HERE, "cases_real_v2.json")
sys.path[:0] = [ROOT, os.path.join(ROOT, "eval", "real_v1")]
from collect_real_v1 import KEYWORDS, fold  # noqa: E402

SEED = 20261024
N_RANDOM, N_TOPIC = 120, 280
SEEN_BY_DEV = 4          # 4 dòng đầu pool: đã hiện ra khi xem thử định dạng (24/10)
COLLECTED_ON = "2026-10-24"
COLLECTOR = "script collect_real_v2.py (pool của real_v1)"


def main():
    pool = [json.loads(l) for l in open(POOL, encoding="utf-8")]
    v1 = {c["source"] for c in json.load(open(V1, encoding="utf-8"))}
    rest = [p for i, p in enumerate(pool) if i >= SEEN_BY_DEV and p["source"] not in v1]
    rnd = random.Random(SEED)
    picked = rnd.sample(rest, N_RANDOM)
    for p in picked:
        p["stratum"] = "random"
    taken = {p["source"] for p in picked}
    topical = [p for p in rest if p["source"] not in taken and any(w in fold(p["text"]) for w in KEYWORDS)]
    t = rnd.sample(topical, min(N_TOPIC, len(topical)))
    for p in t:
        p["stratum"] = "chude"
    out = [{"id": f"real_v2-{n:03d}", "text": p["text"], "source": p["source"], "collected_on": COLLECTED_ON,
            "collector": COLLECTOR, "stratum": p["stratum"], "seed": SEED} for n, p in enumerate(picked + t, 1)]
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pool {len(pool)}; trong real_v1 {len(v1)}; đã thấy {SEEN_BY_DEV}; còn {len(rest)}; chude khả dụng {len(topical)}")
    print(f"ghi {len(out)} câu ({N_RANDOM} random + {len(t)} chude) -> {OUT}")


if __name__ == "__main__":
    main()

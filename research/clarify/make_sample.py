"""Chọn mẫu để gán nhãn từ pool_run.jsonl (đã chạy run_pool.py): 250 câu Cổng Bình Định <= 25 chữ, 80 câu Zalo, 60 câu Bộ Công an <= 50 chữ;
chia tune (60%) / test (40%) theo băm mã câu. -> sample.jsonl. Nhãn gán tay bằng show.py + label.py, bản lưu git: real_questions_labeled.jsonl."""
import hashlib, json, random
R = [json.loads(l) for l in open("research/clarify/pool_run.jsonl", encoding="utf-8")]
rng = random.Random(2026)
pick = lambda xs, n: rng.sample(xs, min(n, len(xs)))
S = (pick([r for r in R if r["src"] == "dvc" and len(r["q"].split()) <= 25], 250) + pick([r for r in R if r["src"] == "zalo"], 80)
     + pick([r for r in R if r["src"] in ("mps", "mpsfaq") and len(r["q"].split()) <= 50], 60))
with open("research/clarify/sample.jsonl", "w", encoding="utf-8") as f:
    for i, x in enumerate(S):
        x["split"] = "tune" if int(hashlib.md5(x["id"].encode()).hexdigest(), 16) % 10 < 6 else "test"
        x["n"] = i
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print(len(S))

"""Gom câu hỏi THẬT của người dân từ các bộ tải về (research/clarify/raw/, không commit) thành research/clarify/pool.jsonl.
Chỉ giữ câu hỏi (bỏ tên người hỏi, câu trả lời, người trả lời); che CCCD/SĐT; bỏ trùng.
Nguồn (Hugging Face, tải 18/10/2026):
  dvc    hieunguyen1053/dichvucong_faqs (config hoi-dap): hỏi đáp Cổng dịch vụ công Bình Định, 1.074 câu
  mps    doanhieung/vn-mps-public-service-qa: hỏi đáp Cổng dịch vụ công Bộ Công an, 809 câu
  mpsfaq doanhieung/vn-mps-public-service-faq: câu hỏi thường gặp Bộ Công an, 17 câu
  zalo   GreenNode/zalo-ai-legal-text-retrieval-vn (queries.jsonl, MIT): câu hỏi pháp luật của người dân, 3.298 câu
    python run_server.py research/clarify/build_pool.py"""
import collections, csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "server"))
from policy import mask_pii  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.join(HERE, "raw")
pool = [("dvc", json.loads(l)["question"]) for l in open(os.path.join(R, "dvc_hoi_dap_questions.jsonl"), encoding="utf-8")]
pool += [("mps", r["question"]) for r in csv.DictReader(open(os.path.join(R, "mps_qa.csv"), encoding="utf-8"))]
for r in csv.DictReader(open(os.path.join(R, "mps_faq.csv"), encoding="utf-8")):
    q = next((v for k, v in r.items() if k and "question" in k.lower()), "")
    pool.append(("mpsfaq", q))
pool += [("zalo", json.loads(l)["text"]) for l in open(os.path.join(R, "zalo_queries.jsonl"), encoding="utf-8")]
seen, out = set(), []
for src, q in pool:
    q = mask_pii(" ".join((q or "").split()))
    if len(q) < 8 or q.lower() in seen:
        continue
    seen.add(q.lower())
    out.append({"id": f"{src}-{len(out):04d}", "src": src, "q": q})
with open(os.path.join(HERE, "pool.jsonl"), "w", encoding="utf-8") as f:
    for x in out:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
c = collections.Counter(x["src"] for x in out)
print(dict(c))
for s in c:
    L = collections.Counter(min(len(x["q"].split()) // 10 * 10, 60) for x in out if x["src"] == s)
    print(s, "số chữ 0-9,10-19,…,60+:", [L[k] for k in range(0, 70, 10)])

"""Dựng lại văn bản câu hỏi của ba bộ đánh giá từ hai dataset công khai trên Hugging Face (bản công khai không kèm văn bản câu hỏi).

labels/<bộ>.jsonl có `source` dạng "hf:<dataset>[/<config>]#row<N>": N là chỉ số dòng trong split `train`, theo thứ tự gốc của dataset
(đã kiểm ngày 25/10/2026: thứ tự trùng với bản nhóm tải về, 1.074 và 809 dòng). Văn bản được làm sạch bằng `clean()` của
eval/real_v1/collect_real_v1.py (che số điện thoại, giấy tờ, email, tên sau "Ông/Bà/Anh/Chị...", tự giới thiệu tên). Bản công khai đã bỏ
danh sách 17 họ tên che tay, nên các tên đó (vốn có trong dataset gốc) không được che.

    python run_server.py eval/rebuild_questions.py        # ghi eval/real_v1|v2|v4/cases_real_v*_labeled.json (đúng chỗ eval/hard/dev.py đọc)
Cần mạng. Dùng API datasets-server của Hugging Face, không cần thư viện `datasets`.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(HERE, "real_v1"), os.path.join(ROOT, "server")]
from collect_real_v1 import clean  # noqa: E402

API = "https://datasets-server.huggingface.co/rows"
DATASETS = {"hieunguyen1053/dichvucong_faqs/hoi-dap": ("hieunguyen1053/dichvucong_faqs", "hoi-dap"),
            "doanhieung/vn-mps-public-service-qa": ("doanhieung/vn-mps-public-service-qa", "default")}
_cache: dict = {}


def row(source: str) -> str:
    name, n = source[3:].split("#row")
    ds, cfg = DATASETS[name]
    n = int(n)
    start = n - n % 100
    key = (ds, cfg, start)
    if key not in _cache:
        q = urllib.parse.urlencode({"dataset": ds, "config": cfg, "split": "train", "offset": start, "length": 100})
        rows = json.load(urllib.request.urlopen(f"{API}?{q}", timeout=60))["rows"]
        _cache[key] = {r["row_idx"]: r["row"]["question"] for r in rows}
    return _cache[key][n]


def main():
    for name, out in (("dev_real_v1", "real_v1/cases_real_v1_labeled.json"), ("test1_real_v2", "real_v2/cases_real_v2_labeled.json"),
                      ("test2_real_v4", "real_v4/cases_real_v4_labeled.json")):
        cases = []
        for line in open(os.path.join(ROOT, "labels", name + ".jsonl"), encoding="utf-8"):
            c = json.loads(line)
            cases.append({"id": c["id"], "q": clean(row(c["source"])), "beh": c["beh"], "expect_ids": c["expect_ids"], "fields": [],
                          "stratum": c["stratum"], "source": c["source"]})
        json.dump(cases, open(os.path.join(HERE, out), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, len(cases))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

"""Tải dữ liệu THẬT cho 3 lĩnh vực mềm (Y tế, Giáo dục, Du lịch) về raw/ (không đưa vào git). Chạy lại được; tệp đã có thì bỏ qua.

    python system4/eval/real_domains/fetch.py [--force]

Nguồn (chi tiết, giấy phép: SOURCES.md). Chỉ GET, chậm (2 giây giữa hai request tới cùng một trang), User-Agent định danh dự án.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
UA = "Instant-Specialist-student-project/1.0 (FPT University intern team; research use)"
WIKI = "https://vi.wikipedia.org/w/api.php"

WIKI_TABLES = {   # tệp raw -> tiêu đề trang Wikipedia tiếng Việt (lấy HTML đã dựng + revid)
    "wiki_benh_vien_hcm.json": "Danh sách bệnh viện tại Thành phố Hồ Chí Minh",
    "wiki_truong_dai_hoc.json": "Danh sách trường đại học, học viện và cao đẳng tại Việt Nam",
    "wiki_di_tich_dac_biet.json": "Di tích quốc gia đặc biệt (Việt Nam)",
}
DESTINATIONS = ["Hội An", "Vịnh Hạ Long", "Vườn quốc gia Phong Nha – Kẻ Bàng", "Sa Pa", "Đà Lạt", "Phú Quốc"]
LAW_GD = "https://pbgdpl.cantho.gov.vn/attachment/284"   # Luật Giáo dục 2019 (43/2019/QH14), toàn văn HTML trên cổng PBGDPL TP. Cần Thơ
MEDQA = "hungnm/vietnamese-medical-qa"
MEDQA_PAGES = 12   # 12 trang × 100 dòng, rải đều trên 9.335 dòng -> build.py chọn 300


def get(url: str, params: dict | None = None, timeout: int = 60) -> bytes:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:   # Wikipedia / HF giới hạn tần suất: đợi rồi thử lại
                time.sleep(15 * (attempt + 1))
                continue
            raise
    raise RuntimeError("không tải được " + url)


def save(name: str, data) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print("  ->", name)


def main(force: bool) -> None:
    have = lambda n: (RAW / n).exists() and not force
    for name, title in WIKI_TABLES.items():
        if have(name):
            continue
        print("Wikipedia:", title)
        p = json.loads(get(WIKI, {"action": "parse", "page": title, "prop": "text|revid", "format": "json", "formatversion": 2}))["parse"]
        save(name, {"title": p["title"], "revid": p["revid"], "html": p["text"], "retrieved": time.strftime("%Y-%m-%d")})
        time.sleep(2)
    if not have("wiki_diem_den.json"):
        out = []
        for title in DESTINATIONS:
            print("Wikipedia (bài):", title)
            q = json.loads(get(WIKI, {"action": "query", "prop": "extracts|revisions", "rvprop": "ids", "explaintext": 1,
                                      "exsectionformat": "wiki", "titles": title, "redirects": 1, "format": "json", "formatversion": 2}))
            pg = q["query"]["pages"][0]
            out.append({"title": pg["title"], "revid": pg["revisions"][0]["revid"], "text": pg["extract"]})
            time.sleep(2)
        save("wiki_diem_den.json", {"pages": out, "retrieved": time.strftime("%Y-%m-%d")})
    if not have("luat_giao_duc_2019.json"):
        print("Luật Giáo dục 2019:", LAW_GD)
        save("luat_giao_duc_2019.json", {"url": LAW_GD, "html": get(LAW_GD).decode("utf-8", "replace"), "retrieved": time.strftime("%Y-%m-%d")})
    if not have("medqa_rows.json"):
        print("Hugging Face:", MEDQA)
        n = json.loads(get("https://datasets-server.huggingface.co/size", {"dataset": MEDQA}))["size"]["dataset"]["num_rows"]
        rows = []
        for k in range(MEDQA_PAGES):
            off = k * (n - 100) // (MEDQA_PAGES - 1)
            r = json.loads(get("https://datasets-server.huggingface.co/rows",
                               {"dataset": MEDQA, "config": "default", "split": "train", "offset": off, "length": 100}))
            rows += [{"row_idx": x["row_idx"], **x["row"]} for x in r["rows"]]
            time.sleep(1)
        save("medqa_rows.json", {"dataset": MEDQA, "num_rows": n, "rows": rows, "retrieved": time.strftime("%Y-%m-%d")})
    print("xong:", sorted(p.name for p in RAW.glob("*.json")))


if __name__ == "__main__":
    main("--force" in sys.argv)

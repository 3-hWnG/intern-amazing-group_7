"""Thu câu hỏi THẬT cho bộ real_v1 (Ngày 1 của docs/eval 3 ngày/VIEC_EVAL_3_NGAY_2026-10-21.md). Chỉ câu hỏi, CHƯA có nhãn, chưa chạy hệ thống.

Nguồn: câu hỏi người dân trên Hugging Face, đã tải vào research/clarify/raw/ (không vào git):
  dvc  hieunguyen1053/dichvucong_faqs (hoi-dap)           hỏi đáp Cổng dịch vụ công Bình Định
  mps  doanhieung/vn-mps-public-service-qa                 hỏi đáp Cổng dịch vụ công Bộ Công an
Bỏ Zalo: tập truy hồi văn bản pháp luật, trong 80 câu đã gán nhãn trước đó chỉ 1 câu là thủ tục cấp xã.
Giấy phép hai tập không ghi rõ -> chỉ dùng đánh giá nội bộ, không phát hành lại bộ câu hỏi.

Hai tầng (báo cáo riêng, không gộp):
  random  : ngẫu nhiên từ toàn pool, đại diện cho phân phối ngoài đời (phần lớn ngoài phạm vi) -> đo từ chối đúng
  chude   : ngẫu nhiên trong các câu chứa từ khoá chủ đề cấp xã -> đo top-1 / top-3
Từ khoá chủ đề (KEYWORDS) lấy từ tên nhóm thủ tục (cột `domain`) của DB bản 3 trong phạm vi cấp xã, viết TRƯỚC khi xem kết quả hệ thống.
Không chọn câu theo nội dung nào khác. Loại: 266 câu đã dùng để chọn luật M1/M2 (research/clarify/real_questions_labeled.jsonl),
câu trùng, câu dưới 4 chữ, dòng chỉ là lời chào.

    python run_server.py eval/real_v1/collect_real_v1.py          # ghi eval/real_v1/cases_real_v1.json (cùng SEED -> cùng tệp)
"""
import json
import os
import random
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "research", "clarify", "raw")
USED = os.path.join(ROOT, "research", "clarify", "real_questions_labeled.jsonl")
OUT = os.path.join(HERE, "cases_real_v1.json")
POOL_OUT = os.path.join(ROOT, "research", "clarify", "pool_real_v1.jsonl")
sys.path.insert(0, os.path.join(ROOT, "server"))
from policy import mask_pii  # noqa: E402

SEED = 20261021
N_RANDOM, N_TOPIC = 120, 180
COLLECTED_ON = "2026-10-20"
COLLECTOR = "script collect_real_v1.py (Hugging Face)"
SOURCES = {"dvc": "hf:hieunguyen1053/dichvucong_faqs/hoi-dap", "mps": "hf:doanhieung/vn-mps-public-service-qa"}

# Tên nhóm thủ tục cấp xã trong DB bản 3 (domain): Hộ tịch, Người có công, Đất đai, Chứng thực, Đăng ký quản lý cư trú, Cấp quản lý căn cước,
# Bảo trợ xã hội, Trẻ em, Nuôi con nuôi, BHXH / BHYT, Việc làm, Hợp tác xã, Hòa giải ở cơ sở, Nhà ở, Giảm nghèo, Tín ngưỡng tôn giáo,
# Giáo dục mầm non, hộ kinh doanh, Lý lịch tư pháp, Định danh điện tử. Khớp trên chữ đã bỏ dấu, chữ thường.
KEYWORDS = [
    "khai sinh", "khai tu", "ket hon", "ho tich", "nhan cha", "nhan con", "giam ho", "thay doi cai chinh",
    "nguoi co cong", "liet si", "thuong binh", "benh binh", "anh hung", "tro cap uu dai",
    "dat dai", "so do", "so hong", "giay chung nhan quyen su dung dat", "chuyen muc dich", "tach thua", "thua ke dat",
    "chung thuc", "sao y", "chu ky", "tam tru", "thuong tru", "cu tru", "dang ky tam tru", "xoa dang ky",
    "can cuoc", "cccd", "chung minh nhan dan", "dinh danh dien tu", "vneid",
    "bao tro xa hoi", "tro cap xa hoi", "nguoi khuyet tat", "tre em", "nuoi con nuoi", "ho ngheo", "can ngheo",
    "bao hiem xa hoi", "bhxh", "bao hiem y te", "bhyt", "that nghiep", "viec lam",
    "hop tac xa", "ho kinh doanh", "hoa giai", "nha o", "ly lich tu phap", "ton giao", "tin nguong", "mam non",
]
GREETING = re.compile(r"^(kinh gui|xin chao|chao)\b.{0,70}$")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
NAME = re.compile(r"\b([Ôô]ng|bà|[Aa]nh|[Cc]hị|[Cc]ô|[Cc]hú)\s+((?:[A-ZÀ-Ỵ][a-zà-ỹ]+)(?:\s+[A-ZÀ-Ỵ][a-zà-ỹ]+){0,3})")
# "Tôi là / tên là / tên / Bạn đọc + 2-4 chữ hoa" = tự giới thiệu tên (chạy trước NAME)
INTRO = re.compile(r"\b(Tôi là|tôi là|Cháu là|cháu là|Em là|em là|Mình là|tên là|tên|Bạn đọc)\s+(?:[A-ZÀ-Ỵ][a-zà-ỹ]+\b\s*){2,4}")
# Tên người còn sót sau khi đọc quét tay 300 câu (chỉ che chữ, không chọn câu). Chỉ che tên người, không che tên đường / trường / địa danh.
MANUAL_NAMES = []   # bản công khai: đã xoá 17 họ tên người thật tìm được khi đọc tay (không công bố)


def fold(s: str) -> str:
    sys.path.insert(0, ROOT)
    from data.textutil import fold as f
    return f(s)


def clean(q: str) -> str:
    q = mask_pii(" ".join((q or "").split()))
    q = EMAIL.sub("[EMAIL]", q)
    q = INTRO.sub(lambda m: m.group(1) + " [TÊN] ", q)
    q = NAME.sub(lambda m: m.group(1) + " [TÊN]", q)
    for n in MANUAL_NAMES:
        q = q.replace(n, "[TÊN]")
    return q


def load_pool():
    import csv
    rows = []
    for i, l in enumerate(open(os.path.join(RAW, "dvc_hoi_dap_questions.jsonl"), encoding="utf-8")):
        rows.append(("dvc", i, json.loads(l)["question"]))
    for i, r in enumerate(csv.DictReader(open(os.path.join(RAW, "mps_qa.csv"), encoding="utf-8"))):
        rows.append(("mps", i, r["question"]))
    return rows


def main():
    used = {fold(" ".join(json.loads(l)["q"].split())) for l in open(USED, encoding="utf-8") if json.loads(l)["q"]}
    seen, pool, drop = set(), [], {"đã dùng": 0, "trùng": 0, "ngắn": 0, "chào": 0}
    for src, idx, raw in load_pool():
        text = clean(raw)
        k = fold(text)
        if k in used:
            drop["đã dùng"] += 1
        elif k in seen:
            drop["trùng"] += 1
        elif len(text.split()) < 4:
            drop["ngắn"] += 1
        elif GREETING.match(k):
            drop["chào"] += 1
        else:
            seen.add(k)
            pool.append({"src": src, "row": idx, "text": text, "fold": k})
    with open(POOL_OUT, "w", encoding="utf-8") as f:   # pool sạch để xem lại / kiểm; nằm cạnh raw/, không vào git
        for p in pool:
            f.write(json.dumps({"source": f"{SOURCES[p['src']]}#row{p['row']}", "text": p["text"]}, ensure_ascii=False) + "\n")
    rnd = random.Random(SEED)
    picked = rnd.sample(pool, N_RANDOM)
    for p in picked:
        p["stratum"] = "random"
    taken = {id(p) for p in picked}
    topical = [p for p in pool if id(p) not in taken and any(w in p["fold"] for w in KEYWORDS)]
    t = rnd.sample(topical, min(N_TOPIC, len(topical)))
    for p in t:
        p["stratum"] = "chude"
    out = []
    for n, p in enumerate(picked + t, 1):
        out.append({"id": f"real_v1-{n:03d}", "text": p["text"], "source": f"{SOURCES[p['src']]}#row{p['row']}", "collected_on": COLLECTED_ON,
                    "collector": COLLECTOR, "stratum": p["stratum"], "seed": SEED})
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pool sạch {len(pool)} (loại {drop}); chude khả dụng {len(topical)}")
    print(f"ghi {len(out)} câu -> {OUT}")


if __name__ == "__main__":
    main()

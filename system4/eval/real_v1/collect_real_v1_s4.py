"""Thu câu hỏi THẬT cho bộ real_v1 của System 4 (Friendly). Chỉ câu hỏi, chưa nhãn, chưa chạy hệ thống.

    python run_server.py system4/eval/real_v1/collect_real_v1_s4.py     # ghi system4/eval/real_v1/cases_real_v1_s4.json (cùng SEED -> cùng tệp)

Hai phần ở đây (phần 3 soạn riêng, xem docs/eval 3 ngày/REAL_V1_S4_BANG_FORM.md):
  du_lich_vqd   UIT-ViQuAD2.0 (taidng/UIT-ViQuAD2.0): câu hỏi do người viết trên bài Wikipedia tiếng Việt. Chỉ có bài
                "Vườn quốc gia Phong Nha - Kẻ Bàng" trùng với 6 bài của dữ liệu Du lịch (du_lich_diem_den.md), nên mọi câu từ một bài.
                Có hai loại: có đáp án (is_impossible=False, đáp án gốc ghi ở source_gold) và KHÔNG có đáp án trong bài (True, để thử "không bịa").
                Lưu ý: bài trong ViQuAD là bản Wikipedia cũ (~2020), dữ liệu hệ thống là bản tải tháng 10/2026; đáp án gốc có thể đã đổi.
  y_te_real     hungnm/vietnamese-medical-qa (Apache-2.0): câu hỏi thật của người dân gửi bác sĩ. Loại 300 câu mà dữ liệu Y tế của hệ thống
                đã nạp (system4/eval/real_domains/data/y_te_hoi_dap_bac_si.md, "Câu số N"). Không có đáp án trong dữ liệu của hệ thống:
                chỉ chấm được hành vi (không chẩn đoán bừa, khuyên đi khám), không chấm đúng/sai nội dung.
Che tên người / SĐT / email bằng eval/collect_real_v1.clean(). Câu giữ nguyên chữ người viết (ViQuAD) / người hỏi (Y tế), bỏ không sửa lỗi.
"""
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RAW = os.path.join(ROOT, "research", "s4_raw")
MD = os.path.join(os.path.dirname(HERE), "real_domains", "data", "y_te_hoi_dap_bac_si.md")
OUT = os.path.join(HERE, "cases_real_v1_s4.json")
sys.path.insert(0, os.path.join(ROOT, "eval", "real_v1"))
import collect_real_v1 as base  # noqa: E402  (che PII, chạy được khi khởi động bằng run_server.py)

SEED = 20261021
N_VQD_ANSWER, N_VQD_NOANS, N_MED = 50, 25, 85
COLLECTED_ON = "2026-10-20"
COLLECTOR = "script collect_real_v1_s4.py (Hugging Face)"
TITLE = "Vườn quốc gia Phong Nha - Kẻ Bàng"


def viquad():
    import pyarrow.parquet as pq
    rows, seen = [], set()
    for sp in ("train", "validation", "test"):
        for i, r in enumerate(pq.read_table(os.path.join(RAW, f"viquad_{sp}.parquet")).to_pylist()):
            if r["title"] != TITLE:
                continue
            k = r["question"].strip().lower()
            if k in seen:
                continue
            seen.add(k)
            ans = r["answers"]
            gold = list(ans["text"]) if isinstance(ans, dict) else []
            rows.append({"text": base.clean(r["question"]), "source": f"hf:taidng/UIT-ViQuAD2.0/{sp}#{r['id']}", "impossible": bool(r["is_impossible"]),
                         "gold": gold})
    return rows


def medical():
    import pyarrow.parquet as pq
    used = {int(n) for n in re.findall(r"Câu số (\d+) trong bộ dữ liệu gốc", open(MD, encoding="utf-8").read())}
    rows, seen = [], set()
    for i, r in enumerate(pq.read_table(os.path.join(RAW, "med.parquet")).to_pylist()):
        q = " ".join((r["question"] or "").split())
        k = q.lower()[:80]
        if i in used or len(q) < 30 or len(q) > 700 or k in seen:
            continue
        seen.add(k)
        rows.append({"text": base.clean(q), "source": f"hf:hungnm/vietnamese-medical-qa#row{i}"})
    return rows, len(used)


def main():
    rnd = random.Random(SEED)
    v = viquad()
    ans = rnd.sample([r for r in v if not r["impossible"]], N_VQD_ANSWER)
    noans = rnd.sample([r for r in v if r["impossible"]], N_VQD_NOANS)
    med, n_used = medical()
    med = rnd.sample(med, N_MED)
    out = []
    for stratum, domain, items in (("du_lich_vqd", "du_lich", ans + noans), ("y_te_real", "y_te", med)):
        for p in items:
            n = len(out) + 1
            row = {"id": f"real_v1_s4-{n:03d}", "text": p["text"], "source": p["source"], "collected_on": COLLECTED_ON, "collector": COLLECTOR,
                   "stratum": stratum, "domain": domain, "seed": SEED}
            if stratum == "du_lich_vqd":
                row["source_gold"] = p["gold"]   # đáp án gốc của bộ dữ liệu (rỗng = câu không có đáp án trong bài)
            out.append(row)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ViQuAD Phong Nha: {len(v)} câu ({sum(1 for r in v if not r['impossible'])} có đáp án, {sum(1 for r in v if r['impossible'])} không); "
          f"Y tế khả dụng sau khi loại {n_used} câu đã nạp")
    print(f"ghi {len(out)} câu -> {OUT}")


if __name__ == "__main__":
    main()

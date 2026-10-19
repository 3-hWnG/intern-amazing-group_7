"""10 prompt mẫu mỗi lĩnh vực (Y tế, Giáo dục, Du lịch) + đáp án tra tay trong data/ — kiểm "trả lời được" KHÔNG cần AI:
đường nhanh trả lời thẳng (chứa đáp án), hoặc tìm kiếm thật (bge-m3 + reranker) đưa đoạn chứa đáp án vào các đoạn gửi AI.

    python run_server.py system4/eval/real_domains/showcase.py          # trên runtime thật (TẮT server trước) hoặc S4_RUNTIME_DIR tạm

Đây là bộ DEMO soạn lúc làm (đã nhìn dữ liệu), KHÔNG phải bộ mù: dùng để trình diễn, không để báo độ chính xác.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "server"))

# (prompt, các chữ phải có trong câu trả lời / đoạn tìm được — đủ MỘT nhóm là đạt; nhóm = mọi chữ trong nhóm đều có)
SHOWCASE = {
    "Y tế": [
        ("Bệnh viện Chợ Rẫy có bao nhiêu giường bệnh?", [["1.800"]]),
        ("Bệnh viện Nhân dân Gia Định trước đây còn có tên gọi là gì?", [["Nguyễn Văn Học"]]),
        ("Bệnh viện Từ Dũ được thành lập năm nào?", [["1943"]]),
        ("Website của Bệnh viện Nhân dân 115 là gì?", [["benhvien115.com.vn"]]),
        ("Bệnh viện Thống Nhất thuộc tuyến khám chữa bệnh BHYT nào?", [["Trung ương"]]),
        ("Đau bụng dưới kèm tiểu nhiều là dấu hiệu của bệnh gì?", [["tiểu nhiều"]]),
        ("Dùng chung bàn chải đánh răng với người nhiễm HIV có bị lây không?", [["HIV", "bàn chải"]]),
        ("Buổi tối hay bị nghẹt mũi, vướng họng là bị gì vậy bác sĩ?", [["nghẹt mũi", "vướng họng"]]),
        ("Bệnh Basedow có những biến chứng nguy hiểm nào?", [["Basedow"]]),
        ("Tôi đang đau ngực dữ dội và khó thở, tôi nên làm gì?", None),   # guardrail: khuyên gọi 115 / đến cơ sở y tế — kiểm bằng mắt
    ],
    "Giáo dục": [
        ("Trường Đại học Ngoại thương viết tắt là gì?", [["FTU"]]),
        ("Tên tiếng Anh của Trường Đại học Sư phạm Hà Nội là gì?", [["Hanoi National University of Education"]]),
        ("Trường Đại học FPT là trường công lập hay tư thục?", [["Tư thục"]]),
        ("Trường Đại học Công nghệ (UET) thuộc đại học nào?", [["Đại học Quốc gia Hà Nội"]]),
        ("Đại học Y Dược Thành phố Hồ Chí Minh trực thuộc cơ quan nào?", [["Bộ Y tế"]]),
        ("Luật Giáo dục 2019 có hiệu lực từ ngày nào?", [["01 tháng 7 năm 2020"]]),
        ("Theo Luật Giáo dục, mục tiêu giáo dục là gì?", [["Mục tiêu giáo dục nhằm phát triển toàn diện"]]),
        ("Hệ thống giáo dục quốc dân gồm những cấp học và trình độ đào tạo nào?", [["Giáo dục mầm non", "giáo dục phổ thông"]]),
        ("Cấp học nào là giáo dục bắt buộc theo Luật Giáo dục 2019?", [["bắt buộc"]]),
        ("Giáo viên tiểu học cần trình độ chuẩn được đào tạo là gì?", [["tiểu học", "cử nhân"]]),
    ],
    "Du lịch": [
        ("Đô thị cổ Hội An được công nhận là di tích quốc gia đặc biệt năm nào?", [["2009"]]),
        ("Địa đạo Củ Chi nằm ở đâu?", [["An Nhơn Tây"]]),
        ("Văn Miếu - Quốc Tử Giám thuộc hạng mục di tích nào?", [["kiến trúc nghệ thuật"]]),
        ("Yên Tử được xếp hạng di tích quốc gia đặc biệt vào đợt nào?", [["Đợt 3"]]),
        ("Khu đền tháp Mỹ Sơn nằm ở đâu?", [["Duy Phú"]]),
        ("Truyền thuyết về tên gọi Vịnh Hạ Long kể gì?", [["rồng"]]),
        ("Hang Sơn Đoòng được phát hiện như thế nào?", [["Sơn Đoòng", "Hồ Khanh"], ["Sơn Đoòng", "1991"]]),
        ("Khí hậu Đà Lạt như thế nào?", [["Đà Lạt", "nhiệt độ"]]),
        ("Chùa Cầu ở Hội An được xây dựng khi nào?", [["Chùa Cầu", "thế kỷ"]]),
        ("Hồ tiêu Phú Quốc có đặc điểm gì?", [["tiêu", "Phú Quốc"]]),
    ],
}


# Câu đường nhanh trả lời SAI / lệch đã thấy (19/10, trên chính dữ liệu này) — in ra để không ai hiểu nhầm là đã ổn, không tính điểm.
KNOWN_LIMITS = {
    "Du lịch": [
        ("Vịnh Hạ Long được UNESCO công nhận là di sản thiên nhiên thế giới năm nào?",
         "đường nhanh trả 'Năm xếp hạng: 2009' (năm xếp hạng di tích); đúng là 1994, có trong bài Wikipedia. Bảng có ghi chú 'UNESCO công nhận' nên không nhường."),
        ("Đô thị cổ Hội An được xếp hạng di tích quốc gia đặc biệt năm nào?",
         "đường nhanh trả 'Đợt xếp hạng: Đợt 1' (gợi ý 'xếp hạng' dài hơn 'năm'); hỏi 'được công nhận … năm nào' thì đúng 2009."),
    ],
}


def main() -> None:
    from system3.system4.server import db, fastpath, search
    dev = db.first_dev_id()
    tot = ok = 0
    for dname, items in SHOWCASE.items():
        dom = next(d for d in db.run("SELECT * FROM domains", many=True) if d["name"].casefold() == dname.casefold())
        ids = [d["id"] for d in db.active_datasets(dev, dom["id"], "dev")]
        print(f"\n=== {dname} (lĩnh vực {dom['id']}, bộ dữ liệu {ids})")
        for q, want in items:
            fp = fastpath.answer(ids, q, [], True, True)
            if fp["use"] and fp["result"]["kind"] == "answer":
                how, text = "đường nhanh", fp["result"]["content"]
            else:
                ev, _ = search.search(dev, q, ids)
                how, text = f"tìm kiếm ({len(ev)} đoạn)", "\n".join(e["title"] + "\n" + e["text"] for e in ev)
            hit = None if want is None else any(all(w.casefold() in text.casefold() for w in grp) for grp in want)
            if hit is not None:
                tot += 1
                ok += hit
            mark = "  ?" if hit is None else (" OK" if hit else " ✗ ")
            print(f"{mark} [{how}] {q}\n      → {' '.join(text.split())[:160]}")
    for dname, lims in KNOWN_LIMITS.items():
        for q, why in lims:
            print(f"  ! [giới hạn đã biết · {dname}] {q}\n      → {why}")
    print(f"\nTrả lời được (có đáp án trong câu trả lời đường nhanh / đoạn gửi AI): {ok}/{tot}")


if __name__ == "__main__":
    main()

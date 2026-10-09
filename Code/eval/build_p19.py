"""Phase 19: ca test cho 2 nhóm lỗi chung nhỏ: (G) "thời gian giải quyết / giải quyết trong bao lâu / bao lâu giải quyết" chỉ là processing_time (không kèm `steps`);
(H) "nếu X thì tôi cần làm gì" (điều kiện, không nêu mục) -> giấy tờ/hồ sơ (components) + điều kiện, không phải `steps`, không tách task thứ hai.
Câu tự nghĩ (KHÔNG lấy từ bộ mù). GHI THÊM idempotent vào cases.jsonl, split "dev", id tiền tố p19-. Gate DEV cũ loại id p16/p18/p19.
Chạy: python build_p19.py"""
import json, os
from build_p18 import T, C, KS, KH, KT, TT, TH, TACH, TV, XT, GHO, HERE, NAMES, exp_task

PT, COMP = ["processing_time"], ["components"]
ASST = "Mình đã trả lời theo dữ liệu của thủ tục. Bạn cần hỏi thêm gì không?"
DEV = [
    ("p19_G_time", C(["Tách hộ thời gian giải quyết như thế nào?"], [T([TACH], PT)])),
    ("p19_G_time", C(["khai tử thời gian giải quyết thế nào ạ"], [T([KT], PT)])),
    ("p19_G_time", C(["Đăng ký tạm trú giải quyết trong bao lâu?"], [T([TT], PT)])),
    ("p19_G_time", C(["Đăng ký kết hôn bao lâu giải quyết xong vậy?"], [T([KH], PT)])),
    ("p19_G_time", C(["Thời gian giải quyết việc đăng ký thường trú ra sao?"], [T([TH], PT)])),
    ("p19_G_time", C(["xóa đăng ký tạm trú thời gian giải quyết bao lâu"], [T([XT], PT)])),
    ("p19_G_time", C(["Đăng ký giám hộ thời gian giải quyết như thế nào, lệ phí bao nhiêu?"], [T([GHO], ["processing_time", "fees"])])),
    ("p19_G_time", C(["Tạm vắng: các bước thực hiện và thời gian giải quyết?"], [T([TV], ["steps", "processing_time"])])),
    ("p19_G_time", C(["Đăng ký tạm trú", "x", "thời gian giải quyết thế nào"], [T([TT], PT)])),
    ("p19_H_cond", C(["Nếu tôi đã ly hôn thì tôi cần làm gì để đăng ký kết hôn lại?"], [T([KH], COMP)])),
    ("p19_H_cond", C(["Nếu con tôi sinh ở nước ngoài thì tôi cần làm gì để đăng ký khai sinh?"], [T([KS], COMP)])),
    ("p19_H_cond", C(["Nếu tôi muốn tách hộ thì tôi cần làm gì?"], [T([TACH], COMP)])),
    ("p19_H_cond", C(["Nếu mẹ tôi mất thì tôi cần làm gì để đi khai tử?"], [T([KT], COMP)])),
    ("p19_H_cond", C(["Nếu tôi ở nhà thuê thì tôi cần làm gì để đăng ký tạm trú?"], [T([TT], COMP)])),
    ("p19_H_cond", C(["đăng ký giám hộ nếu người được giám hộ đang bệnh nặng thì cần làm gì"], [T([GHO], COMP)])),
    ("p19_H_cond", C(["Nếu tôi chuyển đi nơi khác trong vài tháng thì tôi cần làm gì để khai báo tạm vắng?"], [T([TV], COMP)])),
    ("p19_H_cond", C(["Khai sinh cho con", ASST, "Nếu cha mẹ chưa đăng ký kết hôn thì tôi cần làm gì?"], [T([KS], COMP)])),
]


def case(i, cat, c):
    for t in c["tasks"]:
        for p in t["ids"]:
            assert p in NAMES, (cat, p)
    turns = [{"role": "user" if k % 2 == 0 else "assistant", "text": t} for k, t in enumerate(c["turns"])]
    if len(turns) == 3 and turns[1]["text"] == "x":
        turns[1]["text"] = ASST
    exp = dict(tasks=[exp_task(t) for t in c["tasks"]], behavior="answer", must_say_not_published=False, missing_numeric_fields=[],
               free_text_in_source=False, citation_tokens=[], notes="p19")
    return dict(id=f"p19-{cat}-{i:02d}", category=cat, split="dev", source="p19-own", turns=turns, expected=exp)


def main():
    p = os.path.join(HERE, "cases.jsonl")
    keep = [l for l in open(p, encoding="utf-8") if not json.loads(l)["id"].startswith("p19-")]
    n, new = {}, []
    for cat, c in DEV:
        n[cat] = n.get(cat, 0) + 1
        new.append(case(n[cat], cat, c))
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(keep)
        for x in new:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print("cases.jsonl:", len(keep), "cũ +", len(new), "mới p19")


if __name__ == "__main__":
    main()

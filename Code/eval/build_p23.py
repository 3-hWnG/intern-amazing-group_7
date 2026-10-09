"""Phase 23: ca test cho 3 HỌ lỗi blackbox (nhóm báo). Câu TỰ NGHĨ, đa dạng nhiều lĩnh vực và nhiều kiểu nhiễu quanh mỗi ca người dùng đã thấy (KHÔNG lấy từ bộ mù):
  L1  tiền tố nhãn lượt + chữ lạ làm câu nối bị coi là độc lập/ngoài phạm vi ("Turn 2: vậy lệ phí thế nào?")
  L2  câu điều kiện "nếu X thì tôi cần làm gì" sinh task thừa (một chữ chung 'tang lễ' ~ 'lễ hội') và trả `steps` thay vì phần điều kiện/giấy tờ
  L3  gõ dính liền/teencode ("t muon đk kethon", "dangkykhaisinh")
GHI THÊM idempotent vào cases.jsonl (split "dev", id tiền tố p23-) và, với hội thoại nhiều lượt, vào cases_ctx.jsonl (split "ctx-p23"; run_ctx.py --split ctx-p23).
Gate DEV cũ (209 câu) loại id bắt đầu p16/p18/p19/p23. Chạy: python build_p23.py"""
import json, os
from build_p18 import T, C, KS, KH, KT, TT, TH, TACH, TV, XT, XH, CTCK, CTBS, GHO, NCM, GH, HKD, CCCD, LKS, LT, HERE, NAMES, exp_task

ASST = "Mình đã trả lời theo dữ liệu của thủ tục. Bạn cần hỏi thêm gì không?"
PT, FEE, COMP, ADDR = ["processing_time"], ["fees"], ["components"], ["address"]
TF = ["processing_time", "fees"]

L1 = [
    # nhãn lượt kiểu ca gốc, các lĩnh vực khác nhau
    C(["Tôi muốn đăng ký kết hôn.", "x", "Turn 2: Vậy thời gian giải quyết và lệ phí như thế nào?"], [T([KH], TF)]),
    C(["Turn 1: Tôi muốn đăng ký kết hôn.", "x", "Turn 2: Vậy thời gian giải quyết và lệ phí như thế nào?"], [T([KH], TF)]),
    C(["Mình cần đăng ký khai sinh cho bé", "x", "User: vậy lệ phí bao nhiêu?"], [T([KS], FEE)]),
    C(["đăng ký khai tử", "x", "Câu 2: còn thời gian giải quyết thì sao?"], [T([KT], PT)]),
    C(["Cho hỏi thủ tục tách hộ", "x", "Q: vậy nộp ở đâu?"], [T([TACH], ADDR)]),
    C(["Tôi muốn đăng ký tạm trú", "x", "Q2) vậy còn mất bao lâu?"], [T([TT], PT)]),
    C(["Đăng ký thường trú cho con", "x", "Lượt 2 - vậy lệ phí thế nào ạ?"], [T([TH], FEE)]),
    C(["khai báo tạm vắng", "x", "Hỏi: thế còn giấy tờ cần mang theo?"], [T([TV], COMP)]),
    C(["chứng thực chữ ký", "x", "Bạn: vậy phí bao nhiêu?"], [T([CTCK], FEE)]),
    C(["đăng ký giám hộ", "x", "[User] vậy thời gian giải quyết bao lâu?"], [T([GHO], PT)]),
    C(["đăng ký nhận cha mẹ con", "x", "(Turn 2) vậy lệ phí là bao nhiêu"], [T([NCM], FEE)]),
    C(["Gia hạn tạm trú", "x", "Câu hỏi 2: vậy hồ sơ gồm những gì?"], [T([GH], COMP)]),
    # đánh số, gạch đầu dòng, ngoặc kép, nhiều nhãn chồng
    C(["đăng ký khai sinh", "x", "2) vậy lệ phí?"], [T([KS], FEE)]),
    C(["đăng ký khai sinh", "x", "- vậy bao lâu có kết quả?"], [T([KS], PT)]),
    C(["đăng ký kết hôn", "x", "2. còn lệ phí thế nào?"], [T([KH], FEE)]),
    C(["xóa đăng ký thường trú", "x", "> vậy cần giấy tờ gì?"], [T([XH], COMP)]),
    C(["Tôi muốn khai tử cho ông nội", "x", "Turn 2: User: vậy mất bao lâu?"], [T([KT], PT)]),
    C(["tách hộ", "x", "“Vậy còn lệ phí thì sao?”"], [T([TACH], FEE)]),
    # nhãn + chữ lạ + lời đệm
    C(["Tôi muốn đăng ký kết hôn.", "x", "Turn 2: Vậy thời gian giải quyết thế nào hehe"], [T([KH], PT)]),
    C(["đăng ký tạm trú", "x", "Câu 2: 🙏 vậy lệ phí bao nhiêu nhé ạ"], [T([TT], FEE)]),
    C(["Đăng ký khai tử", "x", "Q: dạ cho em hỏi vậy mất bao nhiêu tiền"], [T([KT], FEE)]),
    C(["đăng ký khai sinh", "x", "User: vậy giấy tờ gì zzz"], [T([KS], COMP)]),
    # nhãn trong lịch sử hội thoại (cả lượt trợ lý) + 3 lượt
    C(["Turn 1: đăng ký thường trú", "Bot: " + ASST, "Turn 2: vậy phí bao nhiêu", "x", "Turn 3: còn thời gian giải quyết?"], [T([TH], PT)]),
    C(["Q: Tôi muốn xin chứng thực bản sao", "Assistant: " + ASST, "Q: thế phí bao nhiêu"], [T([CTBS], FEE)]),
    C(["User: đăng ký giám hộ", "x", "User: còn lệ phí và thời gian giải quyết?"], [T([GHO], TF)]),
    # câu đơn có nhãn (không có ngữ cảnh) vẫn phải ra đúng thủ tục
    C(["Turn 1: Đăng ký khai sinh cần giấy tờ gì?"], [T([KS], COMP)]),
    C(["Câu 1: đăng ký kết hôn mất bao lâu?"], [T([KH], PT)]),
    C(["Q: Khai tử lệ phí bao nhiêu?"], [T([KT], FEE)]),
    C(["User: tách hộ nộp ở đâu"], [T([TACH], ADDR)]),
]

L2 = [
    # ca người dùng thấy + biến thể: "nếu <việc chính + hoàn cảnh phụ> thì tôi cần làm gì": MỘT task, mục components (+ phần điều kiện), không `steps`
    C(["Nếu tôi đăng ký khai tử cho người đã chết nhưng người đó có hộ khẩu thường trú ở địa phương và được tổ chức tang lễ ở nơi khác thì tôi cần làm gì?"], [T([KT], COMP)]),
    C(["Nếu tôi đăng ký khai sinh cho con nhưng cha mẹ chưa đăng ký kết hôn và bé sinh ở nước ngoài thì tôi cần làm gì?"], [T([KS], COMP)]),
    C(["Nếu tôi đăng ký kết hôn mà một người đang ở nước ngoài và người kia là quân nhân thì cần làm gì?"], [T([KH], COMP)]),
    C(["Nếu tôi đăng ký tạm trú nhưng chủ nhà không đồng ý và tôi ở nhờ nhà người quen thì tôi cần làm gì?"], [T([TT], COMP)]),
    C(["Nếu tôi tách hộ nhưng nhà đang thế chấp ngân hàng và chủ hộ đi vắng thì tôi cần làm gì?"], [T([TACH], COMP)]),
    C(["Nếu tôi khai báo tạm vắng nhưng đi công tác ở nước ngoài và hộ vẫn ở nhà thì cần làm gì?"], [T([TV], COMP)]),
    C(["Nếu tôi xóa đăng ký thường trú cho người đã mất nhưng giấy báo tử đang ở nơi khác thì tôi cần làm gì?"], [T([XH], COMP)]),
    C(["Nếu tôi chứng thực chữ ký nhưng người ký không tự ký được và đi cùng người thân thì tôi cần làm gì?"], [T([CTCK], COMP)]),
    C(["Nếu mình đăng ký giám hộ cho người thân nhưng người đó đang điều trị bệnh viện ở tỉnh khác thì cần làm gì?"], [T([GHO], COMP)]),
    C(["Nếu tôi đăng ký khai tử cho ông nội, ông mất tại bệnh viện và gia đình tổ chức hỏa táng ở tỉnh khác thì tôi cần làm gì?"], [T([KT], COMP)]),
    C(["Nếu tôi đăng ký thường trú cho con nhưng bố mẹ đã ly hôn và con ở với mẹ thì tôi cần làm gì?"], [T([TH], COMP)]),
    C(["Nếu em đăng ký nhận cha mẹ con nhưng người cha đang ở nước ngoài và không về được thì em cần làm gì?"], [T([NCM], COMP)]),
    C(["neu toi dang ky khai tu cho nguoi da chet nhung to chuc tang le o noi khac thi can lam gi"], [T([KT], COMP)]),
    C(["Nếu tôi đăng ký khai sinh cho con nhưng bé chưa có tên, thì tôi cần làm gì?"], [T([KS], COMP)]),
    C(["Trường hợp tôi đăng ký tạm trú mà đang ở nhà thuê và hợp đồng thuê chưa công chứng thì tôi cần làm gì?"], [T([TT], COMP)]),
    C(["Turn 1: Nếu tôi đăng ký khai tử cho người đã chết nhưng người đó có hộ khẩu ở nơi khác thì cần làm gì?"], [T([KT], COMP)]),
    C(["Dạ cho em hỏi, nếu em đăng ký khai sinh cho cháu mà cháu sinh ở nhà và chưa có giấy chứng sinh thì em cần làm gì ạ? 🙏"], [T([KS], COMP)]),
    C(["Nếu tôi đăng ký khai tử cho người đã chết nhưng tổ chức tang lễ ở nơi khác thì phí bao nhiêu?"], [T([KT], FEE)]),
    C(["Nếu tôi tách hộ nhưng đang ở nhà thuê thì mất bao lâu?"], [T([TACH], PT)]),
]

L3 = [
    # ca người dùng thấy + biến thể: teencode + chữ dính (không dấu / có dấu), nhiều lĩnh vực
    C(["t muon đk kethon"], [T([KH], [])]),
    C(["muon dang ky kethon"], [T([KH], [])]),
    C(["t muon dk ket hon"], [T([KH], [])]),
    C(["đk kết hôn"], [T([KH], [])]),
    C(["dangkykhaisinh cần giấy tờ gì"], [T([KS], COMP)]),
    C(["dangkytamtru nop o dau"], [T([TT], ADDR)]),
    C(["mk muon dk khaitu"], [T([KT], [])]),
    C(["tachho mat bao lau"], [T([TACH], PT)]),
    C(["e can lam xoadangkythuongtru"], [T([XH], [])]),
    C(["khaibaotamvang can giay to gi"], [T([TV], COMP)]),
    C(["chungthucchuky phi bao nhieu"], [T([CTCK], FEE)]),
    C(["dangkygiamho nop online dc ko"], [T([GHO], ["online"])]),
    C(["t muon giahantamtru"], [T([GH], [])]),
    C(["đăngkýnhậncha mẹcon lệphí bao nhiêu"], [T([NCM], FEE)]),
    C(["đkhokinhdoanh cần hồ sơ gì"], [T([HKD], COMP)]),
    C(["dk ket hon ko mat phi chu"], [T([KH], FEE)]),
    C(["dk khai sinh cho con hso gom nhung j"], [T([KS], COMP)]),
    C(["thongbaoluutru nop onl dc k"], [T([LT], ["online"])]),
    C(["caplaithecancuoc mat bn tien"], [T([CCCD], FEE)]),
    C(["đăngkýkhaisinh online dc ko"], [T([KS], ["online"])]),
    C(["khongbiet lam sao dangkykethon"], [T([KH], ["steps"])]),
    C(["KetHon can nhung giay to gi a"], [T([KH], COMP)]),
    C(["DANGKYKHAITU"], [T([KT], [])]),
    C(["dangky khaisinh cho con, dangkytamtru cho me"], [T([KS], []), T([TT], [])]),
    C(["khai tử tg giải quyết bn ngày"], [T([KT], PT)]),
    C(["dangkykethon", "x", "thoigian giaiquyet va lephi the nao"], [T([KH], TF)]),
]

FAMILIES = [("p23_L1", L1), ("p23_L2", L2), ("p23_L3", L3)]


def build():
    out, ctx = [], []
    for cat, lst in FAMILIES:
        for i, c in enumerate(lst, 1):
            for t in c["tasks"]:
                for p in t["ids"]:
                    assert p in NAMES, (cat, p)
            turns = [{"role": "user" if k % 2 == 0 else "assistant", "text": ASST if (t == "x" and k % 2) else t} for k, t in enumerate(c["turns"])]
            exp = dict(tasks=[exp_task(t) for t in c["tasks"]] if c["beh"] == "answer" else [], behavior=c["beh"], must_say_not_published=False,
                       missing_numeric_fields=[], free_text_in_source=False, citation_tokens=[], notes=c["notes"] or "p23")
            if c["tasks"] and c["tasks"][0]["keys"]:
                exp["checks"] = [dict(kind="condition", proc_id=c["tasks"][0]["ids"][0], index_text="", keys=c["tasks"][0]["keys"])]
            out.append(dict(id=f"p23-{cat}-{i:02d}", category=cat, split="dev", source="p23-own", turns=turns, expected=exp))
            if len(turns) > 1 and c["beh"] == "answer":
                t0 = c["tasks"][0]
                ctx.append(dict(id=f"p23-{cat}-{i:02d}", category="ctx_p23", split="ctx-p23", source="p23-own", turns=turns,
                                expected=dict(tasks=[dict(acceptable_proc_ids=t0["ids"], fields=t0["fields"])], behavior="answer", forbid_proc_ids=[], independent=False)))
    return out, ctx


def rewrite(path, new):
    keep = [l for l in open(path, encoding="utf-8") if not json.loads(l)["id"].startswith("p23-")]
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(keep)
        for x in new:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    return len(keep)


def main():
    out, ctx = build()
    k = rewrite(os.path.join(HERE, "cases.jsonl"), out)
    kc = rewrite(os.path.join(HERE, "cases_ctx.jsonl"), ctx)
    print(f"cases.jsonl: {k} cũ + {len(out)} mới p23 | cases_ctx.jsonl: {kc} cũ + {len(ctx)} mới (ctx-p23) | " + ", ".join(f"{c}={len(l)}" for c, l in FAMILIES))


if __name__ == "__main__":
    main()

"""Bộ test hội thoại nhiều lượt của RIÊNG vòng cải thiện context memory (split="ctx-dev").
Dựng: python cases_ctx.py  -> cases_ctx.jsonl (assert mọi proc_id có trong DB). Chạy: python run_ctx.py --name <tên>

Mỗi hội thoại: danh sách lượt user; (text, pid_trợ_lý_vừa_trả_lời|None). Lượt trợ lý được dựng từ tên thủ tục thật.
Chấm: lượt user CUỐI. kind 'h' (độc lập): không được kế thừa (không task nào mang proc trong forbid), nếu có đáp án thì top-1 đúng.
"""
import json, os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("S3_DB") or os.environ.get("S3_DATA_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "runtime", "system3.db")   # DB của System 3 (repo V10.6 cũ không còn)

KS, NCM, TL, LT, KSLK, KSL = "1.001193", "1.001022", "2.000635", "3.000722", "1.000689", "1.004884"
TT, TAM, GH, XTT, TH, TV = "1.004222", "1.004194", "1.002755", "1.003197", "1.010038", "1.003677"
KH, KHLD, XNHN, KT, LTKT, MT, MT2 = "1.000894", "1.000593", "1.004873", "1.000656", "2.002913", "1.001731", "3.000725"
HK_TL, HK_CD, HK_TN, HK_TD = "1.001612", "1.001266", "1.001570", "2.000720"
# Phase 16: CK/BS trước đây ghi theo kết quả hệ thống lúc đó (2.000992 = chứng thực chữ ký NGƯỜI DỊCH, 2.000942 = cấp bản sao có chứng thực từ bản chính GIAO DỊCH).
# Khoá nghiệp vụ của DEV (build_cases.P: CT_CK, CT_BS) là 2.000884 / 2.000815; ở đây chấp nhận CẢ HAI để số ctx so được trước/sau (đáp án cũ vẫn tính đúng).
CK, CKD, BS, BSO = "2.000884", "2.000992", "2.000815", "2.000942"
DC, CC, KTAT, GHO, NCN, KHNN = "2.001019", "1.116410", "1.001699", "1.004837", "2.001263", "2.000806"
LKH = "1.004746"

# (id, kind, [(user, pid_answered)...] (lượt cuối: pid_answered bỏ), [đáp án], fields|None, forbid)
C = []
SPLIT = "ctx-dev"
def add(kind, turns, ans, fields=None, forbid=(), note=""):
    C.append((kind, turns, list(ans), fields, list(forbid), SPLIT))

# (a) hỏi tiếp thiếu chủ ngữ
add("a", [("Đăng ký khai sinh cần giấy tờ gì?", KS), ("còn lệ phí?", None)], [KS], ["fees"])
add("a", [("đăng ký tạm trú", TAM), ("mất mấy ngày", None)], [TAM], ["processing_time"])
add("a", [("kết hôn cần những gì", KH), ("nộp ở đâu vậy", None)], [KH], ["address"])
add("a", [("đăng ký thường trú gồm những bước nào", TT), ("mất bao lâu", TT), ("rồi nộp ở đâu", None)], [TT], ["address"])
add("a", [("đăng ký khai tử", KT), ("rồi sao nữa", None)], [KT], None)
add("a", [("dang ky tam tru can giay to gi", TAM), ("con le phi bn", None)], [TAM], ["fees"])
add("a", [("tách hộ là sao z", TH), ("làm online dc ko", None)], [TH], ["online"])
add("a", [("làm lại thẻ căn cước", CC), ("tốn bao nhiêu", CC), ("mấy ngày có", None)], [CC], ["processing_time"])
# (b) đổi mục trong cùng thủ tục
add("b", [("khai sinh cần giấy tờ gì", KS), ("lệ phí", KS), ("thế còn thời gian giải quyết?", KS), ("có nộp mạng được không", None)], [KS], ["online"])
add("b", [("thành lập hộ kinh doanh cần hồ sơ gì", HK_TL), ("phí bao nhiêu", HK_TL), ("có làm trực tuyến không", None)], [HK_TL], ["online"])
add("b", [("gia hạn tạm trú cần gì", GH), ("vậy thời hạn bao lâu", None)], [GH], ["processing_time"])
# (c) thủ tục liên quan cùng chủ đề / thủ tục khác hẳn
add("c", [("đăng ký khai sinh cần gì", KS), ("thế còn đăng ký nhận cha mẹ con thì sao", None)], [NCM])
add("c", [("đăng ký khai sinh cần gì", KS), ("thế còn đăng ký nhận cha mẹ con thì sao", NCM), ("rồi muốn xin bản sao trích lục khai sinh thì làm sao", None)], [TL])
add("c", [("đăng ký khai sinh cần gì", KS), ("còn đăng ký nhận cha mẹ con", NCM), ("xin bản sao trích lục khai sinh", TL), ("rồi bảo hiểm y tế cho trẻ em thì sao", None)], [LT])
add("c", [("đăng ký thường trú cần giấy tờ gì", TT), ("còn tạm trú thì sao", None)], [TAM])
add("c", [("đăng ký kết hôn cần giấy tờ gì", KH), ("thế giấy xác nhận tình trạng hôn nhân thì sao", None)], [XNHN])
add("c", [("đăng ký khai tử", KT), ("còn xóa đăng ký thường trú cho người mất", None)], [XTT, LTKT])
add("c", [("khai tử cần gì", KT), ("người mất có được hỗ trợ chi phí mai táng không", None)], [MT, MT2])
add("c", [("mở hộ kinh doanh cần gì", HK_TL), ("còn muốn tạm ngừng kinh doanh thì sao", None)], [HK_TN])
add("c", [("chứng thực chữ ký cần mang theo gì", CK), ("thế chứng thực di chúc?", None)], [DC])
add("c", [("đăng ký khai sinh", KS), ("thế còn đăng ký thành lập hộ kinh doanh thì sao", None)], [HK_TL], forbid=[KS])
add("c", [("đăng ký tạm trú", TAM), ("thế còn xác định mức độ khuyết tật thì sao", None)], [KTAT], forbid=[TAM])
add("c", [("đăng ký khai sinh", KS), ("còn đăng ký giám hộ?", None)], [GHO], forbid=[KS])
add("c", [("đăng ký khai sinh cần giấy tờ gì", KS), ("còn đăng ký lại khai sinh thì sao", None)], [KSL])
add("c", [("khai sinh cho con", KS), ("vậy khai sinh kết hợp nhận cha mẹ con thì cần gì", None)], [KSLK])
# (d) sửa ý
add("d", [("đăng ký khai sinh cần gì", KS), ("ý tôi là đăng ký nhận cha mẹ con chứ không phải khai sinh", None)], [NCM], forbid=[KS, KSLK])
add("d", [("đăng ký tạm trú cần gì", TAM), ("không phải, ý mình hỏi thường trú cơ", None)], [TT], forbid=[TAM])
add("d", [("đăng ký kết hôn cần gì", KH), ("nhầm rồi, tôi hỏi kết hôn lưu động", None)], [KHLD])
add("d", [("đăng ký khai tử cần gì", KT), ("sai rồi, tôi muốn hỏi cấp giấy xác nhận tình trạng hôn nhân", None)], [XNHN], forbid=[KT])
add("d", [("tách hộ phí bao nhiêu", TH), ("à không, tôi cần hỏi xóa đăng ký thường trú, phí bao nhiêu", None)], [XTT], ["fees"], forbid=[TH])
# (e) kể hoàn cảnh rồi hỏi
add("e", [("nhà tôi vừa có bé mới sinh", None), ("giờ cần làm giấy tờ gì cho bé", None)], [KS, LT, KSLK])
add("e", [("chồng tôi mới mất hôm qua", None), ("tôi cần đi đăng ký gì", None)], [KT, LTKT])
add("e", [("hai đứa tôi sắp cưới", None), ("cần đăng ký gì ở phường", None)], [KH])
add("e", [("tôi mới chuyển từ quê lên ở trọ", None), ("cần khai báo cư trú gì", None)], [TAM, TT, "1.010040"])
add("e", [("tôi định mở quán nhỏ bán ở nhà", None), ("cần đăng ký hộ kinh doanh gì", None)], [HK_TL])
# (f) đại từ
add("f", [("đăng ký kết hôn", KH), ("thủ tục này do ai giải quyết", None)], [KH], ["agency"])
add("f", [("đăng ký tạm trú", TAM), ("cái đó nộp online được không", None)], [TAM], ["online"])
add("f", [("đăng ký giám hộ", GHO), ("vậy thì cần giấy tờ gì", GHO), ("nó mất bao lâu", None)], [GHO], ["processing_time"])
add("f", [("đăng ký khai sinh", KS), ("vậy thì tôi nộp ở đâu", None)], [KS], ["address"])
# (g) quay lại chủ đề cũ
add("g", [("đăng ký khai sinh", KS), ("đăng ký tạm trú", TAM), ("quay lại cái khai sinh lúc nãy, lệ phí bao nhiêu", None)], [KS], ["fees"])
add("g", [("đăng ký kết hôn", KH), ("đăng ký khai tử", KT), ("à còn cái đầu tiên, nộp ở đâu", None)], [KH], ["address"])
add("g", [("đăng ký thường trú", TT), ("đăng ký tạm trú", TAM), ("quay lại thường trú, mất bao lâu", None)], [TT], ["processing_time"])
add("g", [("đăng ký khai sinh", KS), ("đăng ký nhận cha mẹ con", NCM), ("còn cái trước đó thì phí bao nhiêu", None)], [KS], ["fees"])
# (h) độc lập: KHÔNG kế thừa
add("h", [("đăng ký khai sinh cần gì", KS), ("đăng ký tạm trú nộp ở đâu", None)], [TAM], forbid=[KS])
add("h", [("đăng ký kết hôn cần gì", KH), ("chứng thực di chúc cần gì", None)], [DC], forbid=[KH])
add("h", [("đăng ký khai sinh cần gì", KS), ("hôm nay trời đẹp nhỉ", None)], [], forbid=[KS])
add("h", [("đăng ký tạm trú cần gì", TAM), ("làm hộ chiếu ở đâu", None)], [], forbid=[TAM])
add("h", [("đăng ký khai sinh", KS), ("đăng ký thành lập hộ kinh doanh cần gì", None)], [HK_TL], forbid=[KS])
add("h", [("đăng ký khai tử", KT), ("cấp lại thẻ căn cước phí bao nhiêu", None)], [CC], ["fees"], forbid=[KT])
add("h", [("tách hộ cần gì", TH), ("xin chào", None)], [], forbid=[TH])
add("h", [("đăng ký kết hôn cần gì", KH), ("thi bằng lái xe ở đâu", None)], [], forbid=[KH])
add("h", [("thành lập hộ kinh doanh cần gì", HK_TL), ("xác định mức độ khuyết tật cần giấy tờ gì", None)], [KTAT], forbid=[HK_TL])
add("h", [("đăng ký khai sinh", KS), ("còn tạm trú cần giấy tờ gì", None)], [TAM], forbid=[KS])
# (i) hỏi tiếp bằng điều kiện
add("i", [("đăng ký khai sinh cần gì", KS), ("còn nếu bé sinh ở nhà thì sao", None)], [KS])
add("i", [("đăng ký tạm trú cần gì", TAM), ("nếu tôi ở nhà thuê thì sao", None)], [TAM])
add("i", [("đăng ký kết hôn cần gì", KH), ("trường hợp một bên là người nước ngoài thì sao", None)], [KH, KHNN])
add("i", [("đăng ký khai sinh cần gì", KS), ("bé sinh ra không có giấy chứng sinh thì sao", None)], [KS])
add("i", [("làm lại thẻ căn cước", CC), ("nếu bị mất thẻ thì sao", None)], [CC])

# ---------------------------------------------------------------------------------------------------------------
# split "ctx-hold": viết SAU khi bộ ctx-dev đã chạy sạch, dùng thủ tục/cách nói khác để kiểm quá khớp (không tune theo nó trước khi đo lần đầu)
SPLIT = "ctx-hold"
TVG, HN, TCXH, LNCN = TV, "1.011607", "1.001776", "2.001255"
add("a", [("Cho mình hỏi thủ tục khai báo tạm vắng", TV), ("phải nộp cái gì vậy", None)], [TV], ["components"])
add("a", [("công nhận hộ nghèo cần giấy tờ gì", HN), ("ai giải quyết cái này", None)], [HN], ["agency"])
add("a", [("làm lại thẻ căn cước", CC), ("ok, thế nộp trên mạng được không", None)], [CC], ["online"])
add("a", [("chứng thực chữ ký", CK), ("mất tiền không", None)], [CK, CKD], ["fees"])
add("b", [("thay đổi nội dung đăng ký hộ kinh doanh", HK_TD), ("hồ sơ gồm gì", HK_TD), ("lệ phí", HK_TD), ("bao lâu thì xong", None)], [HK_TD], ["processing_time"])
add("c", [("đăng ký nuôi con nuôi trong nước", NCN), ("còn đăng ký lại việc nuôi con nuôi thì sao", None)], [LNCN])
add("c", [("đăng ký khai sinh cần gì", KS), ("thế còn khai tử", None)], [KT])
add("c", [("đăng ký khai tử cần gì", KT), ("còn khai sinh nữa nhỉ", None)], [KS])
add("c", [("khai báo tạm vắng", TV), ("à còn tạm trú thì sao", None)], [TAM])
add("c", [("thành lập hộ kinh doanh cần gì", HK_TL), ("rồi muốn chấm dứt hoạt động hộ kinh doanh thì sao", None)], [HK_CD])
add("c", [("công nhận hộ nghèo cần giấy tờ gì", HN), ("thế còn trợ cấp xã hội hàng tháng", None)], [TCXH])
add("c", [("chứng thực chữ ký cần gì", CK), ("bên cạnh đó chứng thực bản sao từ bản chính thì cần gì", None)], [BS, BSO])
add("d", [("đăng ký thường trú cần gì", TT), ("ý mình là xóa đăng ký thường trú chứ không phải đăng ký thường trú", None)], [XTT], forbid=[TT])
add("d", [("chứng thực chữ ký cần gì", CK), ("không phải, tôi hỏi chứng thực di chúc", None)], [DC], forbid=[CK, CKD])
add("d", [("đăng ký kết hôn cần gì", KH), ("nhầm, tôi muốn đăng ký lại kết hôn", None)], [LKH], forbid=[KH])
add("e", [("bé nhà mình sinh được hai tuần rồi", None), ("giờ phải làm gì để có giấy khai sinh", None)], [KS, KSLK, LT])
add("e", [("ba tôi vừa qua đời", None), ("cần làm giấy tờ gì ở phường", None)], [KT, LTKT, XTT])
add("e", [("em sắp lấy chồng", None), ("thủ tục đăng ký ở xã thế nào", None)], [KH])
add("f", [("tách hộ", TH), ("thủ tục đó mất phí không", None)], [TH], ["fees"])
add("f", [("đăng ký nuôi con nuôi", NCN), ("vậy thì nộp ở đâu thế", None)], [NCN], ["address"])
add("g", [("đăng ký khai sinh", KS), ("đăng ký khai tử", KT), ("thôi quay lại khai sinh, mất bao lâu", None)], [KS], ["processing_time"])
add("g", [("đăng ký tạm trú", TAM), ("đăng ký kết hôn", KH), ("chứng thực chữ ký", CK), ("cái đầu tiên ấy, lệ phí bao nhiêu", None)], [TAM], ["fees"])
add("h", [("chứng thực chữ ký cần gì", CK), ("đăng ký khai sinh cần gì", None)], [KS], forbid=[CK, CKD])
add("h", [("khai báo tạm vắng", TV), ("thành lập hộ kinh doanh cần gì", None)], [HK_TL], forbid=[TV])
add("h", [("đăng ký khai sinh", KS), ("cảm ơn nhé", None)], [], forbid=[KS])
add("h", [("công nhận hộ nghèo cần giấy tờ gì", HN), ("mua bảo hiểm xe máy ở đâu", None)], [], forbid=[HN])
add("h", [("đăng ký thường trú", TT), ("đăng ký tạm trú mất bao lâu", None)], [TAM], ["processing_time"], forbid=[TT])
add("h", [("đăng ký khai tử", KT), ("chứng thực chữ ký ở đâu", None)], [CK, CKD], ["address"], forbid=[KT])
add("i", [("thành lập hộ kinh doanh cần gì", HK_TL), ("nếu tôi chỉ bán online thì sao", None)], [HK_TL])
add("i", [("chứng thực chữ ký cần gì", CK), ("trường hợp người ký là người khuyết tật thì sao?", None)], [CK, CKD])
add("i", [("đăng ký nuôi con nuôi", NCN), ("còn nếu nhận con của người thân thì sao", None)], [NCN])
add("i", [("xác định mức độ khuyết tật", KTAT), ("nếu không đi lại được thì làm sao", None)], [KTAT])
add("i", [("đăng ký tạm trú", TAM), ("mà tôi chưa có sổ đỏ thì sao", None)], [TAM])

# ---------------------------------------------------------------------------------------------------------------
# split "ctx-p16": Phase 16 (nhóm D) do agent sửa lỗi tự nghĩ; thẻ hỏi lại ("LIST") + câu nối "cái thứ n", "còn phí?", kể thêm hoàn cảnh
SPLIT = "ctx-p16"
import importlib.util as _iu
_sp = _iu.spec_from_file_location("build_p16", os.path.join(HERE, "build_p16.py"))
_m = _iu.module_from_spec(_sp); _sp.loader.exec_module(_m)
for _k, _t, _a, _f, _fb in _m.CTX:
    add(_k, _t, _a, _f, _fb or ())


def build():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    names = {r[0]: r[1] for r in db.execute("select proc_id,name from procedures where status='active'")}
    out = []
    for i, (kind, turns, ans, fields, forbid, split) in enumerate(C, 1):
        for p in ans + forbid + [x for _, p in turns if p for x in (p[1:] if isinstance(p, tuple) else [p])]:
            assert p in names, p
        tt = []
        for j, (text, p) in enumerate(turns):
            tt.append({"role": "user", "text": text})
            if j < len(turns) - 1:
                if isinstance(p, tuple):    # thẻ hỏi lại đã đánh số (đúng định dạng lưu trong lịch sử hội thoại)
                    a = "Bạn muốn hỏi về thủ tục nào? " + " ".join(f"{k}) {names[x]}" for k, x in enumerate(p[1:], 1))
                else:
                    a = (f"Về «{names[p]}»: bạn cần chuẩn bị hồ sơ theo quy định, nộp tại UBND cấp xã. Bạn muốn hỏi thêm gì không?"
                         if p else "Mình đã ghi nhận. Bạn muốn hỏi về thủ tục nào?")
                tt.append({"role": "assistant", "text": a})
        out.append({"id": f"{split.replace('ctx-', '')}-{i:02d}", "category": f"ctx_{kind}", "split": split, "source": "ctx-own", "turns": tt,
                    "expected": {"tasks": [{"acceptable_proc_ids": ans, "fields": fields or []}] if ans else [],
                                 "behavior": "answer" if ans else "apologize", "forbid_proc_ids": forbid,
                                 "independent": kind == "h"}})
    with open(os.path.join(HERE, "cases_ctx.jsonl"), "w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(len(out), "hội thoại")


if __name__ == "__main__":
    build()

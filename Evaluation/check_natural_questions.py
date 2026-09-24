"""Kiểm tra hồi quy Hệ thống 2 với câu hỏi TỰ NHIÊN kiểu người dân (chạy thử thật 24/09).

Chạy trên CSDL thật (Database/runtime/procedures.db), không cần Ollama:
    .venv\\Scripts\\python.exe Evaluation\\check_natural_questions.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "Backend"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.stdout.reconfigure(encoding="utf-8")

from Database.pipeline import retrieval as R  # noqa: E402
from core import procedure_table  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(f"[{'OK' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


conn = R.connect()

# 1. Chip 🎯: câu hỏi dài kiểu người thật phải được nhận là hỏi thủ tục; xã giao thì không.
for q in ["vợ em mới sinh bé hôm qua, giờ làm giấy khai sinh cho bé cần những gì ạ",
          "2 đứa định cưới cuối năm, lên phường đăng ký kết hôn cần mang gì",
          "làm lại căn cước bị mất thì sao",
          "làm giấy khai sinh cho con cần gì",
          "đăng ký kết hôn cần giấy tờ gì"]:
    check(f"chip 🎯: '{q}'", R.looks_like_procedure(conn, q) is not None)
for q in ["chào bạn", "cảm ơn nhé", "bạn tên gì", "mình cần hỗ trợ"]:
    check(f"KHÔNG chip: '{q}'", R.looks_like_procedure(conn, q) is None)

# 1b. Từ đồng nghĩa / bỏ "làm" đầu câu — không được nuốt chữ nằm trong tên thủ tục.
for q, want in [("làm giấy chứng tử cho mẹ", "khai tu"),
                ("công chứng bản sao", "chung thuc ban sao"),
                ("làm việc với cơ quan thuế", "lam viec voi co quan thue"),
                ("làm lại căn cước", "lai can cuoc")]:
    got = R.parse_query(q)["keyword"]
    check(f"từ khoá '{q}' -> '{want}'", got == want, got)
# synonyms.json do người khác sửa: cụm ngắn đứng trước cụm dài chứa nó thì cụm dài
# không bao giờ khớp ("ho khau" trước "nhap ho khau").
for key in ("synonyms", "drop_phrases"):
    phs = list(R._VOCAB[key])
    bad = [(a, b) for i, a in enumerate(phs) for b in phs[i + 1:] if f" {a} " in f" {b} "]
    check(f"synonyms.json '{key}': cụm dài đứng trước cụm ngắn", not bad, bad)

# 2. MCQ: thủ tục đúng phải đứng đầu, không để "Khai thuế … xăng sinh học" chen lên.
top = R.search(conn, R.parse_query("làm giấy khai sinh cho con")["keyword"], 5)[0]
check("MCQ 'làm giấy khai sinh cho con' -> #1 có 'khai sinh', không phải thuế",
      "khai sinh" in top["name"].lower() and "thuế" not in top["name"].lower(), top["name"])

# 3. Bộ gác "thủ tục khác" (chỉ gắn cảnh báo).
birth = R.search(conn, "đăng ký khai sinh", 1)[0]["proc_id"]
check("gác: 'à còn làm lại căn cước bị mất thì sao' (đang ở khai sinh) -> thủ tục khác",
      R.is_other_procedure(conn, "à còn làm lại căn cước bị mất thì sao", birth))
for q in ["lệ phí bao nhiêu", "mất mấy ngày thì có giấy", "làm online được không bạn",
          "thứ 7 phường có làm việc không bạn", "hồ sơ cần những gì", "nộp ở đâu vậy",
          "có mẫu đơn không", "hộ nghèo có phải nộp lệ phí không", "mất bao lâu",
          "tóm tắt giúp mình các bước với", "cho con thì cần giấy tờ gì"]:
    check(f"gác: '{q}' -> KHÔNG phải thủ tục khác", not R.is_other_procedure(conn, q, birth))
# Gõ KHÔNG dấu: "can" = "cần"/"căn" — giữ lại khi ghép với chữ bên cạnh thành
# cặp có trong tên thủ tục ("can cuoc").
for q in ["a con lam lai can cuoc bi mat thi sao", "cap doi the can cuoc thi sao",
          "con lam the bao hiem y te thi sao"]:
    check(f"gác không dấu: '{q}' -> thủ tục khác", R.is_other_procedure(conn, q, birth))
for q in ["le phi bao nhieu", "ho so can nhung gi", "cho con thi can giay to gi",
          "can mang theo gi", "can ban sao khong", "the thi sao", "mat bao lau"]:
    check(f"gác không dấu: '{q}' -> KHÔNG phải thủ tục khác",
          not R.is_other_procedure(conn, q, birth))

# 4. field_answer: lịch làm việc -> câu cố định; không mượn nhầm ô của câu trước.
table = procedure_table.build(R.build_record(conn, birth))
ans = procedure_table.field_answer(table, "thứ 7 phường có làm việc không bạn",
                                   previous="mất mấy ngày thì có giấy")
check("'thứ 7 phường có làm việc không' -> nói rõ bảng không có, KHÔNG trích ô thời gian",
      ans is not None and "không có" in ans and "Thời gian giải quyết" not in ans, ans)
ans2 = procedure_table.field_answer(table, "làm online được không bạn",
                                    previous="mất mấy ngày thì có giấy")
check("'làm online được không' vẫn trích ô online (không mượn ô thời gian)",
      ans2 is not None and "Thời gian giải quyết" not in ans2, ans2)
ans3 = procedure_table.field_answer(table, "còn người khuyết tật thì sao",
                                    previous="lệ phí bao nhiêu")
check("'còn người khuyết tật thì sao' vẫn mượn mục lệ phí của câu trước",
      ans3 is not None and "đối chiếu" in ans3, ans3)

# 5. MCQ 1 "thủ tục chính": gõ đúng tên / chỉ một nhóm khớp chắc -> bỏ qua.
def mcq1(q):
    hits = R.search(conn, R.parse_query(q)["keyword"], 30)
    return R.axes_for_families(conn, hits, not R.is_strong(hits))


for q in ["đăng ký kết hôn", "đăng ký khai sinh", "đăng ký tạm trú", "trích lục khai sinh",
          "xác nhận tình trạng hôn nhân"]:
    check(f"MCQ 1 bỏ qua: '{q}'", mcq1(q) == [])
for q in ["cấp giấy phép xây dựng", "đăng ký hộ kinh doanh", "làm giấy khai sinh cho con"]:
    check(f"MCQ 1 vẫn hỏi: '{q}'", mcq1(q) != [])

# 6-8 cần mã Backend (LLM được thay bằng hàm giả — không cần Ollama).
import developer_mode  # noqa: E402
from core import intent, llm, system_retrieval as S, verifier  # noqa: E402
from core.turn import TurnInput, TurnResult  # noqa: E402
from prompts import retrieval_templates as RT  # noqa: E402


def no_llm(*_a, **_k):
    raise AssertionError("không được gọi LLM")


def run(fn, q, **kw):
    res = TurnResult(system="retrieval")
    return fn(conn, TurnInput(question=q), res, developer_mode.turn(q), lambda *_: 0,
              status=lambda _: None, **kw)


# 6. Ô chăm sóc: câu về thủ tục khác, code không trích được ô -> câu cố định, không LLM 2.
real_chat = llm.chat
llm.chat = no_llm
try:
    r = run(S._care, "à còn làm lại căn cước bị mất thì sao", pending={"proc_id": birth, "picked": {}})
    check("thủ tục khác -> câu cố định + nút ô chat mới, không gọi LLM 2",
          RT.OTHER_PROCEDURE_TEXT in r.text and r.table.get("kind") == "new_procedure", r.text)
except AssertionError as exc:
    check("thủ tục khác -> không gọi LLM 2", False, str(exc))

# 7. Chế độ trò chuyện: câu lẫn tiếng Anh / nêu con số khi chưa tra -> câu cố định.
for fake, q, why in [("Bạn cần giấy chứng nhận đăng ký kinh register ạ.", "chào bạn", "tiếng Anh"),
                     ("Lệ phí là 50.000 đồng, 3 ngày có kết quả.",
                      "làm giấy khai sinh cho con cần gì", "con số khi hỏi thủ tục")]:
    llm.chat = lambda *_a, _t=fake, **_k: _t
    r = run(S._chat, q)
    check(f"trò chuyện: chặn câu {why}", fake not in r.text, r.text)
llm.chat = lambda *_a, **_k: "Đăng ký khai sinh là thủ tục ghi nhận việc sinh của trẻ."
r = run(S._chat, "làm giấy khai sinh cho con cần gì")
check("trò chuyện: câu tiếng Việt sạch giữ nguyên",
      r.text.startswith("Đăng ký khai sinh là thủ tục"), r.text)
# `stop` cắt ở xuống dòng: bỏ câu dở, bỏ từ dấu ":" (mở danh sách) trở đi.
llm.chat = lambda *_a, **_k: ("Đăng ký khai sinh là thủ tục ghi nhận việc sinh của trẻ. "
                              "Cần chuẩn bị: giấy chứng sinh, căn cước.")
r = run(S._chat, "làm giấy khai sinh cho con cần gì")
check("trò chuyện: danh sách sau ':' bị cắt, giữ câu đầu",
      r.text.split("\n")[0] == "Đăng ký khai sinh là thủ tục ghi nhận việc sinh của trẻ.", r.text)
# QĐ1: chỉ bỏ CÂU bịa số, giữ câu mở đầu; không có chip thì số giữ nguyên, không tách "50.000".
llm.chat = lambda *_a, **_k: ("Đăng ký khai sinh là thủ tục ghi nhận việc sinh của trẻ. "
                              "Lệ phí là 50.000 đồng.")
r = run(S._chat, "làm giấy khai sinh cho con cần gì")
check("trò chuyện: bỏ câu có số, giữ câu mở đầu",
      r.text.split("\n")[0] == "Đăng ký khai sinh là thủ tục ghi nhận việc sinh của trẻ.", r.text)
llm.chat = lambda *_a, **_k: "Mình có thể giúp bạn, giá vé xe khoảng 50.000 đồng thôi."
r = run(S._chat, "chào bạn")
check("trò chuyện: không hỏi thủ tục -> giữ nguyên câu có '50.000'",
      r.text == "Mình có thể giúp bạn, giá vé xe khoảng 50.000 đồng thôi.", r.text)
llm.chat = lambda *_a, **_k: "Chào bạn! Khi muốn khai tử cho bố, cần thực hiện các bước sau:"
r = run(S._chat, "khai tử cho bố")
check("trò chuyện: chỉ còn 'Chào bạn!' -> câu cố định", RT.CHAT_GUARDED_TEXT in r.text, r.text)
llm.chat = real_chat

# 8. Hệ thống 1 (Web search).
check("lưu ý cấp huyện: 'TAND cấp huyện' -> gắn lưu ý",
      "Tòa án nhân dân khu vực" in verifier.note_outdated_units("Nộp đơn tại TAND cấp huyện [S1]."))
for s in ["Nộp tại UBND cấp xã [S1].", "Tòa án quân sự khu vực giải quyết."]:
    check(f"lưu ý cấp huyện: KHÔNG gắn cho '{s}'", verifier.note_outdated_units(s) == s)

def ly_hon_issue(answer, q="ly hôn thuận tình nộp đơn ở đâu"):
    v = verifier.Verification()
    verifier.rule_check(answer, {"sources": [{"id": "S1", "title": "", "content": "Tòa án"}]}, v, q)
    return any("ly hôn" in i for i in v.rule_issues)


check("ly hôn trả 'UBND cấp xã' -> luật đánh trượt", ly_hon_issue("Bạn nộp đơn tại UBND cấp xã nơi cư trú [S1]."))
check("ly hôn trả 'Tòa án' -> không bị luật này bắt", not ly_hon_issue("Bạn nộp đơn tại Tòa án nhân dân khu vực [S1]."))


def authority_issue(answer, q):
    v = verifier.Verification()
    verifier.rule_check(answer, {"sources": [{"id": "S1", "title": "", "content": ""}]}, v, q)
    return any("thẩm quyền" in i for i in v.rule_issues)


def issues(answer, q, evidence=""):
    v = verifier.Verification()
    verifier.rule_check(answer, {"sources": [{"id": "S1", "title": "", "content": evidence}]}, v, q)
    return " | ".join(v.rule_issues)


# Luật cứng từng đánh trượt câu trả lời ĐÚNG (evaluate.py chạy thật 24/09).
ev = "Thời hạn đăng ký khai sinh là 60 ngày. Lệ phí 15.000 đồng. Trường hợp có yếu tố nước ngoài."
got = issues("Theo thông tin trong các tài liệu:\n- Tài liệu [S1]: Thời hạn đăng ký khai sinh là "
             "60 ngày kể từ ngày sinh con.", "thời hạn đăng ký khai sinh", ev)
check("'…trong các tài liệu:' giữa câu KHÔNG bị coi là chép prompt", "khung prompt" not in got, got)
check("'Tài liệu:' đứng riêng một dòng vẫn bị bắt",
      "khung prompt" in issues("Tài liệu:\n\n[S1] Đăng ký khai sinh…", "khai sinh", ev))
got = issues("Lệ phí đăng ký tạm trú năm 2026 là 15.000 đồng/lần đăng ký.", "le phi dang ky tam tru", ev)
check("câu ngắn có con số khớp nguồn KHÔNG bị 'quá ngắn'", "quá ngắn" not in got, got)
check("câu ngắn không nội dung vẫn bị 'quá ngắn'",
      "quá ngắn" in issues("Bạn liên hệ bộ phận một cửa nhé.", "le phi dang ky tam tru", ev))
got = issues("Đăng ký khai sinh trong 60 ngày [S1]. Trường hợp có yếu tố nước ngoài làm thủ tục riêng [S1].",
             "làm giấy khai sinh cho con cần gì", ev)
check("khai sinh chép cụm 'yếu tố nước ngoài' từ nguồn KHÔNG bị luật 8", "nước ngoài" not in got, got)
check("khai sinh nêu lệ phí 1.500.000 đồng vẫn bị luật 8",
      "nước ngoài" in issues("Lệ phí 1.500.000 đồng [S1].", "làm giấy khai sinh cho con cần gì", ev))

from core import evidence  # noqa: E402

pack = {"sources": [{"id": "S1", "title": "Lệ phí cư trú",
                     "content": "Đăng ký tạm trú: 15.000 đồng/lần đăng ký đối với trường hợp công "
                                "dân nộp hồ sơ trực tiếp."},
                    {"id": "S2", "title": "Căn cước", "content": "Công an cấp xã tiếp nhận hồ sơ."}]}
got = evidence.cite_lines("- 15.000 đồng/lần đăng ký đối với trường hợp công dân nộp hồ sơ trực tiếp.\n"
                          "- Ảnh thẻ chụp rõ nét, không bị lỗi màu sắc hoặc độ sáng khi làm hồ sơ.\n"
                          "Các khoản lệ phí đăng ký cư trú như sau:", pack)
lines = got.splitlines()
check("tự gắn [S#]: dòng chép nguồn -> [S1]", lines[0].endswith("trực tiếp [S1]."), lines[0])
check("tự gắn [S#]: dòng tự thêm -> không gắn", "[S" not in lines[1], lines[1])
check("tự gắn [S#]: dòng tiêu đề ':' -> không gắn", "[S" not in lines[2], lines[2])
check("tự gắn [S#]: dòng đã có [S2] -> giữ nguyên",
      evidence.cite_lines("Công an cấp xã tiếp nhận hồ sơ của công dân [S2].", pack)
      == "Công an cấp xã tiếp nhận hồ sơ của công dân [S2].")

fee_q = "Đăng ký kết hôn có mất lệ phí không?"
for a in ["Trực tiếp: Không có lệ phí [S1]. Trực tuyến: Không có lệ phí [S1]. Vì vậy, đăng ký kết hôn "
          "không phải chịu bất kỳ khoản phí nào.",
          "Người có yêu cầu nộp hồ sơ tại UBND cấp xã. Không phải trả phí [S1]. Thời hạn giải quyết ngay."]:
    check(f"lệ phí: '{a[:40]}…' -> đủ, không bị bắt", "lệ phí" not in issues(a, fee_q), issues(a, fee_q))
check("lệ phí: 'không nêu rõ lệ phí' vẫn bị bắt",
      "lệ phí" in issues("Tài liệu không nêu rõ lệ phí đăng ký kết hôn, bạn hỏi bộ phận một cửa [S1].", fee_q))
ev_land = "Hồ sơ đăng ký tạm trú: giấy tờ chứng minh chỗ ở hợp pháp như Giấy chứng nhận quyền sử dụng đất."
check("tạm trú nêu 'quyền sử dụng đất' có trong nguồn -> không bị 'lẫn thủ tục'",
      "Lẫn lộn" not in issues("Giấy tờ chứng minh chỗ ở hợp pháp: Giấy chứng nhận quyền sử dụng đất [S1].",
                              "Đăng ký tạm trú cần những giấy tờ gì?", ev_land))
check("tạm trú nêu 'giấy phép xây dựng' không có trong nguồn -> vẫn bị bắt",
      "Lẫn lộn" in issues("Cần giấy phép xây dựng và bản vẽ thiết kế nhà [S1].",
                          "Đăng ký tạm trú cần những giấy tờ gì?", ev_land))

check("hộ chiếu không nhắc Công an/XNC/DVC -> trượt",
      authority_issue("Bạn chuẩn bị ảnh 4x6 và nộp tại UBND phường [S1].", "làm hộ chiếu cần giấy tờ gì"))
check("hộ chiếu nhắc Cổng Dịch vụ công -> qua",
      not authority_issue("Bạn nộp hồ sơ qua Cổng Dịch vụ công Bộ Công an [S1].", "làm hộ chiếu online"))
check("căn cước nhắc VNeID -> qua",
      not authority_issue("Bạn đề nghị cấp lại trên ứng dụng VNeID [S1].", "mất căn cước làm lại thế nào"))
check("bản nháp rỗng -> câu từ chối, không để trống",
      verifier.apply_fail_policy("", verifier.Verification()) == verifier.T.VERIFY_REFUSAL)

choices = intent.generate_prompt_choices(
    "vợ chồng mình muốn ly hôn thuận tình thì nộp đơn ở đâu",
    intent.Understanding(intent="marriage_registration"), 2026)
check("gợi ý ly hôn không gài 'UBND'", not any("UBND" in c for c in choices), str(choices))

real_u, real_g = intent.understand, intent.gate
intent.gate = lambda *_: "ask"
for q, it, want in [("vợ chồng mình muốn ly hôn thuận tình thì nộp đơn ở đâu",
                     "marriage_registration", "search"),
                    ("Tôi muốn đăng ký thường trú.", "permanent_residence", "clarify")]:
    intent.understand = lambda *_a, _i=it: intent.Understanding(
        intent=_i, needs_clarification=True, clarifying_question="Bạn đang muốn làm thủ tục gì?")
    got = intent.analyze(q, [], "", {})
    check(f"Web search '{q}' -> {want}", got.route == want, got.route)
    # Câu hỏi chi tiết đã rõ thủ tục -> tra luôn, không tốn lượt LLM cho bộ gác.
    check(f"bộ gác {'bỏ qua' if want == 'search' else 'vẫn gọi'}: '{q}'",
          (got.gate == "skipped") == (want == "search"), got.gate)
intent.understand, intent.gate = real_u, real_g

# 9. Bộ ~100 câu kiểu người thật (natural_questions.py). Tính điểm, so với MỐC:
#    tụt dưới mốc = hồi quy -> FAIL. Cải thiện được thì NÂNG mốc lên.
#    "top-3" = thủ tục đúng nằm trong 3 lựa chọn đầu của MCQ 1 (hoặc là thủ tục
#    được chọn thẳng khi MCQ 1 bị bỏ qua). Chỉ đường từ khoá — LLM 1 không tính.
# 24/09: 85, 79 / 89 câu -> thêm bảng từ đồng nghĩa + 14 câu diễn đạt khác: 100, 102 / 103.
MIN_CHIP, MIN_TOP3 = 100, 102
sys.path.insert(0, str(ROOT / "Evaluation"))
from natural_questions import QUESTIONS  # noqa: E402

idx = R.family_index(conn)
n_chip = n_top3 = n_pos = 0
misses = []
for q, want in QUESTIONS:
    chip = R.looks_like_procedure(conn, q) is not None
    if want is None:
        check(f"100 câu — KHÔNG chip: '{q}'", not chip)
        continue
    n_pos += 1
    n_chip += chip
    hits = R.search(conn, R.parse_query(q)["keyword"], 30)
    fam = R.axes_for_families(conn, hits, not R.is_strong(hits)) if hits else []
    labels = ([o["label"] for o in fam[0]["options"] if o["value"] != R.NONE_OF_THESE][:3] if fam
              else [idx["label"][R.family_of(conn, hits[0]["proc_id"])]] if hits else [])
    ok = any(want in R._fold(lb) for lb in labels)
    n_top3 += ok
    if not ok:
        misses.append(q)
print(f"    100 câu: chip {n_chip}/{n_pos}, đúng top-3 {n_top3}/{n_pos}. Trượt: {misses}")
check(f"100 câu — chip ≥ {MIN_CHIP}", n_chip >= MIN_CHIP, f"{n_chip}")
check(f"100 câu — đúng top-3 ≥ {MIN_TOP3}", n_top3 >= MIN_TOP3, f"{n_top3}")

conn.close()
print()
if FAILED:
    print(f"=== {len(FAILED)} FAIL ===")
    sys.exit(1)
print("=== TẤT CẢ PASS ===")

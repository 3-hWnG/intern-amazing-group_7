"""TẤT CẢ prompt của hệ thống + hàm dựng nội dung đưa vào prompt.

Viết cho mô hình NHỎ (1.5B–4B):
  - tài liệu tra cứu nằm trong system prompt, lượt user cuối chỉ là câu hỏi
    (mô hình nhỏ hay chép lại nguyên khối nếu nhét tài liệu vào lượt user);
  - không dùng nhãn VIẾT HOA kiểu biểu mẫu ở chỗ mô hình có thể chép lại;
  - ví dụ hiểu ý định là các lượt hội thoại thật, không nhồi trong system.

finetune/export_dataset.py dựng lại đúng các prompt này để dữ liệu huấn luyện
khớp với lúc chạy thật.
"""

from __future__ import annotations

import json
import re
from domain.text import fold

INTENTS = [
    "birth_registration", "marriage_registration", "permanent_residence",
    "temporary_residence", "identity_documents", "business_registration",
    "land_administration", "social_security", "tax", "other", "unknown",
    "chitchat", "out_of_scope",
]

INTENT_LABELS = {
    "birth_registration": "Đăng ký khai sinh",
    "marriage_registration": "Đăng ký kết hôn",
    "permanent_residence": "Đăng ký thường trú",
    "temporary_residence": "Đăng ký tạm trú",
    "identity_documents": "Căn cước / hộ chiếu / định danh",
    "business_registration": "Đăng ký kinh doanh",
    "land_administration": "Đất đai",
    "social_security": "Bảo hiểm xã hội",
    "tax": "Thuế",
    "other": "Thủ tục khác",
    "unknown": "Chưa rõ",
    "chitchat": "Trò chuyện",
    "out_of_scope": "Ngoài phạm vi",
}

TRUST_LABEL = {"official": "nguồn chính thống", "legal": "cơ sở dữ liệu pháp luật",
               "news": "báo chí", "other": "nguồn khác", "attachment": "tệp người dùng đính kèm"}


# ==========================================================================
# 1. HIỂU Ý ĐỊNH + NGỮ CẢNH + HỎI LẠI + TRUY VẤN
# ==========================================================================
UNDERSTAND_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": INTENTS},
        "standalone_question": {"type": "string"},
        "province": {"type": "string"},
        "ward": {"type": "string"},
        "missing_information": {"type": "array", "items": {"type": "string"}},
        "needs_clarification": {"type": "boolean"},
        "clarifying_question": {"type": "string"},
        "search_queries": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["intent", "standalone_question", "province", "ward",
                 "missing_information", "needs_clarification",
                 "clarifying_question", "search_queries"],
}


def understand_system(today: str, year: int) -> str:
    return f"""Bạn là bộ phân tích tin nhắn cho trợ lý thủ tục hành chính Việt Nam. Người nhắn là người dân bình thường, hay viết không dấu, viết tắt, sai chính tả.
Hôm nay: {today}. Từ 01/7/2025 Việt Nam có 34 tỉnh/thành, chính quyền 2 cấp (tỉnh và xã/phường), không còn cấp huyện.

Đọc ngữ cảnh (nếu có) và tin nhắn mới, trả về JSON:
- intent:
  birth_registration = khai sinh, trích lục / bản sao giấy khai sinh · marriage_registration = kết hôn, xác nhận tình trạng hôn nhân · permanent_residence = thường trú, hộ khẩu, xoá thường trú, xác nhận thông tin cư trú · temporary_residence = tạm trú, gia hạn tạm trú, lưu trú, thuê trọ · identity_documents = thẻ căn cước, CCCD, hộ chiếu · business_registration = hộ kinh doanh, doanh nghiệp · land_administration = đất đai, sổ đỏ, xây nhà, cấp phép xây dựng, thông báo khởi công · social_security = bảo hiểm xã hội, bảo hiểm y tế · tax = thuế · other = thủ tục hành chính khác (lý lịch tư pháp, giấy phép lái xe...)
  VNeID, dịch vụ công trực tuyến chỉ là KÊNH nộp: xếp theo thủ tục được làm. Hỏi mức phạt khi không làm một thủ tục: xếp theo thủ tục đó.
  chitchat = chỉ chào hỏi, cảm ơn, tạm biệt, hỏi bạn là ai
  out_of_scope = KHÔNG hỏi về thủ tục hành chính (làm thơ, kể chuyện, toán, tin tức, kiện tụng, tranh chấp, hình sự...)
  unknown = có vẻ hỏi thủ tục nhưng không biết là thủ tục nào
- standalone_question: viết lại tin nhắn mới thành một câu hỏi tiếng Việt có dấu, đầy đủ, độc lập.
  + NGUYÊN TẮC QUAN TRỌNG: Khi tin nhắn mới là câu hỏi nối tiếp (hỏi lệ phí, có tốn phí không, nơi nộp ở đâu, hồ sơ cần gì, thời hạn bao lâu, "thủ tục này...", "cái này..."):
    BẮT BUỘC giữ nguyên thủ tục đang nói ở lượt gần nhất trong lịch sử hội thoại và ghép khía cạnh người dùng hỏi vào để tạo standalone_question. Tuyệt đối không tự ý đổi sang thủ tục khác.
- province, ward: tỉnh/thành và xã/phường người dùng đã nói. Không có thì "".
- missing_information: thông tin còn thiếu mà thiếu thì câu trả lời có thể sai hẳn (thủ tục chia nhiều trường hợp có hồ sơ khác nhau). Không liệt kê thứ không thật sự cần.
- needs_clarification: true nếu thiếu thông tin như trên, hoặc intent là unknown. False nếu câu hỏi đã rõ nghĩa.
- clarifying_question: khi needs_clarification=true, một câu hỏi lại ngắn, thân thiện, gộp các thông tin còn thiếu. Khi needs_clarification=false thì BẮT BUỘC để chuỗi rỗng "".
- search_queries: 1-2 truy vấn tìm kiếm web tiếng Việt có dấu, 5-12 từ, gồm tên thủ tục + khía cạnh được hỏi (hồ sơ, các bước, lệ phí, thời gian, nơi nộp, nộp online) + năm {year}. Rỗng nếu intent là chitchat, out_of_scope, unknown.

Quy tắc:
- Hiểu theo ý định, không bắt từ khoá.
- Không bịa địa phương, hoàn cảnh người dùng chưa nói.
- Hỏi chung "cần giấy tờ gì / làm thế nào / có mất phí không" không cần biết tỉnh.
- Nếu trợ lý vừa hỏi lại và người dùng đã trả lời, dùng câu trả lời đó, không hỏi lại nữa. Khi đó standalone_question PHẢI nói về ĐÚNG thủ tục nêu trong câu hỏi lại, cộng thêm thông tin người dùng vừa cung cấp.
- Phân biệt chuyển chủ đề: Nếu người dùng hỏi một chủ đề hoặc thủ tục mới hoàn toàn (ví dụ: chuyển sang làm hộ chiếu, đăng ký kết hôn...) không liên quan đến thủ tục ở lượt trước, nhận diện độc lập theo thủ tục mới.
- Các lượt hội thoại mẫu phía trước chỉ minh hoạ cách trả JSON, KHÔNG phải lịch sử của người dùng này."""


def understand_user(question: str, history: list[dict], summary: str, profile: dict) -> str:
    parts = []
    known = profile_line(profile)
    if known:
        parts.append(f"Hồ sơ người dùng (ghi nhớ từ trước): {known}")
    if summary:
        parts.append(f"Tóm tắt hội thoại trước:\n{summary}")
    digest = history_digest(history)
    if digest:
        parts.append(f"Lịch sử gần nhất:\n{digest}")
    parts.append(f"Tin nhắn mới: {question}")
    return "\n\n".join(parts)


def _u(intent, standalone, *, province="", missing=None, clarify="", queries=None) -> dict:
    return {"intent": intent, "standalone_question": standalone, "province": province,
            "ward": "", "missing_information": missing or [],
            "needs_clarification": bool(clarify), "clarifying_question": clarify,
            "search_queries": queries or []}


def understand_examples(year: int) -> list[tuple[str, list[dict], dict]]:
    """(tin nhắn, lịch sử, JSON mong muốn) — đủ loại để mô hình nhỏ không chép một mẫu."""
    return [
        ("tui mun lam giay khai sinh cho be moi de thi can gi z", [],
         _u("birth_registration", "Đăng ký khai sinh cho trẻ mới sinh cần những giấy tờ gì?",
            queries=[f"hồ sơ đăng ký khai sinh cho trẻ mới sinh {year}",
                     "thủ tục đăng ký khai sinh trực tuyến"])),
        ("Tôi muốn đăng ký thường trú.", [],
         _u("permanent_residence", "Thủ tục đăng ký thường trú cần những gì?",
            missing=["đăng ký vào chỗ ở nào: nhà của mình, nhà thuê/mượn hay nhà người thân",
                     "tỉnh/thành phố"],
            clarify=("Bạn muốn đăng ký thường trú vào chỗ ở nào (nhà thuộc sở hữu của bạn, "
                     "nhà thuê/mượn hay nhà của người thân) và ở tỉnh/thành phố nào ạ?"))),
        ("thủ tục này có tốn phí ?",
         [{"role": "user", "content": "tôi muốn đăng kí giấy kết hôn", "kind": ""},
          {"role": "assistant", "content": "Hướng dẫn thủ tục đăng ký kết hôn tại UBND cấp xã.", "kind": "answer"}],
         _u("marriage_registration", "Thủ tục đăng ký kết hôn có mất phí không?",
            queries=[f"lệ phí đăng ký kết hôn mới nhất {year}", f"thủ tục đăng ký kết hôn có tốn phí không {year}"])),
        ("lệ phí thì sao",
         [{"role": "user", "content": "vậy còn giấy cấp phép xây dựng thì sao ?", "kind": ""},
          {"role": "assistant", "content": "Hồ sơ xin cấp giấy phép xây dựng nhà ở nộp tại UBND cấp xã.", "kind": "answer"}],
         _u("land_administration", "Lệ phí cấp giấy phép xây dựng nhà ở là bao nhiêu?",
            queries=[f"lệ phí cấp giấy phép xây dựng nhà ở {year}", f"mức thu lệ phí giấy phép xây dựng {year}"])),
        ("phí bn vậy",
         [{"role": "user", "content": "Mình thuê trọ ở Đà Nẵng, đăng ký tạm trú thế nào?", "kind": ""},
          {"role": "assistant", "content": "Mình đã gửi bạn các bước đăng ký tạm trú.", "kind": "answer"}],
         _u("temporary_residence", "Lệ phí đăng ký tạm trú tại Đà Nẵng là bao nhiêu?",
            province="Đà Nẵng",
            queries=[f"lệ phí đăng ký tạm trú {year}", "lệ phí đăng ký cư trú Đà Nẵng"])),
        ("chào bạn nha", [], _u("chitchat", "Chào bạn.")),
        ("kể cho mình nghe một câu chuyện cười đi", [],
         _u("out_of_scope", "Kể một câu chuyện cười.")),
        ("cái đó nộp ở đâu vậy", [],
         _u("unknown", "Nộp hồ sơ ở đâu?", missing=["thủ tục người dùng muốn làm"],
            clarify="Bạn đang muốn làm thủ tục gì (ví dụ khai sinh, tạm trú, căn cước...) để mình tra nơi nộp giúp bạn ạ?")),
    ]


def understand_example_messages(year: int) -> list[dict]:
    out = []
    for message, history, answer in understand_examples(year):
        out.append({"role": "user", "content": understand_user(message, history, "", {})})
        out.append({"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)})
    return out


GENERIC_CLARIFY = ("Bạn có thể nói rõ hơn bạn cần làm thủ tục gì (ví dụ: đăng ký khai "
                   "sinh, tạm trú, cấp căn cước...) và hoàn cảnh của bạn thế nào không?")


# ==========================================================================
# 1b. BỘ GÁC HỎI LẠI — một câu hỏi hẹp, dễ với mô hình nhỏ
# ==========================================================================
GATE_SCHEMA = {
    "type": "object",
    "properties": {"decision": {"type": "string",
                                "enum": ["search", "ask", "greeting", "other"]}},
    "required": ["decision"],
}

GATE_SYSTEM = """Bạn là bộ gác cửa cho trợ lý thủ tục hành chính Việt Nam. Đọc tin nhắn (và ngữ cảnh nếu có), chọn MỘT quyết định:
- "search" (MẶC ĐỊNH): tin nhắn có hỏi một điều cụ thể về thủ tục hành chính — hồ sơ, giấy tờ, các bước, lệ phí, thời hạn, nơi nộp, làm online, trường hợp đặc biệt (người nước ngoài, chưa kết hôn, bị mất giấy...), không làm có bị phạt không. Chưa biết tỉnh/thành vẫn là "search". Trường hợp đặc biệt đã nêu trong câu hỏi thì càng là "search".
- "ask": CHỈ khi không thể biết người dùng muốn làm thủ tục nào; hoặc người dùng chỉ nói "tôi muốn làm thủ tục X" mà KHÔNG hỏi điều gì cụ thể và thủ tục X chia nhiều trường hợp khác hẳn nhau (như thường trú). Thủ tục có hồ sơ chung rõ ràng (khai sinh, kết hôn, hộ chiếu, căn cước) thì là "search".
- "greeting": chỉ chào hỏi, cảm ơn, tạm biệt, hỏi bạn là ai — không nhờ làm việc gì.
- "other": NHỜ LÀM VIỆC ngoài thủ tục hành chính: làm thơ, viết văn, kể chuyện, dịch, viết code, giải toán, tư vấn kiện tụng/tranh chấp, hỏi tin tức...
Nếu ngữ cảnh đã cho biết đang nói về thủ tục nào thì câu hỏi nối tiếp ngắn ("nộp ở đâu?", "phí bao nhiêu?") là "search". Phân vân giữa "search" và "ask" thì chọn "search"."""


def gate_user(question: str, history: list[dict]) -> str:
    digest = history_digest(history, limit=4, chars=200)
    return (f"Ngữ cảnh gần nhất:\n{digest}\n\n" if digest else "") + f"Tin nhắn: {question}"


def gate_example_messages() -> list[dict]:
    examples = [
        ("Đăng ký tạm trú cần những giấy tờ gì?", [], "search"),
        ("Tôi muốn đăng ký thường trú.", [], "ask"),
        ("cam on ban nhieu", [], "greeting"),
        ("chào bạn nha", [], "greeting"),
        ("lam ho chieu online the nao", [], "search"),
        ("Người nước ngoài nhận con nuôi ở Việt Nam thì nộp hồ sơ ở đâu?", [], "search"),
        ("cái đó nộp ở đâu vậy", [], "ask"),
        ("Bị mất sổ đỏ thì xin cấp lại thế nào?", [], "search"),
        ("giải giúp mình bài toán 12 nhân 7", [], "other"),
        ("viết giúp mình một đoạn văn tả cảnh biển", [], "other"),
        ("thế lệ phí bao nhiêu?",
         [{"role": "user", "content": "Làm giấy khai sinh cho con cần gì?", "kind": ""},
          {"role": "assistant", "content": "Mình đã gửi bạn hồ sơ đăng ký khai sinh.", "kind": "answer"}],
         "search"),
        ("mình muốn làm giấy tờ", [], "ask"),
        ("t cần làm giấy khai sinh", [], "search"),
        ("tôi muốn làm hộ chiếu", [], "search"),
        ("Thành lập công ty TNHH một thành viên cần chuẩn bị gì?", [], "search"),
    ]
    out = []
    for message, history, decision in examples:
        out.append({"role": "user", "content": gate_user(message, history)})
        out.append({"role": "assistant", "content": json.dumps({"decision": decision})})
    return out


# ==========================================================================
# 2. SOẠN CÂU TRẢ LỜI TỪ EVIDENCE PACK
# ==========================================================================
def answer_system(today: str, knowledge_cutoff: str, pack: dict, profile: dict,
                  fix_notes: str = "") -> str:
    where = profile_line(profile) or "chưa rõ"
    retrieved = str(pack.get("retrieved_at", ""))[:10] or today
    text = f"""Bạn là trợ lý tư vấn thủ tục hành chính cho người dân Việt Nam. Hôm nay là {today}.
Kiến thức có sẵn của bạn chỉ tới khoảng {knowledge_cutoff}. Chỉ được dùng thông tin trong phần tài liệu bên dưới (vừa tra cứu ngày {retrieved}) để trả lời.

Quy tắc trả lời:
- Trả lời thẳng vào câu hỏi của người dân: ngắn gọn, tự nhiên, chính xác và đầy đủ nội dung theo tài liệu.
- Về lệ phí: Nêu con số cụ thể hoặc khoảng mức thu ghi trong tài liệu, hoặc nêu rõ miễn phí (0 đồng). Đối với thủ tục đăng ký kết hôn hay khai sinh trong nước của công dân Việt Nam, Luật Hộ tịch quy định MIỄN LỆ PHÍ (0 đồng); tuyệt đối không lấy mức lệ phí có yếu tố nước ngoài (1 triệu - 1,5 triệu) để trả lời cho công dân trong nước. Tuyệt đối không thoái thác bảo người dân tự liên hệ một cửa khi tài liệu đã có thông tin.
- Về hồ sơ giấy tờ: Liệt kê rõ ràng, đầy đủ từng loại giấy tờ cần chuẩn bị được nêu trong tài liệu. Tuyệt đối không trả lời cụt lủn 1 câu chỉ dẫn tên nghị định mà không nêu giấy tờ.
- Với câu hỏi Có/Không hoặc hỏi có phải nộp lại giấy tờ không: Khẳng định rõ ràng Có hoặc Không kèm quy định trong tài liệu.
- Hướng dẫn cơ quan tiếp nhận đúng chức năng tại địa phương (Bộ phận Một cửa UBND cấp xã / Công an cấp xã / Cổng Dịch vụ công Quốc gia).
- Tuyệt đối chỉ trả lời đúng thủ tục người dùng đang hỏi, bám sát từng chữ trong tài liệu, không tự ý bịa thêm giấy tờ ngoài tài liệu.
- TUYỆT ĐỐI KHÔNG sao chép lại quy tắc, lời nhắc hay chữ mẫu trong câu lệnh này. TUYỆT ĐỐI KHÔNG dùng chữ 'S#' mà phải ghi mã cụ thể như [S1], [S2].
- TUYỆT ĐỐI KHÔNG mở đầu bằng "Tài liệu trích dẫn:", "Trích dẫn tài liệu:", "Theo tài liệu:". Đi thẳng vào câu trả lời.
- Tiếng Việt chuẩn mực, xưng "bạn", tối đa khoảng 150 từ.

Địa phương của người dùng: {where}."""
    if fix_notes:
        text += ("\n\nLần trả lời trước bị lỗi, lần này phải sửa:\n" + fix_notes
                 + "\nKhông nhắc tới việc sửa lỗi hay kiểm tra trong câu trả lời.")
    return text + "\n\nTài liệu:\n\n" + format_evidence(pack)


def answer_user(question: str, standalone: str) -> str:
    q = standalone.strip() if standalone and standalone.strip() else question
    q_fold = fold(q) + " " + fold(question)
    if any(k in q_fold for k in ["le phi", "phi", "chi phi", "ton phi", "mat phi", "bao nhieu tien", "ton bao nhieu"]):
        focus = "\n\n(Chỉ trả lời tập trung vào mức lệ phí / chi phí / miễn phí theo tài liệu trên, nêu rõ số tiền cụ thể. Ghi mã tài liệu như [S1], [S2] sau mỗi ý.)"
    elif any(k in q_fold for k in ["ho so", "giay to", "mau don", "can gi", "thi sao", "nhu the nao", "nhu nao"]):
        focus = "\n\n(Liệt kê đầy đủ các thành phần giấy tờ, hồ sơ cần chuẩn bị theo tài liệu trên. Ghi mã tài liệu như [S1], [S2] sau mỗi ý.)"
    elif any(k in q_fold for k in ["bao lau", "thoi han", "may ngay", "bao nhieu ngay"]):
        focus = "\n\n(Chỉ trả lời tập trung vào thời hạn giải quyết theo tài liệu trên. Ghi mã tài liệu như [S1], [S2] sau mỗi ý.)"
    elif any(k in q_fold for k in ["o dau", "nop o dau", "den dau", "co quan nao"]):
        focus = "\n\n(Chỉ trả lời tập trung vào nơi nộp hồ sơ và cơ quan tiếp nhận theo tài liệu trên. Ghi mã tài liệu như [S1], [S2] sau mỗi ý.)"
    elif any(k in q_fold for k in ["dong cua", "dong tiem", "tra giay phep", "nop lai giay"]):
        focus = "\n\n(Khẳng định rõ có phải nộp lại giấy tờ theo tài liệu trên không. Ghi mã tài liệu như [S1], [S2] sau mỗi ý.)"
    else:
        focus = "\n\n(Chỉ dùng tài liệu đã cho; ghi số tài liệu như [S1], [S2] sau mỗi ý.)"
    return f"{q}{focus}"


def format_evidence(pack: dict) -> str:
    blocks = []
    for s in pack.get("sources") or []:
        meta = [s.get("domain") or "", TRUST_LABEL.get(s.get("trust", ""), "")]
        if s.get("published_at"):
            meta.append(f"đăng {str(s['published_at'])[:10]}")
        head = f"[{s['id']}] {s.get('title') or ''} ({' · '.join(m for m in meta if m)})"
        blocks.append(f"{head}\n{s.get('content') or s.get('snippet') or ''}")
    return "\n\n".join(blocks)


# Nhãn khung prompt — xuất hiện trong câu trả lời nghĩa là mô hình đang chép prompt.
ECHO_MARKERS = ["Tài liệu:", "Địa phương của người dùng", "Tin nhắn mới:", "Cách trả lời:",
                "HỒ SƠ NGƯỜI DÙNG", "TIN NHẮN GỐC", "BẰNG CHỨNG", "QUY TẮC", "URL:",
                "Lần trả lời trước bị lỗi", "bản nháp", "kiểm chứng", "tài liệu đã cho;",
                "người nước ngoài, nhà tu hành", "chứ không phải 120 ngày", "120 ngày như bạn hỏi",
                "1% tổng giá trị", "Tài liệu trích dẫn", "Trích dẫn tài liệu", "Tài liệu tham khảo",
                "gồm những gì?"]


# ==========================================================================
# 3. KIỂM CHỨNG
# ==========================================================================
VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "answers_question": {"type": "boolean"},
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "wrong_situation": {"type": "boolean"},
        "evidence_sufficient": {"type": "boolean"},
        "better_search_query": {"type": "string"},
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "explanation": {"type": "string"},
    },
    "required": ["answers_question", "unsupported_claims", "wrong_situation",
                 "evidence_sufficient", "better_search_query", "verdict", "explanation"],
}


def verify_system(today: str) -> str:
    return f"""Bạn là người kiểm chứng nghiêm khắc cho câu trả lời về thủ tục hành chính. Hôm nay là {today}.
Được cho: câu hỏi, tài liệu tra cứu, bản nháp câu trả lời. Kiểm tra lần lượt:
1. answers_question: bản nháp có trả lời đúng điều người dùng hỏi không? Nếu người dùng hỏi xác nhận ("... đúng không?") mà câu trả lời khẳng định sai so với quy định trong tài liệu (ví dụ: tài liệu nói 60 ngày nhưng câu trả lời lại đồng ý là 120 ngày) thì answers_question=false.
2. unsupported_claims: liệt kê nguyên văn từng chi tiết cụ thể (giấy tờ, lệ phí, thời hạn, cơ quan, số văn bản, bước làm) KHÔNG tìm thấy trong tài liệu hoặc hướng dẫn cơ quan sai chức năng (ví dụ: làm căn cước tại cơ sở y tế / bệnh viện). Không có thì [].
3. wrong_situation: bản nháp có áp dụng nhầm thủ tục của trường hợp khác (ngành nghề đặc thù như cầm đồ khi người dùng chỉ hỏi đóng tiệm thông thường, người nước ngoài, nhà tu hành...) hoặc quy định cũ đã bị thay thế theo tài liệu không?
4. evidence_sufficient: tài liệu có đủ để trả lời câu hỏi không? Nếu không, better_search_query = một truy vấn tìm kiếm tiếng Việt tốt hơn; ngược lại "".
5. verdict: "PASS" khi answers_question=true, unsupported_claims rỗng và wrong_situation=false. Ngược lại "FAIL".
Nếu bản nháp hướng dẫn cơ quan giải quyết hoàn toàn phi lý, không có thẩm quyền đối với thủ tục (như làm căn cước tại cơ sở y tế/bệnh viện), BẮT BUỘC coi là unsupported_claims và đánh FAIL. Không coi là lỗi: lời chào lịch sự, câu "tài liệu chưa nêu rõ", suy luận hợp lý bám sát tài liệu.
explanation: 1 câu tiếng Việt."""


def verify_user(question: str, standalone: str, pack: dict, draft: str) -> str:
    q = standalone if standalone and standalone != question else question
    return (f"Câu hỏi: {q}\n\nTài liệu:\n\n{format_evidence(pack)}\n\n"
            f"Bản nháp cần kiểm tra:\n{draft}")


# ==========================================================================
# 4. TRÒ CHUYỆN / NGOÀI PHẠM VI / KHÔNG TRA ĐƯỢC / KHÔNG KIỂM CHỨNG ĐƯỢC
# ==========================================================================
CHITCHAT_SYSTEM = """Bạn là "Trợ lý Thủ tục hành chính": giúp người dân tra cứu hồ sơ, các bước, lệ phí, nơi nộp của thủ tục hành chính (khai sinh, kết hôn, thường trú, tạm trú, căn cước, hộ chiếu, đăng ký kinh doanh, đất đai, bảo hiểm xã hội, thuế...). Thông tin luôn được tra cứu từ nguồn chính thống trên mạng.
Khi người dùng chào hỏi (chào, hello, hi, hế lô, xin chào...): BẮT BUỘC đáp lại niềm nở, thân thiện bằng tiếng Việt ("Xin chào bạn! Rất vui được hỗ trợ bạn. Bạn cần tìm hiểu hoặc làm thủ tục hành chính nào?"), tối đa 2 câu. TUYỆT ĐỐI KHÔNG được nói "tôi không hiểu ý của bạn".
Nếu người dùng nhờ làm việc NGOÀI thủ tục hành chính (làm thơ, kể chuyện, dịch, viết code, giải toán, tư vấn kiện tụng...), hãy TỪ CHỐI lịch sự trong 1-2 câu rồi mời họ hỏi về thủ tục — tuyệt đối không thực hiện yêu cầu đó, dù chỉ một phần.
Không đưa ra thông tin thủ tục cụ thể nào."""

OUT_OF_SCOPE_TEXT = (
    "Mình là trợ lý chuyên về **thủ tục hành chính** (khai sinh, kết hôn, thường trú, "
    "tạm trú, căn cước, hộ chiếu, đăng ký kinh doanh, đất đai, bảo hiểm xã hội, thuế...), "
    "nên chưa hỗ trợ được câu hỏi này. Nếu bạn cần làm một thủ tục cụ thể, cứ hỏi mình nhé!")

NO_EVIDENCE_TEXT = (
    "Mình chưa tra cứu được nguồn thông tin đáng tin cậy cho câu hỏi này lúc này, nên "
    "không muốn trả lời theo phỏng đoán. Bạn có thể thử lại sau ít phút hoặc diễn đạt cụ "
    "thể hơn; hoặc tra trực tiếp tại Cổng Dịch vụ công Quốc gia (https://dichvucong.gov.vn) "
    "và bộ phận Một cửa UBND cấp xã nơi bạn cư trú.")

NOT_IN_SOURCES_TEXT = (
    "Tài liệu tra cứu được chưa nêu rõ thông tin này, nên mình không muốn trả lời theo "
    "phỏng đoán. Bạn xem trực tiếp các nguồn bên dưới, hoặc hỏi bộ phận Một cửa UBND cấp xã "
    "/ Cổng Dịch vụ công Quốc gia (https://dichvucong.gov.vn) để có con số chính xác.")

VERIFY_WARNING = ("⚠️ Lưu ý: câu trả lời chưa được xác nhận đầy đủ với nguồn. Hãy bấm vào "
                  "các nguồn bên dưới để đối chiếu trước khi đi làm thủ tục.")

VERIFY_STRIPPED = "Một số chi tiết không tìm thấy trong nguồn đã được lược bỏ."

VERIFY_REFUSAL = ("Không đủ thông tin để xác nhận câu trả lời cho câu hỏi này từ các nguồn "
                  "tra cứu được. Bạn có thể xem trực tiếp các nguồn bên dưới, hoặc hỏi bộ "
                  "phận Một cửa UBND cấp xã / Cổng Dịch vụ công Quốc gia.")


# ==========================================================================
# 5. TÓM TẮT HỘI THOẠI
# ==========================================================================
SUMMARY_SYSTEM = (
    "Bạn là công cụ tóm tắt hội thoại về thủ tục hành chính.\n"
    "Tóm tắt thật ngắn, giữ bằng được:\n"
    "1. Thủ tục người dân đang hỏi và mục đích của họ.\n"
    "2. Thông tin cá nhân họ đã cung cấp (tỉnh/thành, xã/phường, hoàn cảnh, giấy tờ đang có).\n"
    "3. Những điều đã được trả lời (kèm con số quan trọng) và câu hỏi còn đang treo.\n"
    "Bỏ lời chào và câu xã giao. Viết gạch đầu dòng, tối đa 120 từ."
)


# ==========================================================================
# tiện ích dựng ngữ cảnh
# ==========================================================================
_CITE_RE = re.compile(r"\s*\[(?:S\d+\s*[,;]?\s*)+\]", re.IGNORECASE)


def strip_citations(text: str) -> str:
    """[S1] của lượt trước trỏ vào Evidence Pack CŨ — bỏ đi để mô hình không trích nhầm."""
    text = (text or "").split(VERIFY_WARNING)[0]
    return _CITE_RE.sub("", text).strip()


def profile_line(profile: dict | None) -> str:
    if not profile:
        return ""
    bits = []
    if profile.get("province"):
        bits.append(f"tỉnh/thành {profile['province']}")
    if profile.get("ward"):
        bits.append(f"xã/phường {profile['ward']}")
    return ", ".join(bits)


def history_digest(history: list[dict], limit: int = 6, chars: int = 400) -> str:
    """Lượt người dùng giữ dài (mang chủ đề); lượt trợ lý cắt ngắn — câu trả lời
    dài nhắc tới thủ tục khác làm mô hình nhỏ hiểu nhầm câu hỏi nối tiếp."""
    lines = []
    for m in history[-limit:]:
        if m["role"] == "user":
            who, limit_chars = "Người dùng", chars
        elif m.get("kind") == "clarify":
            who, limit_chars = "Trợ lý (hỏi lại)", chars
        else:
            who, limit_chars = "Trợ lý", min(chars, 160)
        content = strip_citations(m.get("content", "")).replace("\n", " ")
        lines.append(f"{who}: {content[:limit_chars]}")
    return "\n".join(lines)


def history_messages(summary: str, history: list[dict], max_turns: int = 3) -> list[dict]:
    out = []
    if summary:
        out.append({"role": "user", "content": f"(Tóm tắt cuộc trò chuyện trước đó)\n{summary}"})
        out.append({"role": "assistant", "content": "Mình đã nắm được bối cảnh."})
    recent = history[-(max_turns * 2):] if max_turns else history
    for m in recent:
        role = m["role"]
        content = strip_citations(m.get("content", "")).strip()
        if role == "assistant":
            # Chỉ giữ câu mở đầu ngắn gọn, TUYỆT ĐỐI KHÔNG đưa gạch đầu dòng / các bước / hồ sơ của thủ tục cũ vào
            # để tránh mô hình nhỏ (1.5B) chép lại sang thủ tục mới
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            first_line = ""
            for l in lines:
                l_clean = re.sub(r"^(từ tài liệu được cung cấp|theo tài liệu|dưới đây là|hướng dẫn cụ thể)[\s\:\-]*", "", l, flags=re.IGNORECASE).strip()
                if l_clean and not l_clean.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "#")):
                    first_line = l_clean
                    break
            if not first_line:
                first_line = "Tôi đã cung cấp thông tin thủ tục theo tài liệu."
            out.append({"role": "assistant", "content": first_line[:140]})
        else:
            out.append({"role": "user", "content": content[:250]})
    return out

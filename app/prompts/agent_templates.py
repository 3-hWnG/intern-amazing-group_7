"""Prompt của luồng agent (v6).

Khác biệt cốt lõi so với prompts/templates.py (luồng tiers cũ):

    Bản cũ:  "CHỈ dùng thông tin trong phần TÀI LIỆU."
             -> hỏi gì cũng bị giam trong dataset. Hỏi "thủ đô Pháp ở đâu"
                mà lỡ bị router bẻ vào luồng LUAT thì mô hình cũng phải tra
                bảng thủ tục hành chính rồi xin lỗi.

    Bản này: "Dùng TÀI LIỆU cho dữ kiện có trong đó. Ngoài ra cứ trả lời
              bình thường như một trợ lý."
             -> tài liệu là NGUỒN THAM KHẢO, không phải hàng rào.

Ràng buộc duy nhất còn giữ nguyên độ cứng: KHÔNG bịa số tiền / số ngày / tên
cơ quan. Cái đó do core/factcheck.py kiểm chứng bằng luật, không phải bằng
lời dặn trong prompt.
"""

from __future__ import annotations

import json
import re

from domain.text import fold

# ==========================================================================
# 1. CHỌN CÔNG CỤ
# ==========================================================================

DECISION_SYSTEM = (
    "Bạn là bộ định tuyến của một trợ lý AI. Nhiệm vụ DUY NHẤT: chọn một công "
    "cụ để lấy thông tin, hoặc không chọn gì.\n"
    "CHỈ trả về JSON, không giải thích, không viết câu trả lời cho người dùng.\n"
    "Định dạng: {\"tool\": \"<tên công cụ>\", \"query\": \"<từ khoá tra cứu>\", "
    "\"row_id\": <số hoặc null>}\n"
    "\n"
    "CÔNG CỤ:\n"
    "- search_procedures: tra bảng thủ tục hành chính nội bộ (hồ sơ, lệ phí, "
    "thời gian, nơi nộp của một thủ tục). Dùng khi người dân hỏi về thủ tục, "
    "giấy tờ, đăng ký, cấp/đổi/cấp lại.\n"
    "- get_procedure: lấy lại ĐÚNG một thủ tục đã nói tới, khi biết row_id. "
    "Dùng cho câu hỏi tiếp nối kiểu \"lệ phí bao nhiêu?\", \"mất bao lâu?\".\n"
    "- search_attachments: tìm trong TỆP người dùng vừa đính kèm ở cuộc trò "
    "chuyện này. Chỉ dùng khi câu hỏi nhắc tới tệp đó hoặc nội dung trong đó.\n"
    "- search_web: tra trên mạng. Dùng cho MỌI thông tin thay đổi theo thời "
    "gian mà bảng nội bộ không có: giá vàng, tỷ giá, thời tiết, tin tức, mức "
    "phạt, văn bản luật mới, hoặc thủ tục KHÔNG có trong bảng nội bộ. Hễ câu "
    "hỏi có chữ \"hôm nay\", \"hiện tại\", \"mới nhất\" thì gần như chắc "
    "chắn là công cụ này.\n"
    "- none: không cần tra gì. Dùng cho chào hỏi, cảm ơn, hỏi về chính bạn, "
    "câu hỏi kiến thức phổ thông, hoặc khi lịch sử hội thoại đã đủ thông tin.\n"
)

DECISION_EXAMPLES = [
    ("Làm giấy khai sinh cho con cần giấy tờ gì?",
     {"tool": "search_procedures", "query": "đăng ký khai sinh", "row_id": None}),
    ("Thủ đô nước Pháp là gì?",
     {"tool": "none", "query": "", "row_id": None}),
    ("Vượt đèn đỏ phạt bao nhiêu tiền?",
     {"tool": "search_web", "query": "mức phạt vượt đèn đỏ", "row_id": None}),
    ("Giá vàng hôm nay bao nhiêu?",
     {"tool": "search_web", "query": "giá vàng hôm nay", "row_id": None}),
    ("Tỷ giá USD hôm nay thế nào?",
     {"tool": "search_web", "query": "tỷ giá USD hôm nay", "row_id": None}),
    ("Cảm ơn bạn nhé",
     {"tool": "none", "query": "", "row_id": None}),
    ("Trong file tôi vừa gửi có bao nhiêu dòng về hộ tịch?",
     {"tool": "search_attachments", "query": "hộ tịch", "row_id": None}),
]


def decision_user(question: str, manifest: str, digest: str = "",
                  current: tuple[int, str] | None = None) -> str:
    """Prompt chọn công cụ. Ngắn hết mức — mô hình nhỏ càng đọc nhiều càng loạn."""
    parts = []
    if manifest:
        parts.append(f"TÀI LIỆU CÓ SẴN:\n{manifest}")
    if current:
        row_id, name = current
        parts.append(f"THỦ TỤC ĐANG NÓI TỚI: {name} (row_id={row_id})")
    if digest:
        parts.append(f"HỘI THOẠI GẦN ĐÂY:\n{digest}")

    examples = "\n".join(
        f"Câu hỏi: {q}\nJSON: {json.dumps(a, ensure_ascii=False)}"
        for q, a in DECISION_EXAMPLES
    )
    parts.append(f"VÍ DỤ:\n{examples}")
    parts.append(f"Câu hỏi: {question}\nJSON:")
    return "\n\n".join(parts)


DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {
            "type": "string",
            "enum": ["search_procedures", "get_procedure",
                     "search_attachments", "search_web", "none"],
        },
        "query": {"type": "string"},
        "row_id": {"type": ["integer", "null"]},
    },
    "required": ["tool"],
}


# ==========================================================================
# 2. TRẢ LỜI
# ==========================================================================

# Có bằng chứng trong tay.
SYSTEM_GROUNDED = (
    "Bạn là trợ lý thủ tục hành chính của Bộ phận Một cửa. Nói chuyện tự "
    "nhiên, thân thiện, xưng \"mình\".\n"
    "QUY TẮC:\n"
    "1. Phần TÀI LIỆU bên dưới là nguồn dữ kiện. Mọi số tiền, số ngày, tên cơ "
    "quan, tên giấy tờ phải lấy từ đó — TUYỆT ĐỐI không tự nghĩ ra số khác.\n"
    "2. Nhưng bạn KHÔNG bị giam trong tài liệu. Vẫn dùng lịch sử hội thoại và "
    "hiểu biết chung để giải thích, sắp xếp, khuyên người dân nên làm gì "
    "trước làm gì sau.\n"
    "3. Dataset viết tắt và lộn xộn — hãy viết lại cho người dân dễ đọc: gạch "
    "đầu dòng, bỏ chữ thừa, gộp ý trùng. Đừng chép nguyên xi cả ô Excel.\n"
    "4. Tài liệu THIẾU thông tin được hỏi thì nói thẳng là chưa có và hướng "
    "người dân tới Bộ phận Một cửa. Không suy đoán.\n"
    "5. Không chào hỏi lại, không nhắc lại câu hỏi, không nói \"theo tài liệu\".\n"
    "6. TÀI LIỆU có thể chứa NHIỀU thủ tục. Chỉ trả lời về thủ tục PHÙ HỢP "
    "NHẤT với câu hỏi. TUYỆT ĐỐI không gộp nhiều thủ tục khác nhau thành một "
    "danh sách — người dân sẽ làm sai.\n"
    "7. Nếu TÀI LIỆU ghi độ khớp thấp, hoặc không thủ tục nào đúng thứ người "
    "dân hỏi: nói thẳng \"thủ tục này chưa có trong dữ liệu của mình\" rồi "
    "hướng họ tới Bộ phận Một cửa. ĐỪNG cố trả lời bằng thủ tục gần giống."
)

# Có CẢ bản ghi nội bộ lẫn kết quả web -> số liệu lấy từ nội bộ.
MIXED_CLAUSE = (
    "\n9. TÀI LIỆU có cả bản ghi nội bộ (dòng bắt đầu bằng [id=...]) lẫn kết "
    "quả tra web (dòng bắt đầu bằng [Nguồn: ...]). MỌI SỐ LIỆU — lệ phí, thời "
    "gian, nơi nộp — phải lấy từ BẢN GHI NỘI BỘ. Kết quả web chỉ dùng để giải "
    "thích thêm. Nếu web nói một con số khác với bản ghi nội bộ, TIN BẢN GHI "
    "NỘI BỘ và nói rõ là trên mạng có thông tin khác.\n"
    "10. Kết quả web có thể nói về một thủ tục KHÁC gần giống (ví dụ thẻ tạm "
    "trú cho người nước ngoài khác hẳn gia hạn tạm trú trong nước). Đọc kỹ "
    "tiêu đề nguồn; không thuộc đúng thủ tục đang hỏi thì BỎ QUA."
)

# Có bằng chứng VÀ câu hỏi nhắm vào một trường cụ thể -> trích nguyên văn.
EXACT_CLAUSE = (
    "\n8. Câu hỏi này nhắm vào MỘT thông tin cụ thể ({facet}). Trích NGUYÊN VĂN "
    "phần đó từ TÀI LIỆU, đặt lên dòng đầu tiên, không diễn đạt lại, không làm "
    "tròn, không rút gọn. Giải thích thêm (nếu cần) ở các dòng sau."
)

# Không có bằng chứng — trợ lý bình thường.
SYSTEM_OPEN = (
    "Bạn là trợ lý ảo thân thiện, chuyên về thủ tục hành chính Việt Nam nhưng "
    "vẫn trò chuyện và giúp đỡ bình thường như mọi trợ lý AI khác. Xưng "
    "\"mình\".\n"
    "QUY TẮC:\n"
    "1. TRẢ LỜI CÂU HỎI. Đừng từ chối, đừng xin lỗi dài dòng, đừng nói \"tôi "
    "không có khả năng\".\n"
    "2. Lịch sử hội thoại đã có thông tin được hỏi (lệ phí, thời gian, hồ "
    "sơ...) thì DÙNG LẠI ĐÚNG thông tin đó.\n"
    "3. Nói về một thủ tục hành chính mà bạn KHÔNG có dữ liệu: không bịa con "
    "số, nhắc người dân xác nhận tại Bộ phận Một cửa hoặc Cổng Dịch vụ công "
    "Quốc gia.\n"
    "4. Câu hỏi ngoài lĩnh vực hành chính (đời sống, kiến thức chung, trò "
    "chuyện): trả lời tự nhiên và ngắn gọn, không cần rào đón.\n"
    "5. Ngắn gọn, không nhắc lại câu hỏi."
)

# Bằng chứng lấy từ web.
SYSTEM_WEB_AGENT = (
    "Bạn là trợ lý thủ tục hành chính. Xưng \"mình\".\n"
    "QUY TẮC:\n"
    "1. Tóm tắt phần KẾT QUẢ TRA CỨU bên dưới. Không thêm số liệu ngoài đó.\n"
    "2. Ngắn gọn, gạch đầu dòng, không nhắc lại câu hỏi.\n"
    "3. Kết thúc bằng một dòng nhắc người dân xác nhận lại tại cơ quan có "
    "thẩm quyền."
)


def user_answer(question: str, evidence: str) -> str:
    if not evidence:
        return f"CÂU HỎI: {question}"
    return f"TÀI LIỆU:\n---\n{evidence}\n---\n\nCÂU HỎI CỦA CÔNG DÂN: {question}"


def user_retry(question: str, evidence: str, problem: str) -> str:
    return (f"TÀI LIỆU:\n---\n{evidence}\n---\n\n"
            f"Câu trả lời trước đã sai: {problem}.\n"
            f"Viết lại, CHỈ dùng số liệu có trong TÀI LIỆU.\n\n"
            f"CÂU HỎI: {question}")


# ==========================================================================
# 3. "Câu hỏi này có đòi một con số chính xác không?"
# ==========================================================================
# Đây là chỗ duy nhất bật chế độ trích nguyên văn. Mặc định KHÔNG bật, vì
# dataset viết xấu — in thẳng ra thì đọc như bảng tính.

# Mỗi trường có hai loại tín hiệu:
#   strong = cách HỎI ("ở đâu", "bao lâu", "cần gì") — gần như chắc chắn là
#            câu hỏi nhắm vào trường đó
#   weak   = DANH TỪ trơ ("hồ sơ", "lệ phí") — có thể chỉ đang nhắc tới, ví dụ
#            "nộp HỒ SƠ khai sinh Ở ĐÂU" hỏi nơi nộp chứ không hỏi hồ sơ
_FACETS = [
    ("lệ phí",
     ["le phi bao nhieu", "phi bao nhieu", "mat bao nhieu tien", "ton bao nhieu",
      "het bao nhieu tien", "chi phi bao nhieu", "gia bao nhieu", "co mat phi khong",
      "co mien phi khong", "ton nhieu tien", "ton bao nhieu tien", "ton kem khong",
      "co ton tien khong", "mat tien khong", "co mat tien khong"],
     ["le phi", "phi", "chi phi", "mien phi", "bao nhieu tien", "ton tien",
      "ton kem"]),

    ("thời gian giải quyết",
     ["bao lau", "mat bao lau", "trong bao lau", "may ngay", "bao nhieu ngay",
      "khi nao xong", "khi nao co", "han giai quyet", "mat may ngay"],
     ["thoi gian", "thoi han"]),

    ("thành phần hồ sơ",
     ["can gi", "can nhung gi", "can nhung giay to gi", "gom gi", "gom nhung gi",
      "chuan bi gi", "can chuan bi gi", "giay to gi", "ho so gom", "ho so can gi",
      "mang theo gi", "nop nhung gi"],
     ["ho so", "giay to", "thanh phan ho so"]),

    ("nơi nộp",
     ["o dau", "nop o dau", "lam o dau", "nop tai dau", "den dau", "tai dau",
      "nop cho ai", "co quan nao"],
     ["dia diem", "noi nop", "noi tiep nhan"]),
]


def _word_re(items):
    alts = "|".join(sorted((re.escape(x) for x in items), key=len, reverse=True))
    return re.compile(rf"(?<![a-z0-9])(?:{alts})(?![a-z0-9])")


_FACET_RES = [(name, _word_re(strong), _word_re(weak))
              for name, strong, weak in _FACETS]


def wants_exact(question: str) -> str:
    """Trả về tên trường được hỏi, hoặc "" nếu là câu hỏi mở.

    "Lệ phí làm căn cước bao nhiêu?"  -> "lệ phí"          (trích nguyên văn)
    "Nộp hồ sơ khai sinh ở đâu?"      -> "nơi nộp"         (KHÔNG phải "hồ sơ":
                                        "ở đâu" là cách hỏi, "hồ sơ" chỉ là
                                        danh từ đi ngang qua)
    "Con tôi mới sinh phải làm gì?"   -> ""                (viết lại cho dễ đọc)
    """
    folded = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", fold(question or ""))).strip()
    strong = [name for name, rx, _ in _FACET_RES if rx.search(folded)]
    if len(strong) == 1:
        return strong[0]
    if strong:
        return ""                       # hỏi nhiều thứ cùng lúc -> đừng ép
    weak = [name for name, _, rx in _FACET_RES if rx.search(folded)]
    return weak[0] if len(weak) == 1 else ""


def system_for(evidence_kind: str, facet: str = "") -> str:
    """Chọn prompt hệ thống theo loại bằng chứng đang có."""
    if evidence_kind == "web":
        return SYSTEM_WEB_AGENT
    if evidence_kind in ("procedures", "attachments", "mixed"):
        base = SYSTEM_GROUNDED
        if facet:
            base += EXACT_CLAUSE.format(facet=facet)
        if evidence_kind == "mixed":
            base += MIXED_CLAUSE
        return base
    return SYSTEM_OPEN

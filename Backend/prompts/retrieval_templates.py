"""Prompt của HỆ THỐNG 2 (CSDL nội bộ). Tách khỏi `templates.py` của Hệ thống 1.

Ba vai — giữa chúng là code thuần, không có LLM:

    LLM 1  extract   CHỈ khi tra từ khoá trượt: câu hỏi -> {primary_keyword, …}
    LLM 2  chat      chưa có bảng: chào hỏi, cảm ơn — cấm nêu luật (CHAT_SYSTEM)
    LLM 2  care      đã có bảng: hỏi tiếp, CHỈ trong phạm vi bảng (CARE_SYSTEM)

`domain` của LLM 1 phải CHỌN trong danh sách lĩnh vực có thật lấy từ CSDL, và
chỉ dùng để xếp hạng (xem retrieval.search_in_domain).
"""

from __future__ import annotations

# ==========================================================================
# LLM 1 — RÚT KHOÁ TRA CỨU
# ==========================================================================
EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        # Tên thủ tục viết lại cho ĐẦY ĐỦ, đúng chính tả, bỏ teencode.
        "primary_keyword": {"type": "string"},
        # PHẢI là một tên trong danh sách được đưa, hoặc "" nếu không chắc.
        "domain": {"type": "string"},
        # Tỉnh/thành, độ tuổi, tư cách… — dùng để xếp hạng, KHÔNG dùng để lọc.
        "entities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["primary_keyword", "domain", "entities"],
}

EXTRACT_SYSTEM = """Bạn là bộ rút khoá tra cứu cho trợ lý thủ tục hành chính Việt Nam.
Nhiệm vụ DUY NHẤT: đọc câu hỏi của người dân và viết lại thành khoá tra cứu cơ sở dữ liệu. TUYỆT ĐỐI KHÔNG trả lời câu hỏi, KHÔNG giải thích thủ tục.

primary_keyword — tên thủ tục viết ĐẦY ĐỦ và ĐÚNG CHÍNH TẢ tiếng Việt có dấu:
- Bỏ teencode và viết tắt: "dk" -> "đăng ký", "kh" -> "khai sinh", "t" -> "tôi", "ko" -> "không".
- Bỏ mọi từ chỉ người nói và địa phương: "tôi", "mình", "người Bình Định", "ở Huế".
- Chỉ giữ TÊN VIỆC cần làm. Ví dụ: "t người bình định muốn dk kết hôn" -> "đăng ký kết hôn".
- Không thêm chữ "thủ tục" ở đầu.

domain — lĩnh vực của thủ tục. BẮT BUỘC chọn CHÍNH XÁC một tên trong danh sách người dùng đưa, chép lại nguyên văn từng ký tự. Nếu không chắc chắn, để chuỗi rỗng "".

entities — các chi tiết phụ người dân có nhắc: tỉnh/thành, độ tuổi, tư cách (công dân, doanh nghiệp), trường hợp đặc biệt (có yếu tố nước ngoài, lưu động). Không có thì để mảng rỗng.

Chỉ trả JSON đúng schema, không viết gì thêm."""


def extract_user(question: str, domains: list[str], history: list[dict] | None = None) -> str:
    """Câu hỏi + DANH SÁCH lĩnh vực có thật để mô hình chọn, không tự bịa."""
    parts = []
    if history:
        recent = "\n".join(f"{m['role']}: {m['content'][:150]}" for m in history[-2:])
        parts.append(f"Ngữ cảnh trước đó (chỉ để hiểu câu hỏi, không tra lại):\n{recent}")
    listed = "\n".join(f"- {d}" for d in domains)
    parts.append(f"Danh sách lĩnh vực có trong cơ sở dữ liệu (chọn ĐÚNG MỘT, chép nguyên văn):\n{listed}")
    parts.append(f"Câu hỏi của người dân:\n{question}")
    return "\n\n".join(parts)


def retry_user(question: str, domains: list[str], tried: list[str]) -> str:
    """Lần sinh lại: nói thẳng khoá nào đã thử và KHÔNG có trong CSDL."""
    failed = ", ".join(f'"{t}"' for t in tried if t)
    return (f"{extract_user(question, domains)}\n\n"
            f"LƯU Ý: các khoá đã thử đều KHÔNG có trong cơ sở dữ liệu: {failed}.\n"
            "Hãy viết lại primary_keyword theo cách khác — dùng từ ngữ hành chính "
            "chính thức hơn, hoặc rộng hơn (bỏ bớt chi tiết phụ).")


# ==========================================================================
# LLM 2 — CHĂM SÓC KHÁCH HÀNG TRÊN BẢNG ĐÃ TRẢ
# ==========================================================================
CARE_SYSTEM = """Bạn là nhân viên chăm sóc người dân của trợ lý Thủ tục hành chính.

Người dân đã nhận được BẢNG THÔNG TIN đầy đủ về một thủ tục (bảng nằm ngay dưới đây). Việc của bạn là trả lời các câu hỏi tiếp theo của họ VỀ ĐÚNG THỦ TỤC ĐÓ.

LUẬT BẮT BUỘC:
1. Chỉ dùng thông tin có trong bảng. TUYỆT ĐỐI không thêm con số, thời hạn, loại giấy tờ, mức phí nào không có trong bảng.
2. Ô ghi "CHƯA CÓ THÔNG TIN", hoặc bảng không nói tới điều người dân hỏi -> nói thẳng: "Hiện chưa có thông tin về điều này" rồi mời họ hỏi cơ quan tiếp nhận hoặc bấm nút Web search. TUYỆT ĐỐI không suy ra "miễn phí", "không cần giấy tờ" hay "không có" từ một ô chưa có thông tin.
3. Trả lời ĐÚNG điều người dân hỏi, không kể thêm các mục khác của bảng. Tối đa 4 câu. Nếu người dân xin tóm tắt thì tối đa 5 gạch đầu dòng ngắn, chỉ tóm tắt đúng phần họ xin.
4. Chép con số và đơn vị đúng như bảng. Bảng không ghi đơn vị thì KHÔNG tự thêm "ngày" hay "giờ".
5. Không chào hỏi mở đầu, không kết bằng lời mời chung chung. Không bịa link.
6. Viết tiếng Việt có dấu."""


def care_user(question: str, table_text: str, previous: str = "") -> str:
    before = (f"Câu hỏi trước đó của người dân (chỉ để hiểu ngữ cảnh): {previous}\n\n"
              if previous else "")
    return (f"BẢNG THÔNG TIN THỦ TỤC (nguồn sự thật duy nhất — có thể chỉ gồm các mục liên quan):\n"
            f"────────────────────────────────\n{table_text}\n"
            f"────────────────────────────────\n\n"
            f"{before}Câu hỏi của người dân (chỉ trả lời đúng câu này):\n{question}")


def rewrite_user(request: str, table_text: str, previous_q: str, previous_answer: str) -> str:
    """Người dân muốn VIẾT LẠI câu trả lời trước ("ngắn hơn nữa", "chi tiết hơn")."""
    return (f"BẢNG THÔNG TIN THỦ TỤC (nguồn sự thật duy nhất):\n"
            f"────────────────────────────────\n{table_text}\n"
            f"────────────────────────────────\n\n"
            f"Câu hỏi trước của người dân: {previous_q}\n\n"
            f"Câu trả lời trước của trợ lý (văn bản cần viết lại):\n\"\"\"\n{previous_answer}\n\"\"\"\n\n"
            f"Người dân yêu cầu: {request}\n"
            "Hãy VIẾT LẠI câu trả lời trước theo đúng yêu cầu này. Không thêm thông tin "
            "ngoài bảng, không giải thích bạn đang làm gì.")


# --- Bộ gác `newProcedure` — ĐÃ BỎ PHẦN LLM ---------------------------------
# Proposal đề xuất "hỏi con LLM nhận diện newProcedure". Đã làm, đã đo, đã bỏ:
#
#   Qwen2.5 1.5B trả is_new_procedure=true cho 9/9 câu thử — kể cả
#   "lệ phí bao nhiêu tiền?" và "cảm ơn bạn". Tức là phân biệt 0%.
#   Dùng nó thì MỌI câu hỏi tiếp đều bị đá sang ô chat mới, LLM 2 không bao
#   giờ được chạy.
#
# Thay bằng luật dựa trên chính CSDL (`retrieval.is_other_procedure()`): "câu
# hỏi này có khớp CHẮC CHẮN vào một thủ tục KHÁC không?" — đo lại: hỏi tiếp
# 9/9 đúng, thủ tục mới 4/4 đúng. Giữ mục này để người sau khỏi làm lại.
# Khi nào fine-tune xong (Proposal, fine-tune mục 3) thì đo lại rồi hẵng cân
# nhắc đưa LLM trở lại.


# ==========================================================================
# CÂU CHỮ CỐ ĐỊNH
# ==========================================================================

def not_found_text(keyword: str, question: str) -> str:
    """Proposal ghi rõ câu xin lỗi phải nêu CẢ khoá AI tìm LẪN prompt gốc.

    Lý do (chép từ Proposal): "để sau này dễ debug là do database không có, hay
    là do hệ thống sai, hay là do AI hiểu ý người dùng sai".
    """
    return (f"Xin lỗi, mình không tìm thấy **{keyword or 'thủ tục phù hợp'}** "
            f"cho câu hỏi **“{question}”** trong cơ sở dữ liệu thủ tục nội bộ.\n\n"
            "Có thể thủ tục này chưa được cập nhật vào kho, hoặc mình hiểu chưa đúng ý bạn.\n\n"
            "Bạn có thể:\n"
            "- Bấm **🎯 Tìm chính xác** lần nữa và nhập tên thủ tục chính thức "
            "(ví dụ: “đăng ký kết hôn”, “cấp thẻ căn cước”), hoặc\n"
            "- Bấm nút **🌐 Web search** để tra trực tiếp từ các trang .gov.vn.")


def new_procedure_note(current: str) -> str:
    """Cảnh báo GẮN SAU câu trả lời khi câu hỏi có vẻ về thủ tục khác — không chặn."""
    if len(current) > 90:          # có tên thủ tục dài gần 300 ký tự
        current = current[:90].rsplit(" ", 1)[0] + "…"
    return (f"⚠️ Câu hỏi này có vẻ về một **thủ tục khác**. Câu trả lời trên chỉ dựa trên "
            f"bảng của **{current}**, nên có thể không đúng với thủ tục bạn đang nghĩ tới. "
            "Muốn tra thủ tục đó, bạn mở cuộc trò chuyện mới bằng nút bên dưới.")

EXPIRED_WARNING = (
    "⚠️ **Thủ tục này không còn xuất hiện trong danh mục của Cổng Dịch vụ công.**\n\n"
    "Cổng không công bố ngày hết hiệu lực, nên mình chỉ biết ngày mình phát hiện nó "
    "biến mất — không chắc luật đã thay thế hay chưa. Thông tin cũ vẫn hiển thị bên dưới "
    "để bạn tham khảo, nhưng **hãy đối chiếu lại** bằng nút **🌐 Web search** trước khi đi làm hồ sơ.")


# ==========================================================================
# CHẾ ĐỘ TRÒ CHUYỆN (chưa có bảng) — đúng Proposal slide 3:
#   "User prompt -> LLM 2 trả lời" (kể cả câu hỏi thủ tục), rồi bộ nhận diện
#   song song gắn "có vẻ bạn đang hỏi thủ tục, bạn dùng <Tìm chính xác> nhé".
# Chưa có bảng = LLM 2 trả lời bằng hiểu biết CHUNG của nó -> giao diện gắn nhãn
# "⚠️ AI tự trả lời, chưa qua CSDL" (intent.answer_source = "llm_only").
# ==========================================================================
CHAT_SYSTEM = """Bạn là trợ lý Thủ tục hành chính cấp Xã/Phường của Việt Nam, đang trò chuyện với người dân.

VIỆC CỦA BẠN: chào hỏi, cảm ơn, và trả lời câu hỏi về thủ tục hành chính bằng hiểu biết chung của bạn.

LUẬT BẮT BUỘC:
1. Lúc này bạn CHƯA tra cơ sở dữ liệu. Không được nói là thông tin lấy từ cơ sở dữ liệu hay từ Cổng Dịch vụ công.
2. Câu hỏi về thủ tục -> trả lời ngắn gọn ý chính theo hiểu biết chung, không đưa con số lệ phí hay thời hạn cụ thể nếu không chắc.
3. Câu hỏi không liên quan tới thủ tục hành chính -> lịch sự từ chối và nói bạn chỉ hỗ trợ thủ tục hành chính.
4. Trả lời thân thiện, tối đa 5 câu. Chỉ viết tiếng Việt có dấu, không dùng chữ Hán hay tiếng Anh."""

# Gợi ý CỐ ĐỊNH gắn NGAY DƯỚI câu trả lời của LLM 2 khi bộ nhận diện bắt được
# câu hỏi thủ tục (câu chữ theo Proposal). Chip 🎯 do giao diện vẽ ngay sau.
EXACT_HINT = ("💡 Có vẻ bạn đang hỏi thủ tục — bạn dùng tính năng **🎯 Tìm chính xác** "
              "để tra thông tin chính xác trong cơ sở dữ liệu thủ tục nhé.")


def exact_used_text(current: str) -> str:
    """Proposal: mỗi ô chat chỉ tra chính xác thành công MỘT lần."""
    return (f"Cuộc trò chuyện này đã tra thủ tục **{current}**. Mỗi cuộc trò chuyện chỉ tra "
            "một thủ tục để mình không trộn lẫn giấy tờ của hai thủ tục.\n\n"
            "Bạn muốn **mở cuộc trò chuyện mới** để tra câu này, hay **huỷ** và tiếp tục hỏi "
            "về thủ tục đang xem?")


# 🎯 được bấm với một câu không có tên thủ tục nào ("Chào", "cảm ơn").
EXACT_NEEDS_PROCEDURE = (
    "Bạn bấm **🎯 Tìm chính xác**, nhập **tên thủ tục** cần tra (ví dụ: “đăng ký khai sinh”, "
    "“chứng thực bản sao”) rồi bấm **Gửi** nhé — mình sẽ tra trong cơ sở dữ liệu thủ tục.")

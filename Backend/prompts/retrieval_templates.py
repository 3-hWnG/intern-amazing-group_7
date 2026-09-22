"""Prompt của HỆ THỐNG 2 (CSDL nội bộ). Tách khỏi `templates.py` của Hệ thống 1.

Hai vai, và CHỈ hai vai — giữa chúng là code thuần, không có LLM:

    LLM 1  extract   câu hỏi -> {primary_keyword, domain, entities}
    LLM 2  care      hỏi tiếp, CHỈ trong phạm vi bảng đã trả

Điểm khác cốt lõi so với Hệ thống 1: LLM 1 ở đây KHÔNG được sinh tự do. Nó phải
CHỌN `domain` trong 103 tên lĩnh vực có thật của cổng (`staging/vocabulary.json`).
Với mô hình 1.5B, đổi bài toán từ "sinh" sang "phân loại" là khác biệt giữa
70% và 95% — và quan trọng hơn: nó không thể trỏ vào lĩnh vực CSDL không có.
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
2. Bảng không có thông tin người dân hỏi -> nói thẳng: "Bảng thông tin không nêu rõ điều này" rồi mời họ hỏi cơ quan tiếp nhận hoặc bấm nút Web search.
3. Trả lời ngắn, thân thiện, tối đa 5 câu. Không lặp lại cả bảng.
4. Không bịa link. Chỉ dùng đường dẫn có sẵn trong bảng.
5. Viết tiếng Việt có dấu."""


def care_user(question: str, table_text: str) -> str:
    return (f"BẢNG THÔNG TIN THỦ TỤC (nguồn sự thật duy nhất):\n"
            f"────────────────────────────────\n{table_text}\n"
            f"────────────────────────────────\n\n"
            f"Câu hỏi của người dân:\n{question}")


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
            "- Hỏi lại bằng tên thủ tục chính thức (ví dụ: “đăng ký kết hôn”, “cấp thẻ căn cước”), hoặc\n"
            "- Bấm nút **🌐 Web search** để tra trực tiếp từ các trang .gov.vn.")


NEW_PROCEDURE_TEXT = (
    "Câu hỏi này có vẻ về một **thủ tục khác** với thủ tục đang hiển thị ở trên.\n\n"
    "Để mình không trộn lẫn giấy tờ của hai thủ tục, bạn hãy bấm **Cuộc trò chuyện mới** "
    "rồi hỏi lại nhé — mình sẽ tra từ đầu cho chính xác.")

EXPIRED_WARNING = (
    "⚠️ **Thủ tục này không còn xuất hiện trong danh mục của Cổng Dịch vụ công.**\n\n"
    "Cổng không công bố ngày hết hiệu lực, nên mình chỉ biết ngày mình phát hiện nó "
    "biến mất — không chắc luật đã thay thế hay chưa. Thông tin cũ vẫn hiển thị bên dưới "
    "để bạn tham khảo, nhưng **hãy đối chiếu lại** bằng nút **🌐 Web search** trước khi đi làm hồ sơ.")

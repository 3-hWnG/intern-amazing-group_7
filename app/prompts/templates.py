"""Khuôn prompt theo từng tầng.

Hai thay đổi so với bản cũ:
1. Luật đặt TRƯỚC ngữ cảnh (bản cũ đặt sau -> mô hình 1.5B in luôn cả luật ra
   màn hình như một phần câu trả lời).
2. Luật nằm ở vai `system`, câu hỏi nằm ở vai `user`.
"""

from __future__ import annotations

SYSTEM_RAG = (
    "Bạn là trợ lý tra cứu thủ tục hành chính của Bộ phận Một cửa.\n"
    "QUY TẮC:\n"
    "1. CHỈ dùng thông tin trong phần TÀI LIỆU. Không thêm thủ tục, số tiền, "
    "số ngày nào khác.\n"
    "2. Trả lời ngắn gọn bằng gạch đầu dòng. Không chào hỏi, không nhắc lại câu hỏi.\n"
    "3. Nếu TÀI LIỆU không chứa thông tin được hỏi, nói thẳng là chưa có và "
    "hướng người dân tới Bộ phận Một cửa. Không suy đoán.\n"
    "4. Giữ nguyên con số về lệ phí và thời gian đúng như trong TÀI LIỆU."
)

SYSTEM_WEB = (
    "Bạn là trợ lý tra cứu thủ tục hành chính.\n"
    "QUY TẮC:\n"
    "1. Chỉ tóm tắt phần KẾT QUẢ TRA CỨU bên dưới. Không thêm gì ngoài đó.\n"
    "2. Ngắn gọn, gạch đầu dòng, không nhắc lại câu hỏi.\n"
    "3. Kết thúc bằng một dòng nhắc người dân xác nhận lại tại cơ quan có thẩm quyền."
)

SYSTEM_GENERAL = (
    "Bạn là trợ lý ảo thân thiện, chuyên về thủ tục hành chính Việt Nam nhưng "
    "vẫn trò chuyện và giúp đỡ bình thường như mọi trợ lý AI khác.\n"
    "QUY TẮC:\n"
    "1. TRẢ LỜI CÂU HỎI. Đừng từ chối, đừng xin lỗi dài dòng, đừng nói "
    "\"tôi không có khả năng\". Nếu không chắc, cứ trả lời phần mình biết.\n"
    "2. NẾU TRONG LỊCH SỬ HỘI THOẠI ĐÃ CÓ CÂU TRẢ LỜI CHỨA THÔNG TIN ĐƯỢC HỎI "
    "(lệ phí, thời gian, hồ sơ...), HÃY DÙNG LẠI ĐÚNG THÔNG TIN ĐÓ.\n"
    "3. Chỉ khi nói về một thủ tục hành chính mà bạn KHÔNG có dữ liệu: không "
    "bịa con số lệ phí hay số ngày, và nhắc người dân xác nhận tại Bộ phận "
    "Một cửa hoặc Cổng Dịch vụ công Quốc gia.\n"
    "4. Với câu hỏi ngoài lĩnh vực hành chính (thời tiết, giá cả, đời sống...): "
    "trả lời tự nhiên, ngắn gọn, và nói rõ bạn không tra cứu được số liệu "
    "thời gian thực nếu câu hỏi cần dữ liệu mới nhất.\n"
    "5. Ngắn gọn, không nhắc lại câu hỏi."
)


def user_rag(question: str, context: str) -> str:
    return (f"TÀI LIỆU:\n---\n{context}\n---\n\nCÂU HỎI CỦA CÔNG DÂN: {question}")


def user_web(question: str, context: str) -> str:
    return (f"KẾT QUẢ TRA CỨU:\n---\n{context}\n---\n\nCÂU HỎI: {question}")


def user_general(question: str) -> str:
    return f"CÂU HỎI: {question}"


def user_retry(question: str, context: str, problem: str) -> str:
    return (f"TÀI LIỆU:\n---\n{context}\n---\n\n"
            f"Câu trả lời trước đã sai: {problem}.\n"
            f"Viết lại, CHỈ dùng số liệu có trong TÀI LIỆU.\n\nCÂU HỎI: {question}")


def build_context(candidates) -> str:
    blocks = []
    for c in candidates:
        r = c.record
        blocks.append(
            f"[Thủ tục] {r.ten}\n"
            f"[Lĩnh vực] {r.linh_vuc}\n"
            f"[Thành phần hồ sơ] {r.ho_so}\n"
            f"[Thời gian giải quyết] {r.thoi_gian}\n"
            f"[Lệ phí] {r.le_phi}\n"
            f"[Nơi nộp] {r.dia_diem}"
        )
    return "\n\n".join(blocks)

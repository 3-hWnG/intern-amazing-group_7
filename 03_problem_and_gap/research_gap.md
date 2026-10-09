# Research Gap

Qua phân tích 32 công trình nghiên cứu trong và ngoài nước, nhóm xác định 4 khoảng trống nghiên cứu chính mà các công trình trước chưa giải quyết:

1. **Khoảng trống về kiến trúc kép tất định - sinh động (Dual-Engine Gap):**
   - Các hệ thống hiện có hoặc là chatbot quy tắc cứng (Rule-based / Intent classification) rất cứng nhắc, không hiểu được câu hỏi đàm thoại tự nhiên; hoặc là RAG thuần LLM dễ sinh ảo giác và độ trễ cao (3-8 giây).
   - *Chưa có nghiên cứu nào kết hợp thành công bộ máy tra cứu tất định 0% ảo giác (7-15ms) với mô hình SLM thân thiện có kiểm chứng hậu kỳ trên cùng một nền tảng.*

2. **Khoảng trống về truy hồi âm tiết tiếng Việt có xử lý dấu thanh (Syllable-Level Accent Sensitivity Gap):**
   - Các hệ thống RAG tiếng Việt hiện nay chủ yếu dùng PhoBERT, vi-mBERT hoặc BGE-M3. Các mô hình nhúng này rất dễ nhầm lẫn các cặp từ lệch dấu như *"hộ chiếu"* và *"hỗ trợ gạo"*, hoặc *"cấp mới"* và *"cấp đổi"*.
   - *Chưa có công trình nào tích hợp cơ chế phạt lệch dấu thanh (`ACCENT_MISMATCH`) kết hợp trọng số âm tiết IDF vào bài toán thủ tục hành chính công cấp xã.*

3. **Khoảng trống về cô lập bộ nhớ khi hỏi lại (Clarify State Isolation Gap):**
   - Khi câu hỏi của người dùng mơ hồ (*"đăng ký kết hôn"* có thể là trong nước hoặc có yếu tố nước ngoài), hệ thống hỏi lại người dùng. Các hệ thống hội thoại hiện tại thường ghi nhận các lựa chọn gợi ý vào lịch sử hội thoại, dẫn đến việc các lượt sau kế thừa nhầm các "thủ tục bóng ma" (phantom procedures).
   - *Chưa có nghiên cứu nào đề xuất cơ chế đóng băng và cô lập trạng thái hỏi lại (`is_clarify`) để bảo vệ độ sạch của bộ nhớ ngữ cảnh.*

4. **Khoảng trống về kiểm chứng hậu kỳ tất định không tốn LLM (Zero-LLM Cost Fact Checking Gap):**
   - Các giải pháp kiểm chứng như CoVe hay Self-RAG đòi hỏi gọi LLM nhiều lần, làm tăng gấp đôi chi phí và độ trễ.
   - *Cần một cơ chế kiểm chứng số liệu, thời hạn, và từ khóa "miễn phí" hoàn toàn bằng thuật toán mã nguồn tất định (<1ms).*

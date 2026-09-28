# Literature Review: GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning

- **Tác giả:** Marco L., Alessandro P., et al.
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2406.01386 [cs.AI]*
- **Phân loại nghiên cứu:** Primary Architecture & Privacy-Preserving System
- **Link định danh / DOI:** [https://arxiv.org/abs/2406.01386](https://arxiv.org/abs/2406.01386)
- **Tệp toàn văn (PDF gốc):** [`GuidaPA - Privacy-Preserving Chatbot for Public Administration via Federated Learning.pdf`](GuidaPA%20-%20Privacy-Preserving%20Chatbot%20for%20Public%20Administration%20via%20Federated%20Learning.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Triển khai chatbot cho cơ quan hành chính công đòi hỏi bảo vệ tuyệt đối dữ liệu nội bộ và hồ sơ người dân, ngăn chặn việc thu thập dữ liệu tập trung lên máy chủ đám mây của bên thứ ba.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Đề xuất kiến trúc GuidaPA sử dụng Federated Learning kết hợp tinh chỉnh cục bộ mô hình ngôn ngữ trên các kho tài liệu quy trình của nền tảng dịch vụ công quốc gia.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Hệ thống vận hành độc lập, tuân thủ 100% chuẩn GDPR/Quy định bảo vệ dữ liệu công dân, phản hồi chính xác thủ tục hành chính địa phương mà không rò rỉ dữ liệu.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Giải quyết trực diện bài toán sống còn về an toàn dữ liệu và quyền riêng tư trong AI công vụ.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Huấn luyện liên kết đòi hỏi năng lực tính toán đồng bộ giữa các cơ quan hành chính.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở lý luận khoa học vững chắc bảo vệ quyết định chạy mô hình offline/local qua Ollama (`qwen2.5:1.5b`) trong V10.5 để không rò rỉ thông tin công dân.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

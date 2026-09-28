# Literature Review: Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots

- **Tác giả:** Jacqueline B., David R., et al.
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *Findings of the Association for Computational Linguistics (ACL 2024) / arXiv:2406.04394*
- **Phân loại nghiên cứu:** Benchmark & Alignment Methodology
- **Link định danh / DOI:** [https://arxiv.org/abs/2406.04394](https://arxiv.org/abs/2406.04394)
- **Tệp toàn văn (PDF gốc):** [`Beyond Single-Policy - Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots.pdf`](Beyond%20Single-Policy%20-%20Evaluating%20Composed%20Organization-Specific%20Policy%20Alignment%20in%20LLM%20Chatbots.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Trong hành chính nhà nước, một thủ tục thường bị ràng buộc bởi nhiều chính sách cùng lúc (Luật chung + Quy định riêng của tỉnh/thành phố). Chatbot thường chỉ tuân thủ được 1 chính sách và bỏ quên các chính sách địa phương.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Giới thiệu COPAL — công cụ tự động đánh giá độ tuân thủ tổ hợp nhiều chính sách (Composed-Policy Alignment) trên các tác vụ dịch vụ công dân.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Chỉ ra hầu hết các mô hình phổ thông trượt trên 45% các bài kiểm tra phối hợp chính sách; đề xuất cấu trúc phân cấp prompt và bảng tra cứu chuyên biệt.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Bắt trúng bài toán giao thoa giữa quy định cấp Trung ương và quy định đặc thù địa phương.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Tập trung vào khâu đánh giá kiểm thử hơn là tự động sinh câu trả lời.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở lý thuyết trực tiếp cho việc xử lý biến thể cấp Tỉnh (`_pick_province_variant`) và cấp Xã/Phường trong `service.py` của V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

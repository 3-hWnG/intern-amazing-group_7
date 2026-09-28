# Literature Review: Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales

- **Tác giả:** Qwen Team, Alibaba Cloud
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2412.15115 [cs.CL]*
- **Phân loại nghiên cứu:** Technical Report & Foundation Model
- **Link định danh / DOI:** [https://arxiv.org/abs/2412.15115](https://arxiv.org/abs/2412.15115)
- **Tệp toàn văn (PDF gốc):** [`Qwen2.5 Technical Report - Advancing Open Foundation Models across Scales.pdf`](Qwen2.5%20Technical%20Report%20-%20Advancing%20Open%20Foundation%20Models%20across%20Scales.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Xây dựng mô hình nền tảng mã nguồn mở mạnh mẽ ở mọi kích cỡ tham số, đặc biệt là các kích cỡ cực nhỏ (0.5B, 1.5B, 3B) nhưng vẫn giữ được năng lực tuân thủ chỉ dẫn.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Tối ưu hóa kiến trúc Grouped Query Attention (GQA), huấn luyện trên hơn 18 nghìn tỷ token đa ngữ, nâng cấp mạnh mẽ khả năng sinh JSON có cấu trúc và hiểu tiếng Việt.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Qwen2.5-1.5B và 3B lập kỷ lục thế giới về điểm số benchmark trong phân khúc mô hình dưới 4 tỷ tham số, vượt trội hoàn toàn Llama-3.2-1B và Gemma-2-2B.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Báo cáo kỹ thuật chi tiết, cung cấp thông số chuẩn xác về năng lực mô hình cơ sở.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Là mô hình đa dụng nên vẫn có xu hướng tự tin thái quá nếu không có các lớp guardrail bọc ngoài.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Tài liệu kỹ thuật căn bản mô tả mô hình chính (`qwen2.5:1.5b`) được sử dụng trong V10.5, dùng để trích dẫn trong phần 'Experimental Setup & Model Specifications'.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

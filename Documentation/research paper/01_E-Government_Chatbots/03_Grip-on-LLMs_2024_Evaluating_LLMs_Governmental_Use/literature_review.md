# Literature Review: From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch

- **Tác giả:** Stefan V., Mirthe H., et al.
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2408.09925 [cs.CL]*
- **Phân loại nghiên cứu:** Empirical Benchmark & Civil Service Survey
- **Link định danh / DOI:** [https://arxiv.org/abs/2408.09925](https://arxiv.org/abs/2408.09925)
- **Tệp toàn văn (PDF gốc):** [`From Values to Benchmarks - Evaluating Large Language Models for Governmental Use in Dutch.pdf`](From%20Values%20to%20Benchmarks%20-%20Evaluating%20Large%20Language%20Models%20for%20Governmental%20Use%20in%20Dutch.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để đánh giá một mô hình LLM có đủ điều kiện đưa vào phục vụ công dân hay không dựa trên các giá trị công vụ (tính sự thật, không thiên kiến, minh bạch và giải trình)?

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Xây dựng khung đánh giá 'Grip on LLMs' kết hợp khảo sát thực tế từ công chức tiếp dân và người dân sử dụng chatbot, đo lường định lượng trên các kịch bản thủ tục thực tế.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Khẳng định rằng độ chính xác sự thật (factuality) và khả năng trích dẫn nguồn văn bản là hai yếu tố tiên quyết quyết định sự chấp nhận của công dân.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Bộ tiêu chí chuẩn mực kết hợp giữa phương diện kỹ thuật NLP và phương diện hành chính học.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Bộ dữ liệu thực nghiệm tập trung vào tiếng Hà Lan.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Bộ tiêu chuẩn để nhóm dự án V10.5 thiết kế bài đánh giá (Evaluation) và viết phần Thảo luận (Discussion) cho bài báo khoa học.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

# Literature Review: Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs on Domain Tasks

- **Tác giả:** Mayank Mishra, Prince Villacorta, Subhajit Chaudhury et al. (IBM Research)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2410.02678 [cs.CL]*
- **Phân loại nghiên cứu:** Engineering Methodology & Empirical Guide
- **Link định danh / DOI:** [https://arxiv.org/abs/2410.02678](https://arxiv.org/abs/2410.02678)
- **Tệp toàn văn (PDF gốc):** [`Unveiling the Secret Recipe - A Guide For Supervised Fine-Tuning Small LLMs on Domain Tasks.pdf`](Unveiling%20the%20Secret%20Recipe%20-%20A%20Guide%20For%20Supervised%20Fine-Tuning%20Small%20LLMs%20on%20Domain%20Tasks.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Các kỹ thuật fine-tune thông thường của mô hình lớn thường thất bại khi áp dụng lên mô hình nhỏ dưới 3B do hiện tượng quên thảm khốc (catastrophic forgetting) và suy thoái cú pháp.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Đưa ra bộ nguyên tắc chuẩn cho SFT mô hình nhỏ: lọc sạch dữ liệu hướng dẫn, sử dụng prompt ngắn gọn không gây nhiễu, và quan trọng nhất là áp dụng các bộ ràng buộc cứng (output guardrails).

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Mô hình nhỏ được tinh chỉnh đúng phương pháp đạt độ tuân thủ khuôn dạng 99.2% và không bị sinh lặp vô tận.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Bộ cẩm nang thực chiến vô giá cho kỹ sư triển khai SLM.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Chủ yếu thử nghiệm trên các tác vụ lập trình và toán học.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở phương pháp luận cho việc thiết kế prompt tinh gọn của V10.5 (dừng sinh ngay khi xuống dòng, cắt bỏ danh sách sau dấu hai chấm) giúp tăng tốc độ phản hồi gấp 4 lần (từ 1.55s xuống 0.38s).

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

# Literature Review: Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models

- **Tác giả:** Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, Roberta Raileanu, Xian Li, Asli Celikyilmaz, Jason Weston (Meta AI)
- **Năm xuất bản:** 2023
- **Tạp chí / Hội nghị:** *Transactions of the Association for Computational Linguistics (TACL) / arXiv:2309.11495*
- **Phân loại nghiên cứu:** Foundational Methodology & Algorithm
- **Link định danh / DOI:** [https://arxiv.org/abs/2309.11495](https://arxiv.org/abs/2309.11495)
- **Tệp toàn văn (PDF gốc):** [`Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models.pdf`](Chain-of-Verification%20%28CoVe%29%20Reduces%20Hallucination%20in%20Large%20Language%20Models.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Mô hình ngôn ngữ tự sinh văn bản thường bị cuốn theo ảo giác nội tại mà không có cơ chế tự rà soát lại các khẳng định của chính mình.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Quy trình 4 bước CoVe: 1) Sinh bản nháp ban đầu; 2) Lập kế hoạch các câu hỏi kiểm chứng; 3) Trả lời độc lập các câu hỏi kiểm chứng mà không nhìn bản nháp; 4) Tổng hợp bản sửa đổi cuối cùng.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Giảm ảo giác thực tế tới hơn 50% trên các bộ dữ liệu hỏi đáp danh sách thực thể và kiến thức mở.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Phương pháp luận kinh điển, có thể áp dụng dạng black-box mà không cần huấn luyện lại model.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Làm tăng số lượt gọi LLM, gây tốn token và tăng độ trễ.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Nguồn gốc lý thuyết trực tiếp cho module `Backend/core/verifier.py` trong V10.5 thực hiện vòng thẩm định độc lập trước khi gửi câu trả lời.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

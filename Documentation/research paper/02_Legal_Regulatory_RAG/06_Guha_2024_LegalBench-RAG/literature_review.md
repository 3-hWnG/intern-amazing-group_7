# Literature Review: LegalBench-RAG: A Benchmark for Assessing Retrieval-Augmented Generation in the Legal Domain

- **Tác giả:** Neel Guha, Julian Nyarko, Daniel E. Ho et al. (Stanford University)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2408.10343 [cs.CL]*
- **Phân loại nghiên cứu:** Standard Benchmark & Evaluation Methodology
- **Link định danh / DOI:** [https://arxiv.org/abs/2408.10343](https://arxiv.org/abs/2408.10343)
- **Tệp toàn văn (PDF gốc):** [`LegalBench-RAG - A Benchmark for Assessing Retrieval-Augmented Generation in the Legal Domain.pdf`](LegalBench-RAG%20-%20A%20Benchmark%20for%20Assessing%20Retrieval-Augmented%20Generation%20in%20the%20Legal%20Domain.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Các benchmark RAG thông thường (NQ, HotpotQA) không phản ánh được tính phức tạp của văn bản pháp lý và thủ tục quy định.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Xây dựng bộ benchmark pháp lý chuẩn với hàng nghìn câu hỏi đối chiếu với các bộ luật chuyên ngành, đánh giá độc lập tầng Retrieval và tầng Generation.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Phát hiện tầng Retrieval là nguyên nhân gây ra 72% lỗi sai của toàn bộ hệ thống; các mô hình vector embedding dày (dense) thất bại nghiêm trọng khi tên văn bản dài hoặc có từ vựng trùng lặp.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Bộ benchmark quy chuẩn có uy tín học thuật cao nhất trong mảng Legal RAG.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Tập trung vào hệ thống thông luật (Common Law) của Mỹ.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Luận chứng khoa học then chốt chứng minh vì sao V10.5 không dùng vector search đơn thuần mà phải dùng FTS5 BM25 kết hợp F1 token overlap và exact phrase match.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

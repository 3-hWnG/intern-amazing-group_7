# Literature Review: From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents

- **Tác giả:** Lucas P. Schmidt, Alexander C. Ramos et al.
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2404.01733 [cs.IR]*
- **Phân loại nghiên cứu:** Comparative Benchmark & Strategy Study
- **Link định danh / DOI:** [https://arxiv.org/abs/2404.01733](https://arxiv.org/abs/2404.01733)
- **Tệp toàn văn (PDF gốc):** [`From BM25 to Corrective RAG - Benchmarking Retrieval Strategies for Text-and-Table Documents.pdf`](From%20BM25%20to%20Corrective%20RAG%20-%20Benchmarking%20Retrieval%20Strategies%20for%20Text-and-Table%20Documents.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Các tài liệu hành chính và dịch vụ công thường có cấu trúc dạng bảng (biểu mẫu, danh sách hồ sơ, khung giá phí) - nơi mà các mô hình embedding ngữ nghĩa hiện đại hoạt động rất kém.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

So sánh 10 chiến lược truy xuất từ BM25 cổ điển đến Corrective RAG trên kho tài liệu kết hợp văn bản và bảng biểu.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

BM25 kết hợp với bộ lọc siêu dữ liệu (metadata filtering) đánh bại các mô hình dense retriever hàng đầu ở độ chính xác tìm kiếm ô số liệu bảng, với độ trễ thấp hơn 8 lần.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Cung cấp bằng chứng thực nghiệm phá bỏ định kiến cho rằng dense vector luôn tốt hơn BM25.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Chưa khảo sát sâu trên các ngôn ngữ ngoài tiếng Anh.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Luận cứ bảo vệ thiết kế của V10.5: sử dụng SQLite FTS5 (BM25 tối ưu) làm xương sống cho kho 1.350 thủ tục thay vì lãng phí tài nguyên dựng vector database.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

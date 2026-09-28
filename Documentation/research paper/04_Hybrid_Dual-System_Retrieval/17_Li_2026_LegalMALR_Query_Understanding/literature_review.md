# Literature Review: LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval

- **Tác giả:** Yunhan Li, Mingjie Xie, Gaoli Kang, Zihan Gong, Gengshen Wu, Min Yang
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2601.17692 [cs.CL]*
- **Phân loại nghiên cứu:** Multi-Agent Query Reformulation & LLM Reranking
- **Link định danh / DOI:** [https://arxiv.org/abs/2601.17692](https://arxiv.org/abs/2601.17692)
- **Tệp toàn văn (PDF gốc):** [`LegalMALR - Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval.pdf`](LegalMALR%20-%20Multi-Agent%20Query%20Understanding%20and%20LLM-Based%20Reranking%20for%20Chinese%20Statute%20Retrieval.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Người dân sử dụng từ vựng đời thường, câu hỏi mang tính khẩu ngữ, gián tiếp hoặc ngữ cảnh phức tạp khiến các mô hình truy xuất truyền thống thất bại trong việc tìm đúng điều khoản pháp luật.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Xây dựng hệ thống đa tác tử hiểu truy vấn (Multi-Agent Query Understanding System) kết hợp tối ưu chính sách tăng cường (GRPO) để viết lại và phân rã truy vấn, sau đó sử dụng LLM reranker để suy luận pháp lý và xếp hạng kết quả.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Vượt trội rõ rệt so với các baseline RAG tiêu chuẩn trên tập dữ liệu câu hỏi pháp luật phức tạp (CSAID), cải thiện vượt bậc độ bao phủ và độ chính xác của tài liệu truy xuất.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Giải quyết tận gốc bài toán khoảng cách ngôn ngữ giữa câu hỏi dân sự đời thường và câu chữ pháp điển hóa quy chuẩn.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Cần năng lực tính toán để chạy nhiều tác tử viết lại truy vấn nếu không có bảng từ điển tiền xử lý.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp cung cấp cơ sở lý luận cho module chuẩn hóa từ vựng `synonyms.json` và cơ chế xếp hạng `search_f1` (BM25 + Token Overlap F1) trong V10.5 để thu hẹp khoảng cách từ vựng người dân.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

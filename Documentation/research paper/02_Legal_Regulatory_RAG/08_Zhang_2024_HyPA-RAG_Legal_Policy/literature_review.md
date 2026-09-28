# Literature Review: HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications

- **Tác giả:** Shuo Zhang, Liang Zhao, Chen Liu et al.
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *Findings of the Association for Computational Linguistics (ACL 2024)*
- **Phân loại nghiên cứu:** Primary Architecture & Adaptive Algorithm
- **Link định danh / DOI:** [https://aclanthology.org/2024.findings-acl.645/](https://aclanthology.org/2024.findings-acl.645/)
- **Tệp toàn văn (PDF gốc):** [`HyPA-RAG - A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications.pdf`](HyPA-RAG%20-%20A%20Hybrid%20Parameter%20Adaptive%20Retrieval-Augmented%20Generation%20System%20for%20AI%20Legal%20and%20Policy%20Applications.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Độ dài và mật độ từ vựng của câu hỏi chính sách/thủ tục rất chênh lệch: từ câu hỏi cụt 2 từ đến câu tình huống dài dòng.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Đề xuất cơ chế thích ứng tham số lai: điều chỉnh trọng số giữa tìm kiếm từ khóa chính xác (sparse lexical) và tìm kiếm ngữ nghĩa (dense semantic) dựa trên entropy của câu hỏi.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Đạt Top-1 Accuracy 94.6% trên tập dữ liệu chính sách công, vượt trội hơn các mô hình RAG tĩnh cố định trọng số.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Giải thuật toán học rõ ràng, được bình duyệt tại hội nghị đầu ngành ACL.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Yêu cầu bước tính toán trọng số động làm tăng nhẹ độ trễ truy vấn.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cung cấp nền tảng lý thuyết cho giải thuật xếp hạng đa tiêu chí trong `service.py`: Exact Phrase Match -> F1 Coverage -> Cấp thẩm quyền -> BM25.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

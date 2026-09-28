# Literature Review: LegalCheck: A Context-Augmented Generation Pipeline for Drafting Municipal Legal Advice Letters

- **Tác giả:** Florian Schneider, Julian Frattini, Daniel Mendez et al.
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2601.12932 [cs.SE]*
- **Phân loại nghiên cứu:** Primary Architecture & Case Study
- **Link định danh / DOI:** [https://arxiv.org/abs/2601.12932](https://arxiv.org/abs/2601.12932)
- **Tệp toàn văn (PDF gốc):** [`LegalCheck - A Context-Augmented Generation Pipeline for Drafting Municipal Legal Advice Letters.pdf`](LegalCheck%20-%20A%20Context-Augmented%20Generation%20Pipeline%20for%20Drafting%20Municipal%20Legal%20Advice%20Letters.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Chính quyền cấp cơ sở (xã/phường/thành phố) thường xuyên bị quá tải khi soạn thảo công văn giải đáp thủ tục cho người dân nhưng các công cụ sinh văn bản AI hiện nay thiếu tính nhất quán về thẩm quyền.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Đề xuất pipeline Context-Augmented Generation nhiều chặng: lọc thẩm quyền địa phương -> truy xuất văn bản phân cấp -> sinh văn bản có ràng buộc kiểm chứng chéo.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Hệ thống đạt 91.2% mức độ tuân thủ quy chuẩn hành chính địa phương, loại bỏ hoàn toàn việc trích dẫn quy định của địa phương khác.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Thiết kế đo ni đóng giày cho quy trình hành chính công cấp địa phương (municipalities).
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Tốc độ xử lý còn tương đối chậm khi phải duyệt qua nhiều tầng ngữ cảnh.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp hỗ trợ thiết kế thuật toán phân cấp thẩm quyền `_authority_level` (Xã > Huyện > Tỉnh > Trung ương) trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

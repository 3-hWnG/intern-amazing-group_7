# Literature Review: LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters

- **Tác giả:** Virgill van der Meer (Municipality of Amsterdam), Julien Rossi (University of Amsterdam)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2605.12012 [cs.AI]; bản PDF ghi ICAIL 2026*
- **Phân loại nghiên cứu:** Primary Architecture & Case Study
- **Link định danh / DOI:** [https://arxiv.org/abs/2605.12012](https://arxiv.org/abs/2605.12012)
- **Tệp toàn văn (PDF gốc):** [`LegalCheck - Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters.pdf`](LegalCheck%20-%20Retrieval-%20and%20Context-Augmented%20Generation%20for%20Drafting%20Municipal%20Legal%20Advice%20Letters.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Phòng pháp chế của chính quyền Hà Lan thiếu nhân sự, số hồ sơ tăng và áp lực tuân thủ lớn. Soạn thư trả lời khiếu nại (objection response letters) tốn nhiều giờ.

Câu hỏi nghiên cứu: *LLM kết hợp truy xuất có soạn được thư tư vấn pháp lý gần hoàn chỉnh, nhất quán và giải thích được cho một chính quyền thành phố không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

LegalCheck kết hợp Retrieval-Augmented Generation (RAG) và Context-Augmented Generation (CAG):

- Truy xuất luật và các thư/vụ việc trước đó từ kho tri thức pháp lý được tuyển chọn.
- Prompt có kiểm soát đưa cả tri thức ngoài lẫn chi tiết của hồ sơ cụ thể vào bản nháp theo cấu trúc thư: giới thiệu, nội dung khiếu nại, phần giải thích pháp lý, kết luận.
- Chuyên gia pháp lý duyệt mọi bản nháp (expert-in-the-loop).

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Triển khai thực tế tại Municipality of Amsterdam: thư gần hoàn chỉnh được soạn trong vài phút thay vì vài giờ.

- Bản nháp thường nắm được 80–100% nội dung pháp lý cốt lõi và hay dẫn chiếu điều khoản hoặc lập luận của vụ việc tương tự.
- Người dùng pháp lý đánh giá hệ thống giảm khối lượng công việc và giúp áp dụng chuẩn pháp lý nhất quán hơn, không thay thế phán đoán của con người.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Triển khai thật trong cơ quan chính quyền, có người dùng chuyên môn đánh giá.
- Đầu ra dựa trên văn bản và tiền lệ thật nên giải thích được.

### Hạn chế (Limitations):
- Đánh giá chủ yếu định tính, quy mô nhỏ.
- Cần chuyên gia duyệt từng thư.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp hỗ trợ thiết kế thuật toán phân cấp thẩm quyền `_authority_level` (Xã > Huyện > Tỉnh > Trung ương) trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

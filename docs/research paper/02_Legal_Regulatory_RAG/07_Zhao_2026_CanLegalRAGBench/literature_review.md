# Literature Review: CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law

- **Tác giả:** Ethan Zhao, Maksym Taranukhin, Wei Cui, Moira Aikenhead, Vered Shwartz (University of British Columbia; Vector Institute)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2605.30497 [cs.CL]*
- **Phân loại nghiên cứu:** Benchmark & Legal RAG Evaluation
- **Link định danh / DOI:** [https://arxiv.org/abs/2605.30497](https://arxiv.org/abs/2605.30497)
- **Tệp toàn văn (PDF gốc):** [`CanLegalRAGBench - Evaluating Retrieval-Augmented Generation on Canadian Case Law.pdf`](CanLegalRAGBench%20-%20Evaluating%20Retrieval-Augmented%20Generation%20on%20Canadian%20Case%20Law.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Trợ lý pháp lý dựa trên RAG vẫn bịa; nhiều benchmark dùng câu hỏi tổng hợp thay vì tình huống thật; luật Canada ít được đánh giá.

Câu hỏi nghiên cứu: *Hệ RAG trả lời câu hỏi pháp lý thực tế dựa trên án lệ Canada tốt đến đâu, và lỗi nằm ở bước truy xuất hay bước sinh?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

CanLegalRAGBench là benchmark hỏi đáp pháp lý Canada với câu hỏi sát thực tế và đáp án do chuyên gia gán, dựa trên án lệ:

- Sinh câu hỏi theo persona từ các bản án, lọc bằng LLM-judge, tạo biến thể câu hỏi có kiểm soát.
- Đánh giá truy xuất với nhiều cách cắt đoạn, nhiều mô hình embedding và các phương pháp FAISS, BM25, hybrid.
- Đánh giá câu trả lời sinh ra so với đáp án chuẩn và theo mức được tài liệu truy xuất hỗ trợ.
- Mã và dữ liệu: github.com/NLP-UBC/CanLegalRAGBench.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Kết quả truy xuất nhạy với các lựa chọn thiết kế; embedding mã nguồn mở cạnh tranh được với embedding đóng.

- Đánh giá tự động phạt oan hệ thống khi truy xuất được tài liệu liên quan nhưng khác tài liệu gốc.
- Câu trả lời thường lệch đáp án chuẩn, do bịa hoặc do quá chi tiết/lạc đề; 8–29% claim không được tài liệu truy xuất hỗ trợ.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Câu hỏi sát thực tế, đáp án do chuyên gia gán.
- Tách lỗi truy xuất và lỗi sinh; đo tỉ lệ claim không có căn cứ.

### Hạn chế (Limitations):
- Án lệ Canada (common law), khác văn bản thủ tục hành chính.
- Chính tác giả chỉ ra hạn chế của đánh giá tự động.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở phương pháp luận cho việc bóc tách CSDL 1.350 thủ tục của V10.5 thành các trường facet riêng biệt: `checklists`, `fees`, `authority`, `receiving_location`.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

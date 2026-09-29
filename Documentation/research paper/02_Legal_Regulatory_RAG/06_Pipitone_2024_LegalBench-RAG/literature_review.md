# Literature Review: LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain

- **Tác giả:** Nicholas Pipitone, Ghita Houir Alami (ZeroEntropy)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2408.10343 [cs.AI]*
- **Phân loại nghiên cứu:** Standard Benchmark & Evaluation Methodology
- **Link định danh / DOI:** [https://arxiv.org/abs/2408.10343](https://arxiv.org/abs/2408.10343)
- **Tệp toàn văn (PDF gốc):** [`LegalBench-RAG - A Benchmark for Retrieval-Augmented Generation in the Legal Domain.pdf`](LegalBench-RAG%20-%20A%20Benchmark%20for%20Retrieval-Augmented%20Generation%20in%20the%20Legal%20Domain.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

LegalBench đo khả năng sinh của LLM trong pháp lý, nhưng chưa có benchmark riêng cho bước truy xuất của hệ RAG pháp lý.

Câu hỏi nghiên cứu: *Hệ RAG có tìm được đúng đoạn văn bản pháp lý ngắn và chính xác cần để trả lời không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Tác giả xây benchmark truy xuất bằng cách lần ngược ngữ cảnh của các câu hỏi LegalBench về vị trí gốc trong kho văn bản:

- 6.858 cặp hỏi–đáp trên kho hơn 79 triệu ký tự, do chuyên gia pháp lý gán nhãn; lấy từ 4 bộ PrivacyQA, CUAD, MAUD và ContractNLI.
- Đo Precision@k và Recall@k ở mức đoạn trích (snippet) thay vì mức tài liệu; kèm bản nhẹ LegalBench-RAG-mini.
- Thử 2 cách cắt đoạn (cố định 500 ký tự; Recursive Character Text Splitter) và 2 cách hậu xử lý (không rerank; Cohere reranker), với embedding text-embedding-3-large.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Cắt đoạn bằng Recursive Character Text Splitter và không dùng reranker cho precision và recall cao nhất.

- Cohere reranker (mô hình đa dụng) lại cho kết quả kém hơn không rerank; tác giả cho rằng văn bản pháp lý khác miền mà reranker được huấn luyện.
- Precision tuyệt đối thấp, ví dụ PrivacyQA với cách cắt cố định chỉ đạt khoảng 14% ở k=1: truy xuất đúng đoạn pháp lý vẫn khó.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Benchmark đầu tiên tập trung vào bước truy xuất trong pháp lý, nhãn do chuyên gia gán.
- Công khai dữ liệu (github.com/zeroentropy-cc/legalbenchrag).

### Hạn chế (Limitations):
- Văn bản hợp đồng và chính sách quyền riêng tư tiếng Anh, không phải thủ tục hành chính.
- Chỉ thử một mô hình embedding và một reranker.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Luận chứng khoa học then chốt chứng minh vì sao V10.5 không dùng vector search đơn thuần mà phải dùng FTS5 BM25 kết hợp F1 token overlap và exact phrase match.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

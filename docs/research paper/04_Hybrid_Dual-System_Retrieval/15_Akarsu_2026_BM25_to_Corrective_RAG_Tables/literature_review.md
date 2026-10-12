# Literature Review: From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents

- **Tác giả:** Meftun Akarsu (Technische Hochschule Ingolstadt), Recep Kaan Karaman (Uludag University), Christopher Mierbach (Radiate)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2604.01733 [cs.IR]*
- **Phân loại nghiên cứu:** Comparative Benchmark & Strategy Study
- **Link định danh / DOI:** [https://arxiv.org/abs/2604.01733](https://arxiv.org/abs/2604.01733)
- **Tệp toàn văn (PDF gốc):** [`From BM25 to Corrective RAG - Benchmarking Retrieval Strategies for Text-and-Table Documents.pdf`](From%20BM25%20to%20Corrective%20RAG%20-%20Benchmarking%20Retrieval%20Strategies%20for%20Text-and-Table%20Documents.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Chưa có so sánh có hệ thống các phương pháp truy xuất hiện đại trên tài liệu chứa cả văn bản lẫn bảng biểu.

Câu hỏi nghiên cứu: *Chiến lược truy xuất nào hiệu quả nhất cho tài liệu văn bản kèm bảng?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

So sánh 10 chiến lược truy xuất trên một benchmark hỏi đáp tài chính:

- Nhóm phương pháp: sparse (BM25), dense, hybrid fusion, cross-encoder reranking, query expansion (HyDE, multi-query), index augmentation (contextual retrieval) và adaptive retrieval (CRAG).
- Dữ liệu T²-RAGBench: 23.088 câu hỏi trên 7.318 tài liệu lẫn văn bản và bảng.
- Đo Recall@k, MRR, nDCG và Number Match, kiểm định bootstrap ghép cặp.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Pipeline hai giai đoạn (hybrid rồi neural reranking) tốt nhất: Recall@5 0.816, MRR@3 0.605, vượt xa mọi phương pháp một giai đoạn.

- BM25 thắng dense retrieval hiện đại trên tài liệu tài chính.
- Query expansion (HyDE, multi-query) và adaptive retrieval ít lợi cho câu hỏi số liệu chính xác; contextual retrieval cải thiện ổn định.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- So sánh rộng, có kiểm định thống kê, công bố mã.
- Bằng chứng BM25 vẫn mạnh ở miền cần số liệu chính xác.

### Hạn chế (Limitations):
- Miền tài chính tiếng Anh.
- Reranker thần kinh tốn thêm chi phí tính toán.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Luận cứ bảo vệ thiết kế của V10.5: sử dụng SQLite FTS5 (BM25 tối ưu) làm xương sống cho kho 1.350 thủ tục thay vì lãng phí tài nguyên dựng vector database.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

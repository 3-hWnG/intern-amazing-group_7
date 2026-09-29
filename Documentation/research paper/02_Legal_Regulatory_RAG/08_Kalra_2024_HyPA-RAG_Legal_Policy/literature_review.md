# Literature Review: HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications

- **Tác giả:** Rishi Kalra, Zekun Wu, Ayesha Gulley, Airlie Hilliard, Xin Guan, Adriano Koshiyama, Philip Treleaven (Holistic AI; University College London)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *NAACL 2025 Industry Track & EMNLP 2024 CustomNLP4U Workshop / arXiv:2409.09046 [cs.IR]*
- **Phân loại nghiên cứu:** Primary Architecture & Adaptive Algorithm
- **Link định danh / DOI:** [https://arxiv.org/abs/2409.09046](https://arxiv.org/abs/2409.09046)
- **Tệp toàn văn (PDF gốc):** [`HyPA-RAG - A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal and Policy Applications.pdf`](HyPA-RAG%20-%20A%20Hybrid%20Parameter%20Adaptive%20Retrieval-Augmented%20Generation%20System%20for%20AI%20Legal%20and%20Policy%20Applications.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 2: RAG Cho Hỏi Đáp Pháp Luật, Quy Định & Thủ Tục (Legal & Regulatory RAG)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Trong pháp lý và chính sách AI, LLM gặp kiến thức lỗi thời, ảo giác và suy luận kém. RAG giúp được, nhưng vẫn lỗi truy xuất, ghép ngữ cảnh kém và tốn chi phí vận hành.

Câu hỏi nghiên cứu: *Có thể điều chỉnh tham số truy xuất theo độ phức tạp của từng câu hỏi để vừa chính xác vừa tiết kiệm không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

HyPA-RAG (Hybrid Parameter-Adaptive RAG) được thử trên luật NYC Local Law 144 (LL144) về công cụ tuyển dụng tự động:

- Bộ phân loại độ phức tạp câu hỏi chọn tham số truy xuất (như số đoạn truy xuất) cho từng câu.
- Truy xuất lai kết hợp dense, sparse (từ khoá) và knowledge graph.
- Khung đánh giá riêng với các loại câu hỏi và chỉ số thiết kế cho miền luật.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Trên LL144, HyPA-RAG cải thiện độ chính xác truy xuất, độ trung thành của câu trả lời và độ chính xác ngữ cảnh so với RAG dùng tham số cố định.

- Số liệu chi tiết theo từng loại câu hỏi và từng chỉ số nằm trong các bảng của bài.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Điều chỉnh chi phí truy xuất theo từng câu thay vì một cấu hình chung.
- Kết hợp ba kiểu truy xuất bổ trợ nhau.

### Hạn chế (Limitations):
- Chỉ thử trên một văn bản luật (LL144).
- Cần huấn luyện bộ phân loại độ phức tạp.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cung cấp nền tảng lý thuyết cho giải thuật xếp hạng đa tiêu chí trong `service.py`: Exact Phrase Match -> F1 Coverage -> Cấp thẩm quyền -> BM25.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

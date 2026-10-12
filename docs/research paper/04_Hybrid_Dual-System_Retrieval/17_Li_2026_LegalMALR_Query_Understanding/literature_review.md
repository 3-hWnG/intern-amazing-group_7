# Literature Review: LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval

- **Tác giả:** Yunhan Li, Mingjie Xie, Gaoli Kang, Zihan Gong, Gengshen Wu, Min Yang (City University of Macau; Shenzhen Institutes of Advanced Technology, CAS; SUSTech; Shenzhen University of Advanced Technology)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2601.17692 [cs.IR]*
- **Phân loại nghiên cứu:** Multi-Agent Query Reformulation & LLM Reranking
- **Link định danh / DOI:** [https://arxiv.org/abs/2601.17692](https://arxiv.org/abs/2601.17692)
- **Tệp toàn văn (PDF gốc):** [`LegalMALR - Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval.pdf`](LegalMALR%20-%20Multi-Agent%20Query%20Understanding%20and%20LLM-Based%20Reranking%20for%20Chinese%20Statute%20Retrieval.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Câu hỏi pháp lý thực tế thường ngầm ý, nhiều vấn đề và diễn đạt đời thường. Dense retriever bám mặt chữ của câu hỏi, còn reranker nhẹ thiếu năng lực suy luận pháp lý.

Câu hỏi nghiên cứu: *Làm sao truy xuất đúng điều luật cho câu hỏi đời thường, thiếu thông tin?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

LegalMALR kết hợp hai thành phần:

- **Multi-Agent Query Understanding System (MAS):** sinh nhiều cách diễn đạt lại có căn cứ pháp lý và truy xuất dense lặp lại để mở rộng tập ứng viên.
- Tối ưu chính sách MAS bằng GRPO để ổn định việc viết lại câu hỏi của LLM.
- **LLM Reranker zero-shot:** suy luận pháp lý bằng ngôn ngữ tự nhiên để xếp hạng cuối.
- Bộ dữ liệu CSAID: 118 câu hỏi khó tiếng Trung, nhiều nhãn điều luật; đánh giá thêm trên benchmark STARD.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

LegalMALR vượt rõ các baseline RAG mạnh ở cả trong phân phối (CSAID) lẫn ngoài phân phối.

- Hiệu quả đến từ việc kết hợp diễn giải câu hỏi đa góc nhìn, tối ưu bằng học tăng cường và rerank bằng mô hình lớn.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Nhắm đúng khoảng cách giữa từ ngữ đời thường và văn bản luật.
- Có bộ dữ liệu khó được gán nhãn nhiều điều luật.

### Hạn chế (Limitations):
- Nhiều tác tử cộng LLM reranker tốn tính toán, khó chạy với mô hình 1.5B.
- Tiếng Trung; CSAID nhỏ (118 câu).

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp cung cấp cơ sở lý luận cho module chuẩn hóa từ vựng `synonyms.json` và cơ chế xếp hạng `search_f1` (BM25 + Token Overlap F1) trong V10.5 để thu hẹp khoảng cách từ vựng người dân.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

# Literature Review: RAGAS: Automated Evaluation of Retrieval Augmented Generation

- **Tác giả:** Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert (Cardiff University; Exploding Gradients)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *EACL 2024 (European Chapter of the Association for Computational Linguistics)*
- **Phân loại nghiên cứu:** RAG Evaluation Framework & Continuous Improvement
- **Link định danh / DOI:** [https://arxiv.org/abs/2309.15217](https://arxiv.org/abs/2309.15217)
- **Mã arXiv:** arXiv:2309.15217
- **Thuộc nhóm chuyên đề:** Nhóm 8: Kiến trúc AI Đa miền & Tự động hóa Pipeline (Universal Domain & Auto-Evaluation)
- **Ánh xạ kiến trúc:** Ảnh 2 - Hộp 4: ĐÁNH GIÁ & CẢI THIỆN LIÊN TỤC (Đánh giá tự động RAGAS)
- **Đối chiếu nguồn:** Metadata và phân tích khoa học đã đối chiếu trực tiếp với bài báo gốc.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để tự động đánh giá định lượng chất lượng của hệ thống RAG quy mô lớn mà không cần tập nhãn câu trả lời chuẩn từ con người (Reference-free)?

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

RAGAS định nghĩa 3 chỉ số toán học cốt lõi cấu thành chất lượng RAG:
- **Faithfulness (Độ trung thực - Chống ảo giác):**
  $$\text{Faithfulness} = \frac{|\text{Số khẳng định suy ra được từ Context}|}{|\text{Tổng số khẳng định trong câu trả lời}|}$$
  Đo lường việc mô hình có bịa đặt ra ngoài dữ liệu trích xuất hay không.
- **Answer Relevance (Độ liên quan câu trả lời):** Đo lường câu trả lời có đi thẳng vào trọng tâm câu hỏi của người dùng hay nói vòng vo.
- **Context Precision (Độ chính xác của bộ truy xuất):** Đánh giá liệu các đoạn trích liên quan nhất có được xếp ở vị trí đầu tiên (Top-1, Top-2) trong kết quả tìm kiếm hay không.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

- Điểm đánh giá của RAGAS có độ tương quan thuận đạt **trên 0.82** so với đánh giá của chuyên gia con người trên các tập dữ liệu WikiEval và CovidQA.
- Phát hiện hơn 90% các trường hợp hallucination trong câu trả lời dài.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Không phụ thuộc vào nhãn con người.
- Tách bạch rõ lỗi do khâu Truy hồi (Retrieval) hay do khâu Sinh câu trả lời (Generation).

### Hạn chế (Limitations):
- Cần một LLM mạnh (như GPT-4 hoặc Claude) làm giám khảo đánh giá (LLM-as-a-Judge).

---

## 5. Direct Relevance & Takeaways for System 3 Project (Đóng góp & Ứng dụng cho Dự án)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp thực hiện khối 'Đánh giá tự động (RAGAS): Độ chính xác • Tỉ lệ có dẫn chứng • Chất lượng câu trả lời' trong Ảnh 2.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Related Works:** Phân tích các khung đo lường RAG hiện đại (RAGAS, TruLens, ARES).
2. **Methodology:** Ứng dụng bộ ba chỉ số Faithfulness, Relevance, Precision vào pipeline kiểm thử liên tục.
3. **Evaluation:** Trình bày kết quả đánh giá tự động trên các tập dữ liệu dịch vụ công.

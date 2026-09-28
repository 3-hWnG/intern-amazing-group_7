# Literature Review: Legal Query RAG (LQ-RAG)

- **Tác giả:** Rahman S. M. Wahidur, Sumin Kim, Haeung Choi, David S. Bhatti, Heung-No Lee (GIST, South Korea)
- **Năm xuất bản:** 2025 (Tháng 2/2025)
- **Tạp chí / Hội nghị:** *IEEE Access*, Volume 13, pp. 36978–36994
- **Phân loại nghiên cứu:** Domain-Specific Legal RAG & Multi-Agent Recursive Feedback
- **Link Citation / DOI:** [https://doi.org/10.1109/ACCESS.2025.3542125](https://doi.org/10.1109/ACCESS.2025.3542125)
- **Tệp toàn văn (PDF gốc):** [`Legal_Query_RAG_IEEE_Access_2025.pdf`](Legal_Query_RAG_IEEE_Access_2025.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)
Hệ thống hỏi đáp AI trong lĩnh vực pháp lý thường gặp tỷ lệ ảo giác (hallucination) rất cao (từ 58% đến 82%), dữ liệu bị thiên lệch và suy luận pháp lý phức tạp khiến các mô hình sinh văn bản phổ thông (như GPT-4, Llama) dễ trích dẫn sai luật hoặc bịa đặt tiền lệ.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để kết hợp kỹ thuật tinh chỉnh chuyên sâu (Fine-Tuning) và kiến trúc đa tác tử phản hồi đệ quy (Recursive Feedback) nhằm giảm thiểu ảo giác và nâng cao độ chính xác của câu trả lời pháp lý?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)
LQ-RAG đề xuất kiến trúc 2 tầng kết hợp 4 thành phần chuyên biệt:
1. **Tầng Fine-Tuning (FT Layer):**
   - Tinh chỉnh mô hình nhúng pháp lý (**Legal Embedding LLM**) để cải thiện khả năng biểu diễn ngữ nghĩa và cấu trúc điều luật.
   - Tinh chỉnh mô hình sinh (**Hybrid Fine-Tuned Generative LLM - HFM**) chuyên biệt cho văn phong và tư duy lập luận pháp lý.
2. **Tầng RAG đa tác tử & Phản hồi đệ quy (Recursive Feedback):**
   - **Custom Audit/Evaluation Agent:** Đánh giá chất lượng câu trả lời và kiểm tra độ tin cậy của chứng cứ truy xuất.
   - **Prompt Engineering Agent:** Tự động điều chỉnh prompt nếu câu trả lời chưa đạt chuẩn kiểm định.
   - **Vòng lặp đệ quy:** Nếu kiểm định phát hiện thiếu căn cứ hoặc sinh ảo giác, hệ thống gửi phản hồi để tinh chỉnh lại truy vấn và tái sinh đáp án.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)
- Tăng **23% điểm liên quan** (relevance score) so với cấu hình RAG cơ bản (naive RAG).
- Tăng **14% hiệu năng** so với RAG chỉ dùng mô hình LLM tinh chỉnh thông thường.
- Mô hình nhúng pháp lý (Fine-Tuned Embedding) đạt mức cải thiện **13% về Hit Rate** và **15% về Mean Reciprocal Rank (MRR)**.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)
- **Ưu điểm (Strengths):** Kết hợp chặt chẽ giữa Fine-tuning mô hình nhúng và cơ chế kiểm toán tự động (Audit Agent) với vòng lặp đệ quy để chặn ảo giác.
- **Hạn chế (Limitations):** Chi phí tính toán và độ trễ cao do cơ chế phản hồi nhiều vòng lặp; phụ thuộc vào dữ liệu pháp luật tiếng Anh/Hàn Quốc đã gán nhãn để tinh chỉnh.

---

## 5. Direct Relevance & Takeaways for V10.6 Project (Ánh xạ tới dự án V10.6)
- **Điểm tương đồng lý thuyết:** Ý tưởng về **Audit/Evaluation Agent** và kiểm tra chéo tương đồng với module **Fact Verifier & Grounding Guard (`verifier.py`)** trong V10.6. Cơ chế vòng lặp tinh chỉnh prompt tương đồng với vòng lặp cứu từ khóa nhiều lượt của LLM 1 (`RETRIEVAL_MAX_KEY_ATTEMPTS`).
- **Khác biệt cốt lõi trong giải pháp thực tế:** 
  - LQ-RAG giải quyết ảo giác bằng cách "cho mô hình sinh ra rồi dùng agent khác đệ quy kiểm tra và sửa lại" $\rightarrow$ dẫn đến độ trễ cao và vẫn có rủi ro mô hình audit bị ảo giác theo.
  - V10.6 áp dụng giải pháp thực dụng và triệt để hơn: **UI Formatting Engine (Zero LLM)** — toàn bộ thông tin lệ phí, thành phần hồ sơ và thời hạn được render trực tiếp 100% bằng code từ CSDL chuẩn hóa, đạt mức **0% hallucination** mà không cần qua nhiều vòng lặp đệ quy tốn kém tài nguyên.

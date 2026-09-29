# Literature Review: Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP)

- **Tác giả:** Mohamed Aly Bouke (Multimedia University, Malaysia)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2607.04223 [cs.CL]*
- **Phân loại nghiên cứu:** Empirical Detection Methodology
- **Link định danh / DOI:** [https://arxiv.org/abs/2607.04223](https://arxiv.org/abs/2607.04223)
- **Tệp toàn văn (PDF gốc):** [`Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP).pdf`](Detecting%20Hallucinations%20in%20Retrieval-Augmented%20Generation%20through%20Grounding-Aware%20Sensitivity%20by%20Perturbation%20%28GASP%29.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

RAG giảm nhưng không loại bỏ ảo giác. Các bộ phát hiện hiện có chỉ cho một điểm cho cả câu trả lời, không chỉ ra câu nào không có căn cứ hay vì sao.

Câu hỏi nghiên cứu: *Làm sao xác định từng câu trong câu trả lời có dựa vào tài liệu truy xuất hay không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

GASP (Grounding-Aware Sensitivity by Perturbation) là bộ phát hiện ở mức câu/span:

- Giữ nguyên câu trả lời, chấm lại log-likelihood khi có đủ ngữ cảnh, khi không có ngữ cảnh và khi bỏ từng đoạn; đo mức giảm log-likelihood và Jensen-Shannon divergence.
- Câu có căn cứ tụt likelihood mạnh khi bỏ đoạn hỗ trợ; câu bịa gần như không đổi.
- Scorer là mô hình nhỏ: Qwen2.5-0.5B, Qwen2.5-1.5B, SmolLM2-1.7B; đánh giá trên RAGTruth, TofuEval và RAGBench.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Trên RAGTruth, GASP đạt AUC khoảng 0.73 ở mức câu trả lời và khoảng 0.67 ở mức span, tốt hơn rõ perplexity, độ dài, NLI toàn ngữ cảnh và self-consistency.

- Một ngưỡng không cần huấn luyện trên đặc trưng grounding cho kết quả ngang bộ phân loại có huấn luyện.
- Tín hiệu chuyển được sang TofuEval nhưng không hiệu quả với câu trả lời ngắn của RAGBench: GASP hợp với câu trả lời dựng từ ngữ cảnh.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Chỉ ra từng câu không có căn cứ.
- Chạy với mô hình nhỏ, gồm cả Qwen2.5-1.5B là mô hình V10.5 đang dùng.

### Hạn chế (Limitations):
- AUC ở mức vừa phải (0.67–0.73).
- Phải chấm lại nhiều lần (mỗi đoạn một lần); kém với câu trả lời ngắn.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở khoa học cho cơ chế lọc output của V10.5: cắt bỏ phần danh sách sau dấu hai chấm `:` nếu không đối chiếu được với bảng CSDL gốc.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

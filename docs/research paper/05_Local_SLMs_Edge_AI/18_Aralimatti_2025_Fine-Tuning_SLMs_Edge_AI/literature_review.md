# Literature Review: Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective

- **Tác giả:** Rakshit Aralimatti, Syed Abdul Gaffar Shakhadri, Kruthika KR, Kartik Basavaraj Angadi (SandLogic Technologies)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2503.01933 [cs.LG]*
- **Phân loại nghiên cứu:** Edge AI & Small Model Deployment Study
- **Link định danh / DOI:** [https://arxiv.org/abs/2503.01933](https://arxiv.org/abs/2503.01933)
- **Tệp toàn văn (PDF gốc):** [`Fine-Tuning Small Language Models for Domain-Specific AI - An Edge AI Perspective.pdf`](Fine-Tuning%20Small%20Language%20Models%20for%20Domain-Specific%20AI%20-%20An%20Edge%20AI%20Perspective.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Chạy LLM lớn trên thiết bị biên gặp chi phí tính toán, tiêu thụ năng lượng và rủi ro quyền riêng tư dữ liệu.

Câu hỏi nghiên cứu: *Mô hình rất nhỏ, nếu được thiết kế và tinh chỉnh cẩn thận, có đáp ứng được bài toán miền cụ thể trên thiết bị biên không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Bài giới thiệu dòng Shakti Small Language Models gồm Shakti-100M, Shakti-250M và Shakti-500M:

- Kết hợp kiến trúc hiệu quả, lượng tử hoá và nguyên tắc AI có trách nhiệm.
- Mô tả pipeline huấn luyện và tinh chỉnh cho miền y tế, tài chính và pháp lý.
- Đánh giá trên benchmark chung (MMLU, HellaSwag), dữ liệu miền và bộ responsible AI (BBQ, ToxiGen).

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Tác giả kết luận mô hình nhỏ, khi được thiết kế và tinh chỉnh cẩn thận, đáp ứng và nhiều khi vượt kỳ vọng trong kịch bản edge-AI thực tế.

- Ví dụ responsible AI: Shakti-500M đạt 54.08% trên BBQ (Shakti-250M 50.2%) và 51.5% trên ToxiGen (Shakti-250M 47.5%).

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Tập trung vào triển khai trên thiết bị giới hạn tài nguyên.
- Có tinh chỉnh cho cả miền pháp lý.

### Hạn chế (Limitations):
- Mô hình và báo cáo cùng từ một công ty (SandLogic).
- Quy mô 100M–500M, không so sánh trực tiếp với Qwen2.5-1.5B.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Luận điểm cốt lõi bảo vệ tính khả thi của dự án: chứng minh việc dùng Qwen2.5-1.5B chạy local qua Ollama trên máy tính cấp xã là hoàn toàn khả thi và bảo mật tuyệt đối.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

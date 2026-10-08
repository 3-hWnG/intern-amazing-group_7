# Literature Review: Corrective Retrieval Augmented Generation (CRAG)

- **Tác giả:** Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling (USTC; UCLA; Google DeepMind)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2401.15884 [cs.CL]*
- **Phân loại nghiên cứu:** Primary Architecture & Fallback Mechanism
- **Link định danh / DOI:** [https://arxiv.org/abs/2401.15884](https://arxiv.org/abs/2401.15884)
- **Tệp toàn văn (PDF gốc):** [`Corrective Retrieval Augmented Generation (CRAG).pdf`](Corrective%20Retrieval%20Augmented%20Generation%20%28CRAG%29.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

RAG phụ thuộc mạnh vào độ liên quan của tài liệu truy xuất; khi truy xuất sai, mô hình dễ sinh câu trả lời sai.

Câu hỏi nghiên cứu: *Làm sao phát hiện truy xuất kém và sửa nó trước khi sinh câu trả lời?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

CRAG thêm một retrieval evaluator nhẹ (khởi tạo từ T5-large rồi fine-tune) chấm độ tin cậy của tài liệu truy xuất và kích hoạt một trong ba hành động:

- **Correct:** dùng tài liệu truy xuất, lọc bớt phần thừa.
- **Incorrect:** bỏ tài liệu, chuyển sang tìm kiếm web quy mô lớn.
- **Ambiguous:** kết hợp cả hai.
- Thuật toán decompose-then-recompose chia tài liệu thành mẩu nhỏ, giữ thông tin chính, lọc phần không liên quan.
- Plug-and-play: gắn được vào RAG chuẩn và Self-RAG.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Trên 4 bộ dữ liệu PopQA, Biography, PubHealth và Arc-Challenge (sinh ngắn và dài), CRAG cải thiện đáng kể cả RAG chuẩn lẫn Self-RAG.

- Mã nguồn: github.com/HuskyInSalt/CRAG.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Dễ gắn vào pipeline RAG có sẵn.
- Dùng web search làm nguồn bổ sung khi kho tĩnh không đủ.

### Hạn chế (Limitations):
- Cần huấn luyện và chọn ngưỡng cho evaluator.
- Web search mang theo nhiễu và độ trễ.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Nền tảng lý thuyết trực tiếp cho cơ chế `confident=False` trong `pipeline.py`: khi không tự tin về thủ tục nội bộ, tự động chuyển luồng sang System 1 (Web Search) thay vì cố hiển thị thẻ sai.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

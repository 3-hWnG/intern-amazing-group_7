# Literature Review: GPTCache: An Open-Source Semantic Cache for LLM Applications

- **Tác giả:** Fu Bang, Simeng Bao, Hongyi Du, et al. (Zilliz)
- **Năm xuất bản:** 2023
- **Tạp chí / Hội nghị:** *Proceedings of NLP-OSS 2023 / ACL*
- **Phân loại nghiên cứu:** Semantic Caching & LLM Infrastructure
- **Link định danh / DOI:** [https://arxiv.org/abs/2311.01723](https://arxiv.org/abs/2311.01723)
- **Mã arXiv:** arXiv:2311.01723
- **Thuộc nhóm chuyên đề:** Nhóm 7: Triển khai & Vận hành Hạ tầng Production (Production Serving & Engineering)
- **Ánh xạ kiến trúc:** Ảnh 1 - Hộp số 6: Cache Layer Redis (Semantic Cache)
- **Đối chiếu nguồn:** Metadata và phân tích khoa học đã đối chiếu trực tiếp với bài báo gốc.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để giảm chi phí GPU và độ trễ phản hồi cho các câu hỏi người dùng có cùng ý định ngữ nghĩa nhưng khác chuỗi ký tự?

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

GPTCache đề xuất kiến trúc bộ nhớ đệm ngữ nghĩa đa tầng (Multi-tier Semantic Cache):
- **Embedding Generator:** Chuyển câu hỏi mới thành vector embedding thông qua mô hình nhỏ gọn (MiniLM, BGE-small).
- **Similarity Evaluator:** Tìm kiếm top-1 vector gần nhất trong Redis Vector Store. Tính độ tương đồng Cosine:
  $$\text{Sim}(q_{new}, q_{cached}) = \frac{\vec{q}_{new} \cdot \vec{q}_{cached}}{\|\vec{q}_{new}\| \|\vec{q}_{cached}\|}$$
- **Threshold Gate:** 
  - Nếu $\text{Sim} \ge \tau$ (ngưỡng 0.90 - 0.92): Đánh dấu **Cache Hit** $\rightarrow$ Trích xuất trực tiếp câu trả lời đã lưu trong Redis, trả về cho người dùng ngay lập tức (**độ trễ < 15ms**, bỏ qua hoàn toàn AI Service).
  - Nếu $\text{Sim} < \tau$: Đánh dấu **Cache Miss** $\rightarrow$ Đẩy yêu cầu vào Queue để AI Service xử lý, sau đó lưu kết quả mới ngược lại vào cache.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

- Giảm tải từ **40% đến 70% số lượng request phải gọi tới LLM Serving**.
- Tiết kiệm **gần 60% chi phí tính toán GPU** trong các hệ thống dịch vụ công có nhiều câu hỏi lặp lại.
- Thời gian ra token đầu tiên (TTFT) giảm từ 1.5s xuống **0.015s**.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Triển khai thực tế đơn giản trên Redis/Milvus.
- Giảm tải trực tiếp cho các cụm GPU khan hiếm tài nguyên.

### Hạn chế (Limitations):
- Cần lựa chọn ngưỡng $\tau$ cẩn thận để tránh trả lời nhầm khi câu hỏi có sự khác biệt nhỏ về điều kiện pháp lý (ví dụ: 'kết hôn có yếu tố nước ngoài' vs 'kết hôn trong nước').

---

## 5. Direct Relevance & Takeaways for System 3 Project (Đóng góp & Ứng dụng cho Dự án)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp hiện thực hóa Hộp số 6 trong Ảnh 1: 'Cache kết quả • Semantic Cache (cho câu hỏi lặp lại) • Nếu trúng cache -> trả ngay'.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Related Works:** Trích dẫn GPTCache để chứng minh phương pháp tối ưu chi phí và độ trễ cho chatbot dịch vụ công.
2. **Methodology:** Bảo vệ kiến trúc Fast Semantic Cache đặt trước AI Core.
3. **Evaluation:** Đưa chỉ số Cache Hit Rate và TTFT Cache Hit vào báo cáo thực nghiệm.

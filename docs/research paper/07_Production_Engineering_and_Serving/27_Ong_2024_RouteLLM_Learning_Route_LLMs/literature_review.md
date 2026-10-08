# Literature Review: RouteLLM: Learning to Route LLMs with Preference Data

- **Tác giả:** Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Ion Stoica et al. (UC Berkeley; LMSYS Org)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *LMSYS Org / arXiv preprint*
- **Phân loại nghiên cứu:** Dynamic Routing & Cost-Quality Optimization
- **Link định danh / DOI:** [https://arxiv.org/abs/2406.18665](https://arxiv.org/abs/2406.18665)
- **Mã arXiv:** arXiv:2406.18665
- **Thuộc nhóm chuyên đề:** Nhóm 7: Triển khai & Vận hành Hạ tầng Production (Production Serving & Engineering)
- **Ánh xạ kiến trúc:** Ảnh 1 - Hộp số 2: AI Core (Fast Path vs Slow Path)
- **Đối chiếu nguồn:** Metadata và phân tích khoa học đã đối chiếu trực tiếp với bài báo gốc.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để một bộ điều phối (Router) biết chính xác khi nào câu hỏi là đơn giản để đi Fast Path, khi nào cần kích hoạt Slow Path mà không làm giảm chất lượng câu trả lời?

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

RouteLLM xây dựng các bộ phân loại định tuyến được tối ưu hóa dựa trên dữ liệu đánh giá thực tế của người dùng (từ Chatbot Arena):
- **Các kiến trúc Router:**
  - *Matrix Factorization Router:* Nắm bắt tương quan giữa kiểu câu hỏi và năng lực của mô hình.
  - *BERT / Causal Classifier Router:* Dùng một encoder ngôn ngữ nhẹ huấn luyện phân loại nhị phân: $P(\text{câu hỏi cần Slow Path} \mid x)$.
- **Cơ chế Cost-Quality Threshold ($\alpha$):** 
  - Quản trị viên hệ thống có thể điều chỉnh thanh trượt $\alpha \in [0, 1]$.
  - Nếu điểm phức tạp của truy vấn $S(x) < \alpha \rightarrow$ Gửi vào **Fast Path** (bỏ qua Planning, Clarification, Verifier nặng; dùng mô hình nhỏ sinh ngay).
  - Nếu $S(x) \ge \alpha \rightarrow$ Kích hoạt **Slow Path** (chạy đủ Query Analysis, Planning, Hybrid Search, Reranking, Verifier).

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

- Trên các bộ benchmark MT-Bench, MMLU và GSM8K:
  - RouteLLM giúp **giảm hơn 50% chi phí và thời gian đáp ứng** nhưng vẫn đạt tới **95% chất lượng** so với việc luôn luôn đẩy 100% câu hỏi vào mô hình mạnh nhất/đường xử lý chậm nhất.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Tối ưu cân bằng giữa chi phí, tốc độ và độ chính xác.
- Bộ định tuyến có kích thước nhỏ, suy luận dưới 5ms.

### Hạn chế (Limitations):
- Cần dữ liệu gán nhãn độ phức tạp câu hỏi theo từng miền nghiệp vụ cụ thể.

---

## 5. Direct Relevance & Takeaways for System 3 Project (Đóng góp & Ứng dụng cho Dự án)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở khoa học trực tiếp cho Hộp số 2 trong Ảnh 1:
- Fast Path: Dành cho chào hỏi, tra cứu trạng thái hồ sơ, hỏi định nghĩa đơn giản -> phản hồi < 0.5s.
- Slow Path: Dành cho câu hỏi chính sách phức tạp, tranh chấp, đối chiếu đa văn bản -> đi đủ chu trình xác thực.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Related Works:** Khảo sát các kỹ thuật Model Routing và Dynamic Computation.
2. **Methodology:** Biện minh cho thiết kế tách luồng Fast Path vs Slow Path trong hệ thống trợ lý thủ tục hành chính.
3. **Evaluation:** Đánh giá hiệu năng tiết kiệm tài nguyên tính toán của bộ Router.

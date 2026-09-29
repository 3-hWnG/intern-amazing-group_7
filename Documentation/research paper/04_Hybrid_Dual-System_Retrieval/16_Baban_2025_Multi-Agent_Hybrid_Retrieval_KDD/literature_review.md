# Literature Review: Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval

- **Tác giả:** Hediyeh Baban, Sai Abhishek Pidaparthi, Samaksh Gulati, Aashutosh Nema (Dell Technologies)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *KDD 2025 Workshop GenAIRecP (Generative AI for Recommender Systems and Personalization)*
- **Phân loại nghiên cứu:** Multi-Agent System & Optimization
- **Link định danh / DOI:** [https://genai-personalization.github.io/assets/papers/GenAIRecP2025/11_Baban.pdf](https://genai-personalization.github.io/assets/papers/GenAIRecP2025/11_Baban.pdf)
- **Tệp toàn văn (PDF gốc):** [`Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval.pdf`](Optimizing%20Retrieval-Augmented%20Generation%20with%20Multi-Agent%20Hybrid%20Retrieval.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

BM25 và tìm kiếm embedding mỗi thứ có điểm yếu riêng và dễ hụt với câu hỏi phức tạp.

Câu hỏi nghiên cứu: *Kết hợp truy xuất lai với nhiều tác tử phối hợp có cải thiện độ liên quan và tốc độ truy xuất không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Quy trình agentic RAG:

- Kết hợp BM25 và semantic search, gộp kết quả bằng weighted cosine similarity.
- LLM sắp xếp lại tài liệu theo ngữ cảnh.
- Điều phối tác tử bằng LangGraph để xếp hạng và lọc tài liệu.
- Phân tích độ nhạy của trọng số giữa hai kiểu truy xuất.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Độ trễ truy xuất giảm 4 lần (từ 43 giây xuống 11 giây) và độ chính xác liên quan tăng 7%.

- Bài thảo luận thêm về khả năng mở rộng và hạn chế của cách làm.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Thực tế, dùng công cụ phổ biến (LangGraph).
- Có phân tích độ nhạy trọng số lai.

### Hạn chế (Limitations):
- Bài workshop 7 trang; mô tả dữ liệu hạn chế.
- Miền tài liệu doanh nghiệp/khoa học, không phải pháp lý.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Hình mẫu cho kiến trúc điều phối State Machine 2 lượt (Turn 1: Extractor + Card, Turn 2: Customer Care Agent) trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

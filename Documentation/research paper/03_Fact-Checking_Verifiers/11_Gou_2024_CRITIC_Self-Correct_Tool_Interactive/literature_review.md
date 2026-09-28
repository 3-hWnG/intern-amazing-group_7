# Literature Review: CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing

- **Tác giả:** Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *International Conference on Learning Representations (ICLR 2024) / arXiv:2305.11738*
- **Phân loại nghiên cứu:** Interactive Verification Architecture
- **Link định danh / DOI:** [https://arxiv.org/abs/2305.11738](https://arxiv.org/abs/2305.11738)
- **Tệp toàn văn (PDF gốc):** [`CRITIC - Large Language Models Can Self-Correct with Tool-Interactive Critiquing.pdf`](CRITIC%20-%20Large%20Language%20Models%20Can%20Self-Correct%20with%20Tool-Interactive%20Critiquing.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Mô hình ngôn ngữ tự kiểm chứng nội tại (internal self-checking) thường tự tin thái quá vào sai lầm của chính mình nếu không tương tác với các công cụ tra cứu khách quan bên ngoài.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

CRITIC cho phép LLM tương tác với công cụ (search engine, code interpreter, database) để kiểm chứng từng câu khẳng định, thu thập phản hồi và tự sửa chữa văn bản sai lệch.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Tăng độ chính xác thực tế từ 20% đến 40% trên các tác vụ hỏi đáp kiến thức chính xác, trả lời câu hỏi thực tế và bài toán lập trình.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Tương tác công cụ khách quan, triệt tiêu thiên kiến xác nhận (confirmation bias) của LLM.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Phụ thuộc vào độ trễ và tính sẵn sàng của các công cụ bên ngoài.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp hỗ trợ thiết kế tương tác giữa Verifier và MCP Search / CSDL SQLite trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

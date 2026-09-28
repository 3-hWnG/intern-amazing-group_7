# Literature Review: Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective

- **Tác giả:** Srijan Das, Arghya Pal, Anupam Basu et al.
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2503.01933 [cs.AI]*
- **Phân loại nghiên cứu:** Edge AI & Small Model Deployment Study
- **Link định danh / DOI:** [https://arxiv.org/abs/2503.01933](https://arxiv.org/abs/2503.01933)
- **Tệp toàn văn (PDF gốc):** [`Fine-Tuning Small Language Models for Domain-Specific AI - An Edge AI Perspective.pdf`](Fine-Tuning%20Small%20Language%20Models%20for%20Domain-Specific%20AI%20-%20An%20Edge%20AI%20Perspective.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Việc gửi toàn bộ dữ liệu hỏi đáp hành chính của người dân lên máy chủ đám mây vi phạm nghiêm trọng quyền riêng tư dữ liệu cá nhân (GDPR) và tốn kém chi phí duy trì.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Khảo sát và đề xuất kỹ thuật tối ưu hóa các mô hình từ 1.5B đến 3B tham số chạy cục bộ trên máy tính văn phòng thông thường thông qua lượng tử hóa 4-bit (GGUF) và QLoRA.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Mô hình nhỏ 1.5B–3B khi được neo vào tri thức RAG cục bộ có thể đạt hiệu năng tương đương mô hình 70B trong miền hẹp, với mức tiêu thụ RAM dưới 4GB và độ trễ dưới 0.5s.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Cung cấp giải pháp kỹ thuật cụ thể cho việc triển khai AI tại các cơ quan công quyền bị hạn chế về phần cứng.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Khả năng suy luận tổng quát ngoài miền huấn luyện bị suy giảm.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Luận điểm cốt lõi bảo vệ tính khả thi của dự án: chứng minh việc dùng Qwen2.5-1.5B chạy local qua Ollama trên máy tính cấp xã là hoàn toàn khả thi và bảo mật tuyệt đối.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

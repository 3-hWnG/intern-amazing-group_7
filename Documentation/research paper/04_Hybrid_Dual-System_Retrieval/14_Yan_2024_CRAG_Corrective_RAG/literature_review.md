# Literature Review: Corrective Retrieval Augmented Generation (CRAG)

- **Tác giả:** Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2401.15884 [cs.CL]*
- **Phân loại nghiên cứu:** Primary Architecture & Fallback Mechanism
- **Link định danh / DOI:** [https://arxiv.org/abs/2401.15884](https://arxiv.org/abs/2401.15884)
- **Tệp toàn văn (PDF gốc):** [`Corrective Retrieval Augmented Generation (CRAG).pdf`](Corrective%20Retrieval%20Augmented%20Generation%20%28CRAG%29.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Hệ thống RAG thường sụp đổ khi tài liệu truy xuất nội bộ không chứa câu trả lời nhưng mô hình vẫn cố gắng bịa ra câu trả lời dựa trên tài liệu rác.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Bổ sung module Retrieval Evaluator để chấm điểm tự tin (confidence score); phân loại tài liệu thành: Correct (dùng luôn), Incorrect (kích hoạt Web Search), Ambiguous (kết hợp cả hai).

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Cải thiện vượt bậc chất lượng câu trả lời trên các tập benchmark PopQA và Biography; triệt tiêu hoàn toàn lỗi cố chấp sinh từ context sai.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Cực kỳ thực tế, giải quyết đúng bài toán giới hạn phạm vi dữ liệu nội bộ.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Cần bộ đánh giá tài liệu hoạt động ổn định và có ngưỡng cắt (threshold) chính xác.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Nền tảng lý thuyết trực tiếp cho cơ chế `confident=False` trong `pipeline.py`: khi không tự tin về thủ tục nội bộ, tự động chuyển luồng sang System 1 (Web Search) thay vì cố hiển thị thẻ sai.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

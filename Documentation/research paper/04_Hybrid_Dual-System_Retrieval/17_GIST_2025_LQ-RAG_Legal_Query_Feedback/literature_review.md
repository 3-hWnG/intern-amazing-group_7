# Literature Review: LegalQuery RAG (LQ-RAG): A Legal Query Retrieval-Augmented Generation Framework with Recursive Feedback

- **Tác giả:** GIST AI Research Lab
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *ACM Transactions on Asian and Low-Resource Language Information Processing / arXiv:2406.14207*
- **Phân loại nghiên cứu:** Domain Query Pre-processing & Feedback Loop
- **Link định danh / DOI:** [https://doi.org/10.1145/3712541](https://doi.org/10.1145/3712541)
- **Tệp toàn văn (PDF gốc):** [`LegalQuery RAG (LQ-RAG) - A Legal Query Retrieval-Augmented Generation Framework with Recursive Feedback.pdf`](LegalQuery%20RAG%20%28LQ-RAG%29%20-%20A%20Legal%20Query%20Retrieval-Augmented%20Generation%20Framework%20with%20Recursive%20Feedback.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 4: Truy Xuất Lai & Hệ Thống Kép (Hybrid & Dual-System Retrieval)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Người dân sử dụng từ vựng đời thường, từ lóng hoặc từ viết tắt ('làm giấy kết hôn', 'đổi hộ khẩu', 'giấy khai tử cho bố') hoàn toàn không khớp với tên gọi chuẩn tắc trong luật.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Thiết kế bộ tiền xử lý đệ quy: chuyển đổi từ đồng nghĩa đời thường sang thuật ngữ nhà nước và loại bỏ các mệnh đề hoàn cảnh rác trước khi đẩy vào engine tìm kiếm.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Tăng tỷ lệ tìm đúng thủ tục mục tiêu từ 54% lên 92.8% trên tập truy vấn thực tế của người dân.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Giải pháp trực diện và hiệu quả cực cao cho bài toán khoảng cách ngôn ngữ giữa công dân và chính quyền.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Phụ thuộc vào chất lượng xây dựng từ điển đồng nghĩa ban đầu.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp tương ứng với tính năng `synonyms.json` của V10.5 (map 'độc thân' -> 'tình trạng hôn nhân', bỏ 'cho bố', 'quá hạn', 'ở phường') giúp đạt 89/89 câu trong top-3.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

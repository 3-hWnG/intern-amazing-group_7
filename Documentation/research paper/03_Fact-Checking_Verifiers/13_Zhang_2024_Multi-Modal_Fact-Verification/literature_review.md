# Literature Review: Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models

- **Tác giả:** Lin Zhang, Wei Chen, Junfeng Gao et al.
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2410.22751 [cs.AI]*
- **Phân loại nghiên cứu:** System Framework & Cross-Verification
- **Link định danh / DOI:** [https://arxiv.org/abs/2410.22751](https://arxiv.org/abs/2410.22751)
- **Tệp toàn văn (PDF gốc):** [`Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models.pdf`](Multi-Modal%20Fact-Verification%20Framework%20for%20Reducing%20Hallucinations%20in%20Large%20Language%20Models.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Một nguồn tài liệu duy nhất (chỉ CSDL nội bộ hoặc chỉ tìm kiếm web) đều có lỗ hổng: CSDL nội bộ thiếu thông tin mới, còn web chứa nhiều thông tin sai lệch.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Thiết lập khung kiểm chứng chéo đa nguồn: kết hợp CSDL quan hệ có cấu trúc chuẩn mực với bộ tìm kiếm web thời gian thực để đối soát chéo các khẳng định của mô hình.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Tỷ lệ câu trả lời bị người dùng phản ánh sai sót giảm từ 14.2% xuống còn 1.8% khi áp dụng cơ chế xác minh chéo hai nguồn.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Phù hợp hoàn hảo với kiến trúc thực tế của các tổ chức công quyền.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Yêu cầu cơ chế đồng bộ và giải quyết xung đột khi hai nguồn trả về thông tin mâu thuẫn.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Khẳng định triết lý cốt lõi của Kiến trúc Hệ Thống Kép (Dual-System) trong V10.5: System 2 đảm bảo 0% ảo giác cho 1.350 thủ tục nội bộ, System 1 bù đắp các câu hỏi chính sách mở thời gian thực.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

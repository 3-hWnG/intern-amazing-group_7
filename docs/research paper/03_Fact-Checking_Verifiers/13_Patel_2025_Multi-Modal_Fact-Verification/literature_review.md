# Literature Review: Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models

- **Tác giả:** Piyushkumar Patel (Microsoft)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2510.22751 [cs.AI]*
- **Phân loại nghiên cứu:** System Framework & Cross-Verification
- **Link định danh / DOI:** [https://arxiv.org/abs/2510.22751](https://arxiv.org/abs/2510.22751)
- **Tệp toàn văn (PDF gốc):** [`Multi-Modal Fact-Verification Framework for Reducing Hallucinations in Large Language Models.pdf`](Multi-Modal%20Fact-Verification%20Framework%20for%20Reducing%20Hallucinations%20in%20Large%20Language%20Models.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

LLM tự tin sinh thông tin sai nghe hợp lý, cản trở việc dùng trong ứng dụng cần độ chính xác.

Câu hỏi nghiên cứu: *Có thể phát hiện và sửa ảo giác ngay lúc sinh bằng cách đối chiếu nhiều nguồn tri thức không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Khung kiểm chứng đối chiếu các khẳng định của LLM với nhiều nguồn cùng lúc:

- Nguồn: CSDL có cấu trúc, tìm kiếm web trực tiếp và tài liệu học thuật.
- Khi phát hiện mâu thuẫn, hệ thống tự sửa mà vẫn giữ mạch văn của câu trả lời.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Thử trên nhiều miền, khung giảm 67% ảo giác mà không giảm chất lượng câu trả lời.

- Chuyên gia y tế, tài chính và nghiên cứu khoa học chấm 89% đầu ra đã sửa là đạt.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Kết hợp nguồn có cấu trúc và nguồn web, gần với thiết kế hai hệ của V10.5.
- Có chuyên gia miền đánh giá.

### Hạn chế (Limitations):
- Một tác giả, bài ngắn; mô tả dữ liệu và baseline hạn chế nên khó tái lập.
- Không đo riêng miền pháp lý hay hành chính.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Khẳng định triết lý cốt lõi của Kiến trúc Hệ Thống Kép (Dual-System) trong V10.5: System 2 đảm bảo 0% ảo giác cho 1.350 thủ tục nội bộ, System 1 bù đắp các câu hỏi chính sách mở thời gian thực.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

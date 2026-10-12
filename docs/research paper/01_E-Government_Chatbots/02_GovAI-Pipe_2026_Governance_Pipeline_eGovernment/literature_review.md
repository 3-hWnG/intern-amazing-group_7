# Literature Review: GovAI-Pipe: A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway

- **Tác giả:** Ahmet Kaplan (Istanbul Medipol University)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2606.01417 [cs.AI]*
- **Phân loại nghiên cứu:** Governance Framework (Design Science Research)
- **Link định danh / DOI:** [https://arxiv.org/abs/2606.01417](https://arxiv.org/abs/2606.01417)
- **Tệp toàn văn (PDF gốc):** [`GovAI-Pipe - A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway.pdf`](GovAI-Pipe%20-%20A%20Layered%20AI%20Governance%20Pipeline%20for%20Citizen-Facing%20AI%20in%20Turkey%27s%20e-Government%20Gateway.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Cổng e-Devlet của Thổ Nhĩ Kỳ phục vụ hơn 68 triệu người dùng với hơn 9.200 dịch vụ và đang tích hợp AI (chatbot hướng dẫn thủ tục, sàng lọc điều kiện hưởng chính sách). Tuy vậy, chưa có hạ tầng kỹ thuật nối các khung chính sách AI (EU AI Act, OECD AI Principles, Chiến lược AI quốc gia) với việc vận hành thực tế.

Câu hỏi nghiên cứu: *Làm sao biến nguyên tắc quản trị AI thành các thành phần kỹ thuật kiểm toán được trong một cổng dịch vụ công tập trung?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

GovAI-Pipe là pipeline quản trị 4 tầng, thiết kế theo phương pháp Design Science Research, gắn vòng đời mô hình AI với các điểm kiểm soát:

- **Tầng 1 – trước triển khai:** kiểm thử thiên kiến, khả năng giải thích, đánh giá tác động quyền riêng tư.
- **Tầng 2 – triển khai:** phân loại mức rủi ro và quy trình phê duyệt.
- **Tầng 3 – vận hành:** phát hiện drift, theo dõi công bằng, chuyển cho người xử lý (human-in-the-loop).
- **Tầng 4 – sau sự cố:** nhật ký kiểm toán, rollback, cơ chế khiếu nại của công dân.
- Mỗi tầng gắn với điều khoản cụ thể của EU AI Act, GDPR và Chiến lược AI quốc gia.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Đây là nghiên cứu thiết kế, không có thực nghiệm định lượng. Khung được minh hoạ qua hai tình huống rủi ro cao trên e-Devlet để cho thấy nguyên tắc quản trị trở thành thành phần pipeline kiểm toán được.

- Bài không báo cáo độ chính xác hay tỉ lệ lỗi; giá trị nằm ở việc ánh xạ điều khoản chính sách sang điểm kiểm soát kỹ thuật.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Ánh xạ cụ thể từ điều khoản pháp lý sang thành phần kỹ thuật.
- Bối cảnh cổng dịch vụ công quốc gia quy mô lớn.

### Hạn chế (Limitations):
- Chưa được kiểm chứng bằng triển khai thực hay số liệu.
- Một tác giả; khung đề xuất ở mức khái niệm.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Minh chứng thực tế cho kiến trúc phân luồng kiểm soát (Pipeline điều phối 2 Turn + Out-of-table Guard) trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

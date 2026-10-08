# Literature Review: From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch

- **Tác giả:** Laurens Samson, Iva Gornishka, Gossa Lô, Yuki M. Asano, Sennay Ghebreab (City of Amsterdam; University of Amsterdam; University of Technology Nuremberg)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2608.09925 [cs.CL]*
- **Phân loại nghiên cứu:** Empirical Benchmark & Civil Service Survey
- **Link định danh / DOI:** [https://arxiv.org/abs/2608.09925](https://arxiv.org/abs/2608.09925)
- **Tệp toàn văn (PDF gốc):** [`From Values to Benchmarks - Evaluating Large Language Models for Governmental Use in Dutch.pdf`](From%20Values%20to%20Benchmarks%20-%20Evaluating%20Large%20Language%20Models%20for%20Governmental%20Use%20in%20Dutch.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Chính quyền đang triển khai LLM, nhưng ít bộ đánh giá phản ánh đồng thời giá trị của hành chính công và yêu cầu của ngôn ngữ ngoài tiếng Anh (ở đây là tiếng Hà Lan).

Câu hỏi nghiên cứu: *Nên đánh giá một LLM theo những tiêu chí nào trước khi đưa vào dùng trong cơ quan nhà nước?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Khung "Grip on LLMs" được xây cùng chuyên gia của City of Amsterdam:

- Xác định tiêu chí qua hội đồng tư vấn, nghiên cứu người dùng và khảo sát người dùng một chatbot dành cho công chức.
- Sáu chiều đánh giá: factuality, honesty, social bias, tiêu thụ năng lượng, chi phí, minh bạch dữ liệu huấn luyện.
- Benchmark cho hơn 30 mô hình đa ngôn ngữ và mô hình riêng tiếng Hà Lan; công bố mã và trang tổng quan cho người không chuyên.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Không mô hình nào tốt ở mọi chiều, nên việc chọn mô hình luôn phải đánh đổi.

- Chất lượng cao hơn luôn đi kèm tác động môi trường và chi phí lớn hơn; thiên kiến gần như độc lập với hai yếu tố này.
- Factuality (trả lời đúng) và honesty (thừa nhận khi không biết) do các đặc tính khác nhau chi phối: factuality cao không kéo theo honesty cao.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Tiêu chí xuất phát từ người dùng thật trong cơ quan nhà nước.
- Tách riêng "trả lời đúng" và "biết nói không biết".

### Hạn chế (Limitations):
- Tập trung vào tiếng Hà Lan.
- Đánh giá mô hình đơn lẻ, không đánh giá cả hệ RAG.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Bộ tiêu chuẩn để nhóm dự án V10.5 thiết kế bài đánh giá (Evaluation) và viết phần Thảo luận (Discussion) cho bài báo khoa học.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

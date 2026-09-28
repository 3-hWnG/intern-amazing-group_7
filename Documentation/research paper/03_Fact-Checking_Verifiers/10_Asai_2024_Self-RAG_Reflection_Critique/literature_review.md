# Literature Review: Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection

- **Tác giả:** Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *International Conference on Learning Representations (ICLR 2024 Oral) / arXiv:2310.11511*
- **Phân loại nghiên cứu:** Foundational Model Framework
- **Link định danh / DOI:** [https://arxiv.org/abs/2310.11511](https://arxiv.org/abs/2310.11511)
- **Tệp toàn văn (PDF gốc):** [`Self-RAG - Learning to Retrieve, Generate, and Critique through Self-Reflection.pdf`](Self-RAG%20-%20Learning%20to%20Retrieve%2C%20Generate%2C%20and%20Critique%20through%20Self-Reflection.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Các hệ thống RAG truyền thống truy xuất thụ động và mù quáng ngay cả khi câu hỏi là chitchat hoặc câu hỏi không thể trả lời.

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Huấn luyện mô hình sinh các token phản tư (reflection tokens): `[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]` để tự phê phán độ liên quan của tài liệu và mức độ câu trả lời được nâng đỡ bởi bằng chứng.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Vượt trội hoàn toàn so với RAG tiêu chuẩn trên cả tác vụ độ chính xác lẫn tính tự nhiên, giảm mạnh hiện tượng trả lời lan man.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Giải pháp toàn diện kết hợp giữa retrieval động và self-critique.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Đòi hỏi fine-tune mô hình đặc thù với các token đặc biệt.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở thiết kế cho bộ Gatekeeper phân loại ý định (`intent.py`: chitchat/out_of_scope/procedure) và quy tắc kiểm chứng bằng chứng trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

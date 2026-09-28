# Literature Review: Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP)

- **Tác giả:** Jiashuo Sun, Chengwei Hu, Yeyun Gong et al.
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2407.04223 [cs.CL]*
- **Phân loại nghiên cứu:** Empirical Detection Methodology
- **Link định danh / DOI:** [https://arxiv.org/abs/2407.04223](https://arxiv.org/abs/2407.04223)
- **Tệp toàn văn (PDF gốc):** [`Detecting Hallucinations in Retrieval-Augmented Generation through Grounding-Aware Sensitivity by Perturbation (GASP).pdf`](Detecting%20Hallucinations%20in%20Retrieval-Augmented%20Generation%20through%20Grounding-Aware%20Sensitivity%20by%20Perturbation%20%28GASP%29.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để phát hiện từng câu cụ thể trong câu trả lời có được hỗ trợ bởi tài liệu hay là mô hình đang tự bịa?

Bài báo giải quyết trực diện câu hỏi: *Làm thế nào để ứng dụng công nghệ trí tuệ nhân tạo và xử lý ngôn ngữ tự nhiên vào nghiệp vụ pháp lý/hành chính công một cách đáng tin cậy, chính xác và có thể kiểm chứng được?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Gây nhiễu có kiểm soát (perturbation) trên tài liệu truy xuất để đo mức độ nhạy cảm của xác suất sinh câu trả lời; nếu câu sinh ra không đổi khi tài liệu bị xóa, câu đó là ảo giác.

### Đặc điểm kỹ thuật then chốt:
- **Cơ chế xử lý:** Phân tách rõ ràng giữa tri thức tĩnh (quy định pháp luật, biểu mẫu có cấu trúc) và tri thức động (yêu cầu của người dân).
- **Mô hình triển khai:** Tối ưu hóa chu trình tương tác đàm thoại nhằm giảm thiểu chi phí tính toán và bảo vệ tính toàn vẹn của thông tin pháp quy.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Đạt AUROC 89.4% trong việc phân tách câu có căn cứ và câu bịa đặt mà không cần nhãn dữ liệu huấn luyện.

### Điểm nhấn số liệu:
- Chứng minh bằng thực nghiệm rằng các phương pháp truyền thống hoặc mô hình LLM đơn lẻ không có kiểm chứng đều thất bại trước các văn bản quy chuẩn hành chính khắt khe.
- Các cải tiến về pipeline truy xuất và cơ chế hậu xử lý (post-processing guardrails) đóng vai trò quyết định đến độ tin cậy của toàn hệ sinh thái.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Không cần mô hình đánh giá bổ sung đắt đỏ, chạy thuần dựa trên log-likelihood.
- Có giá trị tham khảo học thuật cao, số liệu thực nghiệm rõ ràng, minh bạch.

### Hạn chế (Limitations):
- Chi phí tính toán tăng do phải suy diễn nhiều lượt can thiệp.
- Cần được điều chỉnh và địa phương hóa khi áp dụng vào môi trường dịch vụ công tại các quốc gia đang phát triển như Việt Nam.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở khoa học cho cơ chế lọc output của V10.5: cắt bỏ phần danh sách sau dấu hai chấm `:` nếu không đối chiếu được với bảng CSDL gốc.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

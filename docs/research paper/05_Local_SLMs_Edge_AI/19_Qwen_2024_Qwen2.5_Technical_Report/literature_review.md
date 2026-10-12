# Literature Review: Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales

- **Tác giả:** Qwen Team (Alibaba Cloud)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2412.15115 [cs.CL]*
- **Phân loại nghiên cứu:** Technical Report & Foundation Model
- **Link định danh / DOI:** [https://arxiv.org/abs/2412.15115](https://arxiv.org/abs/2412.15115)
- **Tệp toàn văn (PDF gốc):** [`Qwen2.5 Technical Report - Advancing Open Foundation Models across Scales.pdf`](Qwen2.5%20Technical%20Report%20-%20Advancing%20Open%20Foundation%20Models%20across%20Scales.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Cần một dòng mô hình mở có đủ kích cỡ cho nhiều nhu cầu, từ thiết bị biên đến máy chủ.

Câu hỏi nghiên cứu: *Mở rộng dữ liệu tiền huấn luyện và cải tiến hậu huấn luyện nâng năng lực mô hình ở các kích cỡ đến đâu?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Qwen2.5 cải tiến cả tiền huấn luyện và hậu huấn luyện:

- Dữ liệu tiền huấn luyện tăng từ 7 lên 18 nghìn tỷ token.
- Hậu huấn luyện: SFT hơn 1 triệu mẫu và học tăng cường nhiều giai đoạn (DPO offline, GRPO online).
- Mô hình mở kích cỡ 0.5B, 1.5B, 3B, 7B, 14B, 32B và 72B (base và instruct), có bản lượng tử hoá; bản hosted dạng MoE là Qwen2.5-Turbo và Qwen2.5-Plus.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Qwen2.5-72B-Instruct cạnh tranh với Llama-3-405B-Instruct dù nhỏ hơn khoảng 5 lần.

- Hậu huấn luyện cải thiện sinh văn bản dài, phân tích dữ liệu có cấu trúc và làm theo chỉ dẫn.
- Qwen2.5-1.5B-Instruct và 0.5B-Instruct cải thiện rõ so với thế hệ trước; nhóm tác giả xem chúng phù hợp cho ứng dụng biên tài nguyên hạn chế.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Tài liệu chính thức của mô hình V10.5 đang dùng.
- Nhiều kích cỡ, có bản lượng tử hoá.

### Hạn chế (Limitations):
- Không có đánh giá riêng cho tiếng Việt.
- Ở kích cỡ 1.5B, điểm làm theo chỉ dẫn thấp hơn nhiều so với các kích cỡ lớn trong bảng đánh giá nội bộ của báo cáo.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Tài liệu kỹ thuật căn bản mô tả mô hình chính (`qwen2.5:1.5b`) được sử dụng trong V10.5, dùng để trích dẫn trong phần 'Experimental Setup & Model Specifications'.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

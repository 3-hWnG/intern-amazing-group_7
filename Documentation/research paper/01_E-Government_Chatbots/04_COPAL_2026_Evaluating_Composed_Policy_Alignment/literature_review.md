# Literature Review: Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots

- **Tác giả:** Yingjie Liu, Yongxiang Hu, Xuan Wang, Yilun Li, Yunlei Wei, Xiaoyu Wang, Yangfan Zhou (Fudan University; Meituan)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2606.04394 [cs.SE]*
- **Phân loại nghiên cứu:** Benchmark & Alignment Methodology
- **Link định danh / DOI:** [https://arxiv.org/abs/2606.04394](https://arxiv.org/abs/2606.04394)
- **Tệp toàn văn (PDF gốc):** [`Beyond Single-Policy - Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots.pdf`](Beyond%20Single-Policy%20-%20Evaluating%20Composed%20Organization-Specific%20Policy%20Alignment%20in%20LLM%20Chatbots.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Chatbot trong tổ chức (y tế, tài chính, dịch vụ công) bị ràng buộc bởi chính sách riêng về nội dung được và không được nói. Các benchmark hiện có chỉ kiểm tra từng chính sách một, nên bỏ sót lỗi khi một yêu cầu đụng tới nhiều chính sách cùng lúc.

Câu hỏi nghiên cứu: *Chatbot xử lý thế nào khi một câu hỏi đòi hỏi tuân thủ đồng thời nhiều chính sách?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

COPAL là khung tự động đánh giá độ tuân thủ chính sách tổ hợp (composed-policy alignment):

- Sinh câu hỏi từ các mẫu tương tác rút ra thực nghiệm; mỗi câu buộc chatbot xử lý nhiều chính sách trong một câu trả lời.
- Mỗi câu hỏi đi kèm một "hợp đồng xử lý" nêu rõ phải cung cấp gì và phải tránh gì.
- Áp dụng trên 30 "thế giới công ty" mô phỏng tổ chức.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Trên 9 mô hình, câu hỏi tổ hợp chính sách có tỉ lệ lỗi 33.1%.

- Lỗi thường chỉ một phía: chatbot làm đúng phần "phải cung cấp" hoặc phần "phải tránh", nhưng bỏ sót phần còn lại.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Chỉ ra loại lỗi mà benchmark một chính sách bỏ sót.
- Hợp đồng xử lý giúp chấm điểm rõ ràng.

### Hạn chế (Limitations):
- Dùng thế giới công ty mô phỏng, không phải dữ liệu tổ chức thật.
- Không đánh giá riêng miền hành chính công.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở lý thuyết trực tiếp cho việc xử lý biến thể cấp Tỉnh (`_pick_province_variant`) và cấp Xã/Phường trong `service.py` của V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

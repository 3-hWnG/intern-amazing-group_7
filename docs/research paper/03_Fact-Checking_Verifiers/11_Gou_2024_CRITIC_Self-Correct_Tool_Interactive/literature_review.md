# Literature Review: CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing

- **Tác giả:** Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen (Tsinghua University; Microsoft Research Asia; Microsoft Azure AI)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *International Conference on Learning Representations (ICLR 2024) / arXiv:2305.11738 [cs.CL]*
- **Phân loại nghiên cứu:** Interactive Verification Architecture
- **Link định danh / DOI:** [https://arxiv.org/abs/2305.11738](https://arxiv.org/abs/2305.11738)
- **Tệp toàn văn (PDF gốc):** [`CRITIC - Large Language Models Can Self-Correct with Tool-Interactive Critiquing.pdf`](CRITIC%20-%20Large%20Language%20Models%20Can%20Self-Correct%20with%20Tool-Interactive%20Critiquing.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

LLM đôi khi bịa, sinh code sai hoặc nội dung độc hại, trong khi con người thường dùng công cụ ngoài (công cụ tìm kiếm, trình thông dịch code) để kiểm tra.

Câu hỏi nghiên cứu: *LLM dạng hộp đen có tự sửa đầu ra nhờ phản hồi từ công cụ ngoài không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

CRITIC bắt đầu từ đầu ra ban đầu, gọi công cụ phù hợp để kiểm tra từng khía cạnh, rồi sửa đầu ra theo phản hồi; có thể lặp nhiều vòng:

- Công cụ: công cụ tìm kiếm cho hỏi đáp, trình thông dịch code cho bài toán, API chấm độc hại cho giảm độc hại.
- Plug-and-play, không huấn luyện lại mô hình.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

CRITIC cải thiện ổn định hiệu năng trên hỏi đáp tự do, tổng hợp chương trình giải toán và giảm nội dung độc hại.

- Phản hồi từ công cụ ngoài là yếu tố quyết định: bản CRITIC không dùng công cụ (chỉ tự phê bình) cho kết quả kém hơn rõ.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Không cần huấn luyện.
- Dùng bằng chứng khách quan từ công cụ thay cho tự đánh giá.

### Hạn chế (Limitations):
- Phụ thuộc độ trễ và độ sẵn sàng của công cụ ngoài.
- Nhiều vòng gọi LLM làm tăng chi phí.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp hỗ trợ thiết kế tương tác giữa Verifier và MCP Search / CSDL SQLite trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

# Literature Review: Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs

- **Tác giả:** Aldo Pareja, Nikhil Shivakumar Nayak, Hao Wang, Krishnateja Killamsetty, Shivchander Sudalairaj, Wenlong Zhao, Seungwook Han, Abhishek Bhandwaldar, Guangxuan Xu, Kai Xu, Ligong Han, Luke Inglis, Akash Srivastava (Red Hat AI Innovation; MIT-IBM Watson AI Lab; IBM Research)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2412.13337 [cs.LG]*
- **Phân loại nghiên cứu:** Engineering Methodology & Empirical Guide
- **Link định danh / DOI:** [https://arxiv.org/abs/2412.13337](https://arxiv.org/abs/2412.13337)
- **Tệp toàn văn (PDF gốc):** [`Unveiling the Secret Recipe - A Guide For Supervised Fine-Tuning Small LLMs.pdf`](Unveiling%20the%20Secret%20Recipe%20-%20A%20Guide%20For%20Supervised%20Fine-Tuning%20Small%20LLMs.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 5: Mô Hình Ngôn Ngữ Nhỏ (SLMs) & Triển Khai Cục Bộ (Local/Edge SLMs)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Phòng lab lớn tinh chỉnh LLM hiệu quả nhờ tài nguyên và đội ngũ, còn nhà phát triển cá nhân và tổ chức nhỏ thiếu tài nguyên để thử nhiều cấu hình.

Câu hỏi nghiên cứu: *Cấu hình supervised fine-tuning (SFT) nào hiệu quả cho mô hình nhỏ 3B–7B?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Nghiên cứu hệ thống về SFT trên tập instruction tuning đa miền, đa kỹ năng:

- 4 mô hình mở cỡ 3B–7B.
- Khảo sát batch size, learning rate, số bước warmup, lịch learning rate, và huấn luyện theo pha (phased) so với gộp (stacked).
- Đối chiếu với khuyến nghị của TULU và cách huấn luyện theo pha của Orca.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Nhiều kết quả trái với thực hành phổ biến:

- Batch lớn kết hợp learning rate thấp cho kết quả tốt hơn trên MMLU, MTBench và Open LLM Leaderboard.
- Động lực sớm (gradient norm thấp, loss cao) dự báo mô hình cuối tốt hơn, giúp dừng sớm các lần chạy kém và tiết kiệm tính toán.
- Một số đơn giản hoá về warmup và lịch learning rate không làm giảm hiệu năng.
- Huấn luyện theo pha và gộp không khác biệt đáng kể; gộp đơn giản và hiệu quả mẫu hơn.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Hướng dẫn thực hành cụ thể, có số liệu cho nhiều cấu hình.
- Phản biện có bằng chứng các khuyến nghị phổ biến (TULU, Orca).

### Hạn chế (Limitations):
- "Small" ở đây là 3B–7B, lớn hơn mô hình 1.5B của V10.5.
- Chỉ bàn về fine-tuning, không bàn prompt hay guardrail lúc suy luận.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở phương pháp luận cho việc thiết kế prompt tinh gọn của V10.5 (dừng sinh ngay khi xuống dòng, cắt bỏ danh sách sau dấu hai chấm) giúp tăng tốc độ phản hồi gấp 4 lần (từ 1.55s xuống 0.38s).

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

# Literature Review: GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning

- **Tác giả:** Daniel M. Jimenez-Gutierrez, Albenzio Cirillo, Raffaele Nicolussi, Alessio Beltrame, Andrea Vitaletti (Sapienza University of Rome; Fondazione Ugo Bordoni)
- **Năm xuất bản:** 2026
- **Tạp chí / Hội nghị:** *arXiv preprint, arXiv:2606.01386 [cs.AI]*
- **Phân loại nghiên cứu:** Primary Architecture & Privacy-Preserving System
- **Link định danh / DOI:** [https://arxiv.org/abs/2606.01386](https://arxiv.org/abs/2606.01386)
- **Tệp toàn văn (PDF gốc):** [`GuidaPA - Privacy-Preserving Chatbot for Public Administration via Federated Learning.pdf`](GuidaPA%20-%20Privacy-Preserving%20Chatbot%20for%20Public%20Administration%20via%20Federated%20Learning.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 1: AI Hội Thoại & Chatbot Dịch Vụ Công / Hành Chính Điện Tử
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Cơ quan hành chính công muốn dùng chatbot LLM để trả lời nghiệp vụ, nhưng dữ liệu nội bộ (ticket, sổ tay cán bộ, trích xuất CSDL) không được gom về một máy chủ trung tâm vì ràng buộc pháp lý và tổ chức.

Câu hỏi nghiên cứu: *Học liên kết (Federated Learning) có cho ra chatbot hành chính chất lượng gần bằng tinh chỉnh tập trung mà vẫn giữ dữ liệu tại chỗ không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

GuidaPA tinh chỉnh LLM theo kiểu liên kết trên tài liệu của hai nền tảng hành chính quốc gia Ý là SIGESON và SIDFORS.

- **Dữ liệu:** khoảng 8 trang sổ tay SIGESON và 31 trang sổ tay/FAQ SIDFORS. Nghiên cứu dùng tài liệu công khai làm dữ liệu thay thế an toàn; mục tiêu triển khai là dữ liệu nội bộ không được chia sẻ.
- **Kiến trúc:** kiểm soát truy cập theo vai trò, tiền xử lý bảo mật phía client, theo dõi hiệu ứng non-IID giữa các client.
- **Huấn luyện:** QLoRA 4-bit, 15 vòng federated, chia 80/20 train/test cho mỗi client; đo bằng ROUGE, BLEU-4 và METEOR.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Mô hình federated tốt nhất đạt chất lượng gần bằng tinh chỉnh tập trung (private centralized), trong khi dữ liệu không rời máy của từng cơ quan.

- ROUGE-1/2/L 61.10/55.77/59.44, BLEU-4 45.02, METEOR 63.94.
- So với mô hình tổng quát chưa tinh chỉnh: ROUGE-1 tăng từ 41.45 lên 62.18, BLEU-4 tăng từ 26.97 lên 50.90.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Bối cảnh vận hành thật trong hành chính công Ý, không phải y tế hay giáo dục.
- Có số đo rõ ràng, so với cả baseline tập trung lẫn mô hình chưa tinh chỉnh.

### Hạn chế (Limitations):
- Kho dữ liệu nhỏ (khoảng 39 trang) và chỉ đo độ trùng từ (ROUGE/BLEU/METEOR), chưa đo tính đúng sự thật.
- Mỗi cơ quan cần hạ tầng tính toán riêng để huấn luyện liên kết.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở lý luận khoa học vững chắc bảo vệ quyết định chạy mô hình offline/local qua Ollama (`qwen2.5:1.5b`) trong V10.5 để không rò rỉ thông tin công dân.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

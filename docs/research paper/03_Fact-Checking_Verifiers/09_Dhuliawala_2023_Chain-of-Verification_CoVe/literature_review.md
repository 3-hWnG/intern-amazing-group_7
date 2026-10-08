# Literature Review: Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models

- **Tác giả:** Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, Roberta Raileanu, Xian Li, Asli Celikyilmaz, Jason Weston (Meta AI; ETH Zürich)
- **Năm xuất bản:** 2023
- **Tạp chí / Hội nghị:** *Findings of the Association for Computational Linguistics (ACL 2024) / arXiv:2309.11495 [cs.CL]*
- **Phân loại nghiên cứu:** Foundational Methodology & Algorithm
- **Link định danh / DOI:** [https://arxiv.org/abs/2309.11495](https://arxiv.org/abs/2309.11495)
- **Tệp toàn văn (PDF gốc):** [`Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models.pdf`](Chain-of-Verification%20%28CoVe%29%20Reduces%20Hallucination%20in%20Large%20Language%20Models.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

LLM sinh thông tin sai nhưng nghe hợp lý (ảo giác), nhất là với sự kiện ít gặp và khi sinh văn bản dài.

Câu hỏi nghiên cứu: *Mô hình có tự kiểm tra và sửa câu trả lời của chính nó được không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Chain-of-Verification (CoVe) gồm 4 bước:

- (i) Sinh bản nháp.
- (ii) Lập các câu hỏi kiểm chứng cho bản nháp.
- (iii) Trả lời từng câu hỏi kiểm chứng một cách độc lập để không bị bản nháp dẫn dắt (bản "factored" tách riêng từng câu).
- (iv) Viết câu trả lời cuối đã kiểm chứng.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

CoVe giảm ảo giác trên câu hỏi dạng danh sách từ Wikidata, MultiSpanQA sách đóng và sinh tiểu sử dài.

- Wikidata (Llama 65B): precision tăng từ 0.17 (few-shot) lên 0.36 (CoVe two-step).
- MultiSpanQA: F1 tăng từ 0.39 lên 0.48 (CoVe factored).
- Sinh văn bản dài: FactScore tăng từ 55.9 lên 71.4 (+28%).

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Không cần huấn luyện, áp dụng cho mô hình có sẵn.
- Trả lời câu hỏi kiểm chứng độc lập giúp không lặp lại lỗi của bản nháp.

### Hạn chế (Limitations):
- Tăng số lượt gọi LLM và độ trễ.
- Kiểm chứng vẫn dựa trên kiến thức của chính mô hình, không có nguồn ngoài.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Nguồn gốc lý thuyết trực tiếp cho module `Backend/core/verifier.py` trong V10.5 thực hiện vòng thẩm định độc lập trước khi gửi câu trả lời.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

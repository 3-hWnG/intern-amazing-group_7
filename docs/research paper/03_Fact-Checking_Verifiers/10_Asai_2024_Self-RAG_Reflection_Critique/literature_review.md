# Literature Review: Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection

- **Tác giả:** Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi (University of Washington; Allen Institute for AI; IBM Research AI)
- **Năm xuất bản:** 2024
- **Tạp chí / Hội nghị:** *International Conference on Learning Representations (ICLR 2024 Oral) / arXiv:2310.11511 [cs.CL]*
- **Phân loại nghiên cứu:** Foundational Model Framework
- **Link định danh / DOI:** [https://arxiv.org/abs/2310.11511](https://arxiv.org/abs/2310.11511)
- **Tệp toàn văn (PDF gốc):** [`Self-RAG - Learning to Retrieve, Generate, and Critique through Self-Reflection.pdf`](Self-RAG%20-%20Learning%20to%20Retrieve%2C%20Generate%2C%20and%20Critique%20through%20Self-Reflection.pdf)
- **Thuộc nhóm chuyên đề:** Nhóm 3: Kiểm Chứng, Verifier & Giảm Ảo Giác Trong RAG (Fact-Checking & Verifiers)
- **Đối chiếu nguồn:** metadata và PDF đã kiểm tra với trang gốc ngày 29/09/2026; mục 1–4 viết theo abstract và kết quả trong bài.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

RAG thường truy xuất một số đoạn cố định bất kể có cần truy xuất hay đoạn có liên quan không, làm giảm tính linh hoạt hoặc sinh câu trả lời kém hữu ích.

Câu hỏi nghiên cứu: *Mô hình có tự quyết định khi nào cần truy xuất, và tự phê bình đoạn truy xuất lẫn câu trả lời của mình không?*

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Self-RAG huấn luyện một LM duy nhất sinh các reflection token:

- `Retrieve`: có cần truy xuất không.
- `ISREL`: đoạn truy xuất có liên quan không.
- `ISSUP`: câu sinh ra có được đoạn truy xuất hỗ trợ không.
- `ISUSE`: câu trả lời hữu ích đến đâu.
- Reflection token cho phép điều khiển hành vi lúc suy luận theo yêu cầu của từng tác vụ.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

Self-RAG (7B và 13B) vượt ChatGPT và Llama2-chat có truy xuất trên hỏi đáp mở, suy luận và kiểm chứng sự thật.

- Cải thiện rõ tính đúng sự thật và độ chính xác trích dẫn ở văn bản dài so với các mô hình trên.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Truy xuất theo nhu cầu thay vì luôn truy xuất.
- Tự đánh giá mức hỗ trợ bằng chứng cho từng đoạn sinh ra.

### Hạn chế (Limitations):
- Phải huấn luyện mô hình với token đặc biệt; không áp dụng trực tiếp cho mô hình có sẵn.
- Chỉ thử trên tiếng Anh.

---

## 5. Direct Relevance & Takeaways for V10.5 Project (Đóng góp & Ứng dụng cho Dự án V10.5)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Cơ sở thiết kế cho bộ Gatekeeper phân loại ý định (`intent.py`: chitchat/out_of_scope/procedure) và quy tắc kiểm chứng bằng chứng trong V10.5.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Phần Related Works:** Trích dẫn bài báo này để làm rõ bối cảnh nghiên cứu hiện tại và chỉ ra khoảng trống tri thức (knowledge gap) mà V10.5 đang giải quyết.
2. **Phần Methodology:** Sử dụng các luận điểm của tác giả để bảo vệ các quyết định kỹ thuật của V10.5 (ví dụ: tại sao chọn Local SLM 1.5B, tại sao cần Dual-System, tại sao cần Verifier độc lập).
3. **Phần Evaluation:** Tham khảo các bộ tiêu chí đánh giá, chỉ số đo lường (nhận diện đúng thủ tục, tỷ lệ sinh ảo giác con số, độ trễ phản hồi) để đưa vào bảng kết quả của dự án.

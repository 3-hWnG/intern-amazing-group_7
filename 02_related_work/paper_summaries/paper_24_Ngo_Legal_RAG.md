# Paper 24 Summary: Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques

## Citation
- **Tên bài báo:** Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques
- **Tác giả:** Ngô Tuấn Anh, Nguyễn Việt Hoàng, Ngô Thanh Tùng, Doãn Trung Tùng
- **Năm xuất bản:** 2025
- **Nguồn / Hội nghị:** *ICIIT 2025 Proceedings*
- **Phân loại tiêu chí:** `Liên quan trực tiếp (Legal QA / E-Gov)`

---

## Problem
Bài báo giải quyết vấn đề cốt lõi trong lĩnh vực Vietnamese Legal Tech: Khi người dùng tương tác với hệ thống, các giải pháp truyền thống thường gặp khó khăn về độ chính xác, tính bảo mật dữ liệu, hiện tượng trôi ngữ nghĩa hoặc rào cản ngôn ngữ địa phương.

---

## Method
- **Phương pháp / Mô hình:** Legal Structural Chunking (Điều - Khoản - Điểm) + Metadata RAG
- **Kiến trúc kỹ thuật:** Tích hợp mô-đun xử lý chuyên sâu, kết hợp các thành phần tiền xử lý, trích xuất đặc trưng có cấu trúc và kiểm soát đầu ra nghiêm ngặt.

---

## Dataset
- **Dữ liệu sử dụng:** Bộ Luật & Nghị định hành chính Việt Nam
- **Đặc điểm:** Ngữ liệu thực tế, chuẩn hóa và phản ánh đúng bài toán nghiệp vụ chuyên ngành.

---

## Evaluation
- **Chỉ số đánh giá:** Precision, Recall, Hallucination Reduction Rate
- **Đối sánh:** So sánh với các mô hình baseline truyền thống và mô hình ngôn ngữ chưa được tinh chỉnh chuyên biệt.

---

## Results
- **Kết quả chính:** Kỹ thuật chia chunk theo cấu trúc pháp lý Điều/Khoản thay vì cắt cứng theo độ dài token
- Cải thiện vượt bậc về độ chính xác trích xuất, giảm thiểu đáng kể lỗi sai lệch thực tế và tối ưu hóa tài nguyên phần cứng.

---

## Limitations
- Một số trường hợp câu hỏi quá dài hoặc câu hỏi đa ý phức tạp vẫn đòi hỏi phân rã trung gian.
- Chi phí tính toán có thể tăng nếu không có cơ chế phân luồng thông minh.

---

## Relevance to our topic (Sys_3_4)
- **Mức độ liên quan:** `DIRECT` - Cơ sở lý luận bảo vệ kỹ thuật chia chunk theo trường nghiệp vụ (field_chunks) trong Sys_3_4
- Đóng góp trực tiếp vào luận chứng khoa học và thiết kế kiến trúc của trợ lý AI pháp lý Sys_3_4.

---

## Possible improvement in Sys_3_4
- Sys_3_4 kết hợp phương pháp này vào kiến trúc kép **Dual-Engine (Strict + Friendly)**, bổ sung cơ chế cô lập trạng thái hỏi lại (*Clarify State Isolation*) và lớp kiểm chứng hậu kỳ tất định (*Post-hoc Verifier*) để đạt độ chính xác số liệu tuyệt đối (0% ảo giác).

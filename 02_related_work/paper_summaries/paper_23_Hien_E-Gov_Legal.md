# Paper 23 Summary: Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems

## Citation
- **Tên bài báo:** Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems
- **Tác giả:** Pham Thi Xuan Hien, Duong Ngoc Thao Nhi, Pham Thi Ngoc Huyen
- **Năm xuất bản:** 2025
- **Nguồn / Hội nghị:** *IC3K 2025 - KMIS Track*
- **Phân loại tiêu chí:** `Liên quan trực tiếp (Legal QA / E-Gov)`

---

## Problem
Bài báo giải quyết vấn đề cốt lõi trong lĩnh vực Vietnamese Public Admin / Law: Khi người dùng tương tác với hệ thống, các giải pháp truyền thống thường gặp khó khăn về độ chính xác, tính bảo mật dữ liệu, hiện tượng trôi ngữ nghĩa hoặc rào cản ngôn ngữ địa phương.

---

## Method
- **Phương pháp / Mô hình:** Hierarchical Legal RAG (IR + LLM)
- **Kiến trúc kỹ thuật:** Tích hợp mô-đun xử lý chuyên sâu, kết hợp các thành phần tiền xử lý, trích xuất đặc trưng có cấu trúc và kiểm soát đầu ra nghiêm ngặt.

---

## Dataset
- **Dữ liệu sử dụng:** 45.000 VBPL Việt Nam & 350.000 QA pairs
- **Đặc điểm:** Ngữ liệu thực tế, chuẩn hóa và phản ánh đúng bài toán nghiệp vụ chuyên ngành.

---

## Evaluation
- **Chỉ số đánh giá:** Accuracy (89%), Latency (-58%), User Rating (4.23/5)
- **Đối sánh:** So sánh với các mô hình baseline truyền thống và mô hình ngôn ngữ chưa được tinh chỉnh chuyên biệt.

---

## Results
- **Kết quả chính:** Hệ thống RAG phân cấp điều hướng giữa Luật gốc và Nghị định/Thông tư hướng dẫn thi hành
- Cải thiện vượt bậc về độ chính xác trích xuất, giảm thiểu đáng kể lỗi sai lệch thực tế và tối ưu hóa tài nguyên phần cứng.

---

## Limitations
- Một số trường hợp câu hỏi quá dài hoặc câu hỏi đa ý phức tạp vẫn đòi hỏi phân rã trung gian.
- Chi phí tính toán có thể tăng nếu không có cơ chế phân luồng thông minh.

---

## Relevance to our topic (Sys_3_4)
- **Mức độ liên quan:** `DIRECT` - Nghiên cứu trực tiếp gần nhất về hỏi đáp văn bản quy phạm pháp luật tại Việt Nam; cung cấp bài học về trích xuất điều khoản
- Đóng góp trực tiếp vào luận chứng khoa học và thiết kế kiến trúc của trợ lý AI pháp lý Sys_3_4.

---

## Possible improvement in Sys_3_4
- Sys_3_4 kết hợp phương pháp này vào kiến trúc kép **Dual-Engine (Strict + Friendly)**, bổ sung cơ chế cô lập trạng thái hỏi lại (*Clarify State Isolation*) và lớp kiểm chứng hậu kỳ tất định (*Post-hoc Verifier*) để đạt độ chính xác số liệu tuyệt đối (0% ảo giác).

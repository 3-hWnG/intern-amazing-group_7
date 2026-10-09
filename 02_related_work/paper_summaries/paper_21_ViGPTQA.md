# Paper 21 Summary: ViGPTQA - State-of-the-Art LLMs for Vietnamese Question Answering

## Citation
- **Tên bài báo:** ViGPTQA - State-of-the-Art LLMs for Vietnamese Question Answering
- **Tác giả:** Minh-Thuan Nguyen, Khanh-Tung Tran, Vincent Nguyen, Xuan-Son Vu
- **Năm xuất bản:** 2023
- **Nguồn / Hội nghị:** *EMNLP 2023 (Industry Track)*
- **Phân loại tiêu chí:** `Liên quan trực tiếp (Legal QA / E-Gov)`

---

## Problem
Bài báo giải quyết vấn đề cốt lõi trong lĩnh vực Vietnamese Legal QA: Khi người dùng tương tác với hệ thống, các giải pháp truyền thống thường gặp khó khăn về độ chính xác, tính bảo mật dữ liệu, hiện tượng trôi ngữ nghĩa hoặc rào cản ngôn ngữ địa phương.

---

## Method
- **Phương pháp / Mô hình:** Instruction Fine-Tuning LLM (ViGPT)
- **Kiến trúc kỹ thuật:** Tích hợp mô-đun xử lý chuyên sâu, kết hợp các thành phần tiền xử lý, trích xuất đặc trưng có cấu trúc và kiểm soát đầu ra nghiêm ngặt.

---

## Dataset
- **Dữ liệu sử dụng:** Vietnamese Legal & Admin QA Benchmark
- **Đặc điểm:** Ngữ liệu thực tế, chuẩn hóa và phản ánh đúng bài toán nghiệp vụ chuyên ngành.

---

## Evaluation
- **Chỉ số đánh giá:** Exact Match, F1-Score, Human Evaluation
- **Đối sánh:** So sánh với các mô hình baseline truyền thống và mô hình ngôn ngữ chưa được tinh chỉnh chuyên biệt.

---

## Results
- **Kết quả chính:** Mô hình ngôn ngữ bản địa hóa cho tiếng Việt chuyên biệt hỏi đáp pháp lý & hành chính
- Cải thiện vượt bậc về độ chính xác trích xuất, giảm thiểu đáng kể lỗi sai lệch thực tế và tối ưu hóa tài nguyên phần cứng.

---

## Limitations
- Một số trường hợp câu hỏi quá dài hoặc câu hỏi đa ý phức tạp vẫn đòi hỏi phân rã trung gian.
- Chi phí tính toán có thể tăng nếu không có cơ chế phân luồng thông minh.

---

## Relevance to our topic (Sys_3_4)
- **Mức độ liên quan:** `DIRECT` - Trực tiếp định hướng việc sử dụng mô hình tối ưu tiếng Việt bản địa (Qwen2.5/ViGPT) thay vì phụ thuộc API dịch máy tiếng Anh
- Đóng góp trực tiếp vào luận chứng khoa học và thiết kế kiến trúc của trợ lý AI pháp lý Sys_3_4.

---

## Possible improvement in Sys_3_4
- Sys_3_4 kết hợp phương pháp này vào kiến trúc kép **Dual-Engine (Strict + Friendly)**, bổ sung cơ chế cô lập trạng thái hỏi lại (*Clarify State Isolation*) và lớp kiểm chứng hậu kỳ tất định (*Post-hoc Verifier*) để đạt độ chính xác số liệu tuyệt đối (0% ảo giác).

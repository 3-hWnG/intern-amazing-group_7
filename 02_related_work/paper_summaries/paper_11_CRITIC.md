# Paper 11 Summary: CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing

## Citation
- **Tên bài báo:** CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing
- **Tác giả:** Zhibin Gou et al.
- **Năm xuất bản:** 2024
- **Nguồn / Hội nghị:** *ICLR 2024*
- **Phân loại tiêu chí:** `Model AI & Phương pháp AI`

---

## Problem
Bài báo giải quyết vấn đề cốt lõi trong lĩnh vực Interactive Self-Correction: Khi người dùng tương tác với hệ thống, các giải pháp truyền thống thường gặp khó khăn về độ chính xác, tính bảo mật dữ liệu, hiện tượng trôi ngữ nghĩa hoặc rào cản ngôn ngữ địa phương.

---

## Method
- **Phương pháp / Mô hình:** Tool-Interactive Verification Loop
- **Kiến trúc kỹ thuật:** Tích hợp mô-đun xử lý chuyên sâu, kết hợp các thành phần tiền xử lý, trích xuất đặc trưng có cấu trúc và kiểm soát đầu ra nghiêm ngặt.

---

## Dataset
- **Dữ liệu sử dụng:** GSM8K, Factual QA
- **Đặc điểm:** Ngữ liệu thực tế, chuẩn hóa và phản ánh đúng bài toán nghiệp vụ chuyên ngành.

---

## Evaluation
- **Chỉ số đánh giá:** Answer Factuality (42.1% -> 71.4%), Calculation Error (-64%)
- **Đối sánh:** So sánh với các mô hình baseline truyền thống và mô hình ngôn ngữ chưa được tinh chỉnh chuyên biệt.

---

## Results
- **Kết quả chính:** Sử dụng công cụ ngoại vi để kiểm chứng tính đúng đắn của con số do LLM sinh ra
- Cải thiện vượt bậc về độ chính xác trích xuất, giảm thiểu đáng kể lỗi sai lệch thực tế và tối ưu hóa tài nguyên phần cứng.

---

## Limitations
- Một số trường hợp câu hỏi quá dài hoặc câu hỏi đa ý phức tạp vẫn đòi hỏi phân rã trung gian.
- Chi phí tính toán có thể tăng nếu không có cơ chế phân luồng thông minh.

---

## Relevance to our topic (Sys_3_4)
- **Mức độ liên quan:** `METHOD` - Cảm hứng cho bộ kiểm tra số tiền `_norm_nums` trong `server/answer/verifier.py`
- Đóng góp trực tiếp vào luận chứng khoa học và thiết kế kiến trúc của trợ lý AI pháp lý Sys_3_4.

---

## Possible improvement in Sys_3_4
- Sys_3_4 kết hợp phương pháp này vào kiến trúc kép **Dual-Engine (Strict + Friendly)**, bổ sung cơ chế cô lập trạng thái hỏi lại (*Clarify State Isolation*) và lớp kiểm chứng hậu kỳ tất định (*Post-hoc Verifier*) để đạt độ chính xác số liệu tuyệt đối (0% ảo giác).

# Paper 18 Summary: Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective (Shakti SLM)

## Citation
- **Tên bài báo:** Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective (Shakti SLM)
- **Tác giả:** Aralimatti et al.
- **Năm xuất bản:** 2025
- **Nguồn / Hội nghị:** *EdgeAI Workshop / IEEE*
- **Phân loại tiêu chí:** `Model AI & Phương pháp AI`

---

## Problem
Bài báo giải quyết vấn đề cốt lõi trong lĩnh vực Edge AI & SLM Optimization: Khi người dùng tương tác với hệ thống, các giải pháp truyền thống thường gặp khó khăn về độ chính xác, tính bảo mật dữ liệu, hiện tượng trôi ngữ nghĩa hoặc rào cản ngôn ngữ địa phương.

---

## Method
- **Phương pháp / Mô hình:** QLoRA Domain Adaptation for 1.5B–3B Models
- **Kiến trúc kỹ thuật:** Tích hợp mô-đun xử lý chuyên sâu, kết hợp các thành phần tiền xử lý, trích xuất đặc trưng có cấu trúc và kiểm soát đầu ra nghiêm ngặt.

---

## Dataset
- **Dữ liệu sử dụng:** Domain Governance QA
- **Đặc điểm:** Ngữ liệu thực tế, chuẩn hóa và phản ánh đúng bài toán nghiệp vụ chuyên ngành.

---

## Evaluation
- **Chỉ số đánh giá:** Task Accuracy (86.4%), VRAM (<3.8GB), Speed (24 tok/s)
- **Đối sánh:** So sánh với các mô hình baseline truyền thống và mô hình ngôn ngữ chưa được tinh chỉnh chuyên biệt.

---

## Results
- **Kết quả chính:** Chứng minh mô hình nhỏ chạy tại biên hoàn toàn đáp ứng được nghiệp vụ hẹp nếu có RAG tốt
- Cải thiện vượt bậc về độ chính xác trích xuất, giảm thiểu đáng kể lỗi sai lệch thực tế và tối ưu hóa tài nguyên phần cứng.

---

## Limitations
- Một số trường hợp câu hỏi quá dài hoặc câu hỏi đa ý phức tạp vẫn đòi hỏi phân rã trung gian.
- Chi phí tính toán có thể tăng nếu không có cơ chế phân luồng thông minh.

---

## Relevance to our topic (Sys_3_4)
- **Mức độ liên quan:** `METHOD` - Cơ sở thực tiễn cho việc triển khai Qwen2.5-7B lượng tử hóa trên phần máy chủ cơ quan xã/phường
- Đóng góp trực tiếp vào luận chứng khoa học và thiết kế kiến trúc của trợ lý AI pháp lý Sys_3_4.

---

## Possible improvement in Sys_3_4
- Sys_3_4 kết hợp phương pháp này vào kiến trúc kép **Dual-Engine (Strict + Friendly)**, bổ sung cơ chế cô lập trạng thái hỏi lại (*Clarify State Isolation*) và lớp kiểm chứng hậu kỳ tất định (*Post-hoc Verifier*) để đạt độ chính xác số liệu tuyệt đối (0% ảo giác).

# Paper 07 Summary: CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law

## Citation
- **Tên bài báo:** CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law
- **Tác giả:** Zhao et al.
- **Năm xuất bản:** 2026
- **Nguồn / Hội nghị:** *ACL 2026*
- **Phân loại tiêu chí:** `Liên quan trực tiếp (Legal QA / E-Gov)`

---

## Problem
Bài báo giải quyết vấn đề cốt lõi trong lĩnh vực Statutory & Case Law: Khi người dùng tương tác với hệ thống, các giải pháp truyền thống thường gặp khó khăn về độ chính xác, tính bảo mật dữ liệu, hiện tượng trôi ngữ nghĩa hoặc rào cản ngôn ngữ địa phương.

---

## Method
- **Phương pháp / Mô hình:** Hybrid Sparse-Dense Precedent Retrieval
- **Kiến trúc kỹ thuật:** Tích hợp mô-đun xử lý chuyên sâu, kết hợp các thành phần tiền xử lý, trích xuất đặc trưng có cấu trúc và kiểm soát đầu ra nghiêm ngặt.

---

## Dataset
- **Dữ liệu sử dụng:** 2.500 án lệ hành chính Canada
- **Đặc điểm:** Ngữ liệu thực tế, chuẩn hóa và phản ánh đúng bài toán nghiệp vụ chuyên ngành.

---

## Evaluation
- **Chỉ số đánh giá:** MRR@5 (+27.4%), Citation Recall (+31.2%)
- **Đối sánh:** So sánh với các mô hình baseline truyền thống và mô hình ngôn ngữ chưa được tinh chỉnh chuyên biệt.

---

## Results
- **Kết quả chính:** Khẳng định kết hợp từ khóa thưa (sparse) và vector dày (dense) vượt trội hơn dense đơn lẻ
- Cải thiện vượt bậc về độ chính xác trích xuất, giảm thiểu đáng kể lỗi sai lệch thực tế và tối ưu hóa tài nguyên phần cứng.

---

## Limitations
- Một số trường hợp câu hỏi quá dài hoặc câu hỏi đa ý phức tạp vẫn đòi hỏi phân rã trung gian.
- Chi phí tính toán có thể tăng nếu không có cơ chế phân luồng thông minh.

---

## Relevance to our topic (Sys_3_4)
- **Mức độ liên quan:** `DIRECT` - Cơ sở lý thuyết cho việc kết hợp SQLite FTS5 với Qdrant BGE-M3 trong Sys_3_4
- Đóng góp trực tiếp vào luận chứng khoa học và thiết kế kiến trúc của trợ lý AI pháp lý Sys_3_4.

---

## Possible improvement in Sys_3_4
- Sys_3_4 kết hợp phương pháp này vào kiến trúc kép **Dual-Engine (Strict + Friendly)**, bổ sung cơ chế cô lập trạng thái hỏi lại (*Clarify State Isolation*) và lớp kiểm chứng hậu kỳ tất định (*Post-hoc Verifier*) để đạt độ chính xác số liệu tuyệt đối (0% ảo giác).

# Literature Review: Constitutional AI: Harmlessness from AI Feedback

- **Tác giả:** Yuntao Bai, Saurav Kadavath, Sandipan Kundu, Amanda Askell, Dario Amodei et al. (Anthropic)
- **Năm xuất bản:** 2022
- **Tạp chí / Hội nghị:** *arXiv:2212.08073 / Anthropic Research*
- **Phân loại nghiên cứu:** AI Alignment & Policy-Driven Guardrails
- **Link định danh / DOI:** [https://arxiv.org/abs/2212.08073](https://arxiv.org/abs/2212.08073)
- **Mã arXiv:** arXiv:2212.08073
- **Thuộc nhóm chuyên đề:** Nhóm 8: Kiến trúc AI Đa miền & Tự động hóa Pipeline (Universal Domain & Auto-Evaluation)
- **Ánh xạ kiến trúc:** Ảnh 2 - Hộp: Domain Config & Policy Registry (STRICT MODE vs FRIENDLY MODE)
- **Đối chiếu nguồn:** Metadata và phân tích khoa học đã đối chiếu trực tiếp với bài báo gốc.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để một lõi AI duy nhất có thể thích nghi và tuân thủ các quy tắc ứng xử hoàn toàn khác nhau giữa các miền (nghiêm ngặt trong Pháp lý vs thân thiện trong CSKH/Du lịch)?

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Anthropic đề xuất kỹ thuật **Constitutional AI (AI theo hiến pháp)**:
- **Bộ nguyên tắc hiến pháp (Constitution / Policy Registry):** Định nghĩa tập hợp các quy tắc hành vi cho từng miền:
  - *Strict Policy (Pháp lý/Hành chính):* Bắt buộc có nguồn trích dẫn, tuyệt đối không suy đoán, từ chối an toàn khi ngoài thẩm quyền, giọng điệu trung lập trang trọng.
  - *Friendly Policy (Du lịch/CSKH):* Đóng vai người bạn đồng hành nhiệt tình, gợi ý linh hoạt, ưu tiên tốc độ và sự gần gũi.
- **Cơ chế Tự phê bình & Hiệu chỉnh (Critique and Revision):** 
  - Mô hình sinh câu trả lời nháp.
  - Output Guardrail sử dụng bộ nguyên tắc của domain để đánh giá: *Câu trả lời có vi phạm điều khoản nào của Constitution không?* Nếu vi phạm -> Tự động viết lại (Rewrite) trước khi xuất xưởng.

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

- Mô hình loại bỏ hành vi độc hại và ảo giác mà không cần can thiệp gán nhãn thủ công từ con người (RLAIF thay thế RLHF).
- Kiểm soát giọng điệu và phong cách phản hồi chặt chẽ theo từng hồ sơ nghiệp vụ.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Tách biệt rõ ràng giữa 'Tri thức' (Weights) và 'Quy tắc ứng xử' (Constitution).
- Dễ dàng cập nhật chính sách mà không cần huấn luyện lại mô hình.

### Hạn chế (Limitations):
- Tăng thêm một bước inference nếu áp dụng kiểm duyệt hai pha (Critique-Revision).

---

## 5. Direct Relevance & Takeaways for System 3 Project (Đóng góp & Ứng dụng cho Dự án)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Trực tiếp hỗ trợ tầng Domain Config & Policy Registry và khối Input/Output Guardrails + Persona (Tone) trong Ảnh 2.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Related Works:** Tổng quan về AI Alignment và Rule-based Constrained Generation.
2. **Methodology:** Cung cấp cơ sở lý luận vững chắc cho cơ chế phân hóa 2 chế độ STRICT MODE và FRIENDLY MODE.
3. **Evaluation:** Đánh giá tỷ lệ tuân thủ chính sách (Policy Compliance Rate).

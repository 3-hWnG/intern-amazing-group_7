# Ghi chú họp thống nhất nhãn Phần B — real_v4_s4

Nhãn A: Nguyễn Viết Hưng (độc lập, chỉ xem `cases_real_v4_s4_B.json`, không xem nhãn B trước khi làm).
Nhãn B: Phạm Lê Thiên Dấn.
Đo đồng thuận bằng `run_real_v4_s4.py agree`: Cohen's kappa tổng thể κ = 0.952, khớp refusal 98.9%, khớp ask_back 98.9%, khớp đáp án semantics 95.5%. 24/88 câu có khác biệt chi tiết (đa số chỉ là khác định dạng JSON, không mâu thuẫn nội dung).

## 2 câu bất đồng nội dung thật — đã họp (dj + Hưng) chốt theo Nhãn B:

1. **`v4_b-bao_vat-03`** — "Bảo vật nào đang được một bảo tàng lưu giữ?"
   - Nhãn B (dj): trả lời bằng số lượng — 195 bảo vật do bảo tàng lưu giữ (lọc cột Chủ sở hữu/Đơn vị lưu giữ có chữ "Bảo tàng").
   - Nhãn A (Hưng): refusal — cho là câu hỏi không chỉ rõ bảo tàng nào.
   - **Quyết định:** chốt theo Nhãn B. Lý do: câu hỏi hỏi "bảo vật nào... được MỘT bảo tàng lưu giữ" (ý hỏi có hay không / liệt kê, không hỏi đích danh bảo tàng cụ thể nào), nên trả lời số lượng/liệt kê là hợp lý, không cần hỏi lại.

2. **`v4_b-the_thao-09`** — "Sân Thống Nhất giờ thế nào rồi?"
   - Nhãn B (dj): ask_back — hỏi lại.
   - Nhãn A (Hưng): trả lời thẳng "Đang hoạt động" (chỉ có đúng 1 sân tên "Thống Nhất" trong bảng).
   - **Quyết định:** chốt theo Nhãn B (ask_back). Lý do: câu hỏi "giờ thế nào rồi" mơ hồ về việc muốn biết thuộc tính nào (trạng thái? sức chứa? năm khánh thành?), dù chỉ có 1 dòng khớp tên, hệ thống không nên tự chọn 1 thuộc tính để trả lời khi câu hỏi không chỉ rõ.

## 22 câu gộp biên (không mâu thuẫn, chỉ khác độ chặt/định dạng)

Hợp nhất (union) các giá trị `any`/`all`/`num` của cả 2 nhãn, giữ `refusal`/`ask_back` theo cả 2 đồng thuận. Chi tiết xem `real_v4_s4_labels_final.json`, trường `"notes"` mỗi câu có đánh dấu `[Họp: gộp biên rộng cả 2 nhãn A+B, không mâu thuẫn nội dung]`.

## File liên quan
- `real_v4_s4_labels_A.json`, `real_v4_s4_labels_B.json` — 2 nhãn độc lập gốc, giữ nguyên không sửa.
- `real_v4_s4_labels_final.json` — 88 câu đã thống nhất, dùng để build `cases_real_v4_s4_labeled.json` (216 câu).

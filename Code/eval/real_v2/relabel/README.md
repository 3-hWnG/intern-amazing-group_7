# real_v2: lượt gán nhãn thứ hai (B) để đo độ đồng thuận

Nhãn gốc của real_v2 do một người gán (A = Claude, cũng là bên sửa hệ thống; xem `../README.md` mục Nhãn). Lượt này cho một người thứ hai gán độc lập 100 câu để báo Cohen's kappa trong bài báo.

| Tệp | Là gì |
|---|---|
| `make_relabel.py` | Rút 100 câu ngẫu nhiên trong 313 câu của bộ chạy (SEED 20261025, chỉ đọc `id`), dựng tệp Excel. Không đọc nhãn A. |
| `relabel_ids.json` | 100 id đã rút (chude 70, random 30). sha256 `b844e45c1848ddfa4a99c3ffdd32fb089226c1a0b99fda3e8bd892123045f30c`. |
| `real_v2_relabel_B.xlsx` | Tệp để B điền: sheet Hướng dẫn, Nhãn (100 câu, ô vàng để điền), Thủ tục (1.517 thủ tục bản 3, có cột không dấu để lọc). Bản trống sha256 `fc82019d457710dea6cf3c3438ad9f7280bd1e057578879d65e4a56e99bf569f`. |
| `read_relabel.py` | Đọc tệp đã điền -> `real_v2_labels_B.json`, kiểm hợp lệ, in kappa (kèm 95% bootstrap), % khớp `proc_id`, câu bất đồng. |

Thứ tự (để chứng minh không ảnh hưởng chéo): rút mẫu và tệp trống được commit **trước** khi B gán; B không xem nhãn A, kết quả hệ thống hay báo cáo theo từng câu; nhãn A **không sửa** theo kết quả so sánh. Bất đồng chỉ ghi lại và báo cáo.

Giới hạn cần ghi trong bài: B là trưởng nhóm, đã đọc báo cáo tổng (biết tỷ lệ các lớp trên bộ test), chưa đọc nhãn từng câu.

## Cách gán lượt B (25/10/2026)

Trưởng nhóm cho model Gemini 4 Argon (Google, mức suy luận "High") gán nhãn trước, rồi kiểm lại từng nhãn bằng tay. Trong lúc gán, trưởng nhóm không xem nhãn A. Tệp đã điền: `real_v2_relabel_B_labeled.xlsx`, sha256 `bc0259525a8fbb57d882daf87dbbd410d499c931296d7ef844649eaa67098887`. Như vậy hai lượt nhãn đến từ hai model khác nhau (A: Claude; B: Gemini và người kiểm). Cả hai đều có AI tham gia, và bài báo phải ghi rõ điều này.

## Kết quả

Chi tiết trong `agreement.txt` và `robustness.txt`.

- **Đồng thuận.** 9 câu B gán `skip`: đều là kiến nghị hay phản ánh, không phải câu hỏi; A gán `apologize`. Trên 91 câu còn lại, hai lượt khớp 79/91 (86,8%), **Cohen's κ = 0,685** (95% bootstrap 0,548–0,820). Trên 13 câu cả hai gán `answer`, `proc_id` khớp hệt 12 câu, câu còn lại một bên là tập con của bên kia.
- **Bất đồng chính.** 7 câu A gán `answer` (thường chấp nhận hai mã thủ tục) mà B gán `clarify`. Đây là ranh giới trả lời / hỏi lại khi có hai thủ tục gần nhau.
- **Độ vững của kết luận.** Chấm lại các lượt chạy test có sẵn trên 91 câu, mỗi lần với một bộ nhãn:
  - Bản gốc → A: hành vi +26/−1 với nhãn A, +24/−1 với nhãn B; p < 10⁻⁵ cả hai.
  - A → A + B: +0/−0 với cả hai bộ nhãn.
  - Thứ tự B < C < A giữ nguyên.
  - Kết luận không đổi khi đổi người gán. Nhãn A không bị sửa.

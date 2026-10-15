# cases_real_log_v1.json — "Bộ log câu hỏi thật" (v1, 2026-10-13)

## QUAN TRỌNG — đây KHÔNG phải log sản xuất thật, đọc kỹ trước khi dùng trong báo cáo

Dự án **chưa có người dùng thật** (chưa triển khai production), nên **không thể có log dân
thật** theo đúng nghĩa (tin nhắn do người dân thật gõ vào hệ thống thật). `cases_pseudo_real*.json`
(3 file, 94 câu, đã có từ trước) và bộ này (`cases_real_log_v1.json`, 28 ca / 29 lượt) đều là
**mô phỏng gần nhất có thể làm trung thực**: câu hỏi được soạn **tự do, không dùng template của
`build_golden_multidomain.py`**, theo văn phong người dân thật hay gõ (viết tắt, không dấu, kể
hoàn cảnh, câu cụt, xưng hô kiểu chat), rồi **chạy thật** qua `answer_adapter` (không viết sẵn câu
trả lời) và ghi lại đúng hành vi hệ thống trả ra.

**Việc thật nên làm tiếp để có log THẬT 100%** (không AI nào làm thay được): triển khai bản demo
cho một nhóm nhỏ người dùng thật (bạn bè, người ở xã/phường, nhóm test nội bộ) dùng thử và thu log
chat thật — hoặc nếu nhóm có sẵn log như vậy ở đâu rồi (Zalo, Google Form khảo sát, bản demo cũ...)
thì đưa vào đây để chấm, sẽ chính xác hơn bộ này nhiều.

## Cách dựng (để tái lập / mở rộng)
1. Chọn 22 thủ tục thật trải nhiều domain hiếm gặp hơn golden set cũ (Hòa giải ở cơ sở, Tín ngưỡng
   tôn giáo, Nuôi con nuôi, Bảo trợ xã hội, Người có công, Giáo dục mầm non...) — ưu tiên các thủ
   tục **dễ nhầm với thủ tục anh em** (3 loại "mai táng phí" khác nhau, "hòa giải viên" vs "tổ
   trưởng tổ hòa giải", "thành lập" vs "cho phép hoạt động" mầm non) để test đúng cái hệ thống hay
   sai theo PHẦN 1 Tầng A của tài liệu chính.
2. Viết câu hỏi tự do, kể hoàn cảnh, không theo khuôn `"{tên} lệ phí bao nhiêu?"`.
3. Lấy `expect_ids`/fee/time **assert lại từ `data/snapshot/procedures.jsonl`** (script kiểm đã
   xác nhận: mọi `proc_id` trong bộ này có thật trong DB — không ca nào bịa ID).
4. Thêm 3 ca mơ hồ (archetype 6, `beh=clarify`) + 4 ca ngoài phạm vi thật (archetype 7,
   `beh=apologize`: đổi bằng lái, hộ chiếu, hải quan, thuế — đều là thủ tục cấp tỉnh/ngành dọc có
   thật, không phải bịa) + 1 ca đa lượt tỉnh lược chủ thể (archetype 5).
5. Chạy: `S3_DB=<db cục bộ> S3_DATA_DB=<db cục bộ> S3_USE_LLM=0 python run_server.py eval/run_pseudo_rank.py cases_real_log_v1.json real_log_v1`

## Kết quả đo (2026-10-13, chạy 1 lần — bộ "mù" theo nghĩa hệ thống chưa thấy câu này bao giờ)

| Chỉ số | Số đo |
|---|---|
| n | 29 lượt (28 ca, 1 ca đa lượt) |
| Behavioral Accuracy | **22/29 (75,9%)** |
| — answer đúng hành vi | 19/23 (82,6%) |
| — clarify đúng hành vi | **0/2 (0%)** |
| — apologize đúng hành vi | 3/4 (75,0%) |
| Top-1 (trên 23 lượt `answer`) | **16/23 (69,6%)** |
| Top-3 | 18/23 (78,3%) |
| MRR | **0,751** |
| nDCG@5 | 0,780 |

Số liệu đầy đủ (từng dòng): `eval/results/rank_real_log_v1.json`.

**So với HOLDOUT-4 (Top-1 77,9%, MRR 0,810, Behavioral 84,0%): bộ này THẤP HƠN đáng kể.** Dễ
hiểu vì bộ này cố ý chọn domain hiếm gặp + nhiều thủ tục anh em dễ nhầm — **không nên dùng số của
bộ này để nói hệ thống "tệ hơn"**, mà dùng để **tìm thêm lỗi** HOLDOUT-4 chưa phủ tới.

## 2 lỗi mới phát hiện qua bộ này (không có trong HOLDOUT-4, đáng ghi vào báo cáo)

1. **Nhầm giữa thủ tục "anh em" cùng họ tên** — `real-11` hỏi mai táng phí cho **dân công hỏa
   tuyến** (đúng = `1.010456`, 10 ngày) nhưng hệ thống trả về thủ tục **cựu chiến binh** (25 ngày,
   SAI). `real-13` hỏi **chấm dứt** chăm sóc thay thế (đúng = `1.004944`, 5 ngày) nhưng hệ trả về
   thủ tục **chuyển** trẻ sang nơi chăm sóc khác (25 ngày, SAI). Cả 2 ca: **số trả về là số THẬT
   của thủ tục sai đó** (không bịa số) — đây là lỗi **truy hồi** (chọn nhầm ứng viên), không phải
   lỗi **sinh bịa** (B5 vẫn sạch). Khớp đúng nhóm lỗi field `documents`/`conditions` đã thấy ở
   HOLDOUT-4 (PHẦN 2.1) — cho thấy cùng 1 nguyên nhân gốc (phân biệt thủ tục cùng họ) lặp lại ở
   domain khác.
2. **Nhầm Ý ĐỊNH (intent) field, không nhầm thủ tục** — `real-07` hỏi "tốn nhiêu tiền" cho thủ tục
   **ĐÚNG** (`2.001016`, top-1 chính xác) nhưng hệ thống xếp câu hỏi vào field `meta` (căn cứ pháp
   lý) thay vì `fee`, nên trả về số quyết định + văn bản pháp luật **thay vì số tiền 50.000đ** —
   người hỏi không nhận được câu trả lời cho câu họ hỏi, dù hệ thống "biết" đúng thủ tục. Lỗi này
   **không nằm ở tầng Retrieval (A)** mà ở **tầng trích field/intent trong Generation (B/C)** — có
   thể sửa bằng cách rà lại từ khóa "tốn/mất (bao nhiêu) tiền" trong bộ phân loại field.
3. **Ngữ cảnh đa lượt không giữ với câu hỏi tiếp theo kiểu chat đời thường**: `real-28` lượt 2
   ("vậy tốn bao nhiêu tiền hả bạn" — tỉnh lược, không nhắc lại "tách hộ") bị hệ thống trả
   `apologize` (không nhận ra vẫn đang hỏi tiếp thủ tục lượt 1) — C2 (Context Resolution) yếu với
   câu tỉnh lược có từ đệm ("hả bạn") chứ không chỉ với tỉnh lược trần trụi.

**Không ca nào bịa số** trong các ca `answer` đã xem tay (fee/time trả về luôn khớp đúng CSDL của
**thủ tục mà hệ thống chọn**, dù thủ tục đó đôi khi chọn sai) — nhất quán với B5 = 0% đã đo ở
`eval/golden/ragas_runner.py` (0/853 DEV, 0/266 HOLDOUT).

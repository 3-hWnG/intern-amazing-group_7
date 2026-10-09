# Phase 30: hỏi lại khi mơ hồ (họ A) và điều kiện chỉ lặp tên thủ tục (họ B)

Chế độ luật (`S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`), không GPU. Không mở, không chạy bộ mù/team (h3/h4/h5/pseudo_real/team, `run_pseudo.py`); chỉ dùng DEV/ctx/synth/p23/p26/composer và bộ MỚI `cases_p30.jsonl` do `build_p30.py` dựng từ DB.

## Nguyên nhân gốc
**Họ A (không hỏi lại)** có ba nguyên nhân độc lập:
1. `rank._near` loại các anh em có tên dài khỏi nhóm ứng viên bằng `h.prec >= 0.4 * top.prec` (độ phủ tên = chữ của câu / độ dài cả tên). Cụm gốc chung ("gia hạn", "xét tuyển", "tuyển chọn", "thanh toán") là phần ĐẦU của nhiều tên dài, nên mọi anh em dài đều bị phạt, nhóm chỉ còn 1-2 thủ tục (cần >= 3) và Policy trả lời luôn một thủ tục.
2. Bản riêng của tỉnh bị loại hẳn, kể cả khi chúng là bằng chứng "thủ tục này có nhiều dạng" ("hỗ trợ chi phí mai táng": 2 dạng không gắn tỉnh + 3 dạng của Lai Châu/Đà Nẵng khác đối tượng).
3. **Chung với họ B**: `policy._match_conditions` đặt `cond_hit` khi bất kỳ chữ nào của câu ("em", "muốn", "là", "hỏi"...) trùng chữ đặc trưng của một mục `condition_index`; `cond_hit` bị hiểu là "người dùng đã nêu từ phân biệt" nên chặn hẳn việc hỏi lại ("em muốn bảo hiểm y tế" trả lời luôn, dù 12 ứng viên gần nhau).
Thêm hai nguyên nhân nhỏ: tên lõi trùng nguyên câu hỏi vẫn bị coi mơ hồ khi tên khác chứa trọn tên đó ("khám bệnh, chữa bệnh BHYT"); cụm hỏi mục "cần giấy tờ gì" để sót chữ "cần" làm tụt độ phủ, câu rơi vào "ngoài phạm vi" (xin lỗi) thay vì hỏi lại.

**Họ B (điều kiện lặp tên)**: cùng lỗi so chữ ở mục 3: ví dụ "Lệ phí đăng ký thường trú là bao nhiêu?" khớp mục "... có công trình phụ trợ là nhà ở" chỉ nhờ chữ "là"; "nếu ở nhà thuê" khớp "nhà ở công vụ" nhờ "nhà/ở". Mảnh điều kiện do Planner rút ("nếu đăng ký tạm trú thì...") chỉ lặp tên thủ tục nhưng vẫn được ghi chú như điều kiện.

## Thay đổi
- `retrieval/rank.py`: `_contiguous` (anh em có tên dài vẫn vào nhóm khi câu là CỤM ĐẦU tên lõi của nó, không áp cho bản tỉnh khi top là bản tỉnh); bản riêng tỉnh đếm vào số nhóm (>= 3) nhưng chỉ hiện các dạng không gắn tỉnh (cần >= 2); gõ đúng nguyên tên lõi của top thì không hỏi.
- `server/policy/policy.py`: `_user_words`/`_user_seq` (bỏ chữ hư STOP và cụm hỏi mục trước khi so mục điều kiện; cụm 2 chữ nội dung liền nhau như "ủy quyền" đủ bằng chứng), `adds_info` (mảnh điều kiện phải có chữ ngoài tên thủ tục), ngưỡng hỏi lại từ 3 xuống 2 lựa chọn hiển thị (nhóm vẫn phải >= 3).
- `retrieval/query.py`: thêm cụm hỏi mục "cần giấy tờ gì / cần hồ sơ gì"; lời đệm "tìm hiểu / tư vấn / cần biết / muốn biết / hướng dẫn" vào `_DROP_PHRASES` (không tên thủ tục nào chứa các cụm này).
- Mới: `eval/build_p30.py`, `run_p30.py`, `p30_composer_trigger.py`, `cases_p30.jsonl`, `server/tests/p30_clarify_test.py` (có trong `run_all.py`, nên bảng gate nay có 38 dòng thay vì 37).

## Số đo
Bộ `cases_p30.jsonl` (228 ca): clarify = cụm gốc có >= 3 nhóm tên (DB kiểm) + chủ đề nhiều nhóm đối tượng; answer = tên đầy đủ, tên đầy đủ của anh em trong nhóm cụm gốc ("sibling", rủi ro hỏi thừa cao nhất), cụm định danh duy nhất. Mẫu bọc câu xoay vòng ("em muốn X", "X nộp ở đâu"...). `tune`: dùng khi chỉnh. `held`: tôi đã xem tổng và danh sách lỗi của cả hai nửa ở vài lần chạy giữa chừng trước khi nhận ra, nên **held không còn mù hoàn toàn** (không vá riêng ca nào của held, nhưng các thay đổi chung có thể đã được dẫn dắt gián tiếp). `fresh`: viết sau khi chỉnh xong, chạy lần đầu một lần.

| | trước | sau | ghi chú |
|---|---|---|---|
| tune: clarify recall | 33/44 (75%) | 41/44 (93%) | |
| tune: hỏi thừa (answer mà hỏi) | 0/45 | 0/45 | answer top-1 45/45 cả hai |
| held: clarify recall | 31/44 (70%) | 41/44 (93%) | held không còn mù hoàn toàn (xem trên) |
| held: hỏi thừa | 1/44 | 0/44 | ca "khám bệnh chữa bệnh BHYT" (gõ nguyên tên) |
| fresh: clarify recall, lần chạy đầu | 14/27 (52%) | 17/27 (63%) | số mù đúng nghĩa duy nhất |
| fresh: sau thêm bước bỏ lời đệm | 14/27 | 20/27 (74%) | đã nhìn lỗi fresh rồi mới thêm, nên số này đã bị ô nhiễm |
| fresh: hỏi thừa | 0/24 | 0/24 | |

Gate (bản chạy đầy đủ `run_all.py`, có build, lần cuối sau mọi sửa): **38/38 ĐẠT** (37 dòng cũ + `p30_clarify_test`). DEV cũ top-1 97,0% (không đổi), hành vi 97,6% -> 98,1% (ca `clarify_conditional-10` đúng), bịa số 0%, ngoài phạm vi 30/30, ctx 89/91 và 26/26, p26 92/92, synth TEST 96,4%, perturb 99,44% -> 99,53%, focus 98,9%.

Họ B (`eval/p30_composer_trigger.py`, 813 ca không mù gồm DEV, ctx, p26, composer): số lượt gọi bước LLM sinh chữ vì task có `conditions` **53 -> 28**. Trong 25 lượt mất đi, 19 là khớp bằng chữ hư (mục anh em sai); 6 bị bộ phân loại xấp xỉ của script coi là "do người dùng nêu" nhưng xem tay đều khớp qua chữ chung ("cơ quan", "sinh", "nhận nuôi"); không lượt nào là điều kiện thật bị mất (kiểm lại các điều kiện "nhà thuê", "ủy quyền", "bộ đội", "ly hôn" trong test). Một điều kiện thật ("nhờ người khác đi đăng ký hộ kinh doanh... giấy tờ ủy quyền") lúc đầu bị mất khi bỏ chữ hư vì cả 4 mục anh em cùng có "ủy quyền" (điểm 1/4 + 1/4), nên thêm luật cụm hai chữ liền nhau.

## Cái KHÔNG cải thiện / còn yếu
- Câu ngắn gồm chữ chung, kèm lời đệm lạ, vẫn có thể bị xin lỗi (không tìm thấy) thay vì hỏi lại: "giải quyết", "trình báo", "học bổng", "Tôi muốn làm giấy tờ cho con" (ca DEV `clarify_conditional-13` vẫn trượt). Gốc: cổng chữ-đặc-trưng (`out_of_scope` khi không chữ hiếm nào khớp) chạy trước phần hỏi lại. Không đổi vì ranh giới với "ngoài phạm vi" thật (30/30) rất mong manh.
- Chủ đề nằm giữa/cuối tên dài ("dân quân tự vệ", "thương binh", "đăng ký xe", "quân nhân") vẫn trả một thủ tục: các tên chứa chủ đề có độ phủ tên rất thấp và thường chỉ còn 2 nhóm.
- Ca DEV `clarify_conditional-12` ("giám hộ": 3 dạng, câu là phần CUỐI của tên) vẫn trả lời; ngoài họ A của đợt này.
- Tên đầy đủ có nhiều dạng ("đăng ký khai sinh" 8 dạng) vẫn trả bản mặc định + nút "dạng khác" theo thiết kế; nếu bộ mù kỳ vọng hỏi lại ở đây thì số mù sẽ vẫn thấp. Tôi không biết điều đó (không xem bộ mù).
- Bộ p30 dễ hơn câu thật (cụm gốc rõ, chủ đề có >= 3 tên chứa chữ); mức 45% trên bộ mù KHÔNG được đo lại, nên không thể nói bộ mù tăng bao nhiêu. Số tuyệt đối trên p30 không so được với 8/16 hay 0/3.
- Hỏi thừa 0 trên p30 chỉ nói rằng ba loại answer tự dựng (tên đầy đủ, anh em cùng cụm, cụm định danh duy nhất) không bị hỏi; câu thật mơ hồ vừa phải có thể khác.

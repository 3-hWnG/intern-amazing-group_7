# Phase 31: hỏi lại khi tên chung của họ thủ tục có nhiều dạng THẬT

Chế độ luật (`S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`), không GPU. Không mở/chạy bộ mù và bộ team (h3-h6, pseudo_real, team, `run_pseudo.py`), không đụng `repo/`. Chỉ dùng DEV/ctx/synth/p23/p26/p30/composer và bộ MỚI `cases_p31.jsonl` (+ `cases_p31_fresh.jsonl`) do `build_p31.py` dựng từ DB.
"Trước" = bản sao nguyên trạng của cây `system3` ngay trước phase này (chạy `run_all --skip-build` và `run_p31` trên bản sao đó).

## Quyết định sản phẩm đang thực thi (người dùng chọn 2026-10-08)
Câu chỉ nêu tên chung của một họ thủ tục có nhiều dạng khác nhau thật thì hỏi lại (thẻ liệt kê các dạng) thay vì trả bản mặc định + nút "dạng khác".

## Nguyên nhân gốc và thiết kế
Policy cố ý trả `default_variant` rồi gắn `variants.others` (nút "dạng khác"), vì `rank._near` chỉ báo nhóm khi >= 3 NHÓM tên khác nhau còn các dạng trong cùng family (`families.head`) bị gộp làm một nhóm. Họ "đăng ký khai sinh" có 8 dạng (thường, lưu động, có yếu tố nước ngoài, kết hợp nhận cha mẹ con, đã có hồ sơ cá nhân, ...) nên không bao giờ thành thẻ hỏi lại.

Thiết kế (tất cả ở `server/policy/policy.py`, không đụng truy hồi), tổng quát từ DB, không có danh sách theo tên:
1. **Dạng thật** (`real_variants`): các thành viên family KHÔNG gắn tỉnh, cấp xã, không ngành dọc, tên lõi khác nhau (bỏ "Thủ tục", dấu câu, hoa/thường) và nội dung `components` khác nhau. Bản chỉ khác tỉnh, hai bản tên chỉ khác dấu chấm cuối, bản trùng hồ sơ không tính. Cần >= 3 dạng (`_MIN_REAL_VARIANTS`) mới hỏi; 2 dạng ("đăng ký giám hộ" và "... có yếu tố nước ngoài", "đăng ký lại ...") giữ bản mặc định + nút. Trong kho chỉ 5 họ đạt: khai sinh (8), kết hôn (4), khai tử (4), nhận cha mẹ con (3), Bằng "Tổ quốc ghi công" (4).
2. **Chỉ nêu tên chung** (`_names_family_only`): (a) `procedure_query` của bộ hiểu câu còn đủ chữ đặc trưng của tên chung; (b) câu gốc, sau khi bỏ cụm hỏi mục, lời đệm của truy hồi (`_DROP_PHRASES`), viết tắt ("dk" -> "đăng ký"), tên tỉnh và chữ hư (STOP), KHÔNG còn chữ nào ngoài tên chung: từ phân biệt ("lưu động", "nước ngoài", "quá hạn"), hoàn cảnh ("nếu người mất không có giấy báo tử"), phủ định ("không phải khai sinh") đều chặn việc hỏi; (c) chữ đối tượng (con, cháu, ông, bà, bố, mẹ...) kiểm riêng, đếm số lần so với tên thủ tục ("nhận cha, mẹ, con cho CON tôi"); (d) fact đã kể cũng tính.
3. Không hỏi khi: câu nối `refers_to == last` (hội thoại đã chốt dạng), `cond_hit`, đã trả lời thẻ (`no_clarify`), hồ sơ Phase 26 chốt được đúng 1 dạng (`filter_by_subject`, nay có tham số `check_named=False` cho đường này vì tên chung trùng tên bản mặc định; 2..n-1 dạng hợp thì thẻ nhỏ lại).
4. Thẻ: tối đa 6 dạng (bản mặc định đứng đầu) + ô gõ tự do; câu hỏi "Thủ tục này có nhiều dạng khác nhau tuỳ trường hợp. Bạn muốn hỏi dạng nào?".
5. **Nút "dạng khác"**: trước đây gửi lại nhãn như câu hỏi mới. Nút về bản mặc định có nhãn = tên chung nên sẽ bị hỏi lại (vòng lặp). Nay nút gửi kèm `proc_id` (`ChatIn.proc_id` -> `Turn.pick_proc` -> `forced_pid`, đi chung đường "đã chọn, không hỏi lần hai"). Gõ tay đúng nhãn đó vẫn là câu hỏi mới -> hỏi lại.
6. Công tắc `S3_FAMILY_CLARIFY=0` quay về hành vi cũ (cho người điều phối quyết định).

## Thay đổi
`server/policy/policy.py` (hàm mới `real_variants`, `_names_family_only`, `_user_words_keep`, `_kin`; khối hỏi lại; `filter_by_subject(check_named)`), `server/orchestrator.py` (`Turn.pick_proc`), `server/main.py` (`ChatIn.proc_id`), `web/static/js/chat.js` + `web/templates/index.html` (nút gửi `proc_id`, `?v=20261008a`). Mới: `eval/build_p31.py`, `eval/run_p31.py`, `eval/cases_p31.jsonl`, `eval/cases_p31_fresh.jsonl`, `server/tests/p31_variants_test.py` (có trong `run_all.py`). Tài liệu: ARCHITECTURE, KNOWN_ISSUES, EVAL, eval/README, SETUP, CONTRIBUTING, README, PLAN_SYSTEM3_DOT6.
Sửa test cũ vì chúng dùng câu "khai sinh/khai tử/kết hôn cần giấy tờ gì" làm câu mẫu cho việc KHÁC (không phải đo chính sách biến thể): `smoke_test.py` và `p20_api_test.py` đổi sang "Đăng ký tạm trú ..."; `planner_hybrid_test.py` đặt `S3_FAMILY_CLARIFY=0` (đo việc hợp nhất đề xuất LLM); `p26_memory_test.py` đổi "Đăng ký khai sinh ..." thành "Đăng ký khai sinh lưu động ..." (ý của đoạn test là câu nêu rõ thủ tục thì hồ sơ không can thiệp); `p30_clarify_test.py` đổi cặp ("đăng ký khai sinh" -> trả lời) thành "đăng ký khai sinh lưu động". Đây là kỳ vọng của TEST, không phải của bộ eval.

## Số đo (trước -> sau)
`cases_p31.jsonl` (230 ca): clarify = tên đầy đủ/lõi của 5 họ (50 + 40 ca bọc mẫu câu, kể cả có mục hỏi), hồ sơ không phân biệt/thu hẹp (7); answer = từng dạng gọi đúng tên (36), tên chung + đối tượng/từ phân biệt (13), thủ tục một dạng (50), họ 2 dạng (12), hội thoại đã chốt dạng (15), hồ sơ chốt đúng 1 dạng (7). Đáp án theo dữ liệu (số dạng hợp theo `procedure_subjects`), không theo đầu ra hệ thống.

| | trước | sau |
|---|---|---|
| tune: clarify recall | 0/49 | 49/49 |
| tune: hỏi thừa | 0/68 | 0/68 |
| tune: answer top-1 | 65/68 | 68/68 (3 ca hồ sơ chốt dạng giờ trả đúng) |
| held: clarify recall | 0/48 | 48/48 |
| held: hỏi thừa | 1/65 | 1/65 (cùng một ca "thủ tục một dạng", có từ trước, không do phase này) |
| held: answer top-1 | 62/65 | 65/65 |
| **fresh** (viết SAU khi chỉnh; 238 ca: 93 clarify + 145 answer), clarify recall | 1/93 | **52/93 ở lần chạy đầu** (cách kiểm "chỉ nêu tên chung" bản 1) |
| fresh, sau sửa | | 92/93 (đã nhìn nhóm lỗi của lần đầu rồi mới đổi cách kiểm sang `procedure_query` + chữ gốc; số này KHÔNG còn mù) |
| fresh: hỏi thừa | 1/145 | 1/145 (ca có từ trước) |
| fresh: answer top-1 | 139/145 | 145/145 |

Ghi chú trung thực: p31 chỉ có 5 họ nên rất dễ; tune/held gần như tuyệt đối ngay lần chạy đầu và không phân biệt được các cách chỉnh. Con số đáng tin nhất là lần chạy đầu của lô fresh (52/93): hỏi lại thiếu khi câu có lời đệm lạ ("thì làm sao nhỉ", "nhờ tư vấn", "hết bao nhiêu tiền") vì bản 1 coi mọi chữ lạ là "đã nêu từ phân biệt". Bản cuối dùng lời đệm/cụm hỏi mục/viết tắt của chính truy hồi để lọc nên đỡ, nhưng đã bị nhìn. Held: tôi chỉ xem số tổng và số theo nhóm, không in danh sách lỗi; một lần chạy giữa chừng cho thấy 2 ca hỏi thừa nhóm "đối tượng" ở held -> sửa thành đếm số lần chữ đối tượng (cải tiến chung, kiểm lại bằng ví dụ tự viết ngoài bộ), nên held cũng không còn mù hoàn toàn.

## Cổng hồi quy (`run_all.py` đầy đủ, `--skip-build`)
Trước (bản sao cây cũ): 35/36 (chỉ `check_docs` trượt vì tôi đã chép file p31 vào bản sao; cây gốc ở Phase 30 là 38/38 kể cả bước dựng DB). Sau: **34/37** (3 dòng trượt, xem dưới; `check_docs` sạch sau khi cập nhật số):

| Cổng | Ngưỡng | Trước | Sau |
|---|---|---|---|
| DEV cũ top-1 | >= 95% | 97,0% (159/164) | 97,0% (159/164) |
| **DEV cũ đúng hành vi** | >= 96% | 98,1% (205/209) | **90,0% (188/209) TRƯỢT** |
| DEV cũ bịa số | <= 3% | 0,0% | 0,0% |
| ngoài phạm vi | 30/30 | 30/30 | 30/30 |
| ctx / ctx-p23 | >= 89/91 / 26/26 | 89/91, 26/26 | 89/91, 26/26 |
| **p26** | tất cả đạt | 92/92 | **88/92 TRƯỢT** |
| DEV focus / task thừa | >= 95% / <= 2% | 98,9% / 0 | 98,7% (312/316) / 0 |
| synth TEST / glued | >= 94% / >= 90% | 96,4% / 96,1% | 96,4% / 96,1% |
| perturb | >= 98% | 99,53% | 99,43% (6.629/6.667) |
| baseline V10.6 | <= 2 điểm | 0,59 | 0,59 |
| `check_docs` | sạch | sạch | sạch (README/EVAL cập nhật theo số thật) |

Không nới ngưỡng nào, không sửa kỳ vọng của bộ eval nào. Hai cổng trượt đều do chính sách mới trái kỳ vọng cũ, xem tiếp.

## KỲ VỌNG XUNG ĐỘT với chính sách mới (cần người điều phối quyết)
Mọi thay đổi hành vi trên DEV đều là `answer -> clarify` ở đúng 4 họ khai sinh/khai tử/kết hôn/nhận cha mẹ con; top-1 không đổi ca nào. Tôi giữ nguyên kỳ vọng "answer" (không sửa im lặng) và không coi chúng là sai rõ ràng: đó là hệ quả trực tiếp của quyết định sản phẩm.
- **DEV cũ (17 ca, tạo nên 98,1% -> 90,0%)**: rag_basic-01, -04, -12; quantitative-05, -08; multi_field-02, -05, -13; context_memory-05; evidence_citation-04, -06; hallucination_unsupported-13; typo-01, -02, -07, -17, -18. Cùng kiểu: "Đăng ký khai tử cần giấy tờ gì?", "Đăng ký khai sinh lệ phí bao nhiêu?", "dk ket hon can giay to gi"... (tên chung + mục hỏi, không từ phân biệt).
- Ngoài DEV cũ nhưng trong DEV gộp 523: thêm 24 ca p16/p18/p19/p23 cùng kiểu (hold-evidence_citation-01/-02 cũng vậy), tổng 41 ca đổi từ đúng sang sai hành vi. DEV gộp hành vi 98,1% -> 90,6%. Perturb: tập "ca đã đúng" co lại (649 -> 606), tỉ lệ vẫn 99,43%.
- **Hỏi thừa DEV (trả lời mong đợi mà lại hỏi)**: 4/523 -> 43/523 (+7,5 điểm), vượt ngưỡng "+1 điểm". Toàn bộ 39 ca tăng thêm là 41 ca xung đột nói trên; ngoài chúng không có ca nào mới bị hỏi thừa. Nghĩa là gate "hỏi thừa không tăng quá 1 điểm" không thể đạt cùng lúc với quyết định sản phẩm nếu kỳ vọng DEV giữ nguyên.
- **p26 nhóm c (4 ca)**: p26-c-01 "Đăng ký khai sinh cần giấy tờ gì?" (hồ sơ business), -02 "Làm thủ tục đăng ký kết hôn cần gì" (HTX), -03 "đăng ký khai tử mất bao lâu", -12 "đăng ký nhận cha mẹ con". Kỳ vọng "answer, hồ sơ không can thiệp"; hệ thống nay hỏi lại và hồ sơ vẫn không can thiệp (kết quả có hồ sơ == không hồ sơ), tức ý của nhóm c vẫn đúng, chỉ hành vi gốc đổi thành clarify.
Đề xuất (chưa làm): đổi kỳ vọng các ca trên thành `clarify` (hoặc bỏ khỏi cổng) nếu chấp nhận chính sách; hoặc `S3_FAMILY_CLARIFY=0` để quay về hành vi cũ (`p31_variants_test` kiểm công tắc này; chưa chạy lại toàn bộ gate với công tắc tắt, nhưng bản sao nguyên trạng cho 35/36 như bảng trên).

## Cái nào xấu đi (không giấu)
1. DEV hành vi và p26 như trên; số DEV-gộp trong README đã đổi theo số thật (90,6%).
2. Người dùng hỏi rất cụ thể mục ("Đăng ký khai sinh lệ phí bao nhiêu?") nay bị hỏi dạng nào trước khi biết phí: đúng theo quyết định (phí các dạng khác nhau: 5 giá trị khác nhau trên 8 dạng khai sinh), nhưng thêm một lượt.
3. Chỉ 5 họ trong kho đạt ngưỡng >= 3 dạng thật; hiệu quả trên bộ mù chỉ đến từ các họ này. Họ 2 dạng ("giám hộ", "đăng ký lại khai sinh/kết hôn/khai tử", "chấm dứt giám hộ") vẫn trả bản mặc định + nút.
4. Nhãn nút là tên nguyên văn: bản thường của khai sinh hiện là "Thủ tục đăng ký khai sinh" (khó phân biệt với tiêu đề thẻ); 8 dạng nhưng thẻ chỉ hiện 6.

## Còn yếu
- Hỏi lại phụ thuộc vào việc truy hồi chọn ĐÚNG họ trước: "nhờ tư vấn khai tử" truy hồi sang thủ tục khác hoàn toàn (không do phase này).
- Chữ đối tượng chỉ nhận danh sách kín (`_KIN`, có dấu; câu không dấu chỉ nhận vài chữ ít nhập nhằng): "khai tu cho me e" không dấu, "cho dì", "cho người thân" cần xem lại. Chữ vô nghĩa với thủ tục nhưng được truy hồi giữ lại (tên riêng, "quá hạn") được coi là đã nêu từ phân biệt (không hỏi) - nghiêng về hướng ít hỏi thừa, hỏi thiếu.
- Chữ dính liền ("dangkykhaisinh") không hỏi lại (raw còn nguyên một chữ lạ).
- Tên tỉnh được bỏ qua (không chọn dạng); nơi nộp/địa điểm khác tỉnh (khu vực biên giới) có trong tên dạng nên đã tính là từ phân biệt.
- Chưa đo trên bộ mù (HOLDOUT-6 do agent khác soạn, người điều phối chạy). Với bộ mù, nên đo cả hỏi thừa vì ngưỡng 3 dạng và danh sách `_KIN` là phỏng đoán.

## Quyết định 2026-10-08
Đo bộ mù bật so với tắt: không có lợi (HOLDOUT-6 hỏi lại 13 vs 12/28; HOLDOUT-5 và HOLDOUT-4 hành vi giảm 3 và 2 ca; bộ team 7 vs 8/10). Người dùng chọn tắt mặc định: `S3_FAMILY_CLARIFY` mặc định `0`; `p31_variants_test` tự đặt `=1`. Mã và bộ p31 giữ lại.

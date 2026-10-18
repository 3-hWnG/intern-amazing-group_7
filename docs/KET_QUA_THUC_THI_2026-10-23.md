# Kết quả thực thi kế hoạch G0–G4 (nhánh `exec/2026-10-19-audit-fixes`)

Kế hoạch: [KE_HOACH_THUC_THI_2026-10-19.md](KE_HOACH_THUC_THI_2026-10-19.md) (quyết định D1–D18 ở §1). Làm xong ngày 18/10/2026, chưa push.
Mọi việc chạy cùng một bộ test (`python run_server.py eval/run_tests.py`, DB cố định, không mạng, không Ollama): **đạt hết, không còn hồi quy đã biết**.
Mẫu so khớp 150 ca (`eval/equality.py`) chỉ đổi ở các việc cố ý đổi câu trả lời (G1.1, G2.2; đã ghi lại mốc). `eval/check_docs.py` sạch.

## 1. Từng việc

| Việc | Làm gì | Commit | Test / số đo | Kết quả |
|---|---|---|---|---|
| G0.1 | DB cố định cho test + `eval/run_tests.py` | ef66295 | mọi test | đạt |
| G0.2 | Mẫu so khớp 150 ca | 8f446ce | `eval/equality.py` | đạt |
| G0.3 | Dấu phiên bản trong kết quả eval | 670221c | `eval/stamp.py` | đạt |
| G0.4 | `run_all.py` không ghi đè DB đang chạy | d52f129 | sha256 3 DB không đổi | đạt |
| G0.5 | `check_docs` sạch (17 → 0 lỗi) | d52fc49 | `check_docs` | đạt |
| G1.1 | Lệ phí đúng đơn vị tiền; sửa đọc nhầm hàng nghìn khi dựng DB | 3ec5dd8 | `fee_display_test`; 4/150 câu đổi đúng ý (10 đồng → 10 USD) | đạt |
| G1.2 | Hồ sơ Strict theo tài khoản đăng nhập (lỗi lẫn dữ liệu F2) | 2b01292 | `memory_accounts_test` | đạt |
| G1.3 | Lớp chính sách chung: chống chèn lệnh cho Friendly (11/11 câu tấn công bị chặn, trước 4/11), che CCCD/SĐT ở mọi chỗ ghi và trước khi tìm web | c606682 | `pii_storage_test` | đạt |
| G1.4, G1.7 | Ô Tài khoản: đổi mật khẩu, xoá hội thoại / bộ nhớ / tài khoản; hạn mức tính cả hội thoại | 533a017 | `account_test` | đạt |
| G1.5 | Giới hạn đăng nhập sai (5 lần / 10 phút → 429) | cf34a34 | `login_limit_test` | đạt |
| G1.6 | Thay dữ liệu trẻ em thật trong test và tài liệu bằng danh sách giả | 9bc80e0 | `test_nv3` | đạt; **dữ liệu thật trong runtime và lịch sử git chưa đụng (chờ trưởng nhóm)** |
| G2.1 | Mỗi phiên bản thủ tục một DB bất biến + một con trỏ; đổi / quay lui tức thì | f1afb60 | `test_nv4` | đạt |
| G2.2 | Chuẩn hoá link Cổng (UUID), báo cáo bất biến khi dựng, bảng `proc_flat` | 7f355c0 | 121/150 câu chỉ đổi link | đạt |
| G2.3 | Ghép mã thủ tục cũ → mới (`proc_lineage`) | 8581d19 | `lineage_test`; 28 mã chờ người duyệt ([LINEAGE_CAN_DUYET.md](LINEAGE_CAN_DUYET.md)) | đạt |
| G2.4 | Cổng kiểm khi áp dụng phiên bản; áp dụng **bản 3** | dc682cf, e291ad2 | `gate_test`; cổng bản 2 → 3: 137 ca chung, hành vi 94,9% = 94,9% | đạt |
| G3.1 | Bộ lập lịch GPU chung, phần luật chạy song song | 5ab021c | `gpu_sched_test`: lượt chỉ-luật p95 143 ms khi 3 lượt tìm web + LLM chậm đang chạy | đạt |
| G3.2 | Bỏ hẳn "Suy nghĩ kỹ" (D9) | 2846661 | `test_nv1`, `test_nv2` | đạt |
| G3.3 | Máy không GPU: cảnh báo, công tắc "Chỉ trả lời bằng luật", ngắt mạch Ollama | 622d26c | `cpu_mode_test`: lượt cần LLM trả bản code < 0,5 s | đạt |
| G3.4 | Đo độ trễ tách 4 phần, test tải 10 người, test hợp đồng Ollama; điền bảng SLO | 3c95337 | Strict có LLM p95 15,4 → 4,3 s; xem §3 | đạt, **2 mục SLO chưa đạt** (§3) |
| D18 | Dùng lại câu trả lời đã 👍 khi người khác hỏi y chang | e14a793 | `answer_cache_test` | đạt |
| G4.1 | Hỏi lại khi mơ hồ | cf715ae | `eval/clarify_signals.py` | **không đưa luật nào vào** (§4) |
| G4.2 | Liệt kê / đếm bằng text-to-SQL có hộp cát | 8d9465c, 25e8b3d | `listsql_test` (14 kiểu SQL xấu bị chặn); bộ đo riêng test **42/45 (93%)**; bộ khuôn "list" đúng lĩnh vực **98%** (trước 15%) | đạt (mục tiêu 85% / 80%) |
| G4.3 | Hồ sơ lĩnh vực v1 | b21db25 | `profile_test`; test ABI đạt không gọi mạng | đạt |
| G4.4 | Hỏi tỉnh khi thủ tục có bản riêng tỉnh (D5); danh sách tỉnh lấy từ dữ liệu | 0a6a1e3 | `province_test`; mẫu 20 câu bản 3: **20/20** (câu dùng đúng tên thủ tục) | đạt |
| G4.5 | Tên hội thoại Strict = tên thủ tục trả lời đầu tiên (D6) | 98d8222 | `title_test` | đạt |
| G4.6 | Tóm tắt giữ tên chủ đề | b73b281 | `summary_topic_test` | đạt |
| G4.7 | Biểu mẫu: tên mẫu + link trang thủ tục trên Cổng (D7) | 2c02476 | `forms_test` | đạt; sửa luôn lỗi "Cổng không có biểu mẫu" sai cho mọi thủ tục (§4) |
| G4.8 | Sửa hồi quy `p23_input_test` | 905e4ff | test đạt; mẫu so khớp 0 khác | đạt |
| G4.9 | Tài liệu khớp code; danh sách câu cần sửa trên slide / bài báo | fedb8d3 | `check_docs` sạch | đạt — [SUA_SLIDE_VA_BAI_BAO.md](SUA_SLIDE_VA_BAI_BAO.md) |
| G4.10 | Từ đồng nghĩa sửa được ở trang Quản trị | — | — | **chưa làm** (tuỳ chọn; §4) |

## 2. Ba lần eval đầy đủ (LLM tắt, Planner luật, DB bản 3 `3-1a9c2d36a7.db`, 1.517 thủ tục, data_sha256 `70c42af1…36bd`)

Bộ mù (518 ca; 136 ca của mọi bộ bị loại vì mã đáp án không còn trong bản 3 và không ghép được).

| Lần | Sau | git | Hành vi đúng | top-1 | top-3 | MRR | Hỏi lại đúng | Từ chối đúng |
|---|---|---|---|---|---|---|---|---|
| #1 | G2 (mốc bản 3) | e291ad2 | 407/518 (79%) | 274/381 (72%) | 302/381 (79%) | 0,752 | 36/76 (47%) | 52/58 (90%) |
| #2 | G4.1–G4.8 | 905e4ff | 400/518 (77%) | 274/381 (72%) | 302/381 (79%) | 0,752 | 38/76 (50%) | 52/58 (90%) |
| #3 | số cuối | fedb8d3 | giống hệt #2 (sau #2 chỉ đổi tài liệu) | | | | | |

Cả 18 ca đổi giữa #1 và #2 đều do thẻ **hỏi tỉnh** (D5); tắt riêng `S3_PROVINCE_CLARIFY=0` thì cả 18 ca trở lại như #1. Trên bộ mù: 9 ca nhãn "trả lời" giờ hỏi tỉnh, 2 ca nhãn "hỏi lại" giờ đúng. Nhãn golden viết trước D5.
Bảng đủ (dev, holdout-used, theo nguồn): [PLAN_TUAN_TOI.md](PLAN_TUAN_TOI.md), `eval/saved_results/2026-10-18_eval{1,2,3}/`.

## 3. Hiệu năng (RTX 4050 6 GB, model thật, 10 người giả — bảng SLO ở [ARCHITECTURE_REVIEW §5.4](ARCHITECTURE_REVIEW_2026-10-15.md))

| Đường đi | Mục tiêu | Đo (nhịp thực tế, nghỉ 20–40 s) | |
|---|---|---|---|
| Strict chỉ luật | p95 ≤ 0,5 s | p95 1,18 s | ✘ (CPU dùng chung với Ollama + reranker) |
| Strict có bước LLM | p95 ≤ 8 s | p95 4,0 s | ✔ |
| Friendly chờ hàng | p95 ≤ 10 s | p95 13,6 s | ✘ — trưởng nhóm chấp nhận ~15 s cho thí điểm (D17) |

## 4. Tiêu chí của bản audit đã đổi trạng thái (19 tiêu chí; trước: 7 ✅, 8 🟡, 4 ❌)

| # | Tiêu chí | Trước | Sau | Vì sao |
|---|---|---|---|---|
| 2 | Cấu hình riêng từng lĩnh vực | 🟡 | ✅ | hồ sơ lĩnh vực v1 (G4.3); model vẫn chung theo thiết kế |
| 4 | Đa ý định | ✅ (1 hồi quy) | ✅ | hồi quy p23 đã sửa (G4.8) |
| 5 | Nhiều người dùng, không lẫn dữ liệu | 🟡 | ✅ | F2 sửa (G1.2); phần luật song song (G3.1). Còn: chờ hàng Friendly khi đông (D17) |
| 7 | Hỏi lại khi câu không rõ | ❌ | ❌ | 47% → 50%, chưa tới 60% |
| 9 | Một chỗ quản lý xoá / tài khoản | 🟡 | ✅ | ô Tài khoản (G1.4) |
| 10 | Khoanh vùng theo địa bàn | ❌ | ✅ (cấp tỉnh) | thẻ hỏi tỉnh, tỉnh trong hồ sơ, danh sách 34 tỉnh từ dữ liệu (G4.4); xã/phường chưa có dữ liệu |
| 11 | Ngữ cảnh, tóm tắt giữ thủ tục đang hỏi | 🟡 | ✅ | G4.6 |
| 13 | Tự đặt tên phiên theo thủ tục | ❌ | ✅ | G4.5 |
| 15 | Nhập dữ liệu có thời gian cập nhật | ✅ (rủi ro) | ✅ | cổng kiểm (F3), link Cổng (F4), DB bất biến theo phiên bản (G2) |
| 17 | Lưu / tải biểu mẫu | ❌ | 🟡 | tên mẫu + link trang thủ tục (D7); Cổng trả tệp 0 byte nên không lưu tệp |
| — | Liệt kê / thống kê nhanh | 🟡 | ✅ | text-to-SQL (G4.2) |

Sau: **12 ✅, 6 🟡, 1 ❌** (3 bộ kiểm, 14 tìm theo nghĩa, 16 từ đồng nghĩa, 17, 19 benchmark vẫn 🟡; 7 vẫn ❌).

## 5. Việc chưa xong và lý do
- **G4.1 hỏi lại khi mơ hồ:** hai tín hiệu theo kế hoạch (reranker; độ rộng cụm chính) đều **lỗ ròng** trên dữ liệu chọn ngưỡng (tốt nhất +1 ca hỏi lại đúng / −13 ca trả lời đúng). Dữ liệu chọn ngưỡng đã ở mức 83–90% trong khi bộ mù 50%: hai bên khác nhau, chỉnh trên dev/p30 không giúp bộ mù. Theo quy tắc của kế hoạch, không đưa gì vào.
- **G4.10 từ đồng nghĩa ở trang Quản trị:** tuỳ chọn; đụng 4 chỗ trong lõi truy hồi (`build.py`, `query.py`, `context.py`, `policy.py`), nên làm thành một việc riêng có mẫu so khớp.
- **Lượt chỉ-luật khi đông người** (p95 1,18 s so với 0,5 s): chưa tối ưu.
- **Vượt ngân sách đo GPU ở G3.4** (kế hoạch cho ≤ 2 lần chạy ngắn): đã chạy 3 lượt test tải + khoảng 3 lượt test hợp đồng, một lượt treo GPU khoảng 10 phút trước khi có trần độ dài. Trưởng nhóm đã cho phép dùng thêm sau đó.
- Gợi ý "Nhớ tỉnh/thành cho tài khoản" mới hiện ở web System 3, chưa hiện ở Strict trong System 4. Tên tỉnh cũ trước sáp nhập (Bình Dương…) chưa đổi sang tỉnh mới.

## 6. Việc cần trưởng nhóm quyết
1. **Nhãn golden và thẻ hỏi tỉnh:** 9 ca bộ mù (6 ca dev) nhãn "trả lời" nay hỏi tỉnh theo D5. Sửa nhãn (bộ mù không còn "mù" với các ca này) hay giữ và báo kèm giải thích?
2. **Hỏi lại khi mơ hồ:** cần bộ chọn ngưỡng mới giống câu hỏi thật (ví dụ câu thật từ nhật ký thí điểm) mới tiến tiếp được.
3. **Slide và bài báo:** 9 mục slide, 7 mục bài báo ở [SUA_SLIDE_VA_BAI_BAO.md](SUA_SLIDE_VA_BAI_BAO.md). Mục cần sửa trước: bài báo ghi Qwen-2.5 trên vLLM + MCP, thực tế là `qwen3:4b-instruct` trên Ollama.
4. **Dữ liệu thật "DS LỚP 1.5"** trong runtime và lịch sử git có dữ liệu trẻ em cũ: xoá / viết lại lịch sử hay không (G1.6).
5. **28 mã thủ tục cũ chưa ghép được** sang bản 3: cần người duyệt ([LINEAGE_CAN_DUYET.md](LINEAGE_CAN_DUYET.md)).
6. Push nhánh `exec/2026-10-19-audit-fixes` và mở PR khi trưởng nhóm đồng ý.

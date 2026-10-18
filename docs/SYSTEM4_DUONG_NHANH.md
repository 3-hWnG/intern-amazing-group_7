# Đường nhanh (fast path) cho Chuyên gia + Bảng điều khiển lĩnh vực (18/10/2026)

## A. Yêu cầu (nguyên văn ý của leader, 18/10)
- Làm lĩnh vực mới dễ hơn: không phải viết riêng một hệ thống cho mỗi lĩnh vực; bộ đọc tệp đang quá cơ bản.
- **Không** gộp System 3, System 4 và ABI thành một. Áp dụng pipeline mới, rồi **đo đàng hoàng xem có hơn pipeline cũ không**.
- Có công cụ Excel trong `tools/` và dữ liệu du lịch giả, ngắn, dùng được trên web (vì phải đi qua pipeline).
- Mọi việc quản lý dữ liệu dùng chung của lĩnh vực (gồm cả dữ liệu Strict / thủ tục và thống kê thủ tục) dời về **một chỗ**.
- Không sửa, hoặc sửa mà không ảnh hưởng nhiều tới các hệ thống hiện có.

Trả lời trắc nghiệm (18/10):

| Câu | Trả lời |
|---|---|
| Dashboard đặt ở đâu | Mở rộng hộp **Lĩnh vực** sẵn có; dời các thứ ở trang Quản trị qua; một chỗ duy nhất cho lĩnh vực, dữ liệu, thống kê |
| Ai thấy | Cùng một nút; người dùng thấy ít hơn; **cán bộ giống dev**; có công tắc "xem như người dùng" |
| Trang /s4/admin | Chỉ còn quản lý tài khoản và **Thử tìm kiếm** (chỉ dev); dữ liệu và thống kê qua hộp Lĩnh vực; cào dữ liệu và thống kê **thu gọn được** |
| Bố cục | Danh sách lĩnh vực bên trái, tab bên phải |
| Pipeline mới bật thế nào | Theo lĩnh vực + bài tự kiểm (hồ sơ `fast_path`, mặc định bật); Strict và ABI không đổi |
| Công cụ Excel | Script sinh Excel |
| Cách đo | Model thật, cũ so với mới, NV5 (dev + exam) + bộ mù du lịch soạn trước khi chỉnh; toàn bộ test để bắt hồi quy; tối đa 2 lượt đo đầy đủ |

## B. Thiết kế đường nhanh (`system4/server/fastpath/`)
Ý chính: **dời việc tốn AI từ lúc hỏi sang lúc nạp**. Đây là cách System 3 nhanh (luật + dữ liệu đã chuẩn hoá, không AI ở đường nóng),
áp tự động cho tệp bất kỳ thay vì viết tay cho từng lĩnh vực.

1. **Biên dịch lúc nạp** (`compile.py`, chạy nền sau khi tệp nạp xong; bộ dữ liệu dùng được ngay bằng đường cũ trong lúc chờ):
   gom bản ghi thành bảng; suy kiểu cột (đánh dấu x / ngày / số / mã / nhóm / chữ; cột chữ dài không dùng làm điều kiện lọc);
   nhận bảng con theo cột khoá (vd. 8 sheet của `MAU_100_THU_TUC.xlsx` nối bằng `proc_id`); gợi ý từ tên cột; và (⚙ `FASTPATH_LLM_CUES`)
   gọi AI **một lần mỗi bảng** để lấy tên trường tiếng Việt + cách hỏi + từ phủ định cho cột đánh dấu. Code **lọc lại** gợi ý của AI
   (AI 4B hay đưa giá trị trong ô hoặc chữ chung: "sở xây dựng" cho cột cơ quan, "không" làm từ phủ định của cột "Nữ").
2. **Tự kiểm lúc nạp** (`selftest.py`): code sinh câu hỏi + đáp án từ chính dữ liệu (tra trường, đếm theo cột đánh dấu / cột nhóm, một tên
   không có, trích đoạn văn bản), chạy engine; loại câu nào của bảng nào đạt dưới ⚙ `FASTPATH_MIN_PASS` (0,9) thì tắt, câu hỏi loại đó đi đường cũ.
   Giới hạn: câu sinh ra dùng chính tên trường nên chỉ bắt lỗi **cấu trúc** (tiêu đề trùng, cột lọc sai…), không đo được cách người thật hỏi.
3. **Trả lời lúc hỏi** (`engine.py`, code thuần, vài mili giây), gọi trong `chat.py` **trước** bước tìm kiếm, sau guardrail "chặn":
   nhận dòng bằng IDF + "tên nằm trọn trong câu" (NAMED_PREC của System 3) + so dấu khi gõ có dấu (ACCENT_MISMATCH); nhận trường bằng gợi ý;
   câu nối tiếp dùng dòng của lượt trước (kể cả khi lượt trước do AI trả lời với đúng một nguồn); đếm / liệt kê / tháng / năm / sắp tới tính trên
   cả bảng; trùng tên thì hỏi lại bằng nút (tôn trọng `clarify` và số lần hỏi lại tối đa); gọi đích danh một tên riêng không có trong dữ liệu
   thì nói không có (chỉ ở lĩnh vực `grounded`). Không chắc thì **nhường** đường cũ (tìm kiếm + AI), lý do ghi trong 🔍.
4. Không áp cho Thủ tục (System 3 giữ nguyên luật đã tune) và ABI (bộ dữ liệu đồng bộ bỏ qua; router viết tay giữ nguyên).
   Câu trả lời bằng code dùng được cả khi tài khoản bật "Chỉ trả lời bằng luật".

Nguồn gốc: nguyên mẫu `research/domain_compiler/` (cùng ngày). Trên dữ liệu ABI (chạy một lần, không chỉnh) nguyên mẫu chưa có tự kiểm
trả lời sai 22/43 câu nó tự trả lời; các luật "cột chữ dài không lọc", "tra theo thuộc tính phải biết trường được hỏi" và bài tự kiểm sinh ra từ đó.

## C. Bảng điều khiển lĩnh vực
Nút **Lĩnh vực** (trang chat) = một chỗ cho lĩnh vực, dữ liệu, đường nhanh, thống kê (`system4/web/static/js/dashboard.js`, `dashboard.css`).
- Trái: các lĩnh vực + "Thêm lĩnh vực"; dev / cán bộ có thêm *Dữ liệu mọi người dùng*, *Thống kê chung*.
- Phải, theo lĩnh vực: **Tổng quan** (ghim, dùng, sửa tên / guardrail / hồ sơ JSON / cứng-mềm / khoá) · **Dữ liệu** (Thủ tục: phiên bản, nháp,
  sửa / xoá / so sánh / áp dụng, Xuất Excel, cào dichvucong.gov.vn thu gọn; ABI: phiên bản, đồng bộ + lịch sử thu gọn; lĩnh vực khác: bộ dữ liệu) ·
  **Đường nhanh** (kiểu cột, tên trường, cách hỏi, gợi ý bị bỏ, kết quả tự kiểm, nút Biên dịch lại) · **Thống kê** (Thủ tục).
- Quyền: dev = cán bộ ở mọi mục trên (API `/s4/admin/procs|stats|datasets|feedback`, `/s4/abi/*`, sửa lĩnh vực, dữ liệu của người khác).
  Chỉ dev: `/s4/admin` (tài khoản, Thử tìm kiếm), ⚙ Cài đặt (gồm khoá API ABI). Người dùng thường: lĩnh vực của mình, dữ liệu của mình.
  **Thay đổi quyền riêng tư cần biết**: trước đây chỉ dev mở được dữ liệu riêng của người khác (NV3, 2B); nay cán bộ cũng mở được (theo câu "cán bộ giống dev").
- "Xem như người dùng": chỉ vẽ lại giao diện như người dùng thường thấy; quyền thật vẫn do máy chủ kiểm.

## D. Dữ liệu thử
`system4/eval/make_tourism.py` → `system4/eval/data/du_lich_gia.xlsx` (3 sheet: Điểm đến 12, Khách sạn 12, Tour 10; khách sạn / tour / giá / số điện thoại
là bịa). Tải lên web được như mọi tệp. Bộ câu **mù** 32 câu: `system4/eval/bench_cases.py` (suite `tourism`, split `blind`), soạn trước khi viết
đường nhanh, không chỉnh theo kết quả. Công cụ Excel trong `tools/xlsx_scripts/` (skill xlsx; xem `tools/README.md`).

## E. Kết quả đo: pipeline cũ so với mới (18/10/2026, model thật, 2 lượt đầy đủ như đã thống nhất)
Máy dev (RTX 4050 6 GB), `qwen3:4b-instruct-2507-q4_K_M`, temperature 0,2; cùng một runtime sạch cho cả hai lượt; đường nhanh đã biên dịch xong
trước khi hỏi (có gọi AI đặt tên trường). Lệnh: `BENCH_RUNTIME=<thư mục trống> python system4/eval/bench.py run inst02+old --set FASTPATH_ENABLED=false --split all`
rồi `... run inst02+new --split all`. Kết quả: `system4/eval/saved_results/2026-10-18/inst02+old.json`, `inst02+new.json`.

| | cũ | mới |
|---|---|---|
| NV5 đúng (accuracy + halluc, 59 câu) | 96,6% | 96,6% |
| NV5 accuracy dev / exam (24 / 20 câu) | 24 / 20 | 24 / 20 |
| Chào hỏi (18 câu) / hành vi (22 tình huống) | 100% / 17/22 | 100% / 17/22 |
| **Bộ MÙ du lịch** (32 câu) | **26/32 (81,2%)** | **24/32 (75,0%)** |
| Câu do đường nhanh trả lời | 0 / 109 | 29 / 109 (27 đúng) |
| Trung vị cả câu / chữ đầu (mọi câu) | 3,45 s / 1,71 s | 2,22 s / 0,83 s |
| p90 cả câu | 7,0 s | 6,65 s |
| Riêng 29 câu đường nhanh trả lời: trung vị cả câu | 3,01 s (đường cũ) | 0,08 s |

Đọc cho đúng:
- **Nhanh hơn rõ khi đường nhanh trả lời** (0,08 s so với ~3 s, không gọi AI). Nhưng phần lớn 29 câu đó nằm ở NV5: engine được phát triển trên chính bộ này
  (nguyên mẫu `research/domain_compiler/`), nên tỉ lệ phủ và độ đúng trên NV5 là **lạc quan**.
- **Trên dữ liệu mới (bộ mù) pipeline mới CHƯA hơn**: đường nhanh chỉ trả lời 4/32 câu (tự kiểm tắt 5/6 loại câu của tệp du lịch), trong đó **2 câu sai**
  mà đường cũ trả lời đúng → 24/32 so với 26/32. Hai câu sai:
  `tv-b17` "Liệt kê các tour đi Đà Lạt" → hỏi lại "bạn hỏi tour nào" thay vì liệt kê;
  `tv-b18` "Có bao nhiêu điểm đến ở miền Trung?" → trả lời trường "Điểm đến" của tour "Di sản miền Trung".
- Bài tự kiểm **có tác dụng bảo vệ**: các bảng Điểm đến, Khách sạn tự kiểm chỉ đạt ~83% nên bị tắt, câu hỏi về chúng đi đường cũ.
  Nó không bắt được hai lỗi trên vì câu tự sinh không có dạng "liệt kê … <tên trùng>" và "bao nhiêu <danh từ> ở <chữ nằm trong tên một dòng>".

Lỗi chung tìm ra (từ báo cáo tự kiểm + 2 câu sai; **chưa sửa**, vì sửa rồi đo lại trên chính bộ mù này thì số không còn trung thực):
1. Tên dòng bị lọc mất chữ: "Khách sạn Cố Đô" → "khách sạn" là danh từ của bảng, "cố" / "đô" bỏ dấu trùng từ dừng "có" / "đó" → không nhận ra tên dù nằm trọn trong câu.
   Luật "tên nằm trọn" phải xét trên câu gốc, không phải trên phần chữ còn lại sau khi lọc.
2. Câu có từ đếm ("bao nhiêu", "mấy") vẫn có thể bị trả lời như câu tra một dòng khi chữ còn lại nằm trong tên một dòng (b18).
3. Câu liệt kê gặp nhiều dòng ngang điểm thì hỏi lại thay vì liệt kê (b17).
4. Danh từ do AI đặt có chữ thừa ("một tour", "một điểm đến") → luật "bao nhiêu <danh từ>" hỏng, câu chữ lủng củng.
5. Cột giá tiền (số ≥ 6 chữ số, không trùng) bị xếp kiểu "mã"; mã ngắn duy nhất ("T01") không lọc được.

Việc nên làm tiếp (cần leader quyết): sửa 5 lỗi trên + thêm vào bài tự kiểm các dạng câu "liệt kê" / "bao nhiêu <danh từ> ở <giá trị>", rồi đo trên **bộ mù mới**
(dữ liệu khác, câu soạn trước khi sửa). Trước khi có số đó, nên để ⚙ `FASTPATH_ENABLED` bật (không hại trên NV5, nhanh hơn rõ) nhưng biết rằng trên dữ liệu
lạ nó có thể trả lời sai một ít câu đếm / liệt kê; hoặc tắt cho lĩnh vực quan trọng bằng `"fast_path": false`.

Hồi quy: mọi test System 4 đạt (gồm `test_fastpath`, `test_dashboard` mới; `test_nv5` cập nhật vì đường nhanh nay là mặc định). Test System 3 đạt khi chạy trên
DB dựng từ snapshot hiện tại; trên máy dev, `data/runtime/system3.db` (12/10) đã cũ hơn code (thiếu `proc_flat`) nên 10 test System 3 hỏng nếu dùng DB đó —
có từ trước, không do thay đổi này; dựng lại bằng `python run_server.py -m system3.data.build`. `test_nv3` thoát với mã 139 sau khi in OK — có cả trên commit
gốc, không do thay đổi này.

Phát hiện phụ: `system4/eval/bench.py` trước đây dùng `../pyroot`, mà trên máy dev junction đó trỏ sang repo **system3 khác** → server của bench import
`system3.*` của repo kia. Đã sửa (`_pyroot()` chọn junction trỏ đúng repo này; `BENCH_PYROOT`, `BENCH_RUNTIME` ghi đè được). Các số bench NV5 cũ
(`saved_results/2026-10-15`) có thể đã đo lẫn code của repo kia — nên coi là chưa chắc.

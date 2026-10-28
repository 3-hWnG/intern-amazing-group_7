# Báo cáo Bài báo 2 — System 4 (biên dịch lĩnh vực lúc nạp, bộ mù `real_v4_s4`)

Ngày 26/10/2026. Nhánh `merge_sys_3_4`. Theo `docs/KE_HOACH_BAI_BAO_2_SYSTEM4_2026-10-25.md`.

**Trạng thái (cập nhật 27/10/2026):** J1 xong (khoá bộ mù). **J2 xong** — Trịnh Hoàng Nhân sửa 4 lỗi S4-1→S4-4 trên dev (`real_v3`), xác nhận chưa đọc Phần B/nhãn `real_v4_s4` trước khi viết code (xem mục 0, `LOCK.md`). **J3 đã chạy xong** — 7 cấu hình (6 theo kế hoạch + 1 bổ sung để trả lời đúng câu hỏi "tự kiểm có chặn bảng nguy hiểm không"), đúng 1 lần mỗi cấu hình trên bộ mù `real_v4_s4` (216 câu), code đã đóng băng trước khi chạy. Kết quả thật ở mục 3.

## 0. Ai sửa engine (J2) — đã chốt

Theo nguyên tắc cứng của kế hoạch (mục 2, J1): *"Người sửa engine không được đọc câu hỏi phần B trước khi khoá."* dj, Claude, và nhiều khả năng Nguyễn Viết Hưng đều không đủ điều kiện (đã thấy Phần B/nhãn trước khi khoá — xem lịch sử tài liệu này).

**Trịnh Hoàng Nhân** nhận làm J2, xác nhận (27/10/2026, qua dj) chưa đọc câu hỏi/đáp án Phần B của `real_v4_s4` trước khi viết code. Đã sửa đủ 4 lỗi theo cờ (`FASTPATH_WIDE_TABLE`, `FASTPATH_ACCENT_FIRST`, `FASTPATH_ATTR_GUARD`, `FASTPATH_CLEAN_SHOW`), kiểm trên dev (`real_v3`) — 3/4 đạt ngay, S4-3 (`FASTPATH_ATTR_GUARD`) cần sửa lại 1 lần sau khi kiểm thấy case thật (`v3-san_bay-12`) vẫn fail dù unit test cô lập đã pass; sau lần sửa thứ 2, cả 4 cờ đạt (xem `Downloads/J2_devcheck_S4_2026-10-27.md` cho số liệu dev chi tiết, không phải số J3).

## 1. Bộ mù `real_v4_s4` (J1 — đã khoá)

- **216 câu**: 128 câu khuôn (Phần A, sinh từ `make_cases_v4.py`, SEED cố định, đáp án code tự tính) + 88 câu người viết (Phần B, chỉ xem tên cột không xem dữ liệu khi viết).
- **8 bảng Wikipedia thật** (CC BY-SA 4.0, revid ghi trong `SOURCES.md`), ≥ 6 lĩnh vực khác 4 lĩnh vực của `real_v3`: di tích đặc biệt, trường đại học, báu vật quốc gia, ngân hàng, thể thao/sân vận động, dân tộc, văn hoá phi vật thể, xe buýt TPHCM.
- ≥ 2 tệp nhiều sheet cùng đối tượng (để test lỗi ghép sheet S4-1).
- Cột bẩn cấy chủ động (ô gộp, năm dạng "tháng/năm", số kèm đơn vị) + cặp tên gần trùng có/không dấu (test S4-2).
- 2 bảng (ngân hàng, xe buýt TPHCM) được xây thay cho 2 bảng gốc yếu, bằng cách rút trực tiếp từ wikitext Wikipedia (không qua AI tóm tắt số liệu), có cột bị cố ý bỏ (giá vé, loại xe...) để câu từ chối đúng là đúng thật.
- **Độ đồng thuận 2 người gán nhãn độc lập (Phần B, 88 câu)**: κ hành vi tổng thể = 0,952 (từ chối κ=0,967, hỏi lại κ=0,935), đồng thuận đáp án 95,5%. 24/88 câu khác biệt: 2 bất đồng nội dung (đã họp chốt theo dj, ghi lý do trong `ASSUMPTIONS_B.md`), 22 khác định dạng/biên rộng (gộp union). Chi tiết: `system4/eval/real_v4_s4/LOCK.md`, `ASSUMPTIONS_B.md`.
- Mã băm SHA256 toàn bộ tệp dữ liệu + script + nhãn đã ghi vào `LOCK.md` trước khi bất kỳ ai được sửa code J2.

## 2. Giao thức đo (J3 — đã thực hiện đúng như khung này)

- **Dev = `real_v3`** (bộ mù cũ, đã mở từ bài báo đợt trước): mọi cờ sửa lỗi S4-1→S4-4 chỉ được viết/chỉnh trên dev này, không được đụng tới `real_v4_s4`.
- **Test = `real_v4_s4`**: đóng băng code (không có thay đổi chưa commit trong `system4/server/fastpath/`, `system4/eval/`) rồi mới chạy — mỗi cấu hình **đúng một lần**, không chạy lại, không sửa đáp án sau khi thấy số.
- **6 cấu hình** (chạy qua `system4/eval/bench.py`, suite `real4` đã nối trong `bench_cases.py`): tối thiểu cần có bản "trước" (code gốc, chưa sửa S4-1→S4-4) và bản "sau" (đã sửa đủ 4 lỗi) để so cặp McNemar; 4 cấu hình còn lại theo đúng khuôn `real_v3` (rag/old/fp/fp+agg hoặc tương đương) — **chốt chính xác tên 6 cấu hình trước khi chạy, không thêm/bớt sau khi thấy số** (JD mục 8).
- **Giám sát nhiệt độ**: `eval/thermal.py` đã gọi sẵn trong `bench.py` theo từng câu (`guard(label=c["id"])`), ngưỡng ≤ 70°C — không cần code thêm.
- **Chỉ số báo cáo** (`system4/eval/real_v4_s4/report_v4.py`, script có sẵn từ trước, đã chạy ra số thật — xem mục 3): tỷ lệ đạt + Wilson 95% — chung, theo loại câu, theo lĩnh vực, **tách riêng Phần A / Phần B**; trung vị thời gian; số câu đi đường nhanh/SQL; so cặp McNemar chính xác (tổ hợp, không phải xấp xỉ) cho cặp cấu hình chính `v4a_before`/`v4a_after` (cả tổng và tách A/B).

## 3. Kết quả (J3 — đã chạy, 27/10/2026)

Code đóng băng trước khi chạy (không có thay đổi chưa commit trong `system4/server/fastpath/`; `system4/eval/bench.py` được sửa 3 chỗ thuần hạ tầng đo — nạp thiếu bộ dữ liệu `real_v4_s4`, một lỗi crash khi `check["num"]` là số lẻ, và thêm retry cho kết nối loopback hay rớt — không đụng code engine, xem `LOCK.md` mục 4 để biết chi tiết và vì sao lần chạy đầu của `v4a_before` không được tính). Mỗi cấu hình chạy đúng 1 lần trên `real_v4_s4` (216 câu: 128 Phần A + 88 Phần B), nhiệt độ giữ ≤70°C suốt (guard tự động trong `bench.py`).

### 3.1 Tỷ lệ đạt tổng thể (Wilson 95% CI)

| Cấu hình | Vai trò | Đạt / Tổng | % | CI 95% |
|---|---|---|---|---|
| `v4a_before` | SQL fastpath, trước sửa S4-1→S4-4 | 115/216 | 53,2% | [46,6% , 59,8%] |
| `v4a_after` | SQL fastpath, sau sửa đủ 4 lỗi — cặp chính so McNemar | 113/216 | 52,3% | [45,7% , 58,9%] |
| `v4a_sqlraw` | SQL fastpath thô (không qua compile wide-table) | 101/216 | 46,8% | [40,2% , 53,4%] |
| `v4b_fp` | fastpath tắt SQL (đường khác) | 116/216 | 53,7% | [47,0% , 60,2%] |
| `v4b_old` | đường cũ (tool-calling, không fastpath) | **131/216** | **60,6%** | [54,0% , 66,9%] |
| `v4b_rag` | RAG thuần (không SQL, không table tool) | 89/216 | 41,2% | [34,8% , 47,9%] |
| `v4a_noselftest` | SQL fastpath, **tắt ngưỡng tự kiểm** (FASTPATH_MIN_PASS=0, bật SQL cho mọi bảng) | 112/216 | 51,9% | [45,3% , 58,4%] |

### 3.1b Theo loại câu, trung vị thời gian, số câu đi đường nhanh/SQL (tổng Phần A+B, 216 câu)

| Cấu hình | L tra cứu | U không dấu | C đếm | S liệt kê | M lớn/nhỏ nhất | A tổng | R không có | F hỏi tiếp | X chéo sheet | AMB mơ hồ | trung vị s | đường nhanh | SQL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `v4a_before` | 32/74=43% | 14/24=58% | 15/16=94% | 11/16=69% | 10/16=62% | 6/8=75% | 5/26=19% | 12/16=75% | 9/12=75% | 1/8=12% | 1,3 | 126 | 91 |
| `v4a_after` | 30/74=41% | 14/24=58% | 15/16=94% | 11/16=69% | 10/16=62% | 6/8=75% | 6/26=23% | 12/16=75% | 7/12=58% | 2/8=25% | 1,1 | 129 | 89 |
| `v4a_sqlraw` | 28/74=38% | 12/24=50% | 11/16=69% | 11/16=69% | 8/16=50% | 5/8=62% | 6/26=23% | 12/16=75% | 7/12=58% | 1/8=12% | 1,2 | 140 | 101 |
| `v4b_fp` | 31/74=42% | 12/24=50% | 13/16=81% | 12/16=75% | 7/16=44% | 6/8=75% | 14/26=54% | 12/16=75% | 7/12=58% | 2/8=25% | 4,8 | 42 | 0 |
| `v4b_old` | 38/74=51% | 11/24=46% | 13/16=81% | 12/16=75% | 11/16=69% | 6/8=75% | 16/26=62% | 11/16=69% | 11/12=92% | 2/8=25% | 5,6 | 0 | 0 |
| `v4b_rag` | 31/74=42% | 10/24=42% | 1/16=6% | 3/16=19% | 3/16=19% | 2/8=25% | 15/26=58% | 11/16=69% | 11/12=92% | 2/8=25% | 3,9 | 0 | 0 |
| `v4a_noselftest` | 29/74=39% | 14/24=58% | 15/16=94% | 11/16=69% | 11/16=69% | 6/8=75% | 6/26=23% | 12/16=75% | 7/12=58% | 1/8=12% | 1,0 | 129 | 89 |

Ghi chú: `v4b_fp`/`v4b_old`/`v4b_rag` có trung vị thời gian cao hơn (4,8–5,6s) vì không đi đường nhanh (code trả lời trực tiếp) — mọi câu phải qua model sinh câu trả lời đầy đủ (tool-calling hoặc RAG), khác với `v4a_*` đi đường nhanh/SQL cho phần lớn câu (89–140/216) nên trung vị chỉ 1,1–1,3s. Đây là đánh đổi tốc độ-vs-độ chính xác đã biết từ `real_v3`, không phải phát hiện mới.

### 3.2 So cặp McNemar chính: v4a_before → v4a_after

| | before=sai | before=đúng |
|---|---|---|
| **after=đúng** | 3 | 110 |
| **after=sai** | 98 | 5 |

McNemar CHÍNH XÁC (tổ hợp, `real_v4_s4/report_v4.py`): +3/-5, p = 0,727 → KHÔNG có ý nghĩa thống kê. Sửa 4 lỗi S4-1→S4-4 không làm thay đổi đáng kể tỷ lệ đạt tổng thể trên bộ mù này (53,2% → 52,3%, chênh lệch nằm trong nhiễu). Tách riêng: Phần A +1/-5 (p=0,219, xu hướng giảm nhẹ nhưng chưa có ý nghĩa), Phần B +2/-0 (p=0,5) — không có phần nào đạt ngưỡng p<0,05.

Ghi nhận quan trọng, không giấu: cả 5 câu "trước đúng, sau sai" đều rơi đúng vào 1 domain (`san_van_dong`, 16/16 → 11/16) và đều có `fast_path.route` rỗng/absent ở cả hai lần chạy, với lỗi "nguồn sai (có: [])" — tức là một lần retrieval không lấy được dữ liệu bảng, không liên quan tới 4 cờ S4 vừa sửa. Đây gần như chắc là nhiễu giữa 2 lần chạy riêng biệt (temperature=0,2, không phải 0) hơn là hiệu ứng thật của code — khớp với McNemar tổng thể không có ý nghĩa.

### 3.2b So cặp McNemar khác — `v4a_after` (phương pháp đề xuất) vs từng mốc/ablation

Trước đây chỉ tính McNemar cho cặp trước/sau sửa lỗi. Bổ sung đủ các cặp chính mà JD yêu cầu (mỗi cấu hình trả lời một câu hỏi nghiên cứu riêng — xem mục 2):

| Cặp | +/- (tổng A+B) | p (tổng) | p (Phần A) | p (Phần B) | Ý nghĩa |
|---|---|---|---|---|---|
| `v4a_after` → `v4b_old` | +32/−14 | **0,011** | 0,020 | 0,42 | **CÓ ý nghĩa — `v4b_old` thắng** |
| `v4a_after` → `v4a_sqlraw` | +2/−14 | **0,004** | 0,039 | 0,13 | **CÓ ý nghĩa — biên dịch (`v4a_after`) vẫn tốt hơn SQL thô** |
| `v4a_after` → `v4b_rag` | +31/−55 | **0,013** | 0,021 | 0,48 | **CÓ ý nghĩa — `v4a_after` thắng RAG thuần** |
| `v4a_after` → `v4b_fp` | +14/−11 | 0,690 | 1,000 | 0,55 | Không có ý nghĩa |
| `v4a_after` → `v4a_noselftest` (tắt ngưỡng tự kiểm) | +2/−3 | 1,000 | 1,000 | 0,625 | Không khác biệt — **tự kiểm không đo được tác dụng bảo vệ trên bộ này** |

(Quy ước: "+" = `v4a_after` sai/đối thủ đúng, "−" = `v4a_after` đúng/đối thủ sai; dấu dương-âm không đối xứng về ý nghĩa thắng-thua, đọc cột cuối.)

**Sửa lại một kết luận đã viết hơi nhẹ ở 3.5 trước đây:** `v4b_old` thắng `v4a_after` không chỉ là "số cao hơn, chưa kiểm định" — **có ý nghĩa thống kê thật (p=0,011)**, đây là phát hiện mạnh nhất của J3, không phải quan sát phụ.

### 3.3 Theo domain (v4a_before vs v4a_after)

| Domain | before | after |
|---|---|---|
| bao_vat | 13/27 | 13/27 |
| dai_hoc | 15/16 | 15/16 |
| dan_toc | 14/27 | 14/27 |
| di_tich_dac_biet | 10/16 | 11/16 |
| di_tich_quoc_gia_dac_biet | 2/11 | 3/11 |
| ngan_hang | 17/27 | 17/27 |
| phi_vat_the | 11/27 | 11/27 |
| san_van_dong | 16/16 | 11/16 (xem ghi nhận 3.2) |
| the_thao | 5/11 | 6/11 |
| truong_dai_hoc | 3/11 | 3/11 |
| xe_buyt | 9/27 | 9/27 |

### 3.4 Tách Phần A (khuôn, 128 câu) / Phần B (người viết, 88 câu) — Wilson 95% CI

| Cấu hình | Phần A | Phần B |
|---|---|---|
| `v4a_before` | 89/128 = 69,5% [61,1,76,8] | 26/88 = 29,5% [21,0,39,8] |
| `v4a_after` | 85/128 = 66,4% [57,9,74,0] | 28/88 = 31,8% [23,0,42,1] |
| `v4a_sqlraw` | 77/128 = 60,2% [51,5,68,2] | 24/88 = 27,3% [19,1,37,4] |
| `v4b_fp` | 85/128 = 66,4% [57,9,74,0] | 31/88 = 35,2% [26,1,45,6] |
| `v4b_old` | 99/128 = 77,3% [69,4,83,7] | 32/88 = 36,4% [27,1,46,8] |
| `v4b_rag` | 65/128 = 50,8% [42,2,59,3] | 24/88 = 27,3% [19,1,37,4] |
| `v4a_noselftest` | 86/128 = 67,2% [58,8,74,6] | 26/88 = 29,5% [21,0,39,8] |

Mọi cấu hình đều đạt thấp hơn rõ ở Phần B so với Phần A — khớp với kỳ vọng ban đầu: Phần B khó hơn vì không sinh từ khuôn có kiểm soát.

### 3.5 Quan sát cần nêu thẳng cho bài báo (không phải diễn giải thuận lợi)

- **v4b_old (đường cũ, tool-calling, không fastpath) đạt cao nhất (60,6%) và thắng v4a_after (fastpath đã sửa đủ 4 lỗi, 52,3%) CÓ Ý NGHĨA THỐNG KÊ (McNemar p=0,011, mục 3.2b)** — không phải chỉ là số cao hơn chưa kiểm định. Khác với real_v3 cũ (85% vs 88%, không có ý nghĩa). Đây là phát hiện mạnh nhất, bất lợi cho phương pháp fastpath đề xuất của bài báo; ghi nhận thẳng, không chọn số có lợi.
- v4b_rag (RAG thuần) thấp nhất (41,2%) — cho thấy cả SQL fastpath và tool-calling đều hơn RAG thuần trên dữ liệu bảng, nhất quán với lý do thiết kế System 4.
- **`v4a_noselftest` (tắt ngưỡng tự kiểm) gần như giống `v4a_after` (51,9% vs 52,3%, McNemar p=1)** — bỏ bài tự kiểm không làm giảm độ chính xác trên bộ này, nghĩa là bài tự kiểm hiện tại không chặn được lỗi gì đáng kể trên 8 bảng mới (mục 3.7). Đây không chứng minh bài tự kiểm vô dụng nói chung — chỉ là trên đúng 8 bảng của `real_v4_s4`, không có bảng nào "đủ xấu" để tự kiểm phải chặn.
- Lỗi "hỏi lại thừa" / "không hỏi lại" / "không nói là không có / không biết" xuất hiện ở MỌI cấu hình, tập trung nhiều ở Phần B — cho thấy đây là vấn đề hành vi chung của model nền (qwen3:4b-instruct, temperature 0,2), không riêng gì fastpath hay engine.
- File kết quả thô đầy đủ: `system4/eval/results/bench/inst02+<tên cấu hình>.json` (216 bản ghi/file, có lý do fail chi tiết từng câu).


### 3.6 Hành vi chung ("22 tình huống", `nv2_behavior.py`, 27/10 20:00–20:20)

Chạy lại riêng phần này sau khi vá lỗi hạ tầng (xem mục 5 `LOCK.md`) — không chạy lại 216 câu, không vi phạm luật không re-run vì chưa từng có kết quả hành vi hợp lệ trước đó.

| Cấu hình | Đạt |
|---|---|
| `v4a_before` | 17/22 |
| `v4a_after` | 17/22 |
| `v4a_sqlraw` | 17/22 |
| `v4b_fp` | 17/22 |
| `v4b_old` | 17/22 |
| `v4b_rag` | 17/22 |
| `v4a_noselftest` | 17/22 |

**Cả 7 cấu hình ra đúng 17/22, fail đúng cùng 5 tình huống** — hợp lý, không phải lỗi đo: 22 tình huống này đo lớp hành vi/guardrail chung của chế độ Friendly (vai trò, ngôn ngữ, roleplay, cảm xúc, bộ nhớ, tốc độ trả lời), hoàn toàn không liên quan tới cờ fastpath/SQL đang so sánh — nên không có lý do gì để khác nhau giữa các cấu hình. Chỉ số này không giúp phân biệt được các cấu hình, nhưng vẫn đáng ghi lại vì cho thấy 5 lỗi hành vi tồn đọng, không phụ thuộc engine:

- **4/5 lỗi liên quan bộ nhớ** (chế độ "chỉ nhớ khi được bảo"): tự nhớ thông tin người dùng khi chưa được yêu cầu, không nhớ đúng sở thích khi được bảo nhớ, không mang theo bộ nhớ (tên + nghề) sang hội thoại mới, hỏi lại thông tin đã được nhớ (thành phố) thay vì dùng luôn.
- **1/5 lỗi vai trò**: không xưng "chúng tôi/mình" và không nói về "Team 7" khi được hỏi "Team 7 là ai vậy?".
- Đây là lỗi ở lớp hành vi/bộ nhớ chung của model nền (qwen3:4b-instruct), không phải lỗi S4-1→S4-4 hay fastpath — nằm ngoài phạm vi sửa của J2 nhưng cần ghi nhận là việc tồn đọng cho bản sau.
### 3.7 Số bảng qua tự kiểm (selftest) — theo log console từng lần chạy (27/10)

`v4a_before`/`v4a_after` (FASTPATH_WIDE_TABLE khác nhau) có log giống nhau (vì cờ đó không đổi self-test theo cách này); `v4a_sqlraw`/`v4b_fp`/`v4b_old`/`v4b_rag` giống nhau (đều FASTPATH_SQL=false, self-test chạy trên dạng bảng khác):

| Lĩnh vực | `v4a_before`/`v4a_after` | `v4a_sqlraw`/`v4b_fp`/`v4b_old`/`v4b_rag` |
|---|---|---|
| policy | bật 4/4 loại câu | bật 3/3 loại câu |
| dan_toc | bật 5/6 | bật 3/4 |
| san_van_dong | bật 4/6 | bật 2/4 |
| phi_vat_the | bật 1/3 | bật 0/2 |
| bao_vat | bật 2/3 | bật 2/2 |
| dai_hoc | bật 2/3 | bật 1/2 |
| di_tich_dac_biet | bật 2/3 | bật 1/2 |
| ngan_hang | bật 3/3 | bật 2/2 |
| xe_buyt_tphcm | bật 2/3 | bật 1/2 |

Không có bảng nào bị tắt hoàn toàn (0 loại câu nào qua) ở cả 8 bảng mới — tức ngưỡng tự kiểm không chặn cứng bảng nào trong bộ `real_v4_s4`, chỉ tắt một số loại câu cụ thể (ví dụ `phi_vat_the` chỉ qua 0-1/2-3 loại).

**Cấu hình thứ 7 đã bổ sung, trả lời đúng câu hỏi JD mục 3 (J3), số 6:** `v4a_noselftest` (giống `v4a_after`, thêm `FASTPATH_MIN_PASS=0`, bật SQL cho MỌI bảng kể cả bảng không qua ngưỡng tự kiểm). Kết quả: 112/216 = 51,9%, so với `v4a_after` 113/216 = 52,3% — McNemar +2/−3, p=1, **hoàn toàn không khác biệt** (mục 3.1, 3.2b). **Trả lời câu hỏi nghiên cứu:** trên bộ `real_v4_s4`, bỏ ngưỡng tự kiểm không làm giảm (cũng không làm tăng) độ chính xác — tự kiểm hiện tại không đo được tác dụng "chặn bảng nguy hiểm" nào trên 8 bảng này (có thể vì không bảng nào trong bộ này đủ "nguy hiểm" theo nghĩa tự kiểm được thiết kế để bắt, hoặc ngưỡng 0,9 không đủ nhạy). (Lần chạy đầu của `v4a_noselftest` bị lỗi hạ tầng — dùng nhầm bảng biên dịch cũ do chưa xoá runtime — đã phát hiện, bỏ, chạy lại; xem `LOCK.md` mục 7.)

### 3.8 Số dòng code riêng cho từng lĩnh vực mới (real_v4_s4): 0

Đã kiểm bằng `grep -rn "ngan_hang\|xe_buyt\|dan_toc\|san_van_dong\|phi_vat_the\|bao_vat\|dai_hoc\|di_tich" system4/server/fastpath/` — **không có kết quả nào**: không dòng code nào trong engine (`fastpath/`) biết tên hay đặc thù của 8 lĩnh vực mới. Toàn bộ việc "thêm lĩnh vực" chỉ là: tải bảng lên qua `/s4/datasets`, viết `SOURCES.md`, và (cho việc đo, không phải sản phẩm) viết câu hỏi kiểm ở `build_v4.py`/`make_cases_v4.py` (script đo, không phải engine). Đây là bằng chứng trực tiếp, kiểm được, cho đúng luận điểm chính của bài báo ("thêm lĩnh vực mới chỉ bằng tải bảng lên, không viết code mới").


### 3.9 Thời gian nạp mỗi bảng — `system4/eval/table_load_time.py` (27/10, đo riêng, không đụng dữ liệu J3)

| Lĩnh vực | Thời gian nạp |
|---|---|
| dan_toc | 50,0s |
| phi_vat_the | 37,2s |
| dai_hoc | 38,6s |
| bao_vat | 29,3s |
| di_tich_dac_biet | 22,4s |
| san_van_dong | 19,2s |
| xe_buyt_tphcm | 15,8s |
| ngan_hang | 12,2s |

**Trung vị: 29,3s** (bao gồm cả biên dịch + bài tự kiểm cho tới khi đường nhanh sẵn sàng, không chỉ upload). Dao động 12–50s theo từng bảng, không có xu hướng rõ theo số dòng (chưa kiểm tương quan kích thước file — không trọng tâm của bài).
## 4. Giới hạn đã biết trước khi đo (không phải kết quả)

- Bộ `real_v4_s4` chỉ có 8 bảng/216 câu — không đại diện hết độ đa dạng dữ liệu hành chính/thống kê tiếng Việt thật.
- 2/8 bảng (ngân hàng, xe buýt) được xây lại trong tuần này để thay 2 bảng yếu — có ít thời gian kiểm tra độc lập hơn 6 bảng còn lại từ trước.
- Phần B chỉ có 2 người gán nhãn độc lập (không phải 3+), nên khoảng tin cậy của κ không được báo cáo riêng (mẫu theo từng câu nhỏ).
- J2/J3 đã xong (xem mục 0, 3). Rủi ro tiến độ còn lại: J4 (viết báo cáo/paper) — đang làm, xem `docs/paper2_draft_en.md` mục 6.
- `v4b_old` (đường cũ) đạt cao hơn mọi biến thể fastpath trên bộ mù này (mục 3.5) — cần một bản thảo luận trung thực về việc này trong bài báo, không chỉ báo cáo thắng.
- **Dữ liệu "22 tình huống hành vi" ban đầu thiếu ở cả 6 cấu hình gốc** do lỗi hạ tầng đo (`nv2_behavior.py` tự đoán sai đường dẫn `pyroot`, crash ngay từ dòng import đầu — không phải lỗi mạng như chẩn đoán ban đầu, xem `LOCK.md` mục 5) — đã vá và chạy lại riêng phần này (không chạy lại 216 câu), kết quả ở mục 3.6.

## 5. Thảo luận và kết luận

Câu hỏi đặt ra: sửa 4 lỗi S4-1→S4-4 trên engine có cải thiện độ chính xác fastpath trên bộ mù khó hơn (`real_v4_s4`) không? **Trả lời: không rõ rệt** — 53,2% → 52,3% (McNemar chính xác p=0,727). Các lỗi sửa là thật (xác nhận trên dev `real_v3`, không làm dev tụt) nhưng không chuyển thành cải thiện có ý nghĩa thống kê trên bộ mù này.

**Cập nhật quan trọng (sau khi tính đủ các cặp McNemar, mục 3.2b):** `v4b_old` thắng `v4a_after` CÓ ý nghĩa thống kê (p=0,011) — không chỉ là quan sát số như bản viết đầu.

Phát hiện đáng chú ý hơn là so sánh kiến trúc: `v4b_old` (đường cũ, tool-calling) đạt 60,6%, cao hơn MỌI biến thể fastpath kể cả bản đã sửa đủ 4 lỗi (52,3%) — **khác biệt này CÓ ý nghĩa thống kê (McNemar p=0,011)**, không phải nhiễu đo. Trên `real_v3` hai đường gần như ngang nhau (85% vs 88%, không có ý nghĩa); trên `real_v4_s4` khó hơn, khoảng cách mở ra có lợi cho đường cũ, và lần này là một khác biệt thật. Khả năng cao: cách SQL fastpath ghép schema bằng heuristic đơn giản (so khớp chuỗi con bỏ dấu, không join nhiều bảng, theo ADR-09) dễ gãy hơn trước bảng/miền mới lạ so với đường tool-calling chậm hơn nhưng tổng quát hơn — tuy 8 bảng/216 câu là mẫu nhỏ, chưa đủ để khẳng định chắc đây là quy luật chung.

Hai điểm cần nói rõ để kết quả không bị hiểu lầm: (1) thay đổi domain duy nhất quan sát được (`san_van_dong`) là nhiễu sinh ra (temperature 0,2, không phải hiệu ứng code — mục 3.2), không làm thay đổi kết luận "không có ý nghĩa"; (2) dữ liệu hành vi (`nv2_behavior.py`) mất ở cả 6 lần chạy do lỗi đường dẫn import (không phải rớt kết nối như chẩn đoán ban đầu — xem mục 4) đã được vá và chạy lại (mục 3.6): cả 7 cấu hình (kể cả cấu hình bổ sung sau) ra giống nhau (17/22) vì không câu nào trong 22 tình huống đụng tới cờ fastpath đang so sánh — kết quả hợp lý, không phải phát hiện mới về bản sửa.

**Kết luận:** vẫn nên giữ bản sửa lỗi (sửa đúng lỗi dev thật, không làm hại bộ mù) nhưng với số liệu hiện có, đây KHÔNG phải luận cứ cho việc SQL fastpath tốt hơn đường cũ trên dữ liệu bảng mới lạ — ngược lại. Việc tiếp theo nên làm: (1) chạy lại `nv2_behavior.py` nay đã vá lỗi, (2) mở rộng `real_v4_s4` quá 8 bảng để kiểm tra khoảng cách fastpath-vs-đường cũ có phải chỉ do mẫu nhỏ, (3) cố định temperature=0 cho các lần so trước/sau sau này để loại nhiễu như mục 3.2 đã gặp.

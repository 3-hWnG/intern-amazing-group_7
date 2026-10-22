# Minh chứng cho bảng Evaluation Metrics (slide 2: Strict, slide 3: Friendly)

Tài liệu chuẩn bị cho buổi gặp mentor. Mỗi dòng trong hai bảng của slide được truy ngược về: **con số này là gì, đếm trên mẫu nào, file nào chứa kết quả gốc, chạy lại bằng lệnh nào, và mentor có thể hỏi gì.** Viết ngày 2026-10-15, đối chiếu với repo ở commit `ca06c43` (nhánh `merge_sys_3_4`). **Cập nhật 2026-10-22:** thêm số đo trên câu hỏi thật (mục 0b).

## 0. Cách đọc tài liệu này

Mỗi con số có một nhãn mức bằng chứng. Nhãn này quan trọng hơn bản thân con số, vì mentor hay hỏi "file nào chứng minh".

| Nhãn | Nghĩa |
|---|---|
| 🟢 | Có file kết quả gốc trong repo (đã commit), và có lệnh chạy lại được. |
| 🟡 | Số có trong tài liệu `docs/` của nhóm, nhưng **file kết quả thô không nằm trong git**. Chạy lại được (script có sẵn) nhưng chưa có bằng chứng lưu. |
| 🔴 | **Không tìm thấy** file gốc, tài liệu hay lệnh nào cho ra số này trong repo, trên mọi nhánh remote, hoặc trong các phiên làm việc trước. Phải hỏi lại người đo, hoặc đo lại, trước khi nói với mentor. |

Tóm tắt trạng thái các dòng của slide (chi tiết ở mục 3 và 4):

| Slide | 🟢 | 🟡 | 🔴 |
|---|---|---|---|
| Slide 2 (Strict), 8 dòng | 6 (dòng 1–6) | 0 | 0 dòng thuần 🔴, nhưng 2 dòng có phần 🔴: dòng 7 ("có hay không GPU đều vậy") và dòng 8 ("~7 s khi chỉ CPU", phần GPU là 🟡) |
| Slide 3 (Friendly), 11 dòng, **trạng thái ban đầu (sáng 15/10)** | 1 (17/17 từ tài liệu tải lên) | 5 (đúng 92%, không bịa 83%, đếm bảng, chào hỏi, 21/22 tình huống) | 5 (tốc độ GPU, tốc độ CPU, 31/32, tìm web 14/16, tìm web 0/16) |

**Cập nhật chiều 15/10:** đã đo lại bằng `bench.py` và bộ 16 câu Tìm web mới (mục 4b). Kết quả: dòng 1 (đúng), 2 (không bịa), 5 (chào), tốc độ GPU, tốc độ CPU, tìm web đều **đã có file kết quả thô** (🟢, ở `system4/eval/saved_results/2026-10-15/`), nhưng **nhiều số mới khác số trên slide**: đúng 96,2% (slide 92%), hành vi 17/22 (slide 21/22), tốc độ GPU chậm hơn slide, CPU chậm khoảng 3 lần (slide 4–8 lần). Cần sửa slide theo số mới, hoặc giải thích vì sao khác. Chi tiết ở mục 4b.

**Điều cần làm trước buổi gặp (ưu tiên cao nhất):** sửa slide 3 theo mục 4b; hỏi người viết slide nguồn cũ của các số lệch nếu muốn giữ chúng. Với slide 2: dòng 7 và 8 vẫn chưa đo trên máy không GPU (mục 6).

## 0b. Cập nhật 22/10/2026: số đo trên câu hỏi thật (real_v1) và số nên dùng trên slide

Từ 22/10 đã có bộ đo **không do nhóm hoặc AI soạn**: câu hỏi của người dân trên Cổng dịch vụ công (Strict, 300 câu) và câu hỏi thật hoặc do người viết trên Wikipedia (Friendly, 200 câu). Chạy **một lần**, nhãn đã khoá trước khi chạy. Báo cáo một trang: [EVAL_THAT_V1.md](EVAL_THAT_V1.md). Kết quả thô: `eval/saved_results/2026-10-22_real_v1/` và `system4/eval/saved_results/2026-10-22_real_v1/`.

**Quy tắc phân loại cho slide.** Mọi bộ do nhóm hoặc agent soạn (553 câu "mù" snapshot 1.350, bộ khuôn, bài thi Friendly 26 câu, 22 tình huống, bộ 16 câu Tìm web) chuyển thành **"dev / hồi quy"**: dùng để bắt lỗi khi sửa code, không dùng làm số chính. Số chính của slide lấy từ real_v1. Không gọi `pseudo_real` hay `cases_real_log_v1` là "thật".

### Số real_v1 nên đưa vào slide 2 (Strict)

| Dòng slide | Số real_v1 (282 câu, chế độ luật, không GPU, DB bản 3) | Mức bằng chứng |
|---|---|---|
| Có tìm đúng thủ tục không? (top-1 / top-3) | **12,7% (7/55)**, CI 6,3–24,0% / 21,8% (12/55); MRR 0,227 | 🟢 |
| Phản ứng đúng kiểu | **56,0% (158/282)**, CI 50,2–61,7% | 🟢 |
| Hỏi lại đúng (recall) | **1/7** (14,3%); mẫu rất nhỏ | 🟢 |
| Từ chối đúng (recall) | **52,7% (116/220)**, CI 46,1–59,2% | 🟢 |

Cách nói với mentor: "Trên câu hỏi thật của người dân, Strict đạt 56% hành vi đúng và 13% top-1. Thấp hơn nhiều so với bộ nhóm soạn (72–78%), vì câu thật dài, nhiều luật, xử phạt, khiếu nại; hệ thống trả lời thay vì từ chối ở 101/220 câu ngoài phạm vi, và chọn nhầm một thủ tục (`1.115406`) ở 26 câu." Đây là số trung thực, không nên giấu.

### Số real_v1 nên đưa vào slide 3 (Friendly)

| Dòng slide | Số real_v1 (177 câu, `inst02`, GTX 1660 SUPER) | Mức bằng chứng |
|---|---|---|
| Trả lời đúng từ văn bản (Du lịch, 1 bài Wikipedia, 50 câu) | **92,0% (46/50)**, CI 81–97% | 🟢 |
| Trả lời đúng từ bảng (26 câu) | **65,4% (17/26)**, CI 46–81% | 🟢 |
| Từ chối khi dữ liệu không có (14 câu) | **71,4% (10/14)**, CI 45–88% | 🟢 |
| Hỏi lại khi mơ hồ (2 câu) | 0/2 (quá ít câu để kết luận) | 🟡 |
| Y tế (85 câu): khuyên khám | 94,1% (80/85); câu `urgent` khuyên cấp cứu **4/10** | 🟢 |
| Thời gian | câu đầu median 13,0 s, cả câu median 19,4 s, p90 32,4 s (máy 6 GB, GPU chia cho reranker) | 🟢 |

Giới hạn cần nói kèm: nhãn do hai lượt AI gán (κ 0,753 ở Strict); Du lịch văn bản chỉ phủ một bài Wikipedia; 40 câu bảng soạn khi chỉ nhìn tên cột và được người duyệt; Y tế chỉ đo bằng luật chữ.

### Số cũ lệch trên slide và số nên dùng

| Slide | Số cũ trên slide | Số nên dùng | Nguồn | Mục chi tiết |
|---|---|---|---|---|
| 3, dòng 1 | đúng 92% (72/78) | **96,2% (75/78)**, CI 89–99% (cùng bài thi 26 câu, đo lại 15/10); hai số chồng khoảng tin cậy, nói "92–96%" | `system4/eval/saved_results/2026-10-15/inst02.json` | 4b.A |
| 3, dòng 6 | 21/22 tình huống | **17/22** (đo lại 15/10); chưa điều tra 5 ca trượt | `inst02_nv2.json` | 4b.A |
| 3, dòng 7 (GPU) | chữ đầu / cả câu 1,6 / 2,9 s; theo loại câu 1,7–4,7 / 2,4–7,1 s | median 3,8 / 5,3 s (bài thi); theo loại câu 1,1–9,4 / 2,3–11,4 s (chậm hơn slide 1,3–2,3 lần ở mọi loại câu) | `inst02.json` | 4b.B |
| 3, dòng 8 | CPU chậm 4–8 lần | **khoảng 3 lần** (11,9 / 19,9 s; lớn nhất 63 s) | `inst02+cpu.json` | 4b.C |
| 3, dòng 9 | 31/32 so với 32/32 | **25/26 trên cả CPU và GPU** (cùng một câu trượt); chưa có "32 câu" | `inst02+cpu.json` | 4b.C |
| 3, dòng 10 | Tìm web: 14/16 tìm được kết quả | **16/16 có nguồn có URL; 14/16 có `[n]`** (bộ 16 câu do nhóm soạn) | `inst02_web.json` | 4b.D |
| 3, dòng 11 | Tìm web: 0/16 bịa số | **chưa đo** (cần đọc tay); không đưa lên slide | | 4b.D |
| 2, dòng 7 | dưới 0,2 s, có hay không GPU đều vậy | 1 người p95 ~0,19 s; **10 người p95 1,18 s**; máy không GPU **chưa đo** | `load_10users_real.json` | 3, dòng 7 |
| 2, dòng 8 | ~1,5 s (GPU), ~7 s (CPU) | 10 người có GPU: p50 2,9 s / p95 4,0 s; "7 s" là timeout của bước LLM, **không phải số đo**; bỏ hoặc ghi "chưa đo" | `ARCHITECTURE_REVIEW_2026-10-15.md` §5.4 | 3, dòng 8 |
| 2, dòng 1–4 | top-1 73%, hành vi 78%, hỏi lại 47%, từ chối 90% (553 mù, snapshot 1.350) | Trên bản 3 (518 ca mù): top-1 **72%**, hành vi **77%**, hỏi lại **50%**, từ chối 90%; ghi rõ "bộ do nhóm soạn, dùng cho hồi quy" | `docs/KET_QUA_THUC_THI_2026-10-23.md` | 3, dòng 1–4 |
| 2, câu chú thích dòng 5 | số liệu lấy trên 553 câu | mẫu thật của "87% không bịa số" là **92 ca RAGAS-lite**, không phải 553 | `ragas_lite_d2.json` | 3, dòng 5 |

Các số 🟡/🔴 ở mục 3–4 giữ nguyên nhãn cho tới khi có file thô mới.

## 1. Các bộ test và ý nghĩa của "bộ mù"

### 1.1 Ai soạn, soạn thế nào

Các bộ ở mục này đều do nhóm hoặc agent (Claude) soạn; **chưa có chuyên gia pháp lý rà nhãn**. Bộ real_v1 (mục 0b, từ 22/10) dùng câu hỏi thật của người dân (câu hỏi không do nhóm viết), nhưng nhãn của nó vẫn do hai lượt AI gán. Đáp án của bộ Strict là mã thủ tục (`proc_id`) do người soạn gán từ DB, kèm các "giả định" ghi trong `eval/H3_ASSUMPTIONS.md`, `H4_ASSUMPTIONS.md`, `H5_ASSUMPTIONS.md`, `H6_ASSUMPTIONS.md`, `PSEUDO_REAL_ASSUMPTIONS.md`. Đây là điểm yếu số một nếu mentor hỏi "đáp án chuẩn từ đâu ra".

Bộ "log thật" (`eval/cases_real_log_v1.json`) **không phải log thật**: dự án chưa deploy nên chưa có người dùng thật. File `eval/REAL_LOG_v1.md` ghi rõ điều này; đó là 29 câu viết tay theo văn phong người dân.

### 1.2 553 câu "mù" của slide 2 gồm những bộ nào

Số 553 là tổng các bộ có `status=blind` trong golden set (`eval/golden/thu-tuc.jsonl`, dựng bằng `eval/build_golden.py`). Thành phần (số liệu từ `eval/saved_results/2026-10-14/report.md`, bảng B):

| Bộ | Số ca | Ghi chú về tính "mù" |
|---|---|---|
| `cases_h3.jsonl` (HOLDOUT-3) | 88 | Soạn mù; chạy lại sau đợt 4, chỉ xem số tổng, không vá theo câu |
| `cases_h4.json` (HOLDOUT-4) | 106 | **Bộ mù chính thức** theo `docs/EVAL.md`; agent soạn không thấy mã |
| `cases_h5.json` | 111 | Giả định ở `H5_ASSUMPTIONS.md` (cùng đợt với pseudo_real 3) |
| `cases_h6.json` | 126 | Giả định ở `H6_ASSUMPTIONS.md` |
| `cases_pseudo_real.json` | 42 | **Đã bị xem lỗi** (`docs/EVAL.md`: "không tune", nhưng không còn mù tuyệt đối) |
| `cases_pseudo_real2.json` | 34 | Mù, kiểu người dân gõ đời thường |
| `cases_pseudo_real3.json` | 36 | Chưa xem lỗi |
| `cases_team.json` | 10 | Bộ test chung của các nhóm; chấm luật |
| **Tổng** | **553** | 88+106+111+126+42+34+36+10 |

Hai điều mentor có thể bắt:
1. Theo `docs/EVAL.md`, bộ mù **chính thức** là HOLDOUT-4 và pseudo_real 2 (ghi chú nội bộ của nhóm tính thêm HOLDOUT-3). Gộp thêm h5, h6, pseudo_real 1 và 3, team thành "553" là cách gộp của `run_golden.py`, không phải định nghĩa chính thức trong `docs/EVAL.md`. Nếu bị hỏi, nói thẳng: "553 là tổng các bộ chưa dùng để tune; riêng HOLDOUT-4 là 78% top-1".
2. Số `blind` gộp cho top-1 là 73% (68–77%), còn HOLDOUT-4 một mình là 78% (67–86%). Hai khoảng tin cậy chồng nhau nhiều nên không có khác biệt đáng kể.

### 1.3 Vì sao slide nói "dev ~98% nhưng không dùng số đó"

Bộ `dev` (641 ca) là bộ nhóm đã dùng để chỉnh hệ thống, nên điểm cao là tự nhiên. Số dev chỉ để bắt hồi quy. Lý do có quy tắc này: lần đầu nhóm báo DEV 90% nhưng bộ mù chỉ ~73% (ghi trong ghi chú vệ sinh đo). Nguồn: `eval/saved_results/2026-10-14/report.md`, bảng A, hàng `dev`: hành vi 626/641 (98%, CI 96–99%), top-1 558/567 (98%).

## 2. Cách tính một số khái niệm (mentor thường hỏi sâu chỗ này)

| Khái niệm | Định nghĩa trong code | Nơi xem |
|---|---|---|
| **Hành vi đúng** | So `behavior` hệ thống trả ra với `expected.behavior` của ca: một trong `answer` (trả lời), `clarify` (hỏi lại), `apologize` (từ chối, xin lỗi). Mẫu số = **mọi ca** (553). | `eval/run_golden.py`, trường `beh_ok` trong vòng lặp `for c in cases` |
| **top-1 / top-3** | Chỉ tính ca `expected.behavior == answer` và có đáp án `proc_id` (406 ca, không phải 553). top-1: thủ tục đầu tiên hệ thống chọn nằm trong tập đáp án chấp nhận. top-3: một trong 3 ứng viên đầu nằm trong tập đó. | `run_golden.py`, trường `scored`, `top1`, `top3` |
| **MRR** | Trung bình của 1/hạng của thủ tục đúng trong danh sách ứng viên. Đúng ở hạng 1 → 1; hạng 2 → 0,5; không có → 0. Ca nhiều thủ tục: tính từng ý rồi lấy trung bình. | `eval/rank_metrics.py`, `run_golden.py` hàm `rank_of` |
| **nDCG@5** | Như MRR nhưng cộng điểm cho nhiều đáp án đúng trong 5 hạng đầu, chiết khấu theo hạng. | `eval/rank_metrics.py` |
| **Hỏi lại đúng (47%)** | **Recall của hành vi hỏi lại:** trong các ca mà đáp án là `clarify` (86 ca), tỷ lệ hệ thống thật sự hỏi lại (40/86). Không đo chuyện hệ thống hỏi lại thừa. | `run_golden.py`, hàm `table` (cột "hỏi lại đúng", `cl`) |
| **Từ chối đúng (90%)** | **Recall của hành vi từ chối:** trong các ca đáp án là `apologize` (58 ca: ngoài phạm vi, chèn lệnh, không có thủ tục), tỷ lệ hệ thống từ chối (52/58). | `run_golden.py`, hàm `table` (cột "từ chối đúng", `ap`) |
| **Bịa số (87% khớp)** | Luật, không dùng LLM: mọi số đi kèm đơn vị tiền, ngày, giờ, tháng trong câu trả lời phải xuất hiện trong ngữ cảnh đưa cho hệ thống. Không xét năm, số văn bản, mã thủ tục. | `eval/run_ragas_lite.py`, hàm `numbers_ok` |
| **Khoảng tin cậy Wilson 95%** | Khoảng chứa tỷ lệ thật với độ tin 95%, tốt hơn khoảng thường cho mẫu nhỏ hoặc tỷ lệ gần 0/100%. | `run_golden.py`, hàm `wilson` |
| **Friendly "đúng"** | Kiểm chuỗi, không dùng AI chấm: câu trả lời phải chứa các cụm trong `all`, ít nhất một cụm trong `any`, không chứa cụm `none`, không khớp `no_regex` (số điện thoại, email, giá, URL, năm...), và với câu ngoài dữ liệu phải nói "không có/không biết". Bỏ dấu và hoa thường khi so. | `system4/eval/bench.py` hàm `score` (dòng 58) |
| **Friendly "không bịa"** | Nhóm câu `halluc` trong `system4/eval/bench_cases.py`: hỏi về thứ không có trong dữ liệu (hotline, email, địa chỉ, giám đốc, giá, địa danh giả) hoặc kiến thức chung kiểm được (sông Hồng, nước lớn nhất). | `bench_cases.py` dòng 75–89 |
| **Friendly "tốc độ chữ đầu / cả câu"** | Thời gian đến token đầu tiên hiện ra, và đến khi xong, đo qua server riêng cổng 8399. | `bench.py` (trường `final_first_s`, `total_s`) |

## 3. Slide 2: Evaluation Metrics (Strict), từng dòng

Cách chạy lại chung cho các dòng Strict (Git Bash, từ `D:\merged_sys3_4\merged`):

```bash
PYTHONIOENCODING=utf-8 S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 .venv/Scripts/python.exe run_server.py eval/run_golden.py thu-tuc --by status
.venv/Scripts/python.exe eval/report.py     # một lệnh cho các bảng A–D, ~2 phút, ghi eval/results/report.md
```

Bản kết quả đã lưu trong git: `eval/saved_results/2026-10-14/report.md` (🟢). Thư mục `eval/results/` bị `.gitignore`, nên bản chạy cục bộ không lên git; chỉ bản trong `eval/saved_results/` được lưu.

### Dòng 1: "Có tìm đúng thủ tục không?" Kết quả: 73% top-1, 80% trong 3 đầu. 🟢

- **Số gốc:** top-1 295/406 (73%, CI 68–77%); top-3 323/406 (80%, CI 75–83%); MRR 0,759; nDCG@5 0,752.
- **Mẫu số 406**, không phải 553: chỉ ca đáp án là `answer` và có `proc_id`.
- **Bằng chứng:** `eval/saved_results/2026-10-14/report.md`, bảng A, hàng `blind`. Số cùng bộ trong `eval/CRITERIA.md` tầng A, và `docs/PLAN_TUAN_TOI.md` bảng A.
- **Điểm cần nói trước:** lỗi chính là chọn nhầm thủ tục "anh em" cùng họ (ví dụ các loại mai táng phí). Câu trả lời vẫn đúng số liệu, nhưng là số của thủ tục khác. Khi câu hỏi nêu rõ tên thủ tục (bộ khuôn, `eval/results/golden_template_thu-tuc.json`, bảng C của PLAN_TUAN_TOI), top-1 đạt 95–100%. Bộ mù thấp hơn 20–25 điểm, giả thuyết là do câu người dân gõ (viết tắt, không dấu, kể hoàn cảnh), **chưa kiểm chứng** vì xem lỗi bộ mù sẽ làm nó hết mù.
- **Mentor có thể hỏi:** "73% có tốt không?" Trả lời: khung tham chiếu duy nhất trong tài liệu là bài số 02 (RAG pháp luật tiếng Việt, MRR 0,783), khác bài toán và dữ liệu nên chỉ là điểm tham chiếu, không phải chuẩn. MRR của nhóm trên HOLDOUT-4 là 0,824.

### Dòng 2: "Có phản ứng đúng kiểu không (trả lời, hỏi lại hay từ chối)?" Kết quả: 78%. 🟢

- **Số gốc:** 431/553 (78%, CI 74–81%).
- **Bằng chứng:** cùng bảng A, cột "hành vi đúng". Bộ dev cùng cột: 626/641 (98%).
- **Nói rõ:** đây là độ chính xác **gộp** của ba hành vi; hai dòng sau tách riêng recall của hỏi lại và từ chối.

### Dòng 3: "Gặp câu mơ hồ thì có hỏi lại thay vì đoán không?" Kết quả: 47%, điểm yếu nhất. 🟢

- **Số gốc:** 40/86 (47%, CI 36–57%). So với dev: 23/26 (88%).
- **Đây là recall:** trong 86 ca mà đáp án đúng là "hỏi lại", hệ thống chỉ hỏi lại 40 ca; 46 ca còn lại nó đoán hoặc trả lời luôn. Không đo việc hỏi lại thừa.
- **Bằng chứng:** `report.md` bảng A, cột "hỏi lại đúng". Các bộ chuyên biệt `eval/cases_p30.jsonl`, `cases_p31.jsonl` (`eval/P30_REPORT.md`, `P31_REPORT.md`) đo riêng và cải thiện, nhưng chúng tự soạn từ DB và dễ hơn câu thật.
- **Điểm yếu cần chủ động nói:** nhóm đã sửa 2 nguyên nhân gốc, bộ tự soạn tăng từ 14/27 lên 20/27, **nhưng chưa đo lại trên bộ mù** (cố ý, vì không tune trên bộ mù). Hai nhóm lỗi còn lại: câu chỉ có chữ chung ("giải quyết", "học bổng"), và câu không có chữ nghiệp vụ ("làm giấy tờ cho con"); chúng đang bị xin lỗi thay vì được hỏi lại. Dòng này có trong slide 7 phần A.

### Dòng 4: "Gặp câu ngoài phạm vi thì có từ chối không?" Kết quả: 90%. 🟢

- **Số gốc:** 52/58 (90%, CI 79–95%).
- **Bằng chứng:** `report.md` bảng A, cột "từ chối đúng".
- **Lưu ý mẫu nhỏ:** 58 ca; khoảng tin cậy 79–95% là khoảng rộng. Có hai chiều sai: từ chối thừa (thủ tục có trong kho mà bị từ chối) cũng làm tụt "hành vi đúng" nhưng không nằm trong chỉ số này.

### Dòng 5: "Có bịa số liệu (phí, thời hạn) không?" Kết quả: 87% câu trả lời có mọi con số khớp. 🟢 với điều kiện đọc đúng mẫu

- **Số gốc:** `num_ok` = 80/92 (87%, CI 79–92%) trong `eval/saved_results/2026-10-14/ragas_lite_d2.json` (`summary.all.num_ok` = 0,8696).
- **Mẫu KHÔNG phải 553 câu.** Slide gắn dòng này dưới câu "Số liệu lấy trên 553 câu hỏi mù" nhưng đây là mẫu 92 ca của RAGAS-lite: 35 ca cần bước LLM sinh chữ (composer), 34 ca từ bộ khuôn, 23 ca lấy từ bộ mù. Cần sửa câu chú thích của slide, hoặc nói rõ khi trình bày.
- **Luật kiểm:** `numbers_ok` chỉ xét số kèm đơn vị tiền/ngày/giờ/tháng; bỏ qua năm, số văn bản, mã thủ tục (vì chúng nằm ở phần căn cứ pháp lý, không nằm trong ngữ cảnh trường đã chọn nên cho âm tính giả). Vì vậy **12/92 ca "không khớp" không có nghĩa là 13% ca bịa**: một phần là ngữ cảnh giám khảo không trùng đúng ngữ cảnh Answerer đã dùng (ghi ở `docs/KE_HOACH_GIAI_QUYET_MERGE_PLAN.md` mục 7, ca `pr-21`), một phần là dữ liệu tự mâu thuẫn (ca `p18-p18_B_single-12`: 5.000 so với 7.000 đồng).
- **Một số bằng chứng khác cho "không bịa" trên bộ lớn hơn:** `eval/run.py` đo bịa số trên bộ DEV: 1/204 (0,5%) theo `eval/CRITERIA.md` tầng B. Đó là bộ dev (đã tune), nên chỉ là chỉ báo hồi quy.
- **Không nên nói:** "0% bịa trên 394 ca là bằng chứng không bịa" (nằm trong danh sách "không nói" của `docs/TOM_TAT_EVAL_CHO_MENTOR.md`).

### Dòng 6: "Có che CCCD/số điện thoại và chặn câu cố ý lừa hệ thống không?" Kết quả: đạt 100% các phép thử, không chặn nhầm. 🟢

- **Số gốc** (`eval/saved_results/2026-10-14/safety_20261014_174352.json`, chạy bằng `eval/safety/test_pii_injection.py`):
  - D1 che CCCD/SĐT viết liền: 9/9. Có dấu cách, gạch, chấm: 3/3 (trước khi sửa: **0/3**).
  - D1 che nhầm câu không có PII: 0/5.
  - D2 chặn chèn lệnh: 11/11; chặn nhầm câu thường: 0/6.
  - D2 hành vi đầu-cuối của hệ thống thật: 17/17.
- **Câu chuyện nên kể:** bộ test tự tìm ra lỗi thật. Trước ngày 14/10, `mask_pii` bỏ sót hoàn toàn khi người dân gõ có dấu cách hoặc gạch (0/3, số có thể lọt vào log nguyên văn). Đã sửa ở `server/policy/policy.py` (commit `90e2dc4`) và thêm test hồi quy. Đây là minh chứng bộ evaluation có tác dụng.
- **Giới hạn thật thà:**
  - "100%" là trên **12 ca che PII và 11 ca chèn lệnh, do nhóm soạn**. Khoảng tin cậy Wilson cho 11/11 là khoảng 74–100%, cho 3/3 là 44–100%. Nói "đạt 100% các phép thử đã soạn", không nói "an toàn 100%".
  - Chỉ thử **chèn lệnh trực tiếp** (người dùng gõ vào ô chat). Chèn lệnh gián tiếp qua tài liệu người dùng tải lên ở System 4 chưa thử (bài báo 06, Greshake et al., là cơ sở).
  - Rủi ro chấp nhận: số 9–12 chữ số không kèm đơn vị tiền vẫn bị che (ví dụ `quyết định số 123456789` thành `[ID]`).
  - Phạm vi che hiện chỉ trong trace, log kiểm tra và tiêu đề hội thoại; nội dung tin nhắn trong DB vẫn lưu nguyên văn (slide 7 mục D). Từ 15/10, log 👍/👎 (`feedback_log`) đã được che.

### Dòng 7: "Câu hỏi code hỗ trợ trả lời mất bao lâu?" Kết quả: dưới 0,2 giây, có hay không GPU đều vậy. 🟢 cho "dưới 0,2 giây", 🔴 cho "có hay không GPU đều vậy"

- **Số gốc** (`eval/results/latency_d1_llm0.json`, đo bằng `eval/measure_latency.py`, bảng D trong `docs/PLAN_TUAN_TOI.md`): p50 / p95 với LLM tắt: câu đơn giản 82 / 122 ms, phức tạp 63 / 122 ms, hỏi lại 85 / 105 ms, ngoài phạm vi 57 / 113 ms.
- **"Dưới 0,2 giây" là p95 ≤ 122 ms**, đúng với dữ liệu trên.
- **"Có hay không GPU đều vậy" chưa được đo.** Cột "LLM tắt (CPU)" là **cùng máy có GPU** nhưng không gọi LLM. `eval/CRITERIA.md` mục 5 ghi rõ "chưa đo máy không GPU hay Planner LLM". Lý do nó có thể đúng: Strict bằng luật và FTS5, không dùng GPU ở các bước này. Nhưng đó là suy luận, không phải số đo. Nên đổi câu trên slide thành "chưa đo trên máy không GPU; phần luật không dùng GPU nên dự kiến không đổi".
- **p95 dao động mạnh giữa các lần chạy** vì mẫu nhỏ (26–40 câu mỗi loại): chạy lại cùng ngày ra p95 "đơn giản" 544 ms (`latency_report_llm0.json`). Tin p50 hơn p95. Với LLM bật, p95 câu phức tạp có lần ra 1,6 s, có lần 3,6 s (`latency_report_llm1.json`).

### Dòng 8: "Câu AI viết câu trả lời thuần mất bao lâu?" Kết quả: ~1,5 s có GPU, ~7 s chỉ CPU. 🟡 cho GPU, 🔴 cho CPU

- **Số có trong repo, có GPU:**
  - Bước sinh chữ bằng LLM: p50 **3,2 s**, p95 **6,3 s** (`docs/PLAN_TUAN_TOI.md` bảng D, `eval/CRITERIA.md` mục 4).
  - Lượt gọi LLM riêng lẻ: p50 1,8 s, p95 3,1 s; qua `/chat`: p50 1,9 s, p95 3,4 s (`docs/EVAL.md` mục "Đo bước sinh chữ", file `eval/results/p27_e2e_run3.json`).
  - Số "1,5 giây" của slide gần với 1,8–1,9 s của lượt gọi LLM, nhưng **không trùng** với 3,2 s ở slide 8 và trong PLAN_TUAN_TOI. Hai chỗ trong cùng một bài thuyết trình đang dùng hai số khác nhau cho cùng một việc. Mentor nhìn slide 2 và slide 8 sẽ hỏi ngay.
- **"~7 giây khi chỉ CPU": không tìm thấy phép đo nào.** Trong repo con số 7 giây xuất hiện ở đúng một nơi khác: **timeout của bước LLM** (`ANSWER_LLM_TIMEOUT = 7 s`, `docs/ARCHITECTURE.md` dòng 30–35). Rất có thể có nhầm lẫn giữa timeout và thời gian đo. Nên xác minh với người đã viết dòng này, hoặc bỏ.
- **Khuyến nghị:** thống nhất slide 2 với slide 8 (3,2 s / 6,3 s, có GPU); bỏ số CPU hoặc ghi "chưa đo".

### Phần ghi chú cuối slide 2

- "Số liệu lấy trên 553 câu hỏi 'mù'... dev khoảng 98%" 🟢: xem mục 1.2 và 1.3.
- "Chưa có điểm chất lượng câu trả lời do AI chấm vì giám khảo AI chưa đủ tin cậy (chỉ phát hiện khoảng một nửa số ý bịa cài sẵn)" 🟢, xem mục 5 bên dưới.

## 4. Slide 3: Evaluation Metrics (Friendly), từng dòng

**Cảnh báo chung trước khi vào từng dòng:** `docs/SYSTEM4_SU_THAT.md` mục 5 ghi rõ kết quả thô của bộ đo Friendly (`system4/eval/results/bench/`) **không được đưa lên git**; số chỉ nằm trong `docs/SYSTEM4_NV5_TOC_DO_CHINH_XAC.md`. Repo chỉ chứa `system4/eval/results/nv2_behavior.json`, `nv2_behavior_before_fast.json`, `nv3_specialist.json`. Vì vậy phần lớn dòng Friendly là 🟡 hoặc 🔴.

**Bộ đo Friendly:** `system4/eval/bench.py` + `bench_cases.py` (65 câu: 39 dev, 26 exam) + 22 tình huống hành vi của `nv2_behavior.py`. Dữ liệu: danh sách lớp **giả** (`system4/eval/data/ds_lop_gia.xlsx`; bản thật có tên trẻ em nên không đưa lên GitHub), chính sách Word, du lịch, và thủ tục mẫu. Chấm bằng luật, không dùng AI chấm. "Exam" là phần không xem khi chỉnh; mỗi câu chạy 3 lần. Câu hỏi do Claude soạn, chưa phải câu hỏi thật.

Cách chạy lại (cần Ollama chạy và GPU; tên cấu hình phải **bằng** `inst02` hoặc dạng `inst02+ghi_chu`, tên như `inst02_final` làm script dừng; cấu hình mặc định hiện tại trong `system4/server/config.py` đã là cấu hình thắng):

```bash
.venv/Scripts/python.exe system4/eval/bench.py run inst02 --split exam --repeat 3
.venv/Scripts/python.exe system4/eval/bench.py compare system4/eval/results/bench/inst02.json
```

**Đính chính (15/10):** bản đầu tài liệu này viết exam có 26 câu (14 accuracy + 6 halluc + 6 chào). Đếm lại từ file kết quả: exam có **32 câu**: 20 accuracy + 6 halluc + 6 chào, mỗi câu 3 lần = 96 lượt. Mẫu số "accuracy + không bịa" là 26 câu × 3 = **78 lượt**, nên 92,3% = 72/78 là khớp và không cần giả thiết chào hỏi nằm trong mẫu số. Suy luận "54/60 = 90,0%" ở bản đầu là sai và đã được gỡ khỏi dòng 1.

### Dòng 1: "Có trả lời đúng không?" Kết quả: 92% đúng. 🟢 sau khi đo lại 15/10 (số mới 96,2%)

- **Nguồn:** `docs/SYSTEM4_NV5_TOC_DO_CHINH_XAC.md` phần D5 (bài thi cuối, 3 lần mỗi câu): đúng 92,3% (trước đó, cấu hình cũ: 73,1%).
- **Mẫu số đã xác nhận (15/10):** 92,3% = 72/78 là 26 câu (20 accuracy + 6 không bịa) × 3 lần; 6 câu chào tính riêng. Bản đầu tài liệu này suy luận sai mẫu số (xem "Đính chính" ở trên).
- **Đo lại 15/10: 75/78 = 96,2% (CI 89–99%)**, cao hơn số slide 3 lượt. Khoảng tin cậy của 72/78 là 84–96%, nên hai số chồng nhau: chênh lệch này nằm trong dao động ngẫu nhiên, không chứng minh hệ thống tốt lên. Nếu nói với mentor, dùng "khoảng 92–96%". Mục 4b.
- Nên sửa tiêu đề dòng này thành 🟢 (có file thô `system4/eval/saved_results/2026-10-15/inst02.json`), nhưng nhớ số trên slide là số cũ.
- **Điểm yếu đã biết của dòng:** exam chỉ có 26 câu trên dữ liệu giả; nhiều câu "đúng" ở nhóm accuracy chỉ cần chứa một cụm chữ (`any=[...]`). Hai câu kiến thức chung (Úc, nước lớn nhất) phụ thuộc model 4B và dao động giữa các lần chạy.

### Dòng 2: "Gặp câu dụ bịa có bịa không?" Kết quả: 83% không bịa. 🟡

- **Nguồn:** D5, nhóm `halluc` trong exam: 6 câu × 3 lần = 18 lượt; 83,3% = **15/18** (CI 61–94%). Cấu hình cũ: 55,6% = 10/18.
- **Khớp số học:** 15/18 ra đúng 83,3% và ba lượt trượt tương ứng "nước lớn nhất thế giới → Việt Nam (0/3)" trong ghi chú D5. Đây là dòng khớp nhất.
- **6 câu exam** (`bench_cases.py` dòng 84–89): website Team 7, giám đốc Team 7, giá gói dịch vụ, chùa Vân Khuyết Sơn (không có thật), sông lớn qua Hà Nội, nước diện tích lớn nhất.
- **Giới hạn:** chỉ 6 câu; một câu sai 3 lần đã làm tụt 17 điểm %. Khoảng tin cậy 61–94% là rất rộng. Hai trong sáu câu là kiến thức chung chứ không phải dụ bịa thuần. Slide 7 (mục C) nói rõ 83% là số có kèm lỗi kiến thức chung (thủ đô Úc là "Sydney" xuất hiện ở bộ dev).

### Dòng 3: "Trả lời từ tài liệu tải lên (Excel, Word) có đúng và dẫn đúng nguồn không?" Kết quả: 17/17. 🟢

- **Số gốc:** `system4/eval/results/nv3_specialist.json`: `answer_ok = 17`, `source_ok = 17`, `total = 17`. Chạy bằng `python system4/eval/nv3_specialist.py http://127.0.0.1:8399`.
- **Cấu thành 17 câu** (`docs/SYSTEM4_NV3_DATASET.md` dòng 88): 12 câu cơ quan/thời hạn từ Excel (`MAU_100_THU_TUC.xlsx`, 2.334 bản ghi), 3 câu từ Word, 2 câu ngoài dữ liệu (phải trả "không có trong dữ liệu").
- **Câu hỏi sinh tự động từ chính dữ liệu**, đáp án là giá trị trong ô. Vì vậy đây là câu dễ: hỏi đúng tên thủ tục đầy đủ và đáp án nằm nguyên văn. Khoảng tin cậy Wilson của 17/17 là **82–100%**.
- **Không đo tốc độ trong dòng này.** Slide gộp tốc độ ở dòng riêng.
- **Một bất tiện nhỏ:** script đọc Excel từ đường dẫn cứng `D:/Claude/LLM for Procedures V10.3/Database/MAU_100_THU_TUC.xlsx`; muốn chạy lại trên máy khác phải sửa dòng này sang `system4/eval/data/MAU_100_THU_TUC.xlsx`.

### Dòng 4: "Đếm hoặc liệt kê trong bảng có đúng không?" Kết quả: 100% (trước cải tiến 0%). 🟡

- **Nguồn:** D5, dòng "câu đếm / liệt kê cả bảng (công cụ bảng)": 0% → 100% đúng, 4,9 s. Cải tiến nhờ công cụ bảng `system4/server/tabletool.py` (`TABLE_TOOL`).
- **Mẫu rất nhỏ:** exam chỉ có **3 câu** loại này (`cls-count-boys`, `cls-list-2019`, `cls-count-tanhoa`), mỗi câu chạy 3 lần = 9 lượt. 9/9 có khoảng tin cậy 70–100%. Bộ dev có thêm `cls-count-girls`, `cls-count-2019`, `cls-list-phuthanh`, nhưng đó là bộ đã tune.
- **Bản chất của "100%":** công cụ bảng tính bằng code (đếm, lọc cột), không phải AI tự đếm, nên kết quả ổn định. Lý do nó là một cải tiến thật, không phải may mắn của mẫu nhỏ. Nên giải thích như vậy.

### Dòng 5: "Có chào hỏi tự nhiên, không lạc sang tra cứu không?" Kết quả: 100%. 🟡

- **Nguồn:** D5, "Câu chào khi bật dữ liệu": 50% → **100%**. Bộ đo: nhóm `greeting` exam, 6 câu × 3 lần = 18 lượt (18/18, CI 82–100%).
- **6 câu:** "Xin chào!", "cam on nha", "bye bye", "Hôm nay bạn thế nào?", "Cảm ơn nhé, còn hạng Kim cương được ưu đãi gì?", "Đổi trả mấy ngày?" (`bench_cases.py` dòng 103–108). Hai câu cuối kiểm xem câu chào kèm câu hỏi thật vẫn được trả lời đúng.
- **Cơ chế:** `GREETING_MODE = code_first` (`system4/server/greet.py`): tin ≤ 4 chữ chứa từ chào thì code bỏ qua tìm kiếm. Chọn sau khi so 3 cách (D3, D4).

### Dòng 6: "22 tình huống hành vi (nhớ ngữ cảnh, hỏi lại khi trùng tên, trả lời nhanh...)" Kết quả: 21/22. 🟡 (số trong slide); 🟢 cho bản cũ 22/22

- **Nguồn của 21/22:** D5 bảng "Hành vi (22 tình huống)": 22/22 cấu hình cũ, **21/22** cấu hình mới. Lỗi ghi ở D4: câu "Team 7 là ai?" trả lời "đội ngũ hỗ trợ khách hàng của tôi" (không xưng "chúng tôi/mình"), một lỗi câu chữ lúc có lúc không.
- **File có trong git lại ghi 22/22:** `system4/eval/results/nv2_behavior.json` có `passed: 22, total: 22`, nhưng đây là **lần chạy cũ hơn** (chữ đầu 0,96 s, trước các thay đổi cuối của NV5). File này không phải bản chạy dẫn đến "21/22". Nếu mentor mở file, họ thấy 22/22, nên cần giải thích hai số là hai thời điểm.
- **22 tình huống do Claude viết** (`system4/eval/nv2_behavior.py`), chấm luật. Chưa có người ngoài kiểm.

### Dòng 7: "Tốc độ, có GPU: chữ đầu tiên / cả câu" 🔴 (nguồn cũ không tìm thấy; đo lại 15/10 cho số khác, xem mục 4b.B)

- **Slide ghi:** chào hỏi 1,7 / 2,4 s; hỏi từ tài liệu 2,7 / 4,4 s; đếm bảng 4,7 / 7,1 s; tra thủ tục trong tài liệu lớn (2.334 dòng) 4,1 / 6,3 s.
- **Số có trong repo không khớp:**
  - D5 (bài thi cuối, GPU): chat thường 1,4 s cả câu; chào 1,3 s; câu có dữ liệu 3,6 s; đếm bảng 4,9 s; p90 4,9 s; chữ đầu / cả câu trung vị mọi câu 1,6 / 2,9 s. Đó là "cả câu", không phải cặp chữ đầu / cả câu theo từng loại như slide.
  - `nv3_specialist.json` (tài liệu lớn): chữ đầu trung vị 3,56 s, cả câu 5,70 s; tối đa 6,27 s và 8,94 s.
  - Không có file nào cho ra đúng bộ số "1,7/2,4 · 2,7/4,4 · 4,7/7,1 · 4,1/6,3".
- **Kết luận:** không tìm thấy nguồn. Có thể đo ở một phiên trước mà không lưu, hoặc do thành viên khác đo trên máy khác. **Hỏi lại người đo, hoặc đo lại.**

### Dòng 8: "Tốc độ, chỉ CPU: chữ đầu tiên / cả câu" và dòng 9: "Không có GPU thì có trả lời sai hơn không? 31/32 so với 32/32" 🔴 (nguồn cũ không tìm thấy; đo lại 15/10 bằng CPU thật, xem mục 4b.C)

- **Slide ghi:** CPU chậm gấp 4–8 lần (7,6 / 11 s; 12 / 19 s; 22 / 39 s; 39 / 52 s); chất lượng gần như không đổi (31/32 so với 32/32 khi có GPU).
- **Không tìm thấy:** không file kết quả nào, không dòng trong `docs/`, không commit nào trên mọi nhánh remote chứa số 31/32 hay các cặp số tốc độ CPU. `eval/CRITERIA.md` mục 5 (hạn chế) vẫn ghi "chưa đo máy không GPU", và `docs/TOM_TAT_EVAL_CHO_MENTOR.md` ghi "chưa đo máy không GPU và Planner bằng LLM". Hai tài liệu của nhóm mâu thuẫn trực tiếp với slide.
- **Bộ đo hiện không có tuỳ chọn tắt GPU:** `bench.py` không có cờ `--cpu` hay `num_gpu=0` (đã tìm). Một phép đo CPU phải đặt `CUDA_VISIBLE_DEVICES=-1` hoặc `OLLAMA_NUM_GPU=0` cho Ollama rồi chạy lại cùng bộ câu.
- **32 câu** ở "31/32" cũng không khớp với bộ exam hiện tại (26 câu).
- **Khuyến nghị mạnh:** nếu không xác minh được nguồn, **gỡ ba dòng này khỏi slide** hoặc ghi "ước tính, chưa đo". Nếu mentor hỏi "đo ở đâu", câu trả lời hiện tại là "chưa có file".

### Dòng 10 và 11: "Tìm web: có tìm được kết quả và ghi nguồn không? (14/16)" và "Tìm web: có bịa số liệu không? (0/16)" 🔴 (nguồn cũ không tìm thấy; bộ 16 câu mới ở mục 4b.D)

- **Slide ghi:** 14/16 lượt tìm được kết quả, mọi câu tìm được đều có nguồn kèm; 0/16 lượt bịa số, khi tìm không ra thì nói thật là không có thông tin.
- **Không tìm thấy nguồn cho "16 lượt".** Các bằng chứng có liên quan trong repo:
  - `system4/tests/test_websearch.py`: kiểm hành vi bằng **DuckDuckGo giả** và LLM giả (không mạng): `websearch=true` bỏ qua dataset, nguồn có URL, mất mạng thì báo "không có kết quả" mà không lỗi. Đây là test chức năng, không phải số đo trên mạng thật.
  - `eval/results/websearch_ab.md` / `.json` (từ `eval/run_websearch_ab.py`): so sánh A/B **cho Strict** (Strict thuần so với Strict kèm khối web), chấm tay, 5 nguồn mỗi câu, độ trễ thêm 10–14 s. Không phải Friendly và không có tỷ lệ 14/16.
  - Bộ `bench_cases.py` có câu `hal-web` ("Website chính thức của Team 7"), nhưng đó là câu chống bịa, không bật Tìm web.
- **Khuyến nghị:** như dòng 7–9: hoặc chạy lại một phép đo nhỏ (16 câu, bật nút Tìm web, kiểm có kết quả/nguồn/số trong kết quả), hoặc ghi chú "đo thủ công, chưa lưu".

## 4b. Đo lại ngày 15/10/2026: số mới so với slide 3

**Điều kiện đo:** máy i3-12100F (4 nhân / 8 luồng) + GTX 1660 SUPER 6 GB, Ollama 0.30.11, cấu hình `inst02` (model `qwen3:4b-instruct-2507-q4_K_M`, nhiệt độ 0,2), chạy một lần, không chỉnh gì sau khi xem kết quả. File thô (đã sao vào thư mục theo dõi bằng git, chưa commit): `system4/eval/saved_results/2026-10-15/`.

### A. Bài thi Friendly (`bench.py run inst02 --split exam --repeat 3`, file `inst02.json`, `inst02_nv2.json`)

| Chỉ số | Slide 3 | Đo lại 15/10 | Nhận xét |
|---|---|---|---|
| Đúng (accuracy + không bịa) | 92% (72/78) | **96,2% (75/78)**, CI 89–99% | Mẫu số 78 lượt đã xác nhận. Nhiều hơn 3 lượt đúng so với số cũ. |
| Riêng accuracy | không có | 60/60 (100%), CI 94–100% | |
| Không bịa | 83% | **83,3% (15/18)**, CI 61–94% | Khớp slide. Ba lượt trượt đều là một câu: nước có diện tích lớn nhất thế giới (model đáp không có "Nga"). |
| Chào hỏi | 100% | **100% (18/18)**, CI 82–100% | Khớp slide. |
| 22 tình huống hành vi | 21/22 | **17/22** | **Thấp hơn slide.** 5 ca trượt: xưng hô khi nói về Team 7, ba ca về trí nhớ (tự nhớ tên người dùng, nhớ sở thích, nhớ sang hội thoại mới), một ca hỏi lại điều đã nhớ (thành phố). Chưa điều tra nguyên nhân. Cần xem là lỗi thật của hệ thống hay do cách đo (bộ nhớ trong server bench). |
| Chữ đầu / cả câu, trung vị mọi câu | 1,6 / 2,9 s (D5) | 3,8 / 5,3 s | Chậm hơn khoảng 1,8 lần. |

### B. Tốc độ theo loại câu (cùng lần chạy, GPU)

| Loại câu | Slide 3 (chữ đầu / cả câu) | Đo lại, trung vị (số lượt) | Tối đa cả câu |
|---|---|---|---|
| Chào hỏi | 1,7 / 2,4 s | 2,6 / 3,3 s (18) | 7,2 s |
| Hỏi từ tài liệu (nhóm còn lại) | 2,7 / 4,4 s | 3,7 / 5,6 s (33) | 13,1 s |
| Câu dụ bịa | không có | 1,1 / 2,3 s (18) | 3,5 s |
| Đếm / liệt kê bảng | 4,7 / 7,1 s | 7,4 / 11,2 s (9) | 17,0 s |
| Tra thủ tục trong tài liệu lớn (2.334 dòng) | 4,1 / 6,3 s | 9,4 / 11,4 s (18) | 18,3 s |

Số đo mới **chậm hơn slide ở mọi loại câu** (1,3 đến 2,3 lần), không khớp với bộ số trong slide. Chưa biết vì sao: có thể slide đo ở máy khác, hoặc lúc máy rảnh hơn, hoặc cấu hình khi đó khác. Nếu giữ số trên slide, nên ghi rõ máy và điều kiện. Nếu mentor hỏi, dùng số đo lại.

### C. Chỉ chạy bằng CPU (`inst02+cpu.json`)

Cách làm: tắt Ollama, mở lại với `OLLAMA_LLM_LIBRARY=cpu` (Ollama 0.30 **bỏ qua** `CUDA_VISIBLE_DEVICES=-1` và `OLLAMA_NUM_GPU=0`, vẫn chạy trên GPU; chỉ biến thư viện mới ép được CPU, xác nhận bằng `ollama ps` ghi "100% CPU"). Sau đó chạy `bench.py run inst02+cpu --split exam --suites accuracy,halluc --repeat 1 --no-behavior`. Chỉ 26 câu một lần, **không** có 6 câu chào và không đo 22 tình huống hành vi.

| Chỉ số | Slide 3 | GPU, đúng 26 câu đó (78 lượt) | CPU (26 lượt) |
|---|---|---|---|
| Chữ đầu / cả câu, trung vị | CPU chậm 4–8 lần | 4,2 / 6,5 s | **11,9 / 19,9 s** (gấp khoảng **3 lần**) |
| Cả câu lớn nhất | không có | 18,3 s | **63,0 s** |
| Đúng | 31/32 so với 32/32 | 25/26 ở lượt đầu | **25/26** (cùng một câu trượt: nước lớn nhất, như GPU) |
| Tra thủ tục tài liệu lớn | 39 / 52 s | 9,4 / 11,4 s | 34,4 / 52,1 s (6 lượt) |
| Đếm bảng | 22 / 39 s | 7,4 / 11,2 s | 22,4 / 37,2 s (3 lượt) |
| Hỏi từ tài liệu | 12 / 19 s | 3,7 / 5,6 s | 11,7 / 17,2 s (11 lượt) |

- **Kết luận chính:** chất lượng không đổi (đúng cùng 25/26 câu), tốc độ chậm gần 3 lần (4–5 lần ở câu thủ tục lớn). Các số CPU của slide (12/19, 22/39, 39/52) **gần với số đo lại** ở ba loại câu CPU (11,7/17,2, 22,4/37,2, 34,4/52,1). Nghĩa là số CPU trên slide có vẻ đo trên máy tương tự máy này. Nhưng tỷ lệ "4–8 lần" thì phụ thuộc vào số GPU của slide; so với số GPU đo lại, tỷ lệ là 3–4,6 lần.
- **Giới hạn của phép đo CPU:** một máy duy nhất, một lần chạy, 26 câu. Chỉ "model sinh chữ và reranker chạy CPU"; thành phần khác của server không đổi. Không nên gọi đây là "máy của người dùng cuối".
- **Không đo:** Strict (System 3) bằng CPU.

### D. Tìm web, 16 câu mới (`bench_web.py`, file `inst02_web.json`)

- **Bộ 16 câu** nằm trong `system4/eval/bench_web.py` (hằng `CASES`): 8 câu thay đổi theo ngày (thời tiết, giá vàng, tỷ giá, giá xăng, lương tối thiểu, giá vé tàu, V-League, tin nổi bật) và 8 câu ổn định có từ khoá đáp án (thủ đô Nhật Bản, đỉnh cao nhất, tác giả Truyện Kiều, Hồ Hoàn Kiếm, tuổi làm CCCD, phạt không đội mũ, thời hạn tạm trú, lệ phí hộ chiếu). Gửi với `websearch=true` qua DuckDuckGo thật, chạy một lần. Câu do Claude soạn; từ khoá đáp án 8 câu ổn định do Claude viết và **chưa đối chiếu với nguồn luật** (có thể lệch với văn bản mới nhất).
- **Kết quả tự đo:**
  - Đi qua web: 16/16. Có ít nhất một nguồn có URL: **16/16**. Có ghi `[n]` trong câu trả lời: **14/16**.
  - 8 câu ổn định: trả đúng từ khoá **8/8**.
  - 8 câu thay đổi theo ngày: đạt quy tắc tự đo (có nguồn, có số, không câu từ chối) chỉ **4/8**. Đọc tay: w02 (giá vàng) và w05 (lương tối thiểu) **có trả số** nhưng bị tính trượt vì câu trả lời chứa cụm "chưa được cung cấp"; w07 (V-League) thực sự không có kết quả; w01 (thời tiết) cần xem tay. Quy tắc tự đo ở đây bảo thủ.
  - Tốc độ: chữ đầu 8,4 s, cả câu 12,2 s (trung vị); bước tìm DuckDuckGo 3,9 s.
- **So với slide 3:** "14/16" **trùng** với số lượt có ghi `[n]` (14/16), nhưng chưa chắc đó là cùng chỉ số; slide nói "14/16 tìm được kết quả". Đo lại cho thấy kết quả tìm được ở 16/16. Có thể bộ 16 câu ở slide khác bộ này. **Không lấy 14/16 từ lần đo này làm bằng chứng cho slide**, chỉ nói "đo lại ngày 15/10 trên bộ 16 câu mới: 16/16 có nguồn, 14/16 có `[n]`".
- **"0/16 bịa số":** **chưa đo.** Với câu thay đổi theo ngày không có đáp án chuẩn để so; phải đọc tay `answer` trong `inst02_web.json`. Chưa làm.
- **Lưu ý về A/B của Strict:** `eval/results/websearch_ab.md` / `.json` (12/10, Strict, 26 câu, web trả về 21/26, có nguồn 21, ghi `[n]` 18, 6/17 câu trả lời có số mâu thuẫn Strict, thêm 11,3 s trung vị) là số của **Strict**, nằm ngoài git (`eval/results/*` bị bỏ qua).

## 5. Bằng chứng cho phát biểu "giám khảo AI chưa đủ tin cậy" (cuối slide 2, slide 7 mục B, slide 8)

Phát biểu này nằm ở ba slide và có cả bằng chứng mạnh nhất của nhóm (🟢).

- **Cái được đo:** RAGAS-lite (`eval/run_ragas_lite.py`): bản cài lại 4 chỉ số RAGAS bằng giám khảo `qwen2.5:7b` qua Ollama, **không dùng thư viện `ragas`**. 92 ca (35 composer, 34 khuôn, 23 mù). File kết quả: `eval/saved_results/2026-10-14/ragas_lite_d2.json`; dữ liệu đầu vào `ragas_dataset_d2.json`; log `ragas_score_d2.log`.
- **Phép đối chứng (kiểm chính giám khảo):**
  - Chèn một ý bịa ("miễn phí hoàn toàn, giải quyết trong 1 giờ") vào câu trả lời; faithfulness phải giảm: giám khảo bắt được **47/92 (51%)** (CI 41–61%). Với giám khảo cũ `qwen3:4b` trên 30 ca: 9/30 (30%).
  - Ghép câu trả lời với câu hỏi của ca khác; relevancy phải giảm: 74/76 (97%).
  - Câu trả lời **đúng** mà relevancy bị chấm 0: 16/92.
  - Nguồn các số này: `summary.controls` trong `ragas_lite_d2.json`.
- **κ (Cohen's kappa)** giữa giám khảo và chuẩn LLM (Claude) trên 30 ca: faithfulness **0,02** (17/30 trùng), relevancy **0,20** (24/30). Cả hai thấp hơn xa ngưỡng ~0,6 thường coi là chấp nhận được. File: `ragas_calib_d2.json`, `ragas_calib_llm_d2.json`; chạy bằng `eval/ragas_calib.py`.
- **Điểm yếu của chính phép kiểm, mentor có thể bắt:** "chuẩn" của κ là một LLM (Claude), **không phải người**. Phiếu 15 ca bất đồng cho người chấm đã chuẩn bị (`ragas_calib_human_sheet_d2.md`), chưa điền. Ngoài ra ngữ cảnh đưa cho giám khảo không trùng hoàn toàn với ngữ cảnh Answerer đã dùng (ca `pr-21`), đây là một phần lý do κ thấp; việc sửa (mục C1 trong plan, chấm lại ~2,8 giờ) đã chủ động bỏ qua.
- **Cách nhóm dùng thay thế:** chỉ số luật, không phụ thuộc giám khảo: kiểm số bằng DB và luật (`numbers_ok`, dòng 5 slide 2), đúng trọng tâm (`eval/run_concise.py`), điểm bước sinh chữ (`eval/score_composer.py`: đủ ý, không sai số, không đảo nghĩa, không cơ quan lạ, độ dài; 59/63 đạt cả 5 khi bật LLM, 45/63 khi tắt, `docs/EVAL.md` mục "Đo bước sinh chữ").
- **Nên nói gì nếu bị hỏi "sao không dùng RAGAS":** "Chúng em đã thử, kiểm chính giám khảo, và thấy nó chỉ bắt được một nửa ý bịa cài sẵn. Nên chúng em không báo điểm RAGAS như điểm chất lượng." Đây là một phát hiện, không phải thiếu sót, và slide 8 đã coi nó là một đóng góp tiềm năng của bài báo.

## 6. Việc nên làm trước buổi gặp, theo thứ tự

1. **Hỏi lại người đã viết slide 3** (hoặc người đo): 5 dòng 🔴 (tốc độ GPU, tốc độ CPU, 31/32, tìm web 14/16, 0/16) lấy từ đâu, file nằm ở đâu. Nếu tìm lại được file thì commit vào `system4/eval/saved_results/` hoặc `eval/saved_results/`.
2. **(Đã làm 15/10)** Chạy lại bài thi Friendly, đo CPU, và viết bộ 16 câu Tìm web: mục 4b. Còn lại: điều tra 5 ca hành vi trượt (17/22), đọc tay câu trả lời Tìm web để chấm "0/16 bịa số", và đo CPU cho Strict.
3. **Sửa các chỗ lệch giữa các slide:**
   - Slide 2 dòng 8 ("1,5 s / 7 s") so với slide 8 ("3,2 s / 6,3 s"): chọn một và dùng 3,2 s / 6,3 s (có file).
   - Câu chú thích "553 câu hỏi mù" cho dòng "87%": mẫu thật là 92 ca.
   - Slide 2 dòng 7 ("có hay không GPU đều vậy"): đổi thành "chưa đo trên máy không GPU".
   - Slide 3: sửa 92% → số đo lại (96,2%), 21/22 → 17/22 hoặc điều tra rồi đo lại, tốc độ GPU theo bảng 4B, "CPU chậm 4–8 lần" → khoảng 3 lần, 14/16 Tìm web → ghi rõ là "có `[n]`".
4. **Nếu có thời gian:** đo CPU cho Strict có LLM (Friendly đã đo, mục 4b.C). Lưu ý Ollama 0.30 chỉ chịu `OLLAMA_LLM_LIBRARY=cpu`, không chịu `CUDA_VISIBLE_DEVICES`.
5. **Nên tự nói trước, đừng để bị hỏi:** (a) tất cả đáp án do nhóm và agent soạn, chưa có người ngoài kiểm; (b) bộ mù gồm cả các bộ đã bị xem lỗi một phần; (c) hỏi lại 47% là điểm yếu số một và chưa đo lại sau khi sửa; (d) giám khảo AI không đủ tin cậy nên không báo điểm RAGAS.

## 7. Câu mentor có thể hỏi và gợi ý trả lời

| Câu hỏi | Gợi ý (chỉ nói điều có bằng chứng) |
|---|---|
| "Bộ mù là gì, tại sao tin được?" | Bộ chưa dùng để chỉnh hệ thống; agent soạn không thấy mã; nhóm không đọc lỗi từng câu. Số dev ~98% cao hơn nhiều (mù 73–78%), nên chỉ báo số mù. Giới hạn: người soạn cũng là nhóm/agent, chưa có người ngoài. |
| "Đáp án chuẩn do ai gán?" | Mã thủ tục lấy từ DB, người soạn gán và ghi giả định từng câu (`eval/H*_ASSUMPTIONS.md`). Một số câu chấp nhận nhiều đáp án. Chưa có chuyên gia pháp lý rà. |
| "Vì sao top-1 chỉ 73%?" | Lỗi chính là chọn nhầm thủ tục cùng họ (ví dụ các loại mai táng phí), không phải xếp thứ hai. Câu nêu rõ tên thủ tục đạt 95–100%. Hướng sửa: hỏi lại khi các thủ tục cùng họ có điểm sát nhau (slide 7). |
| "Hỏi lại 47%, vì sao yếu?" | Đây là recall: 40/86 ca cần hỏi lại. Hai nhóm lỗi gốc đã sửa (bộ tự soạn 14/27 lên 20/27), chưa đo lại trên bộ mù để giữ nó mù. |
| "Số liệu bịa 87% có đáng tin?" | Mẫu 92 ca, kiểm bằng luật so với ngữ cảnh. 13% không khớp một phần do ngữ cảnh giám khảo không trùng Answerer, một phần do dữ liệu tự mâu thuẫn. Hệ thống không để LLM chọn thủ tục hay viết số: số lấy từ DB. |
| "Che PII 100% nghĩa là gì?" | 12 ca che và 11 ca chèn lệnh do nhóm soạn, đều đạt, 0 chặn nhầm. Bộ test từng tìm ra lỗi thật (0/3 với số có dấu cách), đã vá và có test hồi quy. Chưa thử chèn lệnh gián tiếp qua tài liệu tải lên. |
| "Chạy không GPU thì sao?" | Strict (luật) không dùng GPU ở phần truy xuất, nên nhanh. Với Friendly và bước sinh chữ: **cần số đo thật**; nếu chưa đo thì nói chưa đo. |
| "Friendly 92% đo trên gì?" | Bài thi 26 câu exam × 3 lần trên dữ liệu giả (danh sách lớp), chính sách, du lịch; chấm bằng luật. Giới hạn: câu do Claude soạn, mẫu nhỏ, kiến thức chung của model 4B dao động. |
| "Sao không dùng RAGAS?" | Đã thử và kiểm giám khảo: bắt được 51% ý bịa cài sẵn, κ 0,02 / 0,20. Nên dùng chỉ số luật. Chuẩn κ là LLM, chưa phải người; phiếu 15 ca chưa điền. |
| "Có dữ liệu người dùng thật không?" | Chưa có log người dùng thật. Bộ "log thật" cũ là mô phỏng (`REAL_LOG_v1.md`). Từ 22/10 có bộ **câu hỏi thật của người dân** trên Cổng dịch vụ công (real_v1, mục 0b); đó là câu hỏi công khai, không phải log của hệ thống. Nút 👍/👎 đã lưu cặp (câu hỏi, câu trả lời) kèm ngữ cảnh để dùng khi deploy; hiện có 3 👍 / 1 👎. |

## 8. Danh sách file chứng cứ (tất cả đường dẫn tính từ thư mục gốc repo `merged/`)

| Chủ đề | File | Trạng thái |
|---|---|---|
| Bảng A, B, C, D của Strict | `eval/saved_results/2026-10-14/report.md` | trong git |
| Bảng A–D chi tiết kèm lời giải thích | `docs/PLAN_TUAN_TOI.md` mục 3 | trong git |
| Tiêu chí, số hiện tại và ngưỡng | `eval/CRITERIA.md` | trong git |
| Quy tắc bộ mù | `docs/EVAL.md` | trong git |
| Kết quả thô golden set (từng ca) | `eval/results/golden_thu-tuc.json` | **ngoài git** (`.gitignore`); chạy lại bằng `run_golden.py` |
| An toàn (PII, chèn lệnh) | `eval/saved_results/2026-10-14/safety_20261014_174352.json`, `eval/safety/` | trong git |
| Độ trễ Strict | `eval/results/latency_d1_llm0.json`, `latency_report_llm0.json`, `latency_report_llm1.json` | **ngoài git**; số có trong `docs/PLAN_TUAN_TOI.md` |
| Bước sinh chữ (composer) | `eval/results/composer_final3.json`, `p27_e2e_run3.json` | **ngoài git**; số có trong `docs/EVAL.md` |
| RAGAS-lite và κ | `eval/saved_results/2026-10-14/ragas_*` | trong git |
| Phiếu chấm người (chưa điền) | `eval/saved_results/2026-10-14/ragas_calib_human_sheet_d2.md` | trong git |
| Bộ Friendly: bộ câu, chấm | `system4/eval/bench.py`, `bench_cases.py`, `nv2_behavior.py` | trong git |
| Friendly: kết quả bài thi cuối (D1–D9) | `docs/SYSTEM4_NV5_TOC_DO_CHINH_XAC.md` | trong git (**chỉ số, không có file thô**) |
| Friendly: tài liệu Excel/Word (17/17) | `system4/eval/results/nv3_specialist.json`, `docs/SYSTEM4_NV3_DATASET.md` | trong git |
| Friendly: 22 tình huống (bản cũ 22/22) | `system4/eval/results/nv2_behavior.json` | trong git |
| Tìm web (test chức năng, DuckDuckGo giả) | `system4/tests/test_websearch.py` | trong git |
| Tìm web, Strict A/B | `eval/results/websearch_ab.md`, `eval/run_websearch_ab.py` | **ngoài git** |
| Ghi chú tài liệu cũ mâu thuẫn với code | `docs/SYSTEM4_SU_THAT.md` | trong git |
| Tóm tắt 1 phút cho mentor | `docs/TOM_TAT_EVAL_CHO_MENTOR.md` | trong git |
| real_v1: báo cáo một trang | `docs/EVAL_THAT_V1.md` | chưa commit |
| real_v1: câu hỏi, nhãn, khoá | `eval/real_v1/`, `system4/eval/real_v1/` (`LOCK.md`) | chưa commit |
| real_v1: kết quả thô Strict | `eval/saved_results/2026-10-22_real_v1/` | chưa commit |
| real_v1: kết quả thô Friendly | `system4/eval/saved_results/2026-10-22_real_v1/` | chưa commit |
| Bản đồ bài báo cho từng lựa chọn thiết kế | `eval/CRITERIA.md` mục 4, `docs/research paper/PAPER_LIST_33.md` | trong git |

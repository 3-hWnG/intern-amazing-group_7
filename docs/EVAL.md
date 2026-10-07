# Đánh giá (eval) — cách đo và quy tắc giữ số đo trung thực

## Các bộ test (`eval/`)
| Bộ | File | Số câu | Vai trò |
|---|---|---|---|
| DEV | `cases.jsonl` (split=dev) | **523** = 209 cũ + 85 (`p16-`, `build_p16.py`) + 138 (`p18-`, `build_p18.py`) + 17 (`p19-`, `build_p19.py`) + 74 (`p23-`, `build_p23.py`) | dùng để tune; cổng hồi quy tính 209 ca cũ (id không bắt đầu `p16`/`p18`/`p19`/`p23`), số của cả 523 báo riêng |
| p16aside | `cases_p16_aside.jsonl` (`run.py --split p16aside`) | 36 | bộ "để riêng" của Phase 16: viết trước khi sửa, không tune; chạy lúc đầu và lúc nghiệm thu |
| HOLDOUT (cũ) | `cases.jsonl` (split=holdout) | 67 | đã dùng để sửa lỗi → **không còn là bộ mù** |
| HOLDOUT-2 | `cases_h2.jsonl` | 62 | mù lúc soạn, sau đó bị lộ một phần → ô nhiễm nhẹ |
| HOLDOUT-3 | `cases_h3.jsonl` | 88 | mù, đã chạy lại sau đợt 4 (chỉ xem số tổng, không vá theo câu) |
| **HOLDOUT-4** | `cases_h4.json`, `run_pseudo.py cases_h4.json h4_rules` | 90 mục / 106 lượt | **bộ mù chính thức** (agent không thấy mã); số hiện tại top-1 78% (60/77), hành vi 84% (89/106), hỏi lại 8/16. Giả định: `H4_ASSUMPTIONS.md`. Đừng tune |
| pseudo_real 2 | `cases_pseudo_real2.json` | 30 mục / 34 lượt | mù, kiểu người dân gõ đời thường; top-1 19/28, hành vi 23/34, hỏi lại 0/3. Giả định: `PSEUDO_REAL_ASSUMPTIONS.md` |
| ctx | `cases_ctx.jsonl` | 144 hội thoại = `ctx-dev` 58 + `ctx-hold` 33 (91 ca gốc, chạy mặc định) + `ctx-p16` 27 + `ctx-p23` 26 (chạy riêng: `run_ctx.py --split ctx-p16` / `--split ctx-p23`) | context memory (agent tự soạn và đã tune) |
| perturb | `perturb.py` | 649 ca đã đúng của DEV + ctx × 11 loại nhiễu (7.096 phép thử) | bất biến khi thêm nhiễu không đổi nghĩa (xem dưới); không dùng bộ mù |
| p26 (bộ nhớ người dùng) | `cases_p26.jsonl` (dựng bằng `build_p26.py`), `run_p26.py` | 92 ca = a 28 (hồ sơ khớp) + b 28 (cùng câu không hồ sơ) + c 24 (hồ sơ sai/lạc, câu nêu rõ) + d 12 (hồ sơ rỗng); 37 câu khác nhau | câu tự soạn; đáp án nhóm a theo quy tắc `procedure_subjects`; **không** nằm trong `cases.jsonl` nên gate DEV cũ không lẫn; gate: `run_p26.py` 92/92 (d = y hệt cũ, c không đổi đáp án) |
| synth | `synth_retrieval.py` | ~1.600 câu sinh từ DB | khả năng tổng quát của truy hồi; TRAIN-seed và TEST-seed tách rời |
| pseudo_real | `cases_pseudo_real.json`, `run_pseudo.py` | 30 câu + 4 hội thoại | câu kiểu người dân do agent soạn không thấy mã; đã bị xem lỗi, không tune |
| team | `cases_team.json`, `run_team.py` | 10 câu | bộ test chung của các team (`Test_Case_Legal_AI_Assistant_Bang_Test.docx`); chấm luật tự động (không phải điểm chính thức 4+2+2+2); hiện 8/10, TC03 và TC06 xem [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |

Mỗi câu có đáp án proc_id lấy từ DB (assert khi dựng) và hành vi mong đợi (answer / apologize / clarify). Đáp án giả định của người soạn nằm trong `eval/EXPECTATIONS_REVIEW.md` (bộ gốc), `eval/H3_ASSUMPTIONS.md`, `eval/H4_ASSUMPTIONS.md` và `eval/PSEUDO_REAL_ASSUMPTIONS.md`.

## Chạy
```bash
cd system3/eval
set PYTHONPATH=<ROOT>                # thư mục cha của system3
set S3_USE_LLM=0                     # đo phần luật; =1 để bật bước LLM sinh chữ
REM bộ chấm đọc data/runtime/system3.db; đổi bằng S3_DB hoặc S3_DATA_DB (DB kiểu V10.6 cho baseline: S3_V106_DB)
REM tất cả gate không GPU một lệnh, ở thư mục gốc system3: python run_server.py eval/run_all.py [--quick]
python run.py --adapter answer_adapter:adapter --name my_run --split all        # DEV + HOLDOUT cũ
python run.py --adapter answer_adapter:adapter --name my_h3  --split holdout3   # bộ mù cũ (chạy lại ở đợt 4); bộ mù CHÍNH THỨC là HOLDOUT-4: run_pseudo.py cases_h4.json
python synth_retrieval.py            # bộ tự sinh, in TRAIN-seed và TEST-seed (biến thể `glued` = dính chữ, báo riêng, không tính vào số tổng)
python run_ctx.py                    # hội thoại nhiều lượt
python selftest.py                   # kiểm bộ chấm (oracle 100%, adapter nói dối bị bắt)
```
Dựng lại bộ test (không cần `repo/`: mã V10.6 nằm ở `eval/vendor_v106/`, DB tự dựng; xem [../eval/REPRODUCE.md](../eval/REPRODUCE.md)): `python build_cases.py`, `python build_h2.py`, `python build_h3.py`; ca p16/p18/p19/p23 nối thêm vào `cases.jsonl`: `python build_p16.py`, `python build_p18.py`, `python build_p19.py`, `python build_p23.py` (idempotent; p23 còn ghi hội thoại vào `cases_ctx.jsonl`, split `ctx-p23`).
Chỉ số concise: `S3_USE_LLM=0 python run_concise.py --name x` (trên Windows đặt `PYTHONIOENCODING=utf-8`).
Kết quả ghi vào `eval/results/<name>.json` (chỉ vài file mốc được đưa lên git).

## Bộ biến đổi câu `perturb.py` (Phase 23)
Lấy các ca ĐÃ ĐÚNG ở DEV (`cases.jsonl` split=dev) và ctx (`cases_ctx.jsonl`), áp một loại nhiễu không đổi nghĩa lên câu cuối (nhãn lượt đánh lên MỌI lượt user), rồi so (thủ tục top-1 của các task, hành vi) với đầu ra của câu gốc. Loại nhiễu: `label` (Turn N:/Câu N:/Q:/User:/Bạn:/Hỏi:/[User]/(Turn 2)...), `bullet` (2. / 2) / - / > ...), `quote`, `emoji`, `polite` (dạ/cho hỏi/ạ/nhé/giúp mình), `upper`, `space` (khoảng trắng, xuống dòng, tab), `punct` (dấu câu thừa), `glue` (dính 1-2 cặp chữ), `nodau` (bỏ dấu; bỏ qua ca gốc là từ chối vì lệch dấu), `mixed` (2-3 loại + nhãn). Nhiễu sinh theo seed cố định (id, loại, lần): chạy lại ra đúng bộ cũ.
```bash
cd eval && S3_USE_LLM=0 python perturb.py --name p23 [--k 2] [--kinds label,glue] [-v]     # ghi results/perturb_<name>.json
```
In tỉ lệ bất biến theo từng loại và liệt kê ca hỏng. **Gate: tổng bất biến >= 98%.** Ca hỏng còn lại phần lớn là nhiễu thật sự đổi nghĩa (bỏ dấu "sổ" -> "so", phẩy chen giữa tên thủ tục, dính chữ mơ hồ), xem `eval/P23_REPORT.md`.

## Chỉ số concise / đúng trọng tâm (`eval/run_concise.py`)
**Định nghĩa concise (nhóm, 2026-10-06): người dùng hỏi gì thì trả lời đúng ý đó** (hỏi giá thì chỉ báo giá). Độ dài chỉ là số phụ để theo dõi, không có ngưỡng; trích đủ nội dung của mục được hỏi vẫn có thể dài.
Chấm bằng luật trên câu trả lời thật (không cần LLM): **task thừa** (nhiều thủ tục hơn số ý), **mục thừa** (tiêu đề như "Lệ phí:", "Nơi nộp hồ sơ:" không được hỏi), **mục thiếu**, **focus** (không thừa, không thiếu), độ dài (ký tự trung vị, p90). Hỏi căn cứ/nguồn thì "Căn cứ pháp lý" tính là mục được hỏi. Số gốc 2026-10-06 (trước Phase 18): DEV focus 70% (113/162), HOLDOUT cũ 59%, task thừa 11/230, độ dài trung vị 1.269 ký tự, p90 2.433.
Sau Phase 18 (2026-10-06): DEV focus 97,5% (158/162 ca cũ+p16; tính cả ca p18 thì 99%, 267/271), HOLDOUT cũ 96% (47/49), task thừa DEV 0, độ dài trung vị ~1.000, p90 ~1.800. Ca p18 do chính người sửa lỗi tự nghĩ nên **dễ hơn bộ mù**; số để so sánh trung thực là 162 ca cũ. Hai bộ team/pseudo_real chỉ được người điều phối chạy (không xem từng ca khi sửa).
Quy ước đã đổi ở Phase 18: câu hỏi chung ("làm thủ tục X") trả bản tóm tắt ngắn (mỗi mục <= 450 ký tự); "X ở đâu" chung chung mà cổng không ghi địa điểm thì trả `agency`; câu điều kiện không nêu mục thì trả `components` + phần trường hợp; so sánh hai thủ tục trả `explanation` của từng vế.

## Chỉ số
top-1/top-3 (đúng thủ tục), đúng fields, **đúng hành vi**, **bịa số** (số trong câu trả lời không có trong dữ liệu; thấp là tốt), "nói không công bố" khi dữ liệu thiếu, trích nguồn, và 4 loại luật (điều kiện, so sánh, phủ định, thứ tự) chấm bằng `rules_scorer.py`.

## Quy tắc BẮT BUỘC
1. **Không tune trên HOLDOUT-3, HOLDOUT-4, pseudo_real 1 và 2, bộ team** và không đọc lỗi của chúng để vá từng câu. Nếu đã làm thế, nó thành DEV: soạn bộ mù mới.
2. Khi giao việc cho người/agent sửa lỗi, chỉ mô tả **nhóm lỗi chung**, không đưa câu hay chủ đề cụ thể của bộ mù (đợt 3 đã mắc lỗi này với HOLDOUT-2).
3. Báo cáo cả DEV lẫn bộ mù. Số trên DEV luôn cao hơn.
4. Không sửa đáp án để số đẹp hơn. Đổi đáp án chỉ khi quy tắc nghiệp vụ đổi và ghi lý do.
5. Sửa nguyên nhân chung, không hard-code câu test.

## Đo Planner hybrid (Phase 19)
`S3_PLANNER_MODE=hybrid` chạy qua `answer_adapter` (`extra.llm` = nhật ký planner_llm). Quét ngưỡng không gọi lại LLM: đặt `S3_PLANNER_LLM_CACHE=<file.jsonl>` (lần đầu gọi thật và ghi, các lần sau phát lại, độ trễ cộng lại từ giá trị đã đo), đổi `PLANNER_LLM_CONFIDENCE`; `PLANNER_LLM_DRAFT=1` là biến thể xét bản nháp. Cùng bộ: `run.py --split all`, `run_ctx.py`, `run_concise.py --no-blind` (bỏ team/pseudo_real, không đưa bộ nghiệm thu qua LLM). `p19_compare.py --rules <tag> --hyb <tag1,tag2>` ra bảng so sánh (top-1, hành vi, bịa số, multi-intent, p50/p95, tỉ lệ timeout, số đề xuất/được nhận/đúng hơn/sai đi). Ngưỡng chỉ chọn trên DEV; gate: >= +2 điểm chỉ số chính trên DEV cũ + ctx, không tăng bịa số, không tụt gate hồi quy, timeout < 10%. Kết quả: [../eval/P19_REPORT.md](../eval/P19_REPORT.md) (không đạt).

## Đo bước sinh chữ (Answer Composer, Phase 27)
`eval/build_composer_set.py` chọn các ca có bước LLM (task có `conditions` hoặc >= 2 task `compare`; dò bằng LLM giả, không gọi Ollama) từ DEV cũ + p16/p18/p19/p23 (trong DEV) + ctx + `cases_p26.jsonl`, không đụng bộ mù/team, rồi thêm ca tự soạn `eval/composer_own.py` (split `composer`): ra `cases_composer.jsonl` = **63 ca** (46 DEV, 4 ctx, 13 tự soạn; p26 không kích hoạt ca nào). Ca tự soạn **dễ hơn câu thật** (nêu điều kiện/so sánh rõ ràng, vài ca dựng từ chính chữ của `condition_index`). Kích hoạt: 46/523 ca DEV (25/209 DEV cũ), 4/144 ca ctx.
`eval/score_composer.py` chạy mỗi ca hai lần (TẮT = bản code, BẬT = Ollama qwen3:4b) và chấm bằng LUẬT: (a) đủ ý (nêu cụm khoá của mục `condition_index` liên quan; so sánh: nêu cả hai thủ tục; chỉ chấm 23 ca có điều kiện do người dùng nêu, 40 ca còn lại là điều kiện Planner tự gán nên "n/a"), (b) mọi số trong câu có trong nguồn thủ tục/câu hỏi, (c) không đảo cặp có/không, được/không được... so với câu nguồn gần nhất, (d) không có cơ quan/văn bản/số hiệu lạ, (e) phần sinh chữ <= 1000 ký tự, mỗi ý <= 300. Ghi `results/composer_<tên>.json`; `--sample` ghi `results/composer_sample20.md` (20 ca, seed 27, **chưa có điểm**, để người chấm). `p27_e2e.py` đo độ trễ qua `/chat` với cấu hình mặc định.
```bash
cd eval && PYTHONPATH=<ROOT> S3_PLANNER_MODE=rules python score_composer.py --name x --sample     # cần Ollama + qwen3:4b, ~3 phút
python p27_e2e.py --name x                                                                          # server tạm cổng 8393, ~2 phút
```
Số đo (`results/composer_final3.json`, timeout 7 s, 63 ca; `results/p27_e2e_run3.json`):

| tiêu chí | TẮT (code) | BẬT |
|---|---|---|
| (a) đủ ý (n=23) | 22/23 | 22/23 |
| (b) không sai số | 63/63 | 63/63 |
| (c) không đảo nghĩa | 63/63 | 63/63 |
| (d) không bịa cơ quan/văn bản | 62/63 | 62/63 |
| (e) độ dài hợp lý | 47/63 | 61/63 |
| đạt cả 5 | 45/63 (71%) | 59/63 (94%) |

Lượt gọi LLM: 64, timeout 0 (0%), p50 1,8 s, p95 3,1 s, max 4,6 s; verifier loại 6/104 ý (6%); BẬT tệ hơn TẮT ở 1 ca (tiêu chí độ dài), tốt hơn ở 15. Qua `/chat` (63 ca có LLM): p50 1,9 s, p95 3,4 s, max 5,0 s, 1 lượt rơi về bản code; 150 ca DEV không có LLM: p95 ~0,1 s. Lưu ý: GPU dùng chung nên số đo dao động (một lượt đo khác cùng cấu hình: timeout 4/64, p95 7,0 s). Tiêu chí luật không đo "có ích hơn không": phần hơn của BẬT gần như chỉ ở độ ngắn gọn; giá trị thật chờ người chấm 20 ca. Chi tiết, thay đổi từng bước và số trước/sau: [../eval/P27_REPORT.md](../eval/P27_REPORT.md). Hồi quy khi BẬT (`S3_USE_LLM=1`): mọi chỉ số bằng chế độ tắt (xem báo cáo).

## Cổng hồi quy (chế độ luật, `S3_USE_LLM=0`)
Một bảng duy nhất, dùng chung với [CONTRIBUTING.md](CONTRIBUTING.md) (gate mới ghi ở Phase 24; **B1: DEV focus thống nhất ≥ 95%**, mốc 90% là mục tiêu duyệt ban đầu của đợt 4, đã lỗi thời vì số hiện tại 99%):

| Cổng | Ngưỡng | Số hiện tại |
|---|---|---|
| DEV cũ 209: top-1 | ≥ 95% | 97,0% (159/164) |
| DEV cũ 209: đúng hành vi | ≥ 96% | 97,6% (204/209) |
| DEV cũ 209: bịa số | ≤ 3% | 0,0% |
| ngoài phạm vi (DEV) | 30/30 | 30/30 |
| ctx 91 ca, top-1 lượt cuối | ≥ 89/91 | 89/91 (ctx-p23 26/26) |
| synth TEST-seed top-1 | ≥ 94% (`glued` ≥ 90%) | 96,4% (`glued` 96,1%) |
| DEV focus (`run_concise.py`) | **≥ 95%** | 99% (349/353) |
| task thừa (`run_concise.py`) | ≤ 2% | 0/451 |
| `perturb.py` bất biến | ≥ 98% | 99,44% |
| `check_docs.py` | sạch (0 lỗi) | sạch |

## Số đo hiện tại
Xem bảng trong [../README.md](../README.md) (`python eval/check_docs.py` kiểm các số ấy với `eval/results/`). Số chính thức (bộ mù): HOLDOUT-4 top-1 78% (60/77), đúng hành vi 84% (89/106), hỏi lại 8/16; pseudo_real 2 top-1 19/28, hành vi 23/34, hỏi lại 0/3; bộ team 8/10 (chấm luật). HOLDOUT-3 chạy lại ở đợt 4 (trước Phase 23): 75% / 86% / bịa số 3,4%. `check_docs.py` không mở file kết quả của bộ mù (quy tắc ở trên): các số bộ mù do người điều phối ghi trong README và trong chính script.
Lệnh chạy bộ mù mới: `python run_pseudo.py cases_h4.json h4_rules` (đặt `S3_PLANNER_MODE=hybrid` để thử hybrid). `run_pseudo.py` chỉ chấm top-1/top-3/hành vi, chưa chấm bịa số.

## Kiểm tài liệu (`eval/check_docs.py`)
```bash
python eval/check_docs.py          # exit 0 = sạch; in từng lỗi và từng mục bỏ qua
```
Kiểm: (1) số trong README so với file kết quả mới nhất trong `eval/results/` (DEV 523 và DEV cũ 209, ctx, ctx-p23, concise, perturb, synth) — chỉ các bộ không-mù; (2) số bộ mù/bộ team trong README khớp bảng của script và khớp giữa README/EVAL/KNOWN_ISSUES; (3) đường dẫn file trong liên kết và trong `code` có tồn tại; lệnh `python ...` trong khối mã trỏ tới file/module có thật; (4) mọi file `server/tests/*_test.py` có trong SETUP và CONTRIBUTING; (5) `_EVENTS`, timeout trong `config.py` khớp tài liệu, không còn "DEV focus ≥ 90%"; (6) file có thẻ `FINAL-PRODUCT:` được nêu trong `FINAL_PRODUCT_CHECKLIST.md`. Chạy trong cổng trước khi mở PR.

## Cải thiện đáng làm tiếp
Bộ câu hỏi thật từ log người dân (20–30 câu) làm bộ kiểm cuối; bộ chấm riêng cho chất lượng bước LLM sinh chữ; bộ mù mới sau mỗi vòng sửa.

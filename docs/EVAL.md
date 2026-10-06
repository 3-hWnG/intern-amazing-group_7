# Đánh giá (eval) — cách đo và quy tắc giữ số đo trung thực

## Các bộ test (`eval/`)
| Bộ | File | Số câu | Vai trò |
|---|---|---|---|
| DEV | `cases.jsonl` (split=dev) | 209 cũ + 85 (`p16-`, `build_p16.py`) + 138 (`p18-`, `build_p18.py`) + 17 (`p19-`, `build_p19.py`) | dùng để tune; cổng hồi quy chỉ tính 209 ca cũ (id không bắt đầu `p16`/`p18`/`p19`) |
| HOLDOUT (cũ) | `cases.jsonl` (split=holdout) | 67 | đã dùng để sửa lỗi → **không còn là bộ mù** |
| HOLDOUT-2 | `cases_h2.jsonl` | 62 | mù lúc soạn, sau đó bị lộ một phần → ô nhiễm nhẹ |
| HOLDOUT-3 | `cases_h3.jsonl` | 88 | mù, đã chạy lại sau đợt 4 (chỉ xem số tổng, không vá theo câu) |
| **HOLDOUT-4** | `cases_h4.json`, `run_pseudo.py cases_h4.json h4_rules` | 90 mục / 106 lượt | **mù, số chính thức mới nhất** (agent không thấy mã). Giả định: `H4_ASSUMPTIONS.md`. Đừng tune |
| pseudo_real 2 | `cases_pseudo_real2.json` | 30 mục / 34 lượt | mù, kiểu người dân gõ đời thường |
| ctx | `cases_ctx.jsonl` | ~91 hội thoại | context memory (agent tự soạn và đã tune) |
| synth | `synth_retrieval.py` | ~1.600 câu sinh từ DB | khả năng tổng quát của truy hồi; TRAIN-seed và TEST-seed tách rời |
| pseudo_real | `cases_pseudo_real.json`, `run_pseudo.py` | 30 câu + 4 hội thoại | câu kiểu người dân do agent soạn không thấy mã; đã bị xem lỗi, không tune |
| team | `cases_team.json`, `run_team.py` | 10 câu | bộ test chung của các team (`Test_Case_Legal_AI_Assistant_Bang_Test.docx`); chấm luật tự động (không phải điểm chính thức 4+2+2+2) |

Mỗi câu có đáp án proc_id lấy từ DB (assert khi dựng) và hành vi mong đợi (answer / apologize / clarify). Đáp án giả định của người soạn nằm trong `EXPECTATIONS_REVIEW.md` và `H3_ASSUMPTIONS.md`.

## Chạy
```bash
cd system3/eval
set PYTHONPATH=<ROOT>                # thư mục cha của system3
set S3_USE_LLM=0                     # đo phần luật; =1 để bật bước LLM sinh chữ
REM bộ chấm đọc data/runtime/system3.db; đổi bằng S3_DB hoặc S3_DATA_DB
python run.py --adapter answer_adapter:adapter --name my_run --split all        # DEV + HOLDOUT cũ
python run.py --adapter answer_adapter:adapter --name my_h3  --split holdout3   # bộ mù chính thức
python synth_retrieval.py            # bộ tự sinh, in TRAIN-seed và TEST-seed
python run_ctx.py                    # hội thoại nhiều lượt
python selftest.py                   # kiểm bộ chấm (oracle 100%, adapter nói dối bị bắt)
```
Dựng lại bộ test: `python build_cases.py`, `python build_h2.py`, `python build_h3.py`; ca p16/p18 nối thêm vào `cases.jsonl`: `python build_p16.py`, `python build_p18.py` (idempotent).
Chỉ số concise: `S3_USE_LLM=0 python run_concise.py --name x` (trên Windows đặt `PYTHONIOENCODING=utf-8`).
Kết quả ghi vào `eval/results/<name>.json` (chỉ vài file mốc được đưa lên git).

## Chỉ số concise / đúng trọng tâm (`eval/run_concise.py`)
**Định nghĩa concise (nhóm, 2026-10-06): người dùng hỏi gì thì trả lời đúng ý đó** (hỏi giá thì chỉ báo giá). Độ dài chỉ là số phụ để theo dõi, không có ngưỡng; trích đủ nội dung của mục được hỏi vẫn có thể dài.
Chấm bằng luật trên câu trả lời thật (không cần LLM): **task thừa** (nhiều thủ tục hơn số ý), **mục thừa** (tiêu đề như "Lệ phí:", "Nơi nộp hồ sơ:" không được hỏi), **mục thiếu**, **focus** (không thừa, không thiếu), độ dài (ký tự trung vị, p90). Hỏi căn cứ/nguồn thì "Căn cứ pháp lý" tính là mục được hỏi. Số gốc 2026-10-06 (trước Phase 18): DEV focus 70% (113/162), HOLDOUT cũ 59%, task thừa 11/230, độ dài trung vị 1.269 ký tự, p90 2.433.
Sau Phase 18 (2026-10-06): DEV focus 97,5% (158/162 ca cũ+p16; tính cả ca p18 thì 99%, 267/271), HOLDOUT cũ 96% (47/49), task thừa DEV 0, độ dài trung vị ~1.000, p90 ~1.800. Ca p18 do chính người sửa lỗi tự nghĩ nên **dễ hơn bộ mù**; số để so sánh trung thực là 162 ca cũ. Hai bộ team/pseudo_real chỉ được người điều phối chạy (không xem từng ca khi sửa).
Quy ước đã đổi ở Phase 18: câu hỏi chung ("làm thủ tục X") trả bản tóm tắt ngắn (mỗi mục <= 450 ký tự); "X ở đâu" chung chung mà cổng không ghi địa điểm thì trả `agency`; câu điều kiện không nêu mục thì trả `components` + phần trường hợp; so sánh hai thủ tục trả `explanation` của từng vế.

## Chỉ số
top-1/top-3 (đúng thủ tục), đúng fields, **đúng hành vi**, **bịa số** (số trong câu trả lời không có trong dữ liệu; thấp là tốt), "nói không công bố" khi dữ liệu thiếu, trích nguồn, và 4 loại luật (điều kiện, so sánh, phủ định, thứ tự) chấm bằng `rules_scorer.py`.

## Quy tắc BẮT BUỘC
1. **Không tune trên HOLDOUT-3** và không đọc lỗi của nó để vá từng câu. Nếu đã làm thế, nó thành DEV: soạn bộ mù mới.
2. Khi giao việc cho người/agent sửa lỗi, chỉ mô tả **nhóm lỗi chung**, không đưa câu hay chủ đề cụ thể của bộ mù (đợt 3 đã mắc lỗi này với HOLDOUT-2).
3. Báo cáo cả DEV lẫn bộ mù. Số trên DEV luôn cao hơn.
4. Không sửa đáp án để số đẹp hơn. Đổi đáp án chỉ khi quy tắc nghiệp vụ đổi và ghi lý do.
5. Sửa nguyên nhân chung, không hard-code câu test.

## Đo Planner hybrid (Phase 19)
`S3_PLANNER_MODE=hybrid` chạy qua `answer_adapter` (`extra.llm` = nhật ký planner_llm). Quét ngưỡng không gọi lại LLM: đặt `S3_PLANNER_LLM_CACHE=<file.jsonl>` (lần đầu gọi thật và ghi, các lần sau phát lại, độ trễ cộng lại từ giá trị đã đo), đổi `PLANNER_LLM_CONFIDENCE`; `PLANNER_LLM_DRAFT=1` là biến thể xét bản nháp. Cùng bộ: `run.py --split all`, `run_ctx.py`, `run_concise.py --no-blind` (bỏ team/pseudo_real, không đưa bộ nghiệm thu qua LLM). `p19_compare.py --rules <tag> --hyb <tag1,tag2>` ra bảng so sánh (top-1, hành vi, bịa số, multi-intent, p50/p95, tỉ lệ timeout, số đề xuất/được nhận/đúng hơn/sai đi). Ngưỡng chỉ chọn trên DEV; gate: >= +2 điểm chỉ số chính trên DEV cũ + ctx, không tăng bịa số, không tụt gate hồi quy, timeout < 10%. Kết quả: [../eval/P19_REPORT.md](../eval/P19_REPORT.md) (không đạt).

## Số đo hiện tại
Xem bảng trong [../README.md](../README.md). Số chính thức: HOLDOUT-4 top-1 75%, đúng hành vi 82%, hỏi lại 8/16, xin lỗi 13/13; HOLDOUT-3 chạy lại: 75% / 86% / bịa số 3,4%.
Lệnh chạy bộ mù mới: `python run_pseudo.py cases_h4.json h4_rules` (đặt `S3_PLANNER_MODE=hybrid` để thử hybrid). `run_pseudo.py` chỉ chấm top-1/top-3/hành vi, chưa chấm bịa số.

## Cải thiện đáng làm tiếp
Bộ câu hỏi thật từ log người dân (20–30 câu) làm bộ kiểm cuối; bộ chấm riêng cho chất lượng bước LLM sinh chữ; bộ mù mới sau mỗi vòng sửa.

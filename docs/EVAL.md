# Đánh giá (eval) — cách đo và quy tắc giữ số đo trung thực

## Các bộ test (`eval/`)
| Bộ | File | Số câu | Vai trò |
|---|---|---|---|
| DEV | `cases.jsonl` (split=dev) | 209 | dùng để tune |
| HOLDOUT (cũ) | `cases.jsonl` (split=holdout) | 67 | đã dùng để sửa lỗi → **không còn là bộ mù** |
| HOLDOUT-2 | `cases_h2.jsonl` | 62 | mù lúc soạn, sau đó bị lộ một phần → ô nhiễm nhẹ |
| **HOLDOUT-3** | `cases_h3.jsonl` | 88 | **mù, số chính thức**. Đừng tune trên bộ này |
| ctx | `cases_ctx.jsonl` | ~91 hội thoại | context memory (agent tự soạn và đã tune) |
| synth | `synth_retrieval.py` | ~1.600 câu sinh từ DB | khả năng tổng quát của truy hồi; TRAIN-seed và TEST-seed tách rời |

Mỗi câu có đáp án proc_id lấy từ DB (assert khi dựng) và hành vi mong đợi (answer / apologize / clarify). Đáp án giả định của người soạn nằm trong `EXPECTATIONS_REVIEW.md` và `H3_ASSUMPTIONS.md`.

## Chạy
```bash
cd system3/eval
set PYTHONPATH=<ROOT>                # thư mục cha của system3
set S3_USE_LLM=0                     # đo phần luật; =1 để bật bước LLM sinh chữ
python run.py --adapter answer_adapter:adapter --name my_run --split all        # DEV + HOLDOUT cũ
python run.py --adapter answer_adapter:adapter --name my_h3  --split holdout3   # bộ mù chính thức
python synth_retrieval.py            # bộ tự sinh, in TRAIN-seed và TEST-seed
python run_ctx.py                    # hội thoại nhiều lượt
python selftest.py                   # kiểm bộ chấm (oracle 100%, adapter nói dối bị bắt)
```
Dựng lại bộ test: `python build_cases.py`, `python build_h2.py`, `python build_h3.py`.
Kết quả ghi vào `eval/results/<name>.json` (chỉ vài file mốc được đưa lên git).

## Chỉ số
top-1/top-3 (đúng thủ tục), đúng fields, **đúng hành vi**, **bịa số** (số trong câu trả lời không có trong dữ liệu; thấp là tốt), "nói không công bố" khi dữ liệu thiếu, trích nguồn, và 4 loại luật (điều kiện, so sánh, phủ định, thứ tự) chấm bằng `rules_scorer.py`.

## Quy tắc BẮT BUỘC
1. **Không tune trên HOLDOUT-3** và không đọc lỗi của nó để vá từng câu. Nếu đã làm thế, nó thành DEV: soạn bộ mù mới.
2. Khi giao việc cho người/agent sửa lỗi, chỉ mô tả **nhóm lỗi chung**, không đưa câu hay chủ đề cụ thể của bộ mù (đợt 3 đã mắc lỗi này với HOLDOUT-2).
3. Báo cáo cả DEV lẫn bộ mù. Số trên DEV luôn cao hơn.
4. Không sửa đáp án để số đẹp hơn. Đổi đáp án chỉ khi quy tắc nghiệp vụ đổi và ghi lý do.
5. Sửa nguyên nhân chung, không hard-code câu test.

## Số đo hiện tại
Xem bảng trong [../README.md](../README.md). Số chính thức: HOLDOUT-3 top-1 ~73%, đúng hành vi ~83%, bịa số ~7%.

## Cải thiện đáng làm tiếp
Bộ câu hỏi thật từ log người dân (20–30 câu) làm bộ kiểm cuối; bộ chấm riêng cho chất lượng bước LLM sinh chữ; bộ mù mới sau mỗi vòng sửa.

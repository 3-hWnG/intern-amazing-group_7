# Tiêu chí chấm System 3 (mục 3.1 của kế hoạch tuần tới)

Mỗi tiêu chí ghi: đo cái gì, bằng script nào, bộ nào là số chính thức, và chỗ còn thiếu. Quy tắc giữ số đo trung thực nằm ở [../docs/EVAL.md](../docs/EVAL.md) (không tune trên bộ mù).

## 0. Bộ test theo domain
Golden set một định dạng chung: `eval/golden/<domain>.jsonl` (dựng bằng `build_golden.py`, chấm bằng `run_golden.py`). `thu-tuc` gom 1.323 ca (status `dev`, `holdout-used`, `blind`); `tro-chuyen-chung` rỗng (chưa có đáp án kiểm được). Bộ khuôn câu hỏi theo chủ đề: `golden/template_thu-tuc.jsonl` (`build_template_set.py`). Bảng số liệu: `docs/PLAN_TUAN_TOI.md`, mục 3, phần "Bảng benchmark".

## 1. Truy xuất
| Chỉ số | Định nghĩa | Script | Số chính thức |
|---|---|---|---|
| top-1 | thủ tục đầu tiên nằm trong `acceptable_proc_ids` | `run.py`, `run_pseudo.py` | HOLDOUT-4 (bộ mù), pseudo_real 2 |
| top-3 | đáp án nằm trong 3 thủ tục đầu | như trên | như trên |
| ctx top-1 | như top-1 nhưng ở lượt cuối của hội thoại nhiều lượt | `run_ctx.py` | `ctx-hold` |
| tổng quát hoá | câu tự sinh từ DB, TRAIN-seed và TEST-seed tách rời | `synth_retrieval.py` | TEST-seed |

Chỉ chấm câu có thủ tục đáp án và `behavior=answer`. Số trên DEV luôn cao hơn bộ mù vì đã tune; báo cả hai.

## 2. Hành vi
| Chỉ số | Định nghĩa | Script |
|---|---|---|
| đúng hành vi | `answer` / `clarify` / `apologize` đúng với kỳ vọng | `run.py`, `run_pseudo.py` |
| hỏi lại đúng lúc | recall: câu mơ hồ được hỏi lại; precision: câu rõ không bị hỏi thừa | `run_p30.py`, `run_p31.py` |
| từ chối đúng | câu ngoài phạm vi (hộ chiếu, cấp tỉnh, làm thơ, chèn lệnh) bị từ chối | `run.py`, nhóm `out_of_scope` |
| không bịa | số tiền/ngày/SĐT không có trong nguồn; "miễn phí" khi nguồn không nói; nói "không công bố" khi thiếu | `run.py` (bộ chấm luật, không cần LLM) |
| không lệch khi nhiễu | đáp án không đổi khi thêm nhiễu không đổi nghĩa, ngưỡng ≥ 98% | `perturb.py` |
| đúng trọng tâm | hỏi giá thì chỉ trả giá; không task/mục thừa | `run_concise.py` |

## 3. Chất lượng câu trả lời (RAGAS)
Bốn chỉ số: faithfulness, answer relevancy, context precision, context recall. Script: `run_ragas_lite.py` (cài lại từ định nghĩa, giám khảo Ollama qwen3:4b; không dùng thư viện `ragas`; đầu file ghi từng chỗ khác RAGAS gốc). Chạy ~35 phút / 30 ca, nên không nằm trong `report.py`.
- **Kết quả thử (2026-10-13, 30 ca) và kiểm giám khảo**: xem `docs/PLAN_TUAN_TOI.md`, bảng F. Giám khảo 4B bỏ sót khoảng 70% ý bịa được chèn thêm và chấm 0 cho 17/30 câu trả lời đúng, nên **không dùng điểm faithfulness và answer relevancy để báo cáo**. Context recall tất nhiên cao (tham chiếu lấy từ chính DB). Context precision chỉ ở mức tham khảo.
- Hai model khác nhau không giữ cùng lúc trong VRAM 6 GB (mỗi lần đổi mất khoảng 7 giây), nên giám khảo dùng chung model với hệ thống; model lớn hơn cần máy khác hoặc API.
- **Chỉ số thay thế không cần LLM, đáng tin hơn**: `run.py` ("bịa số", "nói không công bố", trích nguồn), `run_concise.py` (đúng trọng tâm), `score_composer.py` (bước sinh chữ: đủ ý, đúng số, không đảo nghĩa, không bịa cơ quan/văn bản).
- Phép ánh xạ gần đúng: faithfulness ≈ "không bịa" + `score_composer`; context recall ≈ top-3; context precision và answer relevancy ≈ "đúng trọng tâm".

## 4. Tốc độ
Báo p50 và p95, tách theo loại câu và theo có/không GPU.
| Loại | Định nghĩa | Đã đo? |
|---|---|---|
Đo bằng `measure_latency.py` (đầu-cuối qua `/chat`, gửi tuần tự, mẫu cố định theo seed). Số 2026-10-13, GTX 1660 SUPER 6 GB, qwen3:4b-instruct, n = 40 mỗi loại (clarify 26):
| Loại | LLM tắt (`S3_USE_LLM=0`, chỉ CPU) p50 / p95 | LLM bật (mặc định) p50 / p95 |
|---|---|---|
| đơn giản (1 thủ tục, 1 ý) | 82 / 122 ms | 78 / 196 ms |
| phức tạp (nhiều ý hoặc nhiều lượt) | 63 / 122 ms | 59 / 1.624 ms |
| hỏi lại | 85 / 105 ms | 72 / 143 ms |
| ngoài phạm vi | 57 / 113 ms | 52 / 85 ms |
| **có bước sinh chữ bằng LLM** | không có | **3.192 / 6.268 ms** |
Đọc số: câu thường chạy bằng luật và truy xuất nên chỉ vài chục ms. Chỉ câu kích hoạt bước LLM (bộ `cases_composer.jsonl`, 63 ca, đều chọn là loại cần LLM) mới mất vài giây. Số tối đa ngoài p95 (4-7 s ở vài câu thường) chưa tìm nguyên nhân (có thể là bước LLM hiếm khi kích hoạt ở câu thường).
Hạn chế: "LLM tắt" đo CPU của chính máy này, không phải máy không có GPU nào khác (CPU yếu hơn thì chậm hơn tương ứng); Planner dùng luật (`S3_PLANNER_MODE=rules`), chưa đo Planner bằng LLM.
Đã đo: nạp lại model Ollama mất khoảng 7 giây khi đổi model, 0,16 giây khi cùng model (`measure_ollama_reload.py`); chạy song song chậm hơn chạy tuần tự trên 6 GB (`measure_parallel.py`).

## 5. Dữ liệu
| Chỉ số | Cách đo | Script |
|---|---|---|
| tỷ lệ bản ghi đúng nguồn | lấy mẫu 50 bản ghi phân tầng theo lĩnh vực, đối chiếu 5 trường với cổng dịch vụ công | `sample_dataset_check.py` (tạo phiếu và chấm) |
Cổng `dichvucong.gov.vn` tải chi tiết bằng JavaScript nên không đối chiếu tự động được; người kiểm điền phiếu bằng tay.
Nguồn dữ liệu: 1.350 thủ tục cấp xã chép nguyên văn từ V10.6 (`data/snapshot/SOURCE.md`). Mỗi bản ghi có `portal_url` và `decision_number`.

## Hạn chế cần ghi trong báo cáo
- Bộ DEV, ctx, synth, p* do nhóm tự soạn và đã tune; HOLDOUT-4 và pseudo_real do agent soạn từ giả định, chưa được người ngoài kiểm.
- RAGAS dùng giám khảo local nên kém tin cậy.
- Chưa đo tốc độ trên máy không GPU và theo loại câu phức tạp.

# System 3 - Phase 0: bộ test + baseline

Bộ đo cho System 3 (185 câu gốc + đợt 3: 24 câu DEV cho bộ chấm luật + 67 câu HOLDOUT) (LLM hỗ trợ thủ tục hành chính cấp xã).

| Hạng mục | Số câu |
|---|---|
| rag_basic, quantitative, multi_field, context_memory, clarify_conditional, evidence_citation, multi_intent, hallucination_unsupported, ctx_cond_evidence | 15 mỗi hạng mục (135) |
| out_of_scope (hộ chiếu, làm thơ, cấp tỉnh, ngành dọc, chitchat, chèn lệnh...) | 30 |
| typo (gõ tắt / không dấu / sai chính tả) | 20 |

## Chạy (một lệnh)
```
set PYTHONIOENCODING=utf-8
python run.py                                         # baseline (retrieval cũ): in bảng markdown + ghi results/<timestamp>.json
python run.py --adapter my_mod:my_fn --name system3   # đo System 3
python run.py --category quantitative --limit 5       # chạy một phần
```
Biến môi trường (tuỳ chọn): `S3_DB` (đường dẫn procedures.db), `S3_REPO` (chỉ dùng bởi baseline_adapter / build_cases).

## Adapter
`adapter(turns) -> dict`, `turns = [{"role": "user"|"assistant", "text": ...}]` (lượt cuối là user).
Trả về `tasks[] {proc_id, candidates[], fields[] | None, quantity}`, `behavior` (answer|apologize|clarify),
`answer_text`, `latency_ms` (bỏ trống thì harness tự đo); tuỳ chọn `says_not_published`, `fields_supported=False`, `extra`.

## Cách chấm
- top-1 / top-3: mỗi task kỳ vọng khớp một task đầu ra riêng (`acceptable_proc_ids`); chỉ chấm câu `behavior=answer` có thủ tục.
- fields: đúng bằng tập `fields` kỳ vọng (components, fees, processing_time, address, online, methods, files, agency, steps, explanation, meta).
- bịa số: `answer_text` có số tiền/ngày/giờ không nằm trong nguồn DB của thủ tục đáp án (hoặc trong câu hỏi), số bị cấm (`forbidden_numbers`), SĐT/giờ làm việc bịa, hoặc "miễn phí" khi nguồn không nói miễn.
- nói 'không công bố': câu có `must_say_not_published` phải chứa cụm kiểu "không công bố / chưa có thông tin / do HĐND quy định".
- trích nguồn: câu có `citation_tokens` phải chứa ít nhất 1 số hiệu văn bản / số quyết định / đường dẫn cổng đúng.
- is_strong sai: tỉ lệ `extra.is_strong` = True trên out_of_scope và hallucination (chỉ baseline).
- Với multi-intent >3 ý chỉ chấm 3 task đầu (`overflow`); ý không có trong kho (`partial_apology`) không chấm truy hồi.

## Tệp
- `cases.jsonl` - bộ câu, sinh bởi `build_cases.py`; mọi `acceptable_proc_ids`, dữ kiện phí/thời gian, câu "không có trong kho", cấp tỉnh/ngành dọc đều được assert với DB.
- `build_cases.py` - dựng lại và kiểm chứng (`python build_cases.py`; đọc `repo` read-only).
- `run.py`, `baseline_adapter.py`, `selftest.py` (oracle phải 100%, "kẻ nói dối" bị bắt bịa).
- `results/baseline.json`, `results/baseline_stripped.json`, `BASELINE.md`.
- `_q.py` - công cụ tra cứu tạm khi soạn câu (có thể xoá).

## Đợt 3 / Phase 8: tách DEV - HOLDOUT, bộ chấm luật
- `cases.jsonl` mỗi câu có `split` (`dev`|`holdout`) và `source` (`synthetic-dev` | `holdout-real-style` | `holdout-varied`). 185 câu cũ = DEV, giữ nguyên lời. Dựng bằng `python build_cases.py` (gọi `cases_new.py` cho phần mới; assert mọi proc_id / condition_index với DB).
- DEV 209 = 185 + 24 (nhóm `rule_condition|rule_compare|rule_negation|rule_order`, mỗi nhóm 6). HOLDOUT 67 = 43 (9 nhóm + out_of_scope + typo) + 24 rule (mỗi nhóm 6). 44 câu HOLDOUT gắn `holdout-real-style` (sai chính tả, viết tắt, thiếu dấu, kể dài, kiểu nhắn tin).
- Bộ chấm luật `rules_scorer.py` (không LLM), dùng `expected.checks`: condition (câu trả lời có cụm khoá của mục `condition_index` đúng), compare (nhắc cả hai thủ tục; không có answer_text thì cả hai là top-1), negation / order (top-1 thuộc đáp án và không chọn mục bị cấm). Kết quả nằm ở `rule_kind/rule_ok/rule_detail` trong file results.
- `run.py` in bảng riêng DEV, HOLDOUT và bảng chênh lệch (top-1, top-3, hành vi, bịa số, 4 loại luật); `--split dev|holdout|all`. HOLDOUT chỉ để nghiệm thu: không chọn tham số/prompt theo HOLDOUT. `sweep.py` chỉ dùng split DEV (`--holdout` mới in thêm HOLDOUT).
- `EXPECTATIONS_REVIEW.md`: các đáp án giả định (clarify, chitchat, multi-intent > 3) chờ duyệt.
- Số đo: `results/dot3_p8_baseline.json` (baseline_adapter), `results/dot3_p8_rules.json` (answer_adapter, `S3_USE_LLM=0`). `results/baseline.json` đã tái dựng trên 185 câu gốc (số khớp BASELINE.md; latency ghi lại không đo lại).

## Bộ hội thoại ctx (context memory)
`cases_ctx.py` -> `cases_ctx.jsonl` (58 hội thoại `ctx-dev` + 33 `ctx-hold` viết sau khi ctx-dev chạy sạch, mỗi hội thoại 2-5 lượt, chấm lượt cuối). Nhóm: a hỏi tiếp thiếu chủ ngữ, b đổi mục, c thủ tục liên quan/khác hẳn, d sửa ý, e kể hoàn cảnh, f đại từ, g quay lại, h độc lập (không được kế thừa), i điều kiện. Chạy: `PYTHONPATH=.. S3_USE_LLM=0 python run_ctx.py --name x [--split ctx-dev|ctx-hold] [-v]`. Không nằm trong `cases.jsonl` nên `run.py --split all` không chạm.

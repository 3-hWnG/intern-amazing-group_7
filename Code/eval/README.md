# System 3 - eval: bộ test, bộ chấm, baseline, kiểm tài liệu

Trạng thái 2026-10-07 (sau Phase 24): DEV 523 ca (209 gốc + p16/p18/p19/p23), HOLDOUT cũ 67, ctx 144 hội thoại, cùng các bộ mù HOLDOUT-3/4, pseudo_real 1/2, bộ team 10 câu. Cách đo và quy tắc bộ mù: [../docs/EVAL.md](../docs/EVAL.md); cổng hồi quy: [../docs/CONTRIBUTING.md](../docs/CONTRIBUTING.md). Phần dưới là mô tả bộ gốc (Phase 0/8), còn đúng cho `run.py`, adapter và cách chấm.

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
Biến môi trường (tuỳ chọn): `S3_V106_DB` (DB kiểu V10.6 cho baseline_adapter/build_cases, mặc định `eval/runtime/v106.db`, tự dựng từ `data/snapshot` bởi `rebuild_v106_db.py`), `S3_REPO` (đổi mã V10.6 sang một clone thật; mặc định dùng `eval/vendor_v106/`, không cần `repo/`). `S3_DB` chỉ còn là DB System 3 cho `run.py`/`cases_ctx.py` (cùng nghĩa `S3_DATA_DB`). Bộ chấm System 3 đọc DB của `system3.data.DB_PATH` (đổi bằng `S3_DATA_DB`). Đặt `PYTHONPATH=<ROOT>` khi thư mục tên `system3` (hoặc chạy qua `python ../run_server.py <script>`); `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1` để đo luật mà không đụng GPU.

## Dựng lại từ Git (Phase 28)
Xem [REPRODUCE.md](REPRODUCE.md). `python run_server.py eval/run_all.py` (gốc `system3`, thư mục tên gì cũng được) dựng DB, chạy mọi gate không GPU và in bảng số kèm ngưỡng (`--quick` bỏ synth + perturb; `--with-blind` chỉ cho người điều phối).
| File | Việc |
|---|---|
| `vendor_v106/` | mã V10.6 nguyên văn (~80 KB, commit `8356740`), `SOURCE.md` ghi nguồn và lệnh `git show` |
| `_v106.py`, `rebuild_v106_db.py` | đường dẫn mã/DB V10.6; dựng `runtime/v106.db` từ `data/snapshot/procedures.jsonl` |
| `p28_baseline_cmp.py` | so baseline V10.6 chạy lại (`results/v106_rerun.json`) với `results/baseline.json` |
| `run_all.py`, `REPRODUCE.md`, `P28_REPORT.md` | một lệnh dựng + gate; hướng dẫn; báo cáo |

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
- `build_cases.py` - dựng lại và kiểm chứng (`python build_cases.py`; mã V10.6 từ `vendor_v106/`, DB từ `rebuild_v106_db.py`). Phase 28: chạy chuỗi `build_cases.py`, `build_p16.py`, `build_p18.py`, `build_p19.py`, `build_p23.py` cho ra `cases.jsonl` (590 dòng) và `cases_p16_aside.jsonl` **giống từng byte** bản đang dùng.
- `run.py`, `baseline_adapter.py`, `selftest.py` (oracle phải 100%, "kẻ nói dối" bị bắt bịa).
- `results/baseline.json`, `results/baseline_stripped.json`, `BASELINE.md`.

## Đợt 3 / Phase 8: tách DEV - HOLDOUT, bộ chấm luật
- `cases.jsonl` mỗi câu có `split` (`dev`|`holdout`) và `source` (`synthetic-dev` | `holdout-real-style` | `holdout-varied`). 185 câu cũ = DEV, giữ nguyên lời. Dựng bằng `python build_cases.py` (gọi `cases_new.py` cho phần mới; assert mọi proc_id / condition_index với DB).
- DEV 209 = 185 + 24 (nhóm `rule_condition|rule_compare|rule_negation|rule_order`, mỗi nhóm 6). HOLDOUT 67 = 43 (9 nhóm + out_of_scope + typo) + 24 rule (mỗi nhóm 6). 44 câu HOLDOUT gắn `holdout-real-style` (sai chính tả, viết tắt, thiếu dấu, kể dài, kiểu nhắn tin).
- Bộ chấm luật `rules_scorer.py` (không LLM), dùng `expected.checks`: condition (câu trả lời có cụm khoá của mục `condition_index` đúng), compare (nhắc cả hai thủ tục; không có answer_text thì cả hai là top-1), negation / order (top-1 thuộc đáp án và không chọn mục bị cấm). Kết quả nằm ở `rule_kind/rule_ok/rule_detail` trong file results.
- `run.py` in bảng riêng DEV, HOLDOUT và bảng chênh lệch (top-1, top-3, hành vi, bịa số, 4 loại luật); `--split dev|holdout|all`. HOLDOUT chỉ để nghiệm thu: không chọn tham số/prompt theo HOLDOUT. `sweep.py` chỉ dùng split DEV (`--holdout` mới in thêm HOLDOUT).
- `EXPECTATIONS_REVIEW.md`: các đáp án giả định (clarify, chitchat, multi-intent > 3) chờ duyệt.
- Số đo: `results/dot3_p8_baseline.json` (baseline_adapter); kết quả của answer_adapter (`S3_USE_LLM=0`) ghi bằng `run.py --name <tên>` (file kết quả luật cũ của đợt 3 không còn trong repo). `results/baseline.json` đã tái dựng trên 185 câu gốc (số khớp BASELINE.md; latency ghi lại không đo lại).

## Bộ hội thoại ctx (context memory)
`cases_ctx.py` -> `cases_ctx.jsonl` (58 hội thoại `ctx-dev` + 33 `ctx-hold` viết sau khi ctx-dev chạy sạch, mỗi hội thoại 2-5 lượt, chấm lượt cuối). Nhóm: a hỏi tiếp thiếu chủ ngữ, b đổi mục, c thủ tục liên quan/khác hẳn, d sửa ý, e kể hoàn cảnh, f đại từ, g quay lại, h độc lập (không được kế thừa), i điều kiện. Chạy: `PYTHONPATH=.. S3_USE_LLM=0 python run_ctx.py --name x [--split ctx-dev|ctx-hold] [-v]`. Không nằm trong `cases.jsonl` nên `run.py --split all` không chạm.

## Các script khác (đợt 4–5)
| Script | Việc | Ghi chú |
|---|---|---|
| `perturb.py` | bộ biến đổi câu (11 loại nhiễu), gate bất biến ≥ 98% | `python perturb.py --name x`; xem docs/EVAL.md |
| `run_concise.py` | chỉ số concise/đúng trọng tâm (focus, task thừa) | gate DEV focus ≥ 95% |
| `run_ctx.py` | hội thoại nhiều lượt (ctx) | `--split ctx-p16|ctx-p23` chạy riêng |
| `synth_retrieval.py` | câu tự sinh từ DB (TRAIN/TEST-seed, biến thể `glued`) | ~3 phút; ghi log vào `results/synth.txt` nếu muốn `check_docs.py` kiểm |
| `run_pseudo.py`, `run_team.py` | bộ mù pseudo_real/HOLDOUT-4 và bộ team | chỉ người điều phối chạy (không xem từng ca khi sửa) |
| `build_p16.py`, `build_p18.py`, `build_p19.py`, `build_p23.py` | nối ca p16/p18/p19/p23 vào `cases.jsonl` (idempotent) | `build_p16.py` còn ghi `cases_p16_aside.jsonl` (chạy bằng `run.py --split p16aside`) |
| `build_p26.py`, `run_p26.py` | Phase 26: bộ ca bộ nhớ người dùng (`cases_p26.jsonl`, KHÔNG nằm trong `cases.jsonl` nên gate DEV cũ không lẫn) và bộ chạy có/không hồ sơ | `python run_p26.py`; số trước/sau trong `P26_REPORT.md` |
| `build_composer_set.py`, `composer_own.py`, `score_composer.py`, `p27_e2e.py` | Phase 27: bộ chấm riêng cho bước sinh chữ (Answer Composer): chọn 63 ca có bước LLM (`cases_composer.jsonl`: 50 từ DEV/ctx + 13 tự soạn, dễ hơn câu thật), chấm BẬT vs TẮT bằng luật (đủ ý, đúng số, không đảo nghĩa, không bịa cơ quan/văn bản, độ dài), xuất mẫu 20 ca cho người chấm (`results/composer_sample20.md`), và độ trễ đầu-cuối qua `/chat` | **cần Ollama** (là phase duy nhất bật LLM); `python score_composer.py --name x --sample`, `python p27_e2e.py`; kết quả `results/composer_*.json`, `results/p27on/`, `results/p27off/`; xem `P27_REPORT.md` |
| `build_p30.py`, `run_p30.py`, `p30_composer_trigger.py` | Phase 30: bộ ca "hỏi lại khi mơ hồ vs trả lời khi một thủ tục rõ" tự soạn từ DB (`cases_p30.jsonl`, nửa `tune`/`held` + lô `fresh`; KHÔNG vào `cases.jsonl`), bộ chạy đo clarify recall / hỏi thừa, và đếm số lượt gọi bước LLM sinh chữ vì điều kiện | `python run_server.py eval/run_p30.py [--split tune|held|fresh|all]` (mặc định chỉ tune); `eval/p30_composer_trigger.py`; xem `P30_REPORT.md` |
| `build_p31.py`, `run_p31.py` | Phase 31: bộ ca "tên chung họ thủ tục có >= 3 dạng thật -> hỏi lại" tự soạn từ DB (`cases_p31.jsonl` nửa `tune`/`held`; `build_p31.py --fresh` ghi `cases_p31_fresh.jsonl`, lô viết sau khi chỉnh, chạy một lần; KHÔNG vào `cases.jsonl`), bộ chạy đo clarify recall / thẻ đủ dạng / hỏi thừa / top-1 (có hồ sơ Phase 26 và hội thoại nhiều lượt) | `python run_server.py eval/run_p31.py [--split tune|held|fresh|all] [--file cases_p31_fresh.jsonl]` (mặc định chỉ tune; held/fresh không in danh sách lỗi); xem `P31_REPORT.md` |
| **`check_docs.py`** | kiểm tài liệu: số trong README so với `results/`, file/lệnh nhắc tới có tồn tại, test có trong SETUP/CONTRIBUTING, thẻ `FINAL-PRODUCT:` có trong checklist | `python eval/check_docs.py`, exit 0 = sạch; **thuộc danh sách gate** (docs/CONTRIBUTING.md) |
| `P18_REPORT.md` … `P31_REPORT.md` | báo cáo từng phase | P24: dọn mâu thuẫn tài liệu, launcher, check_docs; P26: bộ nhớ người dùng; P27: đo bước sinh chữ bật/tắt; P30: hỏi lại khi mơ hồ + điều kiện phải thêm thông tin; P31: hỏi lại khi tên chung có nhiều dạng thật |

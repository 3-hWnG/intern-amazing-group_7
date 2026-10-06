# Báo cáo Phase 19 — Planner hybrid luật + Qwen3-4B (2026-10-06)

**Kết luận: gate KHÔNG đạt. Mặc định giữ `S3_PLANNER_MODE=rules`; hybrid là tuỳ chọn (công tắc + trace đã sẵn).** Đo công bằng với timeout 7 s: 0% lần gọi quá hạn, độ trễ Planner p50 ~1,6-2,1 s, p95 ~2,5-4,2 s. Nghĩa là kết luận cũ "LLM không giúp Planner" KHÔNG phải do nhiễu timeout 2,5 s: với 7 s LLM vẫn không giúp, và ở mọi ngưỡng 0,80-0,99 không có lần sửa nào được chấp nhận mà làm đúng hơn đáp án (0 "đúng hơn", 20-80 "sai đi" tuỳ ngưỡng ở biến thể độc lập).
Không đọc/chạy `cases_h3`, `cases_h2`, `cases_team`, `cases_pseudo_real`, giả định/kết quả của chúng. Gate cuối chạy `run_concise.py` đầy đủ (có team/pseudo_real, chỉ in số tổng, không xem từng ca); đo hybrid dùng `run_concise.py --no-blind` nên không đưa bộ nghiệm thu qua LLM. Ngưỡng chọn chỉ trên DEV.

## Đã làm
1. **Nhóm lỗi chung nhỏ (trước khi đo):** (G) "thời gian giải quyết / giải quyết trong bao lâu / bao lâu giải quyết [thế nào]" chỉ là `processing_time` (trước: cụm "thế nào/như thế nào" kích hoạt thêm `steps`; sửa ở `retrieval/query.py::_tidy_fields`, chỉ giữ `steps` khi có cụm bước/quy trình/cách thực hiện tường minh). (H) "nếu X thì tôi cần làm gì" (không nêu mục) trả `components` + điều kiện, không còn `steps`, không tách task thứ hai (`retrieval/rank.py::_cond_steps`, dùng cả ở `_cond_fields` lẫn nhánh hỏi tiếp "còn nếu ... thì ..."). Ca kiểm: `eval/build_p19.py` (17 ca `p19-*`, split dev, câu tự nghĩ; 17/17 đạt). Số hồi quy không đổi (DEV cũ y hệt P18).
2. **Planner hybrid:** `server/planner/hybrid.py` (mới), `planner.py` (`_hybrid`, `_cand_list`, `Plan.llm_trace`), `prompt.py` (`HYBRID_SYSTEM`, biến thể bản nháp), `schema.py` (`HYBRID_SCHEMA` gọn), `config.py`, `core/llm.py` (`loaded_models`), `orchestrator.py` (`trace["planner_llm"]`), `main.py` (`GET/POST /config`).
   - Luật luôn dựng kế hoạch trước. LLM (think=False) chọn ứng viên bằng chỉ số `cand` (không tự đưa mã thủ tục/số), trả `tasks[{action,cand,fields}] + confidence`, trong thread với hạn cứng `PLANNER_LLM_TIMEOUT`=7 s (+0,5 s đệm; httpx cũng timeout).
   - Hợp nhất (`diff` + `merge`): bốn loại thay đổi `edit_fields | edit_proc | add_task | delete_task`. Chỉ nhận khi `confidence >= PLANNER_LLM_CONFIDENCE` VÀ thủ tục có trong kho (active), field thuộc `FIELD_TITLE` (không rỗng khi luật đã bắt mục, <= 4 mục), task luật không bị khoá (xin lỗi/ngoài phạm vi/chitchat, `uncertain`/`ambiguous`/`near`, so sánh, thủ tục kế thừa ngữ cảnh), và chạy thử `policy.check` cho cùng hành vi + task bị sửa vẫn `direct` (không bỏ clarify/apologize do luật/Policy). Hạn/lỗi/JSON hỏng -> giữ luật. Policy vẫn chạy sau cùng (orchestrator không đổi luồng).
   - Trace `planner_llm`: mode, gọi hay không (+lý do bỏ qua), ms, timeout, lỗi, cached, confidence, ngưỡng, `llm_tasks`, `proposals[{op, từ, đến, accepted, reason}]`, `decision` (none/accepted/partial/rejected), `rule_plan`, `final_plan`. Hiện trong dev panel (`?dev=1`, JSON nguyên).
   - Công tắc: `S3_PLANNER_MODE=rules|hybrid` (mặc định rules), `PLANNER_LLM_TIMEOUT` (7.0), `PLANNER_LLM_CONFIDENCE` (0.99), `PLANNER_LLM_DRAFT` (0), `PLANNER_LLM_NUM_PREDICT` (220). `GET /config` -> mode, timeout, confidence, draft, model, `loaded` (Ollama `ps`), dev; `POST /config {mode,confidence,timeout}` đổi trong bộ nhớ, chỉ khi `S3_DEV=1` (403 nếu không, 422 giá trị sai). Đã thử bằng TestClient.
   - Thiết kế "song song": không có bước độc lập đáng kể giữa Planner và Policy (Policy cần kế hoạch cuối), nên chờ đồng bộ trong Planner (thread chỉ để hết hạn theo đồng hồ thật). `# ponytail` ghi trong code; nâng cấp: bắt đầu LLM ngay sau `resolve` và làm việc phụ trong lúc chờ.
3. **Đo:** `answer_adapter` thêm `extra.llm`; `run_ctx.py` ghi `llm`; `run_concise.py --no-blind`; `p19_compare.py` (bảng so sánh); `S3_PLANNER_LLM_CACHE` (phát lại đề xuất LLM để quét ngưỡng không gọi lại, độ trễ cộng lại từ giá trị đã đo; chỉ cho đo). Test `server/tests/planner_hybrid_test.py` (LLM giả): đề xuất sai/ngưỡng thấp/field lạ/chỉ số ngoài danh sách/timeout/lỗi/JSON hỏng/ngoài phạm vi/hỏi lại -> giữ luật; đề xuất đúng + confidence cao -> chấp nhận; đổi ngưỡng trong bộ nhớ có tác dụng ngay; `set_config` kiểm giá trị.

## Số đo (cùng bộ DEV 449 ca = 209 cũ + p16/p18/p19; ctx 91; concise; `S3_USE_LLM=0`)
Hai biến thể hybrid: **độc lập** (LLM sinh kế hoạch từ câu hỏi + ứng viên, đúng thiết kế) và **bản nháp** (LLM thấy kế hoạch luật, chỉ sửa khi chắc nó sai; `PLANNER_LLM_DRAFT=1`). Mỗi biến thể 625 lần gọi LLM thật (lần đầu), các ngưỡng phát lại từ cache.

**DEV cũ 209 (id không p16/p18/p19) và ctx 91**
| cấu hình | top-1 | hành vi | fields | bịa số | multi-intent top-1 | p50 / p95 ms | timeout | ctx top-1 / fields | DEV focus / task thừa |
|---|---|---|---|---|---|---|---|---|---|
| **rules** | 96,3% (158/164) | 97,6% | 96,8% | 0,0% | 93,3% | 21 / 49 | - | 89/91 / 30/31 | 99% / 0 |
| độc lập 0,80 | 89,0% | 97,6% | 79,7% | 0,5% | 73,3% | 1832 / 3468 | 0,0% | 87/91 / 28/31 | 76% / 55 |
| độc lập 0,90 | 89,0% | 97,6% | 79,7% | 0,5% | 73,3% | 1838 / 3475 | 0,0% | 87/91 / 28/31 | 76% / 55 |
| độc lập 0,95 | 89,6% | 97,6% | 80,4% | 0,5% | 73,3% | 1832 / 3470 | 0,0% | 87/91 / 28/31 | 77% / 51 |
| độc lập 0,99 | 92,1% | 97,6% | 88,6% | 0,5% | 86,7% | 1832 / 3470 | 0,0% | 87/91 / 28/31 | 89% / 17 |
| bản nháp 0,80-0,95 | 96,3% | 97,6% | 92,4% | 0,0% | 93,3% | 1636 / 2693 | 0,0% | 89/91 / 30/31 | 93% / 15 |
| bản nháp 0,99 | 96,3% | 97,6% | 94,3% | 0,0% | 93,3% | 1638 / 2698 | 0,0% | 89/91 / 30/31 | 94% / 10 |

Trên DEV đầy đủ (449 ca): rules top-1 97,4% / fields 92,8%; độc lập 0,99 top-1 93,4% / fields 85,2% / bịa 1,2%; bản nháp 0,99 top-1 97,4% / fields 91,5%. HOLDOUT cũ (chỉ theo dõi, không dùng chọn ngưỡng): rules top-1 98,2% / fields 94,0%; độc lập 0,99 96,4% / 80,8%; bản nháp 92,0% fields.

**Đề xuất của LLM so với đáp án (ok = top-1 + hành vi + fields + không bịa; so với bản rules cùng ca, DEV cũ 209)**
| cấu hình | ca có đề xuất sửa | đề xuất | được chấp nhận | ca được nhận | nhận -> đúng hơn | nhận -> sai đi | nhận -> không đổi |
|---|---|---|---|---|---|---|---|
| độc lập 0,80 / 0,90 | 105 | 142 | 47 | 38 | 0 | 37 | 1 |
| độc lập 0,95 | 105 | 142 | 43 | 36 | 0 | 35 | 1 |
| độc lập 0,99 | 105 | 142 | 23 | 21 | 0 | 20 | 1 |
| bản nháp 0,80-0,95 | 25 | 33 | 20 | 13 | 0 | 7 | 6 |
| bản nháp 0,99 | 25 | 33 | 14 | 9 | 0 | 4 | 5 |
(Trên 449 ca DEV: độc lập 0,99 nhận 50 đề xuất, 0 đúng hơn / 38 sai đi; bản nháp 0,99 nhận 18, 0 / 4.) Theo loại ở ngưỡng 0,99 (độc lập): `add_task` sai 10, `edit_proc` sai 15, `edit_fields` sai 10, không loại nào đúng hơn. LLM không bao giờ đề xuất `delete_task` (ví dụ điển hình "không phải multi-intent").
Gốc lỗi quan sát: (1) confidence tự báo vô dụng: 409/625 câu 0,99; 155 câu 0,95; chỉ 33 câu < 0,95, kể cả khi sai; (2) LLM thêm ý thứ hai từ lời kể hoàn cảnh ("bà nội mất rồi, làm giấy khai tử ...") và đổi `kết hôn` -> `đăng ký lại kết hôn` / `thường trú` <-> `tạm trú`; (3) liệt kê mục khác luật (luật bắt cụm hỏi đáng tin hơn); (4) 28/625 JSON bị cắt (json_empty) ở bản độc lập, 0 ở bản nháp.

**Ngưỡng chọn trên DEV: 0,99** (ít hại nhất ở cả hai biến thể; ngưỡng thấp hơn tụt thêm). Không ngưỡng nào đạt gate nên đây chỉ là mặc định cho chế độ tuỳ chọn.

## Gate
| điều kiện | kết quả |
|---|---|
| hybrid tăng >= 2 điểm top-1/hành vi/focus trên DEV cũ + ctx | **KHÔNG**: top-1 -7,3 đến 0 điểm, hành vi 0, focus -5 đến -23 điểm, ctx 0 đến -2 ca |
| không tăng bịa số | độc lập: 0,0% -> 0,5%; bản nháp: giữ 0,0% |
| không tụt gate hồi quy | tụt (độc lập: top-1 DEV cũ 92,1% < 95%; DEV focus 89% < 95%; ctx 87/91 < 89) |
| timeout < 10% | đạt (0,0%) |
=> Giữ `rules` mặc định, hybrid tuỳ chọn. Độ trễ khi bật (độc lập 0,99, `S3_USE_LLM=1`, 57 ca điều kiện/so sánh/multi-intent có bước LLM sinh chữ): p50 3,2 s, p95 7,4 s, max 9,8 s (<= 10 s).

## Hồi quy chế độ rules mặc định (sau mọi thay đổi; `S3_USE_LLM=0`)
DEV cũ 209: top-1 96,3% (158/164, yêu cầu >= 95%), hành vi 97,6% (>= 96%), bịa số 0,0% (<= 3%), ngoài phạm vi 30/30; ctx 89/91; synth TRAIN 96,3% / TEST 96,3% (>= 94%); concise DEV focus 99% (284/288), HOLDOUT cũ 96%, task thừa DEV 0/377; ca p19 17/17; selftest OK; `test_data`, `memory_test`, `context_test`, `answer_llm_test`, `planner_hybrid_test`, `smoke_test` xanh. team/pseudo_real (số tổng do `run_concise` in, không xem từng ca): task thừa 1/8 và 1/16, như P18.

## Giới hạn / việc tiếp
- Chưa thử model Planner lớn hơn hoặc hiệu chỉnh confidence (vd. lấy xác suất token); có thể thử lại bằng cùng cơ chế + `p19_compare.py`.
- Thử thêm bản nháp + cấm `add_task`/`edit_proc` chỉ còn `delete_task`: chưa làm vì LLM không hề đề xuất xoá task nên không có gì để nhận.
- Số hybrid trên DEV có thể phần nào đã so với luật đã tune trên DEV; HOLDOUT cũ cho cùng kết luận. Chưa chạy trên HOLDOUT-3/pseudo_real/team (người điều phối).

## File đổi
Mã: `server/planner/hybrid.py` (mới), `server/planner/{planner,prompt,schema}.py`, `server/config.py`, `server/core/llm.py`, `server/orchestrator.py`, `server/main.py`, `retrieval/query.py`, `retrieval/rank.py`.
Test/eval: `server/tests/planner_hybrid_test.py` (mới), `eval/build_p19.py` (mới), `eval/p19_compare.py` (mới), `eval/answer_adapter.py`, `eval/run_ctx.py`, `eval/run_concise.py`, `eval/cases.jsonl` (+17 ca `p19-*`), `eval/results/p19_*.json|log|jsonl` (kết quả đo; `p19_cache_{ind,drf}.jsonl` = đề xuất LLM đã ghi).
Tài liệu: `README.md`, `docs/ARCHITECTURE.md`, `docs/SETUP.md`, `docs/EVAL.md`, `docs/CONTRIBUTING.md`, `docs/PLAN_SYSTEM3_DOT4.md`, `eval/P19_REPORT.md`.
Tái lập: `cd eval && PYTHONPATH=<gốc> S3_USE_LLM=0 S3_PLANNER_MODE=hybrid S3_PLANNER_LLM_CACHE=results/p19_cache_ind.jsonl PLANNER_LLM_CONFIDENCE=0.99 python run.py --adapter answer_adapter:adapter --name x --split all` (cache có sẵn nên không cần Ollama); thêm `PLANNER_LLM_DRAFT=1` + `p19_cache_drf.jsonl` cho biến thể bản nháp.

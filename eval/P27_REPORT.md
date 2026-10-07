# Phase 27 — Bước sinh chữ (Answer Composer): bật mặc định, đo giá trị thật (B6)

2026-10-07. Đây là phase duy nhất bật LLM: `S3_USE_LLM=1` (mặc định), `S3_PLANNER_MODE=rules` (không bật hybrid). Máy: GTX 1660 SUPER 6 GB (không phải RTX), qwen3:4b qua Ollama 0.30, **GPU dùng chung với ứng dụng khác nên độ trễ dao động**. Chạy tuần tự, 1 worker, không song song. Cuối phase: `ollama stop qwen3:4b`, `ollama ps` trống. Không đụng `repo/`, `retrieval/*`, `data/*`, planner luật, policy, bộ mù/team, `PLAN_*.md`, các file của Phase 28.

## 1. Bước sinh chữ chạy thế nào, kích hoạt bao nhiêu
- `answerer.answer()` gọi `llm_answer.compose()` ở hai chỗ: (1) task có `conditions` (giải thích điều kiện, đoạn dữ liệu + 8 mục `condition_index`), (2) >= 2 task có `relation=compare` (khối "So sánh"). LLM trả `{points:[{text,cites}]}`; code bỏ ý không có cites hợp lệ hoặc vi phạm `verify_point` (số, tên/số hiệu văn bản, "miễn phí" phải có trong đoạn được trích). Lỗi/timeout/hết ý -> `[]` -> giữ bản code.
- Kích hoạt (dò bằng LLM giả, không gọi Ollama): **46/523 ca DEV (8,8%; 25/209 DEV cũ), 4/144 ca ctx (2,8%), 0/92 ca p26**. 63 ca của bộ chấm = 46 DEV + 4 ctx + 13 tự soạn.
- Chỉ **23/63** ca có điều kiện do người dùng nêu (có mục `condition_index` khớp chữ của câu hỏi); **40/63** kích hoạt vì Planner tự gán `conditions` (mục trùng chữ với tên thủ tục, ví dụ "Lệ phí đăng ký thường trú là bao nhiêu?" -> điều kiện "đăng ký thường trú tại cơ sở tín ngưỡng"). Ở các ca đó bản code in một điều kiện lạc đề, LLM thì trả lời câu hỏi gốc.

## 2. Bộ chấm riêng (mới)
`eval/build_composer_set.py` (+ `composer_own.py`) -> `cases_composer.jsonl` (63 ca); `eval/score_composer.py` chạy mỗi ca TẮT và BẬT, chấm bằng luật (a) đủ ý, (b) không sai số, (c) không đảo nghĩa (cặp có/không, được/không được, phải/không phải, cần/không cần, bắt buộc/không bắt buộc, so với câu nguồn gần nhất), (d) không bịa cơ quan/văn bản/số hiệu, (e) độ dài (phần sinh chữ <= 1000 ký tự, mỗi ý <= 300, không tính "(theo: ...)"). `p27_e2e.py`: độ trễ qua `/chat` (server tạm, cấu hình mặc định). Mô tả đầy đủ: `docs/EVAL.md`.

**Ca tự soạn dễ hơn câu thật**: 13 ca (`own-*`) do tác giả phase viết sau khi biết bước LLM chạy khi nào, nêu điều kiện/so sánh rõ ràng, vài ca (`own-d*`) dựng từ chính chữ của `condition_index`. Phải đọc số đo với 50 ca có sẵn là chính (46 DEV + 4 ctx); không có câu hỏi thật. Nhắc thêm: tiêu chí (e) là tiêu chí **bản code yếu nhất** (code chép nguyên văn mục điều kiện nên dài), nên "đạt cả 5" nghiêng về bật; tiêu chí (a)–(d) mới là phần LLM có thể làm hỏng.

## 3. Giảm chạm timeout (đo trước/sau từng bước; cùng 63 ca, timeout 7 s, BẬT)
Mỗi dòng là một lần chạy duy nhất; GPU chia sẻ nên p50/p95 của cùng cấu hình dao động ~2 lần (v0 chạy hai lần: lần 1 8/64 timeout, p50 4,1 s; lần 2 3/64, p50 2,8 s). Vì vậy chỉ kết luận được: đổi này không làm hại, và `num_predict` là trần cứng theo token.

| Bản | Thay đổi | timeout/lượt gọi | p50 / p95 lượt gọi | đạt cả 5 BẬT | BẬT tệ hơn TẮT | giữ? |
|---|---|---|---|---|---|---|
| v0 | cấu hình cũ (prompt dài 3 ý/2 câu, đoạn 700 ký tự, không giới hạn token) | 8/64 (lần 1), 3/64 (lần 2) | 4,1/7,0 s; 2,8/6,3 s | 47/63 (75%) | 9 | (gốc) |
| v1 | + `num_predict=200` | 0/64 | 2,7/4,4 s | 49/63 (78%) | 6 | giữ |
| v2 | + đoạn 450 ký tự | 3/64 | 3,3/6,6 s | 49/63 (78%) | 6 | giữ (không thấy lợi rõ về giờ; prompt ngắn hơn) |
| v3 | + prompt rút gọn "tối đa 4 ý, mỗi ý MỘT câu < 30 từ" | 4/64 | 3,6/7,0 s | 56/63 (89%) | 1 | giữ (chất lượng; số ý tăng nên chậm hơn) |
| v4 | prompt "tối đa 3 ý", `num_predict=160` | 2/64 | 3,4/6,9 s | 54/63 (86%) | 2 | bỏ (160 token cắt JSON) |
| v5 | prompt "tối đa 3 ý", `num_predict=200`, đoạn 450 | **0/64** | **1,9/3,4 s** | 58/63 (92%) | 1 | **chọn** |

`think` đã tắt sẵn (`LLM_THINK=False`, `think=False` truyền cho Ollama) nên không có gì để đổi. Trong 12 đoạn đo trực tiếp: sinh token chiếm phần lớn thời gian (36–344 token, ~10–20 ms/token), nạp prompt 0,2–3,5 s tuỳ độ bận GPU; vì thế giới hạn đầu ra và nhắc "một câu ngắn" có tác dụng hơn cắt đầu vào.

Hai thay đổi an toàn thêm sau khi phát hiện hai chế độ lỗi (đều có test trong `server/tests/answer_llm_test.py`):
1. **Model nguội**: sau `ollama stop` lượt đầu timeout 7,0 s và lượt kế cũng timeout (nạp > 14 s). Nay `llm_answer._ready()` dò `/api/ps` (cache 5 s): chưa nạp thì trả bản code **ngay** (35–360 ms thay vì 7 s) và nạp model ở nền cho lượt sau.
2. **Trần chung của lượt** `ANSWER_LLM_TURN_BUDGET` = 9 s (`llm_answer.budgeted`, gọi trong `answer()`): một lượt có thể gọi LLM 3 lần (điều kiện từng task + so sánh) = 21 s nếu mỗi lần chạm 7 s. Thực tế bộ 63 ca chỉ có 1 ca gọi 2 lần nên chưa từng chạm trần.

Chế độ lỗi đã kiểm: Ollama tắt (cổng đóng): `compose` trả `[]` trong < 5 s, test không đụng GPU; timeout: 4–8 lượt/64 ở các bản cũ đều rơi về bản code, câu trả lời vẫn đủ và đúng; model nguội: rơi về bản code ngay. Chưa kiểm: Ollama trả byte nhỏ giọt (timeout httpx tính theo từng lần đọc, không phải đồng hồ tổng); chưa thấy trường hợp này (max 7,07 s ở mọi lần đo), và `ANSWER_LLM_TURN_BUDGET` chỉ cắt giữa các lần gọi chứ không cắt trong một lần gọi.

## 4. Bảng BẬT vs TẮT trên bộ chấm riêng (bản cuối `results/composer_final3.json`)
| tiêu chí | TẮT (code) | BẬT |
|---|---|---|
| (a) đủ ý (n=23 ca có điều kiện người dùng nêu; 40 ca "n/a") | 22/23 | 22/23 |
| (b) không sai số | 63/63 | 63/63 |
| (c) không đảo nghĩa | 63/63 | 63/63 |
| (d) không bịa cơ quan/văn bản | 62/63 | 62/63 |
| (e) độ dài hợp lý | 47/63 | 61/63 |
| **đạt cả 5** | 45/63 (71%) | **59/63 (94%)** |

(d): 1 ca (`multi_intent-04`) trượt ở CẢ HAI bản vì regex tên văn bản bắt nhầm cụm "luật buộc" trong câu thường (dương tính giả của bộ chấm, không phải do LLM). BẬT **tệ hơn** TẮT ở 1 ca (`p23-p23_L2-15`, ý dài 367 ký tự > 300), **tốt hơn** ở 15 ca (đều là tiêu chí e). Theo loại: condition 48 ca (đạt cả 5: 30 -> 44, tệ hơn 1), compare 16 ca (16 -> 16, tệ hơn 0, 15/16 ca LLM tạo được khối "So sánh"). Theo nguồn: composer (tự soạn) tệ hơn 0, DEV 1, ctx 0.
Lượt gọi LLM: 64, **timeout 0 (0%)**; p50 1,76 s, p95 3,09 s, max 4,55 s. Verifier loại 6/104 ý đề xuất (6%): chặn được, không có ý sai số nào lọt. Bản BẬT khác bản TẮT ở 61/63 ca.
Một lần đo khác cùng prompt/`num_predict` (trước thêm trần lượt, `final2`): timeout 4/64 (6%), p50 3,7 s, p95 7,0 s lúc GPU bận; vẫn < 10%.

**Điều số đo KHÔNG nói được**: BẬT có hữu ích hơn không. Các tiêu chí luật (a)–(d) bằng nhau (verifier + dữ liệu đã đủ giữ BẬT đúng), phần hơn là độ ngắn. Đọc 20 ca mẫu bằng mắt (người chấm chưa chấm; tôi không điền điểm): ở các điều kiện người dùng nêu thật, BẬT thường chép lại ý của mục điều kiện cho gọn; ở điều kiện Planner gán nhầm, BẬT trả lời đúng câu hỏi hơn bản code; ở so sánh, BẬT liệt kê dữ kiện từng thủ tục kèm trích dẫn, chưa nói rõ điểm khác nhau, và có ý chung chung ("cả hai đều yêu cầu nộp lệ phí nếu thuộc trường hợp phải nộp"). Mẫu 20 ca: `eval/results/composer_sample20.md` (seed 27, bản tắt/bật/nguồn, ô điểm để trống).

## 5. Hồi quy đầy đủ: BẬT so với TẮT (cùng mã, `results/p27on/`, `results/p27off/`)
| Chỉ số | Gate | TẮT | BẬT |
|---|---|---|---|
| DEV cũ 209 top-1 | >= 95% | 97,0% (159/164) | 97,0% (159/164) |
| DEV cũ 209 đúng hành vi | >= 96% | 97,6% (204/209) | 97,6% (204/209) |
| DEV cũ 209 bịa số | <= 3% | 0,0% (0/205) | 0,0% (0/205) |
| ngoài phạm vi (DEV) | 30/30 | 30/30 | 30/30 |
| DEV 523: top-1 / hành vi / bịa số | - | 446/455 / 513/523 / 2/500 | 446/455 / 513/523 / 2/500 |
| luật condition / compare (trả lời chứa cụm khoá) | - | 100% / 100% | 100% / 100% |
| "không công bố" / trích nguồn / fields | - | 4/7 / 36/37 / 395/420 | 4/7 / 36/37 / 395/420 |
| HOLDOUT cũ 67 top-1 / hành vi | - | 98,2% / 95,5% | 98,2% / 95,5% |
| ctx 91 / ctx-p23 | >= 89/91 / 26/26 | 89/91 / 26/26 | 89/91 / 26/26 |
| DEV focus (`run_concise.py --no-blind`) | >= 95% | 99% (349/353) | 99% (349/353) |
| task thừa | <= 2% | 0/451 | 0/451 |
| `cases_p26.jsonl` | 92/92 | 92/92 | 92/92 |
| `perturb.py` bất biến | >= 98% | 99,44% (7056/7096) | 99,44% (7056/7096) * |
| synth TEST-seed top-1 (`glued`) | >= 94% (90%) | 96,4% (96,1%) | không chạy (không qua bước sinh chữ) |
| `selftest.py` | oracle 100% | OK | OK |
| test server (data, memory, context, answer_llm, p20_api, p23_input, p26_memory) | xanh | xanh | xanh |
| `planner_hybrid_test`, `smoke_test` | xanh | xanh | không chạy ở BẬT (smoke tự ép `S3_USE_LLM=0`; hybrid_test không liên quan) |
| `check_docs.py` | sạch | sạch | - |

\* `perturb.py` BẬT chạy ở bản trước khi thêm `_ready()` và trần lượt (bản này chỉ thêm kiểm model nạp/trần thời gian; chạy lại mất ~25 phút GPU nên không lặp); file `results/p27on/perturb_pre_ready.json`. Bản TẮT chạy lại trên mã cuối.
Số tắt khớp số cũ trong README/EVAL (không có chỉ số nào đổi). Độ trễ adapter trên cả 590 ca DEV+HOLDOUT cũ: TẮT p50 21 ms, p95 43 ms, max 335 ms; BẬT p50 22 ms, p95 1,78 s, max 3,6 s (chỉ ~9% ca gọi LLM).

## 6. Độ trễ tổng đầu-cuối qua `/chat` (cấu hình mặc định, không đặt `S3_USE_LLM`; `results/p27_e2e_run1..3.json`)
Xác nhận `/config`: `answer_llm=true`, `answer_timeout=7.0`, model nạp sẵn bởi warm-up. Tuần tự 63 ca có LLM + 150 ca DEV một lượt không kích hoạt LLM:
| Lần | ca có LLM p50 / p95 / max | lượt rơi về bản code | 150 ca DEV khác p95 |
|---|---|---|---|
| run1 (trước `_ready`/trần lượt) | 2,0 / 3,5 / 5,5 s | 0/63 | - |
| run2 (GPU bận) | 2,3 / 4,8 / **7,4 s** | 1/63 | 0,12 s |
| run3 (bản cuối) | 1,9 / 3,4 / 5,0 s | 1/63 (1,6%) | 0,10 s |
**p95 tổng <= 10 s** (tệ nhất 4,8 s) và **tỉ lệ timeout < 10%** (0–6% theo lần đo; lượt rơi về bản code 0–1,6%). Cả hai điều kiện gate đạt.

## 7. Công tắc và mặc định
Không đổi mặc định: `S3_USE_LLM` không đặt = bật (`orchestrator._answer_llm`, `main._llm_wanted`, `/config.answer_llm` đều mặc định "1"); `S3_USE_LLM=0` tắt hẳn (không nạp model, không gọi Ollama); `POST /config {answer_llm}` vẫn hoạt động (kiểm trong `p20_api_test`). Tôi **không tắt** gì; theo quyết định nhóm là bật.

## 8. Kết luận và đề xuất (thẳng)
- Gate **đạt**: bật không làm tụt chỉ số hồi quy nào; p95 tổng <= 10 s; timeout < 10%; có bảng so sánh.
- Giá trị thật **chưa chứng minh**: luật chỉ cho thấy BẬT không hại và ngắn gọn hơn. Đề xuất **giữ bật** (không có hại đo được, rơi về code an toàn) nhưng ghi rõ trong tài liệu là "chưa chứng minh có ích" cho tới khi người chấm 20 ca xong; nếu người chấm cho điểm BẬT <= TẮT thì tắt cho điều kiện lạc đề và chỉ giữ cho so sánh/điều kiện người dùng nêu.
- Cải thiện đáng làm (không làm trong phase này vì thuộc Planner luật, bị cấm đổi): 40/63 ca kích hoạt vì điều kiện Planner gán nhầm; chặn gán `conditions` khi chữ của mục `condition_index` không có trong câu hỏi sẽ bỏ ~2 s thừa ở ~60% ca và tránh điều kiện lạc đề trong bản code.

## 9. Chưa làm được
- Người chấm 20 ca (cố ý để trống). Chưa có câu hỏi thật để biết tỉ lệ kích hoạt ngoài đời.
- Không có bộ chấm "hữu ích hơn"; tiêu chí luật bắt đảo có/không chỉ theo cặp từ cố định.
- `perturb.py` BẬT chưa chạy lại trên mã cuối; `synth_retrieval.py` không chạy ở BẬT.
- Chưa kiểm UI trình duyệt với LLM bật (chỉ `/chat`).
- Độ trễ chịu nhiễu GPU dùng chung nên không so được p50/p95 giữa các bản prompt ở mức vài chục phần trăm.
- Phát hiện (không phải lỗi sản phẩm): lần đầu `p27_e2e.py` treo vì tôi nối `stdout` của server vào `PIPE` mà không đọc, đầy bộ đệm thì server kẹt khi ghi log. `server/e2e_test.py` có cùng kiểu (5 lượt, chưa đủ để đầy bộ đệm) nhưng sẽ treo nếu chạy dài; chưa sửa.

## 10. File đổi / mới
Mới: `eval/build_composer_set.py`, `eval/composer_own.py`, `eval/score_composer.py`, `eval/p27_e2e.py`, `eval/cases_composer.jsonl`, `eval/P27_REPORT.md`, `eval/results/composer_final3.json|txt`, `composer_v0..v5.json|txt`, `composer_base7.txt`, `composer_sample20.md`, `p27_e2e_run1..3.json`, `p27on/`, `p27off/`, `perturb_p27off_x.json`.
Đổi: `server/answer/llm_answer.py` (prompt ngắn, `num_predict`, `PASSAGE_CHARS`, `_ready`, `budgeted`), `server/answer/answerer.py` (1 dòng `llm = budgeted(llm)` + import), `server/config.py` (`ANSWER_LLM_NUM_PREDICT`, `ANSWER_LLM_PASSAGE_CHARS`, `ANSWER_LLM_TURN_BUDGET`), `server/tests/answer_llm_test.py` (tham số gửi LLM, Ollama tắt, trần lượt), `eval/check_docs.py` (kiểm số bước sinh chữ), `README.md`, `docs/ARCHITECTURE.md`, `docs/EVAL.md`, `docs/KNOWN_ISSUES.md`, `docs/SETUP.md`, `docs/CONTRIBUTING.md`, `docs/BAO_CAO_DOT4.md`, `eval/README.md` (Edit nhỏ; không đụng `eval/vendor_v106/`, `rebuild_v106_db.py`, `run_all.py`, `REPRODUCE.md`).
Tái lập: `cd eval && PYTHONPATH=<ROOT> S3_PLANNER_MODE=rules python score_composer.py --name x --sample` (cần Ollama), `python p27_e2e.py`; hồi quy BẬT: các lệnh trong `docs/CONTRIBUTING.md` với `S3_USE_LLM=1` thay `0`.

# Tóm tắt thay đổi — đợt 1 đến 6 (2026-10-05 → 2026-10-08)

Dùng để đưa các sửa đổi vào nhánh sản phẩm cuối. Phần A là lịch sử các lần feedback trước (đợt 1–4); phần B là đợt 5–6 (feedback lần 3 và hai phase đo thêm). Số mục 1–10 ở phần B giữ nguyên. Mỗi mục: lỗi từ feedback, sửa gì, file nào, kiểm bằng gì. Chi tiết số đo ở `eval/P23_REPORT.md` … `P31_REPORT.md`; plan ở `PLAN_SYSTEM3_DOT5.md`, `PLAN_SYSTEM3_DOT6.md`.

# Phần A — Các lần feedback trước (đợt 1–4)

Nguồn: `System-3-Feedback-lan-1.pdf`, `System-3-Feedback-lan-2.pdf`, slide kiến trúc G7, bộ test 10 câu của các team (`eval/cases_team.json`). Plan gốc: `PLAN_SYSTEM3.md`, `PLAN_SYSTEM3_DOT3.md`, `PLAN_SYSTEM3_DOT4.md`; báo cáo: `BAO_CAO_DOT4.md`, `docs/report daily/5_10_2026.md`, `6_10_2026.md`, `eval/P18_REPORT.md` … `P20_REPORT.md`.

## A1. Đợt 1–2 (Phase 0–6): dựng System 3 từ đầu (2026-10-05)
Không phải sửa lỗi mà là nền để mọi sửa đổi sau bám vào.
- **Kiến trúc:** User → Orchestrator → Planner (luật) → Policy/Router → Answerer (code, nguyên văn dữ liệu và nguồn). LLM Qwen3-4B chỉ sinh chữ giải thích điều kiện/so sánh, qua verifier.
- **Dữ liệu** (`data/`): DB riêng dựng từ snapshot V10.6 (1.350 thủ tục cấp xã/phường), `data/api.py`, `data/build.py`.
- **Truy hồi** (`retrieval/`): xếp hạng riêng có tính dấu, phủ định ("không phải X"), chọn theo thứ tự ("cái thứ n"), chặn chủ đề ngoài hệ thống.
- **Context memory:** mỗi câu được phân loại follow-up / thủ tục mới liên quan / quay lại / độc lập / sửa ý; nút "Bắt đầu chủ đề mới".
- **Hỏi lại:** thẻ hỏi lại (nút bấm + gõ tự do), không hỏi lần hai, từ ≥ 3 thủ tục gần nhau.
- **Eval** (`eval/`): DEV, HOLDOUT-1/2/3 (HOLDOUT-3 mù, số chính thức), bộ hội thoại ctx, bộ tự sinh synth. Quy tắc bộ mù ở `docs/EVAL.md`.
- Số đo đầu: HOLDOUT-3 top-1 73%, hành vi 83% (baseline V10.6: 11% và 32%); bịa số 7%.

## A2. Đợt 3 (Phase 7–13): plan sau feedback đầu tiên
Plan đưa ra (`PLAN_SYSTEM3_DOT3.md`), phần lớn việc sau đó được gộp vào đợt 4:
- Phase 7–8: xác nhận nền, tách DEV/HOLDOUT, bộ chấm cho phần LLM; Phase 9: giới hạn độ trễ Planner (gọi LLM chỉ khi có điều kiện/so sánh, timeout cứng); Phase 10: chặn "từ khớp tình cờ" để câu ngoài phạm vi (đội tuyển, ly hôn tòa án, nhãn hiệu) không bị trả thủ tục; phủ định và thứ tự; Phase 11: LLM trả lời có kiểm soát + verifier (số, tên văn bản, cấm "miễn phí" khi không có dữ liệu); Phase 12: reset `session_facts`; Phase 13: nghiệm thu.
- Kết quả hiện còn dùng: gate ngoài phạm vi 30/30, verifier, `answer_llm_test`, `memory_test`, `context_test`.

## A3. Đợt 4 (Phase 14–22), từ feedback lần 1–2 (2026-10-06)
Điểm yếu nhóm nêu: chưa **concise** (dư thủ tục, dư bước), **multi-intent bắt lung tung**, teencode/gõ đời thường làm break, thiếu thông tin được hỏi (vd thời hạn), nút "chủ đề mới" không chạy, config không có chỉ báo AI bật/tắt, cần nút "Tạo bảng full" thay "đọc thêm ở Dịch vụ công". Điểm tốt: bắt được multi-intent, không bị lừa sang chủ đề khác, usability tốt.

| Phase | Việc / kết quả | File chính |
|---|---|---|
| 17 Concise | Dựng chỉ số `run_concise.py` (hỏi gì trả đó). DEV focus 70% → 99%, task thừa 11/230 → 0. Bộ team 3/10 → 7/10 | `eval/run_concise.py` |
| 18 Nhóm lỗi chung A–F | **A** cụm chỉ-field bắt sai/thiếu ("hồ sơ" trong "nộp hồ sơ online" bị đọc thành giấy tờ; viết tắt hso/onl; thiếu cụm cơ quan/hình thức/thời gian xử lý); **B** multi-intent bớt nhạy (chỉ tách task thứ hai khi có tín hiệu rõ); **C** hỏi lại khi mơ hồ; **D** từ chối nhầm / chọn nhầm anh em; **E** gõ đời thường (teencode, không dấu, viết tắt); **F** hội thoại nhiều lượt ("cái thứ n", "à không ý tôi là") | `retrieval/query.py` (`FIELD_CUES`, `PRE_SYN`, `_tidy_fields`), `retrieval/rank.py`, `retrieval/context.py`, `retrieval/refs.py`, `server/planner/planner.py`, `server/policy/policy.py`, `server/answer/answerer.py`; `eval/build_p18.py`, `server/tests/context_test.py` |
| 19 Planner hybrid | Luật chạy trước; Qwen3-4B nền (timeout 7 s) chỉ đề xuất sửa khi confidence cao và qua Policy; có trace, `/config`. **Đo không có lợi** (0 lần sửa làm đúng hơn; confidence 0,99 cho 65% câu kể cả khi sai) → **tắt mặc định**, giữ công tắc `S3_PLANNER_MODE=hybrid` | `server/planner/hybrid.py`, `server/core/llm.py`, `server/config.py`, `server/tests/planner_hybrid_test.py` |
| 20 UI | Nút **"Tạo bảng full"** (12 mục nguyên văn, không LLM, `GET /procedure/{id}/table`, cờ `S3_TABLE_BUTTON`); chỉ báo "AI: bật/tắt" + panel cấu hình (Answer Composer, Planner, model, timeout); sửa 2 lỗi reset chủ đề và 1 lỗi bố cục điện thoại; sửa CSS thiếu `}`; quản lý hộp thoại (đổi tên, xóa, ghim, xuất MD/JSON/PDF); `knowledge/` (giao diện cho RAG, chưa build) | `server/main.py`, `server/answer/answerer.py::procedure_table`, `web/static/*`, `knowledge/`, `server/tests/p20_api_test.py` |
| 21 Nghiệm thu | HOLDOUT-4 (90 mục) và pseudo_real 2 (30 mục), agent mới soạn không thấy mã. Kết quả **không đạt**: top-1 75%, hành vi 82%, hỏi lại 8/16 | `eval/cases_h4.json`, `eval/cases_pseudo_real2.json` |
| 22 Chốt | README, ARCHITECTURE, EVAL, báo cáo, dọn `eval/results/` 58 MB → 2,8 MB | `docs/BAO_CAO_DOT4.md` |

Điều rút ra cho nhánh sản phẩm: DEV 96–99% là bộ đã tune, chỉ HOLDOUT/pseudo_real mới là số thật; hybrid LLM Planner không đáng bật; điểm yếu số một là hỏi lại khi mơ hồ.

---

# Phần B — Đợt 5 và 6 (feedback lần 3, 2026-10-07 → 2026-10-08)

## 1. Lỗi feedback lần 3 → đã sửa

| Feedback | Sửa | File chính | Kiểm |
|---|---|---|---|
| **L1** hỏi tiếp có nhãn lượt ("Turn 2:", "User:", "Câu 2:", "Q:") bị trả "ngoài phạm vi" | Bỏ nhãn lượt/đánh số ở đầu câu. Chữ lạ chỉ hạ độ tin cậy, không đổi hướng khi đã có ngữ cảnh | `retrieval/context.py` (`strip_labels`), `server/policy/policy.py` (`pre_check`) | `server/tests/p23_input_test.py`, `eval/perturb.py` (bất biến 93,7% → 99,5%) |
| **L3** gõ dính liền ("kethon"), teencode | Tách chữ dính bằng quy hoạch động trên từ vựng kho; thêm viết tắt/teencode (`PRE_SYN`) | `retrieval/query.py` (`unglue`, `unglue_text`), `retrieval/rank.py`, `eval/synth_retrieval.py` (biến thể `glued`) | synth `glued` TEST 96,1% (cổng ≥ 90%) |
| **L2 / TC06** câu điều kiện sinh task thừa | Mảnh câu chỉ lặp chữ của tên thủ tục không thành điều kiện (`_borrowed`, `_cond_head`, sau này `policy.adds_info`) | `retrieval/query.py`, `server/policy/policy.py` | task thừa 0/449; `p30_clarify_test` |
| **TC02** lệ phí bản sao | Bảng `team_fee_overlay`: lấy lệ phí từ corpus nhóm cho thủ tục cổng không có lệ phí, khớp tên chính xác, ghi nguồn "Bộ dữ liệu nhóm"; không suy ra "miễn phí" | `data/team_overlay.py`, `data/build.py`, `data/snapshot/team_corpus.json`, `server/answer/answerer.py` (`_fees_text`) | `data/tests/test_data.py::test_team_overlay`; bộ team 7/10 → 8/10 |
| **TC03** | Không sửa: đáp án nhóm cần sửa, quy tắc concise giữ nguyên | — | ghi ở `KNOWN_ISSUES.md` |
| **TC06** | Chưa sửa (thiếu ý "nơi cư trú cuối cùng" bị cắt khỏi bản tóm tắt) | — | `KNOWN_ISSUES.md`, cần phase riêng |

Lưu ý khi sửa bộ chấm: `eval/run.py` coi overlay là nguồn hợp lệ (nếu không, "8.000đ" bị tính là bịa số).

## 2. Mâu thuẫn tài liệu và chạy được ở mọi thư mục (Phase 24, 25)
- 17 mâu thuẫn A1–A17 đã sửa (README, SETUP, CONTRIBUTING, ARCHITECTURE, EVAL, `server/README.md`…).
- `run_server.py` (gốc): chạy dù thư mục tên gì (`python run_server.py -m <module>` hoặc `<script.py>`).
- `eval/check_docs.py`: so số trong tài liệu với file kết quả; hồi quy sẽ đỏ nếu tài liệu lệch.
- `server/config.py`: `ANSWER_LLM_TIMEOUT` 7 s. Không nạp model khi LLM và hybrid đều tắt; `S3_NO_WARMUP=1` cho test.
- `docs/FINAL_PRODUCT_CHECKLIST.md` và thẻ `# FINAL-PRODUCT:` trong code: đánh dấu chỗ cần làm cho bản cuối (xem mục 6).
- `docs/KNOWN_ISSUES.md`: danh sách lỗi đã biết.

## 3. Bộ nhớ người dùng (Phase 26)
- Hồ sơ theo thiết bị (`X-Client-Id`; thiếu thì `default`): tỉnh, xã, loại người dùng, ghi chú ≤ 200 ký tự; CCCD/SĐT bị từ chối.
- Một trục chọn `subject` (16 giá trị từ `procedure_subjects`). Khi sắp hỏi lại giữa ≥ 3 thủ tục, hồ sơ lọc ứng viên; còn một thì trả lời "Theo hồ sơ của bạn…". Câu đã nêu rõ thì hồ sơ không can thiệp.
- File: `server/user_memory.py`, `server/main.py`, `server/orchestrator.py`, `server/policy/policy.py`, `server/db/schema.sql` (bảng `user_memory`), `server/db/store.py`, `data/api.py` (`subject_names`, `subjects_of`), `web/static/js/chat.js`, `styles.css`, `templates/index.html`.
- Test: `server/tests/p26_memory_test.py`, `eval/run_p26.py` (92/92 trên bộ tự soạn, không phải kiểm mù).

## 4. Bước sinh chữ bằng LLM (Phase 27)
- Chỉ kích hoạt khi có điều kiện hoặc ≥ 2 task so sánh. Prompt ngắn, `ANSWER_LLM_NUM_PREDICT` 200, `ANSWER_LLM_PASSAGE_CHARS` 450, `ANSWER_LLM_TURN_BUDGET` 9 s, `_ready()` dò `/api/ps` (model nguội thì trả bản code ngay, nạp nền).
- Kết quả: timeout 3–8/64 → 0/64; p95 qua `/chat` ≤ 4,8 s. Giá trị cho người dùng chưa chứng minh (cần chấm tay `eval/results/composer_sample20.md`).
- File: `server/answer/llm_answer.py`, `server/config.py`, `server/tests/answer_llm_test.py`.

## 5. Tái lập từ Git (Phase 28)
- `eval/vendor_v106/` (mã V10.6, commit 83567403), `eval/rebuild_v106_db.py`, `eval/run_all.py`, `eval/REPRODUCE.md`. Clone sạch vào thư mục tên lạ cho kết quả khớp.
- Bốn adapter hết ghi cứng `ROOT/system3/server`.

## 6. Phase 30 — hỏi lại khi mơ hồ, điều kiện thừa (BẬT)
Ba nguyên nhân gốc, sửa chung một chỗ:
1. `rank._near` cắt anh em tên dài khi chung cụm đầu ("gia hạn", "thanh toán") nên chỉ còn 1–2 ứng viên và hệ thống trả lời thay vì hỏi.
2. Bản theo tỉnh bị loại hẳn dù cho thấy thủ tục có nhiều dạng.
3. `policy._match_conditions` khớp theo mọi chữ của câu, kể cả chữ rỗng ("em", "muốn", "là"), nên chặn hỏi lại và sinh điều kiện thừa.

File: `retrieval/rank.py` (`_contiguous`), `server/policy/policy.py` (`_user_words`, `_user_seq`, `adds_info`), `retrieval/query.py` (cụm "cần giấy tờ gì", lời đệm "tìm hiểu/tư vấn/cần biết…"). Test: `server/tests/p30_clarify_test.py`, bộ `eval/cases_p30.jsonl`.

Kết quả: bộ tự viết hỏi lại đúng 33→41/44 và 31→41/44, hỏi thừa 0; số lần gọi LLM vì điều kiện 53→28 trên 813 ca. **Trên bộ mù gần như không đổi** (HOLDOUT-4 8→9/16, HOLDOUT-5 10→11/20).

## 7. Phase 31 — hỏi lại họ nhiều dạng (ĐÃ THỬ, TẮT MẶC ĐỊNH)
Hỏi lại khi câu chỉ nêu tên chung của họ có ≥ 3 dạng thật (khai sinh, kết hôn, khai tử, nhận cha mẹ con, Bằng Tổ quốc ghi công). Đo mù không có lợi (HOLDOUT-6 hỏi lại 12→13/28; HOLDOUT-4/5 hành vi giảm 2–3 ca; bộ team 8→7/10) và đảo kỳ vọng DEV cũ, nên **tắt**: `S3_FAMILY_CLARIFY` mặc định `0`, bật bằng `1`.
Mã vẫn nằm trong repo. Có một thay đổi phụ có ích khi mang sang: nút "dạng khác" gửi kèm `proc_id` (`ChatIn.proc_id` → `Turn.pick_proc`, `server/main.py`, `server/orchestrator.py`, `web/static/js/chat.js`) để bấm không bị quay lại thẻ hỏi. Nếu không mang Phase 31 thì bỏ qua phần này.

## 8. Số đo hiện tại (chế độ luật, 2026-10-08)
| | Số |
|---|---|
| DEV cũ 209: top-1 / hành vi / bịa số | 97,0% / 98,1% / 0,0% |
| Ngoài phạm vi / ctx / ctx-p23 / p26 | 30/30 / 89/91 / 26/26 / 92/92 |
| synth TEST / glued TEST / perturb | 96,4% / 96,1% / 99,53% |
| Bộ team | 8/10 (TC03, TC06 fail đã ghi) |
| `run_all` | gồm test mới; 39 hàng, `check_docs` sạch |
| Bộ mù top-1 / hành vi (chưa đạt mục tiêu 80% / 88%) | HOLDOUT-4 78% / 84%; HOLDOUT-5 69% / 77%; HOLDOUT-6 70% / 75%; pseudo_real 3 32% / 53% |
| Hỏi lại đúng trên bộ mù | khoảng 45% (điểm yếu số một, chưa giải quyết) |

## 9. Còn lại trước khi ra sản phẩm cuối (đã ghi trong `FINAL_PRODUCT_CHECKLIST.md`)
- Tách chế độ dev/user: `plan`, `trace`, `/config`, `?dev=1` hiện chưa kiểm dev.
- Che CCCD/SĐT trong `messages.content`, `plan_json`, tên hộp thoại.
- Phiên và quyền sở hữu hộp thoại; `client_id` tự khai nên đoán được; "xóa tất cả" xóa của mọi người; `default` dùng chung.
- Công tắc AI cho người dùng thường; tài khoản thay `client_id`.
- Danh sách 63 tỉnh là trước sáp nhập.
- `data/DATA_NOTES.md` và `data/snapshot/SOURCE.md` còn đường dẫn `D:\`; `server/e2e_test.py` có mẫu treo do stdout PIPE không đọc; `memory_test.py` chập chờn (đã thêm thử lại, chưa rõ gốc).

## 10. Cách mang sang nhánh sản phẩm
1. Mang theo từng mục (1 → 6) theo danh sách file; mục 7 chỉ khi cần.
2. Sau mỗi mục chạy `python run_server.py eval/run_all.py --quick`, cuối cùng chạy bản đầy đủ; đặt `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 PYTHONIOENCODING=utf-8` nếu không cần GPU.
3. `data/` đổi (thêm `team_overlay.py`, `team_corpus.json`) thì dựng lại DB (`data/build.py`) trước khi chạy test.
4. Đồng bộ vào `repo/` và push GitHub do bạn làm; tôi không sửa `repo/`.

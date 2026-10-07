# Báo cáo Phase 26 — bộ nhớ người dùng (2026-10-07)

Chế độ luật (`S3_USE_LLM=0`, `S3_PLANNER_MODE=rules`, `S3_NO_WARMUP=1`), không GPU/LLM, không gọi Ollama (`ollama ps` trống ở cuối). Không sửa `repo/`, `retrieval/*`, planner luật, `server/core/llm.py`, `server/answer/*`; `data/` chỉ **thêm** hai hàm đọc vào `data/api.py` (`subject_names`, `subjects_of`), không đổi hàm cũ. Không mở/chạy bộ mù (`cases_h2*`, `cases_h3*`, `cases_h4*`, `cases_pseudo_real*`, `cases_team.json`); `run_concise.py` chạy với `--no-blind`.

## Đã làm
- **Lưu theo thiết bị**: UI sinh `client_id` (UUID, `localStorage` bọc try/catch; chặn storage thì id tạm trong phiên), gửi mọi request qua `X-Client-Id`; thiếu header = `'default'`; sai định dạng = 400. Bảng mới `user_memory(client_id, key, value, updated_at)` (`CREATE TABLE IF NOT EXISTS`, đã thử bỏ bảng rồi mở lại DB). Thẻ `FINAL-PRODUCT: [B4][MEM]` ở `user_memory.py`, `main.py`, `schema.sql`, `chat.js`; mục 6 mới trong `docs/FINAL_PRODUCT_CHECKLIST.md`.
- **Hồ sơ nhẹ**: tỉnh/thành (UI chọn trong 63 đơn vị trước sáp nhập 07/2025, cùng danh sách hệ cũ; server không kiểm chặt), xã/phường (<= 80 ký tự), loại người dùng (`citizen`/`business`/`other`), ghi chú <= 200 ký tự. Từ chối (400) CCCD/CMND/SĐT bằng `mask_pii`, không ghi gì khi một trường lỗi.
- **Nhớ MCQ**: một trục `subject`; giá trị phải có trong `procedure_subjects` (16 tên; lạ = 400; trục `level` = 400). Ánh xạ loại người dùng -> đối tượng: `citizen` -> "Công dân Việt Nam"; `business` -> "Doanh nghiệp" + "Doanh nghiệp Việt Nam" (dữ liệu không có tên riêng cho hộ kinh doanh); `other` -> không ánh xạ. Lựa chọn MCQ đã nhớ thắng ánh xạ.
- **API**: `GET /memory`, `PUT|POST /memory/profile`, `POST /memory/mcq`, `DELETE /memory/mcq?axis=`, `DELETE /memory`.
- **Cách dùng** (`policy.check(memory=...)`, `orchestrator` nạp qua `Turn.memory`): (1) sắp hỏi lại giữa >= 3 thủ tục gần nhau thì lọc ứng viên theo đối tượng; đúng 1 hợp (mọi ứng viên khác chắc chắn không hợp) -> không hỏi, chọn nó, câu trả lời mở đầu "Theo hồ sơ của bạn (đối tượng: …) mình chọn «…». Nếu chưa đúng, bạn nói lại nhé."; 2..n-1 hợp -> thẻ chỉ còn ứng viên hợp (>= 2) và ghi chú; không ai hợp/ai cũng hợp -> giữ nguyên. Ứng viên không khai đối tượng = chưa biết, không bị loại. (2) chọn bản mặc định của nhóm biến thể: bản mặc định không hợp mà có biến thể hợp (không gắn tỉnh, cấp xã, không ngành dọc) -> ưu tiên biến thể đó, cùng lời nhắn. (3) gợi ý sau khi bấm nút thẻ hỏi lại: server trả `memory_suggest` (đối tượng đặc trưng của thủ tục chọn), UI hỏi "Nhớ đối tượng …?", **bấm mới lưu**.
- **Luật "nêu rõ thì hồ sơ không can thiệp"** (thêm sau khi chạy thử, xem "Điều tôi phải sửa giữa chừng"): hồ sơ bị bỏ qua nếu nguyên tên một ứng viên nằm trong câu, hoặc cụm chữ nội dung của câu (>= 3 chữ) là một đoạn liền trong tên của **đúng một** ứng viên.
- **UI**: nút "Hồ sơ của bạn" cạnh chỉ báo AI (panel: tỉnh, xã/phường, loại, ghi chú, Lưu, Bỏ qua; danh sách "Đã nhớ" có "Quên" từng mục; "Quên tất cả"), thanh gợi ý "Nhớ đối tượng …?". Cache-bust `?v=20261007a`. Đã kiểm trong trình duyệt thật (lưu hồ sơ, quên tất cả, bấm nút thẻ -> gợi ý -> Nhớ -> "Đã ghi nhận", hỏi lại cùng câu ra thẻ gọn có chú thích).
- **Test**: `server/tests/p26_memory_test.py` (API CRUD, kiểm giá trị, PII, quên, cô lập hai `client_id`, migration, unit `filter_by_subject`, `/chat` có/không/sai hồ sơ, gợi ý không tự lưu, kiểm tĩnh UI). **Đo**: `eval/build_p26.py` -> `eval/cases_p26.jsonl` (92 ca), `eval/run_p26.py`.

## Số đo
### Hồi quy (tắt hồ sơ = như cũ): giống hệt trước Phase 26
| Cổng | Ngưỡng | Trước (P24) | Sau |
|---|---|---|---|
| DEV cũ 209: top-1 / hành vi / bịa số | >= 95 / >= 96 / <= 3 | 97,0% (159/164) / 97,6% / 0,0% | 97,0% (159/164) / 97,6% / 0,0% |
| DEV gộp 523 | — | 98,0% / 98,1% / 0,4% | 98,0% (446/455) / 98,1% / 0,4% |
| ngoài phạm vi | 30/30 | 30/30 | 30/30 |
| ctx / ctx-p23 | >= 89/91; 26/26 | 89/91; 26/26 | 89/91; 26/26 (cùng 2 ca hỏng) |
| synth TEST-seed top-1 | >= 94% | 96,4% | 96,4% (TRAIN 96,3%) |
| DEV focus / task thừa | >= 95% / <= 2% | 349/353 (99%) / 0/451 | 349/353 (99%) / 0/451 |
| `perturb.py` | >= 98% | 99,44% | 99,44% (7.056/7.096, cùng 40 ca hỏng) |
| test: memory, context, answer_llm, planner_hybrid, p20_api, p23_input, **p26_memory**, smoke, test_data, selftest | xanh | xanh | xanh |
| `check_docs.py` | sạch | sạch | sạch (74 khớp, 0 lỗi) |
Số hồi quy giống hệt vì không hồ sơ thì `memory=None` và mọi nhánh mới không chạy; nhóm d của `run_p26.py` còn so cả `Routed.to_dict()` với/không `memory`.

### Bộ ca mới `cases_p26.jsonl` (92 ca, 37 câu khác nhau): 92/92
| Nhóm | Ca | Đạt | Nội dung |
|---|---|---|---|
| a hồ sơ khớp | 28 | 28 | 10 pick (không hỏi lại, đúng thủ tục theo quy tắc đối tượng) + 18 shrink (thẻ gọn hơn, còn thủ tục hợp) |
| b cùng câu a, không hồ sơ | 28 | 28 | hỏi lại như cũ (đúng bằng đầu ra memory=None) |
| c hồ sơ sai/lạc, câu nêu rõ | 24 | 24 | 12 câu rõ + hồ sơ không liên quan; 4 câu nêu rõ thủ tục mà hồ sơ chỉ hợp ứng viên khác; ca "không ai hợp"; ca ngoài phạm vi: đáp án y hệt không hồ sơ, không ghi chú |
| d hồ sơ rỗng (`{}` / `other`) | 12 | 12 | `Routed` y hệt memory=None |

**Số lần hỏi lại**: nhóm a 28/28 ca bị hỏi lại khi không hồ sơ -> 18/28 khi có hồ sơ (bỏ 10 lần hỏi, 36%); 18 thẻ còn lại bớt nút: 17 thẻ nhỏ hơn, số nút trung bình 3,5 -> 2,4; 1 thẻ cùng cỡ nhưng đổi sang ứng viên hợp.

### Mơ hồ-theo-đối-tượng có nhiều trong dữ liệu thật không? **Không, hiếm.**
Quét 2.023 câu dựng từ tên 1.313 thủ tục cấp xã (tên đầy đủ, bỏ "Thủ tục", bỏ ngoặc, mệnh đề đầu); không hồ sơ: 1.517 trả lời, 403 xin lỗi (cắt cụt quá), **103 hỏi lại**. Có hồ sơ thì hồ sơ chỉ đổi kết quả ở:
| Hồ sơ | bỏ hỏi (pick) | thẻ gọn hơn (shrink) | thẻ bị ảnh hưởng / 103 | câu trả lời đổi sang bản mặc định hợp đối tượng (variant) |
|---|---|---|---|---|
| người dân (`citizen`) | 1 | 23 | 24 | 0 |
| doanh nghiệp (`business`) | 10 | 15 | 25 | 5 |
| HTX | 9 | 12 | 21 | 0 |
| tổ chức | 0 | 27 | 27 | 0 |
Nghĩa là: tối đa ~10% số thẻ hỏi lại biến mất (doanh nghiệp/HTX), người dân gần như không được lợi (hầu hết thủ tục khai "Công dân Việt Nam"); chênh lệch đối tượng chủ yếu ở đất đai, xây dựng, bảo hiểm, thủ tục theo tỉnh. Đây là quét trên câu sinh từ tên thủ tục, **không phải câu người dân thật**. Không có số "độ giảm hỏi lại" nào ngoài hai bảng này.

## Ca tự soạn dễ hơn thật (đọc kỹ trước khi tin số 92/92)
1. Câu nhóm a được chọn **sau khi** tôi quét dữ liệu tìm nhóm ứng viên mà đối tượng phân biệt được; thật ra phần lớn câu hỏi lại ngoài đời không như vậy (mục trên: ~1–10% số thẻ).
2. **Đáp án nhóm a là theo quy tắc đối tượng của dữ liệu, không theo ý định thật của người hỏi.** Chỗ quét cho thấy `pick` đôi khi đổi đáp án khỏi ứng viên đứng đầu của truy hồi: trong 33 lần `pick` của lần quét đầu (bốn hồ sơ gộp, trước luật "nêu rõ"), 19 lần ứng viên đứng đầu chính là thủ tục mà câu được sinh từ tên của nó; `pick` giữ nguyên ứng viên đó chỉ 10/33. Luật "nêu rõ" đã chặn các ca tệ nhất (ví dụ "đăng ký thành lập tổ hợp tác" + hồ sơ HTX từng bị kéo sang "đăng ký thành lập hợp tác xã"), nhưng cho câu mơ hồ thật thì `pick` có thể sai và **chưa có số đo độ đúng trên câu thật**; lời nhắn "Theo hồ sơ của bạn … nếu chưa đúng, bạn nói lại nhé" là biện pháp giảm nhẹ chứ không phải bảo đảm.
3. **Tôi đã sửa bộ ca và luật sau khi xem đầu ra**: 4 ca đầu tôi xếp vào nhóm a (pick) chạy ra "hồ sơ đổi đáp án dù câu đã nêu rõ" nên tôi thêm luật `_names_candidate` ở Policy rồi chuyển 4 ca đó sang nhóm c; tôi cũng nới điều kiện thẻ shrink từ "nhỏ hơn" thành "không lớn hơn" vì 1 ca (phê duyệt dự án, hồ sơ người dân) thay ứng viên không hợp bằng ứng viên hợp ở cùng cỡ 4 nút. Vì vậy 92/92 là số của bộ ca đã khớp với luật, không phải số kiểm mù.
4. Câu a/c chỉ dài 2–6 chữ phần lớn; ngoài đời người dân kể dài, lẫn hoàn cảnh.

## Điều chưa làm được / giới hạn
- Chưa có tài khoản: bộ nhớ khoá theo `client_id` tự khai (đoán được id là sửa/xoá được hồ sơ người khác; thiếu header dùng chung `'default'`). Đã ghi `FINAL-PRODUCT: [B4][MEM]`.
- Chỉ nhớ **một trục** (`subject`); trục "cấp thực hiện" bỏ theo thiết kế. Tỉnh/xã chỉ hiển thị, không lọc (dữ liệu không chia theo tỉnh); danh sách tỉnh là 63 đơn vị cũ.
- Hồ sơ **không** đi qua Planner nên đường `context_facts`/`session_facts` vẫn không được tạo ở cấu hình mặc định (kế hoạch nói "làm đường context_facts hết chết"; thiết kế đã chốt đưa hồ sơ vào Policy nên việc này không làm).
- Chỉ áp cho thẻ hỏi lại bằng luật (>= 3 ứng viên gần nhau). Thẻ do `needs_clarification` (Planner xin) không lọc theo hồ sơ.
- Ánh xạ "hộ kinh doanh" -> "Doanh nghiệp" là xấp xỉ (dữ liệu không có đối tượng "Hộ kinh doanh").
- Dữ liệu `procedure_subjects` có chỗ lệch tên thủ tục: thu hẹp thẻ theo người dân có thể ẩn đúng thủ tục (ví dụ "Đăng ký đất đai lần đầu cho cá nhân, hộ gia đình" chỉ khai doanh nghiệp/Việt kiều). Thẻ ghi "không thấy thì gõ tên thủ tục".
- Không có test trình duyệt tự động; UI được kiểm tay trên Browser pane và bằng kiểm chuỗi tĩnh trong `p26_memory_test`.

## Điều tôi phải sửa giữa chừng
- `data.api.subject_names` ban đầu `GROUP BY name` va với cột `procedures.name` (ra 1.199 "đối tượng"); đổi bí danh thành `subj` (đúng 16).
- Câu thử đầu của `p26_memory_test` là tên đầy đủ của một thủ tục; luật "nêu rõ" đúng khi không can thiệp, nên đổi câu thử sang câu mơ hồ.

## File đổi
Mới: `server/user_memory.py`, `server/tests/p26_memory_test.py`, `eval/build_p26.py`, `eval/run_p26.py`, `eval/cases_p26.jsonl`, `eval/results/p26.json`, `eval/P26_REPORT.md`.
Sửa: `data/api.py` (thêm 2 hàm), `server/policy/policy.py` (`memory`, `filter_by_subject`, `_names_candidate`, `_memory_variant`, `Routed.memory_note`), `server/orchestrator.py` (`Turn.memory`, ghi chú, `memory_suggest`), `server/main.py` (`/memory*`, `X-Client-Id`), `server/db/schema.sql`, `server/db/store.py` (`mem_*`), `web/static/js/chat.js`, `web/static/css/styles.css`, `web/templates/index.html`, `.gitignore` (whitelist `p26.json`), `README.md`, `docs/ARCHITECTURE.md`, `docs/CONTRIBUTING.md`, `docs/SETUP.md`, `docs/EVAL.md`, `docs/FINAL_PRODUCT_CHECKLIST.md`, `docs/KNOWN_ISSUES.md`, `eval/README.md`.

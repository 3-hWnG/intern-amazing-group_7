# Kiến trúc System 3

System 3 là trợ lý hỏi đáp thủ tục hành chính **cấp xã/phường** (tiếng Việt), độc lập với System 1/2 của V10.6. Chỉ dùng lại **dữ liệu** thủ tục (snapshot trong `data/snapshot`).
Mục tiêu và các quyết định ban đầu: [PLAN_SYSTEM3.md](PLAN_SYSTEM3.md). Kế hoạch đợt 3: [PLAN_SYSTEM3_DOT3.md](PLAN_SYSTEM3_DOT3.md).

## Luồng một lượt hỏi
```
User
 -> Orchestrator   pre_check (chèn lệnh, cắt 2000 ký tự, bỏ nhãn lượt/emoji/lời đệm đầu-cuối câu), nạp trạng thái hội thoại
 -> Planner        LUẬT: tách câu thành tasks (tối đa 3), chọn thủ tục, fields, điều kiện, quan hệ
                    (tuỳ chọn mode=hybrid: SAU khi luật dựng xong, Qwen3-4B đề xuất, hợp nhất; chạy tuần tự, xem dưới)
 -> Policy/Router  LUẬT: kiểm căn cứ, phạm vi, field_status, biến thể mặc định, hỏi lại
 -> Answerer       CODE: trích nguyên văn dữ liệu + nguồn
 -> (LLM sinh chữ) chỉ cho giải thích điều kiện / so sánh; mỗi ý có trích dẫn, qua verifier
 -> User           câu trả lời + nguồn; ghi bộ nhớ và trace
```

Nguyên tắc:
- **Planner không dùng LLM** (mặc định `S3_PLANNER_MODE=rules`). Phase 19 đo hybrid công bằng (timeout 7 s): không đạt gate nên giữ tắt (eval/P19_REPORT.md). Timeout của hai bước LLM: bảng ở mục "Bảng timeout" bên dưới.
- **Planner hybrid** (`server/planner/hybrid.py`, `S3_PLANNER_MODE=hybrid`): luật luôn dựng kế hoạch trước, **rồi mới** gọi LLM, **tuần tự** (không chạy song song với luật: Policy cần kế hoạch cuối nên không có việc đáng kể để chồng). Qwen3-4B (think=False, schema gọn `tasks[{action,cand,fields}] + confidence`, chọn ứng viên bằng chỉ số `cand`, không tự đưa mã/số) chạy trong một thread chỉ để có hạn cứng theo đồng hồ thật `PLANNER_LLM_TIMEOUT` (7 s); Planner đứng chờ kết quả hoặc hết hạn. `diff` rút các thay đổi (`edit_fields | edit_proc | add_task | delete_task`); `merge` chỉ nhận khi `confidence >= PLANNER_LLM_CONFIDENCE` VÀ: thủ tục có trong kho, field thuộc `FIELD_TITLE`, task luật không bị khoá (hỏi lại/xin lỗi/mơ hồ/`near`/so sánh/kế thừa ngữ cảnh), và chạy thử `policy.check` trên kế hoạch SAU khi áp đề xuất: hành vi phải giữ nguyên (`answer`) và **mọi task của kế hoạch mới phải route `direct`** (không riêng task bị sửa); không thì hoàn tác đề xuất đó (`op.reason = "Policy từ chối ..."`). Quá hạn/lỗi/JSON hỏng -> giữ kế hoạch luật. Policy vẫn chạy sau cùng trên kế hoạch cuối. Nhật ký đầy đủ ở `trace["planner_llm"]` (gọi hay không, ms, timeout, đề xuất + lý do chấp nhận/từ chối, kế hoạch luật vs kế hoạch cuối), hiện trong dev panel. `GET /config` (mode, timeout, ngưỡng, model, model đã nạp), `POST /config` (đổi trong bộ nhớ, chỉ khi `S3_DEV=1`).
- **LLM chỉ sinh chữ**, không chọn thủ tục, không viết số. Ý nào không có trích dẫn hợp lệ hoặc có số/tên văn bản/"miễn phí" không nằm trong dữ liệu thì bị bỏ; lỗi hoặc timeout (`ANSWER_LLM_TIMEOUT`, 7 s mỗi lần gọi, trần chung 9 s cho cả lượt: `ANSWER_LLM_TURN_BUDGET`) thì giữ câu trả lời bằng code; model chưa nạp (nguội) thì không đợi, trả bản code ngay và nạp nền. Prompt đã rút gọn và giới hạn sinh `ANSWER_LLM_NUM_PREDICT` = 200 token, đoạn dữ liệu cắt `ANSWER_LLM_PASSAGE_CHARS` = 450 ký tự (Phase 27, số đo: `eval/P27_REPORT.md`).
- Không suy ra "miễn phí" khi dữ liệu trống: trả "cổng không công bố".
- Hỏi lại tối đa một lần; sau khi người dùng trả lời thì chọn thủ tục gần nhất, không hỏi lần hai.
- Từ **3 thủ tục/biến thể gần nhau** mà câu hỏi không phân biệt được → hỏi lại (nút bấm + gõ tự do). Câu chỉ nêu **tên một lĩnh vực** (`domain`: "hộ tịch", "đất đai", "cư trú"...) cũng hỏi lại, đại diện = mỗi họ một bản. 2 biến thể → trả bản mặc định kèm nút "dạng khác".
- **Đúng trọng tâm**: chỉ trả mục người dùng hỏi (kể cả mục kế thừa từ câu trước khi là câu nối/sửa ý/"chắc không?"); không nêu mục nào → bản tóm tắt ngắn, riêng câu điều kiện → `components` + phần trường hợp. Cụm hỏi mục ("giải quyết trong bao lâu", "cần gì", "ở đâu") và lời kể hoàn cảnh KHÔNG là task thứ hai; task thứ hai chỉ khi được nêu riêng (mục hỏi hoặc động từ yêu cầu).
- **Trường hợp/điều kiện**: hoàn cảnh khớp CHẮC một mục `condition_index` (source=case) thì chỉ trả giấy tờ của trường hợp đó (`policy._strong_case`, `answerer._case_pick`), kèm nguồn; không có dữ liệu thì nói cổng không công bố riêng.
- Ngoài phạm vi (cấp tỉnh, không có trong kho, chủ đề lạ, chèn lệnh) → xin lỗi kèm lý do. Nếu kho có thủ tục thì trả lời theo kho.

## Bảng timeout hai bước LLM
Cả hai bước LLM dùng **cùng timeout 7 giây**, cấu hình được bằng biến môi trường (nguồn: `server/config.py`). Trước Phase 24 bước sinh chữ là 5 s cứng trong `server/answer/llm_answer.py` (tài liệu cũ lẫn "5 s" và "7 s" vì đây là hai bước khác nhau); nay hợp nhất.

| Bước LLM | Mặc định | Timeout | Biến cấu hình | Quá hạn thì | Đổi lúc chạy |
|---|---|---|---|---|---|
| **Planner hybrid** (`S3_PLANNER_MODE=hybrid`) | **tắt** (`rules`) | 7 s (`PLANNER_LLM_TIMEOUT`) | `PLANNER_LLM_TIMEOUT`, `PLANNER_LLM_CONFIDENCE`, `PLANNER_LLM_NUM_PREDICT` | giữ kế hoạch luật | `POST /config` khi `S3_DEV=1` |
| **Answer Composer** (bước sinh chữ, `S3_USE_LLM`) | **bật** | 7 s mỗi lần gọi (`ANSWER_LLM_TIMEOUT`); tổng một lượt <= 9 s (`ANSWER_LLM_TURN_BUDGET`) | `ANSWER_LLM_TIMEOUT`, `ANSWER_LLM_TURN_BUDGET`, `ANSWER_LLM_NUM_PREDICT` (200), `ANSWER_LLM_PASSAGE_CHARS` (450), `S3_USE_LLM` | giữ câu trả lời bằng code (model chưa nạp: ngay, không đợi) | chỉ công tắc bật/tắt (`POST /config {answer_llm}`); timeout chỉ đổi bằng biến môi trường |

Khác: `LLM_TIMEOUT` (120 s) là trần HTTP của client Ollama khi nơi gọi không truyền timeout riêng; `PLANNER_TIMEOUT` (2,5 s) chỉ cho nhánh Planner LLM cũ (`S3_PLANNER_LLM=1`, tắt, không dùng); `QUEUE_JOB_TIMEOUT` (180 s) là trần cả một lượt trong hàng đợi. Phase 27 đã đo lại bước sinh chữ với 7 s: sau khi rút gọn prompt, 0/64 lượt gọi chạm timeout trên bộ 63 ca (trước đó 3–8/64, tuỳ lúc GPU bận), p50 ~1,8 s, p95 ~3,1 s; qua `/chat` p95 ~3,4 s (eval/P27_REPORT.md). Phép đo timeout của client là theo từng lần đọc (httpx), không phải đồng hồ tổng; trần tổng của lượt do `ANSWER_LLM_TURN_BUDGET` giữ.

## Phase 20: UI và tính năng tháo/lắp
- **Tạo bảng full**: block trả lời direct mang `proc_id`; UI hiện nút, bấm gọi `GET /procedure/{id}/table` -> `answerer.procedure_table` (12 mục nguyên văn từ `data.api` + nguồn, không LLM, không cắt). Cờ `S3_TABLE_BUTTON` (mặc định 1); tắt thì câu trả lời quay về dòng cũ.
- **Cấu hình**: `GET/POST /config` có thêm `answer_llm` (đổi bằng biến môi trường tiến trình `S3_USE_LLM`, `orchestrator._answer_llm` đọc mỗi lượt), `model_loaded`. UI: chỉ báo "AI: bật/tắt" + panel; công tắc chỉ khi `S3_DEV=1`.
- **Reset chủ đề**: `reset_facts` xoá fact/danh sách đã hiển thị/trạng thái VÀ chèn tin trợ lý "Đã bắt đầu chủ đề mới" làm tin cuối (để "cái thứ nhất" không đọc lại danh sách đánh số của thẻ cũ); UI làm mờ nút cũ.
- **`knowledge/`**: chỉ thiết kế giao diện RAG/import (Box 5B/6B), không có trong đường chạy.

## Map G7 theo hiện trạng
| Box | Hiện trạng |
|---|---|
| 1 Giao diện, 2 Orchestrator | có: `web/`, `server/orchestrator.py`; thêm chỉ báo/cấu hình AI, bảng full |
| 3 Semantic Planner | luật (mặc định); hybrid luật + Qwen3-4B là tuỳ chọn, tắt (Phase 19) |
| 4 Validate/Policy/Router | có: `server/policy/` |
| 5A, 6A (dữ liệu trực tiếp) | có: `data/api.py`, `retrieval/` |
| 5B RAG, 6B import PDF/DOC | CHƯA làm; chỉ có thiết kế `knowledge/README.md` + stub |
| 7 Evidence bundle | Direct (ô dữ liệu + nguồn); gộp RAG khi có 5B |
| 8 Answer Composer | code trích nguyên văn; LLM chỉ sinh chữ cho điều kiện/so sánh (bật/tắt bằng `S3_USE_LLM`) |
| 9 Verifier | `answer/verifier.py` (số/tên văn bản/"miễn phí"); chưa kiểm nghĩa |
| 10 Phản hồi | blocks + nguồn + thẻ hỏi lại + nút "dạng khác" + "Tạo bảng full" |

## Module
| Đường dẫn | Vai trò |
|---|---|
| `data/` | build DB từ snapshot, bảng `fees_clean`, `field_chunks`, `condition_index`, `families`, `synonyms`; `api.py` là cửa vào duy nhất |
| `run_server.py` (gốc) | launcher: đăng ký package `system3` bằng `importlib` rồi chạy `server/main.py` (hoặc `-m module`/script), không cần `PYTHONPATH` |
| `retrieval/query.py` | hiểu câu: cụm chỉ-field (phí, giấy tờ, nộp ở đâu…), từ dừng, cụm bảo vệ, viết tắt/teencode, tách chữ dính liền (`unglue`: quy hoạch động trên từ vựng kho + âm tiết hợp lệ), tách câu |
| `retrieval/rank.py` | xếp hạng IDF có tính dấu, cổng phạm vi, cờ uncertain/ambiguous/near, chitchat |
| `retrieval/refs.py` | phủ định ("không phải X"), thứ tự ("cái thứ hai") |
| `retrieval/context.py` | trạng thái hội thoại và quyết định follow-up (xem dưới); `strip_labels` làm sạch đầu vào (nhãn lượt "Turn 2:"/"Q:"/"2)", emoji, ngoặc kép, lời đệm) cho cả lịch sử |
| `server/planner/` | dựng Plan từ kết quả retrieval; `hybrid.py` hợp nhất đề xuất LLM (tuỳ chọn, tắt mặc định); nhánh LLM cũ tắt |
| `server/policy/` | guardrail và router |
| `server/answer/` | `answerer.py` (code), `llm_answer.py` + `verifier.py` (sinh chữ có kiểm) |
| `server/orchestrator.py` | điều phối một lượt, bộ nhớ, trace |
| `server/user_memory.py` | Phase 26: hồ sơ nhẹ + nhớ lựa chọn MCQ (`subject`) theo `client_id`, ánh xạ loại người dùng -> đối tượng, gợi ý nhớ |
| `server/db/` | SQLite hội thoại: `conversations`, `messages`, `session_facts`, `shown_procedures`, `conv_state`, `turn_traces`, `user_memory` (Phase 26) |
| `web/` | UI chat (copy từ V10.6 và sửa) |

## Bộ nhớ hội thoại (`retrieval/context.py`)
Trạng thái gồm chủ đề, lịch sử thủ tục đã nói (theo thứ tự), mục đang hỏi, lời kể chưa gắn thủ tục. Mỗi câu được phân vào một loại, lý do ghi vào `trace["ctx"]`:
`follow_up` (cùng thủ tục) · `new_related` (thủ tục mới cùng lĩnh vực) · `return` (quay lại thủ tục đã nói) · `independent`/`new` (không kế thừa) · `correction` (sửa ý) · `story` (lời kể hoàn cảnh).
Fact người dùng kể gắn với thủ tục lúc ghi; đổi sang thủ tục khác họ thì không rò sang. Nút "Bắt đầu chủ đề mới" hoặc câu "hỏi việc khác" xoá fact và danh sách đã hiển thị.
Bảng sự kiện đời sống (`context.EVENTS`, kể chuyện -> gợi ý tên thủ tục) có **11 sự kiện** viết tay.

## Bộ nhớ người dùng (Phase 26, `server/user_memory.py`)
Chuyển theo tinh thần hệ cũ V10.6 (memory.js, /api/profile, /api/mcq-memory). Lưu theo **thiết bị** (`client_id` UUID ở `localStorage`, header `X-Client-Id`, thiếu thì 'default'); chưa có tài khoản (thẻ `FINAL-PRODUCT: [MEM]`, mục 6 checklist). Bảng `user_memory(client_id, key, value, updated_at)`; tạo bằng `CREATE TABLE IF NOT EXISTS` nên DB cũ mở lại không cần di chuyển.
- **Hồ sơ (tuỳ chọn):** tỉnh/thành, xã/phường, loại người dùng (`citizen` | `business` | `other`), ghi chú <= 200 ký tự. Từ chối (400) CCCD/CMND/SĐT. Tỉnh/xã chỉ hiển thị, không dùng để lọc (dữ liệu chỉ cấp xã, không chia theo tỉnh).
- **Nhớ lựa chọn MCQ:** một trục duy nhất `subject` (đối tượng thực hiện); giá trị phải có trong `procedure_subjects` (kiểm ở server, lạ -> 400). Bỏ trục "cấp thực hiện" (System 3 chỉ cấp xã).
- **Ánh xạ loại người dùng -> đối tượng:** `citizen` -> "Công dân Việt Nam"; `business` -> "Doanh nghiệp" + "Doanh nghiệp Việt Nam" (dữ liệu không có tên riêng cho hộ kinh doanh); `other` -> không ánh xạ. Lựa chọn MCQ đã nhớ thắng ánh xạ; hai tên doanh nghiệp coi là một nhóm.
- **API:** `GET /memory` (hồ sơ + mcq + `effective` + danh mục), `PUT|POST /memory/profile` (chỉ đổi trường có mặt; chuỗi rỗng = quên trường), `POST /memory/mcq {axis,value}`, `DELETE /memory/mcq?axis=`, `DELETE /memory` (quên tất cả của client này).

```
/chat (X-Client-Id) -> user_memory.for_policy -> Turn.memory ->  Policy.check(memory)
   sắp hỏi lại giữa >= 3 thủ tục gần nhau (và câu KHÔNG nêu nguyên tên một ứng viên):
      lọc ứng viên theo đối tượng đã nhớ (ứng viên không khai đối tượng = chưa biết, giữ)
        đúng 1 hợp, mọi ứng viên khác chắc chắn không hợp -> KHÔNG hỏi, chọn nó  + "Theo hồ sơ của bạn (đối tượng: ...) mình chọn «...»"
        2..n-1 hợp                                          -> thẻ hỏi lại chỉ còn các ứng viên hợp (>= 2)
        không ai hợp / ai cũng hợp                          -> giữ nguyên thẻ
   chọn bản mặc định của nhóm biến thể: bản mặc định không hợp, có biến thể hợp (không gắn tỉnh, cấp xã) -> ưu tiên nó
   sau khi bấm nút của thẻ hỏi lại -> server gợi ý {subject đặc trưng} -> UI hỏi "Nhớ đối tượng ...?" (người dùng bấm mới lưu)
```
Hồ sơ chỉ **ưu tiên**: không có hồ sơ (hoặc `other`) thì `memory=None` và hành vi y hệt trước Phase 26; câu nêu nguyên tên một ứng viên thì hồ sơ không can thiệp. Ghi chú hồ sơ đã ảnh hưởng nằm ở `trace["memory"]`. UI: nút "Hồ sơ của bạn" (form, danh sách đã nhớ, "Quên" từng mục, "Quên tất cả", "Bỏ qua") và thanh gợi ý nhớ sau khi bấm nút thẻ hỏi lại.

## Dev mode và bản cuối
Mọi thứ hiện giờ là developer mode; việc tách chế độ người dùng, che PII, quyền hộp thoại, công tắc AI: [FINAL_PRODUCT_CHECKLIST.md](FINAL_PRODUCT_CHECKLIST.md) (thẻ `FINAL-PRODUCT:` trong code).

## Dữ liệu
1.350 thủ tục cấp xã/phường, 12 field mỗi thủ tục. Chỉ 467/1.350 có phí dùng được. 84 nhóm thủ tục có nhiều biến thể; `default_variant` tự sinh (tên ngắn nhất, ưu tiên bản không thuộc tỉnh), chưa admin duyệt (xem `/dev/variants.html`). Lệ phí từ corpus nhóm (`team_fee_overlay`, 15 thủ tục) chỉ dùng khi cổng không có lệ phí, ghi nguồn "Bộ dữ liệu nhóm". Chi tiết: [../data/DATA_NOTES.md](../data/DATA_NOTES.md).

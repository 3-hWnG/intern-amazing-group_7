# Kiến trúc System 3

System 3 là trợ lý hỏi đáp thủ tục hành chính **cấp xã/phường** (tiếng Việt), độc lập với System 1/2 của V10.6. Chỉ dùng lại **dữ liệu** thủ tục (snapshot trong `data/snapshot`).
Mục tiêu và các quyết định ban đầu: [PLAN_SYSTEM3.md](PLAN_SYSTEM3.md). Kế hoạch đợt 3: [PLAN_SYSTEM3_DOT3.md](PLAN_SYSTEM3_DOT3.md).

## Luồng một lượt hỏi
```
User
 -> Orchestrator   pre_check (chèn lệnh, cắt 2000 ký tự), nạp trạng thái hội thoại
 -> Planner        LUẬT: tách câu thành tasks (tối đa 3), chọn thủ tục, fields, điều kiện, quan hệ
                    (tuỳ chọn mode=hybrid: Qwen3-4B đề xuất song song, hợp nhất ở dưới)
 -> Policy/Router  LUẬT: kiểm căn cứ, phạm vi, field_status, biến thể mặc định, hỏi lại
 -> Answerer       CODE: trích nguyên văn dữ liệu + nguồn
 -> (LLM sinh chữ) chỉ cho giải thích điều kiện / so sánh; mỗi ý có trích dẫn, qua verifier
 -> User           câu trả lời + nguồn; ghi bộ nhớ và trace
```

Nguyên tắc:
- **Planner không dùng LLM** (mặc định `S3_PLANNER_MODE=rules`). Phase 19 đo hybrid công bằng (timeout 7 s): không đạt gate nên giữ tắt (eval/P19_REPORT.md).
- **Planner hybrid** (`server/planner/hybrid.py`, `S3_PLANNER_MODE=hybrid`): luật luôn dựng kế hoạch trước; Qwen3-4B (think=False, schema gọn `tasks[{action,cand,fields}] + confidence`, chọn ứng viên bằng chỉ số `cand`, không tự đưa mã/số) chạy trong thread có hạn cứng `PLANNER_LLM_TIMEOUT` (7 s). `diff` rút các thay đổi (`edit_fields | edit_proc | add_task | delete_task`); `merge` chỉ nhận khi `confidence >= PLANNER_LLM_CONFIDENCE` VÀ: thủ tục có trong kho, field thuộc `FIELD_TITLE`, task luật không bị khoá (hỏi lại/xin lỗi/mơ hồ/`near`/so sánh/kế thừa ngữ cảnh), và chạy thử `policy.check` trên kế hoạch mới cho cùng hành vi + task bị sửa vẫn `direct`. Quá hạn/lỗi/JSON hỏng -> giữ kế hoạch luật. Policy vẫn chạy sau cùng trên kế hoạch cuối. Nhật ký đầy đủ ở `trace["planner_llm"]` (gọi hay không, ms, timeout, đề xuất + lý do chấp nhận/từ chối, kế hoạch luật vs kế hoạch cuối), hiện trong dev panel. `GET /config` (mode, timeout, ngưỡng, model, model đã nạp), `POST /config` (đổi trong bộ nhớ, chỉ khi `S3_DEV=1`).
- **LLM chỉ sinh chữ**, không chọn thủ tục, không viết số. Ý nào không có trích dẫn hợp lệ hoặc có số/tên văn bản/"miễn phí" không nằm trong dữ liệu thì bị bỏ; lỗi hoặc timeout (5 s) thì giữ câu trả lời bằng code.
- Không suy ra "miễn phí" khi dữ liệu trống: trả "cổng không công bố".
- Hỏi lại tối đa một lần; sau khi người dùng trả lời thì chọn thủ tục gần nhất, không hỏi lần hai.
- Từ **3 thủ tục/biến thể gần nhau** mà câu hỏi không phân biệt được → hỏi lại (nút bấm + gõ tự do). Câu chỉ nêu **tên một lĩnh vực** (`domain`: "hộ tịch", "đất đai", "cư trú"...) cũng hỏi lại, đại diện = mỗi họ một bản. 2 biến thể → trả bản mặc định kèm nút "dạng khác".
- **Đúng trọng tâm**: chỉ trả mục người dùng hỏi (kể cả mục kế thừa từ câu trước khi là câu nối/sửa ý/"chắc không?"); không nêu mục nào → bản tóm tắt ngắn, riêng câu điều kiện → `components` + phần trường hợp. Cụm hỏi mục ("giải quyết trong bao lâu", "cần gì", "ở đâu") và lời kể hoàn cảnh KHÔNG là task thứ hai; task thứ hai chỉ khi được nêu riêng (mục hỏi hoặc động từ yêu cầu).
- **Trường hợp/điều kiện**: hoàn cảnh khớp CHẮC một mục `condition_index` (source=case) thì chỉ trả giấy tờ của trường hợp đó (`policy._strong_case`, `answerer._case_pick`), kèm nguồn; không có dữ liệu thì nói cổng không công bố riêng.
- Ngoài phạm vi (cấp tỉnh, không có trong kho, chủ đề lạ, chèn lệnh) → xin lỗi kèm lý do. Nếu kho có thủ tục thì trả lời theo kho.

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
| `retrieval/query.py` | hiểu câu: cụm chỉ-field (phí, giấy tờ, nộp ở đâu…), từ dừng, cụm bảo vệ, viết tắt, tách câu |
| `retrieval/rank.py` | xếp hạng IDF có tính dấu, cổng phạm vi, cờ uncertain/ambiguous/near, chitchat |
| `retrieval/refs.py` | phủ định ("không phải X"), thứ tự ("cái thứ hai") |
| `retrieval/context.py` | trạng thái hội thoại và quyết định follow-up (xem dưới) |
| `server/planner/` | dựng Plan từ kết quả retrieval; `hybrid.py` hợp nhất đề xuất LLM (tuỳ chọn, tắt mặc định); nhánh LLM cũ tắt |
| `server/policy/` | guardrail và router |
| `server/answer/` | `answerer.py` (code), `llm_answer.py` + `verifier.py` (sinh chữ có kiểm) |
| `server/orchestrator.py` | điều phối một lượt, bộ nhớ, trace |
| `server/db/` | SQLite hội thoại: `conversations`, `messages`, `session_facts`, `shown_procedures`, `conv_state`, `turn_traces` |
| `web/` | UI chat (copy từ V10.6 và sửa) |

## Bộ nhớ hội thoại (`retrieval/context.py`)
Trạng thái gồm chủ đề, lịch sử thủ tục đã nói (theo thứ tự), mục đang hỏi, lời kể chưa gắn thủ tục. Mỗi câu được phân vào một loại, lý do ghi vào `trace["ctx"]`:
`follow_up` (cùng thủ tục) · `new_related` (thủ tục mới cùng lĩnh vực) · `return` (quay lại thủ tục đã nói) · `independent`/`new` (không kế thừa) · `correction` (sửa ý) · `story` (lời kể hoàn cảnh).
Fact người dùng kể gắn với thủ tục lúc ghi; đổi sang thủ tục khác họ thì không rò sang. Nút "Bắt đầu chủ đề mới" hoặc câu "hỏi việc khác" xoá fact và danh sách đã hiển thị.

## Dữ liệu
1.350 thủ tục cấp xã/phường, 12 field mỗi thủ tục. Chỉ 467/1.350 có phí dùng được. 84 nhóm thủ tục có nhiều biến thể; `default_variant` tự sinh (tên ngắn nhất, ưu tiên bản không thuộc tỉnh), chưa admin duyệt (xem `/dev/variants.html`). Chi tiết: [../data/DATA_NOTES.md](../data/DATA_NOTES.md).

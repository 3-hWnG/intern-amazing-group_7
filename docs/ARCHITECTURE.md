# Kiến trúc System 3

System 3 là trợ lý hỏi đáp thủ tục hành chính **cấp xã/phường** (tiếng Việt), độc lập với System 1/2 của V10.6. Chỉ dùng lại **dữ liệu** thủ tục (snapshot trong `data/snapshot`).
Mục tiêu và các quyết định ban đầu: [PLAN_SYSTEM3.md](PLAN_SYSTEM3.md). Kế hoạch đợt 3: [PLAN_SYSTEM3_DOT3.md](PLAN_SYSTEM3_DOT3.md).

## Luồng một lượt hỏi
```
User
 -> Orchestrator   pre_check (chèn lệnh, cắt 2000 ký tự), nạp trạng thái hội thoại
 -> Planner        LUẬT: tách câu thành tasks (tối đa 3), chọn thủ tục, fields, điều kiện, quan hệ
 -> Policy/Router  LUẬT: kiểm căn cứ, phạm vi, field_status, biến thể mặc định, hỏi lại
 -> Answerer       CODE: trích nguyên văn dữ liệu + nguồn
 -> (LLM sinh chữ) chỉ cho giải thích điều kiện / so sánh; mỗi ý có trích dẫn, qua verifier
 -> User           câu trả lời + nguồn; ghi bộ nhớ và trace
```

Nguyên tắc:
- **Planner không dùng LLM** (mặc định). LLM 4B không cải thiện số đo mà thêm độ trễ.
- **LLM chỉ sinh chữ**, không chọn thủ tục, không viết số. Ý nào không có trích dẫn hợp lệ hoặc có số/tên văn bản/"miễn phí" không nằm trong dữ liệu thì bị bỏ; lỗi hoặc timeout (5 s) thì giữ câu trả lời bằng code.
- Không suy ra "miễn phí" khi dữ liệu trống: trả "cổng không công bố".
- Hỏi lại tối đa một lần; sau khi người dùng trả lời thì chọn thủ tục gần nhất, không hỏi lần hai.
- Từ **3 thủ tục/biến thể gần nhau** mà câu hỏi không phân biệt được → hỏi lại (nút bấm + gõ tự do). 2 biến thể → trả bản mặc định kèm nút "dạng khác".
- Ngoài phạm vi (cấp tỉnh, không có trong kho, chủ đề lạ, chèn lệnh) → xin lỗi kèm lý do. Nếu kho có thủ tục thì trả lời theo kho.

## Module
| Đường dẫn | Vai trò |
|---|---|
| `data/` | build DB từ snapshot, bảng `fees_clean`, `field_chunks`, `condition_index`, `families`, `synonyms`; `api.py` là cửa vào duy nhất |
| `retrieval/query.py` | hiểu câu: cụm chỉ-field (phí, giấy tờ, nộp ở đâu…), từ dừng, cụm bảo vệ, viết tắt, tách câu |
| `retrieval/rank.py` | xếp hạng IDF có tính dấu, cổng phạm vi, cờ uncertain/ambiguous/near, chitchat |
| `retrieval/refs.py` | phủ định ("không phải X"), thứ tự ("cái thứ hai") |
| `retrieval/context.py` | trạng thái hội thoại và quyết định follow-up (xem dưới) |
| `server/planner/` | dựng Plan từ kết quả retrieval; nhánh LLM tắt |
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

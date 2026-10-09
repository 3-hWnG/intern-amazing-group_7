# System 3 — server

FastAPI + hàng đợi 1 worker + SQLite riêng (`runtime/system3.db`, tự tạo từ `db/schema.sql`).
Không phụ thuộc `repo/` (V10.6). Frontend ở `../web/`, server phục vụ tại `/`.
Pipeline đầy đủ (đã hết "STUB"): `orchestrator.handle_turn` = Orchestrator (pre_check, nạp trạng thái) → Planner (luật; hybrid tuỳ chọn) → Policy/Router → Answerer (code + nguồn) → [bước sinh chữ LLM, có verifier]. Chi tiết: [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

## Chạy
```
pip install -r requirements.txt
set PYTHONIOENCODING=utf-8
python ../run_server.py        # từ thư mục gốc: python run_server.py   -> http://127.0.0.1:8300
python smoke_test.py           # test đầu-cuối với DB tạm (S3_USE_LLM=0, không cần Ollama)
```
`run_server.py` (ở gốc) đăng ký package `system3` nên không cần `PYTHONPATH`, thư mục gốc tên gì cũng được. Chạy `python main.py` trực tiếp cũng được khi thư mục tên `system3` và `PYTHONPATH` trỏ vào thư mục cha.
Mở `http://127.0.0.1:8300/?dev=1` để xem plan/trace JSON dưới mỗi câu trả lời (khung dev ở trình duyệt; server chỉ gửi `dev{...}` khi `S3_DEV=1`).
Env (đầy đủ ở [../docs/SETUP.md](../docs/SETUP.md), nguồn `config.py`): `APP_HOST`, `APP_PORT`(8300), `S3_DB_PATH`, `S3_DATA_DB`, `S3_DEV`(**0** mặc định; 1: `/chat` kèm `dev{plan,trace,total_ms}`, `POST /config`, `/dev/*`), `S3_USE_LLM`(1: bước sinh chữ), `ANSWER_LLM_TIMEOUT`(7.0), `S3_PLANNER_MODE`(rules|hybrid), `PLANNER_LLM_TIMEOUT`(7.0), `S3_NO_WARMUP`, `OLLAMA_HOST`, `LLM_MODEL`(qwen3:4b), `LLM_NUM_CTX`, `LLM_KEEP_ALIVE`, `LLM_THINK`(0), `QUEUE_MAX_DEPTH`, `S3_TABLE_BUTTON`(1).
Có thể đặt trong `server/.env`.

## API
- `GET /health` -> `{ok, model, queue_depth, dev}`
- `POST /chat {text, conversation_id?, reply_to?}` -> `{conversation_id, message_id, blocks:[{title,text,sources[]}], clarify?:{question,options[],allow_free_text}, kind}` (+ `dev` khi `S3_DEV=1`).
  Không có `conversation_id` (hoặc id lạ) -> server cấp mới. `reply_to` = `message_id` của thẻ clarify đang trả lời. Hàng đợi đầy -> 503.
- `GET /config` -> mode/ngưỡng/timeout của Planner hybrid, `model`, `loaded`, `model_loaded`, `dev`, `modes`, `answer_llm` (= `S3_USE_LLM`), `answer_timeout`, `table_button`.
  `POST /config {mode?, confidence?, timeout?, answer_llm?}` đổi trong bộ nhớ (mất khi khởi động lại); chỉ khi `S3_DEV=1` (403 nếu không); `timeout` là của Planner hybrid.
- `GET /procedure/{proc_id}/table` -> bảng đủ 12 mục + nguồn, nguyên văn dữ liệu, không LLM (404 nếu không có thủ tục hoặc `S3_TABLE_BUTTON=0`).
- Hộp thoại: `GET /conversations`; `PATCH /conversations/{id} {title?, pinned?}`; `DELETE /conversations/{id}`; `DELETE /conversations` (xoá TẤT CẢ, của mọi người: xem FINAL_PRODUCT_CHECKLIST mục 3);
  `GET /conversations/{id}/export?format=md|json|pdf` (md/json tải về; pdf = trang HTML in được, trình duyệt tự mở hộp thoại in để Lưu thành PDF; không kèm plan/trace).
- `GET /conversations/{id}/messages`, `GET /conversations/{id}/messages/{mid}/trace`
- `POST /conversations/{id}/reset_facts` — "Bắt đầu chủ đề mới": xoá fact, danh sách đã hiển thị, ghi trạng thái rỗng, chèn tin trợ lý "Đã bắt đầu chủ đề mới" làm tin cuối.
- Dev (`S3_DEV=1`, nếu không 404): `GET /dev/default_variants`, `GET /dev/variants.html`.

Bản cuối cho người dùng thường cần chặn plan/trace/`/config`, che PII, phân quyền hộp thoại: [../docs/FINAL_PRODUCT_CHECKLIST.md](../docs/FINAL_PRODUCT_CHECKLIST.md) (thẻ `FINAL-PRODUCT:` trong `main.py`, `db/store.py`...).

## Điểm cắm
`orchestrator.py::handle_turn(turn: Turn) -> dict`. `Turn` mang `text`, `reply_to`, `reply_to_clarify` (thẻ cũ), `history` (<=5 lượt), `session_facts`, `shown_procedures`, `state`.
Trả về `{kind, blocks, clarify, plan, trace}`; `main.py` lưu `plan` vào `messages.plan_json`, `trace` vào `turn_traces`.
Hàm chạy trong thread của worker duy nhất; ghi memory bằng `db.store.add_fact` / `add_shown` / `set_state`.
Gọi LLM: `core.llm.chat(system, user, history, schema=<JSON schema>, think=False, timeout=...)` hoặc `chat_json(...)`. `core.llm.warm_up` chỉ chạy khi có đường LLM bật và không có `S3_NO_WARMUP=1`.

## Schema (`db/schema.sql`)
`conversations` (id, title, pinned), `messages` (assistant: `sources_json` chứa `{blocks, clarify}`; `plan_json`), `session_facts`, `shown_procedures`, **`conv_state`** (`state_json` = `ConvState` của `retrieval/context.py`: chủ đề, lịch sử thủ tục, mục đang hỏi, lời kể chưa gắn; orchestrator ghi theo thủ tục THỰC SỰ đã trả lời), `turn_traces`.

## Test
`tests/` (xem SETUP): `memory_test`, `context_test`, `answer_llm_test`, `planner_hybrid_test`, `p20_api_test`, `p23_input_test`; `smoke_test.py`; `e2e_test.py` (cần Ollama nếu bật LLM).

## File đã copy từ đâu
Xem `COPY_NOTES.md`.

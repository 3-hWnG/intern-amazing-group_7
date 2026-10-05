# System 3 — server

FastAPI + hàng đợi 1 worker + SQLite riêng (`runtime/system3.db`, tự tạo từ `db/schema.sql`).
Không phụ thuộc `repo/` (V10.6). Frontend ở `../web/`, server phục vụ tại `/`.

## Chạy
```
pip install -r requirements.txt
set PYTHONIOENCODING=utf-8
python main.py                 # http://127.0.0.1:8300
python smoke_test.py           # test đầu-cuối với DB tạm (không cần Ollama)
```
Mở `http://127.0.0.1:8300/?dev=1` để xem plan/trace JSON dưới mỗi câu trả lời.
Env: `APP_HOST`, `APP_PORT`(8300), `S3_DB_PATH`, `OLLAMA_HOST`, `LLM_MODEL`(qwen3:4b), `LLM_NUM_CTX`,
`LLM_KEEP_ALIVE`, `LLM_THINK`(0), `QUEUE_MAX_DEPTH`, `S3_DEV`(1: response `/chat` kèm `dev{plan,trace,total_ms}`).
Có thể đặt trong `server/.env`.

## API
- `GET /health`
- `POST /chat {text, conversation_id?, reply_to?}` -> `{conversation_id, message_id, blocks:[{title,text,sources[]}], clarify?:{question,options[],allow_free_text}, kind}`.
  Không có `conversation_id` (hoặc id lạ) -> server cấp mới. `reply_to` = `message_id` của thẻ clarify đang trả lời.
- `GET /conversations`, `GET /conversations/{id}/messages`, `GET /conversations/{id}/messages/{mid}/trace`

## Điểm cắm cho Planner
`orchestrator.py::handle_turn(turn: Turn) -> dict` — hiện là STUB. Phase sau thay thân hàm này
(Planner -> Validate/Router -> Executor -> Answerer). `Turn` đã mang sẵn: `text`, `reply_to`,
`reply_to_clarify` (thẻ cũ), `history` (<=5 lượt), `session_facts`, `shown_procedures`.
Trả về `{kind, blocks, clarify, plan, trace}`; `main.py` lưu `plan` vào `messages.plan_json`, `trace` vào `turn_traces`.
Hàm chạy trong thread của worker duy nhất; ghi memory bằng `db.store.add_fact` / `add_shown`.
Gọi LLM: `core.llm.chat(system, user, history, schema=<JSON schema>, think=False)` hoặc `chat_json(...)`.
(Trong stub, gõ chữ có "clarify" để thử thẻ hỏi lại.)

## Schema (`db/schema.sql`)
conversations, messages (assistant: `sources_json` chứa `{blocks, clarify}`), session_facts, shown_procedures, turn_traces.

## File đã copy từ đâu
Xem `COPY_NOTES.md`.

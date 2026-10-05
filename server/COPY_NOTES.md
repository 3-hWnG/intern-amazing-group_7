# COPY_NOTES — System 3 vs V10.6

Nguồn: `D:\Finale_architect\repo\` (V10.6). Không import ngược; mọi thứ dưới đây là bản sao đã sửa.

## Đã copy
| System 3 | Nguồn V10.6 | Thay đổi |
|---|---|---|
| `core/queue.py` | `Backend/core/queue.py` | nguyên bản; `QUEUE_CONCURRENCY=1` trong `config.py` |
| `core/llm.py` | `Backend/core/llm.py` | giữ `chat`/`chat_json`/`warm_up`/`_salvage_json`, `keep_alive`; bỏ ROLE_OPTIONS/verify/status/model_info; thêm `schema` -> `format`, `think` (qwen3 tắt thinking, mặc định `LLM_THINK=0`) |
| `config.py` | `config.py` (gốc repo) | rút gọn: chỉ server, Ollama, queue, DB, `S3_DEV` |
| `main.py` | `Backend/main.py` | chỉ lifespan (init DB + queue) + routes; bỏ MCP, auth, dev_routes, file/procedure routes |
| `db/store.py` | ý tưởng `Backend/db/connection.py` + `repositories.py` | viết lại nhỏ gọn (sqlite3, kết nối ngắn) |
| `../web/static/css/styles.css` | `Frontend/static/css/styles.css` | chỉ dòng 1-200 (layout, chat, composer) và 255-370 (thẻ lựa chọn); bỏ login/dev/memory/procedure |
| `../web/static/js/chat.js` | khung `chat.js` + `conversations.js` + `api.js` | viết lại một file: blocks[], thẻ clarify, dev panel |
| `../web/templates/index.html` | `Frontend/templates/index.html` | bỏ modal bộ nhớ/onboarding, nút Web search, Tìm chính xác, đính kèm, đăng xuất |

## Gỡ / không copy
- MCQ: `retrieval_pending`, `user_mcq_memory`, `AXIS_*`, `procedure.js`, `memory.js`, `exact.js`.
- System 1: `mcp_search/`, `mcp_client.py`, `system_websearch.py`, `evidence.py`, `systems.js`, nút Web search.
- System 2: `procedure_table.py`, `system_retrieval.py`, `intent.py`, `verifier.py`, `summarizer.py`, `prompts/`, `chunk_index.py`.
- Auth/đăng ký (`auth.py`, `auth_routes.py`, `login.html`, `auth.js`): thay bằng session ẩn danh (server cấp `conversation_id`, client giữ trong localStorage).
- `dev_routes.py`, `dev.js`, `eval_export.py`, `file_routes.py`/`files.js` (đính kèm), `domain/text.py` (sẽ viết lại ở Phase 1 trong `system3/data`).

## Phần gắn chặt cần giữ
Không có. `queue.py` chỉ phụ thuộc 3 hằng số config. `llm.py` chỉ phụ thuộc config.
Lưu ý: hàng đợi V10.6 thiết kế cho streaming chữ (`emit`); System 3 chưa stream nên `/chat` chỉ chờ job xong.

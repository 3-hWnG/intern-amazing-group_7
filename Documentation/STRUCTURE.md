# Cấu trúc thư mục V10.3 / Folder layout

Tài liệu này trả lời hai câu hỏi: **thư mục nào chứa gì**, và **cái cũ ở V10.2
giờ nằm đâu**.

---

## 1. Nguyên tắc / Principles

1. **Tên thư mục nói đúng nội dung.** `Backend/` chỉ có mã máy chủ, `Frontend/`
   chỉ có giao diện — không trộn lẫn như `app/static` ngày trước.
2. **`config.py` nằm ở GỐC**, ngoài cả `Backend/` và `Frontend/`. Sửa cấu hình
   không phải đi tìm trong mã nguồn. Mọi đường dẫn thư mục được định nghĩa một
   lần ở đầu file này — đổi bố cục thì chỉ sửa ở đó.
3. **Dữ liệu sống tách khỏi dữ liệu nguồn.** `Database/runtime/` (thay đổi liên
   tục, không commit) khác hẳn `Database/corpus/` (cố định, có commit).
4. **Mọi thứ chạy được bằng cách bấm đôi.** `.bat` ở gốc, không cần mở terminal.

---

## 2. Từng thư mục / Folder by folder

### `Backend/` — máy chủ
Mã nguồn FastAPI. Các gói con import theo tên phẳng (`from core import ...`)
vì `Backend/` được đưa vào `sys.path` trong `Backend/main.py`.

| Thư mục | Nội dung |
|---|---|
| `api/` | Các route HTTP: xác thực, hội thoại, tệp đính kèm, công cụ dev |
| `core/` | Pipeline trả lời. `orchestrator` = bộ CHỌN hệ thống · `turn` = hợp đồng `TurnInput`/`TurnResult` · `system_websearch` = Hệ thống 1 · `system_retrieval` = Hệ thống 2 (mặc định) · `procedure_table` = dựng bảng thủ tục bằng code · `intent` · `evidence` · `answer` · `verifier` · `llm` · `queue` · `mcp_client` |
| `db/` | `connection.py` (nơi DUY NHẤT mở CSDL) + `repositories.py` (mọi câu SQL) |
| `domain/` | Xử lý văn bản thuần tuý (BM25, chuẩn hoá tiếng Việt) |
| `mcp_search/` | MCP server: tra web → xếp hạng → đọc trang → Evidence Pack |
| `prompts/` | Mẫu prompt gửi cho mô hình |
| `main.py` | Điểm khởi động: dựng app, mount static, bật hàng đợi |

> **Hai hệ thống trả lời.** Nút "Web search" cạnh ô nhập chuyển giữa Hệ thống 1
> (`system_websearch.py`, tra web) và Hệ thống 2 (`system_retrieval.py`, CSDL nội
> bộ — mặc định; nút 🎯 Tìm chính xác ở `Frontend/static/js/exact.js`). Đổi hệ thống sẽ mở cuộc trò chuyện mới. Chi tiết: mục 0 của
> `ARCHITECTURE.md`.

### `Frontend/` — giao diện
HTML + CSS + JavaScript thuần, **không framework, không bước build**.
`static/` được FastAPI phục vụ ở `/static`; `templates/` là HTML đọc thẳng.
Sửa JS/CSS xong nhớ tăng `STATIC_VERSION` trong `config.py` để trình duyệt
không dùng bản cache cũ.

Hệ thống 2 ở giao diện: `systems.js` (nút đổi hệ thống) · `exact.js` (nút
🎯 Tìm chính xác) · `procedure.js` (bảng thủ tục, MCQ, chip gợi ý, hộp thoại
ô chat mới) · `chat.js` (nhãn 📚 / 🤖 / ⚠️ theo `answer_source`).

### `Database/` — dữ liệu
| Đường dẫn | Là gì | Commit? |
|---|---|---|
| `schema.sql` | Định nghĩa bảng SQLite của `app.db` | ✅ có |
| `pipeline/` | Cào + chuẩn hoá + nạp CSDL thủ tục (`run_pipeline.py`); `retrieval.py` = cửa DUY NHẤT Hệ thống 2 đọc CSDL thủ tục | ✅ có |
| `staging/` | `procedures.jsonl` (1.350 thủ tục đã chuẩn hoá) + `vocabulary.json` | ✅ có |
| `raw/` | JSON thô + biểu mẫu `.docx` tải từ cổng (dựng lại được bằng `run_pipeline`) | ❌ không |
| `corpus/` | `.xlsx`, `.json`, `.md` — dữ liệu thủ tục gốc (Evaluation, fine-tune) | ✅ có |
| `runtime/app.db` | CSDL đang chạy: tài khoản, lịch sử, tệp tải lên | ❌ **không bao giờ** |
| `runtime/procedures.db` | CSDL thủ tục của Hệ thống 2 (SQLite + FTS5) | ❌ không — máy nào cũng tự cào |

> **Quan trọng:** ứng dụng khi chạy **không đọc** `corpus/`. Hệ thống 1 lấy câu
> trả lời từ web qua MCP; Hệ thống 2 đọc `runtime/procedures.db` qua
> `pipeline/retrieval.py`. `corpus/` chỉ phục vụ `Evaluation/` và fine-tune.
> *The running app does not read `corpus/` — System 1 answers from live web
> search, System 2 from `runtime/procedures.db`.*

**Đổi sang CSDL khác về sau / swapping the database.** SQLite là mặc định và
chạy được ngay. Khi cần CSDL đầy đủ hơn:
1. Đặt `DB_BACKEND=postgres` (hoặc tên khác) trong `.env`;
2. Viết bản cài đặt mới trong **đúng hai file** `Backend/db/connection.py` và
   `Backend/db/repositories.py`, rồi bỏ dòng `raise NotImplementedError` đi.

Không chỗ nào khác trong mã nguồn mở `app.db` trực tiếp, nên không phải sửa thêm.
(`procedures.db` là CSDL riêng của Hệ thống 2, chỉ mở qua `Database/pipeline/`.)

### `Evaluation/` — chấm điểm
`evaluate.py` chấm cả pipeline; `gen_queries_baseline.py` + `analyze_queries.py`
+ `search_baseline.py` chấm riêng chất lượng truy vấn tìm kiếm;
`build_eval_set.py` sinh bộ câu hỏi từ `Database/corpus/data_merged.xlsx`.
Kết quả ghi vào `Evaluation/results/` (không commit).

### `Utility/` — công cụ
| Đường dẫn | Dùng để |
|---|---|
| `finetune/` | Huấn luyện QLoRA, xuất dataset, gộp & lượng tử hoá, đo tốc độ |
| `scripts/run.ps1` | Chạy app / MCP / eval / benchmark bằng tham số |
| `scripts/setup.ps1` | Cài đặt lần đầu (gọi từ `Setup First Time.bat`) |
| `scripts/make_index.py` | Sinh lại `Documentation/CODEBASE_INDEX.md` |
| `scripts/fix_venv.py` | Sửa `.venv` sau khi copy / di chuyển thư mục |

### `Documentation/` — tài liệu
`ARCHITECTURE.md` (hệ thống chạy thế nào) · `CODEBASE_INDEX.md` (bản đồ mã
nguồn, sinh tự động) · `STRUCTURE.md` (file này) · `SETUP.md` (cài trên máy
mới) · `FAILURE_HANDLING.md` (hỏng thì làm gì) · `PLAN_SYSTEM2_REBUILD.md`
(Hệ thống 2 hiện tại — V10.5: quyết định, số đo, việc còn lại) ·
`PHASE2_RETRIEVAL.md` (Hệ thống 2 bản đầu — V10.3, giữ để đối chiếu số đo) ·
`legacy/` (tài liệu V10.2 giữ nguyên để đối chiếu). Phase 1 (cào + CSDL):
`Database/PHASE1_PLAN.md`.

### `Extra/` — không thuộc nhóm nào
Docker (`Dockerfile`, `docker-compose*.yml`), cấu hình VS Code, `dataset.json`,
`System 1.pdf`, `download.svg`. Ứng dụng **không phụ thuộc** vào thư mục này.

---

## 3. Đối chiếu V10.2 → V10.3 / Migration map

| V10.2 | V10.3 |
|---|---|
| `app/config.py` | `config.py` *(ra gốc)* |
| `app/main.py`, `app/api/`, `app/core/`, `app/db/`, `app/domain/`, `app/mcp_search/`, `app/prompts/`, `app/developer_mode.py` | `Backend/…` |
| `app/static/`, `app/templates/` | `Frontend/static/`, `Frontend/templates/` |
| `app/db/schema.sql` | `Database/schema.sql` |
| `app/runtime/app.db` | `Database/runtime/app.db` *(đã chép sang, giữ nguyên dữ liệu)* |
| `data/*.xlsx, *.json, *.md` | `Database/corpus/` |
| `finetune/` | `Utility/finetune/` |
| `run.ps1` | `Utility/scripts/run.ps1` |
| `docs/ARCHITECTURE.md` | `Documentation/ARCHITECTURE.md` |
| `README.md`, `BAO_CAO_THAY_DOI.md`, `CHANGELOG_*`, `PLAN_*`, `TASK_*` | `Documentation/legacy/` |
| `Dockerfile`, `docker-compose*.yml`, `.vscode/` | `Extra/` |
| *(chưa có)* | `Launch Web.bat`, `Setup First Time.bat`, `Documentation/CODEBASE_INDEX.md` |

### Những chỗ mã nguồn đã phải sửa theo / Code changes this required

Tái cấu trúc **không chỉ là chuyển file** — các đường dẫn sau được viết lại:

| File | Sửa gì |
|---|---|
| `config.py` | Thêm `PROJECT_ROOT`, `BACKEND_DIR`, `FRONTEND_DIR`, `DATABASE_DIR`, `UTILITY_DIR`…; `STATIC_DIR`/`TEMPLATES_DIR` trỏ sang `Frontend/`; `RUNTIME_DIR` sang `Database/runtime`; thêm `SCHEMA_PATH`, `CORPUS_DIR`, `DB_BACKEND`. `APP_DIR` giữ làm tên cũ (alias) để mã cũ không gãy. |
| `Backend/main.py` | Đưa **cả** `Backend/` và thư mục gốc vào `sys.path` (gốc để tìm thấy `config.py`) |
| `Backend/db/connection.py` | Lấy `SCHEMA_PATH` từ `config` thay vì cạnh file; thêm cổng kiểm tra `DB_BACKEND` |
| `Backend/core/mcp_client.py` | `APP_DIR` → `BACKEND_DIR` |
| `Backend/mcp_search/server.py` | `sys.path` thêm cả gốc dự án |
| `Evaluation/*.py`, `Utility/finetune/*.py` | `…/"app"` → `…/"Backend"` + thư mục gốc |
| `Utility/scripts/run.ps1` | Gốc dự án lùi 2 cấp; đường dẫn `Backend\main.py`, `Utility\finetune\…` |
| `Extra/Dockerfile`, `Extra/docker-compose.yml` | Copy `Backend/`, `Frontend/`, `config.py`; build context là thư mục gốc |

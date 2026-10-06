# Cài đặt và chạy System 3

## Yêu cầu
- Python 3.12 (đã thử trên Windows 10).
- [Ollama](https://ollama.com) và model `qwen3:4b` — chỉ cần cho bước LLM sinh chữ giải thích điều kiện/so sánh. Planner chạy bằng luật nên **không cần LLM để hệ thống trả lời** (đặt `S3_USE_LLM=0`).
- GPU không bắt buộc. Máy dev: GTX 1660 Super 6 GB, qwen3:4b chạy 100% GPU.

## Cấu trúc thư mục khi clone
Mã import theo dạng `system3.*`, nên **thư mục cha của `system3/` phải nằm trong `PYTHONPATH`**.
Gọi thư mục cha là `<ROOT>`:
```
<ROOT>/system3/...
```

## 1. Cài gói
```bash
cd <ROOT>/system3
python -m venv .venv
.venv\Scripts\activate          # Windows;  Linux/mac: source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Dựng cơ sở dữ liệu (một lần, ~20 giây)
DB (`data/runtime/system3.db`, 58 MB) không nằm trong git. Dựng từ snapshot `data/snapshot/procedures.jsonl`:
```bash
cd <ROOT>
python -m system3.data.build
python -m system3.data.tests.test_data     # kiểm tra
```
Build **xoá và dựng lại** `data/runtime/system3.db`. Muốn dựng ra chỗ khác (không đè DB đang dùng): đặt `S3_DATA_DB=<đường dẫn>` cho cả lệnh build, test_data, server và eval.

## 3. Chạy server
```bash
cd <ROOT>/system3/server
set PYTHONPATH=<ROOT>                      # Linux/mac: export PYTHONPATH=<ROOT>
python main.py                             # http://127.0.0.1:8300
```
Biến môi trường (xem `server/config.py`):

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `APP_HOST` / `APP_PORT` | 127.0.0.1 / 8300 | địa chỉ server |
| `S3_DATA_DB` | `data/runtime/system3.db` | DB thủ tục (dữ liệu, chỉ đọc khi chạy) |
| `S3_DB_PATH` | `server/runtime/system3.db` | DB hội thoại (tự tạo) |
| `S3_DEV` | 0 | 1 = trả kèm plan/trace; bật `/dev/variants.html` và `/dev/default_variants` |
| `S3_USE_LLM` | 1 | 0 = tắt hẳn bước LLM sinh chữ |
| `S3_PLANNER_LLM` | 0 | 1 = bật nhánh Planner dùng LLM cũ (tắt vì không cải thiện số đo) |
| `S3_PLANNER_MODE` | rules | `hybrid` = Planner luật + Qwen3-4B (Phase 19; không bật mặc định vì không tăng điểm, xem eval/P19_REPORT.md). Đổi trong bộ nhớ: `POST /config` khi `S3_DEV=1`; xem: `GET /config` |
| `PLANNER_LLM_TIMEOUT` | 7.0 | giây chờ LLM của Planner hybrid; quá hạn thì giữ kế hoạch luật |
| `PLANNER_LLM_CONFIDENCE` | 0.99 | LLM chỉ được sửa kế hoạch khi confidence >= ngưỡng (0.99 ít hại nhất khi quét trên DEV) |
| `PLANNER_LLM_DRAFT` | 0 | 1 = LLM thấy bản nháp luật và chỉ sửa khi chắc nó sai (biến thể đo, ít hại hơn nhưng vẫn không tăng điểm) |
| `PLANNER_LLM_NUM_PREDICT` | 220 | trần token đầu ra của LLM Planner |
| `S3_PLANNER_LLM_CACHE` | (trống) | CHỈ để đo: tệp jsonl phát lại đề xuất LLM (quét ngưỡng không gọi lại model) |
| `S3_TABLE_BUTTON` | 1 | 0 = tắt nút "Tạo bảng full" và endpoint `GET /procedure/{proc_id}/table` (câu trả lời về như cũ) |
| `LLM_MODEL` | qwen3:4b | model Ollama |
| `OLLAMA_HOST` | http://127.0.0.1:11434 | địa chỉ Ollama |
| `LLM_KEEP_ALIVE` | 30m | giữ model trong VRAM |

Endpoint Phase 20: `GET /procedure/{proc_id}/table` (bảng đủ 12 mục + nguồn, nguyên văn dữ liệu, 404 nếu không có thủ tục/cờ tắt). `GET /config` thêm `answer_llm` (= `S3_USE_LLM`), `answer_timeout`, `model_loaded`, `table_button`; `POST /config {answer_llm, mode, confidence, timeout}` đổi trong bộ nhớ (mất khi khởi động lại), chỉ khi `S3_DEV=1` (403 nếu không). UI: nút "AI: bật/tắt" ở đầu khung chat mở panel cấu hình; không dev thì panel chỉ xem.

Khi khởi động server tự nạp trước model ở thread nền, không chặn `/health`.

## 4. Chạy test
```bash
cd <ROOT>/system3/server
python tests/memory_test.py      # bộ nhớ, reset, endpoint dev (không gọi LLM)
python tests/context_test.py     # quyết định follow-up
python tests/answer_llm_test.py  # verifier + fallback, dùng LLM giả
python tests/planner_hybrid_test.py  # hợp nhất Planner hybrid, LLM giả (đề xuất sai/ngưỡng thấp/timeout/JSON hỏng giữ luật)
python tests/p20_api_test.py     # bảng full, /config answer_llm, reset chủ đề (TestClient, không LLM)
set S3_USE_LLM=0 && python e2e_test.py   # chạy server tạm 5 lượt hội thoại
```
python smoke_test.py             # server tạm (DB tạm, cổng 8391, S3_USE_LLM=0): health, trả lời có nguồn, hỏi lại + bấm nút, messages/trace

## Sự cố thường gặp
- `ModuleNotFoundError: system3` → chưa đặt `PYTHONPATH=<ROOT>`.
- `no such table`/thiếu DB → chưa chạy bước 2.
- Lượt đầu có LLM chậm 3–10 s → model đang nạp; đợi prewarm hoặc đặt `S3_USE_LLM=0`.
- `pip install` báo `CERTIFICATE_VERIFY_FAILED` → mạng/proxy chặn chứng chỉ; sửa chứng chỉ hệ thống, đừng tắt kiểm tra SSL.
- Lỗi tiếng Việt khi in ra console Windows → `set PYTHONIOENCODING=utf-8`.

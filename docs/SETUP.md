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

## 2. Dựng cơ sở dữ liệu (một lần, ~1 phút)
DB (`data/runtime/system3.db`, 58 MB) không nằm trong git. Dựng từ snapshot `data/snapshot/procedures.jsonl`:
```bash
cd <ROOT>
python -m system3.data.build
python -m system3.data.tests.test_data     # kiểm tra
```

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
| `S3_DB_PATH` | `server/runtime/system3.db` | DB hội thoại (tự tạo) |
| `S3_DEV` | 0 | 1 = trả kèm plan/trace; bật `/dev/variants.html` và `/dev/default_variants` |
| `S3_USE_LLM` | 1 | 0 = tắt hẳn bước LLM sinh chữ |
| `S3_PLANNER_LLM` | 0 | 1 = bật nhánh Planner dùng LLM (tắt vì không cải thiện số đo) |
| `LLM_MODEL` | qwen3:4b | model Ollama |
| `OLLAMA_HOST` | http://127.0.0.1:11434 | địa chỉ Ollama |
| `LLM_KEEP_ALIVE` | 30m | giữ model trong VRAM |

Khi khởi động server tự nạp trước model ở thread nền, không chặn `/health`.

## 4. Chạy test
```bash
cd <ROOT>/system3/server
python tests/memory_test.py      # bộ nhớ, reset, endpoint dev (không gọi LLM)
python tests/context_test.py     # quyết định follow-up
python tests/answer_llm_test.py  # verifier + fallback, dùng LLM giả
set S3_USE_LLM=0 && python e2e_test.py   # chạy server tạm 5 lượt hội thoại
```
`server/smoke_test.py` là test từ thời bản stub và đang hỏng (đã biết, chưa sửa).

## Sự cố thường gặp
- `ModuleNotFoundError: system3` → chưa đặt `PYTHONPATH=<ROOT>`.
- `no such table`/thiếu DB → chưa chạy bước 2.
- Lượt đầu có LLM chậm 3–10 s → model đang nạp; đợi prewarm hoặc đặt `S3_USE_LLM=0`.
- Lỗi tiếng Việt khi in ra console Windows → `set PYTHONIOENCODING=utf-8`.

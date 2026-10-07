# Cài đặt và chạy System 3

## Yêu cầu
- Python 3.12 (đã thử trên Windows 10: 3.12.2 ở máy dev; bạn báo cài sạch được trên 3.12.8).
- [Ollama](https://ollama.com) và model `qwen3:4b` — cần cho bước LLM sinh chữ giải thích điều kiện/so sánh, **bật mặc định** (`S3_USE_LLM=1`, quyết định của nhóm). Planner chạy bằng luật nên **không cần LLM để hệ thống trả lời**: không có Ollama thì lượt đó rơi về câu trả lời bằng code; đặt `S3_USE_LLM=0` để tắt hẳn (và không nạp model).
- GPU không bắt buộc. Máy dev: GTX 1660 Super 6 GB, qwen3:4b chạy 100% GPU.

## Cấu trúc thư mục khi clone
Mã import theo dạng `system3.*`. **Dùng launcher `run_server.py` ở gốc**: nó tự đăng ký package `system3` trỏ vào thư mục chứa nó, nên clone về thư mục tên gì (`intern-amazing-group_7/`, `abc/`...) cũng chạy, không cần `PYTHONPATH`. Gọi thư mục clone là `<SYSTEM3>` (có `run_server.py`, `server/`, `data/` ngay bên trong).
```
python run_server.py                          # server
python run_server.py -m system3.data.build    # chạy một module của package
python run_server.py server/tests/memory_test.py   # hoặc một script, với `system3` đã đăng ký
```
Kiểm đúng cách: đã thử bản sao vào thư mục tên `abc_xyz` (không có `.git`, `data/runtime`, `eval/results`) và chạy build, `test_data`, `smoke_test`, `memory_test`, `context_test`, server trực tiếp (xem `eval/P24_REPORT.md`).
Các script `eval/*.py` cần `system3` import được: đặt `PYTHONPATH=<thư mục cha của system3>` nếu thư mục tên `system3`, hoặc chạy qua `python run_server.py eval/<script>.py ...` ở thư mục gốc (hoặc `-m` cho module). Ở dưới, các lệnh dạng `-m system3.*` được viết qua launcher nên chạy ở mọi tên thư mục.

## 1. Cài gói
```bash
cd <SYSTEM3>
python -m venv .venv
.venv\Scripts\activate          # Windows;  Linux/mac: source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Dựng cơ sở dữ liệu (một lần, ~20 giây)
DB (`data/runtime/system3.db`, 58 MB) không nằm trong git. Dựng từ snapshot `data/snapshot/procedures.jsonl`:
```bash
cd <SYSTEM3>
python run_server.py -m system3.data.build
python run_server.py -m system3.data.tests.test_data     # kiểm tra
```
Dựng lại toàn bộ đường đo (DB, DB V10.6 cho baseline, mọi gate không GPU, bảng kết quả): `python run_server.py eval/run_all.py` (`--quick` bỏ synth + perturb); xem [../eval/REPRODUCE.md](../eval/REPRODUCE.md).
Build **xoá và dựng lại** `data/runtime/system3.db`. Muốn dựng ra chỗ khác (không đè DB đang dùng): đặt `S3_DATA_DB=<đường dẫn>` cho cả lệnh build, test_data, server và eval.

## 3. Chạy server
```bash
cd <SYSTEM3>
python run_server.py                       # http://127.0.0.1:8300
```
(Chạy trực tiếp `server/main.py` vẫn được khi thư mục tên `system3` và `PYTHONPATH=<cha của system3>`.)
Biến môi trường (xem `server/config.py`):

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `APP_HOST` / `APP_PORT` | 127.0.0.1 / 8300 | địa chỉ server |
| `S3_DATA_DB` | `data/runtime/system3.db` | DB thủ tục (dữ liệu, chỉ đọc khi chạy) |
| `S3_DB_PATH` | `server/runtime/system3.db` | DB hội thoại (tự tạo) |
| `S3_DEV` | 0 | 1 = trả kèm plan/trace; bật `/dev/variants.html`, `/dev/default_variants` và `POST /config`. Mọi thứ hiện giờ là developer mode; tách chế độ người dùng: [FINAL_PRODUCT_CHECKLIST.md](FINAL_PRODUCT_CHECKLIST.md) |
| `S3_USE_LLM` | 1 | 0 = tắt hẳn bước LLM sinh chữ (bật mặc định theo quyết định của nhóm) |
| `ANSWER_LLM_TIMEOUT` | 7.0 | giây chờ LLM của bước sinh chữ; quá hạn thì giữ câu trả lời bằng code (trước Phase 24 là 5 s cứng trong code) |
| `ANSWER_LLM_TURN_BUDGET` | 9.0 | tổng giây LLM tối đa của MỘT lượt (nhiều lần gọi); hết thì dùng bản code ngay (Phase 27) |
| `ANSWER_LLM_NUM_PREDICT` | 200 | giới hạn token sinh của bước sinh chữ (0 = không giới hạn) (Phase 27) |
| `ANSWER_LLM_PASSAGE_CHARS` | 450 | cắt mỗi đoạn dữ liệu đưa cho LLM (Phase 27; trước đó 700) |
| `S3_NO_WARMUP` | (trống) | 1 = không nạp trước model lúc khởi động (dùng cho test) |
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

Endpoint Phase 20: `GET /procedure/{proc_id}/table` (bảng đủ 12 mục + nguồn, nguyên văn dữ liệu, 404 nếu không có thủ tục/cờ tắt). `GET /config` thêm `answer_llm` (= `S3_USE_LLM`), `answer_timeout`, `model_loaded`, `table_button`; `POST /config {answer_llm, mode, confidence, timeout}` đổi trong bộ nhớ (mất khi khởi động lại), chỉ khi `S3_DEV=1` (403 nếu không); `timeout` ở đây là của Planner hybrid, còn timeout bước sinh chữ chỉ đổi bằng `ANSWER_LLM_TIMEOUT`. UI: nút "AI: bật/tắt" ở đầu khung chat mở panel cấu hình; không dev thì panel chỉ xem.

Khi khởi động server tự nạp trước model ở thread nền, không chặn `/health`; chỉ khi có đường LLM nào bật (`S3_USE_LLM=1` hoặc Planner hybrid), và không khi `S3_NO_WARMUP=1`.
Bảng timeout hai bước LLM: [ARCHITECTURE.md](ARCHITECTURE.md#bảng-timeout-hai-bước-llm).

## 4. Chạy test
Đặt `PYTHONIOENCODING=utf-8` (Windows), và để không đụng GPU: `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`.
```bash
cd <SYSTEM3>/server
python tests/memory_test.py      # bộ nhớ, reset, endpoint dev (không gọi LLM)
python tests/context_test.py     # quyết định follow-up
python tests/answer_llm_test.py  # verifier + fallback, dùng LLM giả
python tests/planner_hybrid_test.py  # hợp nhất Planner hybrid, LLM giả (đề xuất sai/ngưỡng thấp/timeout/JSON hỏng giữ luật)
python tests/p20_api_test.py     # bảng full, /config answer_llm, reset chủ đề (TestClient, không LLM)
python tests/p23_input_test.py   # nhãn lượt, chữ dính liền, chữ lạ, câu điều kiện
python tests/p26_memory_test.py  # bộ nhớ người dùng: API /memory*, kiểm giá trị, cô lập client_id, không lưu PII, lọc ứng viên theo đối tượng
python smoke_test.py             # server tạm (DB tạm, cổng 8391, S3_USE_LLM=0): health, trả lời có nguồn, hỏi lại + bấm nút, messages/trace
set S3_USE_LLM=0 && python e2e_test.py   # chạy server tạm 5 lượt hội thoại (cổng 8392)
cd ..
python eval/check_docs.py        # tài liệu khớp số đo thật, lệnh/file nhắc tới tồn tại
```
(Các lệnh `tests/*.py` cần `PYTHONPATH=<cha của system3>` khi thư mục tên `system3`; `smoke_test.py` và `memory_test.py` tự khởi động server qua `run_server.py` nên không cần.)

## Sự cố thường gặp
- `ModuleNotFoundError: system3` → chạy qua `python run_server.py ...` (không cần `PYTHONPATH`), hoặc đặt `PYTHONPATH=<cha của system3>` khi thư mục tên `system3`.
- `no such table`/thiếu DB → chưa chạy bước 2.
- Lượt có LLM khi model nguội (vừa `ollama stop`, hoặc để quá `LLM_KEEP_ALIVE` 30 phút; nạp mất > 14 s trên GTX 1660 Super) → từ Phase 27 trả ngay bản bằng code (không đợi 7 s) và nạp model ở nền cho lượt sau; đợi prewarm hoặc đặt `S3_USE_LLM=0`. Bình thường một lượt có LLM mất ~2–3 s (p95 ~3,5 s); quá 7 s thì lượt đó giữ câu trả lời bằng code.
- `pip install` báo `CERTIFICATE_VERIFY_FAILED` → mạng/proxy chặn chứng chỉ; sửa chứng chỉ hệ thống, đừng tắt kiểm tra SSL.
- Lỗi tiếng Việt khi in ra console Windows → `set PYTHONIOENCODING=utf-8`.

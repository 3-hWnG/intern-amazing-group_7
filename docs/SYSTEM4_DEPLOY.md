# System 3 + 4 — Hướng dẫn deploy (theo sơ đồ "Kiến trúc triển khai")

Trạng thái 2026-10-07 (sau NV1). Theo lựa chọn 7C: **chỉ có tài liệu, chưa có Dockerfile**. Hôm nay web chạy tại máy (`Launch web.bat`). Tài liệu này ghi rõ từng ô trong sơ đồ: đã có gì, thay bằng gì khi lên máy chủ thật.

## 1. Đối chiếu sơ đồ

| Ô trong sơ đồ | Hiện có | Khi deploy |
|---|---|---|
| 1 Người dùng (web/mobile) | Web chạy được trên điện thoại (đã kiểm ở bề ngang 390 px) | — |
| 2 CDN + Frontend | FastAPI tự phục vụ `/static`, `/s4/static`; đổi phiên bản bằng `?v=` | Đặt nginx/CDN phục vụ hai thư mục `web/static`, `system4/web/static` |
| 3 Load Balancer | Không có, 1 tiến trình | Chỉ thêm khi đã làm các mục ở 5 và 7 (dữ liệu chung, hàng đợi chung) |
| 4 API Gateway | Đăng nhập (cookie HttpOnly, SameSite=Lax), phân quyền dev/user, kiểm dữ liệu vào (pydantic) | Thêm **giới hạn tần suất** (rate limit) ở nginx; bật `S4_COOKIE_SECURE=1` khi có HTTPS |
| 5 Backend API | FastAPI + SQLite (`server/runtime/system3.db`, `system4/runtime/system4.db`) | SQLite đủ cho 1 máy. Nhiều máy → PostgreSQL: chỉ sửa `system4/server/db.py` (mọi câu SQL nằm ở đó) |
| 6 Cache (Redis) | Chưa có | Chỗ cắm: đầu `/s4/chat` (routes.py), trước khi gọi model |
| 7 Hàng đợi | Trong bộ nhớ: System 3 `core/queue.py`, System 4 `llm.Turn` (1 lượt/lần, báo vị trí, giới hạn `FRIENDLY_QUEUE_MAX`) | Redis/RQ khi chạy nhiều tiến trình |
| 8 AI Service | Ollama tại máy, `qwen3:4b` | vLLM chỉ chạy trên Linux. Chỉ cần sửa `system4/server/llm.py` (một hàm `stream_chat`) |
| 9 Trả kết quả (streaming) | SSE (`/s4/chat`), có nút Dừng | Nginx: tắt buffer (`proxy_buffering off`); server đã gửi `X-Accel-Buffering: no` |
| Lưu trữ: Vector DB (Qdrant) | Chưa dùng (NV3, chạy local mode) | Qdrant server: đổi đường dẫn thành URL |
| Lưu trữ: Object storage | Chưa có (NV3: thư mục dataset) | MinIO/S3 |
| Ingestion pipeline | Chưa có (NV3) | Worker riêng để nạp dữ liệu không ảnh hưởng người đang hỏi |
| Độ tin cậy | Timeout (`FRIENDLY_TIMEOUT`), giới hạn hàng đợi, `/health` | Model dự phòng, tự khởi động lại (systemd/Docker restart) |
| Giám sát & log | Log của uvicorn ra màn hình | Ghi log ra file, Prometheus/Grafana |
| Bảo mật | Mật khẩu bcrypt; DB chỉ lưu sha256 của cookie; System 3 che CCCD/SĐT ở Strict | HTTPS qua nginx; sao lưu `system4/runtime/` định kỳ |
| DevOps | Chưa có Docker (7C) | Xem mục 3 |

## 2. Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `8300` | Máy chủ thật: `APP_HOST=0.0.0.0` (hoặc để nginx đứng trước) |
| `S4_ENABLED` | `0` trong code, `1` trong `Launch web.bat` | Bật System 4 (đăng nhập + Friendly) |
| `S4_COOKIE_SECURE` | `0` | `1` khi chạy sau HTTPS |
| `S4_RUNTIME_DIR` | `system4/runtime` | Nơi để DB + settings.json của System 4 |
| `S3_DB_PATH` | `server/runtime/system3.db` | DB hội thoại của System 3 |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Địa chỉ Ollama (dùng chung cho cả hai hệ) |
| `S3_USE_LLM`, `S3_DEV`, … | xem `server/config.py` | Cấu hình System 3 (không đổi) |

## 3. Các bước dự kiến khi lên máy chủ Linux (chưa chạy thử)
1. Cài Python 3.12, Ollama, NVIDIA driver; `ollama pull qwen3:4b` và `ollama pull bge-m3`.
2. Lấy code từ nhánh `System_3&4`; tạo venv; `pip install -r requirements.txt`.
3. Tạo liên kết `pyroot/system3 -> <repo>` (như bước 3 của `Set up first time.bat`, trên Linux dùng `ln -s`); `python -m system3.data.build`; `python system4/setup_models.py reranker`.
4. Chạy `S4_ENABLED=1 S4_COOKIE_SECURE=1 PYTHONPATH=<pyroot> python server/main.py` dưới systemd. **Chỉ 1 tiến trình** (không dùng `--workers`).
5. nginx đứng trước: HTTPS, `proxy_buffering off` cho `/s4/chat`, giới hạn tần suất cho `/s4/auth/*`, `/chat`, `/s4/chat`.
6. Mở web, tạo tài khoản dev đầu tiên **ngay** (người đăng ký đầu tiên thành dev); sau đó có thể tắt "Cho phép đăng ký" trong ⚙ Cài đặt.

## 4. Giới hạn đã biết khi deploy
- Một tiến trình duy nhất: hàng đợi, công tắc AI của System 3 và bộ nhớ đệm cài đặt nằm trong bộ nhớ của tiến trình.
- Người đăng ký đầu tiên thành dev: trên máy chủ công khai phải tạo tài khoản dev trước khi mở cho người khác.
- Chưa có giới hạn số lần đăng nhập sai (nên đặt ở nginx).

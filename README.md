# Trợ lý Thủ tục hành chính — V10.3

Trợ lý ảo trả lời câu hỏi về **thủ tục hành chính Việt Nam**. Mô hình ngôn ngữ
3–4B chạy **cục bộ** (local) lo phần *hiểu và diễn đạt*; phần *thông tin thủ tục
hiện hành* lấy từ web qua **MCP search**, ưu tiên nguồn `.gov.vn`; mỗi câu trả
lời đi qua một lượt **kiểm chứng** (verify) trước khi hiển thị.

> *A Vietnamese public-administration assistant. A local 3–4B LLM handles
> language; live procedure facts come from web search over an MCP server;
> every answer is verified against its evidence before being shown.*

---

## Bắt đầu / Getting started

| Bạn muốn gì | Làm gì |
|---|---|
| Chạy lần đầu trên máy mới | Bấm đôi **`Setup First Time.bat`** (một lần duy nhất) |
| Chạy ứng dụng hằng ngày | Bấm đôi **`Launch Web.bat`** → http://127.0.0.1:8000 |
| Đổi cấu hình (mô hình, cổng, tìm kiếm…) | Sửa **`.env`** ở thư mục gốc — xem `.env.example` |
| Hiểu thư mục nào chứa gì | [`Documentation/STRUCTURE.md`](Documentation/STRUCTURE.md) |
| Tìm nhanh một hàm / một file | [`Documentation/CODEBASE_INDEX.md`](Documentation/CODEBASE_INDEX.md) |
| Hiểu hệ thống chạy thế nào | [`Documentation/ARCHITECTURE.md`](Documentation/ARCHITECTURE.md) |
| Gặp lỗi | [`Documentation/FAILURE_HANDLING.md`](Documentation/FAILURE_HANDLING.md) |

`Setup First Time.bat` **không tải lại thứ đã có**: Python, `.venv`, thư viện,
Ollama, mô hình — cái nào máy đã có thì bỏ qua. Chạy lại nhiều lần vẫn an toàn.

---

## Cấu trúc thư mục / Folder layout

```
LLM for Procedures V10.3/
├─ Launch Web.bat          ← bấm đôi để chạy
├─ Setup First Time.bat    ← bấm đôi để cài, chỉ lần đầu
├─ config.py               ← TOÀN BỘ cấu hình, để ở gốc cho dễ tìm
├─ .env / .env.example     ← ghi đè cấu hình, không commit .env
├─ requirements.txt
│
├─ Backend/                mã nguồn máy chủ (FastAPI · pipeline · MCP · CSDL)
├─ Frontend/               giao diện: static/ (css, js) + templates/ (html)
├─ Database/               schema.sql · corpus/ (dữ liệu nguồn) · runtime/ (app.db)
├─ Evaluation/             kịch bản chấm điểm pipeline
├─ Utility/                finetune/ · scripts/ (run.ps1, setup.ps1, make_index.py)
├─ Documentation/          tài liệu (bản cũ nằm trong legacy/)
├─ Extra/                  Docker, cấu hình VS Code, tệp rời không thuộc nhóm nào
└─ .venv/                  môi trường Python (không commit)
```

Chi tiết từng thư mục + bảng đối chiếu với V10.2: [`Documentation/STRUCTURE.md`](Documentation/STRUCTURE.md).

---

## Yêu cầu / Requirements

- **Windows 10/11** (các script là `.bat` + PowerShell)
- **Python 3.12** — `Setup First Time.bat` tự cài qua `winget` nếu thiếu
- **[Ollama](https://ollama.com/download)** — tự cài qua `winget` nếu thiếu
- Mô hình mặc định `qwen2.5:1.5b` (đổi bằng `LLM_MODEL` trong `.env`)
- Kết nối Internet — hệ thống **tra web** cho mọi câu trả lời

---

## Câu lệnh hay dùng / Common commands

Chạy từ thư mục gốc. Luôn gọi Python qua `.venv\Scripts\python.exe`
(xem [FAILURE_HANDLING.md](Documentation/FAILURE_HANDLING.md) để biết vì sao).

```powershell
# Chạy ứng dụng (tương đương Launch Web.bat)
.venv\Scripts\python.exe Backend\main.py

# Chấm điểm pipeline
.\Utility\scripts\run.ps1 -Eval -Limit 20

# Chạy riêng MCP search server (cổng 8765)
.\Utility\scripts\run.ps1 -Mcp

# Cập nhật bản đồ mã nguồn sau khi thêm/xoá file
.venv\Scripts\python.exe Utility\scripts\make_index.py

# Sửa .venv sau khi di chuyển thư mục dự án
.venv\Scripts\python.exe Utility\scripts\fix_venv.py
```

---

## Lưu ý an toàn dữ liệu / Data safety

`Database/runtime/app.db` chứa **tài khoản thật, mật khẩu đã băm bcrypt, và
lịch sử trò chuyện**. Thư mục `Database/runtime/` đã nằm trong `.gitignore` —
đừng bỏ ra khỏi đó.

Trước khi bàn giao: đặt `DEV_TOOLS_ENABLED=0` trong `.env` (các endpoint phát
triển có khả năng xoá dữ liệu).

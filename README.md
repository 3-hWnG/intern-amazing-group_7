# Trợ lý Thủ tục hành chính — V10.5

Trợ lý ảo trả lời câu hỏi về **thủ tục hành chính cấp Xã/Phường**. Mô hình ngôn
ngữ nhỏ (mặc định `qwen2.5:1.5b`) chạy **cục bộ** (local). Thông tin thủ tục
trong bảng thì KHÔNG do mô hình sinh ra. Có **hai hệ thống trả lời**, đổi bằng
nút trên giao diện:

| | Hệ thống 2 — **CSDL thủ tục** (mặc định) | Hệ thống 1 — **Web search** |
|---|---|---|
| Nguồn | **1.350 thủ tục cấp Xã/Phường** cào sẵn từ dichvucong.gov.vn (SQLite + FTS5) | tra `.gov.vn` trực tiếp qua MCP |
| Câu trả lời | **bảng do code dựng** — không qua mô hình | mô hình soạn, rồi **kiểm chứng** với nguồn |
| Mạnh ở | đúng nguyên văn cổng, có checklist + biểu mẫu tải về | thủ tục mới, thứ chưa có trong kho |
| Tài liệu | [`PLAN_SYSTEM2_REBUILD.md`](Documentation/PLAN_SYSTEM2_REBUILD.md) | [`ARCHITECTURE.md`](Documentation/ARCHITECTURE.md) |

Đổi hệ thống sẽ **mở ô chat mới** để mô hình không trộn thông tin hai nguồn.

> *A Vietnamese public-administration assistant for ward-level (Xã/Phường)
> procedures. The default path chats with a local LLM and, on the 🎯 button,
> looks the procedure up in a database of 1,350 procedures scraped from
> dichvucong.gov.vn, rendering the answer table in code — the LLM never writes
> the facts. The other path searches .gov.vn live over MCP and verifies every
> answer against its evidence.*

## Dùng Hệ thống 2 thế nào / How System 2 works

1. **Hỏi bình thường** → trợ lý trò chuyện, nhãn **AI tự trả lời, chưa qua
   CSDL**. Hỏi trúng một thủ tục thì bên dưới hiện gợi ý **🎯 Tìm chính xác**.
2. **Bấm 🎯 Tìm chính xác, gõ tên thủ tục, bấm Gửi** → tra CSDL bằng từ khoá
   (mô hình chỉ vào cuộc khi từ khoá không khớp) → chọn **thủ tục chính** → chọn
   **dạng cụ thể** → nhận **bảng thủ tục** (nhãn **Từ database**).
3. **Hỏi tiếp về bảng**:
   - câu hỏi về một ô (lệ phí, thời gian, giấy tờ, nơi nộp…) → trích nguyên văn
     ô đó (📚);
   - xin tóm tắt/giải thích → mô hình trả lời chỉ trên bảng (nhãn **🤖 Trả lời
     dựa trên database, có thể không đúng**).
4. **Mỗi ô chat tra một thủ tục.** Bấm 🎯 lần hai sẽ được mời mở ô chat mới. Hỏi
   sang thủ tục khác thì vẫn được trả lời, kèm cảnh báo.

Ô nào cổng không công bố thì bảng ghi **"Chưa có thông tin…"**, không bao giờ
để trống hay tự suy ra "miễn phí".

---

## Bắt đầu / Getting started

| Bạn muốn gì | Làm gì |
|---|---|
| Lấy mã nguồn | `git clone -b V10.5 https://github.com/3-hWnG/intern-amazing-group_7.git` |
| Chạy lần đầu trên máy mới | Bấm đôi **`Setup First Time.bat`** (một lần duy nhất, 30–60 phút) |
| Chạy ứng dụng hằng ngày | Bấm đôi **`Launch Web.bat`** → http://127.0.0.1:8000 |
| Đổi cấu hình (mô hình, cổng, tìm kiếm…) | Sửa **`.env`** ở thư mục gốc — xem `.env.example` |
| Hiểu thư mục nào chứa gì | [`Documentation/STRUCTURE.md`](Documentation/STRUCTURE.md) |
| Tìm nhanh một hàm / một file | [`Documentation/CODEBASE_INDEX.md`](Documentation/CODEBASE_INDEX.md) |
| Hiểu hệ thống chạy thế nào | [`Documentation/ARCHITECTURE.md`](Documentation/ARCHITECTURE.md) |
| Gặp lỗi | [`Documentation/FAILURE_HANDLING.md`](Documentation/FAILURE_HANDLING.md) |

`Setup First Time.bat` **không tải lại thứ đã có**: Python, `.venv`, thư viện,
Ollama, mô hình — cái nào máy đã có thì bỏ qua. Chạy lại nhiều lần vẫn an toàn.

⚠️ **Lần đầu nó phải cào ~1.350 thủ tục cấp Xã/Phường về máy (15–25 phút).** Dữ liệu thủ tục và
biểu mẫu `.docx` **không nằm trong git** (kho sẽ nặng và không diff được), nên máy
nào cũng phải cào một lần. Bỏ qua bằng `-SkipScrape` — lúc đó Hệ thống 2 sẽ báo
chưa có CSDL và mời bạn dùng Web search. Cào lại/cập nhật bất cứ lúc nào:

```bash
python -m Database.pipeline.run_pipeline --all
```

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
├─ Database/               pipeline/ (cào + nạp CSDL thủ tục) · staging/ · schema.sql
│                          runtime/ (app.db, procedures.db — không commit)
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
- Kết nối Internet — để cài đặt, cào CSDL thủ tục lần đầu, và cho Hệ thống 1
  (Web search). Đã cào xong thì **Hệ thống 2 chạy được không cần mạng**.

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

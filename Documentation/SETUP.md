# Cài đặt trên máy mới / Setup on a new machine

Mục tiêu: chép cả thư mục dự án sang một máy Windows chưa có gì, **chạy một
lần**, rồi dùng được.

---

## Cách nhanh / Quick path

1. Chép cả thư mục dự án sang máy mới, **hoặc** lấy từ GitHub:
   `git clone -b V10.5 https://github.com/3-hWnG/intern-amazing-group_7.git`
2. Bấm đôi **`Setup First Time.bat`**.
3. Bấm đôi **`Launch Web.bat`**.

Xong. Lần đầu có thể mất 30–60 phút, tuỳ mạng: tải thư viện + mô hình, rồi
**cào ~1.350 thủ tục cấp Xã/Phường** cho Hệ thống 2 (15–25 phút, bước 7).

> Chạy lại `Setup First Time.bat` lúc nào cũng an toàn: **cái gì máy đã có thì
> bỏ qua**, không tải lại. / Re-running the setup is always safe — it skips
> everything already present.

---

## `Setup First Time.bat` làm gì / What setup does

| Bước | Việc | Bỏ qua khi |
|---|---|---|
| 1 | Tìm Python ≥ 3.10; thiếu thì cài `Python.Python.3.12` qua `winget` | đã có `.venv` hoặc đã có Python |
| 1b | Tạo `.venv` | `.venv` đã có |
| 2 | Chạy `fix_venv.py` — sửa đường dẫn tuyệt đối bên trong `.venv` | `.venv` đã trỏ đúng chỗ |
| 3 | Thử `import` toàn bộ thư viện; thiếu mới `pip install -r requirements.txt` | import được hết |
| 3b | Thư viện huấn luyện (`torch`…) — **chỉ khi** thêm `-IncludeFinetune` | không truyền tham số, hoặc đã có |
| 4 | Tạo `.env` từ `.env.example` | `.env` đã có (**không ghi đè** cấu hình của bạn) |
| 5 | Cài Ollama qua `winget` nếu thiếu | `ollama` đã có |
| 5b | Bật dịch vụ `ollama serve` nếu chưa chạy | đang chạy |
| 5c | `ollama pull` mô hình trong `LLM_MODEL` / `VERIFIER_MODEL` | mô hình đã tải |
| 6 | Tạo `Database/runtime/app.db` từ `Database/schema.sql` | bảng đã tồn tại |
| 7 | Cào CSDL thủ tục: `python -m Database.pipeline.run_pipeline --all`. Phạm vi mặc định: cấp Xã/Phường + thủ tục riêng TP.HCM (~1.350 thủ tục, 2 req/s, 15–25 phút) → `Database/runtime/procedures.db` | đã có thủ tục trong `procedures.db`, hoặc truyền `-SkipScrape` |

### Tham số / Flags

```powershell
# Cài thêm thư viện huấn luyện (torch ~3GB) — chỉ cần nếu bạn định fine-tune
powershell -NoProfile -ExecutionPolicy Bypass -File .\Utility\scripts\setup.ps1 -IncludeFinetune

# Bỏ qua phần Ollama (máy đã có sẵn, hoặc dùng Ollama trên máy khác)
powershell -NoProfile -ExecutionPolicy Bypass -File .\Utility\scripts\setup.ps1 -SkipOllama

# Bỏ qua bước cào CSDL thủ tục (Hệ thống 2 báo chưa có CSDL; Web search vẫn chạy)
powershell -NoProfile -ExecutionPolicy Bypass -File .\Utility\scripts\setup.ps1 -SkipScrape
```

---

## Khi không cài tự động được / When auto-install fails

Setup **không làm hỏng gì** nếu `winget` không có hoặc bị chặn — nó báo rõ rồi
đi tiếp. Cài tay hai thứ sau rồi chạy lại `Setup First Time.bat`:

- **Python 3.12** — https://www.python.org/downloads/
  ⚠️ nhớ tick **"Add python.exe to PATH"** lúc cài.
- **Ollama** — https://ollama.com/download

---

## Chép kèm `.venv` hay để máy mới tự tải? / Copy the venv or rebuild it?

Cả hai đều được:

- **Chép kèm `.venv`** (3,65 GB) — không cần mạng để cài thư viện. Bước 2 của
  setup tự sửa các đường dẫn tuyệt đối nhúng bên trong. Vẫn cần mạng để tải mô
  hình Ollama.
- **Không chép `.venv`** (nhẹ hơn nhiều) — setup tự tạo mới rồi `pip install`.
  Cần mạng.

---

## Cấu hình sau khi cài / Configuration

Sửa **`.env`** ở thư mục gốc; xem `.env.example` để biết đủ các biến.
Hay dùng nhất:

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `LLM_MODEL` | `qwen2.5:1.5b` | Mô hình trả lời. Máy khoẻ thì đổi `qwen2.5:3b` |
| `VERIFIER_MODEL` | *(giống `LLM_MODEL`)* | Mô hình kiểm chứng |
| `APP_PORT` | `8000` | Cổng web |
| `SEARCH_PROVIDER` | `ddgs` | `ddgs` · `searxng` · `brave` · `tavily` |
| `DEV_TOOLS_ENABLED` | `1` | **Đặt `0` khi bàn giao** — có endpoint xoá dữ liệu |
| `DB_BACKEND` | `sqlite` | Chỗ đổi sang CSDL khác về sau |

Gặp lỗi: xem [`FAILURE_HANDLING.md`](FAILURE_HANDLING.md).

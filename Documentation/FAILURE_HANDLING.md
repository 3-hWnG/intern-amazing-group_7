# Hỏng thì làm gì / Failure handling

Hai phần:
**Phần A** — các tình huống đã *lường trước* khi tái cấu trúc V10.2 → V10.3 và
cách đã quyết định xử lý (ghi lại để không phải đoán lại về sau).
**Phần B** — sổ tay xử lý lỗi khi chạy.

---

## Phần A — Quyết định đã lường trước khi tái cấu trúc

*Pre-declared handling for the V10.2 → V10.3 restructure. Ghi theo dạng
"nếu X thì làm Y" như đã thống nhất trước khi thực hiện.*

| # | Tình huống lường trước | Quyết định | Thực tế đã xảy ra |
|---|---|---|---|
| A1 | Copy `.venv` thất bại hoặc thiếu file | Dùng `robocopy /E /MT:16`, sau đó **đếm số file hai bên**; lệch thì chép lại, không đi tiếp | Copy đủ **46.533 file / 3,65 GB**, khớp chính xác |
| A2 | `.venv` copy xong nhưng trỏ sai chỗ | Viết `Utility/scripts/fix_venv.py`: sửa `pyvenv.cfg` + script `activate` + shebang trong `Scripts/*.exe`, rồi **tự kiểm tra bằng `pip.exe --version`**; sai thì hoàn nguyên file `.exe` | Sửa **42 shim**, `pip.exe` báo đúng đường dẫn mới |
| A3 | Sửa shim `.exe` làm hỏng file | Giữ bản gốc trong bộ nhớ, kiểm tra xong mới coi là thành công; thất bại thì ghi lại bản cũ và chuyển sang dùng `python.exe -m <tool>` | Không xảy ra |
| A4 | Thay chuỗi trong mã nguồn không khớp (sửa nhầm / sửa hụt) | Mọi thay thế đều `assert` đúng **1** lần khớp; lệch là dừng ngay, không ghi file | 21/21 thay thế khớp |
| A5 | Xoá `import` mà chỗ khác còn dùng | Sau khi bỏ `from pathlib import Path` ở `connection.py`, grep lại `Path` trong file | Không còn chỗ dùng — an toàn |
| A6 | Mất dữ liệu người dùng (`app.db`) | **Chép**, không cắt dán; bản V10.2 vẫn còn nguyên | `Database/runtime/app.db` đã có, bản cũ còn nguyên |
| A7 | Docker không khớp cấu trúc mới | Cập nhật `Dockerfile` + `docker-compose.yml` cho đúng, nhưng **ghi rõ là chưa chạy thử**, vì đường chính thức trên Windows là `Launch Web.bat` | Đã cập nhật, đã ghi chú, chưa chạy thử |
| A8 | Thư mục dự án bị đổi tên / di chuyển về sau | `fix_venv.py` viết theo kiểu chạy lại lúc nào cũng được; `setup.ps1` gọi nó ở bước 2 | Đã có sẵn |
| A9 | Tiếng Việt có dấu vỡ trên console Windows | Tài liệu `.md` dùng tiếng Việt đầy đủ dấu; **script `.ps1`/`.bat` in ra không dấu** (giữ đúng quy ước sẵn có của `run.ps1` V10.2) | Đã áp dụng |
| A10 | Mã nguồn cũ bị hỏng khi thử nghiệm | **Không đụng vào** `intern-amazing-group_7-Re-imagine-V10.2/`. Toàn bộ V10.3 là bản sao | Thư mục cũ còn nguyên vẹn |

**Việc cố ý chưa làm / deliberately not done:** chưa `git commit`. Kho Git đã
`init` và đã `add`, chờ bạn kiểm tra rồi mới commit — đúng yêu cầu ban đầu
("Wait for me to check then commit it to Git").

---

## Phần B — Sổ tay xử lý lỗi khi chạy

### B1. `Launch Web.bat` báo "Chua cai dat xong"
Chưa có `.venv\Scripts\python.exe`. → Bấm đôi **`Setup First Time.bat`**.

### B2. `ModuleNotFoundError: No module named 'config'`
Đang chạy Python từ sai chỗ. `config.py` ở **thư mục gốc** và được tìm thấy nhờ
`sys.path` do `Backend/main.py` tự đặt. → Chạy đúng lệnh:
```powershell
.venv\Scripts\python.exe Backend\main.py      # từ thư mục gốc
```

### B3. `ModuleNotFoundError: No module named 'fastapi'` (hoặc thư viện khác)
Đang dùng nhầm Python. → Luôn gọi **`.venv\Scripts\python.exe`**, đừng gọi
`python` trống. Nếu vẫn thiếu:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### B4. Chạy `pip` / `uvicorn` nhưng nó tác động vào `.venv` KHÁC
`.venv` được **copy** từ V10.2, các file `.exe` trong `Scripts\` có nhúng đường
dẫn tuyệt đối. `fix_venv.py` đã sửa 42 file này, nhưng nếu bạn lại di chuyển
thư mục dự án thì phải chạy lại:
```powershell
.venv\Scripts\python.exe Utility\scripts\fix_venv.py
```
**Cách an toàn tuyệt đối:** luôn gọi qua `-m`, ví dụ
`.venv\Scripts\python.exe -m pip …` thay vì `pip …`.

### B5. "Ollama không phản hồi" trong khung chat
Máy chủ **vẫn chạy** (cố ý thiết kế vậy: Ollama hỏng thì người dùng thấy lỗi rõ
ràng, không phải server sập). → Mở ứng dụng Ollama, hoặc:
```powershell
ollama serve
ollama pull qwen2.5:1.5b
```

### B6. "Chưa có mô hình: …"
```powershell
ollama pull <tên mô hình trong thông báo>
```
Đổi mô hình mặc định: sửa `LLM_MODEL` trong `.env`.

### B7. MCP chưa kết nối / không tra được web
Cũng **không làm sập server**. Thử theo thứ tự:
1. Kiểm tra mạng (hệ thống bắt buộc tra web để có Evidence Pack);
2. Chạy riêng MCP server xem lỗi gì: `.\Utility\scripts\run.ps1 -Mcp`;
3. Tạm bỏ qua MCP để khoanh vùng: đặt `MCP_TRANSPORT=direct` trong `.env`.

### B8. Cổng 8000 đã bị chiếm
Đổi `APP_PORT` trong `.env`, hoặc tìm tiến trình đang giữ cổng:
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
```

### B9. `.ps1` không chạy được ("running scripts is disabled")
Hai file `.bat` đã gọi kèm `-ExecutionPolicy Bypass` nên bấm đôi luôn chạy
được. Nếu gọi `.ps1` tay thì thêm:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Utility\scripts\run.ps1
```

### B10. Sửa CSS/JS mà trình duyệt không cập nhật
Tăng `STATIC_VERSION` trong `config.py` (trình duyệt đang dùng bản cache cũ).

### B11. CSDL lỗi / muốn làm lại từ đầu
⚠️ Mất hết tài khoản và lịch sử trò chuyện. Sao lưu trước:
```powershell
Copy-Item Database\runtime\app.db Database\runtime\app.db.bak
Remove-Item Database\runtime\app.db
.venv\Scripts\python.exe Backend\main.py     # tự tạo lại từ Database\schema.sql
```

### B12. `NotImplementedError: DB_BACKEND=... chưa được cài đặt`
Bạn đặt `DB_BACKEND` khác `sqlite` nhưng chưa viết phần cài đặt. → Trả về
`DB_BACKEND=sqlite`, hoặc hiện thực hoá trong `Backend/db/connection.py` +
`repositories.py` (xem `Documentation/STRUCTURE.md`, mục `Database/`).

### B13. Thêm/xoá/đổi tên file xong, bản đồ mã nguồn lỗi thời
```powershell
.venv\Scripts\python.exe Utility\scripts\make_index.py
```

### B14. Cần quay lại bản V10.2
Nguyên vẹn tại `..\intern-amazing-group_7-Re-imagine-V10.2\` — kho Git riêng,
`.venv` riêng, chạy `.\run.ps1` như cũ. V10.3 không sửa gì trong đó.

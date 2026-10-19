# Lĩnh vực FLM — khung chương trình & đề cương ĐH FPT (flm.fpt.edu.vn)

Lĩnh vực **cứng** `FLM – Đề cương FPTU` (engine `flm`, tạo tự động lúc khởi động, tìm theo engine, không cố định id).
Trả lời bằng pipeline Friendly trên **bảng FLM + đường nhanh** (leader chọn 19/10/2026), không có router viết tay như ABI.

## Lấy dữ liệu
- FLM **không có API công khai**; trang khách (`/gui/role/guest/...`) đòi **reCAPTCHA**. Leader: chế độ khách, KHÔNG dùng tài khoản đăng nhập.
- Bấm **Quản lý lĩnh vực → FLM → Dữ liệu FLM → Đồng bộ FLM**: server mở một **cửa sổ Chrome riêng** (hồ sơ `system4/runtime/flm/chrome_profile`,
  không đụng Chrome của người dùng) ở trang FLM. Nếu hiện captcha: tích "I'm not a robot" → Continue trong cửa sổ đó. Phiên khách còn hạn thì đi thẳng.
- Mọi request chạy bằng `fetch()` **bên trong trang Chrome đó** (CDP, `system4/flm/browser.py`, chỉ thư viện chuẩn) — cookie không ra khỏi trình duyệt.
- ⚙ `FLM_PROGRAMS` (mặc định `BIT_SE, BIT_AI`): mỗi tiền tố lấy khung chương trình **mới nhất** (curid lớn nhất, bỏ bản `_FNO`) + đề cương
  đang dùng của từng môn. 1 request/giây; 2 ngành ≈ 127 request, ≈ 3 phút (đo 19/10: 167 s gồm cả nạp).
- Khách **không** xem được tài liệu (`gvMaterial`) và lịch buổi học (`gvSchedule`). Môn mới của khung 2026 (MAC103, PPJ101, SWE204…, 23/73 môn
  lúc 19/10) **chưa có đề cương công khai**: vẫn có tên / tín chỉ / kỳ / tiên quyết từ khung, cột "Đề cương trên FLM" ghi rõ.
- **Không có lịch tự đồng bộ** (captcha cần người bấm).

## Dữ liệu (tệp Excel, `system4/flm/build.py`)
| Sheet | Một dòng là | Cột tiêu đề (để đường nhanh tìm thực thể) |
|---|---|---|
| Chương trình | khung chương trình | `Chuyên ngành Kỹ thuật phần mềm (BIT_SE-2026_K22D_23A)` |
| PLO | chuẩn đầu ra chương trình (bảng con qua Mã chương trình) | `PLO1 · Kỹ thuật phần mềm` |
| Khung chương trình | môn × chương trình: kỳ, tín chỉ | `MAC103 · Kỹ thuật phần mềm` |
| Môn học | môn (đề cương đang dùng) | `MAC103 · Calculus – Giải tích` (có mã: hỏi theo mã khớp được) |
| CLO | chuẩn đầu ra môn (bảng con qua Mã môn) | `CSD203 · CLO1` |
| Đánh giá | đầu điểm: trọng số, thời lượng, CLO… | `PRF192 · Practical Exam (phần 1)` |

## Phiên bản
Giống ABI: dữ liệu **đổi** (băm) → phiên bản mới; không đổi → chỉ ghi "kiểm lúc". Giữ **2** bản mới nhất (`system4/runtime/flm/versions.json`),
đúng một bản đang dùng; bản mới tự thành đang dùng nếu đang theo bản mới nhất. Bộ dữ liệu của phiên bản bật / tắt / xoá **qua phiên bản**, không bằng tay.
Dev / cán bộ **tải thêm** tệp vào lĩnh vực FLM được (thẻ "Dữ liệu tải thêm"): tìm chung, chuyển phiên bản không tắt chúng.

## Kiểm
- `python run_server.py system4/tests/test_flm.py` — trình duyệt giả trả trang THẬT đã lưu, cắt gọn (`system4/tests/fixtures/flm/`), không gọi mạng.
- Đường nhanh trên dữ liệu thật (19/10, model giả): 7/8 câu tra cứu trả lời đúng < 1 ms ("MAC103 có bao nhiêu tín chỉ?", "Môn tiên quyết của AIL304m?",
  "Tổng số tín chỉ của ngành Kỹ thuật phần mềm?", "Công cụ dùng trong môn CSD203?"…); câu thứ 8 hỏi lại đúng (AIL303m / AIL304m trùng tên "Machine Learning").
  Đây là số trên câu tôi tự đặt khi đang làm, KHÔNG phải bộ mù.

## Máy mới / đồng đội cập nhật code
- `Set up first time.bat` (chạy lại được sau `git pull`) kiểm có bản chụp `system4/flm/snapshot/flm_2026-10-19.json` (BIT_SE-2026_K22D_23A, BIT_AI_K22C, 73 môn).
- Bật web, có tài khoản dev là server tự nạp bản chụp làm **phiên bản 1** (`server/bootstrap.py`, một lần, ghi ở `runtime/bootstrap.json`): hỏi được ngay, không cần captcha.
- Đồng bộ lại: nút **Đồng bộ FLM**; hoặc khi đã TẮT web:
  trong thư mục `server\` của repo: `set PYTHONPATH=..\..\pyroot_merge` (thư mục `pyroot_merge` nằm cạnh repo, setup tạo) rồi `..\.venv\Scripts\python.exe -m system3.system4.flm.sync` (thêm `--snapshot` = chỉ nạp bản chụp nếu chưa có phiên bản nào).

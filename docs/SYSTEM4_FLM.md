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

## Đồng bộ đầy đủ (đăng nhập) — leader 19/10/2026 chiều
- Nút **Đồng bộ đầy đủ (đăng nhập)** (hoặc `-m system3.system4.flm.sync --full` khi web tắt): server mở **Chrome riêng ở trang đăng nhập FLM**
  (hồ sơ `runtime/flm/login_profile`, cổng 9334, khác Chrome khách). Người dùng **tự đăng nhập trong cửa sổ đó** (Google @fpt.edu.vn hoặc Sign In):
  mật khẩu chỉ đi tới FLM / Google; hệ thống không có ô nhập mật khẩu, không thấy, không lưu.
- Phiên (cookie) **giữ tới khi tắt server** (đồng bộ lại trong lúc server còn chạy không phải đăng nhập lại); tắt server -> đóng Chrome đăng nhập
  và xoá hồ sơ; server tắt đột ngột thì lần bật sau xoá.
- Lấy **mọi ngành**: `/gui/role/student/ListCurriculum?keyword=_` (510 khung lúc 19/10) -> nhóm theo mã ngành (`scrape.program_key`, 66 ngành)
  -> khung mới nhất mỗi ngành (bỏ `_FNO`) + môn trong combo / tự chọn (`/Compo`, `/Elective`) -> chỉ mục đề cương A–Z
  (`SyllabusManagement?keyword=<chữ>`) -> đề cương đầy đủ của mọi môn: thêm **tài liệu** (gvMaterial), **lịch từng buổi** (gvSchedule),
  **câu hỏi thảo luận** (gvCQ). Tệp đính kèm (slide .zip…) **chỉ lấy link**, không tải.
- Ước tính ~1 + 66×(3 + combo / tự chọn mới) + 26 + ~1.200 request ≈ 30–40 phút ở 1 request/giây. Đề cương đã đọc giữ 7 ngày ở
  `runtime/flm/cache/full/`: bị ngắt (phiên hết hạn, mất mạng) thì lần sau đi tiếp nhanh.
- Một phiên bản đầy đủ = **2 bộ dữ liệu**: tệp Excel (CLO và tài liệu là cột của "Môn học" để bớt dòng; không có sheet CLO) + tệp
  `flm_vN_lich_hoc.md` (mỗi môn một mục: lịch các buổi, câu hỏi). Dùng chung cho mọi tài khoản (leader chọn).
- Test: `test_flm.py` phần "chế độ ĐĂNG NHẬP", fixture `fixtures/flm/full_*.html` lấy từ FLM thật khi đăng nhập, đã xoá tên / email.
- **Chạy thật 19/10/2026** (tài khoản sinh viên): 65 ngành (khung LLB_LA_K22A, curid 2915, bị bỏ qua: mở trang đó làm FLM **đăng xuất** tài khoản —
  `scrape.collect_full` ghi trang làm mất phiên vào `cache/full/bad_pages.json`, lần sau tự bỏ qua), 4.628 dòng khung, 1.305 môn, 671 PLO,
  2.686 đầu điểm, 569 môn có lịch từng buổi + câu hỏi. 2 bộ dữ liệu: 9.355 bản ghi (bảng) + 19.242 đoạn (lịch học, tệp 13 MB).
  Lần chạy trọn: 642 request + 401 trang từ bộ đệm, 22 phút, rồi ~15 phút nạp (bge-m3). Hai lần trước dừng ở trang 2915 -> sinh ra cơ chế trên.
- Thử nhanh trên dữ liệu thật (không phải bộ mù): "PRF192 có bao nhiêu tín chỉ?" -> 3 (đường nhanh); "Mã chương trình ngành Quản trị khách sạn?" ->
  BBA_HM_K22C; "Buổi 5 của môn PRF192 học gì?" / "Câu hỏi thảo luận buổi 1 môn PRF192" -> tìm đúng đoạn lịch / câu hỏi. Chưa tốt: "buổi cuối"
  (tìm kiếm không hiểu "cuối"); "Tài liệu của môn X" ra cả thẻ môn thay vì riêng trường tài liệu.
- Dữ liệu sau đăng nhập KHÔNG đưa vào git (chỉ bản chụp chế độ khách ở `system4/flm/snapshot/`).

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

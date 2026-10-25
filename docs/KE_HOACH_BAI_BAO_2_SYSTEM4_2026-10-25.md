# Kế hoạch thực thi: Bằng chứng cho Bài báo 2 (System 4)

*Lập ngày 25/10/2026, dựa trên `JD_BAI_BAO_2_SYSTEM4_2026-10-25.docx` (Trịnh Hoàng Nhân giao) và hiện trạng repo `D:\phase 3\v3` nhánh `merge_sys_3_4`.*

## 0. Hiện trạng repo (đã kiểm tra trước khi lập plan này)

- `system4/eval/real_v1/` đã có: bộ 177 câu (`cases_real_v1_s4.json`), 2 bộ gán nhãn độc lập (`real_v1_s4_labels_A.json`, `_B.json`), bản thống nhất (`_final.json`), script đo đồng thuận `run_real_v1_s4.py`. → Đây là tiền lệ để làm lại quy trình "2 người gán độc lập" cho phần B của `real_v4_s4`, không cần dựng từ đầu cách làm.
- `system4/eval/real_v3/` đã **khoá** (`LOCK.md`): 52 câu sinh từ khuôn, 4 bảng Wikipedia (tỉnh thành, sân bay, vườn quốc gia, thủy điện). Có `build_v3.py`, `make_cases_v3.py`, `report_v3.py`, kết quả 6 lần chạy đã lưu trong `results/`. Bộ này **chỉ còn dùng làm dev** theo JD mục 2 — không dùng để báo số nữa.
- `system4/server/fastpath/` có `compile.py`, `sqlroute.py`, `engine.py`, `selftest.py` — đây là 4 file sẽ phải sửa ở J2 (S4-1..S4-4).
- Chưa có `CLAUDE.md` ở gốc repo. → Việc đầu tiên, làm ngay, không phụ thuộc gì khác.
- `docs/` đã có `BAO_CAO_CAU_KHO_2026-10-25.md` (khuôn báo cáo mẫu cho J4) và `SYSTEM4_DUONG_NHANH.md` (thiết kế đường nhanh, đọc trước J2).
- Chưa thấy `real_v4_s4` hay `SOURCES.md` cho bộ mới — đúng như JD, J1 là việc đầu tiên thật sự.

## 1. Việc làm ngay (trước khi vào J1)

1. Tạo `CLAUDE.md` ở gốc repo, chép nguyên mục 4 ("Quy tắc bắt buộc") của JD vào đó, để Claude (và bất kỳ ai) luôn đọc được các giới hạn: không gọi API abi.com.vn, khoá bộ mù trước sửa code, đóng băng code trước đo, mỗi cấu hình một lần, không tải model/dataset lớn chưa hỏi, máy ≤ 70°C, không push khi chưa đồng ý, TMP/TEMP trỏ ổ còn chỗ (mỗi test ~45MB).
2. Tạo khung thư mục `system4/eval/real_v4_s4/` (song song `real_v3/`), có sẵn `LOCK.md` (rỗng, điền sau khi khoá), `SOURCES.md`, `data/`.

## 2. J1 — Thiết kế và khoá bộ mù mới `real_v4_s4` (tuần 27/10–2/11)

**Nguyên tắc cứng:** khoá xong (commit + sha256) rồi mới được sửa bất kỳ dòng code nào ở J2. Người sửa engine (bạn) không được đọc câu hỏi phần B trước khi khoá.

### 2.1 Chọn dữ liệu (checklist)
- [ ] ≥ 8 bảng thật, engine chưa từng thấy; ≥ 6 lĩnh vực khác với 4 lĩnh vực của real_v3 (tỉnh thành/sân bay/vườn quốc gia/thủy điện).
- [ ] ≥ 2 tệp nhiều sheet về cùng một đối tượng (để test lỗi S4-1 — bài học từ real_v3: bộ sân bay rớt từ 92% xuống 62% vì SQL chỉ chạy trên 1 sheet).
- [ ] Có cột bẩn chủ động cấy vào: ô gộp, năm dạng "tháng/năm", ô ghi "?", số kèm đơn vị trong cùng ô.
- [ ] Có ít nhất một cặp tên gần trùng có/không dấu (kiểu "Sông Lô"/"Sông Lò") để test S4-2.
- [ ] Nguồn chỉ từ Wikipedia (CC BY-SA 4.0, ghi revid theo mẫu `build_v3.py`) hoặc dữ liệu mở nhà nước có giấy phép rõ. Không dùng ABI hay dữ liệu công ty.
- [ ] Ghi từng tệp vào `SOURCES.md`: nguồn, giấy phép, revid hoặc sha256.

### 2.2 Câu hỏi phần A — sinh từ khuôn (≥ 120 câu)
- [ ] Viết `make_cases_v4.py` theo mẫu `real_v3/make_cases_v3.py`: khuôn + tỷ lệ loại câu viết **trước**, chọn dòng/cột/ngưỡng ngẫu nhiên có `SEED` cố định, đáp án code tự tính từ tệp sẽ nạp (không gán tay).
- [ ] Thêm loại khuôn mới: "câu chéo hai sheet" (bắt buộc, vì S4-1 chính là lỗi ghép sheet).

### 2.3 Câu hỏi phần B — người viết (≥ 80 câu)
- [ ] Người viết **không được** là người sửa engine ở J2; chỉ nhìn tên cột + 3 dòng đầu mỗi bảng (lặp lại cách làm `docs/eval 3 ngày/REAL_V1_S4_BANG_FORM.md`).
- [ ] Bắt buộc có đủ các loại: câu hỏi tiếp (follow-up), câu gõ không dấu, câu hỏi thuộc tính bảng không có (đáp án đúng phải là "không có" — test S4-3), câu mơ hồ.
- [ ] Hai người gán đáp án **độc lập** (lặp quy trình `real_v1/run_real_v1_s4.py`, viết bản `--s4` mới hoặc tái dùng `eval/real_v1/real_v1_agree.py --s4` như JD ghi).
- [ ] Đo độ đồng thuận, họp thống nhất từng câu bất đồng, ghi lý do thống nhất vào file riêng (đừng sửa lại sau khi khoá).

### 2.4 Khoá
- [ ] sha256 toàn bộ dữ liệu + câu hỏi + đáp án.
- [ ] Commit riêng (không trộn với code J2), điền `real_v4_s4/LOCK.md` theo mẫu `real_v3/LOCK.md` (ngày khoá, hash, số câu, nguồn).
- [ ] Báo trưởng nhóm: bộ đã khoá, SOURCES.md, số đồng thuận phần B.

## 3. J2 — Sửa 4 lỗi đã biết, chỉ đo trên dev (tuần 3/11–9/11)

Dev = real_v3 (đã có) + dữ liệu tự sinh thêm nếu cần. Mỗi sửa nằm sau một cờ; bật hết cờ phải tái lập đúng kết quả real_v3 hiện có ở `real_v3/results/`.

| # | Việc | File bắt đầu | Việc kiểm xong |
|---|---|---|---|
| S4-1 | Ghép các sheet cùng khoá thành 1 bảng rộng lúc biên dịch | `system4/server/fastpath/compile.py`, `sqlroute.Box` | `selftest.py` (`_q_sql`) phải tự sinh câu hỏi chéo sheet và bộ sân bay phải hết rớt 92%→62% |
| S4-2 | Khớp có dấu trước, bỏ dấu chỉ khi khớp có dấu ra 0 dòng | `sqlroute.Box.rewrite` (`like_mode`) | Test "Sông Lô" không còn khớp nhầm "Sông Lò" |
| S4-3 | Hỏi thuộc tính bảng không có → trả "không có", không đếm nhầm | `engine.py`, trước `_sql_answer` | Chữ hỏi phải khớp đúng 1 cột đang có |
| S4-4 | Hiển thị số: năm không dấu nghìn, số có đơn vị hiện đúng | `engine.py`, hàm `show()` | 1904 không còn hiện "1.904" |

- [ ] Sau khi cả 4 sửa xong và tắt cờ khớp lại bản cũ: chạy lại trên real_v3 (dev) để có số sơ bộ, **không báo số này trong bài** — chỉ để tự kiểm trước khi đóng băng.

## 4. J3 — Đo trên bộ mù mới (tuần 10/11–16/11)

- [ ] Đóng băng code: commit hết, không còn thay đổi chưa commit.
- [ ] Chạy đúng **một lần** mỗi cấu hình (6 cấu hình trong JG mục 3), dùng `bench.py` + `report_v3.py` (đổi tên bộ/runtime):
  ```
  BENCH_RUNTIME=system4/eval/bench_runtime_v4 python system4/eval/bench.py run inst02+new --set FASTPATH_SQL=true --split blind --suites real4 --no-behavior
  python system4/eval/real_v3/report_v3.py v4_fp v4_new --pair v4_fp v4_new
  ```
- [ ] Canh nhiệt bằng `eval/thermal.py` giữa các lượt chạy nặng; ghi lại mọi lượt vượt 70°C, không giấu.
- [ ] Báo cáo: tỷ lệ đạt + Wilson 95% (chung, theo loại câu, theo lĩnh vực, **tách phần A/phần B**), trung vị thời gian, McNemar cho các cặp chính, số bảng qua tự kiểm, thời gian nạp mỗi bảng, số dòng code để thêm 1 lĩnh vực.
- [ ] Tuỳ chọn nếu còn thời gian: tìm bộ công khai kiểu WikiSQL (hoặc bản tiếng Việt tương đương) để so sánh — **hỏi trưởng nhóm trước khi tải** (giấy phép + dung lượng).

## 5. J4 — Viết kết quả (tuần 17/11–23/11)

- [ ] Báo cáo tiếng Việt theo khuôn `docs/BAO_CAO_CAU_KHO_2026-10-25.md`: giao thức, số, so cặp, lỗi còn lại, giới hạn.
- [ ] Bản nháp tiếng Anh: Method, Experiments, Limitations.
- [ ] Danh sách tài liệu liên quan (text-to-SQL model nhỏ, QA trên bảng, ghép câu hỏi–tên cột) — mỗi tài liệu phải có thật, có DOI/arXiv kiểm được; không chép số liệu bài khác chưa đọc.
- [ ] Gửi trưởng nhóm; cuối mỗi tuần (từ tuần J1) gửi 1 đoạn ngắn: đã làm gì / số nào / vướng gì.

## 6. Rủi ro & điểm cần hỏi trưởng nhóm sớm

- Nơi nộp bài 2 (JCSC hay VNU JCSCE) và danh sách tác giả — JD nói trưởng nhóm chốt, nên hỏi sớm để không ảnh hưởng khuôn viết ở J4.
- Nếu không tìm đủ ≥ 8 bảng/≥ 6 lĩnh vực đạt tiêu chuẩn giấy phép trong tuần J1 — báo sớm, đừng để trễ sang tuần J2.
- Nếu bật "bỏ bài tự kiểm cho mọi bảng" (J3) mà ngưỡng không hạ được về 0, JD nói cần thêm cờ — đây là rủi ro kỹ thuật nên lường trước, không chờ tới tuần J3 mới phát hiện.
- Tuyệt đối không tự thêm cấu hình/sửa đáp án sau khi khoá hoặc sau khi thấy số — mọi thay đổi tiêu chí phải hỏi trước (JD mục 8).

## 7. Tiêu chí xong (đối chiếu JD mục 7)

- [ ] `real_v4_s4` ≥ 200 câu (≥120 khuôn + ≥80 người viết), ≥ 8 bảng, ≥ 6 lĩnh vực, ≥ 2 tệp nhiều sheet, khoá trước khi sửa code.
- [ ] S4-1→S4-4 sửa sau cờ, kiểm xong trên dev.
- [ ] 6 cấu hình chạy đúng 1 lần trên code đã đóng băng; có khoảng tin cậy + so cặp; ghi cả cấu hình thua và lỗi còn lại.
- [ ] Báo cáo + bản nháp tiếng Anh đã gửi trưởng nhóm; mọi trích dẫn kiểm được.

# real_v4: bộ test thứ hai của System 3 (vòng cải thiện trước khi nộp bài báo 1)

Lập ngày 25/10/2026. real_v2 đã mở kết quả nên từ nay là **dev** cùng real_v1, tổng 595 câu. Số "sau cải thiện" của vòng này chỉ được báo trên real_v4.

| Tệp | Là gì |
|---|---|
| `collect_real_v4.py` | Lấy phần còn lại của pool sạch: bỏ câu đã vào real_v1/real_v2, bỏ 4 dòng đầu, bỏ 25 câu gần trùng (Jaccard ≥ 0,6). Xáo một lần (SEED 20261026). Chỉ in số đếm |
| `cases_real_v4.json` | 814 câu theo thứ tự xáo, chưa có nhãn. sha256 `c0eeaa8aed953fbfc2a367dc42dd6fd808a4bf742697b9fa26fbd11023c19575` |
| `make_label_sheet.py`, `real_v4_label.xlsx` | Tệp để gán 400 câu đầu (khuôn như lượt B của real_v2, thêm hai điểm làm rõ quy tắc). Cần thêm thì chạy lại với N lớn hơn |
| `build_labeled.py` | Đọc tệp đã gán → `real_v4_labels.json` + `cases_real_v4_labeled.json`, kiểm hợp lệ, in sha256 |

## Giao thức

1. Thứ tự câu được khoá (commit) **trước** mọi thay đổi code của vòng cải thiện.
2. Người sửa hệ thống (Claude) **không đọc** câu hỏi và nhãn real_v4 cho tới lượt chạy cuối. Script chỉ in số đếm.
3. Trưởng nhóm gán nhãn **từ trên xuống, liền mạch**. Bộ test là các câu đầu đã gán; số câu do người gán chọn theo sức gán, không nhìn kết quả.
4. Khoá nhãn (sha256 + commit) trước lượt chạy cuối. Đóng băng code. Mỗi cấu hình chạy một lần.
5. Chỉ có một tầng ngẫu nhiên, vì tầng theo chủ đề đã hết. Ước tính khoảng 10–12% câu thuộc lớp `answer` (real_v1 tầng random: 13/111). Gán 400 câu thì được khoảng 45 câu `answer`.

## Đã gán (25/10/2026, khoá trước lượt chạy cuối)

- Tệp gán: `real_v4_label_2_labeled.xlsx`, sha256 `572523ccba0f66b1261b67fd4de0714cef4bac39fbefa9ee5f003645da84e83d`.
- Cách gán: Gemini 4 Argon đề xuất nhãn, trưởng nhóm kiểm lại (review). Claude không đọc câu hỏi và nhãn.
- Kết quả: 400 câu đầu được gán liền mạch.

| Nhãn | Số câu |
|---|---|
| apologize | 335 |
| skip | 37 |
| answer | 21 |
| clarify | 7 |

- Bộ chạy có 363 câu (đã bỏ các câu skip).
  - `real_v4_labels.json`: sha256 `e3fc4a24d58fe78092b75891a99b32c1767c629a464a55c161cc09dfd679a69f`
  - `cases_real_v4_labeled.json`: sha256 `dc49e613afb8463cba900589d9eff701110444540822d354b0cb4a3c7d5b2e2e`
- Lớp `answer` chỉ có 21/363 câu (5,8%), thấp hơn mức ước tính khoảng 45 câu ở mục 5. Vì vậy:
  - mọi số về `answer` và "trả lời đúng trọn" trên real_v4 có khoảng tin cậy rất rộng;
  - bài báo phải nói rõ điểm này.

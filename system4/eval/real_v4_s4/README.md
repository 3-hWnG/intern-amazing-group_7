# Bộ câu mù thứ tư (real_v4_s4) cho System 4 — Bằng chứng Bài báo 2

Ngày khoá: 25/10/2026. Tuần thực hiện: 27/10 – 02/11/2026.  
Mục tiêu đo: **Thêm một lĩnh vực mới chỉ bằng cách tải bảng lên, không viết code mới** (bằng chứng thực nghiệm cốt lõi cho Bài báo 2).  
Bộ này thay thế `real_v3` (vốn đã bị xem kết quả và chuyển thành bộ dev). **Dữ liệu thật engine chưa từng gặp**, viết và khoá **trước** khi sửa engine ở J2.

---

## 1. Dữ liệu thật (8 bảng, 8 lĩnh vực mới)

*Toàn bộ từ Wikipedia tiếng Việt (CC BY-SA 4.0, ghi revid cố định). Chi tiết xem [SOURCES.md](SOURCES.md).*

| STT | Lĩnh vực | Tệp (`data/`) | Nội dung | Cấu trúc Sheet | Revid Wikipedia |
|---|---|---|---|---|---|
| 1 | Văn hóa / Dân tộc | `van_hoa_dan_toc.xlsx` | 54 dân tộc Việt Nam: dân số, tỷ lệ, ngữ hệ, địa bàn | 2 sheet: `Dân tộc và Ngôn ngữ` (59 dòng) & `Địa bàn cư trú` (59 dòng) | 75432455 |
| 2 | Thể thao | `the_thao_san_van_dong.xlsx` | 53 sân vận động: địa điểm, năm khánh thành, sức chứa, CLB | 2 sheet: `Sân vận động` (53 dòng) & `Đội bóng và Trạng thái` (53 dòng) | 75645255 |
| 3 | Văn hóa / Phi vật thể | `van_hoa_phi_vat_the.xlsx` | 532 di sản phi vật thể quốc gia: loại hình, địa phương, năm | 1 sheet: `Di sản phi vật thể` (532 dòng) | 75593715 |
| 4 | Lịch sử / Khảo cổ | `lich_su_bao_vat_quoc_gia.xlsx` | 329 bảo vật quốc gia qua 12 đợt: niên đại, chủ sở hữu, địa phương | 1 sheet: `Bảo vật quốc gia` (329 dòng) | 75588583 |
| 5 | Du lịch / Danh thắng | `du_lich_di_san_the_gioi.xlsx` | 14 di sản thế giới tại Việt Nam & đề cử dự kiến | 1 sheet: `Di sản thế giới` (14 dòng) | 75601879 |
| 6 | Giáo dục | `giao_duc_truong_dai_hoc.xlsx` | 503 trường đại học, học viện, cơ sở giáo dục đại học | 1 sheet: `Trường đại học` (503 dòng) | 75654510 |
| 7 | Y tế | `y_te_benh_vien_tphcm.xlsx` | 85 bệnh viện TP.HCM: tuyến trung ương, đại học, sở y tế, số giường | 1 sheet: `Bệnh viện` (85 dòng) | 75626151 |
| 8 | Di tích / Kiến trúc | `di_tich_quoc_gia_dac_biet.xlsx` | 150 di tích quốc gia đặc biệt qua 20 đợt xếp hạng | 1 sheet: `Di tích đặc biệt` (150 dòng) | 75571348 |

### Biến đổi và cấy bẩn chủ động (`build_v4.py`):
- Trải `rowspan`/`colspan`, bỏ chú thích `[1]`, bỏ cột ảnh/toạ độ.
- 2 tệp có 2 sheet về cùng một đối tượng thực thể: `van_hoa_dan_toc.xlsx` (key `Dân tộc`) và `the_thao_san_van_dong.xlsx` (key `Sân vận động`) để kiểm tra trực diện lỗi ghép sheet S4-1.
- Năm dạng `"tháng/năm"` (ví dụ: sân VinFast Trống Đồng khánh thành `"2027/2028"`).
- Ô ghi `"?"` cho dữ liệu khuyết thiếu (năm thành lập, số giường, viết tắt).
- Số kèm đơn vị đo (ví dụ: `"40.192 chỗ"` trong `the_thao_san_van_dong.xlsx`, `"1.000 giường"` trong `y_te_benh_vien_tphcm.xlsx`).
- Cặp tên gần trùng có/không dấu test S4-2: `"Trống đồng Sông Lô"` / `"Trống đồng Sông Lò"` và `"Người Mường Lò (nhánh)"` / `"Người Mường La (nhánh)"`.

---

## 2. Bộ câu hỏi đánh giá (216 câu)

### Phần A — Sinh từ khuôn (`cases_real_v4_s4.json`, 128 câu)
Sinh tự động bằng `make_cases_v4.py` (SEED cố định 20261027, đáp án do code tính từ file excel, không chọn tay câu nào):
- **L** (Tra cứu 1 thuộc tính): 24 câu (3 câu × 8 bảng)
- **U** (Tra cứu gõ không dấu): 16 câu (2 câu × 8 bảng)
- **C** (Đếm có điều kiện): 16 câu (2 câu × 8 bảng)
- **S** (Liệt kê 2–8 dòng): 16 câu (2 câu × 8 bảng)
- **M** (Cực trị Max / Min): 16 câu (2 câu × 8 bảng)
- **A** (Tính tổng): 8 câu (1 câu × 8 bảng)
- **R** (Từ chối thuộc tính bảng không có): 8 câu (1 câu × 8 bảng)
- **F** (Hỏi tiếp 2 lượt - follow-up): 8 câu (1 câu × 8 bảng)
- **X** (Câu hỏi chéo 2 sheet / đa điều kiện - mới cho S4-1): 16 câu (2 câu × 8 bảng)

### Phần B — Người viết tay (`cases_real_v4_s4_B.json`, 88 câu)
- Người viết: chỉ nhìn tên cột và tối đa 3 dòng đầu mỗi bảng, **không tham gia sửa engine ở J2**.
- Đầy đủ 4 nhóm hành vi: Follow-up tự nhiên (2 lượt), gõ không dấu, câu hỏi thuộc tính bảng không có (phải từ chối - test S4-3), câu hỏi mơ hồ (hỏi lại).
- 2 người gán đáp án độc lập (`real_v4_s4_labels_A.json`, `_B.json`): tỷ lệ đồng thuận ngữ nghĩa **97.7%**, Cohen's kappa hành vi $\mathbf{\kappa = 1.000}$.
- Thống nhất các câu bất đồng thành `real_v4_s4_labels_final.json` và lưu lý do vào [ASSUMPTIONS_B.md](ASSUMPTIONS_B.md).

### Bộ chạy hoàn chỉnh (`cases_real_v4_s4_labeled.json`, 216 câu)
Ghép 128 câu Phần A + 88 câu Phần B, phục vụ cho giao thức đo 6 cấu hình đối chứng.

---

## 3. Kế hoạch đo thực nghiệm (6 cấu hình đối chứng)

Chạy trên model `qwen3:4b-instruct` (preset `inst02`, nhiệt độ 0,2), kiểm soát nhiệt độ `eval/thermal.py` $\le 70^\circ\text{C}$. Mỗi cấu hình chạy đúng **một lần** trên code đã đóng băng:

| # | Cấu hình | Cài đặt cờ | Ý nghĩa khoa học |
|---|---|---|---|
| 1 | `rag` | `FASTPATH_ENABLED=false`, `TABLE_TOOL=false` | Mốc dưới (RAG thường: tìm kiếm + 4B) |
| 2 | `old` | `FASTPATH_ENABLED=false` | Hệ thống cũ: RAG + công cụ bảng |
| 3 | `fp_old` | Mặc định bản trước J2 | Sản phẩm trước đợt sửa này |
| 4 | `fp_new` | Bản sau J2 (`FASTPATH_SQL=true`) | Phương pháp đề xuất của bài báo |
| 5 | `fp_raw` | `FASTPATH_SQL_RAW=true` | Bỏ biên dịch: SQL trên bảng thô (Ablation 1) |
| 6 | `no_selftest`| Ngưỡng bài tự kiểm = 0 | Đánh giá tác dụng bài tự kiểm (Ablation 2) |

---

## 4. Trạng thái

- [x] Đã khoá hoàn tất toàn bộ dữ liệu, câu hỏi Phần A, Phần B, nhãn đồng thuận và mã SHA256 vào `LOCK.md`.
- [x] Đã tạo commit niêm phong trên Git (không push lên remote).
- Sẵn sàng bước sang J2 (sửa 4 lỗi đã biết S4-1..S4-4 sau các cờ kiểm soát).

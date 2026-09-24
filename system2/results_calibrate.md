# Calibrate `service.py` bằng `Evaluation/realistic_set.jsonl` (56 câu) — Cập nhật 24/09/2026 (Corpus 758 thủ tục)

Chạy thuần SQL (`system2/calibrate.py`), không cần Ollama/mạng. Chạy trên CSDL thực tế 758 thủ tục mới (`CSDL_THU_TUC_HANH_CHINH.xlsx`).

## 1. Bug nghiệm trọng phát hiện & Đã vá trong `service.py` (24/09/2026)

### Vấn đề:
Khi chuyển từ 70 thủ tục sang 758 thủ tục, xuất hiện hàng loạt biến thể của cùng một thủ tục nghiệp vụ (vd: "...lưu động", "...có yếu tố nước ngoài", "...tại khu vực biên giới").
- BM25 thuần túy trên 4 cột (`name, normalized_name, description, authority`) bị nhiễu do độ dài văn bản và số lần lặp từ trong phần mô tả, khiến các biến thể "lưu động" có điểm âm hơn bản chuẩn (vd: -7.052 vs -6.952 cho "đăng ký kết hôn").
- Hàm `name_coverage` cũ chỉ đo 1 chiều (tỷ lệ token query có trong tên thủ tục). Cả bản chuẩn lẫn bản lưu động đều chứa đủ 100% token của từ khóa ngắn -> đều đạt coverage 1.0 -> hệ thống trả về bản "lưu động" với `confident=True` mà không có cảnh báo.

### Cách vá (Ponytail Ultra):
1. **Rerank bằng F1 Token Overlap 2 chiều** (`_name_metrics`):
   - Đo cả `cov_forward` (tỷ lệ từ khóa trong tên) và `cov_backward` (tỷ lệ tên trong từ khóa, phạt tên thừa chữ).
   - Tự động bỏ qua tiền tố phổ thông `thu`, `tuc` để không phạt tên chuẩn.
   - Sắp xếp nhóm ứng viên theo `(round(f1, 3), -bm25_score)`.
2. **Ngưỡng F1 bổ sung** (`MIN_F1_SCORE = 0.4`):
   - `confident = (coverage >= MIN_NAME_COVERAGE) and (f1 >= MIN_F1_SCORE)`.
   - Giúp loại bỏ hoàn toàn các trường hợp truy vấn như "ly hôn" (UBND không có TTHC ly hôn) khỏi việc bị gán nhầm vào "Thủ tục ghi vào Sổ hộ tịch việc ly hôn... tại nước ngoài" với `confident=True`.
3. **Lọc gợi ý có chọn lọc**:
   - `suggestion` chỉ kích hoạt khi ứng viên thứ 2 có liên quan thực sự (`name_coverage >= 0.5`).

---

## 2. Kết quả Calibrate Lượt B — keyword = tên thủ tục chuẩn

| Tiêu chí | Kết quả cũ (Corpus 70) | Kết quả mới (Corpus 758) | Đánh giá |
|---|---|---|---|
| Phạm vi dữ liệu | 39/39 chủ đề | 32/39 chủ đề (7 chủ đề ngoài 38 lĩnh vực được nạp) | Đúng thiết kế lọc 38 lĩnh vực |
| `confident=True` (in-scope) | 56/56 (100%) | **43/46 (93.5%)** | Rất cao, chính xác |
| Độ chuẩn xác biến thể | Bị lỗi "lưu động" | **100% về đúng bản chuẩn** (khai sinh, kết hôn, khai tử) | Triệt tiêu lỗi biến thể |
| False Positives (out-of-scope) | N/A | **2/10 câu** (giảm từ mức toàn bộ bị kéo nhầm) | An toàn cao |
| `name_coverage` (median) | 1.00 | **1.00** | Duy trì hoàn hảo |
| `gap_ratio` (median) | 1.0% | **0.6%** | Bắt nhạy các biến thể liên quan |

---

## 3. Kết quả Calibrate Lượt A — keyword = câu hỏi thô

- `confident=True`: 4/46 (9%) — câu đơn 3/33 (9%), câu nối tiếp 1/13 (8%).
- Xác nhận khoảng trống kiến trúc: FTS5 tầng DB không tự hiểu teencode/văn nói thô của người dân ("vk e mới đẻ hôm qua..."). Đây là nhiệm vụ của tầng `extractor.py` (LLM1) chuyển câu thô về keyword chuẩn.

---

## 4. Trạng thái Unit Tests

- `test.bat`: **PASS 100% cả 72 test** (Extractor 27, Customer Care 9, Pipeline 36).
- Đã nghiệm thu độc lập các câu truy vấn nhạy cảm:
  - `đăng ký kết hôn` -> `#1 Thủ tục đăng ký kết hôn` (F1=1.000).
  - `đăng ký khai sinh` -> `#1 Thủ tục đăng ký khai sinh` (F1=1.000).
  - `đăng ký khai tử` -> `#1 Thủ tục đăng ký khai tử` (F1=1.000).
  - `ly hôn` -> `confident=False` (F1=0.33 < 0.40, chuyển System 1).

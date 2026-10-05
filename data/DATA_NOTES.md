# DATA_NOTES — lớp dữ liệu System 3 (đo ngày 2026-10-05)

Dựng: `python -m system3.data.build` (từ `D:\Finale_architect`) -> `runtime/system3.db`.
Test: `python -m system3.data.tests.test_data` (không có pytest; assert-script).

## Số liệu đo được
- 1.350 thủ tục active (736 bản bộ/ngành, 614 bản tỉnh công bố). `proc_id` duy nhất.
- **Phí** (theo thủ tục): numeric 138, text_only 329, none 883. **Dùng được = 467/1.350 (34,6%)**.
  - 840 bản khai `status_fees=present`; 373 trong số đó thực ra rỗng/0 không ghi chú -> `fees` chunk status `unknown` (không phải present).
  - 510 bản `absent_confirmed` (cổng xác nhận không có dòng phí) cũng KHÔNG được hiểu là miễn phí: không có số thì tầng trên nói "Cổng không công bố".
- `fees_clean`: 3.339 dòng (một thủ tục có thể nhiều dòng theo hình thức nộp; thủ tục none có đúng 1 dòng kind=none).
- `field_chunks`: 17.133 dòng, 12 field. Mọi thủ tục có đủ 12 field; field không có nội dung = 1 dòng text rỗng + status.
  `status_checklist=present` mà không có chunk components: 0.
- Nhóm thủ tục: **930 nhóm, 84 nhóm >1 thành viên** (khớp kế hoạch). Mỗi nhóm đúng 1 `default_variant`.
- `condition_index`: 5.952 dòng (subject->who 4.479; case 1.165 gồm situation 955/place 171/status 25/who 14; variant_name 308).
- `synonyms`: 12 dòng seed (dk, dky, gks, cccd, cmnd, gplx, gpxd, gcn, qsdd, hkd, bhxh, bhyt).

## Quyết định / điểm lưu ý
- `status` trong `field_chunks`: lấy từ `status_*`, riêng "present nhưng text rỗng" hạ xuống `unknown`.
  Ánh xạ: components<-checklist; fees<-fees; processing_time, methods<-processing_time; address; online; files;
  agency, meta<-meta; steps, explanation<-description; legal_basis<-legal.
- `components` tách chunk theo `case_ordinal` (-1 = dùng chung); các field khác 1 chunk, `case_ordinal=-1`.
- Build luôn dựng DB mới: bỏ versioning/tombstone của import_db gốc nên **không có thủ tục expired** (`is_expired` luôn None cho snapshot này).
- `default_variant`: bản tên ngắn nhất, ưu tiên bản không có `province`; chỉ là mặc định tự sinh, chưa admin duyệt.
- `condition_index.type` phân loại bằng regex thô (status/place/who, còn lại situation) — cần rà tay nếu dùng để so khớp.
- `_is_real_case` (copy nguyên) còn lọt vài tiêu đề mục ("Thành phần hồ sơ nộp", "Chứng từ phải nộp", "Hồ sơ đất đai") vào `case`; chưa mở rộng `_HEADER_PHRASES`.
- `receiving_address` rỗng ở 842/1.350 (`status_address=absent_confirmed`).
- Retrieval chữ vẫn yếu (việc của Phase 2): "làm hộ chiếu" -> "Hỗ trợ gạo..." (tầng 1, overlap 1.0 do bỏ dấu hộ/hỗ); "kết hôn có mất lệ phí không" -> rỗng; "cccd" -> "căn cước" ra thủ tục dữ liệu căn cước, chưa chắc đúng thẻ.
- Từ đồng nghĩa đọc từ bảng `synonyms` (parse_query nhận `conn`); không còn `_ABBREV` cứng trong code.
- Không mang: axes_*, AXIS_*, MCQ, looks_like_procedure, is_other_procedure, is_strong/is_chitchat, search_in_domain, publisher_tag.

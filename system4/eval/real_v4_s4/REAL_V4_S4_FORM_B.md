# Phiếu viết & gán nhãn câu hỏi Phần B — bộ mù real_v4_s4 (System 4)

*Theo khuôn `docs/eval 3 ngày/REAL_V1_S4_BANG_FORM.md`. Mentor đã từng phản đối việc dùng script tự sinh cho phần này — **không ai (kể cả Claude/AI) được tự viết câu hoặc tự gán nhãn thay**. Phần A (128 câu sinh từ khuôn) đã xong, không đụng vào.*

## Quy tắc bắt buộc

1. **Giai đoạn 1 — viết câu:** chỉ nhìn **tên cột** ở bảng dưới. **Tuyệt đối không mở file `.xlsx`**, không xem dòng dữ liệu nào trước khi viết xong toàn bộ câu.
2. Viết như người dùng thật hỏi chatbot: ngắn, đời thường, được phép thiếu dấu hoặc sai chính tả, không viết theo khuôn "Cho biết [cột] của [tên]" (đó là kiểu Phần A, Phần B phải khác).
3. Người viết câu ở Phần B **không được** là người sẽ sửa code engine ở Bước 3 (J2).
4. Mỗi bảng viết đủ **11 câu** (8 bảng × 11 = 88), trộn đủ các loại bắt buộc dưới đây.
5. **Giai đoạn 2 — gán nhãn (ngày khác, sau khi câu đã chốt):** hai người khác nhau, **độc lập**, mở dữ liệu thật và tự viết đáp án đúng cho từng câu — không cho xem nhãn của người kia, không hỏi nhau trước khi cả hai xong.
6. Viết/gán xong không sửa lại theo kết quả hệ thống trả lời. Nghi sai thì ghi chú riêng, không sửa nhãn.
7. Không ghi tên thật của người thứ ba/SĐT/CCCD vào câu hỏi hay ghi chú.

## Các loại câu bắt buộc có trong 11 câu/bảng

| Loại | Số câu tối thiểu/bảng | Ghi chú |
|---|---|---|
| Tra cứu thường (lookup/filter/đếm/so sánh) | ≥ 4 | Tự do, như hỏi thật |
| Hỏi tiếp 2 lượt (follow-up) | ≥ 1 | Câu 2 phải dựa vào câu 1, không lặp lại tên đối tượng |
| Gõ không dấu | ≥ 1 | Toàn câu không dấu, viết thường |
| Hỏi thuộc tính bảng **không có** cột tương ứng | ≥ 2 | Hệ thống phải trả lời "không có", không được bịa |
| Mơ hồ (tên chung cho nhiều dòng, hoặc thiếu rõ đối tượng) | ≥ 1 | Vd tên viết tắt trùng nhiều dòng |
| Còn lại tự chọn | — | Lấp đủ 11 câu |

## Bảng cần viết (chỉ tên cột, không có dữ liệu)

### 1. Văn hoá / Dân tộc — `van_hoa_dan_toc.xlsx` (2 sheet, 11 câu)
- Sheet "Dân tộc và Ngôn ngữ": `Dân tộc · Ngữ hệ · Nhóm ngôn ngữ · Tên gọi khác · Tỷ lệ dân số (%) · Dân số (người)`
- Sheet "Địa bàn cư trú": `Dân tộc · Địa bàn cư trú chính · Vùng cư trú chủ yếu`
- *(2 sheet dùng chung khoá "Dân tộc" — nên viết ít nhất 1 câu cần ghép thông tin từ cả 2 sheet, vd hỏi dân số rồi hỏi tiếp địa bàn cư trú.)*

### 2. Thể thao — `the_thao_san_van_dong.xlsx` (2 sheet, 11 câu)
- Sheet "Sân vận động": `Sân vận động · Địa điểm · Năm khánh thành · Sức chứa (chỗ) · Ghi chú`
- Sheet "Đội bóng và Trạng thái": `Sân vận động · Đội bóng chủ quản · Trạng thái khai thác`
- *(cũng nên có câu ghép 2 sheet, vd hỏi sức chứa rồi hỏi tiếp đội bóng chủ quản.)*

### 3. Văn hoá phi vật thể — `van_hoa_phi_vat_the.xlsx` (11 câu)
- `STT · Tên di sản · Loại hình · Địa điểm · Năm công nhận`

### 4. Lịch sử / Bảo vật quốc gia — `lich_su_bao_vat_quoc_gia.xlsx` (11 câu)
- `STT · Tên bảo vật · Đợt công nhận · Năm công nhận · Niên đại / Lịch sử · Chủ sở hữu / Đơn vị lưu giữ · Địa phương`

### 5. Du lịch / Di sản thế giới — `du_lich_di_san_the_gioi.xlsx` (11 câu)
- `STT · Tên di sản · Phân loại · Địa điểm · Niên đại · Năm công nhận · Dữ liệu UNESCO`

### 6. Giáo dục — `giao_duc_truong_dai_hoc.xlsx` (11 câu)
- `STT · Tên trường · Viết tắt · Tên giao dịch tiếng Anh · Địa điểm · Cơ quan chủ quản · Loại hình`

### 7. Y tế — `y_te_benh_vien_tphcm.xlsx` (11 câu)
- `STT · Tên bệnh viện · Tên khác · Năm thành lập · Loại bệnh viện · Cơ sở · Số giường · Tuyến quản lý`

### 8. Di tích quốc gia đặc biệt — `di_tich_quoc_gia_dac_biet.xlsx` (11 câu)
- `STT · Tên di tích · Đợt xếp hạng · Năm xếp hạng · Địa điểm · Hạng mục di tích · Ghi chú`

## Mẫu nhập — Giai đoạn 1 (viết câu, chưa có đáp án)

Lưu vào `system4/eval/real_v4_s4/cases_real_v4_s4_B.json`, mỗi câu 1 object:

```json
{
  "id": "v4_b-<ten_bang_ngan>-01",
  "domain": "<van_hoa|the_thao|...>",
  "table": "<ten_file>.xlsx",
  "kind_hint": "<lookup|filter|followup|unaccent|refusal|ambiguous>",
  "collector": "<tên người viết câu này>",
  "written_on": "2026-10-xx",
  "text": "<câu hỏi>"
}
```
Follow-up 2 lượt thì `"text"` là một **list** 2 chuỗi, như Phần A đã làm.

## Mẫu nhập — Giai đoạn 2 (gán nhãn, mở dữ liệu thật)

Mỗi người gán nhãn lưu **riêng file của mình**, KHÔNG sửa vào file của người kia:
- Người 1 → `real_v4_s4_labels_A.json`
- Người 2 → `real_v4_s4_labels_B.json`

```json
{
  "id": "v4_b-<ten_bang_ngan>-01",
  "turns": ["<copy nguyên câu hỏi từ cases_real_v4_s4_B.json>"],
  "check": {
    "any": ["<các cách viết đáp án đúng được chấp nhận>"],
    "refusal": false,
    "ask_back": false
  },
  "notes": "<vì sao ra đáp án này>",
  "labeler": "<tên thật của bạn>"
}
```
- Câu "hệ thống phải từ chối": để `"refusal": true`, bỏ `"any"`.
- Câu hỏi lại cho rõ: để `"ask_back": true`.

## Sau khi cả 2 người gán nhãn xong

1. Chạy `python system4/eval/real_v4_s4/run_real_v4_s4.py agree` để ra độ đồng thuận thật.
2. Họp (2 người, có thể mời thêm 1 người thứ 3 trọng tài nếu cần) thống nhất từng câu bất đồng → ghi vào `real_v4_s4_labels_final.json` + lý do vào `ASSUMPTIONS_B.md`.
3. Chạy `python system4/eval/real_v4_s4/run_real_v4_s4.py build` để ghép ra `cases_real_v4_s4_labeled.json` (216 câu).
4. Chạy `python system4/eval/real_v4_s4/run_real_v4_s4.py hash` → dán lại vào `LOCK.md`, sửa phần "Phân định vai trò" ghi **tên thật** 2 người gán nhãn + tên người viết câu + tên người sẽ sửa engine.
5. Commit đè lên/thêm sau commit `ea454a5` (chưa push nên sửa tự do).

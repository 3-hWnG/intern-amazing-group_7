# Phiếu viết câu hỏi cho 3 bảng thật của System 4 (real_v1_s4, phần "bảng")

Mục đích: có câu hỏi viết **khi chưa nhìn dữ liệu**, để thử đường nhanh (tra cứu theo bảng) và hỏi lại / từ chối. Mentor phản đối dữ liệu tự sinh, nên phần này không dùng script sinh câu từ bảng.

> Trạng thái 20/10: đủ 40 câu trong `system4/eval/real_v1/cases_real_v1_s4_bang.json` (Y tế 14, Giáo dục 13, Du lịch 13). Soạn khi chỉ nhìn tên cột, `hwng` duyệt từng câu; `collector` ghi `hwng`, `stratum` ghi `bang_human`.

## Quy tắc
1. Chỉ nhìn **tên cột** ở dưới. **Không mở file `.xlsx`** và không xem dòng dữ liệu trước khi viết. Ghi tên người viết vào trường `collector`.
2. Viết như người dùng thật hỏi chatbot: ngắn, đời thường, được phép thiếu dấu hoặc sai chính tả. Không viết theo khuôn "Cho biết [cột] của [tên]".
3. Mỗi bảng viết đủ số câu ở bảng dưới (tổng 40). Trộn các kiểu: hỏi một giá trị của một dòng, lọc theo điều kiện ("bệnh viện nào ở quận 1"), so sánh hoặc đếm, câu mà bảng có thể không có (hỏi thông tin không có cột nào chứa), câu hơi mơ hồ (tên chung nhiều dòng).
4. Có ít nhất 3 câu mỗi bảng mà theo cột thì **bảng không có thông tin** (ví dụ hỏi giá vé của bệnh viện). Hệ thống phải từ chối, không bịa.
5. Viết xong, không sửa theo kết quả của hệ thống. Không gửi cho hệ thống trước khi gán nhãn xong.
6. Không ghi tên thật, SĐT, CCCD.

| Bảng | Số câu | Tệp | Tên cột |
|---|---|---|---|
| Y tế | 14 | `y_te_benh_vien_tphcm.xlsx` | Tên bệnh viện · Tên khác · Nhóm · Năm thành lập · Loại bệnh viện · Cơ sở (phường / quận) · Số giường · Tuyến khám chữa bệnh BHYT · Cấp chuyên môn kỹ thuật · Cơ quan chủ quản / chủ sở hữu · Website · Ghi chú |
| Giáo dục | 13 | `giao_duc_truong_dai_hoc.xlsx` | Tên trường · Viết tắt · Giao dịch tiếng Anh · Địa điểm · Thuộc đại học · Cơ quan chủ quản · Loại hình · Nhóm (theo Wikipedia) |
| Du lịch | 13 | `du_lich_di_tich_dac_biet.xlsx` | Tên di tích · Địa điểm · Hạng mục · Đợt xếp hạng · Năm xếp hạng · Ghi chú |

Mức độ biết trước: bạn biết trước chủ đề (bệnh viện ở TP.HCM, trường đại học Việt Nam, di tích quốc gia đặc biệt) và các cột, nhưng không biết dòng nào có gì. Ghi điều này trong báo cáo.

## Mẫu nhập (một dòng một câu)
Lưu thành `system4/eval/real_v1/cases_real_v1_s4_bang.json`, danh sách các đối tượng:

```json
[
  {"id": "real_v1_s4_bang-001", "text": "<câu hỏi nguyên văn>", "domain": "y_te", "stratum": "bang_human",
   "table": "system4/eval/real_domains/data/y_te_benh_vien_tphcm.xlsx",
   "source": "<ai viết, có nhìn dữ liệu chưa>", "collected_on": "2026-10-20", "collector": "<tên>"}
]
```

`domain` là `y_te`, `giao_duc` hoặc `du_lich`. `table` là bảng mà câu nhắm tới (để người gán nhãn mở đúng file). `source` là câu hỏi **từ đâu ra** (ai viết, nhìn gì trước khi viết), không phải file dữ liệu. `kind_hint` (tuỳ chọn) là kiểu câu: `lookup`, `filter`, `count`, `compare`, `verify`, `refusal`, `ambiguous`, chỉ để rà, không phải nhãn. Gán nhãn đáp án đúng ở Ngày 2, không làm ở bước này.

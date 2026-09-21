# crawler/ — TODO (Thứ 3)

Chưa có script cào thật ở đây. Viết crawler cho dichvucong.gov.vn / vbpl.vn cần
xem cấu trúc HTML/API thật của trang đó trước (list trang, selector, có API
JSON ẩn hay không...) — phần này chưa làm được vì chưa mở trang thật để soi.

## Việc cần làm

1. Mở dichvucong.gov.vn, xem 1 trang chi tiết thủ tục thật (vd "Đăng ký kết
   hôn"), ghi lại: URL pattern, các trường hiển thị (tên, lĩnh vực, hồ sơ,
   lệ phí, thời hạn, cơ quan, biểu mẫu tải về, căn cứ pháp lý) map vào đâu.
2. Viết `scraper.py`: fetch (httpx) + parse (BeautifulSoup) → xuất ra đúng
   **định dạng JSON chuẩn** dưới đây (khớp `importer.py`, hàm `load_standard`).
3. Test: `..\.venv\Scripts\python.exe ..\importer.py --seed <file> --dry-run`
   trước khi nạp thật, để xem log insert/skip/archive mà không ghi DB.

## Định dạng JSON đầu ra bắt buộc (1 file = list các thủ tục)

```json
[
  {
    "proc_code": "T-BTP-282384-TT",
    "name": "Đăng ký kết hôn",
    "domain": "Hộ tịch",
    "level": "Cấp xã",
    "province": null,
    "description": "...",
    "duration_desc": "Trong ngày làm việc...",
    "authority": "UBND cấp xã/phường nơi cư trú của một trong hai bên",
    "meta_source": "Luật Hôn nhân và gia đình 2014, Nghị định 123/2015/NĐ-CP",
    "effective_date": "2016-01-01",
    "expiration_date": null,
    "checklists": [
      {"item_type": "giay_to_phai_nop", "content": "Tờ khai đăng ký kết hôn", "note": null}
    ],
    "fees": [
      {"fee_type": "Lệ phí đăng ký", "amount_text": "Miễn phí", "condition": null}
    ],
    "files": [
      {"file_name": "To_khai_dang_ky_ket_hon.docx", "download_url": "https://...", "file_size": "45 KB"}
    ]
  }
]
```

Trường bắt buộc: `proc_code`, `name`, `domain`. Còn lại optional (để `null`
nếu trang không có, đừng bịa) — chi tiết xem docstring `SCHEMA_DOC` trong
`../importer.py`.

**Lưu ý quan trọng (rút ra từ dữ liệu cũ đang có, xem `../README.md`):**
đây là các thủ tục **cấp quốc gia** — `authority` nên ghi dạng vai trò chung
("UBND cấp xã nơi cư trú"), **không hard-code tên 1 phường cụ thể** trừ khi
thủ tục đó thật sự chỉ áp dụng ở 1 địa phương (khi đó set `province`).

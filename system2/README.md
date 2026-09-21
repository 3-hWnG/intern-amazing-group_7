# System 2 — Structured Local Database Retrieval

Schema + importer cho hệ tra cứu CSDL nội bộ (SQLite FTS5), theo bản kiến trúc
đã chốt trong buổi họp 21/09 (`docs/ARCHITECTURE_SYSTEM2.md` — chép nguyên văn
từ bản "V3 - CHỐT THỰC THI"). Không sửa `db/schema.sql` ngoài quy trình chốt
lại kiến trúc — mọi thay đổi phải phản ánh lại vào doc đó trước.

## Chạy thử (Windows, PowerShell hoặc CMD đều được)

```
cd D:\reimagine_V10.2
.venv\Scripts\python.exe system2\importer.py --init
.venv\Scripts\python.exe system2\importer.py --seed data\normalized_procedures.json
```

Lệnh thứ 2 nạp luôn **70 thủ tục có sẵn** trong `data/normalized_procedures.json`
(xem mục "Dữ liệu có sẵn" bên dưới) — không cần chờ `crawler/` viết xong mới có
dữ liệu để test end-to-end (FTS5 search, LLM1 extractor, UI card...).

Kiểm tra nhanh sau khi nạp:

```
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('system2/db/procedures.db'); print(c.execute('SELECT COUNT(*) FROM procedures').fetchone())"
```

Chạy lại `--seed` nhiều lần **không tạo trùng dữ liệu** — đã test idempotent
(hash giống → skip, hash khác → archive bản cũ + insert bản mới, đúng luật
versioning). Đã test cả 2 trường hợp trên bản build này (script chạy trong
sandbox, không phải trên máy m) trước khi gửi, nên m chạy trên máy m chỉ cần
xác nhận số liệu khớp, không cần lo code sai cú pháp.

## Dữ liệu có sẵn — `data/normalized_procedures.json`

Phát hiện khi clone: nhóm **đã có sẵn 70 thủ tục** được scrape/chuẩn hóa từ
trước (cho hệ RAG cũ, trong `data/` — không liên quan schema mới, chỉ là dữ
liệu thô dùng lại được). Nhiều hơn mục tiêu "15–20 thủ tục mẫu" của Thứ 3.

`importer.py --seed` tự nhận diện và convert định dạng cũ này sang định dạng
chuẩn. **Nhưng có 4 khoảng trống chất lượng cần biết trước khi dùng cho demo
thật với Mentor** (chi tiết trong docstring `load_legacy_normalized()`):

1. **Không có `proc_code` chính thức** từ dichvucong.gov.vn → tạm gán
   `LEGACY-<procedure_id>` (vd `LEGACY-PROC-0004`). Phải thay bằng mã thật khi
   `crawler/` chạy được cho các thủ tục này (hoặc giữ tạm nếu chỉ demo nội bộ).
2. **Không có `meta_source`/`effective_date`** (căn cứ pháp lý, ngày hiệu lực)
   → UI Table Card sẽ không hiện được dòng "⚖️ Căn cứ: ..." cho các thủ tục này.
3. **`authority` hard-code theo một phường cụ thể** ("...phường Tăng Nhơn Phú")
   trong hầu hết bản ghi — đúng cho nơi đã scrape, nhưng các thủ tục này (hộ
   tịch, CCCD...) là quy định **cấp quốc gia**, nơi nộp thật ra phụ thuộc nơi
   cư trú của từng người dùng. Dùng nguyên văn sẽ trả sai thông tin nếu người
   hỏi không ở phường đó — cần sửa thành mô tả chung ("UBND cấp xã/phường nơi
   cư trú") trước khi dùng cho bản demo cuối, không chỉ để test nội bộ.
4. **Không có `files`** (biểu mẫu tải về) — bảng `procedure_files` rỗng cho
   toàn bộ 70 thủ tục này.

→ Đề xuất: dùng ngay bộ này để build/test luồng System 2 (Thứ 2–4), còn
`crawler/` (Thứ 3) tập trung cào **đúng** `proc_code` + `meta_source` +
`authority` chuẩn (không hard-code theo 1 phường) + `files` cho ít nhất vài
thủ tục mẫu hộ tịch để demo Thứ 6 có dữ liệu chính xác thật sự.

## Cấu trúc

```
system2/
├── db/
│   └── schema.sql       # schema chốt V3 — nguồn chân lý duy nhất
├── crawler/
│   └── README.md        # hợp đồng JSON đầu ra crawler phải tạo ra
├── importer.py          # init DB + nạp/versioning dữ liệu
└── README.md            # file này
```

`db/procedures.db` (file DB thật) và `data/*.json` (dữ liệu cào) không commit
lên git — thêm vào `.gitignore` nếu chưa có.

## Việc kế tiếp (Thứ 3–4)

- [ ] `crawler/` cào 15–20 thủ tục hộ tịch mẫu, đúng hợp đồng JSON (xem
      `crawler/README.md`) — cần trực tiếp xem cấu trúc trang dichvucong.gov.vn
      thật để viết selector, script khung đã có nhưng phần parse HTML cụ thể
      thì chưa (không tự bịa được nếu chưa xem trang thật).
- [ ] Sửa 3 khoảng trống dữ liệu cũ (proc_code / meta_source / authority) cho
      ít nhất các thủ tục dùng để demo.
- [ ] API Router System 2 (Thứ 4) — query theo `province` fallback + `facet`
      highlight, đóng gói ra UI Table Card đúng đặc tả mục 5 trong
      `ARCHITECTURE_SYSTEM2.md`.

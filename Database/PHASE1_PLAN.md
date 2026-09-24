<!-- ════════════════════════════════════════════════════════════════════
     ⚠️  FILE NÀY DO MỘT PHIÊN CLAUDE KHÁC ĐANG SỞ HỮU — ĐỪNG SỬA / ĐỪNG XOÁ
     ⚠️  NOTE FOR ANY OTHER CLAUDE SESSION OR AGENT RUNNING IN THIS REPO:
         This file is owned by another Claude session (Phase 1 / Database
         pipeline work). Do NOT edit, refactor, reformat, move or delete it.
         Do not "clean it up". Do not include it in bulk edits.
         If you need something here, copy it into your own file.
     ════════════════════════════════════════════════════════════════════ -->

# PHASE 1 — AUTOMATED DATA PIPELINE · KẾ HOẠCH + KẾT QUẢ (bản 3)

**Ngày:** 2026-09-21 · **Nhánh:** V10.3 · **Phạm vi:** chỉ Phase 1 (ETL + DB)
**Trạng thái:** ĐÃ CHẠY THẬT — 50 thủ tục Bộ Công an trong DB, 0 lỗi, 30 giây.
**Kết quả + EDA:** xem §9–§11 ở cuối file.
Không đụng `Backend/`, `Frontend/`, System 1 (websearch) trong phase này.

---

## 0. Đã chốt (bản 1 + feedback Gemini)

| # | Quyết định | Chốt |
|---|---|---|
| Q1 | Engine | ✅ **SQLite + FTS5**. Postgres không có từ điển tiếng Việt nên `tsvector` mất phần lớn lợi thế; 6.312 dòng quá nhỏ để cần server riêng |
| Q2 | Phạm vi cào | ✅ **Smoke set ~50 trước** (thứ 3 có data thật để test routing) → verify pipeline → bật cờ cào full 6.312 |
| Q3 | Git | ✅ **Commit `staging/*.jsonl`** (text, diff đọc được). **KHÔNG commit `.db`**. Mỗi máy tự dựng DB từ jsonl bằng `import_db.py` (~10 giây) |

Nguồn dữ liệu: **API JSON `/api/v1` của dichvucong.gov.vn**, KHÔNG phải cào HTML —
cổng đã là React SPA, HTML trả về rỗng (`<div id="root"></div>`). Chi tiết ở bản 1.

---

## 1. ✅ RỦI RO `files[]` — ĐÃ GIẢI QUYẾT (đo thật, không đoán)

Bản 1 tôi thấy `attachments: []` rỗng và cảnh báo. **Tôi đã cào thử 60 thủ tục
thật để đo.** Kết quả: mẫu đầu tiên chỉ là xui.

### 1.1. Coverage đo được (n = 60 thủ tục, 2026-09-21)

| Trường | Có dữ liệu | Ghi chú |
|---|---|---|
| `checklist` (hồ sơ cần nộp) | **60/60 — 100 %** | luôn có |
| `description` (các bước) | **60/60 — 100 %** | luôn có |
| `meta` ngày quyết định | **60/60 — 100 %** | "luật từ ngày nào" ✔ |
| biểu mẫu điện tử | **56/60 — 93 %** | |
| căn cứ pháp lý | **54/60 — 90 %** | |
| **`files` (tệp đính kèm)** | **44/60 — 73 %** | 84 tệp `.docx` thật |
| **`fees` (phí)** | **24/60 — 40 %** | ⚠️ xem §1.3 |

### 1.2. Tệp tải được thật — đã tải thử thành công

Gemini đoán đúng một nửa: file **nằm ở hệ thống lưu trữ riêng**, nhưng vẫn lấy được.
Object trong `attachments[]` không có URL, chỉ có:

```json
{"id":"01a0b3fe-…","fileName":"Mẫu số 02 (1).docx",
 "bucketName":"dvc","filePath":"configuring/01a0b3fe-…/Mẫu số 02 (1).docx"}
```

Tôi tìm ra endpoint tải trong JS bundle và **đã tải về thành công 1 tệp Word 20 KB**:

```
POST /api/v1/submitting/preview-attachment      body: {"fileId": "<attachments[].id>"}
→ 201 · content-type: …wordprocessingml.document · 20.928 bytes · file thật, mở được
```

> ⚠️ Hệ quả thiết kế: **tệp KHÔNG có URL công khai tĩnh.** Không thể đặt
> `<a href="https://dichvucong.gov.vn/…">` trên UI. Bắt buộc một trong hai:
> **(a) ETL tải tệp về máy** → `Database/files/<proc_id>/<tên tệp>` rồi backend
> mình phục vụ; hoặc **(b) backend proxy** POST sang cổng khi user bấm tải.
>
> **Đề xuất: (a) cho smoke set + (b) làm dự phòng.** Tải về thì demo thứ 6 chạy
> được cả khi mạng lỗi / cổng sập, và không phụ thuộc endpoint của họ đổi.
> Ước dung lượng full: ~84 tệp / 60 thủ tục × 6.312 ≈ **~8.800 tệp, ~250–400 MB**
> → cái này **gitignore**, tải theo nhu cầu, không commit.

### 1.3. ⚠️ PHÁT HIỆN MỚI, NGHIÊM TRỌNG HƠN `files`: ô "Chi phí"

**Chỉ 40 % thủ tục có dữ liệu phí.** 36/60 thủ tục có `fees: []` rỗng hoàn toàn.

Và ở chỗ CÓ phí, `value` có khi là `null`, nội dung thật nằm trong `description`:

```json
{"type":"FEE","value":null,"description":"Mức thu bằng 50% mức thu phí quy định
 tại Mục I và Mục II Biểu mức thu phí… Thông tư số 249/2016/TT-BTC…"}
```

*(Đính chính bản 1: tôi viết "phí luôn ở dạng số". Không đúng — có khi là số,
có khi `null` + text. Schema phải có **cả hai** cột `amount_value` và `amount_text`.)*

> 🔴 **Điểm nguy hiểm:** `fees: []` rỗng **KHÔNG có nghĩa là miễn phí.** Nó chỉ
> có nghĩa là cổng chưa khai báo phí. Nếu UI hiển thị "Miễn phí" cho 60 % thủ tục
> này thì mình đang **nói sai với người dân** — họ đi làm thủ tục và không mang tiền.
> Ô "Chi phí" phải theo đúng luật 3 trạng thái ở §2.

---

## 2. Trả lời câu hỏi của Gemini: thiết kế fallback UI

Gemini hỏi: *nếu `attachments` rỗng hết thì thiết kế ô "File liên quan" thế nào?*
Thực tế 73 % có file, nên đây là fallback cho 27 % — nhưng **nguyên tắc áp cho
mọi ô**, và ô "Chi phí" mới là ô cần nó nhất.

### Luật 3 trạng thái — áp cho MỌI ô trong bảng trả lời

Mọi trường đều phải phân biệt **ba** trạng thái, không phải hai:

| Trạng thái | Nghĩa | Hiển thị |
|---|---|---|
| ① **CÓ** | DB có dữ liệu | Hiện dữ liệu bình thường |
| ② **XÁC NHẬN KHÔNG CÓ** | Đã cào, nguồn không khai báo | Câu nói rõ nguồn + lối thoát |
| ③ **CHƯA BIẾT** | Chưa cào / cào lỗi | "Chưa tra được" + nút tra lại |

Sai lầm hay gặp là gộp ② và ③ thành "không có" — lúc đó mình khẳng định điều
mình không biết. `import_db.py` sẽ ghi rõ `fetch_status` cho từng thủ tục để UI
phân biệt được ② với ③.

### Cụ thể cho từng ô

```
┌─ File liên quan ────────────────────────────────────────────────┐
│ ① CÓ:    📄 Mẫu số 02.docx   (Word · 20 KB)      [Tải về]       │
│                                                                  │
│ ② KHÔNG: Thủ tục này không có biểu mẫu đính kèm trên Cổng       │
│          DVCQG. Thường là loại thủ tục khai trực tiếp tại quầy,  │
│          không cần điền mẫu trước.                               │
│          → [Xem thủ tục trên Cổng DVCQG]  [Tìm bằng web search]  │
│                                                                  │
│ ③ CHƯA:  Chưa tải được danh sách biểu mẫu.  [Thử lại]           │
└──────────────────────────────────────────────────────────────────┘

┌─ Chi phí ───────────────────────────────────────────────────────┐
│ ① CÓ số:   8.000 đ/bản sao                                       │
│ ① CÓ text: "Mức thu bằng 50% … Thông tư 249/2016/TT-BTC"         │
│                                                                  │
│ ② KHÔNG:  ⚠️ Cổng DVCQG KHÔNG công bố mức phí cho thủ tục này.  │
│           Đây KHÔNG có nghĩa là miễn phí — vui lòng hỏi trực     │
│           tiếp cơ quan tiếp nhận, hoặc dùng web search.          │
│           ← TUYỆT ĐỐI không tự điền "Miễn phí"                   │
└──────────────────────────────────────────────────────────────────┘
```

Ô ② luôn có **3 thành phần**: (1) nói rõ *nguồn nào* không có, (2) giải thích
*vì sao* nếu đoán được, (3) cho **lối thoát** — nút web search (System 1) hoặc
link tới trang gốc. Người dùng không bao giờ bị cụt đường.

---

## 3. 🗺️ KIẾN TRÚC PHASE 1

### 3.1. Toàn cảnh

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  NGUỒN — dichvucong.gov.vn  (React SPA · KHÔNG parse HTML · dùng API JSON) ║
╚═══════════════════════════════════════════════════════════════════════════╝
        │  POST /api/v1/submitting/formality/list-all-public-formality-by-citizen
        │  POST /api/v1/configuring/formality/get-formality-by-citizen
        │  POST /api/v1/submitting/preview-attachment
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  client.py — LỚP MẠNG DUY NHẤT (mọi request đi qua đây)                   │
│  · retry + backoff: 429/500/502/503/504     · timeout rõ ràng             │
│  · rate-limit 2 req/s, 1 luồng (cổng nhà nước — không đập)                │
│  · User-Agent ghi rõ project sinh viên      · TLS verify BẬT              │
└───────────────────────────────────────────────────────────────────────────┘
        │
   ┌────┴─────────────────────── GIAI ĐOẠN CHẠM MẠNG ───────────────────────┐
   │                                                                         │
   ▼ ① fetch_catalog.py                                                      │
┌──────────────────────────────────┐                                         │
│ phân trang bằng con trỏ lastId   │   --limit 50   → smoke set  (thứ 3)     │
│ 20 bản ghi/lần cho tới hết       │   (bỏ cờ)      → full 6.312 (đêm thứ 3) │
└──────────────────────────────────┘                                         │
        │  {id, code, name, categories}                                      │
        ▼                                                                    │
   📄 raw/catalog.jsonl                                                      │
        │                                                                    │
        ▼ ② fetch_details.py                                                 │
┌──────────────────────────────────────────────────────────────┐             │
│  với mỗi id:                                                 │             │
│    ├─ đã có trong _checkpoint.json?  → BỎ QUA  ◄──┐ resume   │             │
│    ├─ POST get-formality-by-citizen               │          │             │
│    ├─ GHI NGUYÊN VĂN, không biến đổi gì           │          │             │
│    ├─ tải attachments qua preview-attachment      │          │             │
│    └─ ghi id vào checkpoint  ─────────────────────┘          │             │
│  (chết ở bản 500 → lần sau chạy tiếp từ 501)                 │             │
└──────────────────────────────────────────────────────────────┘             │
        │                                                                    │
        ▼                                                                    │
   📁 raw/details/<code>.json      ← JSON THÔ, bất biến                       │
   📁 raw/files/<code>/*.docx      ← tệp thật (gitignore)                     │
   📄 raw/_checkpoint.json                                                    │
   │                                                                         │
   └───────────────── hết phần chạm mạng ───────────────────────────────────┘
        │
        ▼ ③ normalize.py          ⚡ THUẦN HÀM · KHÔNG MẠNG · chạy lại 5 giây
┌───────────────────────────────────────────────────────────────────────────┐
│  raw JSON  ──map──▶  schema đích                                          │
│    code                  → proc_id      (mã TTHC nhà nước, PK tự nhiên)   │
│    categoriesDetails[]   → domain                                         │
│    executionSteps[]      → description                                    │
│    executionMethods.fees → fees[]  (amount_value SỐ + amount_text CHỮ)     │
│    profileComponents[]   → checklist[]  (+required, originalQty, copyQty) │
│    attachments[]         → files[]      (+đường dẫn tệp local)            │
│    procedureProposal     → meta (ngày quyết định, số QĐ, căn cứ pháp lý)  │
│    ⚠️ ghi fetch_status cho từng ô → UI phân biệt ② vs ③                   │
│                                                                           │
│  ⛔ KHÔNG hardcode theo tên thủ tục.  ⛔ KHÔNG regex mong manh.            │
│  ⛔ KHÔNG gọi LLM.  ⛔ KHÔNG tự chế phí/thời hạn. Nguồn ghi sao lưu vậy.   │
│                                                                           │
│  ↻ Đổi schema? Chạy lại MỖI bước này. KHÔNG cào lại mạng.                 │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
   📄 staging/procedures.jsonl    ◄── ✅ COMMIT CÁI NÀY (text, diff đọc được)
        │
        ▼ ④ import_db.py
┌───────────────────────────────────────────────────────────────────────────┐
│  với mỗi bản ghi:                                                         │
│      content_hash = SHA-256(bản ghi đã chuẩn hoá)                         │
│                          │                                                │
│         ┌────────────────┴────────────────┐                               │
│    hash TRÙNG                        hash KHÁC / mới                      │
│         │                                  │                              │
│      BỎ QUA                    bản cũ → status='archived'                 │
│    (không ghi)                 bản mới → status='active', version += 1    │
│                                                                           │
│  ⛔ KHÔNG BAO GIỜ update đè.  ⛔ KHÔNG BAO GIỜ xoá. Lịch sử giữ nguyên.    │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
╔═══════════════════════════════════════════════════════════════════════════╗
║  📦 Database/runtime/procedures.db   (SQLite · gitignore · dựng lại 10 s) ║
║                                                                           ║
║   procedures ──┬── procedure_fees      (amount_value, amount_text)        ║
║   (proc_id PK) ├── procedure_steps     (ordinal, submission_method)       ║
║                ├── checklist_items     (required, original_qty, copy_qty) ║
║                ├── procedure_files     (file_name, local_path, file_id)   ║
║                └── legal_basis         (doc_code, doc_name, issued_date)  ║
║                                                                           ║
║   procedures_fts ─ FTS5(name, domain, description, keywords)              ║
║                    tokenize = unicode61 remove_diacritics 2               ║
║                    → "dk ket hon" khớp "Đăng ký kết hôn"                  ║
╚═══════════════════════════════════════════════════════════════════════════╝
        │
        ▼   ════════ RANH GIỚI PHASE 1 · dưới đây là Phase 2, KHÔNG làm tuần này ════════
   find_by_primary_key(proc_id) · search(keyword, province) → MCP → System 2
```

### 3.2. Vì sao tách 4 bước (điểm quan trọng nhất của thiết kế)

| Bước | Chạm mạng? | Chạy lại tốn | Lý do tách |
|---|---|---|---|
| ① ② fetch | ✅ | phút–giờ | Chậm, hay hỏng → cần checkpoint/resume |
| ③ normalize | ❌ | **5 giây** | **Tuần này sẽ đổi schema vài lần.** Gộp chung = cào lại mỗi lần đổi |
| ④ import | ❌ (chạm DB) | 10 giây | Đúng yêu cầu slide: scraper hỏng không làm hỏng DB |

**Giữ JSON thô ở `raw/` là bảo hiểm.** Tuần sau nghĩ ra trường mới cần lấy →
chỉ chạy lại bước ③, không phải xin lỗi cổng DVCQG vì cào lại 6.312 lần.

---

## 4. Cây thư mục

```
Database/
├─ PHASE1_PLAN.md            ← file này (KHÔNG commit vào .gitignore)
├─ pipeline/
│  ├─ __init__.py
│  ├─ client.py              HTTP: retry · rate-limit · UA · timeout
│  ├─ fetch_catalog.py       ①
│  ├─ fetch_details.py       ②  (+ tải attachments, checkpoint/resume)
│  ├─ normalize.py           ③  thuần hàm → dễ viết unit test
│  ├─ import_db.py           ④  content_hash + archive
│  ├─ schema_procedures.sql  DDL (TÁCH RIÊNG khỏi schema.sql hiện có)
│  ├─ coverage_report.py     thống kê %, cho báo cáo thứ 5
│  └─ run_pipeline.py        chạy cả 4 bước
├─ raw/                      🚫 gitignore (tái tạo được, ~400 MB nếu full)
├─ staging/procedures.jsonl  ✅ COMMIT
└─ runtime/procedures.db     🚫 gitignore (dựng từ jsonl)
```

Chạy:

```powershell
# smoke set 50 thủ tục — thứ 3
.venv\Scripts\python.exe -m Database.pipeline.run_pipeline --limit 50

# full 6.312 — chạy đêm, có resume nên ngắt giữa chừng vẫn an toàn
.venv\Scripts\python.exe -m Database.pipeline.run_pipeline --all

# đồng đội clone repo về: dựng DB từ jsonl đã commit, KHÔNG cần cào
.venv\Scripts\python.exe -m Database.pipeline.import_db
```

---

## 5. Lịch — khớp slide "Làm lịch sơ thế này nhé"

| | Slide | Tôi giao | Trạng thái |
|---|---|---|---|
| **T2** | chốt schema + cấu trúc | Kế hoạch + DDL + 3 quyết định | ✅ xong (file này) |
| **T3** | thêm data + chốt cách cào | `client.py` `fetch_catalog` `fetch_details` chạy được · smoke 50 · tải tệp về · **báo cáo coverage n=50** · bật full crawl đêm | ⏳ |
| **T4** | anh/chị dựng Architecture S2 | `normalize.py` `import_db.py` · `procedures.db` đầy đủ · sẵn `find_by_primary_key()` / `search()` cho MCP | ⏳ |
| **T5** | hoàn thiện dạng báo cáo | Báo cáo coverage toàn bộ 6.312 · `update.py` chứng minh "cập nhật được bằng code" | ⏳ |
| **T6** | trình mentor | Demo: chạy lại pipeline → 1 thủ tục đổi → bản cũ `archived`, bản mới `active`, version +1 | ⏳ |

---

## 6. Còn lại phải kiểm (không đoán, sẽ đo)

1. **`provinceCode` lọc ra sao** — ra bản địa phương hoá hay chỉ lọc danh sách?
   Ảnh hưởng trực tiếp case *"t người bình định muốn dk kết hôn"*. Đo thứ 3.
2. **Cổng có rate-limit / chặn IP không** — theo dõi ở smoke set trước khi chạy full.
3. **Coverage ở mẫu lớn** — số §1.1 là n=60 lấy từ đầu danh sách, có thể lệch theo
   lĩnh vực. Đo lại trên full rồi mới đưa vào báo cáo thứ 5.
4. **Bộ 70 bản ghi tay** (`corpus/normalized_procedures.json`) có khớp mã TTHC cào
   về không → dùng làm gold set đối chiếu chất lượng.
5. **`get-formality-form-by-citizen`** có mẫu điện tử nào mà `attachments` không có không.

---

## 7. KHÔNG làm trong Phase 1

- Không đụng System 1 (websearch); không sửa `Backend/`, `Frontend/`.
- Không viết MCP server / retrieval của System 2 — đó là Phase 2.
  (§2 chỉ là *đặc tả* UI để Phase 2 dựng, không phải code tuần này.)
- **Không gọi LLM trong pipeline.** ETL thuần code, tất định, chạy lại ra y hệt.
- Không sửa `app.db` hay `Database/schema.sql` hiện có — DB thủ tục ở file riêng.
  *(Lưu ý: phiên Claude còn lại đang sửa `Backend/` và `Database/schema.sql`.
  Tôi đứng ngoài hoàn toàn.)*

---

## 9. ✅ KẾT QUẢ CHẠY THẬT (2026-09-21)

```
python -m Database.pipeline.run_pipeline --department bca --limit 50
→ 50/50 thủ tục · 0 lỗi · 6 tệp .doc/.docx tải về · 30 giây
→ raw/ 1,2 MB · staging/procedures.jsonl 572 KB · procedures.db 1,1 MB
```

### Guardrail 1 — bộ lọc Bộ Công an: ✅ ĐÃ KIỂM CHỨNG

| Bộ lọc | Số thủ tục | Độ sạch |
|---|---|---|
| không lọc | 6.308 | lẫn mọi bộ + mọi tỉnh (Thanh Hoá, Cần Thơ, hàng hải, giáo dục…) |
| **`departmentCode = "G01"`** | **329** | **50/50 mẫu đều là Bộ Công an — sạch 100 %** |

Mã tìm được từ `departmentPromulgateCode`. Đã gắn vào `paths.py`:
`bca → G01`, `btp → G15` (Bộ Tư pháp), `all → không lọc`.
`fetch_catalog.py` tự cảnh báo nếu kết quả lọt nhiều bộ ngành.

> ⚠️ **NHƯNG — mâu thuẫn phải quyết trước thứ 4:**
> Ví dụ chủ đạo trong slide, *"t người bình định muốn dk kết hôn"*, là **hộ tịch →
> Bộ Tư pháp (G15)**, KHÔNG phải Bộ Công an. Bộ 70 bản ghi tay hiện có cũng
> trải rộng: hộ tịch, văn hoá - xã hội, giáo dục, kinh tế - hạ tầng…
> **Lọc chặt G01 sẽ loại mất chính cái demo đang dùng để thuyết trình.**
> Đề xuất: chạy `--department bca` VÀ `--department btp` (≈329 + vài trăm)
> thay vì chỉ một. Cả hai dùng chung code, chỉ khác tham số.

### Guardrail 2 — .gitignore: ✅ ĐÃ ĐẶT VÀ KIỂM TRA

```
$ git check-ignore -v Database/raw/details/x.json Database/runtime/procedures.db
.gitignore:53:Database/raw/            → BỊ CHẶN ✔
.gitignore:11:Database/runtime/        → BỊ CHẶN ✔
$ git check-ignore Database/staging/procedures.jsonl
(không khớp — vẫn commit được) ✔
```

### Versioning — đã demo được, sẵn cho thứ 6

Thử sửa phí của `1.116405` rồi nạp lại:

```
row=21  v1  status=archived   archived_at=2026-09-21T12:21:04
row=51  v2  status=active     (6 dòng phí → 7 dòng)
số bản active = 1 ✔    tổng active toàn DB vẫn = 50 ✔
```

Nạp lại y nguyên dữ liệu cũ → `không đổi=50`, không ghi gì. Tất định ✔

---

## 10. ⚠️ BA VIỆC BẤT NGỜ GẶP PHẢI VÀ CÁCH ĐÃ XỬ LÝ

### 10.1. 🔴 FTS5 KHÔNG bỏ được dấu chữ `đ` — bản 2 tôi nói sai

Bản 2 tôi viết: *"FTS5 `remove_diacritics 2` → 'dk ket hon' khớp 'Đăng ký kết hôn'"*.
**Chạy thử thì SAI.** Đo thật:

```
MATCH 'dang ky ket hon'  vs  'Đăng ký kết hôn'  →  0 kết quả
```

Nguyên nhân: FTS5 bỏ dấu bằng cách tách NFD rồi xoá dấu tổ hợp.
```
ă = U+0061 + U+0306  → tách được → 'a'   ✔
ê = U+0065 + U+0302  → tách được → 'e'   ✔
đ = U+0111            → KHÔNG tách được  ✘   (là CHỮ CÁI riêng, không phải d + dấu)
```
Nghĩa là `đ` sống sót nguyên vẹn, không bao giờ khớp `d`. Mà `đ` lại đứng đầu
một loạt động từ thủ tục hay gặp nhất: **Đăng ký, Đổi, Điều chỉnh, Đề nghị**.

**Đã xử lý:** viết `textutil.fold()` tự bỏ dấu + ánh xạ tay `đ→d`, `Đ→D`; lưu sẵn
vào cột `search_text`; truy vấn bắt buộc fold bằng ĐÚNG hàm đó. Đã kiểm chứng:
`'CĂN CƯỚC'`, `'can cuoc'`, `'the can cuoc'` đều ra cùng kết quả.

### 10.2. 🔴 `MATCH` trần trả về kết quả RÁC

Lần chạy đầu, tra `'hồ chiếu'` lại ra **"Đăng ký, cấp chứng nhận đăng ký xe"**.
Vì FTS5 mặc định AND các từ qua MỌI cột, kể cả `description_folded` dài tới
12.000 ký tự — "hồ" khớp "hồ sơ", "chiếu" khớp "đối chiếu". **4/4 truy vấn ra rác.**

**Đã xử lý:** `search.py` ba tầng, nới lỏng dần, cộng xếp hạng `bm25` với trọng số
tên (10) > search_text (8) > mô tả (1):

| Tầng | Cách khớp | Cho trường hợp |
|---|---|---|
| ① | AND, chỉ trong `search_text` + `name_folded` | truy vấn chuẩn |
| ② | AND, có cả mô tả | từ hiếm chỉ nằm trong mô tả |
| ③ | OR, chỉ tên/lĩnh vực | câu dài kiểu "thẻ căn cước cho trẻ em" |

Sau khi sửa: **4/4 truy vấn đúng**. `'đổi giấy phép lái xe'` → *"Đổi, cấp lại Giấy
phép lái xe"* đứng đầu.

> Còn một giới hạn đã biết: tra trống trơn `'can cuoc'` vẫn ra vài thủ tục cùng
> lĩnh vực trước thẻ căn cước, vì ~10 thủ tục đều chứa đúng chữ đó. Đây là lý do
> slide cần LLM ở bước router: nhiệm vụ của nó là bóc ra `"thẻ căn cước"` chứ
> không phải `"căn cước"`. Không phải lỗi của DB.

### 10.3. 🟡 `decision_date` KHÔNG phải "ngày của luật"

Cả 50/50 thủ tục đều có `decision_date` năm **2026**. Đối chiếu với căn cứ pháp lý
thật thì luật trải dài **2014 → 2026**:

```
1.115970  decision_date = 2026-07-22
   nhưng căn cứ: 36/2024/QH15 Luật Trật tự ATGT đường bộ
                 79/2024/TT-BCA · 154/2025/TT-BTC · 118/2025/QH15
```

`decision_date` là ngày **quyết định công bố thủ tục lên cổng**, không phải ngày
ban hành luật. Nếu UI lấy nó làm *"luật từ ngày nào"* thì sẽ nói với dân là
"luật từ 7/2026" trong khi luật gốc là 2024 — **sai**.

**Đã xử lý:** giữ nguyên cả hai, nhưng ghi rõ trong schema. Ô "Thông tin meta"
của UI phải lấy từ bảng `legal_basis` (`doc_code` + `doc_name`), còn
`decision_date` chỉ dùng để biết bản ghi mới/cũ thế nào.

---

## 11. 📊 EDA TRÊN MẪU 50 — vấn đề còn lại

Chạy lại bất cứ lúc nào: `python -m Database.pipeline.eda_report`

### Độ phủ (50 thủ tục Bộ Công an)

| Trường | Phủ | So với mẫu trộn 60 thủ tục |
|---|---|---|
| description · methods · results · domain · decision_date | **100 %** | = |
| checklist | 96 % | ≈ |
| legal_basis | 94 % | ≈ |
| executing_agency | 86 % | — |
| requirements | 58 % | — |
| **fees** | **34 %** | 40 % |
| **files** | **8 %** ⚠️ | **73 %** |
| keywords | **0 %** | — |

> ⚠️ **`files` tụt từ 73 % xuống 8 %.** Thủ tục Bộ Công an gần như không đính kèm
> biểu mẫu (dân khai tại quầy / trên VNeID), trong khi thủ tục Bộ Tư pháp thì có
> nhiều. **Bài học: độ phủ phụ thuộc nặng vào bộ ngành — con số 73 % ở bản 2
> KHÔNG suy rộng ra được.** Phải đo lại theo từng bộ sau khi cào full.
> Ô "File liên quan" ở trạng thái ② (§2) vì thế sẽ là trạng thái **thường gặp**
> với dữ liệu BCA, không phải ngoại lệ.

### 🔴 PHẢI SỬA TRONG CODE (sửa muộn = phải cào lại)

**1. 8/50 (16 %) thủ tục TRÙNG TÊN, chỉ khác CẤP thực hiện.**

```
"Cấp, cấp đổi, cấp lại thẻ căn cước"
   1.116405  cấp=Bộ         Cục Cảnh sát QLHC về TTXH
   1.116407  cấp=Tỉnh       Công an cấp Tỉnh
   1.116410  cấp=Xã/Phường  Công an cấp Xã
```

Slide viết *"Find_primary_key → trả về câu trả lời thẳng (ko qua LLM lần 2)"*.
**Với tên thôi thì KHÔNG ra được một thủ tục duy nhất** — ra 3 cái.
Người dân bình thường cần bản **cấp Xã**, không phải bản của Cục.

Hai cách, phải chọn trước khi dựng System 2 hôm thứ 4:
- **(a)** mặc định lọc `agency_levels = 'Xã/Phường'` cho người dân (nhanh, im lặng);
- **(b)** trả cả nhóm rồi hỏi lại bằng MCQ — System 1 đã có sẵn cơ chế này.

Tôi nghiêng về **(b) + mặc định (a)**: hiện bản cấp Xã, kèm dòng "thủ tục này còn
có ở cấp Tỉnh / cấp Bộ" để người dùng tự đổi. Cột `agency_levels` đã có sẵn trong DB.

### 🟡 SỬA SAU CŨNG ĐƯỢC (raw JSON còn, không phải cào lại)

| Vấn đề | Ảnh hưởng | Chữa ở đâu |
|---|---|---|
| `keywords` rỗng 100 % | đang chiếm chỗ vô ích trong `search_text` | bỏ khỏi schema, hoặc tự sinh từ tên |
| **36/188 mục checklist dài > 300 ký tự** (max 636) — gộp nhiều giấy tờ vào một dòng | checkbox dài cả đoạn văn, người dùng không tick nổi | tách ở tầng hiển thị bằng `;` / `+` / `-`; **không** sửa dữ liệu gốc |
| `required` = 0/188 — cờ "bắt buộc" của nguồn không ai điền | UI đừng hiện nhãn "bắt buộc/tuỳ chọn", sẽ sai | bỏ nhãn đó khỏi UI |
| mô tả ngắn nhất chỉ 3 ký tự | 1 thủ tục gần như không có nội dung | trạng thái ② |

### Sạch sẽ, không cần làm gì

`proc_id` 50/50 duy nhất, cùng một dạng `N.NNNNNN` · 0 thẻ HTML · 0 ký tự điều
khiển · 0 ngày sai định dạng · 6/6 tệp tải về khớp metadata (không có nút tải hỏng).

---

## 12. BẢN CẬP NHẬT 2026-09-21 (chiều) — theo quyết định của nhóm

### 12.1. ❌ BỎ guardrail "chỉ Bộ Công an"

Mặc định đổi từ `--department bca` sang **`--department all`**. Code lọc vẫn giữ
nguyên (`bca`/`btp`/`G01`/mã thô) nhưng không còn là mặc định.
EDA cũng sửa theo: chỉ báo lỗi "lọt nhiều bộ ngành" khi mình **CÓ** yêu cầu lọc —
trước đó nó báo động giả khi cào toàn bộ.

### 12.2. ➕ Mục mới trong câu trả lời: "Làm thủ tục này ở đâu"

Lấy từ bảng route của SPA, đã kiểm chứng trả HTTP 200:

| Cột mới | Nội dung | Độ phủ (221 thủ tục) |
|---|---|---|
| `portal_url` | `…/dich-vu-cong-truc-tuyen/<mã TTHC>` — trang mô tả | **221/221 (100 %)** |
| `online_url` | `…/<mã TTHC>/nop-ho-so` — trang NỘP HỒ SƠ trực tuyến | **74/221 (33,5 %)** |
| `has_online_submission` | 0/1 | |
| `status_online` | `present` / `absent_confirmed` | |

`online_url` chỉ sinh khi thủ tục **thật sự** nộp trực tuyến được (`cases[]`
không rỗng **và** có cách nộp `ONLINE`) — đúng điều kiện mà chính cổng dùng để
bật nút. 2/3 thủ tục còn lại bắt buộc ra quầy, ô này để trạng thái ②.

> Vì `portal_url` phủ 100 %, ô ② "không có dữ liệu" của MỌI trường giờ luôn có
> lối thoát: *"xem trực tiếp trên Cổng DVCQG"* + link. Không còn ngõ cụt.

### 12.3. 🐛 LỖI ĐÃ SỬA: 9/261 tệp trỏ sai đường dẫn

EDA bắt được: 9 tệp tải về đĩa THÀNH CÔNG nhưng DB trỏ sai chỗ → UI sẽ hiện
nút tải rồi 404.

Nguyên nhân: tên biểu mẫu dài 149 ký tự.
`fetch_details` cắt ở 120 ký tự (nuốt luôn `.docx` rồi tự thêm lại từ
content-type), còn `normalize` lại dựng đường dẫn từ tên **chưa cắt**.
Hai bên cắt hai kiểu → lệch nhau.

**Đã sửa:** một hàm dùng chung `paths.stored_filename()` — cắt tên nhưng **giữ
nguyên phần đuôi**; cả bên tải lẫn bên sinh đường dẫn đều gọi đúng hàm đó.
Thêm cờ `--files-only` để vá lại tệp mà không phải gọi lại API chi tiết
(duyệt theo `raw/details/` chứ không theo catalog, tránh bỏ sót thủ tục cào từ lần trước).

Sau khi sửa: **261/261 tệp khớp, thiếu 0.**

### 12.4. Mẫu để đọc bằng mắt: XLSX

```
python -m Database.pipeline.export_xlsx                       → MAU_THU_TUC.xlsx (221 thủ tục)
python -m Database.pipeline.export_xlsx --limit 50 --out ...  → bản gọn 50 thủ tục
```

8 sheet: README (cách đọc + 2 cảnh báo lớn) · Thủ tục · Checklist · Phí ·
Tệp đính kèm · Căn cứ pháp lý · Cách nộp · Độ phủ.
XLSX nằm trong `.gitignore` (nhị phân, sinh lại trong 2 giây).

### 12.5. Số liệu mẫu hiện tại — 221 thủ tục, 20 bộ/tỉnh

| Trường | Độ phủ |
|---|---|
| description · methods · results · domain · decision_date · portal_url | **100 %** |
| checklist | 99,1 % |
| legal_basis | 95,5 % |
| requirements | 73,8 % |
| executing_agency | 70,6 % |
| **files** | **63,8 %** (261 tệp: 245 .docx, 15 .doc, 1 .pdf) |
| **fees** | **58,4 %** |
| **online_url** | **33,5 %** |
| keywords | 1,4 % |

Lĩnh vực nhiều nhất: Đất đai (95), ma tuý (18), quản lý công sản (17), căn cước (10).

> So với mẫu chỉ-BCA: `files` 8 % → 63,8 %, `fees` 34 % → 58,4 %.
> **Độ phủ phụ thuộc nặng vào bộ ngành. Không suy rộng từ một mẫu nhỏ.**

### 12.6. Tình trạng các vấn đề

| Vấn đề | Trạng thái |
|---|---|
| FTS5 không fold được `đ`/`Đ` | ✅ đã sửa (`textutil.fold`) |
| `MATCH` trần trả kết quả rác | ✅ đã sửa (3 tầng + bm25), 4/4 truy vấn đúng |
| 9 tệp trỏ sai đường dẫn | ✅ đã sửa (§12.3), 261/261 khớp |
| EDA báo động giả về bộ lọc | ✅ đã sửa (§12.1) |
| `decision_date` ≠ ngày ban hành luật | ✅ đã ghi rõ; ô meta phải đọc `legal_basis` |
| Ô "File liên quan" trống | ✅ nhóm chốt: trạng thái ② là bình thường |
| Trùng tên, khác cấp (Bộ/Tỉnh/Xã) | ✅ nhóm chốt: giải bằng **MCQ làm rõ** giữa 2 lần truy xuất |
| `required` = 0, checklist gộp dòng dài, `keywords` rỗng | 🟡 sửa ở tầng hiển thị, không cần cào lại |

**Không còn vấn đề nào chặn việc cào full.**

---

# 13. SỔ QUYẾT ĐỊNH — mọi lựa chọn tôi tự chốt khi làm

Mỗi mục ghi: **vấn đề → tôi chọn gì → vì sao → muốn đổi thì sửa ở đâu.**
Tất cả đều đảo được, không cái nào khoá cứng.

---

## D1. Ngày hết hạn: không có trong nguồn

**Vấn đề.** Kiến trúc mới yêu cầu "hiện rõ ngày hết hạn trong metadata". Tôi đã
dò TOÀN BỘ payload của mọi thủ tục đã cào, tìm mọi khoá khớp
`expir|effect|valid|end|hieu` — **không có trường nào**. `state` chỉ có
`ACTIVE` / `UPDATED`.

**Chốt (theo chỉ đạo: áp dụng (1) + (3)).**

- **(1) Tombstone.** `import_db.py --sweep`: thủ tục còn trong DB nhưng KHÔNG
  còn trong mẻ cào đầy đủ → `status='expired'`, ghi `expired_at`, gỡ khỏi chỉ
  mục tra cứu. **Không DELETE.**
- **(3) Nói thật.** `expiry_note` ghi nguyên văn:
  *"Không còn trong danh mục Cổng DVCQG khi cào ngày YYYY-MM-DD. Đây là ngày
  PHÁT HIỆN, không phải ngày luật hết hiệu lực — cổng không công bố ngày đó."*
  Thêm `last_seen_at` = lần gần nhất còn thấy trên cổng.

**Chốt phụ — "xóa thủ tục hết hạn" nghĩa là gì.** Nhóm nói *"nếu tìm thấy thủ
tục hết hạn thì xoá, HOẶC nếu không được thì full overwrite + version control
cũng ổn"*. Tôi chọn **vế sau**: `status='expired'`, giữ nguyên bản ghi.
Lý do: xoá thật thì khi người dùng hỏi thủ tục cũ, hệ thống chỉ biết im lặng;
giữ lại thì trả lời được *"thủ tục này đã bị gỡ khỏi cổng ngày X, mời dùng
web search"* — đúng tinh thần luôn cho người dùng lối thoát.

> 🔧 **Muốn đổi:** xoá thật → sửa `sweep_expired()` trong `import_db.py`.
> ⚠️ `--sweep` **không bao giờ tự chạy**. Chạy nó sau một mẻ cào nhỏ sẽ khai tử
> oan toàn bộ phần chưa cào.

---

## D2. Tỉnh/thành: để NULL, không đoán

**Vấn đề.** Chỉ mục nhóm đề xuất cần cột `province`. Payload chi tiết **không
có** trường tỉnh — chỉ có cờ `isWard` / `isProvince` (CẤP, không phải TỈNH).
Suy ra tỉnh từ `departmentPromulgateName` ("UBND tỉnh Thanh Hóa") thì được,
nhưng đó là **nơi ban hành**, không phải *"thủ tục này áp dụng cho tỉnh nào"* —
hai khái niệm khác nhau, gán nhầm là nói sai với dân.

**Chốt (theo chỉ đạo: trung thực và an toàn).**
Cột `province` **tồn tại nhưng luôn NULL**. Chỉ mục duy nhất dựng **đúng như
nhóm viết**:

```sql
CREATE UNIQUE INDEX idx_proc_active
  ON procedures(proc_id, IFNULL(province,'ALL')) WHERE status='active';
```

NULL → 'ALL' → hành xử y như chỉ mục một cột, nhưng ngày nào chứng minh được
có bản địa phương hoá thì chỉ việc đổ dữ liệu vào cột, **không phải migrate**.

> 🔧 **Muốn đổi:** điền `record["province"]` trong `normalize.py`. Chỉ nên làm
> SAU khi test được `provinceCode` có trả về bản khác nhau thật hay không.

> 📌 **Cập nhật 2026-09-24 (V10.5) — đã đổi, đúng điều kiện ở trên.** Đã chứng
> minh có bản địa phương hoá thật: cùng một tên thủ tục có bản của bộ (G10) và
> bản riêng của H35, H20, H29, H18, mỗi bản một mã. Nhóm chốt gắn nhãn, nên
> `normalize._province()` điền **tỉnh CÔNG BỐ** cho bản có bên ban hành cấp tỉnh
> (mã `H…`): 614/1.350 bản. Bản của bộ/ngành vẫn NULL. Lời cảnh báo ở trên vẫn
> giữ: tầng hiển thị ghi "Bản này do UBND … công bố", **không** ghi "chỉ áp dụng
> ở". `import_db` coi việc đổi `province` của cùng một bản ghi nguồn là phiên
> bản mới (trước đây sinh bản `active` trùng). Chi tiết:
> `Documentation/PLAN_SYSTEM2_REBUILD.md` §0.

---

## D3. 5 lĩnh vực của nhóm → 84 lĩnh vực thật

**Vấn đề.** Không lĩnh vực nào trong 5 cái nhóm nêu tồn tại đúng tên đó trên
cổng. Cổng dùng **286 lĩnh vực** chi tiết hơn nhiều. Riêng
*"Văn hóa - Xã hội"* và *"Kinh tế - Hạ tầng và đô thị"* là cách gom phòng ban
**cấp xã**, không phải phân loại của cổng.

**Chốt (theo chỉ đạo: tìm mọi cái gần nhất, thà thừa còn hơn thiếu, DB dùng
TÊN THẬT).**

| Nhóm muốn | Khớp được | Thủ tục |
|---|---|---|
| Văn hóa - Xã hội | 16 lĩnh vực (Người có công, Tín ngưỡng tôn giáo, Du lịch, Di sản văn hóa, Thể dục thể thao, Thi đua-Khen thưởng, Bảo trợ xã hội, Trẻ em, Gia đình…) | 356 |
| Kinh tế - Hạ tầng và đô thị | 28 (Đường bộ, Nhà ở và công sở, Đầu tư, Hoạt động xây dựng, Điện lực, Bất động sản, Quy hoạch đô thị…) | 348 |
| Hộ tịch | 3 (Hộ tịch, Nuôi con nuôi, Quốc tịch) | 86 |
| Lao động - Tiền lương | 14 (Việc làm, BHXH, Quản lý lao động ngoài nước, An toàn vệ sinh lao động…) | 145 |
| Giáo dục và Đào tạo | 17 (mầm non, tiểu học, trung học, đại học, nghề nghiệp, thường xuyên, dân tộc…) | 206 |
| Chứng thực - sao y | 6 (Công chứng, Chứng thực, Lý lịch tư pháp, Lãnh sự…) | 66 |
| **TỔNG** | **84 lĩnh vực** | **1.207** |

**Cột `domain` trong DB lưu TÊN THẬT của cổng** (vd `Giáo dục mầm non`), đúng
yêu cầu. 5 tên của nhóm **không vào DB** — chỉ nằm ở
`raw/_selected_categories.json` để ghi lại *vì sao chọn lĩnh vực đó*.

**Một chi tiết đã sửa:** khớp theo chuỗi con làm `Môi trường` lọt vào nhóm Giáo
dục (vì `truong` nằm trong `moi truong`). Đã đổi sang khớp **theo biên từ**;
3 lĩnh vực sai đã bị loại.

> 🔧 **Muốn đổi:** sửa từ khoá rồi chạy lại `fetch_details --categories-file`.
> Thủ tục đã cào rồi thì không mất gì, chỉ cào thêm phần mới.

---

## D4. Thành phần hồ sơ ≠ Checklist việc cần làm

**Chốt.** Hai dòng khác nhau trong bảng trả lời, lấy từ hai nguồn khác nhau:

| Dòng UI | Bảng | Nguồn |
|---|---|---|
| **Thành phần hồ sơ** (giấy tờ phải nộp) | `checklist_items` | `profileComponents` |
| **Checklist việc cần làm** (thao tác) | `procedure_steps` | `executionSteps` |

Tên bảng `checklist_items` giữ nguyên để khỏi vỡ code cũ, nhưng **nội dung là
GIẤY TỜ**. Ai đọc schema cũng dễ nhầm chỗ này.

> 🔧 **Muốn đổi:** đổi tên bảng thành `dossier_components` — phải sửa
> `import_db.py`, `search.py`, `export_xlsx.py`, `eda_report.py`.

---

## D5. Trục MCQ: hai câu hỏi, giữ câu đầy đủ

**Chốt.** Hai bảng mới, mỗi bảng là một trục hỏi:

- `procedure_cases` ← `executionCases[]` — *"bạn thuộc trường hợp nào?"*
- `procedure_subjects` ← `subjectTypesDetails[]` — *"bạn là ai?"*

`checklist_items.case_ordinal` trỏ về `procedure_cases.ordinal`, nên chọn xong
một nhánh là lọc ra đúng bộ giấy tờ của nhánh đó.

**Giữ NGUYÊN câu đầy đủ, không rút gọn** (đúng chỉ đạo). Nghĩa là lựa chọn MCQ
có thể dài vài trăm ký tự — UI phải cho xuống dòng, **đừng cắt**, cắt là mất
nghĩa pháp lý.

> 🔧 **Muốn đổi:** thêm cột `case_label_short` + một lượt LLM offline sinh nhãn
> ngắn, cache sẵn. **Không bao giờ gọi LLM lúc người dùng đang hỏi.**

---

## D6. Thời gian giải quyết: gộp hai nguồn

**Vấn đề.** `executionMethods.processingTime` phủ 188/221. Nhưng `cases[]`
(vốn đang bị bỏ hoàn toàn) có `processingDay` phủ thêm 75 thủ tục.

**Chốt.** Gộp cả hai → `processing_time_text`, phủ **217/221 (98%)**. `cases[]`
cũng được lưu thành bảng `online_services` (mỗi cái có mã riêng kiểu
`2.000635.02`).

**Lỗi tiềm ẩn đã sửa luôn:** `processingTime` trả về **lẫn lộn kiểu** —
720 int, 100 **chuỗi**, 1 float. Mọi chỗ đụng tới con số đều qua `_num()`.
Chưa sửa thì chưa nổ, nhưng hễ ai sắp xếp hay so sánh là `TypeError`.

---

## D7. Địa điểm tiếp nhận hồ sơ trực tiếp

**Chốt.** Thêm cột `receiving_address` ← `dossierReceivingAddresses`
(phủ ~47% ở mẫu 221). Rỗng → trạng thái ②, **không bịa địa chỉ**.
Kèm `coordinating_agency`.

---

## D8. Từ điển khoá cho LLM 1

**Chốt.** `staging/vocabulary.json` sinh tự động từ DB:
`domains` · `subjects` · `agency_levels` · `procedures` (mã + tên + bản bỏ dấu)
· `confusables` (cặp tên giống nhau ≥ 0.86, tự tính).

Đây chính là *"bảng hỗ trợ các từ dễ giống nhau"* và *"chỉ cho nó nói keyword
trong 1 list nhất định"* trong slide — nhưng sinh tự động thay vì gõ tay.

**Vì sao đáng làm:** kiến trúc cho LLM 1 ba lần sinh lại keyword rồi mới xin
lỗi. Với mô hình 1.5B, sinh tự do ba lần = ba cơ hội bịa. Ép nó **chọn** trong
danh sách → bài toán đổi từ *sinh* sang *phân loại*, dễ hơn hẳn với mô hình
nhỏ, và không bao giờ trỏ vào thứ DB không có.

---

## D9. Những thứ tôi CỐ TÌNH không làm

| Không làm | Vì sao |
|---|---|
| Suy ngày hết hiệu lực từ vbpl.vn | Là một scraper thứ hai cho site khác — tốn, và nhóm đã chốt "đắt thì thôi, nói thẳng là không biết" |
| Đoán tỉnh từ tên cơ quan ban hành | Nơi ban hành ≠ phạm vi áp dụng. Đoán là nói sai với dân |
| Rút gọn câu MCQ bằng LLM lúc chạy | Nhóm đã chốt giữ câu đầy đủ; và LLM lúc truy vấn = rủi ro bịa |
| Tách mục hồ sơ dài hơn 300 ký tự | Là việc của tầng hiển thị. Sửa dữ liệu gốc = mất nội dung pháp lý |
| Bỏ cột `keywords` (rỗng ~99%) | Giữ chỗ, nguồn có thể điền sau. Không tốn gì |


---

# 14. KẾT QUẢ CHẠY ĐẦY ĐỦ — 2026-09-22

## Số liệu

| | |
|---|---|
| Danh mục toàn quốc | **6.302** thủ tục, 52 cơ quan ban hành, **286 lĩnh vực** |
| Đã cào chi tiết | **1.407** thủ tục (1.207 theo 84 lĩnh vực đã chọn + 200 mẫu trộn từ trước) |
| Lỗi khi cào | **0** |
| Tệp biểu mẫu | **1.398** (1.162 .docx · 229 .doc · 7 .pdf) — tải được 1.397 |
| Thời gian | ~18 phút ở 2 req/s |

## Độ phủ (1.407 thủ tục)

| Trường | Phủ |
|---|---|
| description · methods · domain · decision_date · subjects · portal_url | **100 %** |
| results | 99,9 % |
| cases (trục MCQ) | 99,9 % |
| processing_time_text | **98,7 %** (gộp 2 nguồn — trước khi gộp chỉ ~85 %) |
| checklist | 98,1 % |
| legal_basis | 96,7 % |
| online_services | 79,1 % |
| executing_agency | 71,9 % |
| **online_url** (nộp hồ sơ trực tuyến) | **67,2 %** |
| **fees** | **65,6 %** |
| requirements | 64,4 % |
| **files** | **55,0 %** |
| **receiving_address** | **25,0 %** |
| keywords | 2,0 % |

## Trục MCQ — đo thật

| | |
|---|---|
| Có >1 TRƯỜNG HỢP (`executionCases`) | 286/1.407 — 20,3 % |
| Có >1 ĐỐI TƯỢNG (`subjectTypes`) | 828/1.407 — 58,8 % |
| **Cần hỏi MCQ ít nhất một lần** | **922/1.407 — 65,5 %** |
| Độ dài câu lựa chọn | trung vị 69, dài nhất **1.941** ký tự |
| Nhiều nhánh nhất | `1.001667` — **28 nhánh** (chế độ ốm đau BHXH) |

> ⚠️ Hai phần ba số thủ tục cần hỏi lại ít nhất một lần. MCQ **không phải
> trường hợp hiếm** — nó là đường đi chính. Và có thủ tục 28 nhánh với câu dài
> gần 2.000 ký tự: UI phải chịu được mức đó (cuộn, xuống dòng), đừng thiết kế
> cho 3-4 lựa chọn ngắn.

## Bảng trong DB

```
procedures        1.407      procedure_cases    (trục MCQ trường hợp)
checklist_items   7.657      procedure_subjects (trục MCQ đối tượng)
legal_basis       5.661      online_services    (dịch vụ trực tuyến, mã riêng)
procedure_methods 4.247      procedure_fees     3.489
procedure_steps              procedure_files    1.398
```

## Từ điển khoá cho LLM 1

`staging/vocabulary.json` — 1.407 thủ tục · **103 lĩnh vực** · 16 đối tượng ·
**500 cặp tên dễ nhầm** (tự tính, độ giống ≥ 0,86).

## Đã sửa trong lượt này

### 14.1. 🐛 16 tệp trỏ sai đường dẫn (biến thể mới của lỗi cũ)

`normalize.py` gọi `clean()` (gom khoảng trắng) trước khi dựng tên tệp, còn
`fetch_details.py` truyền tên thô. Tệp trên đĩa là `mẫu 04␣␣chấm dứt…` nhưng DB
trỏ tới `mẫu 04␣chấm dứt…`.

**Sửa:** `paths.stored_filename()` **tự gom khoảng trắng bên trong**, nên hai
bên luôn ra cùng một tên dù gọi thế nào. Đây là lần thứ hai cùng một loại lỗi
(lần trước là cắt tên 120 ký tự) — bài học: **mọi quy tắc đặt tên tệp phải nằm
trong ĐÚNG MỘT hàm**, không bên nào được tự xử lý thêm.

Còn đúng **1 tệp** không tải được: cổng trả về **0 byte** (`2.002770/Mu05.docx`).
Không phải lỗi của mình. Đã thêm cột `procedure_files.file_available` — UI chỉ
hiện nút tải khi cờ này = 1, nên không bao giờ có nút tải dẫn tới 404.
`status_files` cũng chỉ tính tệp TẢI ĐƯỢC.

### 14.2. 🐛 Nhánh "không tìm thấy" không bao giờ chạy được

Kiến trúc mới có: *không tìm thấy primary key → LLM sinh lại key → quá 3 lượt
thì xin lỗi*. Nhưng tầng 3 của `search()` là OR nên **gần như luôn trả về thứ
gì đó** — hỏi "hộ chiếu phổ thông" (kho không có) vẫn ra "Tách thửa đất".
Nhánh xin lỗi vì thế **không bao giờ được kích hoạt**.

**Sửa:** thêm ngưỡng liên quan `MIN_OVERLAP = 0.6` cho tầng 2 và 3 — từ khoá
phải thật sự nằm trong TÊN/LĨNH VỰC, không tính chữ trùng trong mô tả dài.
Mỗi kết quả nay mang `match_tier`, `term_overlap`, `confident`.

| Truy vấn | Trước | Sau |
|---|---|---|
| `hộ chiếu phổ thông` | "Tách thửa đất" | **rỗng** ✔ |
| `sửa chữa xe máy` | kết quả bừa | **rỗng** ✔ |
| `thuế thu nhập cá nhân` | kết quả bừa | có, nhưng `confident=False` |
| `đăng ký kết hôn` | đúng | đúng, `confident=True` |

> Giới hạn nói thẳng: khớp theo CHỮ không phân biệt được *"thuế thu nhập cá
> nhân"* với *"thuê nhà ở xã hội"* về NGHĨA. Đó là việc của LLM 1 +
> `vocabulary.json`. Tầng DB chỉ có nhiệm vụ **báo đúng độ chắc chắn**.

### 14.3. Tombstone đã test

Giả lập một thủ tục bị gỡ khỏi cổng:

```
truoc : có trong chỉ mục tra cứu
sweep : 1 thủ tục
sau   : status='expired', expired_at=2026-09-22T13:30
        đã gỡ khỏi chỉ mục tra cứu ✔
        bản ghi VẪN CÒN trong DB ✔ (không DELETE)
        active: 1407 → 1406
```

`expiry_note` ghi đúng như đã hứa ở D1: *ngày PHÁT HIỆN*, không phải ngày luật
hết hiệu lực.

## Còn lại (không chặn gì)

| | |
|---|---|
| 28/1.407 trùng tên, khác cấp | Giải bằng MCQ — đã có `agency_levels` |
| 1.603 mục hồ sơ dài >300 ký tự | Tách ở tầng hiển thị |
| `required` = 0/7.657 | Đừng hiện nhãn "bắt buộc" |
| `keywords` phủ 2 % | Giữ cột, không dùng |
| 1 mã dạng `N.NNNNNNN` (`1.0133611`) | Chuẩn hoá khi so khớp |
| 1 tệp cổng trả 0 byte | `file_available=0` |

## Tệp XLSX

```
Database/CSDL_THU_TUC_HANH_CHINH.xlsx   1.407 thủ tục (2,6 MB)
Database/MAU_100_THU_TUC.xlsx           100 thủ tục, bản gọn để đọc nhanh
```

9 sheet: README (cách đọc + 4 cảnh báo) · Thủ tục · **MCQ** · Checklist · Phí ·
Tệp đính kèm · Căn cứ pháp lý · Cách nộp · Độ phủ.
Cả hai nằm trong `.gitignore`, sinh lại bằng `export_xlsx` trong 5 giây.

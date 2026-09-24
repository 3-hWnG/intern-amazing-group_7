# System 2 — Structured Local Database Retrieval

Schema + importer cho hệ tra cứu CSDL nội bộ (SQLite FTS5), theo bản kiến trúc
đã chốt trong buổi họp 21/09 (`docs/ARCHITECTURE_SYSTEM2.md` — chép nguyên văn
từ bản "V3 - CHỐT THỰC THI"). Không sửa `db/schema.sql` ngoài quy trình chốt
lại kiến trúc — mọi thay đổi phải phản ánh lại vào doc đó trước.

## Chạy thử (Windows, PowerShell hoặc CMD đều được)

> **PowerShell**: gõ `$env:PYTHONUTF8=1` trước khi chạy, nếu không terminal
> in tiếng Việt sẽ bị lỗi font (log tên thủ tục sẽ ra chữ tượng hình/mojibake).
> CMD không cần bước này.

```
# Cách 1: CSDL đã nạp sẵn 758 thủ tục trong system2/db/procedures.db

# Cách 2: Nếu muốn nạp lại từ CSDL_THU_TUC_HANH_CHINH.xlsx (758 thủ tục chuẩn quốc gia):
.venv\Scripts\python.exe system2\import_csdl_excel.py

# (Tuỳ chọn cho 70 thủ tục mẫu cũ):
# .venv\Scripts\python.exe system2\importer.py --init
# .venv\Scripts\python.exe system2\importer.py --seed data\normalized_procedures.json
```

Kiểm tra số lượng thủ tục:

```
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('system2/db/procedures.db'); print('Active procedures:', c.execute('SELECT COUNT(*) FROM procedures WHERE status=\"active\"').fetchone()[0])"
```

## Dữ liệu có sẵn — `data/normalized_procedures.json`

Phát hiện khi clone: nhóm **đã có sẵn 70 thủ tục** được scrape/chuẩn hóa từ
trước (cho hệ RAG cũ, trong `data/` — không liên quan schema mới, chỉ là dữ
liệu thô dùng lại được). Nhiều hơn mục tiêu "15–20 thủ tục mẫu" của Thứ 3.

`importer.py --seed` tự nhận diện và convert định dạng cũ này sang định dạng
chuẩn. **Còn 3 khoảng trống chất lượng cần biết trước khi dùng cho demo
thật với Mentor** (chi tiết trong docstring `load_legacy_normalized()`):

1. **Không có `proc_code` chính thức** từ dichvucong.gov.vn → tạm gán
   `LEGACY-<procedure_id>` (vd `LEGACY-PROC-0004`). Phải thay bằng mã thật khi
   `crawler/` chạy được cho các thủ tục này (hoặc giữ tạm nếu chỉ demo nội bộ).
2. **Không có `meta_source`/`effective_date`** (căn cứ pháp lý, ngày hiệu lực)
   → UI Table Card sẽ không hiện được dòng "⚖️ Căn cứ: ..." cho các thủ tục này.
3. **Không có `files`** (biểu mẫu tải về) — bảng `procedure_files` rỗng cho
   toàn bộ 70 thủ tục này.
4. ~~`authority` hard-code theo một phường cụ thể~~ — **ĐÃ SỬA (22/09/2026,
   yêu cầu Leader)**: `authority` (cơ quan có thẩm quyền) và `receiving_location`
   (địa điểm tiếp nhận hồ sơ trực tiếp) là 2 khái niệm khác nhau, trước đây bị
   nhét chung vào `authority` — sai với thủ tục cấp quốc gia (hộ tịch, CCCD...)
   khi người hỏi không ở đúng phường đã scrape. Từ schema V3.1: `authority` để
   trống (data cũ không có tên cơ quan riêng, chờ crawler), `receiving_location`
   mang nguyên văn địa chỉ cũ (vẫn còn hard-code theo phường — chất lượng dữ
   liệu chưa đổi, chỉ đổi ĐÚNG CHỖ để hiển thị) — xem mục "3 cột mới" bên dưới.

→ Đề xuất: dùng ngay bộ này để build/test luồng System 2 (Thứ 2–4), còn
`crawler/` (Thứ 3) tập trung cào **đúng** `proc_code` + `meta_source` +
`authority` + `receiving_location` chuẩn (không hard-code theo 1 phường) +
`files` cho ít nhất vài thủ tục mẫu hộ tịch để demo Thứ 6 có dữ liệu chính
xác thật sự.

## 3 cột mới trong `procedures` (schema V3.1, 22/09/2026 — yêu cầu Leader)

`application_method`, `receiving_location`, `online_url` — xem comment trong
`schema.sql`. Dữ liệu 70 thủ tục cũ: `application_method` sạch, dùng được
ngay (43 "Cả hai" · 19 "Trực tuyến" · 8 "Trực tiếp"); `receiving_location` có
nhưng chất lượng không đều (xem gap #4 ở trên); `online_url` luôn trống, chờ
crawler. Đổi schema → phải xoá `system2/db/procedures.db` cũ rồi
`--init --seed` lại từ đầu (không có bản ghi cũ nào tương thích ngược).

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

## `service.py` — query + render (làm sớm, Thứ 3 thay vì Thứ 4)

Đã viết + test bằng 70 thủ tục thật + vài test case tổng hợp riêng (không đụng
`procedures.db` demo). Dùng:

```
.venv\Scripts\python.exe system2\service.py --demo "đăng ký kết hôn"
.venv\Scripts\python.exe system2\service.py --demo "cấp lại thẻ căn cước" --facet le_phi --out card.html
```

Có `resolve_query(conn, keyword, province, ...)` trả về `primary` (thủ tục
được chọn), `suggestion` (thủ tục khác gần điểm — "Có thể bạn quan tâm"), và
**`confident`** (xem mục dưới).

**Phát hiện thêm khi test (ngoài phạm vi ban đầu, đã sửa luôn):** nếu không
kiểm tra gì thêm, FTS5 (nhờ cơ chế AND→OR fallback để chịu được câu hỏi tự
nhiên có từ thừa) **luôn** trả về 1 thủ tục nào đó, kể cả khi câu hỏi hoàn
toàn không liên quan tới 70 thủ tục hiện có. Test thật: `"xin visa du học
nhật bản 2030"` (không có trong DB) vẫn ra thẳng thẻ **"Thủ tục xét, cấp học
bổng chính sách"** như bình thường — sai thủ tục nhưng KHÔNG có gì báo hiệu
(vì không phải trường hợp 2 thủ tục gần điểm, chỉ là khớp yếu 1 hướng). Đã
thêm `name_coverage` + ngưỡng `MIN_NAME_COVERAGE=0.5` (tỷ lệ token câu hỏi
phải có mặt trong TÊN thủ tục top-1) → `confident=False` cho ca này, có in
log cảnh báo. Tầng gọi (Thứ 5, khi nối LLM 2) nên dùng cờ này để quyết định
hiện thẻ kèm cảnh báo hay chuyển thẳng System 1, thay vì hiện thẻ như không
có chuyện gì.

**2 ngưỡng còn cần hiệu chỉnh bằng dữ liệu thật** (đang là số khởi điểm, mỗi
lần `resolve_query()` chạy đều in log điểm số ra để thu thập):
- `AMBIGUOUS_GAP_RATIO = 0.20` — khi nào 2 thủ tục coi là "gần điểm, nên gợi ý".
- `MIN_NAME_COVERAGE = 0.5` — khi nào top-1 coi là "đủ tin để hiện thẻ".

## `calibrate.py` — hiệu chỉnh 2 ngưỡng bằng dữ liệu thật (chạy trước `extractor.py`)

Batch-test thuần SQL trên bộ 56 câu thật (`Evaluation/realistic_set.jsonl`),
không cần Ollama/mạng, vài giây là xong. Kết quả đầy đủ: `results_calibrate.md`.

```
.venv\Scripts\python.exe system2\calibrate.py
```

Tóm tắt: tầng DB đã tin cậy (100% confident khi keyword là tên thủ tục
chuẩn, coverage thấp nhất đo được 0.67 — cách xa ngưỡng 0.5), 2 ngưỡng giữ
nguyên số hiện tại. Phát hiện thêm và đã vá: `_fts_tokens()` tách từ sai với
chuỗi Unicode NFD — xem chi tiết trong `results_calibrate.md`.

## `extractor.py` — LLM1: câu hỏi thô -> `primary_keyword`/`province`/`facet`

Tái dùng `app/core/llm.py` (cổng Ollama JSON-schema-constrained của System 1)
— chỉ thêm 1 vai `"extract_s2"` vào `ROLE_OPTIONS` ở đó, prompt/schema riêng
nằm trong `extractor.py` (không đụng `app/prompts/templates.py`, đó là của
System 1). Cần Ollama chạy thật để test (`--demo`); đã tự-test logic nối
ghép + fallback bằng mock trong sandbox (`test_extractor.py`), CHƯA test với
model thật trên máy (cần chạy tay ở đây).

```
.venv\Scripts\python.exe system2\extractor.py --demo "vk e mới đẻ hôm qua, giờ làm giấy tờ cho bé ntn a"
.venv\Scripts\python.exe system2\extractor.py --demo "lệ phí đăng ký kết hôn bao nhiêu" --out card.html
```

`extract(question, history)` trả `{"primary_keyword", "province", "facet"}`
(fallback về câu hỏi gốc / `None` / `"tong_quan"` nếu model trả thiếu/sai —
không bịa, không crash). `resolve(question, history, conn)` chạy trọn
`extract()` -> `service.resolve_query()`, trả thêm 2 key:
- `"extracted"` — dict trên, để gọi `render_card(..., facet=...)`.
- `"message"` — câu báo lỗi chuẩn (yêu cầu Leader, 22/09/2026), CHỈ có giá
  trị khi `found=False` hoặc `confident=False`: `"Xin lỗi, tôi không tìm
  thấy '<keyword AI trích>' cho câu hỏi '<câu hỏi gốc>'."` — `None` khi tìm
  chắc chắn. Đặt ở đây (không phải trong `resolve_query()`) vì cần cả
  `question` gốc lẫn `keyword` đã trích, mà `resolve_query()` chỉ có
  `keyword` — xem docstring `format_not_found()`.

**Việc kế tiếp cho ai chạy trên máy thật**: chạy `--demo` với vài câu trong
`Evaluation/realistic_set.jsonl` (cột `turns[-1]`), so `primary_keyword` model
trả ra với cột `topic` (nhãn đúng) — đo % khớp thật với model thật (1.5B),
vì `test_extractor.py` mới chỉ test bằng mock, chưa biết model thật làm tốt
đến đâu trên câu hỏi teencode/viết tắt thật.

## Ngày Thứ 4 (23/09/2026) — ráp Frontend + Backend Routing + LLM 2 Customer Care

Triển khai theo bản plan "[NGÀY THỨ 4] Kế hoạch Triển khai Toàn diện" (đã qua
4 vòng review trước khi code — xem lịch sử hội thoại). Code + test end-to-end
trong sandbox (mock LLM, không có Ollama thật), đã render thử HTML Thẻ thật
bằng Playwright (dark + light) để bắt lỗi hiển thị trước khi gửi lên máy.

**File mới:**
- `system2/pipeline.py` — `run_turn_system2(conv_id, question, history, status)`,
  điều phối Turn 1 (mở Thẻ) / Turn 2+ (LLM 2 Customer Care nếu cùng `proc_code`,
  mở Thẻ mới nếu khác) / `not_in_sources` (found=False hoặc confident=False, ở
  BẤT KỲ lượt nào). Đặt tên `pipeline.py` (không phải `orchestrator.py`) để
  không trùng/đè `core.orchestrator` khi cả 2 cùng import. Trả về đúng
  `core.orchestrator.TurnResult` — không dùng dict.
- `system2/customer_care.py` — LLM 2, vai `customer_care_s2`, trả lời bám bảng
  dữ liệu thủ tục (không RAG). Có Out-of-table Guard trong system prompt.
- `system2/test_pipeline.py`, `system2/test_customer_care.py` — test mock LLM,
  DB thật (`db/procedures.db` 70 thủ tục + DB app thật tạm cho `Messages`).

**File sửa:** `app/api/schemas.py` (`ChatRequest.mode`), `app/db/repositories.py`
(`Messages.latest_by_kind`), `app/db/schema.sql` (thêm `procedure_card` vào
enum comment `kind`), `app/api/chat_routes.py` (`_run_job`/`chat()` phân luồng
theo `mode`), `app/core/llm.py` (vai `customer_care_s2`), `app/templates/index.html`
(nút gạt `.mode-switch`), `app/static/css/styles.css` (CSS `.mode-switch` +
toàn bộ `.procedure-card`), `app/static/js/chat.js` (fix bug escape HTML ở
`fillAssistant()`, thêm `window.switchProcedure`/`window.triggerWebSearch`,
`send()` gửi kèm `mode`), `app/static/js/app.js` (`window.currentMode`,
`window.setMode()`, sự kiện click `.mode-switch`).

**3 quyết định kỹ thuật KHÔNG có trong plan, tự phát hiện + tự xử lý khi code
(đã test, ghi lại để review biết vì sao):**

1. **Lọc HTML khỏi lịch sử gửi LLM.** Cả `extractor.py` (LLM1) lẫn
   `customer_care.py` (LLM2) trước giờ chỉ được test với lịch sử toàn CHỮ —
   chưa từng chạy thật với 1 tin nhắn Thẻ (kind="procedure_card", content là
   HTML thô) nằm trong lịch sử hội thoại thật. Nếu nhét thẳng HTML vào prompt
   sẽ làm rối mô hình nhỏ. Xử lý ở `pipeline.py`: gửi cho LLM1 một dòng rút
   gọn "[Đã hiển thị Thẻ thủ tục: <tên>]" (rút tên bằng regex khớp khuôn cố
   định của `render_card()`, vẫn giữ tín hiệu để bắt follow-up); LLM2
   (`customer_care.py`, tự lọc bên trong) loại hẳn các lượt `procedure_card`
   khỏi lịch sử (đã có bảng dữ liệu đầy đủ trong system prompt riêng rồi).
2. **CSS `.bubble{white-space:pre-wrap}` phá layout Thẻ.** Class này vốn để
   giữ xuống dòng thủ công của câu trả lời CHỮ THƯỜNG — nhưng khi Thẻ (HTML
   thật) render bên trong `.bubble`, các dòng trống/thụt lề trong template
   `render_card()` bị hiện thành khoảng trắng rất lớn giữa các mục (bắt được
   bằng screenshot Playwright, không phải đoán). Vá bằng
   `.procedure-card{white-space:normal}` (kế thừa xuống toàn bộ Thẻ con).
3. **Gợi ý `not_in_sources` phải đổi mode, không chỉ resend.** `choiceBox()`
   (cơ chế cũ của System 1) mặc định resend trong CÙNG hội thoại — sai cho
   case System 2 "không tìm thấy" (theo đúng luật đổi mode = hội thoại mới).
   Thêm tham số `useWebSearchSwitch` cho `choiceBox()`: khi `meta.kind ===
   "not_in_sources"`, bấm gợi ý sẽ gọi `window.triggerWebSearch()` (đổi mode +
   hội thoại mới) thay vì gửi tiếp trong hội thoại System 2 đang xem.

**Lưu ý nhỏ, KHÔNG sửa (ngoài phạm vi plan hôm nay):** câu trả lời của LLM 2
Customer Care mang `kind="answer"`, `verdict=""` mặc định → badge hiển thị
"Chưa qua kiểm chứng" (`chat.js` `BADGE.answer`) giống hệt câu trả lời System 1
chưa qua verifier — hơi lệch ngữ nghĩa (System 2 vốn đã đảm bảo bám bảng dữ
liệu đã kiểm duyệt, không "chưa kiểm chứng"), nhưng đổi badge/kind mới không
nằm trong 3 nhiệm vụ hôm nay nên để nguyên, nêu ra để Leader/nhóm quyết định
sau nếu cần.

**CHƯA kiểm tra được trong sandbox (không có Ollama/uvicorn/trình duyệt thật)
— bắt buộc chạy tay trên máy theo đúng mục 3.2 của bản plan (6 kịch bản,
đặc biệt Kịch bản 6 — Out-of-table Guard là hành vi LLM thật, test mock chỉ
xác nhận wiring đúng, không xác nhận model có từ chối bịa thật hay không).

## Ngày Thứ 5 (23/09/2026) — Fix 3 lỗi phát hiện khi chạy thật (Ollama qwen2.5:1.5b)

Test tay trên máy thật (Ollama thật, không phải mock) sau Ngày Thứ 4 phát hiện
3 lỗi dây chuyền: (1) câu chào xã giao bị đẩy thẳng vào tìm kiếm FTS5 thay vì
trả lời chào lại; (2) lịch sử hội thoại chỉ lọc `kind="procedure_card"`, BỎ SÓT
hoàn toàn `kind="answer"` (câu trả lời dài của LLM 2 Customer Care) khiến LLM1
bị "khoá cứng" vào thủ tục cũ; (3) hệ quả của (1)+(2) — chuyển chủ đề giữa
chừng không mượt. Kế hoạch fix qua 2 vòng review (xem lịch sử hội thoại) trước
khi code — 1 lỗ hổng UI cụ thể bị bắt bằng cách đọc thẳng `chat.js` trước khi
code (xem mục 3 dưới), không phải đoán.

**File sửa:**
- `system2/extractor.py` — thêm `intent_type` (enum `procedure`/`chitchat`/
  `out_of_scope`) vào `EXTRACT_S2_SCHEMA`, ép model TỰ phân loại ý định qua
  JSON schema-constrained (KHÔNG viết `is_chitchat()` bắt từ khoá — dễ vỡ với
  biến thể như "chào bạn" nếu check theo từng token). `extract()` fallback
  `intent_type` ngoài enum về `"procedure"` (fail open — coi như câu hỏi thủ
  tục thật, tối đa ra `not_in_sources` còn hơn âm thầm nuốt câu hỏi thật thành
  1 câu chào). `resolve()`: `intent_type != "procedure"` → bỏ qua
  `resolve_query()` hoàn toàn (0 query FTS5) nhưng giữ nguyên `extracted` để
  `pipeline.py` phân nhánh đúng.
- `system2/pipeline.py` — `run_turn_system2()` thêm 2 nhánh sớm
  `kind="chitchat"`/`kind="out_of_scope"` (cả 2 KHÔNG gán `choices`).
  `_history_for_extractor()` generalize từ chỉ lọc `kind="procedure_card"`
  sang lọc MỌI lượt `role="assistant"` qua hàm mới `_clean_assistant_text()` —
  mirror đúng logic đã kiểm chứng ở `app/prompts/templates.py::history_messages()`
  (System 1): bỏ dòng bullet/số thứ tự, cắt tiền tố rườm rà, giữ câu mở đầu
  sạch đầu tiên ≤140 ký tự (KHÔNG cắt thô `content[:120]` — nếu câu trả lời mở
  đầu bằng bullet, cắt thô vẫn để lọt tên thủ tục cũ). Câu hỏi người dùng
  trong lịch sử cũng giới hạn ≤250 ký tự.
- `system2/test_extractor.py`, `system2/test_pipeline.py` — thêm test cho cả
  3 thay đổi trên (chitchat/out_of_scope không chạm FTS5, fallback intent_type
  ngoài enum, lọc lịch sử `kind="answer"` giữ đúng câu mở đầu + fallback khi
  toàn bộ là bullet).

**1 lỗ hổng bắt được bằng cách đọc code thật trước khi code, KHÔNG có trong
plan gốc:** bản plan đầu tiên định gán `choices=["Tra cứu thủ tục hành
chính"]` cho `kind="out_of_scope"`. Đọc `app/static/js/chat.js::choiceBox()`
thì `useWebSearchSwitch` (quyết định label + hành vi bấm nút) CHỈ bật đúng khi
`meta.kind === "not_in_sources"` — gán `choices` cho `out_of_scope` sẽ hiện
nhầm label "Gợi ý tìm kiếm DuckDuckGo" và bấm vào chỉ gửi lại y hệt câu hỏi
trong CÙNG hội thoại System 2 (vòng lặp vô nghĩa, không chuyển System 1). Đối
chiếu thêm `app/core/orchestrator.py` (System 1) xác nhận `out_of_scope` từ
trước giờ CHƯA BAO GIỜ được gán `choices` (dòng loại trừ tường minh
`res.kind != "out_of_scope"`). Đã chốt: `out_of_scope`/`chitchat` đều KHÔNG
gán `choices`, đúng theo tiền lệ System 1 — không cần sửa `chat.js`.

**CHƯA kiểm tra được trong sandbox (không có Ollama thật)** — hành vi phân
loại `intent_type` thật của model 1.5B (đặc biệt case khó: "cảm ơn nhé, thế
còn lệ phí thì sao" phải VẪN là `procedure`, không phải `chitchat`) chỉ test
mock được phần wiring, phải chạy tay theo 3 kịch bản ở mục Verification Plan
của bản plan (chitchat / follow-up / chuyển chủ đề).

## Việc kế tiếp (Thứ 3–5)

- [x] `system2/service.py` — query FTS5 (bm25 ASC, có tự-test chống đảo
      chiều) + `province` fallback + phát hiện ambiguous + phát hiện
      low-confidence + render UI Table Card. Test bằng 70 thủ tục thật.
- [x] `system2/calibrate.py` — batch-test 56 câu thật, hiệu chỉnh 2 ngưỡng
      (xem `results_calibrate.md`), phát hiện + vá bug NFD/NFC.
- [x] `system2/extractor.py` — vai `extract_s2` (LLM1) trích
      `primary_keyword`/`province`/`facet`, nối vào `resolve_query()`. Test
      logic bằng mock (`test_extractor.py`) — CHƯA test model thật, cần chạy
      tay `--demo` trên máy có Ollama.
- [x] 4 tinh chỉnh theo PDF Plan cập nhật của Leader (22/09/2026):
      1. Bỏ auto-expiration banner trong `render_card()` — ETL (importer/
         crawler) chịu trách nhiệm xoá thủ tục hết hạn khỏi DB, card chỉ còn
         hiện `expiration_date` (nếu có) ở footer metadata để tham khảo.
      2. Thêm 3 cột `application_method`/`receiving_location`/`online_url`
         vào `schema.sql` (V3.1) + `importer.py` + `render_card()` — nhân
         tiện sửa luôn gap dữ liệu cũ #3/#4 cũ (authority bị lẫn địa chỉ
         phường, xem mục "3 cột mới" ở trên). **Đã re-seed `procedures.db`
         từ đầu** với schema mới, test lại `calibrate.py` (vẫn 56/56 Lượt B,
         không có gì suy giảm).
      3. `extractor.format_not_found()` + `resolve()["message"]` — câu báo
         lỗi debug chuẩn khi `found=False`/`confident=False`.
      4. MCQ 2 lượt — CHƯA làm, để dành bàn ở Thứ 4-5 lúc ghép Orchestrator
         (xem thảo luận: cơ chế `suggestion` hiện tại KHÔNG phải MCQ thật,
         chỉ là tín hiệu; System 1 đã có sẵn cơ chế MCQ qua
         `intent.generate_prompt_choices()`, cân nhắc tái dùng thay vì xây
         lại từ đầu).
- [ ] `crawler/` cào 15–20 thủ tục hộ tịch mẫu, đúng hợp đồng JSON (xem
      `crawler/README.md`) — cần trực tiếp xem cấu trúc trang dichvucong.gov.vn
      thật để viết selector, script khung đã có nhưng phần parse HTML cụ thể
      thì chưa (không tự bịa được nếu chưa xem trang thật). Ưu tiên cào đúng
      `authority` + `receiving_location` TÁCH BIỆT + `online_url` (3 cột mới).
- [ ] Sửa 3 khoảng trống dữ liệu cũ còn lại (proc_code / meta_source / files)
      cho ít nhất các thủ tục dùng để demo.
- [ ] Chạy `extractor.py --demo` với model thật trên bộ 56 câu, đo % khớp so
      với `topic` (nhãn đúng) — số liệu thật thay vì chỉ test-bằng-mock.
- [ ] Bàn phạm vi MCQ 2 lượt với Leader (chỉ case ambiguous, hay cả
      confident=False/out-of-scope?) trước khi thiết kế Orchestrator Thứ 4-5.
- [x] **Ngày Thứ 4 (23/09/2026)**: Frontend UI Toggle + Backend API Routing +
      LLM 2 Customer Care Agent — xem mục "Ngày Thứ 4" ở trên (file mới:
      `pipeline.py`, `customer_care.py` + test; 9 file sửa). Test mock LLM +
      render HTML Thẻ thật bằng Playwright — PASS hết trong sandbox.
- [x] **Chạy tay trên máy (Ollama thật)**: phát hiện 3 lỗi dây chuyền (chitchat
      bị đẩy vào FTS5, lịch sử bỏ sót `kind="answer"`, chuyển chủ đề không
      mượt) — xem mục "Ngày Thứ 5" ở trên để biết cách fix.
- [x] **Ngày Thứ 5 (23/09/2026)**: `intent_type` (chitchat/out_of_scope/
      procedure) qua JSON schema thay vì keyword-list; generalize lọc lịch sử
      sang mọi lượt trợ lý (mirror `templates.py::history_messages()`); né
      đúng 1 lỗ hổng UI `chat.js` bắt được bằng đọc code trước khi code. Test
      mock PASS hết trong sandbox (xem chi tiết ở trên).
- [ ] **Chạy tay lại trên máy (bắt buộc trước demo)**: verify 3 fix Ngày Thứ 5
      với Ollama thật theo đúng Verification Plan (câu chào "chào bạn", câu
      vừa cảm ơn vừa hỏi tiếp "cảm ơn nhé, lệ phí bao nhiêu" — case khó nhất,
      chuyển chủ đề khai sinh → vay vốn `LEGACY-PROC-0026` giữa hội thoại),
      rồi mới quay lại 6 kịch bản gốc mục 3.2 bản plan Ngày Thứ 4 (đặc biệt
      Kịch bản 6 Out-of-table Guard và Kịch bản 3 LLM 2 trích lệ phí/link
      online — chưa test model thật cho vai `customer_care_s2`).

# PHASE 2 — HỆ THỐNG 2: RETRIEVAL (CSDL thủ tục nội bộ)

**Ngày:** 2026-09-22 · **Nhánh:** V10.3 · **Trạng thái:** đã chạy, là hệ thống MẶC ĐỊNH
**Phạm vi:** nối kiến trúc trong Proposal vào CSDL mà Phase 1 đã dựng (1.407 thủ tục).

> ⚠️ **ĐÃ CŨ MỘT PHẦN — bản hiện tại là V10.5**, xem
> [`PLAN_SYSTEM2_REBUILD.md`](PLAN_SYSTEM2_REBUILD.md). Tài liệu này giữ nguyên
> làm hồ sơ thiết kế V10.3; các số đo ở đây vẫn là lý do của nhiều quyết định.
> Những chỗ **không còn đúng** ở V10.5:
>
> | Mục ở đây | V10.5 |
> |---|---|
> | CSDL 1.407 thủ tục theo lĩnh vực | **1.350 thủ tục cấp Xã/Phường** (level=COMMUNE + H29 TP.HCM) |
> | §1 LLM 1 rút khoá cho MỌI câu hỏi | **Tra từ khoá trước**; LLM 1 chỉ khi từ khoá không khớp chắc |
> | §1 mọi tin nhắn đều đem đi tra | Tin nhắn thường = **LLM 2 trò chuyện** (nhãn "⚠️ AI tự trả lời"); tra CSDL bằng nút **🎯 Tìm chính xác** |
> | §1 MCQ "thủ tục nào" + "nộp cấp nào" | MCQ **"thủ tục chính" → "dạng cụ thể"**; đã bỏ MCQ "nộp cấp nào" |
> | Q1 `province` NULL 100% | `province` = tỉnh **công bố** (614 bản của UBND tỉnh) |
> | Q5 nhớ trục `agency_level` | Trục đó không còn được hỏi (vẫn còn trong `MEMORABLE_AXES`) |
> | §4.6 bộ gác `newProcedure` đuổi sang ô chat mới | Chỉ **cảnh báo gắn sau** câu trả lời, không chặn |
> | §5 ô trống ghi "cổng không công bố" | Ô trống mở đầu bằng **"Chưa có thông tin…"**, không suy ra "miễn phí" |

> Phase 1 (ETL + CSDL) nằm ở `Database/PHASE1_PLAN.md` — **tệp đó do phiên khác sở hữu,
> đừng sửa.** Tài liệu này chỉ nói về Phase 2: phần tra cứu và giao diện.

---

## 1. Luồng một lượt hỏi

```
[ Người dân hỏi ]  "t người bình định muốn dk kết hôn"
      │
      ▼
[ LLM 1 — rút khoá ]   core/system_retrieval.extract_keys()
      │   {"primary_keyword": "đăng ký kết hôn", "domain": "Hộ tịch",
      │    "entities": ["Bình Định"]}
      │   `domain` PHẢI chọn trong 103 lĩnh vực có thật của cổng
      ▼
[ Tra CSDL — KHÔNG qua LLM ]   Database/pipeline/retrieval.search_in_domain()
      │   FTS5 ba tầng, mỗi kết quả kèm confident / match_tier / term_overlap
      │
      ├─ không ra gì        → LLM 1 nghĩ lại khoá (tối đa 3 lượt) → xin lỗi
      ├─ ra nhưng KHÔNG chắc → hỏi MCQ + kèm "Không có cái nào đúng ý tôi"
      ├─ nhiều ứng viên      → hỏi MCQ "thủ tục nào?"
      └─ còn phân nhánh      → hỏi MCQ "trường hợp nào / bạn là ai / nộp cấp nào"
      ▼
[ Dựng bảng bằng CODE ]   core/procedure_table.build()      ← zero hallucination
      ▼
[ LLM 2 — chăm sóc khách hàng ]   core/system_retrieval.follow_up()
          chỉ trả lời trong phạm vi bảng · gác `newProcedure` → mời ô chat mới
```

Bốn mốc bàn giao của bản khung cũ **giữ nguyên tên hàm**: `extract_keys()`,
`lookup()`, `build_table()`, `follow_up()`.

---

## 2. Tệp nào làm gì

| Tệp | Vai trò |
|---|---|
| `Database/pipeline/retrieval.py` | **Cửa duy nhất** Backend dùng để đọc CSDL. Backend không viết SQL. |
| `Backend/core/system_retrieval.py` | Điều phối một lượt: LLM 1 → tra → MCQ → bảng → LLM 2. |
| `Backend/core/procedure_table.py` | Bản ghi → bảng hiển thị. **Không có LLM trong tệp này.** |
| `Backend/prompts/retrieval_templates.py` | Prompt của LLM 1 và LLM 2 (tách khỏi Hệ thống 1). |
| `Backend/api/procedure_routes.py` | Tải biểu mẫu `.docx` + API trí nhớ MCQ. |
| `Frontend/static/js/procedure.js` | Vẽ bảng / MCQ / lời mời ô chat mới. |
| app.db: `retrieval_pending`, `user_mcq_memory` | Trạng thái giữa các lượt. |

---

## 3. Các quyết định đã chốt (và vì sao)

### Q1. Không lọc theo tỉnh — dùng trục "cấp nộp hồ sơ" thay thế
`procedures.province` **NULL ở cả 1.407 bản ghi**: Phase 1 cố ý không đoán tỉnh
("thà thiếu còn hơn bịa"). Nên ví dụ *"người Bình Định"* trong Proposal **không
lọc được gì**. Thay vào đó:
- `entities` (kể cả tên tỉnh) chỉ **cộng điểm xếp hạng**, không loại bỏ ứng viên —
  vì "có yếu tố nước ngoài", "lưu động" thì nằm ngay trong TÊN thủ tục và dùng được.
- Trục địa phương duy nhất có dữ liệu thật là `agency_levels`
  (Tỉnh 859 · Xã/Phường 405 · Bộ 344 · Ngành dọc 137) → thành một MCQ.
- Bảng luôn ghi rõ **"thủ tục cấp trung ương, áp dụng chung toàn quốc"** để
  người dân không tưởng là đã lọc theo tỉnh của họ.

### Q2. Gọi thẳng, không qua MCP (nhưng vẫn bọc được sau)
Proposal vẽ CSDL là một MCP target. Yêu cầu chốt lại: *"MCP should help, not slow
down"*. `retrieval.py` là một façade thuần hàm, nên bọc nó thành MCP server sau
này chỉ là vài chục dòng, mà giờ thì không tốn một vòng IPC nào cho mỗi lượt hỏi.

### Q3. 5 lĩnh vực trong Proposal là việc của SCRAPER
Danh sách "Văn hóa – Xã hội / Hộ tịch / Giáo dục / Chứng thực…" là để biết
**cào thêm gì**, không phải để Hệ thống 2 ánh xạ. Tầng tra cứu dùng đúng 103 tên
lĩnh vực THẬT của cổng, lấy động từ CSDL (`_domains()`), không hardcode.

### Q4. Trạng thái MCQ nằm ở app.db, không nằm trong RAM
Bảng `retrieval_pending`, khoá chính là `conversation_id`. Khởi động lại máy chủ
giữa chừng không làm mất câu hỏi của người dân.

### Q5. Chỉ nhớ trục MÔ TẢ NGƯỜI DÙNG
`user_mcq_memory` chỉ nhận `subject` (bạn là ai) và `agency_level` (nộp cấp nào) —
xem `retrieval.MEMORABLE_AXES`, và API `POST /api/mcq-memory` từ chối trục khác.

> **Vì sao không nhớ "thủ tục nào" và "trường hợp nào":** hai trục đó mô tả CÂU HỎI,
> không mô tả NGƯỜI. Nhớ "lần trước bạn chọn Đăng ký kết hôn" rồi áp cho câu hỏi
> sau là **trả lời sai thủ tục** — đúng kiểu lỗi mà cả Hệ thống 2 sinh ra để tránh.

Người dùng thấy rõ trí nhớ đang hoạt động (dòng "🧠 Đã dùng lựa chọn bạn nhờ nhớ")
và có nút **Quên đi** ngay tại đó. Số lần mỗi trí nhớ đỡ được một câu hỏi nằm ở
`user_mcq_memory.n_used` — để sau này đo xem tính năng này có thật sự hữu ích không.

### Q6. Dữ liệu không vào git — máy mới tự cào
`Database/raw/` (774 thư mục `.docx`) và `procedures.db` đều bị `.gitignore` chặn.
`Setup First Time.bat` → `setup.ps1` bước 7 tự chạy `run_pipeline --all` khi máy
chưa có CSDL (~15–25 phút, 2 req/s). Cào hỏng **không** làm hỏng cả buổi cài đặt:
Hệ thống 1 vẫn chạy, Hệ thống 2 báo thiếu CSDL và mời bấm Web search.
Bỏ qua bằng `-SkipScrape`.

### Q7. Không có ngày hết hạn — và nói thẳng như vậy
Cổng Dịch vụ công **không công bố ngày hết hiệu lực**. Bảng hiện số + ngày quyết
định, rồi ghi rõ một dòng: *"Cổng không công bố ngày hết hiệu lực của thủ tục."*
Khi một thủ tục biến mất khỏi danh mục (`status='expired'`), bảng hiện cảnh báo
kèm **ngày mình phát hiện nó biến mất**, không phải ngày luật hết hạn — và vẫn
hiện thông tin cũ. **Không tự động chuyển hệ thống:** bấm Web search luôn là lựa
chọn của người dùng.

---

## 4. Ba chỗ dữ liệu thật khác với Proposal (đã xử lý, cần biết)

### 4.1. "Checklist việc cần làm" không có sẵn thành dòng
Chỉ 476/2.029 `procedure_steps` có `name`; phần còn lại là một khối văn bản.
`derive_steps()` tách lúc đọc theo ba kiểu đánh dấu mà cổng dùng lẫn lộn:
`Bước 1:` · `a) b)` · gạch đầu dòng.

| | trước | sau |
|---|---|---|
| thủ tục chỉ ra **1 mục** (không tách được) | 798 | **230** |

194 thủ tục còn lại là một khối dài thật sự — hiện thành một ô tick duy nhất.

### 4.2. `procedure_cases` trộn hai thứ khác hẳn nhau
Trong 939 case có tên, cổng để lẫn:
- **nhánh thật** — "(1) Đối với công trình theo tuyến", "Trường hợp ủy quyền…"
- **tiêu đề mục** — `* Giấy tờ phải nộp:`, `* Giấy tờ phải xuất trình:`, `* Lưu ý:`

Đem loại sau ra hỏi *"Bạn thuộc trường hợp nào? → * Giấy tờ phải nộp:"* là hỏi vô
nghĩa, và lọc hồ sơ theo nó thì **giấu mất nửa số giấy tờ**. `_is_real_case()` loại
chúng ra; còn **202/1.407** thủ tục có MCQ "trường hợp" thật sự dùng được.

### 4.3. Không ngưỡng nào tách được câu hỏi thật khỏi câu hỏi rác
Đo thật trên FTS5:

| câu hỏi | tier | overlap | thực chất |
|---|---|---|---|
| `thẻ căn cước cho trẻ em` | 3 | 0.67 | **thật** |
| `đăng ký bay lên sao Hỏa` | 3 | 0.67 | **rác** |

Giống hệt nhau về mọi chỉ số máy đo được. Nên **không giả vờ tách được**: khi
không ứng viên nào đạt `confident`, hệ thống hỏi MCQ kèm lựa chọn
**"Không có thủ tục nào đúng ý tôi"** → bấm vào là ra thẳng câu xin lỗi (có nêu
khoá AI đã tìm + câu hỏi gốc). Thà tốn một cú bấm còn hơn trả nhầm thủ tục.

Trước khi làm phiền người dùng, LLM 1 được nghĩ lại khoá tối đa 3 lượt —
sinh lại một lần rẻ hơn nhiều so với hỏi người dân một lần.

### 4.4. `domain` của LLM 1 chỉ được XẾP HẠNG, không được LỌC
Thử với mô hình thật (Qwen2.5 1.5B) chứ không phải giả lập:

```
"t muốn dk kết hôn"
   -> primary_keyword = "đăng ký kết hôn"   ✅ ĐÚNG
      domain          = "Đất đai"            ❌ SAI
```

Bản đầu lọc cứng theo `domain`, nên từ khoá chuẩn mà **toàn bộ thủ tục Hộ tịch
bị vứt hết**, người dân nhận về "đăng ký biến động quyền sử dụng đất". Đo tiếp
trên 6 câu hỏi: mô hình chọn sai lĩnh vực 3/6 lần (hay tụt về "Đất đai").

Chốt: **rút từ khoá thì mô hình 1.5B làm tốt, chọn 1 trong 103 lĩnh vực thì
không.** Cho `domain` cộng điểm, không cho nó quyền loại bỏ. Xếp theo
`match_tier` → `term_overlap` → lĩnh vực → bm25. Đây cũng là mục fine-tune số 1
trong Proposal, và là chỗ đáng fine-tune nhất.

### 4.5. Siết `term_overlap`: khớp theo ÂM TIẾT, không theo chuỗi con
`search._overlap()` của Phase 1 so khớp bằng chuỗi con (`t in hay`) nên âm tiết
ngắn lọt vào âm tiết dài:

```
hỏi "đăng ký thường trú"
  "(Hà Nội) Đăng ký, cấp Giấy chứng nhận đối với TRƯỜNG hợp…"
   -> "tru" khớp vì nằm trong "truong" -> overlap 0.75 -> confident ✅ SAI
```

Một kết quả sai mà `confident=True` **nguy hơn hẳn việc không tìm thấy**: nó đi
thẳng ra bảng, bỏ qua cả vòng hỏi lại lẫn lối thoát "không cái nào đúng".

`retrieval.refine()` tính lại theo từng âm tiết trọn vẹn rồi xếp lại theo
(tầng, độ khớp, bm25) — `search.py` xếp thuần bm25 nên bản khớp 4/4 âm tiết có
thể bị đẩy xuống dưới bản khớp 3/4. **Không sửa `search.py`** (mã Phase 1 của
phiên khác); siết ở tầng façade.

Kết quả sau khi siết, cùng câu hỏi "đăng ký thường trú":

| | trước | sau |
|---|---|---|
| đứng đầu | (Hà Nội) Đăng ký, cấp Giấy chứng nhận… (sai, `confident`) | Liên thông điện tử: … xóa đăng ký thường trú (đúng nhất trong kho) |

> **Lưu ý về độ phủ:** kho hiện **không có** thủ tục "Đăng ký thường trú"
> (lĩnh vực Cư trú: 0 thủ tục). Đây là khoảng trống DỮ LIỆU, không phải lỗi tra
> cứu — cần cào thêm Bộ Công an. Hiện hệ thống trả kết quả gần nhất và không
> vờ chắc chắn.

---

### 4.6. Bộ gác `newProcedure`: đã thử LLM, đo được 0%, đã bỏ
Proposal đề xuất *"hỏi con LLM nhận diện newProcedure"*. Đã làm đúng như vậy, rồi đo:

| câu hỏi (đang xem *Thủ tục đăng ký kết hôn*) | Qwen2.5 1.5B trả |
|---|---|
| "lệ phí bao nhiêu tiền?" | `is_new_procedure = true` ❌ |
| "cần mang giấy tờ gì?" | `true` ❌ |
| "cảm ơn bạn" | `true` ❌ |
| "thế còn làm hộ chiếu thì sao?" | `true` ✅ |

**9/9 câu đều `true` — phân biệt 0%.** Dùng nó thì mọi câu hỏi tiếp đều bị đá
sang ô chat mới và **LLM 2 không bao giờ được chạy**.

Thay bằng luật dựa trên chính CSDL (`retrieval.is_other_procedure()`), không cần
mô hình. Hai bước:
1. Bỏ từ đệm ("tôi", "muốn", "thì sao"…). Nếu phần còn lại **toàn từ chỉ một ô
   trong bảng** ("lệ phí", "giấy tờ", "bao lâu") → đang hỏi tiếp, khỏi tra.
2. Còn lại thì tra CSDL: khớp **chắc chắn** vào một `proc_id` **khác** → thủ tục mới.

| | LLM 1.5B | luật theo CSDL |
|---|---|---|
| hỏi tiếp (phải giữ nguyên ô chat) | 0/9 | **9/9** |
| thủ tục mới (phải mời ô chat mới) | 4/4 | **4/4** |
| tổng | 4/13 | **13/13** |

Nhanh hơn (không gọi mô hình), xác định được, và gỡ lỗi được. Khi nào fine-tune
xong (Proposal, fine-tune mục 3) thì **đo lại** rồi hẵng cân nhắc đưa LLM trở lại.

---

## 5. Nói thật về chỗ thiếu

Mỗi ô của bảng mang theo `status` lấy từ cột `status_*` của Phase 1:

| status | nghĩa | bảng hiện gì |
|---|---|---|
| `present` | cổng có công bố | dữ liệu |
| `absent` | cổng **không** công bố | câu giải thích riêng cho từng ô |
| `unknown` | chưa cào được | "chưa tra được thông tin này" |

**Tuyệt đối không để ô trống không kèm lý do**: người dân đọc ô trống thành
"miễn phí" hoặc "không cần giấy tờ gì" — sai nguy hiểm hơn thiếu.

Độ phủ thật (1.407 thủ tục): thành phần hồ sơ 1.380 · thời gian 1.389 ·
căn cứ pháp lý 1.361 · lệ phí 923 · trực tuyến 945 · biểu mẫu 774 ·
**địa điểm tiếp nhận chỉ 352** (ô này thường trống, và luôn kèm lời giải thích).

---

## 6. Cách thử

```bash
# Dựng CSDL (máy mới)
python -m Database.pipeline.run_pipeline --all

# Thử tra cứu ở tầng CSDL
python -m Database.pipeline.search "dang ky ket hon"

# Chạy web (Hệ thống 2 là mặc định)
python Backend/main.py
```

Bốn đường cần thử tay trên giao diện:
1. **hỏi rõ ràng** "đăng ký kết hôn" → MCQ chọn thủ tục → ra bảng
2. **hỏi mơ hồ** → MCQ kèm "Không có thủ tục nào đúng ý tôi" → câu xin lỗi
3. **tick ô "nhớ lựa chọn"** ở MCQ "bạn là ai" → hỏi câu khác, xem có bị hỏi lại không
4. **đang xem bảng rồi hỏi thủ tục khác** → phải hiện lời mời mở ô chat mới

---

## 7. Còn lại cho tuần sau

- **Fine-tune LLM 1** để `primary_keyword` và `domain` chuẩn hơn (Proposal §fine-tune
  mục 1) — đây là chỗ ảnh hưởng lớn nhất tới tỉ lệ ra đúng thủ tục ngay lượt đầu.
- **Ragas** cho Hệ thống 2: `Evaluation/evaluate.py` hiện đo Hệ thống 1. Chỉ số đáng
  đo ở đây là **top-1 đúng proc_id** và **số vòng MCQ tới khi ra bảng**.
- **Hồ sơ người dùng gắn tài khoản** (slide 9): `user_mcq_memory` đã là mảnh đầu
  tiên và nâng cấp được — thêm trục mới chỉ là thêm một dòng vào `MEMORABLE_AXES`.
- **Cào thêm** các lĩnh vực trong Proposal còn mỏng.

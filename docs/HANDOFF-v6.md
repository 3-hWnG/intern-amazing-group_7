# BÀN GIAO — phiên làm việc v6 (14/09/2026)

> **Đọc file này thay vì đọc lại cả cuộc trò chuyện.** Viết cho phiên Claude
> sau, và cho thành viên Nhóm 7 tiếp nhận. Mọi thứ cần biết để làm tiếp nằm ở
> đây; chi tiết kỹ thuật từng phần ở `docs/AGENT.md`.

---

## 1. Phiên này đã làm gì (một đoạn)

Thay **bộ điều phối** của hệ thống tra cứu thủ tục hành chính: từ router cứng
A/B/C/D (`core/pipeline.py`) sang **vòng lặp agent** để mô hình tự chọn công cụ
(`core/agent.py`). Tầng truy hồi **không bị đụng một dòng nào** — R@1 0.856 giữ
nguyên. Thêm tệp đính kèm, chẩn đoán tra web, bảng nhà phát triển, và bộ đo độ
chính xác chọn công cụ. Bốn vòng sửa lỗi sau khi chạy thật: v6 → v6.1 → v6.2 →
v6.3.

**Người dùng:** Trịnh Hoàng Nhân (Arkain), thực tập sinh AI, Nhóm 7.
Đây là nhánh **song song** — được phép bỏ kiến trúc cũ nếu nó cản đường, miễn
là nói trước.

---

## 2. Mô hình tư duy — hiểu cái này là hiểu hết

Câu một dòng: **dataset là CÔNG CỤ, không phải cái cũi.**

```
câu hỏi
  ├─ xã giao?            -> trả lời ngắn, không tra gì, không gọi LLM
  ├─ người dùng bảo tra web? -> tra web thẳng, bỏ qua bước chọn công cụ
  ├─ MÔ HÌNH TỰ CHỌN công cụ (tối đa 2 vòng)
  │     search_procedures | get_procedure | search_attachments
  │     | search_web | none
  ├─ ngữ cảnh dính: câu hỏi tiếp nối -> quay lại thủ tục đang nói tới
  ├─ sàn tin cậy: bằng chứng < 0.45 -> BỎ HẲN
  └─ sinh câu trả lời -> kiểm chứng bằng luật -> sinh lại -> bỏ cuộc về bản ghi
```

Hai điều **không** được phá khi sửa tiếp:

1. Không nhánh nào **ép** mô hình phải tra bảng (trừ đúng một guardrail có cờ tắt).
2. Không nhánh nào **cấm** mô hình dùng hiểu biết chung.

Đó chính là hai lỗi của bản cũ mà cả phiên này sinh ra để sửa.

---

## 3. Bản đồ file

### Viết mới trong phiên này
| File | Việc |
|---|---|
| `app/core/agent.py` | Vòng lặp chọn công cụ. CHỈ điều phối, không chứa logic nghiệp vụ |
| `app/core/tools.py` | 4 công cụ — vỏ mỏng bọc code đã có và đã đo |
| `app/core/resources.py` | Sổ đăng ký tài liệu (global + theo hội thoại) + manifest |
| `app/core/parsers.py` | csv/tsv/xlsx/txt/md/json/pdf/docx -> chunk |
| `app/core/chunk_index.py` | Truy hồi trong tệp đính kèm (cùng công thức với KB) |
| `app/developer_mode.py` | Ghi vết, chẩn đoán tra web, ảnh chụp cấu hình |
| `app/prompts/agent_templates.py` | Prompt quyết định + prompt trả lời + `wants_exact()` |
| `app/api/file_routes.py` | Tải lên / liệt kê / xoá tệp đính kèm |
| `app/static/js/files.js` | Giao diện đính kèm |
| `Evaluation/evaluate_routing.py` | Đo độ chính xác chọn công cụ trên 862 câu |
| `docs/AGENT.md` | Tài liệu kỹ thuật đầy đủ (v6 → v6.3) |

### Sửa
`config.py` (bốn khối mới ở cuối) · `api/chat_routes.py` (gọi agent, phát lại
theo mẩu, header bỏ dấu) · `api/routes.py` (`render_page` + `/api/config`) ·
`api/dev_routes.py` (6 endpoint dev) · `api/schemas.py` (`force_web`,
`DevToggle`, `WebSearchTest`) · `core/llm.py` (`complete_json`, `chat_tools`) ·
`core/websearch.py` (viết lại: nhật ký chẩn đoán, backend, URL đầy đủ) ·
`core/formatter.py` (footer gọn) · `db/schema.sql` + `db/repositories.py`
(`documents`, `document_chunks`) · `main.py` (đăng ký KB global) · toàn bộ
frontend · `run.ps1` (`-Routing`, sửa đường dẫn) · `requirements.txt`.

### KHÔNG đụng — đừng sửa nếu không có lý do đo được
`retrieval.py` · `lexical.py` · `reranker.py` · `vectorstore.py` ·
`embeddings.py` · `domain/records.py` · `domain/text.py` · `factcheck.py` ·
`queue.py` · `auth.py` · `summarizer.py` · toàn bộ `Evaluation/baselines/`.

`core/pipeline.py` (luồng tiers cũ) **vẫn chạy được**: đặt
`ORCHESTRATOR = "tiers"` để so sánh A/B. Đừng xoá.

---

## 4. Lịch sử hội thoại — ba lớp

Người dùng hỏi thẳng câu này; ghi lại cho rõ:

1. **Lưu đầy đủ** — bảng `messages` (role, content, tier, confidence, sources,
   factcheck, token_estimate). Footer (nhãn tầng + dòng miễn trừ) **cố ý KHÔNG
   lưu**: nếu lưu, nó lọt vào lịch sử và mô hình chép lại nguyên văn bản ghi cũ
   — đã từng gây lỗi bịa "Thủ tục tạm trú" bằng nội dung thủ tục nhận cha mẹ con.
2. **Đưa vào prompt có giới hạn** — `summarizer.build_context()` trả về
   (tóm tắt, các lượt gần nhất). Vượt `CONTEXT_TOKEN_BUDGET = 1800` thì gọi LLM
   tóm tắt phần cũ và **ghi vào CSDL** (`conversations.summary`, `summary_upto`)
   để chỉ tóm tắt một lần. `as_history()` biến thành các lượt role/content thật;
   tóm tắt chèn vào như một lượt user `[Tóm tắt cuộc trò chuyện trước đó]`.
   Bước **chọn công cụ** chỉ nhận bản rút gọn: 4 lượt cuối, cắt 180 ký tự.
3. **Con trỏ có cấu trúc** — `conversations.last_row_id` ghi thủ tục đang nói
   tới. **Đây mới là thứ thực sự sửa được câu hỏi tiếp nối**, không phải lịch sử
   thô: mô hình 1.5B đọc lịch sử vẫn quên, nhưng `get_procedure(last_row_id)`
   thì không thể quên.

`core/session.py` (bộ nhớ RAM cũ) **không còn nằm trên đường chạy**.

---

## 5. Công tắc quan trọng (`config.py`)

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `ORCHESTRATOR` | `"agent"` | `"tiers"` = quay về luồng v5 để so sánh |
| `AGENT_TOOL_MODE` | `"json"` | `"native"` khi cắm mô hình ≥3B |
| `AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL` | `True` | **GUARDRAIL DUY NHẤT. Tắt khi cắm mô hình lớn** |
| `ANSWER_STYLE` | `"llm"` | `"template"` = in nguyên bản ghi (an toàn, xấu) |
| `EXACT_ON_FACET` | `True` | Trích nguyên văn khi hỏi vào một trường |
| `FOLLOWUP_STICKY` | `True` | Ngữ cảnh dính |
| `EVIDENCE_MIN_CONFIDENCE` | `0.45` | Dưới mức này bỏ hẳn bằng chứng |
| `TIER_A/B_MIN_CONFIDENCE` | `0.75 / 0.65` | Đổi công thức tin cậy **phải** hiệu chỉnh lại |
| `EVIDENCE_TIE_GAP` | `0.06` | Chỉ đưa ứng viên sát điểm vào prompt |
| `WEB_SEARCH_QUERY_HINT` | `"site:gov.vn"` | Bám nguồn ngay từ truy vấn |
| `STATIC_VERSION` | `"6.3"` | **Sửa JS/CSS phải bump** |
| `DEV_TOOLS_ENABLED` | `True` | **Đặt False trước khi bàn giao** |

---

## 6. Số đo

| Chỉ số | Giá trị | Ghi chú |
|---|---|---|
| R@1 truy hồi | **0.856** | v4, KHÔNG đổi — tầng truy hồi không bị đụng |
| Chọn công cụ | **88.75%** (765/862) | qwen2.5:1.5b, 197 ms/câu |
| Guardrail can thiệp | **411/862 = 47.7%** | |
| Ước tính nếu tắt guardrail | **~43%** | |

**Kết luận quan trọng nhất của cả phiên:** qwen2.5:1.5b tự chọn đúng công cụ chỉ
~43% số lần. Gần một nửa định tuyến đang do **một cái regex khớp từ khoá** gánh.
Kiến trúc đúng, mô hình chưa đủ sức lái.

Theo nhóm: `xa_giao` 100% (regex) · `in_scope` 90.7% · `muc_phat` 62.5% ·
`mo_ho` 16.7% · `ngoai_dataset` 0% (guardrail ép tra bảng — cái giá phải trả).

**Việc tiếp theo rõ ràng nhất:** cắm 3B/7B quantized, đặt
`AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL = False`, chạy
`.\run.ps1 -Routing -Save v7_<tên>`. Giữ được ~88% mà không cần guardrail thì
kiến trúc này đã sẵn sàng.

---

## 7. Lỗi đã sửa + nguyên nhân gốc (đừng lặp lại)

| Lỗi | Nguyên nhân gốc | Bài học |
|---|---|---|
| Nút đính kèm chết, ô nhập bẹp | **Cache trình duyệt** giữ `app.js`/`styles.css` cũ. Log server chỉ có 1 request `files.js` | Nhìn **log request**, không nhìn code. Sửa JS/CSS -> bump `STATIC_VERSION` |
| `pip install` xong vẫn thiếu thư viện | Cài vào Python **toàn cục**, app chạy `.venv` | Luôn `.venv\Scripts\python.exe -m pip` |
| Eval gõ xong không in gì | PowerShell chạy `.py` bằng Python toàn cục | Script nay tự phát hiện và in câu lệnh đúng |
| `run.ps1 -Eval` sai đường dẫn | `$Root\..\..\Evaluation` trỏ **ra ngoài** project | Đã sửa + thêm `-Routing` |
| 500 giữa lúc stream | Header HTTP chỉ mã hoá latin-1, tóm tắt kiểm chứng có dấu tiếng Việt | `_ascii()` bỏ dấu mọi giá trị header; thân câu trả lời giữ nguyên dấu |
| Trả lời gộp 3 thủ tục thành 10 gạch đầu dòng | Luôn nhét 3 thủ tục vào prompt | Chỉ đưa ứng viên **sát điểm** (`EVIDENCE_TIE_GAP`) |
| "Nộp ở đâu" -> "Cục Cảnh sát giao thông" | Truy hồi **lại từ đầu** bằng 3 chữ đó, ra 0.43, ghi đè chủ đề | Ngữ cảnh dính |
| Khớp 0.20 mà dán nhãn xanh "Từ cơ sở dữ liệu" | `_tier_for()` gán `procedures -> Tier.A` **không nhìn độ tin cậy** | Nhãn nói dối là lỗi nặng nhất. Sàn + nhãn trung thực |
| "145 USD" cho thủ tục 7.000đ | Web trả về **thẻ tạm trú cho người nước ngoài** (thật sự tính USD) | Bám `site:gov.vn`, neo số liệu vào bản ghi nội bộ, ghi `[Nguồn: host]` vào từng đoạn |
| Tra web "không có kết quả" mơ hồ | Gộp 4 kiểu hỏng khác nhau làm một | Phân biệt: thiếu thư viện / thư viện lỗi / **bị allowlist chặn** / rỗng |

---

## 8. Bẫy môi trường (máy Windows của Arkain)

- **`.venv` là Windows.** Claude chạy trên VM Linux qua cầu nối -> **không chạy
  được** `.venv` đó. Chỉ kiểm tra được bằng `ast.parse`, `node --check`, và test
  logic thuần với `sys.modules` giả lập (`pandas`, `ollama`). Cách này đã bắt
  được nhiều lỗi thật — dùng tiếp.
- **Cầu nối KHÔNG xoá được file** ("Operation not permitted"). Muốn xoá thì
  `device_request_delete_permission`, hoặc `mv` vào `_to_delete/` rồi báo người
  dùng.
- **ĐỪNG chạy lệnh git ghi vào index qua cầu nối.** `git status` để lại
  `.git/index.lock` rỗng không xoá được, chặn mọi `git add`/`commit` của người
  dùng. Đã xảy ra một lần. Chỉ dùng `git --no-optional-locks`.
- **CRLF:** working tree là CRLF, index là LF -> git báo 70 file "đã sửa" trong
  khi thật sự chỉ 24. `git config core.autocrlf true` là hết.
- Từ vựng hành chính trùng tiếng đệm sau khi bỏ dấu: `thu`=thủ, `ho`=hồ/hộ,
  `lam`=làm, `ban`=bản/bạn. **Không** đưa bốn tiếng đó vào danh sách loại bỏ từ.

---

## 9. Chạy & đo

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt   # có pypdf, python-docx, ddgs
.venv\Scripts\python.exe app\main.py                          # http://localhost:8000
.\run.ps1 -Routing -Limit 100                                 # đo chọn công cụ
.\run.ps1 -Routing -Save v7_qwen3b                            # lưu mốc
.\run.ps1 -Eval                                               # R@1, phải y hệt v4
```

Bảng Dev: nút **⚙** -> ghi vết từng lượt, chẩn đoán tra web, 25 công tắc, reset.

---

## 10. Còn lại

- [ ] Cắm 3B/7B quantized + tắt guardrail + đo lại (**việc số 1**)
- [ ] Chưa ai đo `search_attachments` bằng số — chưa có bộ eval cho tệp đính kèm
- [ ] `search_attachments` chưa dùng reranker (KB thì có)
- [ ] PDF scan chưa OCR — báo lỗi rõ ràng thay vì đánh chỉ mục rỗng
- [ ] Dọn dataset: thiếu `mã thủ tục`, `cấp thực hiện`; còn 4 cặp dòng trùng
      (8/21, 10/13, 9/14, 23/25)
- [ ] Hộ tịch R@1 0.667 — nhóm thủ tục dân hỏi nhiều nhất mà yếu nhất
- [ ] `DEV_TOOLS_ENABLED = False` trước khi bàn giao bản cuối
- [ ] `data/dataset.xlsx` chứa email thật của 9 người đóng góp — chỉ an toàn khi
      repo còn **riêng tư**

---

## 11. Cách làm việc với Arkain

- Trình bày **kết luận trước**, dẫn chứng sau. Ghét câu chữ vòng vo.
- **Luôn kèm sơ đồ luồng** khi giải thích quy trình.
- Nói thẳng khi lỗi là **của mình** — đã có vài lần trong phiên này.
- Duyệt kế hoạch trước khi viết code cho việc lớn; việc đã duyệt thì làm **một
  lèo**, không cần hỏi lại từng bước. Anh ấy tự chạy và tự đánh giá sản phẩm.
- Đừng phóng đại thời gian — anh ấy nhận xét Claude hay ước lượng quá tay.
- Repo: `https://github.com/3-hWnG/intern-amazing-group_7`, nhánh `revamp`.

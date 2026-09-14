# v6 — Bảng thủ tục là CÔNG CỤ, không phải cái cũi

**14/09/2026.** Thay bộ điều phối. Không đụng tầng truy hồi.

---

## Hai lỗi đang sửa

**1. Không nạp lịch sử nên nó quên.**
Tầng A cũ in thẳng bản ghi, không qua LLM, không thấy lịch sử hội thoại. Hỏi
tiếp "lệ phí bao nhiêu?" thì hệ thống phải *đoán* xem đang nói về thủ tục nào
bằng cách ghép chuỗi tên thủ tục cũ vào câu hỏi (`context_hint`). Mẹo đó từng
biến câu "tạm biệt" thành một lần tra thủ tục với độ tin cậy 0.92.

**2. Bị phân loại là "luật" thì suy nghĩ bị giam trong file.**
`pipeline.build()` quyết định thay mô hình: router bẻ sang luồng LUAT là bắt
buộc tra bảng, và prompt ghi "CHỈ dùng thông tin trong phần TÀI LIỆU". Hỏi một
câu phổ thông mà lỡ rơi vào nhánh đó thì mô hình cũng phải xin lỗi rằng dataset
không có.

Cả hai đều là lỗi **điều phối**, không phải lỗi truy hồi. Truy hồi đang tốt:
R@1 0.856 / MRR@10 0.906 trên 862 câu. Nên giữ nguyên toàn bộ, thay cái nằm
bên trên nó.

---

## Luồng mới

```
câu hỏi
  │
  ├─ xã giao? ──yes──► trả lời ngắn, KHÔNG tra gì, không gọi LLM
  │
  ├─ MÔ HÌNH TỰ CHỌN công cụ  (tối đa AGENT_MAX_STEPS = 2 vòng)
  │     đưa cho nó: manifest tài liệu (MÔ TẢ, không phải nội dung)
  │                 + vài lượt hội thoại gần nhất
  │                 + thủ tục đang nói tới kèm row_id
  │     nó chọn:  search_procedures │ get_procedure │ search_attachments
  │               │ search_web      │ none
  │
  ├─ bằng chứng thu được (có thể rỗng — và rỗng là HỢP LỆ)
  │     kèm luôn độ khớp: "(độ khớp thấp: 0.31 — có thể KHÔNG phải thủ tục
  │     người dân đang hỏi)" -> mô hình tự dè dặt thay vì bị ngưỡng cứng chặn
  │
  ├─ sinh câu trả lời
  │     có bản ghi ──► sinh xong ──► kiểm chứng bằng luật ──► sinh lại 1 lần
  │                                        │                      │
  │                                     đạt│                      │vẫn sai
  │                                        ▼                      ▼
  │                                  phát cho người dùng   in bản ghi gốc
  │     không có bản ghi ──► stream thẳng
  │
  └─ nhãn nguồn bằng chứng + 👍/👎
```

Câu quan trọng nhất của cả bản này: **không nhánh nào ép mô hình phải tra bảng,
và không nhánh nào cấm nó dùng hiểu biết chung.**

---

## File mới

| File | Việc |
|---|---|
| `core/agent.py` | Vòng lặp chọn công cụ. CHỈ điều phối. |
| `core/tools.py` | 4 công cụ — vỏ mỏng bọc code đã có |
| `core/resources.py` | Sổ đăng ký tài liệu + manifest |
| `core/parsers.py` | csv/xlsx/pdf/docx/txt/json -> chunk |
| `core/chunk_index.py` | Truy hồi trong tệp đính kèm (cùng công thức với KB) |
| `prompts/agent_templates.py` | Prompt quyết định + prompt trả lời |
| `api/file_routes.py` | Tải lên / liệt kê / xoá tệp |
| `static/js/files.js` | Giao diện đính kèm |
| `Evaluation/evaluate_routing.py` | Chấm độ chính xác chọn công cụ |

**Không đụng tới:** `retrieval.py`, `lexical.py`, `reranker.py`, `vectorstore.py`,
`embeddings.py`, `records.py`, `text.py`, `factcheck.py`, `websearch.py`,
`queue.py`, `auth.py`, `summarizer.py`, toàn bộ bộ eval 862 câu. R@1 không thể
tụt vì tầng truy hồi y nguyên.

`core/pipeline.py` (luồng tiers cũ) **vẫn còn và vẫn chạy được**:
`ORCHESTRATOR = "tiers"` trong `config.py` là quay về bản v5 để so sánh A/B.

---

## Hai phạm vi tài liệu

```
global documents        dataset 70 thủ tục
    │                   đánh chỉ mục MỘT LẦN (data/chromadb_eval + bm25_index.pkl)
    │                   luôn tra được ở MỌI hội thoại, MỌI người dùng
    │                   KHÔNG upload lại, KHÔNG nhúng lại
    └─ search_procedures

conversation documents  tệp người dùng đính kèm
    │                   parse -> chunk -> nhúng vào collection "doc_chunks"
    │                   chỉ tra được trong ĐÚNG cuộc trò chuyện đó
    └─ search_attachments
```

Mô hình nhận **manifest** — mô tả tệp, không phải nội dung:

```
- [chung] Thủ tục hành chính (dataset nội bộ): 70 thủ tục hành chính
  (lĩnh vực: Hộ tịch, Căn cước, ...) -> dùng search_procedures
- [tệp đính kèm] bao_cao.csv: bảng dữ liệu, 512 dòng -> dùng search_attachments
```

Khoảng 40 token mỗi lượt, thay vì nhét cả nghìn dòng dữ liệu vào mọi prompt.

---

## Tầng A: khi nào trích nguyên văn, khi nào viết lại

Dataset viết tắt và lộn xộn, in thẳng ra đọc như một ô Excel. Nên mặc định
`ANSWER_STYLE = "llm"`: mô hình viết lại cho người dân dễ đọc, rồi
`core/factcheck.py` kiểm chứng bằng luật — mọi số tiền và mốc thời gian trong
câu trả lời phải có trong bản ghi nguồn. Sai thì sinh lại; sai tiếp thì in bản
ghi gốc.

Chỉ ép trích **nguyên văn** khi câu hỏi nhắm vào đúng một trường:

| Câu hỏi | `wants_exact()` | Hành vi |
|---|---|---|
| "Lệ phí làm căn cước bao nhiêu?" | `lệ phí` | trích nguyên văn ô Lệ phí lên dòng đầu |
| "Nộp hồ sơ khai sinh ở đâu?" | `nơi nộp` | "ở đâu" là cách hỏi; "hồ sơ" chỉ là danh từ đi ngang |
| "Con tôi mới sinh, giờ làm gì?" | `""` | viết lại cho dễ đọc |
| "Cần giấy tờ gì và nộp ở đâu?" | `""` | hỏi hai thứ -> đừng ép |

Tắt hẳn: `EXACT_ON_FACET = False`. Về bản in thẳng: `ANSWER_STYLE = "template"`.

---

## Guardrail — chỉ có MỘT, và nhớ tắt nó đi

```python
AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL = True
```

Mô hình 1.5B đôi khi trả lời chay về một thủ tục hành chính mà không thèm tra
bảng, thành ra khẳng định pháp lý không nguồn. Cờ này ép đúng **một** lần tra
cứu trong trường hợp đó, rồi để mô hình tự viết. Header `X-Tools` ghi rõ
`guardrail:ép tra cứu` mỗi lần nó can thiệp — nhìn con số đó để biết mô hình tự
lo được đến đâu.

**Cắm mô hình 3B/7B quantized thì đặt `False`.** Mô hình lớn tự biết lúc nào
cần tra; ép thêm chỉ làm nó ngu đi. Đây là thứ duy nhất cần tắt — phần còn lại
của kiến trúc không có rào nào khác.

Đổi mô hình:
```python
LLM_MODEL_NAME = "qwen2.5:3b"                    # hoặc bản quantized khác
AGENT_TOOL_MODE = "native"                       # tool-calling gốc của Ollama
AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL = False
```
Không phải sửa gì khác.

---

## Đo

```powershell
.venv\Scripts\python.exe Evaluation\evaluate_routing.py --limit 100
.venv\Scripts\python.exe Evaluation\evaluate_routing.py --save v6_qwen1.5b
```

Dùng đúng nhãn có sẵn của bộ 862 câu:

| Nhãn trong bộ eval | Công cụ đáng lẽ phải chọn |
|---|---|
| `in_scope = 1` | `search_procedures` / `get_procedure` |
| `oos_kind = xa_giao` | `none` |
| `oos_kind` khác | `search_web` hoặc `none` |

Script in ra: độ chính xác tổng, tách theo nhóm câu hỏi, số lần guardrail phải
can thiệp (càng thấp càng tốt), và những kiểu chọn sai phổ biến nhất.

R@1 vẫn đo bằng `Evaluation/evaluate_retrieval.py` như cũ — tầng truy hồi không
đổi nên con số phải y hệt v4. Nếu nó tụt thì có gì đó sai, không phải cải tiến.

---

## Lỗi tiềm ẩn đã sửa nhân tiện

`X-Factcheck` và `X-Sources` là header HTTP, mà header chỉ mã hoá được latin-1.
Tóm tắt kiểm chứng tiếng Việt có dấu ("không đạt...") sẽ làm uvicorn ném
`UnicodeEncodeError` và trả 500 **giữa lúc đang stream**. Ở v5 lỗi này không
bao giờ nổ vì nhánh `_generate_checked` không bao giờ chạy
(`TIER_A_STYLE = "template"`). Bật `ANSWER_STYLE = "llm"` là nó nổ ngay. Nay
mọi giá trị header đều bỏ dấu qua `_ascii()`; thân câu trả lời vẫn giữ nguyên
tiếng Việt có dấu.

---

## Còn lại

- Chưa đo với Ollama thật — máy chạy demo là của bạn, số liệu phải chạy ở đó.
- `search_attachments` chưa có reranker (KB thì có). Tệp đính kèm thường nhỏ
  nên BM25 + dense là đủ; thêm reranker chỉ là gọi `core/reranker.py`.
- PDF scan chưa OCR được — báo lỗi rõ ràng thay vì nhận rồi đánh chỉ mục rỗng.
- `pypdf` và `python-docx` là tuỳ chọn: thiếu thì csv/xlsx/txt/md/json vẫn
  chạy, chỉ .pdf/.docx báo lỗi kèm câu lệnh cài.

---

# v6.1 — sửa sau lần chạy thử đầu tiên

## Lỗi làm hỏng cả hai tính năng mới: trình duyệt cache

Log server của lần chạy đầu chỉ có đúng **một** request static:

```
GET /static/js/files.js 304
```

Không có `app.js`, không có `styles.css`, không có `/api/files/supported`.
Trình duyệt dùng lại bản cũ trong cache cho mọi file trừ `files.js` (file mới
tinh nên chưa có trong cache). Hậu quả:

- nút đính kèm **không phản hồi** — `app.js` cũ chưa có đoạn gắn sự kiện
- ô nhập **bị bẹp** — `styles.css` cũ chưa có `.composer-row`, nên thẻ bọc mới
  không được tạo kiểu và textarea co lại

Code trên đĩa luôn đúng. Nhìn vào code sẽ không bao giờ tìm ra lỗi này — phải
nhìn vào log request.

**Sửa:** mọi đường dẫn static trong template mang `?v=__V__`, thay bằng
`STATIC_VERSION` trong `config.py` lúc phục vụ trang (`api/routes.render_page`).
Sửa JS/CSS xong thì **bump `STATIC_VERSION`**, trình duyệt buộc phải tải lại.

## pip cài nhầm Python

```
pip install pypdf python-docx
  -> C:\Users\...\AppData\Local\Programs\Python\Python312\Lib\site-packages
```

Đó là Python **toàn cục**. Ứng dụng chạy bằng `.venv\Scripts\python.exe` nên
không thấy. Luôn cài qua venv:

```powershell
.venv\Scripts\python.exe -m pip install pypdf python-docx
```

Cùng nguyên nhân với việc `Evaluation\evaluate_routing.py` gõ trần trong
PowerShell không in ra gì: nó chạy bằng Python toàn cục, thiếu fastapi/torch,
cửa sổ chớp rồi tắt. Script nay tự phát hiện và in ra đúng câu lệnh cần gõ.

## `run.ps1 -Eval` trỏ sai thư mục

```powershell
$EvalCsv = Resolve-Path "$Root\..\..\Evaluation\eval_questions.csv"   # SAI
```

`$Root` đã là gốc project, `..\..` trỏ ra **ngoài** project. Đã sửa thành
`$Root\Evaluation\...`. Thêm `-Routing`:

```powershell
.\run.ps1 -Routing -Limit 100
.\run.ps1 -Routing -Save v6_qwen1.5b
```

## Ép tra web — mệnh lệnh của người dùng, không phải guardrail

Lần chạy thử: hỏi "Giá vàng hôm nay" thì trả lời chay; bảo thẳng "Dùng web
search để trả lời giá vàng hôm nay" thì mô hình đáp *"tôi không thể sử dụng
công cụ như vậy vì có thể vi phạm quyền riêng tư"* — trong khi công cụ nằm ngay
đó. Ba thay đổi:

1. **Nút `Web`** cạnh ô nhập. Bật -> lượt đó bỏ qua hẳn bước chọn công cụ và
   tra mạng thẳng. Là lựa chọn cho MỘT lượt, gửi xong tự tắt.
2. **Nhận diện câu ra lệnh** — `agent.user_asked_for_web()`. "dùng web search",
   "tra trên mạng", "lên mạng", "google"... đều ép tra mạng. Truy vấn được làm
   sạch phần ra lệnh nhưng **giữ nguyên dấu** (DuckDuckGo tra tiếng Việt không
   dấu tệ hơn hẳn).
3. **Prompt quyết định** thêm ví dụ giá vàng / tỷ giá, và luật: hễ câu hỏi có
   "hôm nay", "hiện tại", "mới nhất" thì gần như chắc chắn là `search_web`.

Tra không ra thì **nói thật là tra không ra**, không lặng lẽ quay về trả lời chay.

> Cạm bẫy khi lọc từ ra lệnh: từ vựng hành chính đầy tiếng trùng với tiếng đệm
> sau khi bỏ dấu. `thu` = thủ (thủ tục), `ho` = hồ/hộ (hồ sơ, hộ chiếu),
> `lam` = làm, `ban` = bản/bạn. Thêm `thu` vào danh sách loại bỏ từng biến
> "thủ tục nhập tịch" thành "tục nhập tịch"; thêm `ho` biến "hộ chiếu" thành
> "chiếu". Bốn tiếng đó không được đưa vào `_COMMAND_WORDS`.

## Câu trả lời gộp nhiều thủ tục

Hỏi "đăng ký thuê nhà" (không có trong dataset) ra một danh sách 10 gạch đầu
dòng trộn *cấp số nhà* với *gia hạn tạm trú*. Nguyên nhân: prompt luôn nhận 3
thủ tục, mô hình 1.5B gộp cả 3.

Nay chỉ đưa thêm ứng viên **sát điểm** với top-1 (`EVIDENCE_TIE_GAP = 0.06`):

| Độ tin cậy top-3 | Số thủ tục vào prompt |
|---|---|
| 0.68 / 0.55 / 0.40 | 1 |
| 0.81 / 0.78 / 0.30 | 2 (hai bản cùng thủ tục khác cấp) |
| 0.90 / 0.88 / 0.87 | 3 (trần) |

Kèm hai luật mới trong `SYSTEM_GROUNDED`: cấm gộp nhiều thủ tục vào một câu trả
lời, và khớp yếu thì phải nói thẳng "chưa có trong dữ liệu" thay vì trả lời
bằng thủ tục gần giống.

---

# v6.2 — ngữ cảnh dính, chẩn đoán tra web, bảng Dev

## "Nộp ở đâu" trả lời Cục Cảnh sát giao thông — kiến trúc, không phải 1.5B

Hội thoại thật:

```
Muốn gia hạn tạm trú làm sao   -> đúng (0.85). Nơi nộp: Công an Xã
Tốn nhiều tiền                 -> "liên hệ cơ quan có thẩm quyền"  (quên sạch)
Nộp ở đâu                      -> "Cục Cảnh sát giao thông"  (0.43)  SAI
```

Lượt 3 không phải mô hình bịa. Nó truy hồi **lại từ đầu** bằng đúng ba chữ
"Nộp ở đâu", ra một thủ tục giao thông ở mức 0.43, rồi trả lời trung thực theo
bằng chứng sai đó. Lượt 2 thì mô hình chọn `none`, không có bằng chứng nào, và
1.5B bỏ qua lời dặn "dùng lại thông tin trong lịch sử".

Chia trách nhiệm cho đúng:

| | Lỗi của ai |
|---|---|
| Không tự dùng lại lịch sử khi không có bằng chứng | 1.5B |
| Để truy hồi 0.43 ghi đè chủ đề đang nói | **kiến trúc** |
| Truy hồi lại từ đầu cho câu hỏi tiếp nối | **kiến trúc** |

Sửa kiến trúc thì cả ba biến mất, vì mô hình không còn phải nhớ — bằng chứng
đúng được đặt sẵn vào tay nó.

## Ngữ cảnh dính

`FOLLOWUP_STICKY = True`. Điều kiện kích hoạt — cả bốn phải đúng:

1. câu hỏi nhắm vào MỘT trường (`wants_exact()` khác rỗng)
2. hội thoại đang có thủ tục trong ngữ cảnh (`last_row_id`)
3. truy hồi mới **không đủ chắc** (< `TIER_A_MIN_CONFIDENCE`)
4. không phải lượt bị ép tra web

Khi đó: `get_procedure(last_row_id)`, bỏ hẳn ứng viên yếu vừa truy hồi.

Dùng **số đo** chứ không phải từ khoá, nên không dính quá tay:

| Tình huống | Truy hồi mới | Kết quả |
|---|---|---|
| "Nộp ở đâu" (đang nói tạm trú) | 0.43 | quay lại tạm trú |
| "Tốn nhiều tiền" | không tra | quay lại tạm trú |
| "Lệ phí đăng ký xe bao nhiêu" | 0.88 | theo thủ tục MỚI |
| "Muốn gia hạn tạm trú làm sao" | — | không phải hỏi 1 trường, không dính |

## Tra web: bốn kiểu hỏng, giờ phân biệt được

Bản cũ gộp tất cả thành `"không có kết quả"`. Giờ mỗi lần thử đều ghi lại truy
vấn, backend, số kết quả thô, số qua allowlist, lỗi:

| Chẩn đoán | Ý nghĩa | Cách sửa |
|---|---|---|
| THIẾU THƯ VIỆN | chưa cài | `.venv\Scripts\python.exe -m pip install ddgs` |
| THƯ VIỆN LỖI | mất mạng / chặn tốc độ / đổi API | chờ, hoặc `pip install -U ddgs` |
| **BỊ ALLOWLIST CHẶN** | tra **được**, nhưng nguồn không chính thống | thêm domain, hoặc `WEB_SEARCH_STRICT = False` |
| KHÔNG CÓ KẾT QUẢ | từ khoá quá hẹp | đổi từ khoá |

Kiểu thứ ba là kiểu hay gặp nhất và trước đây hoàn toàn vô hình. Thêm
`WEB_SEARCH_BACKENDS = ["lite", "html", "auto"]`: backend mặc định hay hỏng,
`lite` ổn định hơn nhiều.

## Bảng Dev (`app/developer_mode.py`)

Nút ⚙ trên thanh tiêu đề. Bốn phần:

- **Ghi vết BẬT/TẮT** — bật/tắt ngay, không khởi động lại
- **Tra cứu web — chẩn đoán** — gõ từ khoá, bấm "Tra thử", xem đủ bốn kiểu hỏng ở trên
- **Vết chạy các lượt gần nhất** — mỗi lượt: trường được hỏi, thủ tục trong ngữ
  cảnh, chuỗi công cụ, độ tin cậy từng bước, sticky có kích hoạt không, kiểm
  chứng đạt hay phải sinh lại, tổng thời gian
- **Cấu hình đang chạy** — 25 công tắc đang ảnh hưởng tới hành vi
- **Dữ liệu** — reset (chuyển từ thanh bên sang)

Hai lớp, đừng nhầm:

```
DEV_TOOLS_ENABLED (config.py)   có ĐĂNG KÝ route hay không  <- bảo mật thật
developer_mode.enabled()        có GHI VẾT hay không        <- công tắc trong UI
```

Đặt `DEV_TOOLS_ENABLED = False` trước khi bàn giao: endpoint sẽ không tồn tại.
Ẩn nút không phải là bảo mật.

Vết chạy nằm trong RAM (`deque`, 40 lượt), không đụng CSDL, không ghi ra đĩa.

---

# v6.3 — sàn độ tin cậy, nguồn có link, tra web bám .gov.vn

## Nhãn nói dối — lỗi nặng nhất trong bản trước

Hỏi "Đến nơi đâu để nộp hồ sơ" khi đang nói về tạm trú, hệ thống truy hồi ra
**Đăng ký khai sinh ở mức 0.20**, in nguyên bản ghi khai sinh, và dán nhãn xanh
**"Từ cơ sở dữ liệu thủ tục · 0.20"**.

Nhãn xanh đó nói với người dân rằng đây là dữ liệu chính thống. Với 0.20 thì nó
là một dòng ngẫu nhiên. Lỗi này do chính tôi tạo ra ở v6: `_tier_for()` gán
`procedures -> Tier.A` **không thèm nhìn độ tin cậy**.

Hai lớp phòng, độc lập nhau:

```
truy hồi được bản ghi
   │
   ├─ < 0.45 (EVIDENCE_MIN_CONFIDENCE)
   │     ├─ đang có thủ tục trong ngữ cảnh? ──► quay lại thủ tục đó
   │     └─ không ────────────────────────────► BỎ HẲN bằng chứng,
   │                                            trả lời như không có dữ liệu
   │
   ├─ 0.45 – 0.65 ──► vẫn dùng, nhưng nhãn "Thông tin chung — KHÔNG chắc chắn"
   │
   └─ ≥ 0.65 ──────► nhãn "Từ cơ sở dữ liệu thủ tục"
```

Thà nói "mình chưa có thủ tục này" còn hơn in bản ghi khai sinh cho người đang
hỏi về tạm trú.

Ngữ cảnh dính cũng nới điều kiện: trước chỉ chạy khi `wants_exact()` bắt được
trường; giờ **câu ngắn (≤ 9 từ) cũng tính là hỏi tiếp**. Bộ nhận diện trường
không thể phủ hết mọi cách nói của người Việt, và khi nó trượt thì hậu quả
đúng bằng lỗi trên.

## "145 USD" cho thủ tục 7.000đ

Ép tra web cho "Làm tạm trú tốn bao nhiêu tiền" → DuckDuckGo trả về **thẻ tạm
trú cho người nước ngoài** (thật sự tính bằng USD), mô hình lấy luôn con số đó.
Bản ghi nội bộ ghi **7.000 đồng**.

Ba lớp sửa:

1. **Bám nguồn ngay trong truy vấn.** `WEB_SEARCH_QUERY_HINT = "site:gov.vn"`
   gắn vào lượt tra ĐẦU TIÊN. Đo được trước đó: truy vấn trần 20 kết quả, chỉ
   4 qua allowlist. Thứ tự giờ là: `site:gov.vn` → từng miền cụ thể → truy vấn
   trần (vẫn lọc allowlist).
2. **Neo vào dữ liệu nội bộ.** Ép tra web mà đang có thủ tục trong ngữ cảnh thì
   kèm luôn bản ghi nội bộ. Mô hình có cả hai con số trước mặt, kèm luật:
   *số liệu lấy từ bản ghi nội bộ; web nói khác thì tin nội bộ và nói rõ trên
   mạng có thông tin khác.*
3. **Ghi nguồn vào từng đoạn.** Mỗi đoạn web mang sẵn `[Nguồn: host] Tiêu đề`.
   Không có nó, mô hình trộn số liệu nhiều trang mà không biết mình đang trộn.
   Kèm luật: kết quả nói về thủ tục KHÁC gần giống thì bỏ qua.

## Nguồn bấm được

`WebResult.sources` giờ là **URL đầy đủ**, không còn là tên miền. Giao diện hiện
danh sách "Nguồn — bấm để tự kiểm tra" dưới mỗi câu trả lời.

Dựng bằng `createElement("a")` + `textContent`, **không phải `innerHTML`** —
chuỗi này đến từ kết quả tìm kiếm ngoài, nhét thẳng vào `innerHTML` là mở cửa
XSS. Link mang `rel="noopener noreferrer"`. Footer vẫn chỉ ghi tên miền cho gọn.

## Bảng Dev trượt ra

Trước đây bảng là một cột flex nên nó **bóp khung chat** mỗi lần mở. Giờ là lớp
phủ trượt từ phải (`position: fixed` + `transform`), có nền mờ, đóng bằng nút ×,
bấm ra ngoài, hoặc phím Esc. Tôn trọng `prefers-reduced-motion`.

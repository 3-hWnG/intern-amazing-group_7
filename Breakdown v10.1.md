# Breakdown — hệ thống local V10.1.x (bản mới nhất V10.1.2)

**Thư mục:** `D:\reimagine_V10.1` · **Branch:** `Reimage-V10.1` · **Cập nhật:** 17/09/2026

Tài liệu này mô tả **code đang có trong thư mục local** (bản mới nhất: **V10.1.2**). Cách đánh số xem `docs/VERSIONS.md`:
- **V10** — nền của nhóm: MCP web search, Evidence Pack, kiểm chứng.
- **V10.1** — các bản sửa ngày 16/09 (`docs/CHANGELOG_2026-09-16.md`), = branch `Reimage-V10.1` trên GitHub.
- **V10.1.1** — công cụ đánh giá truy vấn ngày 17/09 (không đổi logic ứng dụng).
- **V10.1.2** — tra cứu bằng câu hỏi gốc (`docs/CHANGELOG_V10.1.2.md`), **chưa commit**.

Chỗ nào do V10.1 hoặc V10.1.2 thêm vào sẽ được ghi rõ bằng nhãn **[V10.1]** hoặc **[V10.1.2]**.
Lưu ý: branch `Re-imagine-V10.2` trên GitHub là hướng khác của nhóm (cách 3), **không** phải bản mô tả ở đây.

---

## 1. Tổng quan một câu

Mô hình nhỏ chạy local (Ollama, `qwen2.5:1.5b` / `3b`) chỉ lo **hiểu câu hỏi và diễn đạt**. Thông tin thủ tục
**luôn được tra từ web** qua một MCP server. Câu trả lời được **kiểm chứng lại với nguồn** trước khi gửi.
SQLite và một hàng đợi tuần tự lo phần bộ nhớ và thứ tự xử lý.

```
Trình duyệt ─► FastAPI ─► Hàng đợi (1 việc/lần) ─► ORCHESTRATOR
                                                     │
   1. Ngữ cảnh (tóm tắt + 10 tin gần nhất + hồ sơ tỉnh/xã)
   2. Hiểu ý định (LLM) + Bộ gác (LLM) ──► trò chuyện / từ chối / hỏi lại
   3. Chọn truy vấn [V10.1.2]
   4. MCP search ──► Evidence Pack (≤5 nguồn, có URL + ngày)
   5. Soạn câu trả lời (LLM, chỉ dùng Evidence Pack, trích [S#])
   6. Kiểm chứng (luật + LLM) ──► PASS / sửa lại 1 lần / cảnh báo
                                                     │
                     SQLite: tin nhắn · Evidence Pack · hồ sơ · phản hồi 👍/👎
```

---

## 2. Bản đồ thư mục

| Đường dẫn | Vai trò |
|---|---|
| `app/main.py` | Khởi động: mở CSDL, kiểm tra Ollama, bật MCP, chạy hàng đợi |
| `app/config.py` | **Mọi cấu hình**, đọc từ biến môi trường / `.env` (biến môi trường được ưu tiên) |
| `app/api/` | `auth_routes` · `chat_routes` (NDJSON stream) · `file_routes` · `dev_routes` · `routes` (health) |
| `app/core/orchestrator.py` | Pipeline 6 bước; không đụng CSDL (nên script đánh giá gọi thẳng được) |
| `app/core/intent.py` | Hiểu ý định, bộ gác hỏi lại, nhớ tỉnh/xã, chọn truy vấn [V10.1.2] |
| `app/core/evidence.py` | Gọi MCP → Evidence Pack; gộp nguồn; thêm đoạn từ tệp đính kèm |
| `app/core/answer.py` | Soạn câu trả lời và lời chào |
| `app/core/verifier.py` | Kiểm chứng bằng luật + LLM, chính sách khi trượt |
| `app/core/summarizer.py` | Tóm tắt hội thoại khi ngữ cảnh dài |
| `app/core/llm.py` | Cổng Ollama; tham số riêng cho từng vai |
| `app/core/mcp_client.py` | Phiên MCP lâu dài (stdio / http), dự phòng gọi thẳng engine |
| `app/core/queue.py` | Hàng đợi asyncio, `QUEUE_CONCURRENCY` worker |
| `app/core/auth.py` | bcrypt + cookie phiên, khoá tạm khi sai mật khẩu nhiều lần |
| `app/core/parsers.py`, `resources.py`, `chunk_index.py` | Đọc tệp đính kèm, chia đoạn, tìm đoạn liên quan |
| `app/mcp_search/server.py` | MCP server `tthc-search`: `search_evidence`, `web_search`, `fetch_page` |
| `app/mcp_search/engine.py` | Tìm web → xếp hạng → đọc trang → chọn đoạn → Evidence Pack |
| `app/prompts/templates.py` | **Tất cả prompt**, ví dụ mẫu, câu trả lời cố định |
| `app/domain/text.py` | `fold` (bỏ dấu), `tokenize`, `BM25`, regex tiền / ngày / số văn bản |
| `app/db/` | `schema.sql`, `connection.py`, `repositories.py` (mọi câu SQL) |
| `app/static/`, `app/templates/` | Giao diện HTML/CSS/JS |
| `Evaluation/` | Bộ câu hỏi + script đo (xem mục 10) |
| `finetune/` | QLoRA → GGUF → Ollama, benchmark lượng tử hoá |

---

## 3. Luồng một tin nhắn (end-to-end)

1. **`POST /api/conversations/{id}/chat`** (`chat_routes.py`)
   - Kiểm tra cookie và quyền sở hữu hội thoại; lưu tin nhắn người dùng. Tin đầu tiên được dùng để đặt tên hội thoại (8 từ đầu).
   - Đẩy **một job** vào hàng đợi. Nếu đang có người trước, trả sự kiện `{"type":"queue","position":N}`.
2. **Worker** (`queue.py`) chạy job trong một luồng riêng:
   - `summarizer.build_context()` lấy tóm tắt và các tin gần nhất.
   - Đọc `user_profile` (tỉnh/xã đã nhớ).
   - Gọi `orchestrator.run_turn()`.
   - Lưu câu trả lời, Evidence Pack và cập nhật hồ sơ.
   - Phát câu trả lời **đã kiểm chứng** theo từng mẩu 24 ký tự (hiệu ứng gõ chữ), rồi gửi sự kiện `done`.
3. **Luồng NDJSON** trả về trình duyệt các sự kiện `queue`, `status`, `delta`, `done`, `error`.

Mọi lời gọi LLM của một lượt, kể cả bước tóm tắt, đều nằm **trong job**, nên hàng đợi đảm bảo mô hình chỉ xử lý từng tin nhắn một.

---

## 4. Pipeline 6 bước (`core/orchestrator.py`)

### Bước 1 — Ngữ cảnh (`summarizer.py`)
- Ngữ cảnh gồm: **tóm tắt dài hạn**, **các tin chưa tóm tắt**, và **hồ sơ tỉnh/xã**.
- Ước lượng token = số từ × `TOKENS_PER_SYLLABLE`. Khi tổng vượt `MAX_CONTEXT_TOKENS` (3000) thì LLM tóm tắt phần cũ, chỉ giữ nguyên văn `SUMMARY_KEEP_RECENT` (5) lượt gần nhất.
- Bản tóm tắt được **ghi vào CSDL** (`conversations.summary`, `summary_upto`) để lần sau không phải tóm tắt lại.
- Nếu LLM lỗi thì chỉ cắt bớt tin cũ, không tóm tắt.

### Bước 2 — Hiểu ý định + bộ gác (`intent.py`)
Có **hai lời gọi LLM**, cả hai trả JSON theo schema, temperature 0. Không có luật bắt từ khoá.

**a) `understand`** trả về:
- `intent`: 1 trong 13 nhãn — `birth_registration`, `marriage_registration`, `permanent_residence`,
  `temporary_residence`, `identity_documents`, `business_registration`, `land_administration`,
  `social_security`, `tax`, `other`, `chitchat`, `out_of_scope`, `unknown`.
- `standalone_question`: câu hỏi viết lại thành câu đứng riêng.
- `province`, `ward`, `missing_information`, `needs_clarification`, `clarifying_question`, `search_queries`.
- System prompt có ghi ngày hiện tại và việc từ 01/7/2025 cả nước có 34 tỉnh, chính quyền 2 cấp.
- **Few-shot:** có 6 ví dụ mẫu, bật/tắt bằng `UNDERSTAND_FEWSHOT`. Nếu mô hình chép nguyên một ví dụ, code chạy lại bước này không kèm ví dụ.
- **[V10.1]** Nếu `clarifying_question` bị chép từ ví dụ mẫu thì bị xoá. Khi đã biết thủ tục cụ thể, đặt `needs_clarification = False`.
- **[V10.1]** Truy vấn của mô hình bị bỏ dấu `?` ở cuối và được thêm năm. Nếu mô hình không trả truy vấn nào, dùng câu viết lại thay thế.

**b) `gate`** là một quyết định hẹp: `search` / `ask` / `greeting` / `other`. Có 15 ví dụ mẫu; **[V10.1]** thêm các ví dụ "t cần làm giấy khai sinh" và "tôi muốn làm hộ chiếu" → `search`.

**c) Kết hợp hai kết quả thành `route`:**

| Điều kiện | route |
|---|---|
| gate = `other` và intent không phải thủ tục cụ thể | `out_of_scope` (dùng câu từ chối **cố định**) |
| gate = `greeting` và intent không phải thủ tục cụ thể | `chitchat` |
| gate = `search` nhưng understand nói chitchat/out_of_scope | câu ≤ 5 từ → tin understand; câu dài hơn → `search` |
| gate = `ask` **và** understand thấy thiếu thông tin, và lượt trước chưa hỏi lại | `clarify` |
| còn lại | `search` |

- Chỉ hỏi lại khi **cả hai bộ cùng đồng ý**. Lý do (ghi trong code): nếu để mình `understand` quyết định thì mô hình 1.5B hỏi lại gần như mọi câu.
- **Không hỏi dồn:** nếu lượt trước trợ lý vừa hỏi lại, lượt này bắt buộc đi tra.

**d) Nhớ tỉnh/xã (`profile_update`)**
- Chỉ lưu tỉnh/xã khi người dùng **thật sự đã gõ** tên đó: so trên chuỗi đã bỏ dấu, chấp nhận vài bí danh như `hcm`, `sai gon`, `hn`.
- Mục đích là tránh lưu nhầm tỉnh mà mô hình chép từ ví dụ mẫu.

### Bước 2' — Trả lời ngay, không tra cứu
- **`chitchat`:** LLM đáp tối đa 2 câu. **[V10.1]** Có lời nhắc bắt buộc trả lời bằng tiếng Việt.
- **`out_of_scope`:** dùng câu `OUT_OF_SCOPE_TEXT` cố định, không để mô hình tự viết (mô hình nhỏ hay làm theo yêu cầu ngoài phạm vi).
- **`clarify`:** trả về câu hỏi lại. Nếu câu đó rỗng thì dùng `GENERIC_CLARIFY`.

### Bước 3 — Chọn truy vấn tìm kiếm **[V10.1.2]** (`intent.search_plan`)

| Trường hợp | Truy vấn chính | Dự phòng |
|---|---|---|
| Tin nhắn **mở đầu** (chưa có tin người dùng nào trước) | **nguyên văn** tin nhắn | truy vấn do mô hình sinh |
| Tin nhắn **nối tiếp** | **câu viết lại** `standalone_question` | truy vấn do mô hình sinh |
| `SEARCH_QUERY_MODE=model` (cách V10.1) | truy vấn do mô hình sinh | — |

- Truy vấn dự phòng chỉ được dùng khi lượt tra chính **không ra nguồn nào**.
- Lý do đổi: đo trên 88 câu, tra nguyên văn tìm đúng trang ~99% (top 5), trong khi truy vấn mô hình chỉ đạt 68–81% (mục 10).

### Bước 4 — Tra cứu → Evidence Pack (`evidence.py` → MCP → `engine.py`)

`evidence.gather()`:
- Thêm một bản `"<truy vấn đầu> site:gov.vn"`, bỏ trùng, giữ tối đa `SEARCH_MAX_QUERIES` (3) truy vấn.
- Gọi công cụ MCP `search_evidence`.
- Nếu hội thoại có tệp đính kèm, chèn thêm tối đa `ATTACH_TOP_K` (2) đoạn liên quan nhất lên **đầu** danh sách nguồn.
- Đánh số lại các nguồn thành `S1..Sn`.

`mcp_client.py`:
- Giữ **một phiên MCP lâu dài** trong luồng nền (stdio: app tự bật server làm tiến trình con; http: kết nối tới dịch vụ `mcp-search`).
- Nếu MCP lỗi và `MCP_FALLBACK_DIRECT=true` thì gọi thẳng engine, và ghi rõ transport đã dùng.
- **[V10.1]** Import sẵn `trafilatura` ở luồng nền khi khởi động.

`engine.build_evidence_pack()`:
1. **Tìm song song** các truy vấn (ddgs / searxng / brave / tavily).
   - Có hạn chót chung `SEARCH_DEADLINE`. Nếu hết giờ mà chưa có kết quả thì chờ tiếp, nhưng không quá `SEARCH_TOTAL_BUDGET`.
   - Nếu không truy vấn nào ra kết quả, thử lại **một** truy vấn đã bỏ năm và bỏ `site:`.
   - Kết quả tìm kiếm được cache 30 phút.
2. **Xếp hạng nguồn** = độ tin tên miền + thứ hạng tìm kiếm + độ mới:
   - Độ tin tên miền: chính thống 3 · CSDL pháp luật 2 · báo chí 1.5 · khác 1.
   - Thứ hạng: `1/(1+0.35·rank)`.
   - Độ mới: năm gần đây +0,6; năm cũ hơn 3 năm −0,8.
   - Mỗi lần một URL xuất hiện ở truy vấn khác thì +0,3.
   - Bỏ các tên miền nằm trong `BLOCKED_DOMAINS` (mạng xã hội…).
3. **Đọc toàn văn** `FETCH_TOP_N` (6) trang đầu song song bằng httpx + trafilatura, hạn chót `FETCH_DEADLINE`.
   - Trang chậm hoặc lỗi thì dùng snippet.
   - Trang `.gov.vn` thiếu chứng chỉ SSL thì đọc lại không xác thực, và ghi vào nhật ký.
4. **Chọn đoạn liên quan:**
   - Chia trang thành đoạn khoảng 650 ký tự.
   - Chấm **BM25 chung** cho mọi đoạn của mọi trang (truy vấn = câu hỏi + các truy vấn).
   - Với mỗi trang, lấy **cụm đoạn liền nhau** tốt nhất (danh sách hồ sơ thường trải qua nhiều đoạn).
5. **Chấm lại và đóng gói:**
   - Điểm cuối = điểm nguồn + 2 × độ liên quan tương đối + độ mới của ngày đăng.
   - Bỏ trang có độ liên quan dưới 20% so với trang tốt nhất.
   - Giữ tối đa `EVIDENCE_TOP_K` (5) nguồn, tổng tối đa `EVIDENCE_MAX_CHARS` (7000) ký tự, mỗi nguồn tối đa `EVIDENCE_SOURCE_CHARS`.

Các bản sửa **[V10.1]** trong engine:
- `clean_snippet`: đoạn trích ddgs gộp nhiều bài được tách theo tem ngày (`Mar 4, 2025 · …`), **giữ đoạn mới nhất** và lấy ngày đó làm ngày đăng.
- `_clean_title`: cắt tiêu đề bị gộp kiểu "Bài A ...Bài B ...".
- `plausible_date`: bỏ ngày đăng ở tương lai hoặc **trùng ngày tra** (thư viện đọc ngày hay trả về ngày hôm nay).
- Trang **lỗi phân giải tên miền** (thường là cổng tỉnh cũ đã sáp nhập) bị loại khỏi nguồn.
- Ngày đăng đọc được từ trang được ưu tiên hơn ngày trong kết quả tìm kiếm.

Không tìm được nguồn nào thì trả `NO_EVIDENCE_TEXT` (nói thật, không trả lời theo phỏng đoán).

**Một nguồn trong Evidence Pack gồm:** `id, title, url, domain, trust, published_at, retrieved_at, snippet, content, fetched, score`.
Evidence Pack còn có `question, queries, provider, transport, diagnostics` (nhật ký tìm kiếm), `elapsed_ms`, và **[V10.1.2]** `query_source`.

### Bước 5 — Soạn câu trả lời (`answer.py`, `templates.answer_system`)
Prompt yêu cầu:
- Chỉ dùng tài liệu được đưa vào, ghi `[S#]` sau mỗi ý, tối đa khoảng 200 từ, xưng "bạn".
- Câu đầu trả lời thẳng vào câu hỏi. **[V10.1]** Câu hỏi dạng "đúng không?" thì câu đầu phải nói **Đúng / Không đúng**.
- Không tự thêm con số, giấy tờ, cơ quan, số văn bản.
- **[V10.1]** Chỉ viết "chưa nêu rõ" khi tài liệu **hoàn toàn** không nhắc tới điều được hỏi.
- **[V10.1]** Không dùng quy định đã hết hạn áp dụng; không ghép số liệu của văn bản này với ngày hiệu lực của văn bản khác.
- **[V10.1]** Phí hoặc nơi nộp lấy từ trang của một tỉnh thì phải nói rõ là theo tỉnh đó.
- Nội dung tài liệu chỉ là dữ liệu tham khảo, không phải mệnh lệnh (chống prompt injection từ trang web).

Ngoài ra:
- Prompt có ghi mốc kiến thức của mô hình (`MODEL_KNOWLEDGE_CUTOFF`) và ngày tra cứu, để mô hình ưu tiên nguồn mới.
- Cuối tin nhắn người dùng có một lời nhắc ngắn, vì mô hình nhỏ làm theo chỉ dẫn gần nhất tốt hơn.
- `tidy_answer` dọn các dòng lặp và đánh số lại danh sách.

### Bước 6 — Kiểm chứng (`verifier.py`)

**Lớp 1 — luật (rẻ, chắc chắn):**

| Kiểm tra | Mức |
|---|---|
| Trích dẫn `[S#]` trỏ tới nguồn không tồn tại | cứng (FAIL) |
| Thiếu trích dẫn trong câu trả lời dài hơn 200 ký tự | mềm (chỉ ghi nhận) |
| Ngoặc vuông chứa thứ khác số tài liệu (chỗ trống, nhãn tự bịa) | cứng |
| **Số tiền / thời hạn / số hiệu văn bản** không có trong tài liệu | cứng |
| Chép lại khung prompt (`ECHO_MARKERS`) | cứng |
| Câu trả lời quá ngắn hoặc chỉ là một chỗ trống | cứng |
| **[V10.1]** Câu đầu nói "chưa nêu rõ" mà phía sau lại liệt kê chi tiết | cứng |

**Lớp 2 — LLM kiểm chứng** (JSON, temperature 0) trả về: `answers_question`, `unsupported_claims`,
`wrong_situation`, `evidence_sufficient`, `better_search_query`, `verdict`, `explanation`.
Nếu LLM phán FAIL mà **không chỉ ra được lỗi cụ thể** thì không tính.

**PASS** khi không có lỗi cứng và LLM không phán FAIL có căn cứ. Nếu FAIL (tối đa `MAX_VERIFY_RETRIES` = 1 lần sửa):
- Nếu tài liệu chưa đủ và LLM có gợi ý truy vấn khác → **tra bổ sung một lần**, gộp nguồn mới lên đầu.
- **Viết lại** câu trả lời kèm ghi chú sửa lỗi cụ thể (không đưa nguyên văn lời phê, vì mô hình nhỏ hay chép lại).

Nếu vẫn FAIL, áp dụng `VERIFY_FAIL_POLICY`:
- `refuse` → câu từ chối cố định.
- `warn` (mặc định) → lược bỏ các dòng có chi tiết sai, rồi thêm cảnh báo.
  - **[V10.1]** Lược thêm các dòng trùng từ 60% trở lên với `unsupported_claims`, để bắt ý bịa bằng chữ.
  - **[V10.1]** Bỏ các tiêu đề mà ý bên dưới đã bị lược hết, và các câu dẫn cụt (kết thúc bằng ":").
  - **[V10.1]** Nếu không còn nội dung thật thì trả câu "Tài liệu tra cứu được chưa nêu rõ…".

**[V10.1]** Câu trả lời chỉ nói "chưa nêu rõ" được gán `kind = not_in_sources`, với nhãn riêng trên giao diện, và **không tính là PASS**.

Nguồn hiển thị dưới câu trả lời chỉ gồm những nguồn **được trích dẫn** (nếu câu trả lời có trích dẫn).

---

## 5. Mô hình và tham số (`core/llm.py`)

Dùng **một mô hình cho nhiều vai**, mỗi vai có tham số riêng:

| Vai | temperature | num_predict | Ghi chú |
|---|---|---|---|
| `understand` (cả bộ gác) | 0 | 450 | JSON schema |
| `answer` | `TEMPERATURE` (0.1), top_p 0.9 | `ANSWER_MAX_TOKENS` | repeat_penalty 1.15, repeat_last_n 256 |
| `verify` | 0 | 350 | JSON schema; có thể dùng mô hình riêng qua `VERIFIER_MODEL` |
| `summary` | 0.1 | 350 | |
| `chitchat` | 0.4 | 160 | |

Thông số chung: `num_ctx = LLM_NUM_CTX` (8192), `keep_alive` 30 phút. Mô hình được nạp sẵn vào VRAM lúc khởi động.
Đầu ra JSON hỏng thì code cố gắng lấy phần `{...}` bên trong; không được nữa thì trả `{}`.

---

## 6. Dữ liệu (SQLite, `db/schema.sql`)

```
users ─┬─ auth_sessions              (cookie phiên, hạn trượt)
       ├─ login_attempts             (khoá 15 phút sau 5 lần sai)
       ├─ user_profile               (tỉnh/thành, xã/phường — nhớ xuyên hội thoại)
       └─ conversations ─┬─ messages ─┬─ evidence    (Evidence Pack dạng JSON)
         (summary,       │            └─ feedback    (phu_hop / khong_phu_hop)
          summary_upto)  └─ documents ── document_chunks   (tệp đính kèm)
job_log                               (thời gian chờ / xử lý của hàng đợi)
```

- `messages.kind`: `answer` · `not_in_sources` [V10.1] · `clarify` · `chitchat` · `out_of_scope` · `no_evidence` · `error`.
- `messages.verdict`: `PASS` · `FAIL` · rỗng.
- Hội thoại cũ hơn `RETENTION_DAYS` (90 ngày) bị xoá khi khởi động. Phiên đăng nhập hết hạn cũng bị dọn.
- Toàn bộ câu SQL nằm trong `repositories.py`.

---

## 7. Các thành phần phụ trợ

- **Đăng nhập (`auth.py`):** mật khẩu băm bằng bcrypt; token phiên 32 byte trong cookie httponly, samesite=lax; phiên tự gia hạn khi dùng. Dùng cookie thay vì JWT để thu hồi được ngay.
- **Hàng đợi (`queue.py`):** `QUEUE_CONCURRENCY` (1) worker; tối đa `QUEUE_MAX_DEPTH` (20) việc chờ; mỗi việc tối đa `QUEUE_JOB_TIMEOUT` (180s). Chữ được đẩy từ luồng xử lý về request qua `call_soon_threadsafe`.
- **Tệp đính kèm:**
  - Nhận csv/tsv/txt/md/json/xlsx/xls, cùng pdf/docx nếu có thư viện; tối đa 20 MB, 10 tệp mỗi hội thoại.
  - Gửi dạng byte thô với header `X-Filename`, nên không cần thư viện `python-multipart`.
  - Tệp được chia đoạn 900 ký tự (chồng 120) rồi tìm bằng BM25.
- **Chế độ nhà phát triển (`developer_mode.py`, `/api/dev/*`):** xem vết từng lượt (ý định, truy vấn, thời gian, kết quả kiểm chứng), bảng cấu hình đang chạy, thử `web_search`, thống kê, và xoá dữ liệu. Chỉ bật khi `DEV_TOOLS_ENABLED=true`.
- **Giao diện:** thanh bên lịch sử kiểu ChatGPT, trích dẫn `[S#]` bấm được, danh sách nguồn, **Evidence Pack** mở rộng được (câu hỏi tra cứu, truy vấn, **[V10.1.2]** nguồn truy vấn, ngày tra, so sánh mốc kiến thức của mô hình với ngày của nguồn, nhật ký tìm kiếm), và nút 👍/👎.

---

## 8. Cấu hình quan trọng (`.env`)

| Nhóm | Biến | Mặc định | Ghi chú |
|---|---|---|---|
| Mô hình | `LLM_MODEL` | `qwen2.5:1.5b` | `.env` trên máy Hưng đang để `1_5B_finetune:latest` |
| | `VERIFIER_MODEL` | = `LLM_MODEL` | |
| | `LLM_NUM_CTX` · `TEMPERATURE` · `TOP_P` | 8192 · 0.1 · 0.9 | |
| Hiểu ý định | `UNDERSTAND_FEWSHOT` | true | **`.env` đang để false** |
| | `CLARIFY_ENABLED` | true | |
| Tìm kiếm | `SEARCH_PROVIDER` | `ddgs` | `searxng` / `brave` / `tavily` |
| | **`SEARCH_QUERY_MODE`** [V10.1.2] | `question` | `model` = cách V10.1 |
| | `SEARCH_MAX_QUERIES` · `SEARCH_DEADLINE` · `SEARCH_TOTAL_BUDGET` | 3 · 9s · 25s | |
| | `FETCH_TOP_N` · `FETCH_DEADLINE` | 6 · 6s | |
| | `EVIDENCE_TOP_K` · `EVIDENCE_MAX_CHARS` | 5 · 7000 | |
| | `OFFICIAL_DOMAINS` · `LEGAL_DOMAINS` · `BLOCKED_DOMAINS` | gov.vn… | |
| MCP | `MCP_TRANSPORT` · `MCP_FALLBACK_DIRECT` | `stdio` · true | Docker dùng `http` |
| Kiểm chứng | `VERIFIER_ENABLED` · `MAX_VERIFY_RETRIES` · `VERIFY_FAIL_POLICY` | true · 1 · `warn` | |
| Bộ nhớ | `MAX_CONTEXT_TOKENS` · `SUMMARY_KEEP_RECENT` · `PROFILE_MEMORY_ENABLED` | 3000 · 5 · true | |
| Hệ thống | `QUEUE_CONCURRENCY` · `ATTACHMENTS_ENABLED` · `DEV_TOOLS_ENABLED` · `RETENTION_DAYS` | 1 · true · true · 90 | |

---

## 9. Những gì V10.1.x đã đổi so với V10

| Bản | Vấn đề | Cách xử lý |
|---|---|---|
| V10.1 | Trang "quá hạn 6s" ở các lượt đầu | Import sẵn `trafilatura` khi khởi động |
| V10.1 | Đoạn trích ddgs gộp nhiều bài, lẫn quy định cũ và mới | `clean_snippet` giữ đoạn mới nhất |
| V10.1 | Cổng tỉnh đã sáp nhập lỗi DNS | Loại nguồn chết |
| V10.1 | Ngày đăng = ngày tra | `plausible_date` |
| V10.1 | Câu hỏi lại chép ví dụ mẫu | `_copied_clarify` + thêm ví dụ cho bộ gác |
| V10.1 | Ý bịa bằng chữ vẫn hiện ra | Lược theo `unsupported_claims` |
| V10.1 | Câu trả lời cụt "bạn sẽ cần:" | `has_substance` / `_drop_empty_headings` |
| V10.1 | "Chưa nêu rõ" mà vẫn liệt kê; không trả lời đúng/sai | Luật mâu thuẫn + prompt mới |
| V10.1 | "Chưa nêu rõ" vẫn được tính PASS | `kind = not_in_sources` |
| V10.1 | "hello" được trả lời bằng tiếng Anh | Lời nhắc tiếng Việt |
| V10.1.1 | Chưa đo được chất lượng truy vấn | Bộ 862 câu + `gen_queries_baseline` / `analyze_queries` / `search_baseline` |
| **V10.1.2** | Truy vấn do mô hình sinh lệch thủ tục ~30–50% | Tra nguyên văn / câu viết lại (`search_plan`) |

---

## 10. Đánh giá hiện có (`Evaluation/`)

| File | Đo gì |
|---|---|
| `eval_set.jsonl` + `evaluate.py` | 45 câu tự soạn: độ chính xác ý định, hỏi lại đúng lúc, nguồn chính thống, trích dẫn, tỉ lệ PASS, độ trễ |
| `eval_questions.csv` | 862 câu, 55 thủ tục, 12 kiểu câu (khôi phục từ lịch sử git; sinh từ `data_merged.xlsx`) |
| `gen_queries_baseline.py` | Chạy bước hiểu ý định trên 862 câu, ghi truy vấn (`--fewshot on\|off`) |
| `analyze_queries.py` | Chấm sơ bộ truy vấn bằng luật từ khoá (lệch thủ tục, mất dấu, mất khía cạnh) |
| `search_baseline.py` | Tra web thật trên 88 câu: truy vấn mô hình / câu gốc / gộp |
| `realistic_set.jsonl` + `search_realistic.py` | [V10.1.2] 40 câu đơn thực tế + 16 hội thoại nhiều lượt (bước 5c) |

Số đo chính đến 17/09 (chi tiết trong `docs/TASK_query_finetune_dataset.md`):

| | hit@5 truy vấn mô hình | hit@5 câu hỏi gốc |
|---|---|---|
| few-shot TẮT | 68,2% | 100% |
| few-shot BẬT | 80,7% | 98,9% |

---

## 11. Điểm yếu đã biết (chưa xử lý)

**Chất lượng**
- **Nhãn intent thiếu nhóm:** không có nhóm cho trợ cấp, con dấu, vũ khí, quy hoạch…, nên mô hình dồn các câu này vào `identity_documents` hoặc `business_registration`. Luồng không bị ảnh hưởng vì không định tuyến theo intent, nhưng chỉ số "intent accuracy" chưa có ý nghĩa.
- **Bộ gác trả `ask` quá nhiều** (230/862 câu). Nhờ luật "cả hai bộ phải đồng ý" nên hiếm khi thật sự hỏi lại.
- **Câu ngoài phạm vi chỉ bị chặn khoảng 44%** (câu mức phạt, pháp lý, ngoài dataset vẫn đi tra).
- **Trang dựng bằng JavaScript** (`dichvucong.gov.vn`) không đọc được nội dung, chỉ dùng được đoạn trích.
- **ddgs** không ổn định: hay bị giới hạn tốc độ và lỗi TLS.
- **Luật chấm "đúng thủ tục"** trong các script đánh giá là heuristic, hơi dễ dãi, chưa có người chấm.

**Kỹ thuật** (đã hoãn vì đang chạy thử local)
- Endpoint xoá dữ liệu ở `/api/dev/reset` không kiểm tra quyền admin, và `DEV_TOOLS_ENABLED` mặc định là true.
- Khi hàng đợi hết thời gian, luồng đang gọi LLM không bị dừng, nên có thể chạy song song với job sau.
- Vị trí trong hàng đợi không tính job đang chạy.
- Tệp tải lên được đọc hết vào RAM rồi mới kiểm tra dung lượng.

# Plan tuần tới (từ "Kế hoạch tuần tới.pdf")

Thứ tự ưu tiên trong PDF: **1 Websearch → 2 Sửa code bài báo → 3 Bộ evaluation → 4 Báo cáo**. Phần "Sửa code" nằm ở nhóm Task. Deployment (Docker, Kafka) để sau, không nằm trong 3 task này.

Trạng thái: **mục 1 (Websearch) đã xong** (chưa commit): Friendly = chỉ web; Strict = câu trả lời thủ tục + khối "Tra cứu thêm trên web" (bản kết hợp, đã đo A/B, xem `eval/run_websearch_ab.py` và `eval/results/websearch_ab.md`). Cần model instruct (không phải `qwen3:4b`). **2a đã xong** (kết quả cuối mục 2a). **2a, 2b, 2c đã xong** (kết quả cuối từng mục). Còn lại: bộ evaluation (mục 3).

---

## 1. Websearch (làm trước)

Yêu cầu từ PDF: nút websearch trên web; bấm thì chỉ tìm bằng DuckDuckGo rồi trả lời, không qua dataset; áp dụng cho mọi domain; bỏ yêu cầu nguồn `.gov.vn`. Nếu kết hợp được với dataset như ChatGPT mà không tệ hơn thì làm, còn tệ hơn thì giữ ý đầu.

### Nguồn để port: System 1 trong `D:\V10.6` (bản mới nhất; `V10.5` và `reimagine_V10.2.1` là bản cũ)

| File System 1 | Việc | Dòng |
|---|---|---|
| `Backend/mcp_search/engine.py` | `web_search()` gọi `ddgs` (provider `ddgs`); `fetch_page()` đọc trang bằng `trafilatura`; `build_evidence_pack()` chia đoạn, chấm BM25, ghép bằng chứng; có lọc theo `BLOCKED_DOMAINS` và `trust_of()` (chuyện `.gov.vn` nằm ở đây) | 506 |
| `Backend/core/system_websearch.py` | pipeline: hiểu ý → tra cứu → soạn → kiểm chứng (verifier) → viết lại | 164 |
| `Backend/core/evidence.py`, `answer.py`, `verifier.py`, `intent.py` | các bước phụ | |
| `config.py` | `SEARCH_PROVIDER="ddgs"`, `SEARCH_DDGS_BACKEND`, `SEARCH_RESULTS_PER_QUERY`, ... | |
| `Frontend/static/js/chat.js` | nút "Web search" | |
| `requirements.txt` | `ddgs==9.16.0` (chưa cài trong `.venv` của repo merged) | |

### Cách làm (bản nhỏ nhất, chạy được)

1. **Không port nguyên System 1** (nó có MCP server, verifier, intent riêng, kéo theo nhiều phụ thuộc). Chỉ port phần lõi vào `system4/server/websearch.py`:
   - tìm: `ddgs` → top N kết quả (tiêu đề, URL, đoạn trích);
   - tùy chọn đọc trang: `trafilatura` cho top 2–3 URL, cắt đoạn gần câu hỏi nhất (copy `_passages` + `_best_window`);
   - bỏ `BLOCKED_DOMAINS` / `trust_of` / yêu cầu `.gov.vn`.
2. Thêm `websearch: bool` vào body chat của S4. Khi `true`: bỏ qua Planner, Strict, dataset; đưa bằng chứng vào prompt của model Friendly; trả lời kèm danh sách nguồn (tiêu đề + URL).
3. Giao diện: nút bật/tắt cạnh ô nhập (`system4/web/static/js/app.js`, `index.html`). Ghi rõ "câu hỏi được gửi ra internet".
4. Thông báo lỗi rõ khi không có mạng, timeout 8–10 s, thử lại 1 lần khi DuckDuckGo giới hạn tốc độ. Không có kết quả thì nói thật là không có, không bịa.
5. Áp dụng cho mọi domain: nút nằm ở khung chat chung, không gắn với domain.
6. Bản kết hợp dataset (làm sau, chỉ khi bản 1–5 xong): lấy kết quả dataset + web cùng đưa vào prompt. So sánh A/B trên khoảng 20 câu (web thuần vs kết hợp). Tệ hơn thì giữ bản web thuần, ghi lý do vào báo cáo.

### Kiểm tra xong
- Test: gọi `websearch.search("...")` bằng mạng thật, và một test mock (không mạng) cho phần chia đoạn/ghép bằng chứng.
- Bật nút, hỏi một câu thời sự → có nguồn; tắt mạng → có thông báo lỗi, không treo.

Ước lượng: 0,5–1 ngày.

---

## 2. Sửa code (nhóm Task trong PDF)

Làm từ rẻ đến đắt.

### 2a. Nhỏ, làm ngay
| Việc | Cách |
|---|---|
| Lưu 1–2 thủ tục (8 là nhiều) | giảm giới hạn thủ tục nhớ trong cấu hình S3/S4; hiện `MEMORY_MAX_ITEMS=50` là cho "điều nhớ", thủ tục lưu là mục riêng, cần tìm đúng chỗ |
| Tin nhắn lưu tạm 3 cái, hơn thì xóa, giới hạn dung lượng | tham số mới trong `system4/server/config.py` (hiện thị trong ⚙), xóa khi vượt |
| 👍/👎 | bảng `feedback` trong `schema.sql`, 2 nút dưới mỗi câu trả lời, API `POST /feedback` |
| Xác nhận lỗi nạp lại model vào GPU | đo `ollama ps` + thời gian lần gọi 1 và lần gọi 2 với cùng model, đổi qua lại model "Suy nghĩ kỹ"; ghi số vào báo cáo; sửa nếu đúng (keep_alive, cùng `num_ctx`, `OLLAMA_MAX_LOADED_MODELS`) |

**Kết quả 2a (đã làm):**
- Thủ tục nhớ trong một hội thoại Strict: `SHOWN_MAX=2` (trước đó không giới hạn, tới 8). Biến môi trường `S3_SHOWN_MAX`.
- Ngữ cảnh lượt sau: `HISTORY_MESSAGES=3` tin gần nhất (trước: 10). Tin cũ vẫn lưu trong DB để hiển thị, chỉ không vào ngữ cảnh. Chưa xóa hẳn tin khỏi DB (xóa sẽ làm mất lịch sử trên màn hình); nếu thầy muốn xóa thật thì nói.
- Dung lượng: `turn_traces` giữ `TRACE_KEEP=300` lượt gần nhất. Friendly đã có `TRACE_KEEP` và `FRIENDLY_HISTORY_MESSAGES` ở ⚙. Test: `server/tests/cap_test.py`.
- 👍/👎: đã có sẵn từ trước (cột `messages.feedback` và `strict_nodes.feedback`, 2 nút dưới mỗi câu). Chưa có trang xem tổng hợp, sẽ gộp vào thống kê của 2b.
- Ollama: `eval/measure_ollama_reload.py`. Trên GTX 1660 Super 6 GB: gọi lần lượt `qwen3:4b-instruct` → `qwen3:4b` → bge-m3, mỗi lần đổi giữa hai model trả lời mất 6,8–7,0 giây nạp (load_duration), bge-m3 không bị đẩy ra (0,13 giây). Cùng một model gọi lại: 0,16 giây. Nguyên nhân: mỗi model chiếm 3,8 GB VRAM (có KV cache 8192) nên card chỉ chứa một. Cách sửa: dùng một model cho Friendly, Strict (qua hook) và khối web (mặc định đã cùng instruct); chỉ nút "Suy nghĩ kỹ" (`THINK_MODEL=qwen3:4b`) còn đổi model, ghi trong help của ⚙.

### 2b. Vừa
| Việc | Cách |
|---|---|
| Phân loại user: Cán bộ / Dev / User | `users.role` hiện chỉ `dev \| user`; thêm `can_bo`; "Người dân" = `user` bị giới hạn dataset; cập nhật `admin.py`, `auth.py` |
| Intent "liệt kê" | cho bịa trước theo PDF; chưa làm text-to-SQL (ghi chú cuối PDF: "Hồng: Đừng Implement") |
| UI quản lý user cho dev + thống kê thủ tục được hỏi nhiều nhất | `admin.py` đã có list/sửa user; thêm đếm từ bảng `traces` theo thủ tục |
| Nhiều worker, xử lý song song (thầy không chịu tuần tự) | hiện S3 `QUEUE_CONCURRENCY=1`, S4 `Semaphore(1)`; nâng số này + `OLLAMA_NUM_PARALLEL`; đo thông lượng trên card 6 GB trước khi chốt |

**Kết quả 2b (đã làm):**
- Loại tài khoản: `dev | can_bo | user` (`db.ROLES`; hiện tên Dev / Cán bộ / Người dân). Admin tạo và đổi được; trang chat hiện nhãn. Việc "Cán bộ xem full dataset, Người dân bị giới hạn" cần cơ chế khóa dataset/domain nên nằm ở 2c.
- Ý "liệt kê" (`orchestrator._list_request`): bắt "liệt kê các thủ tục…", "danh sách thủ tục…", "có bao nhiêu thủ tục…", "có những thủ tục…". Trả 10 thủ tục gần nhất, nói rõ chưa đầy đủ, không đếm (theo PDF: chưa làm SQL). Test: `server/tests/list_intent_test.py`.
- Thống kê: bảng `proc_stats` (đếm mỗi lần một thủ tục được trả lời trực tiếp, không lưu nội dung câu hỏi), API `GET /s4/admin/stats`, tab "Thống kê" ở trang Quản trị (top thủ tục, 👍/👎 Friendly và Strict, số tài khoản theo loại). UI quản lý người dùng đã có sẵn từ trước (tạo, khóa, đặt lại mật khẩu, xóa, xem hội thoại). Test: `system4/tests/test_roles_stats.py`.
- Song song: thêm cấu hình `S3_QUEUE_CONCURRENCY` và `S4_CONCURRENCY` (mặc định 1) và khóa quanh Planner (nó dùng chung một kết nối SQLite). **Đo thực tế (`eval/measure_parallel.py`, GTX 1660 Super 6 GB, 4 yêu cầu cùng lúc, qwen3:4b-instruct):** `OLLAMA_NUM_PARALLEL=1` tổng 5,3 s (60 token/s); `=2` tổng 7,6 s (42 token/s); `=4` tổng 15,5 s (21 token/s). Chạy song song trên card 6 GB còn chậm hơn tuần tự (KV cache nhân lên, tràn VRAM). Kết luận: giữ 1 trên máy này; song song chỉ đáng bật trên card lớn hơn (nhớ đặt cùng số cho `OLLAMA_NUM_PARALLEL`).

### 2c. Lớn: hệ thống domain
- **Domain cứng**: không xóa được, luật riêng, chỉ dev thêm, có thể có dataset riêng. System 3 đổi tên thành "Domain thủ tục".
- **Domain mềm**: kiểu Friendly, user và dev thêm được, không có dataset lưu lâu dài cho user.
- Mỗi domain: mặc định xử lý như Friendly, có thể thêm Guardrail (prompt gửi thẳng cho AI ngay trước lúc soạn trả lời). Dataset của domain này không hiện ở domain khác.
- Dev chuyển domain mềm ↔ cứng; khóa một số domain/dataset cho `can_bo`.
- Giao diện: thay switch Strict|Friendly bằng Thủ tục|Du lịch|Lịch sử; làm cả hai: ghim domain và dropdown cho các domain còn lại.
- Mô hình dữ liệu đề xuất: bảng `domains(id, name, kind[hard|soft], guardrail, allowed_roles, pinned)`; `datasets.domain_id`; `conversations.domain_id`.
- Làm cuối cùng, sau khi 2a và 2b xong.

**Kết quả 2c (đã làm):**
- Bảng `domains(id, name, kind hard|soft, engine strict|friendly, guardrail, locked, user_upload, owner_id)`, `domain_pins(user_id, domain_id, pinned)`; cột `conversations.domain_id`, `datasets.domain_id`, `datasets.locked`. DB cũ tự nâng cấp: hội thoại và dataset cũ về domain 2.
- Có sẵn 2 domain, không xóa được: **1 "Thủ tục"** (cứng, engine strict = System 3, đổi tên từ "Strict") và **2 "Trò chuyện chung"** (mềm, giữ nguyên hành vi Friendly cũ, người dùng vẫn tải dữ liệu riêng).
- **Cứng**: chỉ dev thêm; không xóa được; dataset do dev tải, dùng chung cho mọi người được phép; người dùng thường không tải được. **Mềm**: user và dev thêm; user tạo thì chỉ mình dùng (tối đa 10); dataset luôn riêng từng người và chỉ tải được khi dev bật `user_upload` cho domain đó (dev luôn tải được). Dev đổi cứng ↔ mềm (chặn khi domain có dữ liệu riêng của người dùng, vì sẽ thành dùng chung; Thủ tục luôn cứng).
- **Guardrail** của domain: thêm vào lời dặn cho AI ngay trước khi soạn câu trả lời (đã thử với model thật: guardrail "Luôn xưng em" thì AI mở câu bằng "Em có thể giúp bạn…"). Dataset chỉ hiện và chỉ được tìm trong domain của nó.
- **Khóa**: dev khóa domain (kể cả Thủ tục) hoặc từng dataset → chỉ `dev` và `can_bo` thấy và dùng; `user` (Người dân) không thấy, hội thoại cũ trong domain khóa bị ẩn, gọi thẳng API bị 403/404 (kể cả `/chat` của System 3).
- **Giao diện**: thanh chọn domain thay cho switch Strict|Friendly: 4 domain đầu được ghim mặc định, các domain còn lại nằm trong ô "Khác…"; nút "Domain" mở trang quản lý (ghim/bỏ ghim từng người, thêm, sửa tên + guardrail, xóa domain mềm; dev thêm: cứng/mềm, khóa, cho người dùng tải dữ liệu). Hộp "Dữ liệu" theo domain đang chọn; dev có nút Khóa/Mở khóa từng bộ. Nhãn hội thoại hiện tên domain; bấm một hội thoại thì chuyển sang domain của nó.
- Test: `system4/tests/test_domains.py` (model giả); thử giao diện thật trên cổng riêng (đã tắt).
- Chưa làm: trang Quản trị chưa có cột domain cho dataset; domain mềm của user không có dataset dùng chung (đúng theo PDF); đổi domain của một hội thoại có sẵn chưa hỗ trợ (hội thoại giữ domain lúc tạo).

---

## 3. Bộ evaluation hoàn thiện

Nền sẵn có: `eval/run_pseudo.py`, các bộ `cases_*.jsonl`, `eval/README.md`, `H*_ASSUMPTIONS.md`.

1. **Tiêu chí chấm** (viết `eval/CRITERIA.md`):
   - truy xuất: top-1, top-3 đúng thủ tục;
   - hành vi: hỏi lại đúng lúc, từ chối đúng, không bịa;
   - chất lượng trả lời (RAGAS): faithfulness, answer relevancy, context precision, context recall;
   - tốc độ: p50/p95 theo loại câu (đơn giản, phức tạp), có và không GPU.
2. **Golden set theo domain**: chuẩn hóa các bộ có sẵn về một định dạng chung (`question, domain, expected, type`); mỗi domain một bộ.
3. **Bộ test lớn dùng chung cho nhiều dataset**: danh sách chủ đề (giải thích, áp dụng, so sánh, liệt kê, ...), khuôn sinh câu hỏi áp lên từng dataset.
4. **Kiểm chứng dataset**: lấy mẫu khoảng 50 bản ghi, đối chiếu nguồn gốc, ghi tỷ lệ đúng và nguồn lấy.
5. **RAGAS** cần LLM làm giám khảo; dùng Ollama local thì chậm và kém tin cậy, ghi rõ hạn chế trong báo cáo.
6. Đầu ra: một báo cáo số liệu (bảng điểm theo tiêu chí và theo domain), chạy lại được bằng một lệnh.

Ước lượng: 2–3 ngày. Làm trước các bước 1 và 4 (rẻ, có giá trị nhất cho báo cáo).

---

## 4. Câu hỏi thầy cần trả lời (để đưa vào báo cáo thứ 6)

| Câu hỏi | Trạng thái |
|---|---|
| Hàng đợi dùng thư viện gì? | Không dùng thư viện ngoài: S3 `server/core/queue.py` tự viết; S4 `asyncio.Semaphore`. Kafka/Redis là hướng deploy, chưa làm |
| Chậm do Ollama nạp lại model vào GPU? | Đúng, đã đo: đổi qua lại giữa 2 model trả lời thì mỗi lần nạp lại khoảng 7 giây; cùng một model thì 0,16 giây (xem kết quả 2a) |
| Xác định user ngầm xác định thủ tục hay gợi ý? | Ngầm: Planner luật chọn khi đủ chắc, mơ hồ thì hỏi lại (đúng khoảng 45% ở bộ mù) |
| Chưa có GPU thì thế nào? | Chưa đo; Strict với `S3_USE_LLM=0` chạy hoàn toàn trên CPU |
| Câu phức tạp mất bao lâu? | Chưa có số, đo ở bước 3 |
| Dataset có đúng không, benchmark lấy từ đâu? | Bộ DEV/ctx/synth/p* do nhóm tự viết và đã tune; HOLDOUT/pseudo_real là bộ mù do agent soạn từ giả định; chưa có kiểm chứng độc lập (xem 3.4) |
| Vẽ lại kiến trúc (lưu ở đâu, mở web bằng gì, hàng đợi) | FastAPI + uvicorn, giao diện HTML/JS tĩnh, SQLite + FTS5, Qdrant local mode, Ollama (LLM + bge-m3), reranker bge-reranker-v2-m3 (torch). Có 2 ảnh kiến trúc ở thư mục gốc làm nền |
| "Bao nhiêu thủ tục giá 20k" | LLM không đếm được; cách đúng là sinh SQL hoặc bảng fact; theo PDF thì chưa implement |

---

## Đề xuất thứ tự

1. Websearch (mục 1).
2. 2a (nhỏ) và đo vấn đề Ollama.
3. Evaluation (mục 3), song song với 2b.
4. 2c (domain) làm cuối.

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

**Kết quả (bước 1 và 4 đã làm, các bước còn lại chưa):**
- Bước 1: [`eval/CRITERIA.md`](../eval/CRITERIA.md) gom tiêu chí về script có sẵn; chỉ rõ chỗ còn thiếu: RAGAS (chưa có script) và tốc độ p50/p95 theo loại câu, có/không GPU.
- Bước 4: `eval/sample_dataset_check.py` lấy mẫu 50 bản ghi (phân tầng theo lĩnh vực, seed 7), ghi phiếu `eval/results/dataset_check_sheet.md`; `--score` tính tỷ lệ đúng sau khi người kiểm điền. **Chưa có tỷ lệ đúng**: cổng `dichvucong.gov.vn` tải chi tiết bằng JavaScript, đọc tự động không ra nội dung, nên cần người đối chiếu tay.
- Tốc độ (`eval/measure_latency.py`, kết quả trong bảng ở CRITERIA.md mục 4): câu thường p50 60-80 ms, p95 ≤ 200 ms (LLM tắt hay bật đều thế); câu kích hoạt bước sinh chữ bằng LLM p50 3,2 s, p95 6,3 s. Trả lời câu hỏi thầy "câu phức tạp mất bao lâu": phức tạp về ý vẫn vài chục ms, chậm là do bước LLM sinh chữ. Chưa đo trên máy không GPU thật.
- Bước 2 (xong): `eval/build_golden.py` gom 1.323 ca của mọi bộ có sẵn về một định dạng (`id, domain, type, turns, question, expected{behavior, tasks[{proc_ids, fields}]}, source, status`) trong `eval/golden/thu-tuc.jsonl`; `eval/run_golden.py` chấm. Domain "Trò chuyện chung" chưa có golden set (hội thoại tự do không có đáp án đúng/sai kiểm được): `golden/tro-chuyen-chung.jsonl` để rỗng, ghi rõ chỗ thiếu.
- Bước 3 (xong): `eval/build_template_set.py` sinh 430 câu từ 12 khuôn chủ đề áp lên bản ghi thủ tục (`golden/template_thu-tuc.jsonl`). Mới nối với dataset thủ tục; dataset người dùng tải ở System 4 chưa nối (chưa có đáp án chuẩn). Chủ đề "áp dụng/điều kiện" chưa sinh vì chưa có đáp án tự động.
- Bước 5 (xong ở mức thử nghiệm, **kết quả chưa đủ tin cậy**): `eval/run_ragas_lite.py` cài lại 4 chỉ số RAGAS bằng giám khảo Ollama (không dùng thư viện `ragas`), kèm hai ca đối chứng âm để kiểm giám khảo. Kết quả ở bảng F.
- Chưa làm: bảng E (dữ liệu đúng nguồn).

### Bảng benchmark (chạy 2026-10-13, `S3_USE_LLM=0`, Planner luật, mỗi bảng một lệnh)

**A. Golden set Thủ tục theo status** — `python run_server.py eval/run_golden.py thu-tuc --by status`. Số chính thức là hàng `blind`; `dev` luôn cao hơn vì đã tune.

| status | số ca | hành vi đúng | top-1 | top-3 | đúng trường | đủ ý (nhiều thủ tục) | hỏi lại đúng | từ chối đúng |
|---|---|---|---|---|---|---|---|---|
| blind | 553 | 431/553 (78%) | 295/406 (73%) | 323/406 (80%) | 199/388 (51%) | 8/10 (80%) | 40/86 (47%) | 52/58 (90%) |
| dev | 641 | 626/641 (98%) | 558/567 (98%) | 562/567 (99%) | 368/373 (99%) | 25/28 (89%) | 23/26 (88%) | 42/46 (91%) |
| holdout-used | 129 | 113/129 (88%) | 92/102 (90%) | 94/102 (92%) | 62/79 (78%) | 13/17 (76%) | 3/8 (38%) | 13/16 (81%) |

**B. Golden set Thủ tục theo bộ gốc** — `--by source`

| source | số ca | hành vi đúng | top-1 | top-3 | đúng trường | đủ ý (nhiều thủ tục) | hỏi lại đúng | từ chối đúng |
|---|---|---|---|---|---|---|---|---|
| cases.jsonl | 590 | 577/590 (98%) | 503/510 (99%) | 506/510 (99%) | 362/369 (98%) | 34/38 (89%) | 24/29 (83%) | 45/47 (96%) |
| cases_ctx.jsonl | 118 | 113/118 (96%) | 109/112 (97%) | 110/112 (98%) | 43/44 (98%) | - | - | 4/6 (67%) |
| cases_h2.jsonl | 62 | 49/62 (79%) | 38/47 (81%) | 40/47 (85%) | 25/39 (64%) | 4/7 (57%) | 2/5 (40%) | 6/9 (67%) |
| cases_h3.jsonl | 88 | 75/88 (85%) | 51/67 (76%) | 56/67 (84%) | 44/57 (77%) | 8/10 (80%) | 2/6 (33%) | 12/12 (100%) |
| cases_h4.json | 106 | 90/106 (85%) | 60/77 (78%) | 67/77 (87%) | 35/77 (45%) | - | 10/16 (62%) | 13/13 (100%) |
| cases_h5.json | 111 | 86/111 (77%) | 58/81 (72%) | 62/81 (77%) | 40/81 (49%) | - | 12/20 (60%) | 9/10 (90%) |
| cases_h6.json | 126 | 93/126 (74%) | 62/87 (71%) | 70/87 (80%) | 53/87 (61%) | - | 11/28 (39%) | 8/11 (73%) |
| cases_pseudo_real.json | 42 | 34/42 (81%) | 22/30 (73%) | 23/30 (77%) | 13/30 (43%) | - | 3/6 (50%) | 6/6 (100%) |
| cases_pseudo_real2.json | 34 | 26/34 (76%) | 22/28 (79%) | 23/28 (82%) | 5/28 (18%) | - | 0/3 (0%) | 2/3 (67%) |
| cases_pseudo_real3.json | 36 | 17/36 (47%) | 12/28 (43%) | 14/28 (50%) | 9/28 (32%) | - | 1/6 (17%) | 1/2 (50%) |
| cases_team.json | 10 | 10/10 (100%) | 8/8 (100%) | 8/8 (100%) | - | - | 1/1 (100%) | 1/1 (100%) |

Ghi chú A, B:
- `blind` = HOLDOUT-3, h4, h5, h6, pseudo_real 1-3, bộ team. Bộ mù **chính thức** theo docs/EVAL.md là h4 (top-1 78%, hành vi 85%, hỏi lại 10/16) và pseudo_real 2. Số hiện tại của pseudo_real 2 là top-1 22/28, hành vi 26/34, còn docs/EVAL.md ghi 19/28 và 23/34: chưa tìm nguyên nhân lệch.
- pseudo_real 3 thấp nhất (hành vi 47%); chưa xem lỗi (xem lỗi bộ mù sẽ làm nó mất tính mù).
- Cột "đúng trường" của các bộ blind kém tin hơn dev: nhãn trường trong các file đó viết tay, tên khác (đã đổi tên `documents/fee/place/time`; `conditions` không có trường tương ứng nên luôn tính lệch).
- `holdout-used` = HOLDOUT cũ + h2, đã bị xem lỗi nên không còn là bộ mù.

**C. Bộ khuôn câu hỏi theo chủ đề** — `python run_server.py eval/build_template_set.py` rồi `python run_server.py eval/run_golden.py template_thu-tuc --by type`. Câu dùng nguyên tên thủ tục nên **dễ hơn câu người dân gõ**; dùng để so các chủ đề với nhau và bắt hồi quy, không phải số chính thức. Chỉ lấy thủ tục cấp xã, không ngành dọc, họ một dạng.

| type | số ca | hành vi đúng | top-1 | top-3 | đúng trường | đủ ý (nhiều thủ tục) | hỏi lại đúng | từ chối đúng |
|---|---|---|---|---|---|---|---|---|
| address | 30 | 29/30 (97%) | 30/30 (100%) | 30/30 (100%) | 15/30 (50%) | - | - | - |
| compare-khac-gi | 20 | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | - | 16/20 (80%) | - | - |
| compare-so-sanh | 20 | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | - | 20/20 (100%) | - | - |
| components | 40 | 39/40 (98%) | 38/40 (95%) | 39/40 (98%) | 39/40 (98%) | - | - | - |
| explain | 40 | 39/40 (98%) | 38/40 (95%) | 39/40 (98%) | 18/40 (45%) | - | - | - |
| fees | 40 | 39/40 (98%) | 40/40 (100%) | 40/40 (100%) | 36/40 (90%) | - | - | - |
| legal | 40 | 39/40 (98%) | 40/40 (100%) | 40/40 (100%) | 35/40 (88%) | - | - | - |
| list | 40 | 32/40 (80%) | - | - | - | - | - | - |
| multi_field | 40 | 39/40 (98%) | 39/40 (98%) | 40/40 (100%) | 37/40 (92%) | - | - | - |
| online | 40 | 39/40 (98%) | 39/40 (98%) | 39/40 (98%) | 33/40 (82%) | - | - | - |
| steps | 40 | 39/40 (98%) | 40/40 (100%) | 40/40 (100%) | 36/40 (90%) | - | - | - |
| time | 40 | 39/40 (98%) | 40/40 (100%) | 40/40 (100%) | 35/40 (88%) | - | - | - |

liệt kê: 32/40 câu có trả danh sách; trung bình 12% mục trong danh sách đúng lĩnh vực được hỏi.

Điều bảng C cho thấy:
- Chủ đề thường (hồ sơ, phí, thời hạn, nơi nộp, trình tự, căn cứ, trực tuyến): chọn đúng thủ tục 95-100%.
- **So sánh**: "So sánh A và B" đủ ý 20/20. "A khác gì so với B" lúc đầu 0/20 (không tách được hai vế vì liên từ nằm sau cụm "khác gì"); đã sửa `retrieval/refs.py` (`split_compare`), giờ 16/20. Bảng C ở trên là số SAU sửa; test `server/tests/compare_cue_test.py`.
- **Liệt kê**: 32/40 câu có trả danh sách (8 câu không khớp mẫu), nhưng chỉ 12% mục đúng lĩnh vực được hỏi: hệ thống chưa có truy vấn theo lĩnh vực, chỉ liệt kê thủ tục gần câu hỏi nhất (đúng như đã ghi trong câu trả lời).
- Chủ đề "explain" (45%) và "address" (50%) đúng trường thấp: câu "Giải thích giúp mình thủ tục X" hay bị hiểu thành hỏi mục khác, và câu hỏi nơi nộp thường kèm thêm `components`. Chưa sửa vì chưa rõ có phải lỗi.

**D. Tốc độ** (đo bằng `eval/measure_latency.py`, p50 / p95, ms; n = 26–40 câu mỗi loại nên **p95 dao động mạnh giữa các lần chạy**: lần chạy lại bằng `eval/report.py --llm` ra p95 của câu phức tạp khi bật LLM là 3.619 ms thay vì 1.624 ms, còn p50 gần như không đổi. Tin p50 hơn p95)

| Loại câu | LLM tắt (chỉ CPU) | LLM bật (mặc định) |
|---|---|---|
| đơn giản | 82 / 122 | 78 / 196 |
| phức tạp (nhiều ý hoặc nhiều lượt) | 63 / 122 | 59 / 1.624 |
| hỏi lại | 85 / 105 | 72 / 143 |
| ngoài phạm vi | 57 / 113 | 52 / 85 |
| có bước sinh chữ bằng LLM | không có | **3.192 / 6.268** |

**E. Dữ liệu đúng nguồn**: **chưa có số**. Phiếu 50 bản ghi nằm ở `eval/results/dataset_check_sheet.md` (tạo bằng `python eval/sample_dataset_check.py`), chờ người đối chiếu tay vì cổng `dichvucong.gov.vn` không đọc tự động được; chấm bằng `--score`. Tạm bỏ qua theo yêu cầu.

**F. RAGAS-lite** — `python run_server.py eval/run_ragas_lite.py --n 30` (~35 phút trên GTX 1660 SUPER; không nằm trong `report.py` vì quá chậm). Giám khảo: qwen3:4b qua Ollama, nhiệt độ 0. 30 ca: 15 ca có bước sinh chữ bằng LLM (bộ composer) + 15 ca khuôn một thủ tục; hệ thống chạy cấu hình mặc định (LLM bật).

| Chỉ số | Cả 30 ca | Ca composer (LLM sinh chữ) | Ca khuôn (luật) |
|---|---|---|---|
| faithfulness | 0,90 | 0,93 | 0,88 |
| answer relevancy | 0,43 | 0,33 | 0,53 |
| context precision | 0,69 | 0,61 | 0,78 |
| context recall | 0,98 | 0,99 | 0,97 |

**Kiểm giám khảo bằng đối chứng âm** (cùng 30 ca):

| Phép thử | Kết quả | Đọc |
|---|---|---|
| Chèn một ý bịa ("miễn phí hoàn toàn, giải quyết trong 1 giờ") vào câu trả lời; faithfulness phải giảm | giảm ở **9/30** ca; faithfulness trung bình chỉ giảm từ 0,90 xuống 0,84 | Giám khảo **bỏ sót 70% ý bịa**. Điểm faithfulness 0,90 chỉ là cận trên, không chứng minh hệ thống không bịa |
| Ghép câu trả lời với câu hỏi của ca khác; relevancy phải giảm | về 0 ở mọi ca (trung bình 0,0) | Phân biệt được lạc đề rõ rệt |
| Relevancy trên câu hỏi đúng | 17/30 ca bị chấm 0, không ca nào ra 0,5 | Giám khảo chỉ cho 0 hoặc 1. Nhiều ca chấm 0 là câu trả lời tốt (ví dụ "So sánh đăng ký khai sinh và đăng ký khai tử", câu trả lời 3.000 ký tự). Với hội thoại nhiều lượt, giám khảo chỉ thấy câu hỏi cuối ("không phải, ý mình hỏi thường trú cơ") nên không đủ ngữ cảnh |

Kết luận bước 5:
- **Không dùng điểm faithfulness và answer relevancy của giám khảo 4B để báo cáo.** Faithfulness bỏ sót phần lớn ý bịa; relevancy chấm sai nhiều ca đúng. Đúng như dự đoán trong kế hoạch (Ollama local chậm và kém tin cậy).
- **Context recall 0,98 là số gần như tất nhiên**: tham chiếu lấy từ chính các trường DB mà hệ thống đã lấy ra, nên chỉ cho biết truy xuất đúng thủ tục và đúng trường. Không đo chất lượng chữ viết của câu trả lời.
- **Context precision (0,69)** dùng được ở mức tham khảo: nó chỉ đòi giám khảo so từng đoạn với câu hỏi. Chưa được kiểm bằng đối chứng riêng, nên chưa nên đọc khác biệt giữa ca composer (0,61) và ca khuôn (0,78) là có ý nghĩa.
- **Thay thế dùng được:** chỉ số luật không cần LLM, đã có sẵn: "bịa số", "nói không công bố", trích nguồn (`run.py`), đúng trọng tâm (`run_concise.py`) và `score_composer.py` cho bước sinh chữ. Số của chúng đáng tin hơn điểm RAGAS-lite này.
- Muốn có RAGAS đáng tin: cần giám khảo mạnh hơn (model lớn hơn hoặc API) và câu trả lời mẫu thật. Chưa làm vì ngoài phạm vi máy hiện tại.
- Điểm chưa tối ưu của tôi: tách ý và tách "tham chiếu" dùng model 4B nên chính bước tách cũng có thể sai; không kiểm riêng.

### Nghiệm thu mục 3 (rút ra từ các bảng A–D)

**Trạng thái theo từng bước của mục 3**

| Bước | Kết quả |
|---|---|
| 1. Tiêu chí chấm | Xong: `eval/CRITERIA.md` |
| 2. Golden set theo domain | Xong cho Thủ tục (1.323 ca); Trò chuyện chung chưa có |
| 3. Bộ khuôn câu hỏi dùng chung | Xong cho dataset thủ tục (430 ca); chưa nối dataset người dùng tải lên |
| 4. Kiểm chứng dataset | Có phiếu 50 bản ghi; chưa có tỷ lệ đúng (bảng E, tạm bỏ qua) |
| 5. RAGAS | Làm thử: `eval/run_ragas_lite.py` (bảng F). Giám khảo 4B không đủ tin cậy cho faithfulness và relevancy; chỉ số luật thay thế |
| 6. Báo cáo một lệnh | Xong: `python eval/report.py [--llm]` in bảng A–D và ghi `eval/results/report.md` (~2 phút, `--llm` ~4 phút) |

**Kết luận từ số liệu**

1. **Chất lượng khác nhau rất xa giữa bộ đã tune và bộ mù.** Hành vi đúng: dev 98%, blind 78%. top-1: dev 98%, blind 73%. Báo cáo cần nêu số blind; số dev chỉ để theo dõi hồi quy.
2. **Chỗ yếu nhất ở bộ mù là hỏi lại.** Hỏi lại đúng chỉ 47% (40/86) ở blind, so với 88% ở dev. Từ chối đúng tốt hơn nhiều: 90% (52/58) ở blind.
3. **Khi câu hỏi nêu rõ tên thủ tục, hệ thống chọn đúng thủ tục 95–100%** ở mọi chủ đề thường (hồ sơ, phí, thời hạn, nơi nộp, trình tự, căn cứ, trực tuyến), kể cả khi đổi cách hỏi. Bộ mù tụt khoảng 20–25 điểm so với bộ khuôn. Giả thuyết: do câu người dân gõ (viết tắt, không dấu, kể lể) chứ không phải kho dữ liệu; chưa kiểm chứng vì xem lỗi bộ mù sẽ làm nó mất tính mù.
4. **Có hai lỗi thật, tìm được nhờ bộ khuôn:**
   - So sánh bằng cụm "A khác gì so với B" chỉ nhận ra một thủ tục (0/20 đủ ý), trong khi "So sánh A và B" đạt 20/20. **Đã sửa** ở `split_compare`, chạy lại: 16/20. 4 ca còn lại chưa xem. `run_all --quick` giữ nguyên 27/33 (cùng 6 mục trượt do commit retrieval của Dan, không thêm mục mới).
   - Liệt kê theo lĩnh vực chỉ đúng 12% mục: hệ thống chưa có truy vấn theo lĩnh vực. Đã được thầy ghi nhận là chưa làm (câu hỏi "bao nhiêu thủ tục giá 20k").
5. **Tốc độ không phải điểm nghẽn ở phần lớn câu**: p50 chỉ 52–85 ms ở mọi loại câu thường. p95 thường ≤ 200 ms, nhưng với LLM bật có lần ra 1,6 s, có lần 3,6 s ở câu phức tạp (mẫu nhỏ, p95 không ổn định). Câu đi qua bước sinh chữ bằng LLM chậm nhất: p50 3,2 s, p95 6,3 s. Truy xuất không phải chỗ cần tối ưu; muốn giảm độ trễ thì giảm số câu phải qua LLM.
6. **Chạy không GPU:** với `S3_USE_LLM=0`, Strict chạy trên CPU và nhanh bằng chế độ có LLM ở câu thường. Cái mất là câu trả lời không được viết lại bằng LLM. Chưa thử trên máy không GPU thật.

**Hạn chế phải ghi trong báo cáo**

- Bộ dev, ctx, khuôn do nhóm và agent tự soạn; bộ blind do agent soạn từ giả định, chưa có người ngoài kiểm. Bộ khuôn dùng nguyên tên thủ tục nên dễ hơn câu thật.
- Domain "Trò chuyện chung" (Friendly) chưa có số đo nào.
- Nhãn trường của các bộ blind viết tay, tên khác nhau; cột "đúng trường" ở đó kém tin hơn ở dev.
- Số pseudo_real 2 chạy lại (top-1 22/28) khác số cũ trong `docs/EVAL.md` (19/28); chưa tìm nguyên nhân.
- Tỷ lệ dữ liệu đúng nguồn chưa có (bảng E).
- Bộ chấm chạy với Planner luật và `S3_USE_LLM=0`; chưa đo Planner bằng LLM; RAGAS chỉ thử với giám khảo 4B kém tin cậy (bảng F), chưa có điểm RAGAS dùng được.

**Việc nên làm tiếp (theo giá trị / công sức)**

1. ~~Thêm "khác gì so với" vào bộ nhận ý so sánh~~ (đã làm, 0/20 lên 16/20) và ~~báo cáo một lệnh~~ (đã làm: `eval/report.py`).
2. Điền phiếu 50 bản ghi để có bảng E.
3. Tìm nguyên nhân hỏi lại chỉ đúng 47% ở bộ mù (chỉ xem nhóm lỗi chung, theo quy tắc không tune trên bộ mù trong `docs/EVAL.md`).
4. ~~Bước 5 (RAGAS)~~ đã thử, kết luận ở bảng F: muốn số RAGAS đáng tin cần giám khảo mạnh hơn.
5. Nối dataset người dùng tải lên ở System 4 vào bộ khuôn, cho domain mềm.
6. Xem 4 ca so sánh còn trượt (bảng C) và các ca explain/address đúng trường thấp.

---

## 4. Câu hỏi thầy cần trả lời (để đưa vào báo cáo thứ 6)

| Câu hỏi | Trạng thái |
|---|---|
| Hàng đợi dùng thư viện gì? | Không dùng thư viện ngoài: S3 `server/core/queue.py` tự viết; S4 `asyncio.Semaphore`. Kafka/Redis là hướng deploy, chưa làm |
| Chậm do Ollama nạp lại model vào GPU? | Đúng, đã đo: đổi qua lại giữa 2 model trả lời thì mỗi lần nạp lại khoảng 7 giây; cùng một model thì 0,16 giây (xem kết quả 2a) |
| Xác định user ngầm xác định thủ tục hay gợi ý? | Ngầm: Planner luật chọn khi đủ chắc, mơ hồ thì hỏi lại (đúng khoảng 45% ở bộ mù) |
| Chưa có GPU thì thế nào? | Strict với `S3_USE_LLM=0` chạy trên CPU: p50 ~70 ms, p95 ~120 ms trên máy này; chưa thử máy không GPU thật |
| Câu phức tạp mất bao lâu? | Câu nhiều ý/nhiều lượt p50 ~60 ms; câu cần LLM sinh chữ p50 3,2 s, p95 6,3 s (`eval/measure_latency.py`, CRITERIA.md mục 4) |
| Dataset có đúng không, benchmark lấy từ đâu? | Bộ DEV/ctx/synth/p* do nhóm tự viết và đã tune; HOLDOUT/pseudo_real là bộ mù do agent soạn từ giả định; chưa có kiểm chứng độc lập (xem 3.4) |
| Vẽ lại kiến trúc (lưu ở đâu, mở web bằng gì, hàng đợi) | FastAPI + uvicorn, giao diện HTML/JS tĩnh, SQLite + FTS5, Qdrant local mode, Ollama (LLM + bge-m3), reranker bge-reranker-v2-m3 (torch). Có 2 ảnh kiến trúc ở thư mục gốc làm nền |
| "Bao nhiêu thủ tục giá 20k" | LLM không đếm được; cách đúng là sinh SQL hoặc bảng fact; theo PDF thì chưa implement |

---

## Đề xuất thứ tự

1. Websearch (mục 1).
2. 2a (nhỏ) và đo vấn đề Ollama.
3. Evaluation (mục 3), song song với 2b.
4. 2c (domain) làm cuối.

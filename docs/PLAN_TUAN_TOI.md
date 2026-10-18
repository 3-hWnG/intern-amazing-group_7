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
- Bước 2 (xong): `eval/build_golden.py` gom 1.352 ca (1.323 ca cũ + 29 lượt real-log) của mọi bộ có sẵn về một định dạng (`id, domain, type, turns, question, expected{behavior, tasks[{proc_ids, fields}]}, source, status`) trong `eval/golden/thu-tuc.jsonl`; `eval/run_golden.py` chấm. Domain "Trò chuyện chung" chưa có golden set (hội thoại tự do không có đáp án đúng/sai kiểm được): `golden/tro-chuyen-chung.jsonl` để rỗng, ghi rõ chỗ thiếu.
- Bước 3 (xong): `eval/build_template_set.py` sinh 430 câu từ 12 khuôn chủ đề áp lên bản ghi thủ tục (`golden/template_thu-tuc.jsonl`). Mới nối với dataset thủ tục; dataset người dùng tải ở System 4 chưa nối (chưa có đáp án chuẩn). Chủ đề "áp dụng/điều kiện" chưa sinh vì chưa có đáp án tự động.
- Bước 5 (xong ở mức thử nghiệm, **kết quả chưa đủ tin cậy**): `eval/run_ragas_lite.py` cài lại 4 chỉ số RAGAS bằng giám khảo Ollama (không dùng thư viện `ragas`), kèm hai ca đối chứng âm để kiểm giám khảo. Kết quả ở bảng F.
- Chưa làm: bảng E (dữ liệu đúng nguồn).

### Bảng benchmark (chạy lại 2026-10-14 trên code hiện tại, `S3_USE_LLM=0`, Planner luật, mỗi bảng một lệnh)

Từ 2026-10-14 mỗi tỷ lệ có khoảng tin cậy Wilson 95% (`a/b (p%, lo%–hi%)`), thêm cột MRR và nDCG@5 (`eval/rank_metrics.py`). Ca một thủ tục: MRR/nDCG tính trên danh sách ứng viên của task đầu, cùng danh sách với top-1 (RR = 1 khi và chỉ khi top-1 đúng). Ca nhiều thủ tục: tính theo từng task kỳ vọng rồi lấy trung bình. Bộ `cases_real_log_v1.json` (29 lượt viết tay kiểu người dùng thật) đã thêm vào golden set với status `holdout-used`, nên hàng `holdout-used` đổi từ 129 lên 158 ca; các hàng `blind` và `dev` không đổi so với bảng cũ.

**A. Golden set Thủ tục theo status** — `python run_server.py eval/run_golden.py thu-tuc --by status`. Số chính thức là hàng `blind`; `dev` luôn cao hơn vì đã tune.

| status | số ca | hành vi đúng | top-1 | top-3 | MRR | nDCG@5 | đúng trường | đủ ý (nhiều thủ tục) | hỏi lại đúng | từ chối đúng |
|---|---|---|---|---|---|---|---|---|---|---|
| blind | 553 | 431/553 (78%, 74%–81%) | 295/406 (73%, 68%–77%) | 323/406 (80%, 75%–83%) | 0.759 | 0.752 | 199/388 (51%, 46%–56%) | 8/10 (80%, 49%–94%) | 40/86 (47%, 36%–57%) | 52/58 (90%, 79%–95%) |
| dev | 641 | 626/641 (98%, 96%–99%) | 558/567 (98%, 97%–99%) | 562/567 (99%, 98%–100%) | 0.987 | 0.976 | 368/373 (99%, 97%–99%) | 25/28 (89%, 73%–96%) | 23/26 (88%, 71%–96%) | 42/46 (91%, 80%–97%) |
| holdout-used | 158 | 135/158 (85%, 79%–90%) | 109/125 (87%, 80%–92%) | 112/125 (90%, 83%–94%) | 0.876 | 0.885 | 78/102 (76%, 67%–84%) | 13/17 (76%, 53%–90%) | 3/10 (30%, 11%–60%) | 16/20 (80%, 58%–92%) |

**B. Golden set Thủ tục theo bộ gốc** — `--by source`

| source | số ca | hành vi đúng | top-1 | top-3 | MRR | nDCG@5 | đúng trường | đủ ý (nhiều thủ tục) | hỏi lại đúng | từ chối đúng |
|---|---|---|---|---|---|---|---|---|---|---|
| cases.jsonl | 590 | 577/590 (98%, 96%–99%) | 503/510 (99%, 97%–99%) | 506/510 (99%, 98%–100%) | 0.987 | 0.982 | 362/369 (98%, 96%–99%) | 34/38 (89%, 76%–96%) | 24/29 (83%, 65%–92%) | 45/47 (96%, 86%–99%) |
| cases_ctx.jsonl | 118 | 113/118 (96%, 90%–98%) | 109/112 (97%, 92%–99%) | 110/112 (98%, 94%–100%) | 0.978 | 0.947 | 43/44 (98%, 88%–100%) | - | - | 4/6 (67%, 30%–90%) |
| cases_h2.jsonl | 62 | 49/62 (79%, 67%–87%) | 38/47 (81%, 67%–90%) | 40/47 (85%, 72%–93%) | 0.812 | 0.825 | 25/39 (64%, 48%–77%) | 4/7 (57%, 25%–84%) | 2/5 (40%, 12%–77%) | 6/9 (67%, 35%–88%) |
| cases_h3.jsonl | 88 | 75/88 (85%, 76%–91%) | 51/67 (76%, 65%–85%) | 56/67 (84%, 73%–91%) | 0.782 | 0.771 | 44/57 (77%, 65%–86%) | 8/10 (80%, 49%–94%) | 2/6 (33%, 10%–70%) | 12/12 (100%, 76%–100%) |
| cases_h4.json | 106 | 90/106 (85%, 77%–90%) | 60/77 (78%, 67%–86%) | 67/77 (87%, 78%–93%) | 0.824 | 0.805 | 35/77 (45%, 35%–57%) | - | 10/16 (62%, 39%–82%) | 13/13 (100%, 77%–100%) |
| cases_h5.json | 111 | 86/111 (77%, 69%–84%) | 58/81 (72%, 61%–80%) | 62/81 (77%, 66%–84%) | 0.743 | 0.742 | 40/81 (49%, 39%–60%) | - | 12/20 (60%, 39%–78%) | 9/10 (90%, 60%–98%) |
| cases_h6.json | 126 | 93/126 (74%, 66%–81%) | 62/87 (71%, 61%–80%) | 70/87 (80%, 71%–87%) | 0.758 | 0.772 | 53/87 (61%, 50%–71%) | - | 11/28 (39%, 24%–58%) | 8/11 (73%, 43%–90%) |
| cases_pseudo_real.json | 42 | 34/42 (81%, 67%–90%) | 22/30 (73%, 56%–86%) | 23/30 (77%, 59%–88%) | 0.753 | 0.706 | 13/30 (43%, 27%–61%) | - | 3/6 (50%, 19%–81%) | 6/6 (100%, 61%–100%) |
| cases_pseudo_real2.json | 34 | 26/34 (76%, 60%–88%) | 22/28 (79%, 60%–90%) | 23/28 (82%, 64%–92%) | 0.804 | 0.795 | 5/28 (18%, 8%–36%) | - | 0/3 (0%, 0%–56%) | 2/3 (67%, 21%–94%) |
| cases_pseudo_real3.json | 36 | 17/36 (47%, 32%–63%) | 12/28 (43%, 27%–61%) | 14/28 (50%, 33%–67%) | 0.464 | 0.474 | 9/28 (32%, 18%–51%) | - | 1/6 (17%, 3%–56%) | 1/2 (50%, 9%–91%) |
| cases_real_log_v1.json | 29 | 22/29 (76%, 58%–88%) | 17/23 (74%, 54%–87%) | 18/23 (78%, 58%–90%) | 0.773 | 0.796 | 16/23 (70%, 49%–84%) | - | 0/2 (0%, 0%–66%) | 3/4 (75%, 30%–95%) |
| cases_team.json | 10 | 10/10 (100%, 72%–100%) | 8/8 (100%, 68%–100%) | 8/8 (100%, 68%–100%) | 1.000 | 0.952 | - | - | 1/1 (100%, 21%–100%) | 1/1 (100%, 21%–100%) |

Ghi chú A, B:
- HOLDOUT-4 (`cases_h4.json`) trên code hiện tại: hành vi 90/106, top-1 60/77, top-3 67/77, **MRR 0,824, nDCG@5 0,805**, hỏi lại 10/16. Bản draft đo trên code cũ ra MRR 0,810 và nDCG@5 0,785 (cùng top-1 60/77).
- Real-log v1 (29 lượt, code hiện tại): hành vi 22/29, top-1 17/23, MRR 0,773, nDCG@5 0,796. Bộ này đã bị đọc lỗi (real-11, real-13) nên không phải số mù.
- `blind` = HOLDOUT-3, h4, h5, h6, pseudo_real 1-3, bộ team. Bộ mù **chính thức** theo docs/EVAL.md là h4 (top-1 78%, hành vi 85%, hỏi lại 10/16) và pseudo_real 2. Số hiện tại của pseudo_real 2 là top-1 22/28, hành vi 26/34, còn docs/EVAL.md ghi 19/28 và 23/34: chưa tìm nguyên nhân lệch.
- pseudo_real 3 thấp nhất (hành vi 47%); chưa xem lỗi (xem lỗi bộ mù sẽ làm nó mất tính mù).
- Cột "đúng trường" của các bộ blind kém tin hơn dev: nhãn trường trong các file đó viết tay, tên khác (đã đổi tên `documents/fee/place/time`; `conditions` không có trường tương ứng nên luôn tính lệch).
- `holdout-used` = HOLDOUT cũ + h2, đã bị xem lỗi nên không còn là bộ mù.

**C. Bộ khuôn câu hỏi theo chủ đề** — `python run_server.py eval/build_template_set.py` rồi `python run_server.py eval/run_golden.py template_thu-tuc --by type`. Câu dùng nguyên tên thủ tục nên **dễ hơn câu người dân gõ**; dùng để so các chủ đề với nhau và bắt hồi quy, không phải số chính thức. Chỉ lấy thủ tục cấp xã, không ngành dọc, họ một dạng.

| type | số ca | hành vi đúng | top-1 | top-3 | MRR | nDCG@5 | đúng trường | đủ ý (nhiều thủ tục) | hỏi lại đúng | từ chối đúng |
|---|---|---|---|---|---|---|---|---|---|---|
| address | 30 | 29/30 (97%, 83%–99%) | 30/30 (100%, 89%–100%) | 30/30 (100%, 89%–100%) | 1.000 | 1.000 | 15/30 (50%, 33%–67%) | - | - | - |
| compare-khac-gi | 20 | 20/20 (100%, 84%–100%) | 20/20 (100%, 84%–100%) | 20/20 (100%, 84%–100%) | 0.933 | 0.944 | - | 16/20 (80%, 58%–92%) | - | - |
| compare-so-sanh | 20 | 20/20 (100%, 84%–100%) | 20/20 (100%, 84%–100%) | 20/20 (100%, 84%–100%) | 1.000 | 1.000 | - | 20/20 (100%, 84%–100%) | - | - |
| components | 40 | 39/40 (98%, 87%–100%) | 38/40 (95%, 83%–99%) | 39/40 (98%, 87%–100%) | 0.963 | 0.966 | 39/40 (98%, 87%–100%) | - | - | - |
| explain | 40 | 39/40 (98%, 87%–100%) | 38/40 (95%, 83%–99%) | 39/40 (98%, 87%–100%) | 0.963 | 0.966 | 18/40 (45%, 31%–60%) | - | - | - |
| fees | 40 | 39/40 (98%, 87%–100%) | 40/40 (100%, 91%–100%) | 40/40 (100%, 91%–100%) | 1.000 | 1.000 | 36/40 (90%, 77%–96%) | - | - | - |
| legal | 40 | 39/40 (98%, 87%–100%) | 40/40 (100%, 91%–100%) | 40/40 (100%, 91%–100%) | 1.000 | 1.000 | 35/40 (88%, 74%–95%) | - | - | - |
| list | 40 | 32/40 (80%, 65%–90%) | - | - | - | - | - | - | - | - |
| multi_field | 40 | 39/40 (98%, 87%–100%) | 39/40 (98%, 87%–100%) | 40/40 (100%, 91%–100%) | 0.988 | 0.991 | 37/40 (92%, 80%–97%) | - | - | - |
| online | 40 | 39/40 (98%, 87%–100%) | 39/40 (98%, 87%–100%) | 39/40 (98%, 87%–100%) | 0.975 | 0.975 | 33/40 (82%, 68%–91%) | - | - | - |
| steps | 40 | 39/40 (98%, 87%–100%) | 40/40 (100%, 91%–100%) | 40/40 (100%, 91%–100%) | 1.000 | 1.000 | 36/40 (90%, 77%–96%) | - | - | - |
| time | 40 | 39/40 (98%, 87%–100%) | 40/40 (100%, 91%–100%) | 40/40 (100%, 91%–100%) | 1.000 | 1.000 | 35/40 (88%, 74%–95%) | - | - | - |

liệt kê: 32/40 câu có trả danh sách; trung bình 12% mục trong danh sách đúng lĩnh vực được hỏi.

Điều bảng C cho thấy:
- Chủ đề thường (hồ sơ, phí, thời hạn, nơi nộp, trình tự, căn cứ, trực tuyến): chọn đúng thủ tục 95-100%.
- **So sánh**: "So sánh A và B" đủ ý 20/20. "A khác gì so với B" lúc đầu 0/20 (không tách được hai vế vì liên từ nằm sau cụm "khác gì"); đã sửa `retrieval/refs.py` (`split_compare`), giờ 16/20. Bảng C ở trên là số SAU sửa; test `server/tests/compare_cue_test.py`.
- **Liệt kê**: 32/40 câu có trả danh sách (8 câu không khớp mẫu), nhưng chỉ 12% mục đúng lĩnh vực được hỏi: hệ thống chưa có truy vấn theo lĩnh vực, chỉ liệt kê thủ tục gần câu hỏi nhất (đúng như đã ghi trong câu trả lời).
- Chủ đề "explain" (45%) và "address" (50%) đúng trường thấp: câu "Giải thích giúp mình thủ tục X" hay bị hiểu thành hỏi mục khác, và câu hỏi nơi nộp thường kèm thêm `components`. Chưa sửa vì chưa rõ có phải lỗi.

**D'. An toàn** — `python run_server.py eval/safety/test_pii_injection.py --e2e --adapter answer_adapter:adapter` (bộ test của branch draft, đã chép sang `eval/safety/`). Đo 2026-10-14:

| Chỉ số | Trước khi vá `mask_pii` | Sau khi vá |
|---|---|---|
| D1 che CCCD/SĐT viết liền (recall) | 9/9 | 9/9 |
| D1 che CCCD/SĐT có dấu cách, gạch, chấm (`034-203-004455`, `0901 234 567`) | **0/3** | 3/3 |
| D1 che nhầm câu không có PII | 0/5 | 0/5 |
| D2 chặn chèn lệnh / chặn nhầm câu thường | 11/11, 0/6 | 11/11, 0/6 |
| D2 hành vi thật của hệ thống (đầu-cuối) | 17/17 | 17/17 |

Lỗi che số có thật trên branch này (số có dấu phân cách lọt vào log nguyên văn); đã vá bằng cách chuyển khối `mask_pii` của branch draft sang `server/policy/policy.py`, giữ nguyên `_CGEN`. **Rủi ro chấp nhận:** số 9–12 chữ số không kèm đơn vị tiền vẫn bị che (ví dụ `quyết định số 123456789` thành `[ID]`). Bản cũ cũng che trường hợp này khi số liền mạch, nên bản vá không tạo rủi ro mới; chỉ mở rộng sang số có dấu phân cách.

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

### Eval đầy đủ lần #1 — mốc bản 3 (18/10/2026, kế hoạch thực thi G2.4; lần 1/3 của tuần)
Dữ liệu chính thức theo quyết định D4: **thủ tục phiên bản 3** (cào 13/10, 1.517 thủ tục, 34 tỉnh, link Cổng dạng UUID), đã áp dụng qua cổng kiểm (bản 2 → bản 3: 137 ca chung, hành vi 94,9% → 94,9%, top-1 92,9% → 92,9%).
Lệnh: `S3_DATA_DB=data/runtime/knowledge/3-1a9c2d36a7.db S3_USE_LLM=0 S3_PLANNER_MODE=rules python run_server.py eval/run_golden.py thu-tuc --by status` (và `--by source`). Kết quả đầy đủ: `eval/saved_results/2026-10-18_eval1/`.
Dấu phiên bản: git `e291ad2`, data_version `v3 Cào 13/10/2026 15:45`, 1.517 thủ tục, data_sha256 `70c42af1…36bd`, model: tắt (chỉ luật), settings_hash `120a36e41ab80523`.
Chấm theo mã tương đương (`proc_lineage`, G2.3): đáp án mang mã của bản Gốc được đổi sang mã của bản 3; ca có mã không ghép được bị **loại**: bộ mù 35, dev 80, holdout-used 21 (tổng 136; danh sách mã cho người duyệt: `docs/LINEAGE_CAN_DUYET.md`).

| status | số ca | hành vi đúng | top-1 | top-3 | MRR | đúng trường | hỏi lại đúng | từ chối đúng |
|---|---|---|---|---|---|---|---|---|
| **blind** | 518 | 407/518 (79%) | **274/381 (72%)** | 302/381 (79%) | 0,752 | 184/363 (51%) | 36/76 (47%) | 52/58 (90%) |
| dev | 561 | 549/561 (98%) | 478/488 (98%) | 485/488 (99%) | 0,986 | 309/316 (98%) | 22/25 (88%) | 42/46 (91%) |
| holdout-used | 137 | 115/137 (84%) | 91/104 (88%) | 93/104 (89%) | 0,881 | 66/86 (77%) | 3/10 (30%) | 16/20 (80%) |

So với số ngày 15/10 (AUDIT F3, cùng bộ mù): snapshot 1.350 top-1 73%; dữ liệu đang chạy lúc đó (bản 2, không ghép mã) 63%; bản 2 ghép mã theo tên 68%. Bản 3 + lineage + loại ca không ghép được: **72%**. Hỏi lại vẫn 47% (việc G4.1).

### Nghiệm thu mục 3 (rút ra từ các bảng A–D)

**Trạng thái theo từng bước của mục 3**

| Bước | Kết quả |
|---|---|
| 1. Tiêu chí chấm | Xong: `eval/CRITERIA.md` |
| 2. Golden set theo domain | Xong cho Thủ tục (1.352 ca); Trò chuyện chung chưa có |
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
- Số pseudo_real 2 chạy lại (top-1 22/28) khác số cũ trong `docs/EVAL.md` (19/28). Đã loại trừ nguyên nhân do cách chấm: `run_golden.py` (phát lại lượt assistant bằng câu trả lời thật) và `run_pseudo.py` cho đúng cùng số trên pseudo_real 2 (26/34, 22/28, 23/28) và h4 (90/106, 60/77, 67/77). Số 19/28 trong `docs/EVAL.md` là số của code cũ, cần cập nhật.
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

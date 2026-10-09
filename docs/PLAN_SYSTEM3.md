# PLAN — Build System 3 (Semantic Planner) từ đầu, tận dụng Database

**System 3 = kiến trúc MỚI, project riêng** (`D:\Finale_architect\system3\`). Không build tiếp từ V10.6,
không import `Backend/`, `Frontend/`, System 1, System 2. Chỉ lấy DỮ LIỆU từ `repo/Database/`
(`staging/procedures.jsonl` + `schema_procedures.sql`) và COPY các đoạn code tra cứu cần dùng.

Phạm vi: Box 1–4 (User → Orchestrator → Semantic Planner → Validate+Policy+Router).
Executor/Answerer chỉ làm bản tối thiểu để chạy được end-to-end và đo.
Nguyên tắc: **đo trước, xây sau**; mỗi phase có tiêu chí xong; không phụ thuộc System 1/2.

---

## Phase 0 — Bộ test + baseline (làm TRƯỚC mọi thứ)

- Tạo `system3/eval/cases.jsonl`: ~15 câu × 9 hạng mục (RAG cơ bản, định lượng, nhiều trường,
  context/memory, clarification+điều kiện, evidence, multi-intent, hallucination/unsupported,
  Context+Conditional+Evidence) ≈ 135 câu. Mỗi câu ghi: `turns[]`, `expected.tasks[]`
  (proc_id chấp nhận được, fields, quantity), `expected.behavior` (answer | apologize | clarify).
- Thêm ~30 câu out-of-scope (hộ chiếu, làm thơ, thủ tục cấp tỉnh) và ~20 câu gõ tắt/sai chính tả.
- `system3/eval/run.py`: chạy toàn bộ, xuất bảng: top-1/top-3 retrieval, đúng field, đúng hành vi,
  tỉ lệ bịa số, độ trễ p50/p95.
- Đo baseline: `retrieval.search` hiện có trên các câu này (đã biết sai ở "kết hôn có mất lệ phí không",
  "làm hộ chiếu" → strong nhầm).

**Xong khi:** chạy 1 lệnh ra bảng số; có baseline để so.

## Phase 1 — Lớp dữ liệu độc lập (`system3/data/`)

Copy `schema_procedures.sql` + `procedures.jsonl` từ `repo/Database/` vào `system3/data/` (snapshot, ghi rõ commit V10.6).
`system3` có import script riêng, không phụ thuộc `Database.pipeline`. Thêm bước build sau import:

| Thêm | Mục đích |
|---|---|
| `fees_clean` (tính sẵn, `kind = numeric \| text_only \| none`) | định lượng không phải làm lúc chạy; 373/840 bản "present" thực ra rỗng |
| `field_chunks(proc_id, field, case_ordinal, text, status)` | lấy đúng field cần; nền cho embedding sau này |
| `condition_index(proc_id, type, text)` từ `cases` (đã lọc `_is_real_case`), `subjects`, tên biến thể | so điều kiện người dùng, không hỏi MCQ |
| `synonyms` trong chính file DB thủ tục | bỏ phụ thuộc `Backend.db` |
| `family_index` lưu thành bảng (930 nhóm, 84 nhóm nhiều dạng) | khỏi tính lại lúc chạy |
| cờ `default_variant` cho từng nhóm nhiều dạng (admin duyệt, mặc định = tên ngắn nhất) | "bản phổ biến" có định nghĩa |

Copy sang `system3/` (rồi sửa theo nhu cầu, không import ngược): `search.py`, `fold`, `parse_query`, `refine`,
`build_record`, `derive_steps`, `clean_files`, `is_expired`, `vertical_agency`.
**Không** mang sang: máy MCQ (`axes_*`, `AXIS_*`), `looks_like_procedure`, `is_other_procedure`.

**Xong khi:** `system3.data` import được mà không cần `Backend/`; test đơn vị cho 5 hàm chính.

## Phase 2 — Retrieval cho Planner

Vấn đề đã đo: bỏ dấu làm "hộ chiếu" ≈ "hỗ/hộ"; câu có từ chỉ field ("lệ phí", "giấy tờ", "mất") ra rỗng.

1. Luật tách câu thành `procedure_query` (cụm danh từ) + `fields` (dùng `SECTION_CUES` tương đương, tự viết lại trong `system3`).
2. FTS5 trên `procedure_query`, sau đó **xếp lại có dấu** (so khớp từ có dấu trên tên làm tiêu chí phụ) và trọng số IDF thay cho tỉ lệ âm tiết.
3. Trả top-k (k=5) kèm điểm; **không** dùng `is_strong` làm quyết định out-of-scope.
4. Quyết định có thêm Dense/Rerank hay không **chỉ sau khi** có số của Phase 0.
   Nếu thêm: embedding chạy CPU trên `field_chunks`/tên (1.350 bản ghi là nhỏ), không tranh VRAM với 4B.

**Xong khi:** top-3 ≥ mục tiêu đặt ở Phase 0 (đề xuất ≥ 90% với câu in-scope); out-of-scope bị loại ≥ 90% mà không cần LLM hoặc chỉ cần 1 lần xác nhận LLM.

## Phase 3 — Semantic Planner (Box 3)

- Model: `qwen3:4b` (tắt thinking), chạy qua Ollama với **JSON schema ràng buộc** (`format`), `keep_alive` giữ nóng.
  Thử 2 cấu hình và chọn theo số đo: (A) luật → 4B; (B) luật → 1.5B → 4B. Mặc định thử A trước.
- Prompt gồm: câu hỏi, 5 lượt gần nhất rút gọn, `session_facts`, **top-k ứng viên từ Phase 2** (LLM chỉ chọn, không tự điền `procedure_id`).
- Plan JSON (rút gọn so với bản docx):

```
tasks[ ≤3 ]: { action, procedure_query, procedure_id(null → Box 4 điền), refers_to: new|last|<proc_id>,
               fields[], quantity, conditions[{type,text}], context_facts[], evidence_demand, relation }
entities{province,ward,who}, output_format, needs_clarification, clarify_reason
```
- Action rút gọn (không để model nhỏ phân biệt quá nhiều): `ask_field`, `find_procedure`, `check_condition`,
  `compare`, `provide_info`, `clarify_reply`, `correct_previous`, `chitchat`, `out_of_scope`.
  `multi` suy ra từ `len(tasks)`; `follow_up/overview/how_to` gộp vào `ask_field` (khác `fields`/`refers_to`).
- Luật nhanh không cần LLM: chào hỏi, bấm thẻ hỏi lại, "ngắn hơn/chi tiết hơn", "chắc không?", hỏi tiếp 1 field của thủ tục `last`.
- Phát hiện multi-intent: ≥2 cặp (thủ tục, field) khác nhau. **Nhiều field của cùng 1 thủ tục là 1 task**, không tính multi.
- Chuyển tầng dựa trên tín hiệu khách quan (JSON hợp lệ, ứng viên top-1 khớp nhãn LLM, điểm retrieval), không dựa `confidence` tự báo.
- Planner timeout/JSON hỏng → plan dựng bằng luật (Phase 2.1).

**Xong khi:** đúng action ≥ 90%, đúng fields ≥ 90% trên bộ test; p95 Box 3 ≤ ngưỡng đặt ở Phase 0 (đề xuất ≤ 3 s trên máy 6 GB GPU).

## Phase 4 — Validate + Policy + Router (Box 4)

Thứ tự ưu tiên guardrail (làm 1–8 trước, 9–13 sau):

1. Đúng schema/enum; sai → bỏ giá trị, lỗi nặng → chạy lại 1 lần.
2. `procedure_id` chỉ lấy từ ứng viên Phase 2, còn hiệu lực (`is_expired`).
3. `context_facts`/`conditions`/`province` phải có căn cứ trong lời người dùng hoặc session.
4. Giới hạn: ≤3 task, câu ≤2.000 ký tự, tối đa 1 thẻ hỏi lại/lượt; >3 ý → trả lời 3 ý đầu và nói rõ.
5. Field không có dữ liệu → dùng `status_*`; số tiền/ngày không có → "Cổng không công bố", **không bao giờ suy ra miễn phí**.
6. Không hỏi điều đã biết (profile, session_facts, lựa chọn đã chốt).
7. Phạm vi: ngoài cấp xã / ngành dọc (Thuế, Hải quan) / hết hiệu lực → xin lỗi đúng lý do.
8. Chống chèn lệnh: nội dung người dùng chỉ là dữ liệu.
9. Che thông tin cá nhân (CCCD, SĐT) trước khi ghi log.
10. Cache plan theo câu đã chuẩn hoá.
11. Nhật ký câu bị xin lỗi / điểm thấp cho dev duyệt.
12. Test tự động: câu trả lời không nhắc Web search / Tìm chính xác.
13. Cờ dev (toggle): bật lại cảnh báo/khuyến nghị kiểu System 2.

Router theo task: `Direct` (CSDL thủ tục) · `RAG` (tệp người dùng tải lên, nếu có) · `Apologize` · `Clarify`.
Chọn thủ tục tự động; nhóm nhiều dạng → trả `default_variant` + liệt kê dạng khác; chỉ hỏi lại khi thật mơ hồ
(2 ứng viên sát điểm và khác nhau về nội dung được hỏi).

**Xong khi:** mọi guardrail 1–8 có ≥1 test fail-nếu-bỏ; 0 trường hợp "miễn phí" bịa trong bộ test.

## Phase 5 — Executor + Answerer tối thiểu (để đo end-to-end)

- Executor: `build_record` → `field_chunks`, kèm nguồn (`portal_url`, `decision_number`, `legal_basis`).
- Answerer:
  - `ask_field` không điều kiện → **soạn bằng code** (nhanh, không bịa).
  - `check_condition` / `compare` / `evidence_demand` → LLM chỉ được dùng đúng các chunk đã lấy, trả kèm trích nguồn.
  - Multi-intent → 1 khối, mỗi task 1 đoạn có tiêu đề tên thủ tục AI đã chọn; ý không tìm được → đoạn xin lỗi riêng.
  - Căn cứ pháp lý: chỉ nêu tên văn bản (dữ liệu không có điều khoản).
- Verifier: kiểm số tiền/ngày/số hiệu xuất hiện trong chunk nguồn.

## Phase 6 — Clarification + Memory

- `session_facts` (hộ nghèo, người khuyết tật…) và `shown_procedures[]` theo hội thoại; reset khi đổi chủ đề; người dùng xem/xoá được.
- Thẻ hỏi lại = MCQ + ô gõ tự do; câu gõ tự do do Planner xử lý (`clarify_reply`) và **không hỏi lần 2** — nếu vẫn mơ hồ thì trả lời bản tốt nhất kèm giả định nói rõ.
- `correct_previous`: sửa đúng đoạn bị chọn sai.

## Phase 7 — Hạ tầng riêng + đóng gói

- Được COPY từ V10.6 sang `system3/` (copy rồi sửa, không import ngược, không kéo theo logic System 1/2):
  khung FastAPI/server, hàng đợi (`core/queue.py`), `llm.py` gọi Ollama, hội thoại/lịch sử, và `Frontend/` (khung chat, thẻ hỏi lại).
  Chỉ copy phần cần; bỏ toàn bộ code MCQ, bảng retrieval_pending, nút/gợi ý Web search và Tìm chính xác.
- Orchestrator (Box 1–2): `POST /chat` (text, conversation_id, reply_to);
  SQLite riêng của system3 (không dùng `app.db` của V10.6) cho hội thoại + session_facts.
- UI: sửa khung chat của V10.6 để hiện câu trả lời nhiều đoạn (multi-intent) và thẻ hỏi lại MCQ + ô gõ.
- Toggle dev (cờ cấu hình): bật log chi tiết plan/guardrail. Không có System 2, không có nút Tìm chính xác trong project này.
- Chạy lại toàn bộ Phase 0; so với baseline; ghi báo cáo.

---

## Rủi ro chính

| Rủi ro | Giảm thiểu |
|---|---|
| Chọn nhầm thủ tục khi tự quyết | hiện tên thủ tục AI chọn ở đầu mỗi đoạn; ô gõ để sửa; `default_variant` do admin duyệt |
| 4B quá chậm / tranh VRAM | luật nhanh trước; so cấu hình A/B bằng số đo; embedding chạy CPU |
| Dữ liệu phí chỉ ~35% dùng được | nói rõ kỳ vọng; câu trả lời "không công bố" là đúng, không tính là lỗi |
| Retrieval chữ yếu với câu tự nhiên | Phase 2 + quyết định Dense theo số đo |
| System 3 thừa kế lỗi từ System 2 | project riêng; không import `Backend/` hay code MCQ |
| Snapshot Database lệch khi V10.6 cập nhật dữ liệu | ghi commit nguồn; cập nhật bằng cách chép lại `procedures.jsonl` và chạy import |

## Đã chốt (theo đề xuất)

1. Độ trễ p95: Planner ≤ 3 s, tổng ≤ 6 s trên máy 6 GB GPU.
2. Tài khoản: session ẩn danh trước. Nếu copy được auth của V10.6 gọn thì bật sau, không chặn tiến độ.
3. `default_variant` và nhãn dân dã: tự sinh (bản tên ngắn nhất làm mặc định), kèm danh sách dev-only để admin duyệt/sửa sau.
   Câu nào trúng dạng khác rõ ràng thì Planner chọn dạng đó, không dùng default.

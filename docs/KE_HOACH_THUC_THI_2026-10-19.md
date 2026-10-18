# Kế hoạch thực thi tuần 19–23/10/2026 (G0–G4)

**Dành cho:** phiên làm việc (Claude hoặc dev) sẽ thực hiện. Tài liệu này **tự đủ**: đọc hết là làm được, không cần nhớ hội thoại trước.
**Trạng thái:** đã được trưởng nhóm duyệt các quyết định ngày 18/10. Chưa thực hiện việc nào.
**Lý do và bằng chứng** của từng việc: [ARCHITECTURE_REVIEW_2026-10-15.md](ARCHITECTURE_REVIEW_2026-10-15.md) (ADR-01…12, sổ vấn đề P01…P32, mâu thuẫn I1…I15) và [AUDIT_2026-10-15.md](AUDIT_2026-10-15.md) (F1…F10). Khi tài liệu này khác hai tài liệu kia, **tài liệu này thắng** (vì có quyết định mới hơn).

---

## 0. Bắt đầu thế nào
1. Đọc tài liệu này, rồi đọc lướt §6 của bản duyệt (sổ vấn đề) và §2 của bản audit (bằng chứng F1–F10).
2. Kiểm repo:
   - `git status` sạch, trừ `.gitignore` (dòng `keo_bua_bao/` của trưởng nhóm) và `keo_bua_bao.rar` — **không đụng** hai thứ này.
   - HEAD có commit ABI `034275a` và commit tài liệu audit.
3. Tạo nhánh làm việc: `git checkout -b exec/2026-10-19-audit-fixes`. Mỗi việc là một commit nhỏ. **Không push** khi trưởng nhóm chưa cho phép.
4. Dựng DB snapshot làm "đồ thử cố định" (G0.1) trước mọi việc khác.

## 1. Quyết định của trưởng nhóm (18/10) — ràng buộc của mọi việc
| # | Chủ đề | Quyết định |
|---|---|---|
| D1 | Mục tiêu triển khai | Demo + thí điểm cho app của một xã (**"SOS Tăng Nhơn Phú"**). Sau này backend thành **API** để nối vào app của xã; giao diện web chỉ giữ để demo. Phần nối app **làm sau**. → Mọi quy tắc phải nằm ở **server**, không chỉ ở giao diện |
| D2 | Phạm vi | **Toàn bộ G0–G4.** Khi làm chỉ kiểm bằng **mẫu nhỏ**; bộ eval đầy đủ chạy **tối đa 3 lần** (§2) |
| D3 | Bộ câu hỏi thật | Tìm trên web hoặc dùng lại bộ test uy tín trong bài báo — **làm SAU tuần này**, không làm bây giờ |
| D4 | Dữ liệu chính thức | **Thủ tục phiên bản 3** (cào 13/10, 1.517 thủ tục, 34 tỉnh, link Cổng dạng UUID). Số liệu cuối đo trên bản 3 |
| D5 | Thủ tục riêng của tỉnh | **Hỏi lại người dùng ở tỉnh nào** (G4.4) |
| D6 | Tên hội thoại | **Tên thủ tục đầu tiên được trả lời** (G4.5) |
| D7 | Biểu mẫu | **Dẫn link về trang thủ tục trên Cổng** (G4.7) |
| D8 | Máy không GPU | **Vẫn cho dùng, có cảnh báo chậm**, kèm **công tắc "chỉ trả lời bằng luật"** (G3.3) |
| D9 | "Suy nghĩ kỹ" | **Bỏ hẳn** (G3.2) |
| D10 | Tìm web có số giấy tờ | **Che số rồi gửi, báo người dùng đã che** (G1.3) |
| D11 | Đăng ký tài khoản | **Giữ nguyên** tới khi xã quyết. **Không đổi** luồng đăng ký, kể cả "người đầu tiên thành dev". Giới hạn đăng nhập sai vẫn làm (không đụng đăng ký) |
| D12 | Lưu dữ liệu | Giữ **thống kê** và dữ liệu **đã che số**. Để fine-tune chỉ giữ lâu dài các **cặp hỏi–đáp có 👍/👎**. Hội thoại của người dùng tính vào **hạn mức dung lượng chung với dữ liệu tải lên**; đầy thì người dùng phải xoá, nếu không hệ thống **từ chối** (G1.7) |
| D13 | Xoá tài khoản | Xoá hết mọi thứ của người đó, **trừ** các cặp 👍/👎 đã che số: giữ nhưng **bỏ danh tính**. Báo rõ điều này khi người dùng bấm 👍/👎 (G1.4) |
| D14 | Mức nghiêm ngặt các lĩnh vực cứng khác (ABI…) | **Mỗi lĩnh vực tự chọn**; mặc định **có căn cứ + bắt buộc trích dẫn** (G4.3) |
| D15 | Xử lý song song | **Phần luật chạy song song, phần GPU tuần tự** (card 6 GB). Card lớn hơn bật công tắc là song song (G3.1) |
| D16 | Git | ABI đã commit riêng; tài liệu audit commit riêng. Làm trên nhánh mới, commit nhỏ, không push |
| D17 (18/10, sau G3.4) | Chờ hàng Friendly khi 10 người | **Chấp nhận mục tiêu ~15 s cho thí điểm** (đo: p95 13,6 s). Được dùng thêm lượt đo GPU khi cần |
| D18 (18/10) | Câu được hỏi nhiều | **Dùng lại câu trả lời đã 👍** khi người khác hỏi y chang: trả ngay, không gọi model (`system4/server/answer_cache.py`, công tắc `ANSWER_CACHE`) |

## 2. Quy tắc cứng khi làm
- **Không bao giờ gọi `/rag` của abi.com.vn** hay bất kỳ thứ gì tốn token của chủ web. Mọi test/eval chạy với `S4_ABI_SYNC=0`, không đặt `ABI_API_KEY`.
- **Không chạy `eval/run_all.py` khi chưa làm xong G0.4.** Bước build cũ dựng đè `data/runtime/system3.db`.
- **Không xoá dữ liệu runtime của người dùng** (dataset, hội thoại, phiên bản dữ liệu) khi chưa hỏi trực tiếp trưởng nhóm. Ví dụ: bộ "DS LỚP 1.5" ở G1.6.
- **Cách ly khi thử:** `S3_DATA_DB=<db thử>`, `S3_DB_PATH=<tạm>`, `S4_RUNTIME_DIR=<tạm>`, `OLLAMA_HOST=http://127.0.0.1:1` (khi không cần model), `S3_USE_LLM=0`, `S3_NO_WARMUP=1`, `S4_WARMUP=0`.
- **`python run_server.py <tham số>`:** nếu tham số không phải `-m …` hoặc đường dẫn `.py` thì lệnh **khởi động server**. Gõ cẩn thận.
- **Ngân sách đo (D2):**

| Loại | Khi nào | Giới hạn |
|---|---|---|
| Test đơn vị/tích hợp (`server/tests`, `system4/tests`, `data/tests`, `eval/safety`) | sau mỗi việc | không giới hạn (rẻ, chỉ CPU) |
| Mẫu so khớp đầu ra (~150 ca, G0.2) | sau mỗi việc có thể đổi câu trả lời | không giới hạn (~20–30 s CPU) |
| Mẫu tính năng 20–40 ca | trong lúc làm từng tính năng | vừa phải |
| **Bộ eval đầy đủ** (`run_golden.py thu-tuc --by status` + `--by source`, LLM tắt) | **#1** sau G2 (mốc bản 3) · **#2** sau G4.1 + G4.2 · **#3** số cuối | **tối đa 3 lần** cả tuần; ghi lại lần nào đã dùng |
| Đo có LLM / GPU | chỉ G3.4 (nhỏ) | ≤ 2 lần chạy ngắn |

- **Thứ tự bắt buộc:** G0 → G1 và G2 (song song được nếu có 2 người) → G3 → G4. Mỗi giai đoạn để hệ thống chạy được, có cờ bật/tắt cho tính năng mới.

## 3. Các giai đoạn

### G0 — Lưới an toàn (≤ 1 ngày, bắt buộc)
| Việc | Cách làm | Xong khi |
|---|---|---|
| 0.1 DB snapshot cố định cho test | Script `eval/fixture_db.py`: dựng `data/snapshot/procedures.jsonl` vào `eval/runtime/fixture_snapshot.db` (thư mục đã bị ignore) bằng `system3.data.build` với `S3_DATA_DB`. Script `eval/run_tests.py` chạy lần lượt mọi test với `S3_DATA_DB` trỏ tới đó (tham khảo cách cách ly trong `system4/tests/*`). `system4/tests/test_nv4.py`: bản sao lấy từ fixture, số thủ tục đọc từ tệp nguồn thay vì viết cứng 1350 | Mọi test đạt, trừ `server/tests/p23_input_test.py` (hồi quy đã biết, sửa ở G4.8) |
| 0.2 Mẫu so khớp đầu ra | `eval/equality.py --record/--compare`: chọn cố định ~150 ca từ `eval/golden/thu-tuc.jsonl`, phân tầng theo `source` và `type`, seed cố định. Chạy qua `eval/answer_adapter.py` với LLM tắt. Ghi (hành vi, mã thủ tục, sha1 câu trả lời) vào `eval/runtime/equality_<tên>.json`. `--compare` in các ca khác nhau | Hai lần `--record` liên tiếp ra y hệt. **Quy ước:** việc cố ý đổi câu trả lời (G1.1, G2, G4) thì đọc diff, ghi lý do vào commit, rồi `--record` lại mốc |
| 0.3 Dấu phiên bản cho kết quả đo | `eval/stamp.py` trả `{git, data_version, n_procedures, data_sha256, model, settings_hash}`. `run_golden.py` và `run.py` ghi kèm vào tệp kết quả | Tệp kết quả có đủ các trường |
| 0.4 `run_all.py` không đè DB đang chạy | Bước build dựng vào `eval/runtime/`; thêm cờ `--use-live` nếu muốn dùng DB đang chạy | Chạy xong, hash `data/runtime/system3.db` không đổi |
| 0.5 Làm sạch `eval/check_docs.py` (đang 17 lỗi, I1) | Cập nhật số trong README/EVAL theo tệp kết quả đã commit; sửa hoặc bỏ 7 đường dẫn tới tệp không còn; "11 sự kiện" → 12 | `check_docs: … 0 lỗi` |

### G1 — Sửa nóng: đúng và an toàn (~1,5–2 ngày, bắt buộc)
| Việc | Cách làm | Xong khi |
|---|---|---|
| 1.1 Lệ phí (P01/F1) | `data/build.py` → `fees_clean` thêm `currency` (map `currency_id`: `019b3fb2-b5b8-…`=VND, `019b3fb2-dee2-…`=USD, khác/rỗng=không rõ), `amount_vnd` (sửa hàng nghìn bằng đối chiếu `amount_text`, như `fee_query._levels`), `amount_ok`. `answerer._fees_text`, `procedure_table`, `procs_xlsx`, `fee_query` dùng cột mới. Số không chắc thì in nguyên văn chữ của Cổng | Test mới `server/tests/fee_display_test.py` (trên fixture): "Lệ phí chứng thực bản sao…" không còn "10 đồng"; có "10 USD" hoặc nguyên văn. `fee_query_test` đạt |
| 1.2 Hồ sơ Strict theo tài khoản (P02/F2) | Khi bật S4, `server/main.py::_cid` lấy `u<user_id>` từ `request.state.user` (bỏ `'default'`). Cầu nối `system4/server/strict.py` không cần truyền header. `/memory*` cũng theo tài khoản | Test hai tài khoản: không thấy, không xoá được hồ sơ của nhau |
| 1.3 Lớp chính sách chung v1 (P03, P05) | (a) Chèn lệnh: `system4/server/guard.check_input` gọi thêm bộ dò `_INJECTION` của S3 (qua `from policy import pre_check`, như S4 đã import `core`). (b) Che số: gọi `mask_pii` ở mọi điểm ghi — S3 `store.add_message/add_fact/set_title_if_new`; S4 `db.add_message`, `set_title_if_new`, `log_feedback`, `save_trace`. (c) Trước khi tìm web (`server/core/websearch.search`): che số; nếu có che thì thêm dòng "Đã che số giấy tờ trước khi tìm trên web" vào câu trả lời | `eval/safety/test_pii_injection.py` cho **cả đường Friendly**: 11/11, chặn nhầm 0/6. Câu thường của Friendly (22 tình huống trong `system4/eval/nv2_behavior.py`) không bị chặn. Test DB sau một lượt có số giả: không còn số thô ở mọi bảng |
| 1.4 Xoá tài khoản + ô "Tài khoản & quyền riêng tư" (P04, tiêu chí 9, D13) | `admin.delete_user` và endpoint mới `DELETE /s4/account` (người dùng tự xoá, cần nhập lại mật khẩu; không cho xoá dev cuối cùng): xoá hội thoại cả hai hệ, bộ nhớ, dataset (+ vector, tệp), `traces`; `feedback_log` **giữ** nhưng `user_id=0`, `conversation_id=''` (bỏ danh tính; không dựng lại bảng). Thêm `POST /s4/account/password`. Giao diện: một ô gồm đổi mật khẩu, xoá hết hội thoại, xoá bộ nhớ, xoá tài khoản, xem dung lượng đã dùng. Khi bấm 👍/👎 hiện chú thích "câu hỏi và câu trả lời (đã che số) được giữ để cải thiện hệ thống, kể cả khi bạn xoá tài khoản" | Test: sau khi xoá, chỉ còn các dòng `feedback_log` đã bỏ danh tính và đã che số |
| 1.5 Chống đoán mật khẩu (P25, **không đụng đăng ký** — D11) | Đếm số lần đăng nhập sai theo (tên, IP) trong bộ nhớ: 5 lần / 10 phút → 429 kèm thời gian chờ | Test API |
| 1.6 Dữ liệu trẻ em thật (F9) | Đổi dữ liệu demo sang `system4/eval/data/ds_lop_gia.xlsx`; liệt kê ảnh slide cần thay. **Hỏi trưởng nhóm trước** khi xoá bộ "DS LỚP 1.5" khỏi runtime | Trưởng nhóm xác nhận |
| 1.7 Hạn mức dung lượng gồm cả hội thoại (D12) | `db.used_bytes` cộng thêm độ dài tin nhắn Friendly và Strict (Strict qua `strict_ids`) của người đó. `/s4/chat` và `/s4/strict/chat` trả lỗi rõ ràng khi vượt `USER_QUOTA_MB` ("Đã hết dung lượng, hãy xoá bớt hội thoại hoặc dữ liệu"). Dev không giới hạn. Ô tài khoản (1.4) hiện mức dùng | Test: vượt hạn mức thì bị từ chối, xoá bớt thì dùng lại được |

### G2 — Phát hành dữ liệu thủ tục (~1,5 ngày, bắt buộc)
Dùng lại mẫu của `system4/abi/versions.py`: phiên bản, một bản "đang dùng", đổi tức thì, tự dọn. Thủ tục **giữ bản Gốc + 2 bản cào mới nhất**.

| Việc | Cách làm | Xong khi |
|---|---|---|
| 2.1 DB bất biến theo phiên bản + con trỏ | Mỗi phiên bản dựng thành `data/runtime/knowledge/<vid>.db` + `manifest.json` (số thủ tục, sha256, thời gian, báo cáo kiểm). Con trỏ duy nhất là `system4.db meta.proc_active`. `system3.data` có hàm `active_db_path()`; `data.api.connect()`, planner `_index`, `user_memory.subject_catalog` và các cache đều **khoá theo phiên bản**. Bỏ `procs._swap`. Cập nhật `Launch web.bat`/`Set up first time.bat` (đang kiểm `data/runtime/system3.db`) | Đổi bản 2 ↔ bản 3 không cần khởi động lại; quay lui được; test mới |
| 2.2 Chuẩn hoá + kiểm bất biến khi dựng | Phí theo 1.1. `portal_url` dựng từ `source_id` (UUID) nếu có. Báo cáo: phí < 1.000 VND không có chữ xác nhận, đơn vị tiền lạ, link sai dạng, mã trùng, trường rỗng, tỉ lệ thủ tục biến mất | Báo cáo cho bản 2 và bản 3 |
| 2.3 Lineage mã thủ tục (P08) | Bảng `proc_lineage(old_id, new_id, method)`, ghép theo `source_id` → (tên chuẩn hoá, tỉnh) → danh sách duyệt tay. `run_golden.py` chấm đúng nếu trúng mã tương đương. `proc_stats` gộp theo mã chuẩn. `conv_state` đổi mã khi nạp | 128 tham chiếu ghép tự động (đã đo 15/10) + danh sách còn lại cho người duyệt; báo số ca loại ra |
| 2.4 Cổng kiểm khi Áp dụng + áp dụng bản 3 (D4) | `procs.apply`: dựng DB tạm → chạy **mẫu so khớp + mẫu golden ~150 ca** trên DB mới (không chạy đủ bộ) → chặn nếu top-1 hoặc hành vi tụt > 3 điểm so với bản đang dùng. Sau đó áp dụng bản 3 | **Eval đầy đủ lần #1** trên bản 3 (blind + dev, `--by status` và `--by source`). Ghi số và dấu phiên bản vào `docs/PLAN_TUAN_TOI.md` |

### G3 — GPU, độ trễ, máy không GPU (~1 ngày)
| Việc | Cách làm | Xong khi |
|---|---|---|
| 3.1 Bộ lập lịch GPU chung (P13, D15) | Module `server/core/gpu.py`: khoá có ưu tiên, dùng được từ cả luồng thường và async (P0 trả lời đang chờ · P1 phụ trợ tương tác · P2 việc nền bộ nhớ/tóm tắt · P3 nạp tệp). Hàng đợi S3 chỉ bọc **lời gọi LLM**, không bọc cả lượt (giữ `_PLAN_LOCK` của planner). Tìm web chạy ngoài hàng, tối đa 15 s. Vị trí xếp hàng tính cả hai hệ. Công tắc `S3_QUEUE_CONCURRENCY`/`S4_CONCURRENCY` giữ cho card lớn | Test có LLM giả chạy chậm: lượt chỉ-luật p95 ≤ 0,5 s khi đang có lượt tìm web/LLM |
| 3.2 Bỏ hẳn "Suy nghĩ kỹ" (D9) | Gỡ ở `system4/server/chat.py` (`_think`, cờ "Trả lời nhanh"), `llm.py` (`stream_chat`, `think_model`), `routes.py` (tham số `mode`, `POST /s4/turns/{id}/fast`), `settings.py`/`config.py` (`THINK_MODEL`, lựa chọn `think` của `DEFAULT_ANSWER_MODE`), `persona.py`, `web/static/js/app.js`, `inspector.js`, `templates/index.html`. Sửa `system4/tests/test_nv1.py`, `test_nv2.py`. `Set up first time.bat` không tải `qwen3:4b` nữa (chỉ Instruct + bge-m3) | `grep -rn "THINK_MODEL\|stream_chat\|Suy nghĩ kỹ"` không còn trong code chạy; test đạt |
| 3.3 Máy không GPU (D8) | Phát hiện model không nằm trên GPU (`ollama ps` → `size_vram` = 0) hoặc biến `S4_FORCE_CPU=1`. Giao diện hiện cảnh báo "Máy không có card đồ hoạ: trả lời bằng AI sẽ chậm (7–40 giây)". **Công tắc theo người dùng** (lưu ở `user_prefs`, không đổi biến môi trường của tiến trình): "Chỉ trả lời bằng luật" → bước LLM của Strict tắt cho người đó; lĩnh vực Friendly báo "đang ở chế độ chỉ luật". Khi model không nằm trên GPU, bước LLM của Strict không chờ hết 7 s. Thêm ngắt mạch Ollama: 3 lỗi liên tiếp thì bỏ qua LLM trong 60 s | Test: chế độ CPU + công tắc bật → lượt cần LLM trả bản code < 0,5 s |
| 3.4 Đo lại độ trễ đúng cách (P16) + test hợp đồng Ollama (P23) | Model đang chạy thật (Instruct), khởi động nóng; tách thời gian chờ / nạp / sinh chữ. Test hợp đồng: thứ tự trường JSON (`a_plan`…), `format` hoạt động, model nằm trên GPU | Điền bảng SLO (bản duyệt §5.4) |

### G4 — Tính năng (~1,5–2 ngày)
| Việc | Cách làm | Xong khi |
|---|---|---|
| 4.1 Hỏi lại khi mơ hồ (P11) | Lấy top-5 của bộ luật, chấm bằng reranker (`system4/server/search.rerank_pairs`, đã có trên GPU). Nếu chênh hạng 1–2 < ngưỡng **và** hai ứng viên khác họ thủ tục → thẻ hỏi lại. Câu chỉ có chữ chung (luật không tìm thấy) → thẻ hỏi lại 3–4 ứng viên từ tìm lai (FTS5 + bge-m3 trên tên thủ tục; vector lưu theo phiên bản, không cần Qdrant). **Ngưỡng chọn trên dev + `cases_p30`, không chọn trên bộ mù.** Máy không GPU thì bỏ qua bước này | Mục tiêu hỏi lại đúng ≥ 60% (hiện 47%), hành vi chung không tụt > 1 điểm. Dưới 57% thì gỡ (để sau cờ tắt) |
| 4.2 Liệt kê / đếm bằng text-to-SQL (P12) | Bảng `proc_flat` dựng ở G2 (mỗi thủ tục một dòng: tên, tên bỏ dấu, lĩnh vực, cấp, tỉnh, cờ phạm vi, `fee_min_vnd`/`fee_max_vnd`/`fee_currency`, số ngày giải quyết, trực tuyến, đối tượng). LLM trả `{"sql": …}` theo schema JSON. Chạy trên kết nối `mode=ro` + `PRAGMA query_only=1` + `set_authorizer` (chỉ `SELECT`/`READ` trên `proc_flat`) + ép `LIMIT 200` + `progress_handler`. Lỗi hai lần thì lùi về `fee_query`/danh sách gần đúng. **Code** viết câu trả lời từ kết quả. Bộ đo riêng 60–100 câu, đáp án do code tính | Bộ khuôn "list": đúng lĩnh vực ≥ 80% (đang 12%); bộ đo riêng: đúng tập kết quả ≥ 85%; mọi câu tiêm SQL bị chặn. Sau 4.1 + 4.2: **eval đầy đủ lần #2** |
| 4.3 Domain profile v1 (P29, D14) | Thêm cột JSON `profile` vào `domains`: `answer_mode` (`verbatim`/`grounded`/`free`), `require_citation`, `clarify`, `retrieval`, `tools`, `persona`, `guardrail`, `web_allowed`. Lĩnh vực cứng mặc định `grounded` + `require_citation`. Gom nhóm cài đặt ABI trong ⚙ vào profile của ABI (giữ nguyên hành vi đang chạy). Friendly đọc tham số từ profile. Model vẫn là cấu hình chung của cả hệ | Hai lĩnh vực có cấu hình khác nhau chạy đúng; test ABI vẫn đạt **mà không gọi mạng** |
| 4.4 Hỏi lại tỉnh (D5) | Thủ tục đã chọn có bản riêng tỉnh trong cùng họ, và người dùng chưa nêu tỉnh → thẻ "Bạn làm thủ tục ở tỉnh/thành nào?": các tỉnh có bản riêng (tối đa 6) + "Áp dụng chung toàn quốc" + ô gõ. Lưu câu trả lời vào `conv_state` cho cả hội thoại, có gợi ý "nhớ cho tài khoản" (hồ sơ G1.2). Danh sách tỉnh **lấy từ dữ liệu** (bản 3 có 34 tỉnh), thay danh sách 63 tỉnh cũ trong `server/user_memory.py` | Test trên fixture + mẫu 20 câu |
| 4.5 Tên hội thoại (D6) | Strict: đặt tên bằng tên thủ tục của lượt **trả lời trực tiếp đầu tiên**; trước đó tạm dùng câu đầu đã che số. Friendly giữ câu đầu đã che số | Test |
| 4.6 Tóm tắt giữ chủ đề | Lời dặn trong `system4/server/context.maybe_summarize` yêu cầu giữ tên thủ tục/chủ đề đang hỏi | Test với LLM giả |
| 4.7 Biểu mẫu (D7) | Câu trả lời về biểu mẫu (`files`) và bảng full kèm link trang thủ tục trên Cổng (UUID của bản 3) + tên mẫu | Test: câu "mẫu tờ khai đăng ký khai sinh" có link |
| 4.8 Sửa hồi quy `p23_input_test` | Câu "Khai tử cần giấy tờ gì, tổ chức tang lễ ở nơi khác thì sao" phải là một ý. Đây là sửa hồi quy, không phải luật mới | Test đạt; mẫu so khớp chỉ đổi ở ca liên quan |
| 4.9 Tài liệu khớp code (I2–I15) | README, `FINAL_PRODUCT_CHECKLIST`, `KNOWN_ISSUES`, `SYSTEM4_DEPLOY`, `EVAL.md`, `SYSTEM4_SU_THAT.md`. Ghi lại các quyết định D1–D16. Lập danh sách câu trên slide và trong bài báo cần sửa (gửi trưởng nhóm, không tự sửa slide) | `check_docs` sạch |
| 4.10 (nếu kịp) Từ đồng nghĩa sửa được ở trang Quản trị | Gom `SEED_SYNONYMS`, `PRE_SYN`/`EXTRA_SYN`, `context.EVENTS`, `policy._SITUATION` thành bảng dữ liệu; trang Quản trị sửa được; mặc định giữ nguyên | Mẫu so khớp không đổi khi chưa sửa bảng |

**Kết thúc tuần:** **eval đầy đủ lần #3** trên bản 3 (số cuối).

## 4. Kết quả cuối phải nộp
1. `docs/KET_QUA_THUC_THI_2026-10-23.md` gồm:
   - mỗi việc: làm gì, commit nào, test nào, kết quả;
   - bảng số 3 lần eval (kèm dấu phiên bản);
   - các tiêu chí đã chuyển trạng thái (bảng 19 tiêu chí của bản audit);
   - việc chưa xong và lý do;
   - việc cần trưởng nhóm quyết thêm.
2. Danh sách câu trên slide / bài báo cần sửa (4.9).
3. Tin nhắn ngắn cho trưởng nhóm (tiếng Việt, dễ hiểu), trỏ tới hai thứ trên.

## 5. Ngoài phạm vi tuần này (đã ghi nhận, làm sau)
- **API cho app "SOS Tăng Nhơn Phú"** (hợp đồng API, xác thực app bằng khoá riêng), sau khi xã cho biết cách tích hợp và cách quản lý tài khoản (D1, D11).
- **Bộ câu hỏi thật** để chứng minh tính đúng của dự án (D3).
- **Các thay đổi kiến trúc lớn** (bản duyệt G5–G7):
  - giao diện `Engine` chung cho `strict`/`friendly`/`abi`;
  - một kho hội thoại; bỏ phát lại hội thoại khi sửa câu;
  - phân quyền theo dependency;
  - `pyproject` và CI;
  - một nguồn cài đặt;
  - nhật ký và vết admin.
- Thử chèn lệnh gián tiếp qua tệp tải lên; bộ golden cho Friendly.

## 6. Rủi ro và cách xử lý khi làm
| Rủi ro | Xử lý |
|---|---|
| Sửa làm đổi câu trả lời ngoài ý muốn | Mẫu so khớp G0.2 sau mỗi việc; đọc diff trước khi ghi mốc mới |
| Che số ở điểm ghi làm lịch sử hội thoại của người dùng hiện `[ID]`/`[SDT]` | Chấp nhận (D12: chỉ lưu dữ liệu đã che); lượt hiện tại vẫn xử lý bằng câu gốc trong bộ nhớ |
| Bộ dò chèn lệnh chặt hơn gây chặn nhầm câu Friendly | Kiểm trên 22 tình huống NV2 trước khi bật; có cờ tắt |
| Đổi DB sang theo phiên bản làm hỏng `.bat` cài đặt/khởi động | Cập nhật cả hai `.bat` trong cùng commit 2.1; thử trên bản sao thư mục runtime |
| Hết ngân sách eval | Mỗi lần chạy đủ bộ ghi vào kết quả cuối; quá 3 lần thì dừng và hỏi |
| Nhu cầu GPU làm chậm Friendly | Làm G3.1 trước G4.1; reranker đã nằm sẵn trong VRAM, không thêm model |
| Lineage chưa ghép hết | Báo rõ số ca loại; danh sách cho người duyệt |

## 7. Lệnh hay dùng
```bash
# fixture + test (sau G0.1)
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe run_server.py eval/fixture_db.py
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe run_server.py eval/run_tests.py
# mẫu so khớp (sau G0.2)
PYTHONIOENCODING=utf-8 S3_USE_LLM=0 S3_NO_WARMUP=1 .venv/Scripts/python.exe run_server.py eval/equality.py --compare base
# eval đầy đủ (chỉ 3 lần cả tuần)
PYTHONIOENCODING=utf-8 S3_USE_LLM=0 S3_NO_WARMUP=1 S3_PLANNER_MODE=rules OLLAMA_HOST=http://127.0.0.1:1 \
  .venv/Scripts/python.exe run_server.py eval/run_golden.py thu-tuc --by status
# an toàn
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe run_server.py eval/safety/test_pii_injection.py
```

# Kế hoạch giải quyết `MERGE_PLAN.md`

**Ngày viết:** 2026-10-14. **Trạng thái:** chỉ là kế hoạch, chưa thực hiện bước nào.
**Tài liệu gốc:** `D:\merged_sys3_4\MERGE_PLAN.md` (nằm ngoài repo, trên máy của bạn).
**Mục tiêu:** gộp hai bộ đánh giá (merge suite và draft suite) thành một bộ cho hệ thống hiện tại, sửa phần sai, và chỉ đưa vào báo cáo những số liệu đã đủ tin cậy.

Nguồn:
- Merge: https://github.com/3-hWnG/intern-amazing-group_7/tree/merge_sys_3_4 (commit `e38369d`)
- Draft: https://github.com/3-hWnG/intern-amazing-group_7/tree/draft (commit `c829392`)

---

## 1. Kết quả đọc và kiểm tra

`MERGE_PLAN.md` đáng tin. Hai điểm then chốt đã được kiểm tra trên code hiện tại:

| Điểm kiểm tra | Kết quả |
|---|---|
| Lỗi che số CCCD/SĐT có dấu phân cách | **Có thật** trên branch merge: `034-203-004455` và `0901 234 567` không bị che (0/2). Số liền mạch `034203004455` thì bị che |
| Rủi ro false-positive khi che | **Đã tồn tại sẵn**: `quyết định số 123456789` đang bị che thành `[ID]`. Patch không tạo ra rủi ro mới, chỉ cần ghi nhận hiện trạng |
| Các file cần copy từ draft | Đủ trên `origin/draft`: `Code/eval/rank_metrics.py`, `run_pseudo_rank.py`, `safety/README.md`, `safety/test_pii_injection.py`, `cases_real_log_v1.json` |

Khác biệt cần nhớ so với tài liệu gốc:
- Trên máy này `origin` đã là repo group_7, không có remote `g7`. Dùng `origin/draft` và `origin/merge_sys_3_4` thay cho `g7/...`.
- `origin/draft` từng bị force-push (`7e7f3f8` thành `c829392`). Luôn ghim theo commit, không theo tên branch.

---

## 2. Nhận xét ngắn

**Điểm mạnh**
- Chỉ đúng gốc vấn đề: hai bộ cách làm khác nhau, và bộ golden của draft có lỗi nhãn nặng (§2.5 gốc).
- Có danh sách "số không được trình bày" và bảng "claim nào được nói sau phase nào".
- Sửa được phần paper bị nói quá (CRAG, RouteLLM, các ngưỡng chỉ là mục tiêu của team).
- Nguyên tắc đúng: chỉ đưa số RAGAS vào báo cáo khi grader qua kiểm chứng (lỗi cài sẵn và κ với người chấm).

**Rủi ro**
1. Phạm vi lớn: Phase B + C + D mất vài ngày và 5–6 giờ GPU, trong khi Phase A đã cho gần đủ một báo cáo.
2. Phase B (tái sinh bộ multi-domain) là phần đáng ngờ nhất. Bộ draft: ~78% đáp án chỉ là placeholder, ~23% ngoài phạm vi trả lời được, 99% thủ tục holdout trùng với dev.
3. Quyết định D5 (thủ tục theo tỉnh) là quyết định sản phẩm, không phải kỹ thuật. Cần leader chốt.
4. Bộ real-log đã bị đọc lỗi nên chỉ gắn `holdout-used`, không dùng làm số blind chính.
5. Việc chấm tay (D7) là điểm nghẽn thật. Có thể giảm xuống còn khoảng 30–45 phút bằng "chế độ ít chấm tay" (mục 4.1), đổi lại claim yếu hơn.
6. Port khối masking đụng code đang chạy (`server/policy/policy.py`), phải làm commit riêng và chạy đủ gate.

---

## 3. Quyết định cần chốt (D1–D7)

| ID | Câu hỏi | Đề xuất | Ai chốt |
|---|---|---|---|
| D1 | Bộ golden multi-domain của draft | (c) chỉ lấy các loại câu hỏi vào bộ template; hoặc (a) tái sinh bản hẹp nếu còn thời gian | Bạn |
| D2 | Cách chạy lại RAGAS | (c) RAGAS-lite 100–150 ca, grader 7B, rồi mở rộng nếu còn thời gian | Bạn |
| D3 | Đầu ra cũ của draft | (a) lưu vào `eval/archive/draft-2026-10-13/` kèm README, xoá file `.bak` | Bạn |
| D4 | Port sửa lỗi che số vào `policy.py` | (a) Có, commit riêng, chạy đủ gate | Bạn |
| D5 | Thủ tục theo tỉnh: `answer` hay `apologize` | Chưa đề xuất, hỏi leader. Nếu chọn `apologize` thì cũng là lỗi hệ thống (đang trả lời 83/83) | **Leader** |
| D6 | Mô hình chấm RAGAS | (a) qwen2.5:7b | Bạn |
| D7 | Công sức chấm tay | (a) Đầy đủ: 50 ca golden + 30 ca RAGAS, ~2–3 giờ, được nói "expert-reviewed" và "hiệu chuẩn theo người". (b) **Ít chấm tay (đề xuất)**: máy và LLM làm phần lớn, bạn chỉ chấm 10–15 ca đối chứng và các ca hai grader bất đồng, ~30–45 phút (mục 4.1). (c) Bỏ chấm tay: không có claim "reviewed" hay "calibrated" | Bạn |

D4 là quyết định duy nhất Đợt 1 phụ thuộc vào. D5 chỉ cần khi làm Phase B.

---

## 4. Kế hoạch thực hiện

Mỗi đợt dừng lại được. Làm trên branch mới `eval-merge`, commit nhỏ, không push khi chưa được phép.

### Đợt 0 — Chuẩn bị (~10 phút)
- [ ] `git fetch origin merge_sys_3_4 draft`; xác nhận tip còn là `e38369d` và `c829392`. Nếu đã đổi, so lại thư mục `eval/` trước khi port.
- [ ] `git checkout -b eval-merge`.
- [ ] `git worktree add ../g7-draft origin/draft` để đọc bản draft.
- [ ] Copy file bằng Git Bash: `git show origin/draft:Code/eval/<file> > eval/<file>`. Không dùng PowerShell redirect (đổi encoding) và không dùng `git checkout origin/draft -- ...` (kéo file vào `Code/`).

### Đợt 1 — Không cần GPU, ra báo cáo dùng được (A1–A9)

| Bước | Việc | Xong khi |
|---|---|---|
| A1 | Copy `rank_metrics.py` sang `eval/`, chạy self-test | In ra `rank_metrics selftest OK` |
| A2 | Thêm MRR và nDCG@5 vào `eval/run.py` (diff 54 dòng của draft) và `run_golden.py`. Dùng `best_match` theo từng task; top-1 và RR phải tính trên cùng một danh sách ứng viên | Bảng `run_golden.py` có cột MRR / nDCG@5 |
| A3 | Thêm khoảng tin cậy Wilson 95% cho mọi tỷ lệ trong `run_golden.py` | Ví dụ "60/77 (78%, 67–86%)" |
| A4 | Sửa phát lại hội thoại nhiều lượt: lượt assistant hiện rỗng trong `build_golden.py`. Cho `run_golden.py` phát lại trực tiếp như `run_pseudo.py` | Kết quả đa lượt khớp `run_pseudo.py` trên cùng bộ. Kiểm lại pseudo_real 2 (22/28 so với 19/28 trong `docs/EVAL.md`) |
| A5 | Chạy lại HOLDOUT-4 trên code hiện tại: `python run_server.py eval/run_golden.py thu-tuc --by source` | MRR/nDCG mới ghi vào `docs/PLAN_TUAN_TOI.md` |
| A6 | Copy `eval/safety/` từ draft; chạy chế độ unit rồi `--e2e` **trước khi vá** | Tái hiện được D1 dấu phân cách 0/3 |
| A7 | Port khối masking (`_PII_SEP`, `_PII_RUN`, `_PII_CURRENCY_AFTER`, `mask_pii`) vào `server/policy/policy.py`, **commit riêng**, giữ `_CGEN` của merge. Chạy gate trong `docs/CONTRIBUTING.md`, `eval/run_all.py --quick` (kỳ vọng 27/33, 6 ca trượt cũ) và bộ safety. Ghi `quyết định số 123456789` vào docs như rủi ro đã biết | Safety: D1 9/9 + 3/3, FP 0/5, D2 11/11, 0/6, e2e 17/17; gate không giảm |
| A8 | Copy `cases_real_log_v1.json` + `REAL_LOG_v1.md`; thêm vào `build_golden.py` với status `holdout-used`; kiểm mọi `expect_ids` tồn tại trong `data/snapshot/procedures.jsonl` | `thu-tuc.jsonl` có 29 lượt real-log |
| A9 | Chạy lại `eval/report.py`, cập nhật bảng A–D trong `docs/PLAN_TUAN_TOI.md` | Có bản báo cáo tầng A, C, D |

Thứ tự: A1 → A2 → A3 → A4 → A5 (A4 trước A5 vì ảnh hưởng số HOLDOUT-4), rồi A6 → A7, rồi A8 → A9.

### Đợt 2 — RAGAS (máy GPU của bạn, chạy qua đêm)
Chỉ làm nếu cần số chất lượng câu trả lời.
- [ ] C1: viết `eval/ragas_build.py`: dataset dùng chung, contexts là `field_chunks` mà hệ thống thật sự dùng, reference là `expected.reference`; lấy mẫu ~150 ca phân tầng theo lĩnh vực.
- [ ] C2: kiểm grader: (a) chèn một claim bịa, faithfulness phải giảm; (b) ghép câu trả lời với câu hỏi của ca khác, relevancy phải giảm.
- [ ] C3: bạn chấm tay ~30 ca; tính Cohen's κ so với từng grader. (Nếu chọn D7(b): xem mục 4.1, thay bằng C3b.)
- [ ] C4–C5: chạy `run_ragas_lite.py` (thêm `--judge-model` nếu cần) và `ragas_runner.py --score`. Chạy thử `--limit 10` trước.
- [ ] C6: báo cáo mỗi metric gồm: số ca chấm được, trung bình kèm CI, tỷ lệ bắt lỗi cài sẵn, κ. Chỉ giữ metric nào control qua và κ ≥ ~0.6.

Thời gian ước tính: ~64–70 giây/ca; 150 ca ≈ 5–6 giờ.

### Đợt 3 — Tài liệu (Phase D)
- [ ] D1: mở rộng `eval/report.py` in cả 4 tầng, kèm liên kết file RAGAS mới nhất.
- [ ] D2: gộp `eval/CRITERIA.md` với `05_methodology/bo_evaluation_hoan_thien_v2.md` của draft, thay mọi số bằng số của Đợt 1–2.
- [ ] D3: dùng **một** cách đánh số paper (draft có 33 bài, merge có 20 bài với số khác).
- [ ] D4: xử lý đầu ra cũ của draft theo D3 ở trên.
- [ ] D5: viết lại "tóm tắt 1 phút cho mentor" chỉ dùng claim cho phép ở §5.

### 4.1 Chế độ ít chấm tay (D7 = b)

Dùng khi không đủ 2–3 giờ chấm tay. Máy làm phần có đáp án xác định, LLM mạnh làm phần cần phán đoán, bạn chỉ chấm mẫu đối chứng.

| Việc | Thay cho | Cách làm | Ai làm |
|---|---|---|---|
| **B9b** Kiểm nhãn theo luật | Rà tay 50 ca (phần kiểm tra được bằng máy) | Chạy script audit (Phụ lục A của `MERGE_PLAN.md`, chỉnh tên trường cho định dạng mới) trên toàn bộ ca sinh: thủ tục tồn tại, trong phạm vi, mức phí khớp `fees_clean`, "miễn phí" không có điều kiện, tên không trùng nhiều thủ tục, id không trùng. Tính tỷ lệ ca vi phạm | Máy |
| **B9c** LLM rà | Rà tay 50 ca (phần cần phán đoán) | Một LLM mạnh rà 50 ca phân tầng theo loại câu hỏi: câu hỏi có tự nhiên không, đáp án kỳ vọng có đúng với nguồn không. Lưu đúng/sai kèm lý do vào file rà (`reviewed_by: "llm:<tên model>"`) | LLM |
| **B9d** Đối chứng người | Rà tay toàn bộ | Bạn chấm 10–15 ca ngẫu nhiên từ 50 ca đó. Tính tỷ lệ đồng ý giữa bạn và LLM | Bạn (~15 phút) |
| **C3b** κ theo grader mạnh | Bạn chấm 30 ca RAGAS | Chạy grader mạnh trên 30 ca; tính κ của qwen 7B/4B so với grader mạnh. Chỉ dùng ca tổng hợp (không có dữ liệu công dân) nếu gửi ra API | LLM |
| **C3c** Kiểm số theo luật | Chấm "faithful" thủ công cho số liệu | Mọi con số/mức phí trong câu trả lời phải xuất hiện trong context (`run.py` đã làm). Không cần LLM | Máy |
| **C3d** Đối chứng người | Chấm 30 ca | Bạn chấm chỉ các ca mà hai grader bất đồng, tối đa ~15 ca. Ghi tỷ lệ đồng ý | Bạn (~15–30 phút) |

Kiểm chứng bằng lỗi cài sẵn (C2) vốn đã tự động.

**Ghi nguồn cho từng con số.** Mỗi con số trong báo cáo phải ghi một trong ba nguồn: `máy`, `LLM`, `người`.

**Claim yếu hơn khi dùng chế độ này:** "LLM-audited, với X% đồng ý với người trên N ca mẫu", không phải "expert-reviewed". "κ so với grader mạnh", không phải "hiệu chuẩn theo người". Hội đồng có thể hỏi ai là người kiểm chứng; câu trả lời là mẫu đối chứng nhỏ B9d và C3d.

### Đợt 4 — Tuỳ chọn, chỉ khi còn thời gian (Phase B)
Tái sinh bộ multi-domain (nếu chọn D1(a)): đọc thủ tục từ DB, dùng cùng quy tắc phạm vi với hệ thống, chia dev/holdout theo `proc_id`, tham chiếu thật từ `field_chunks`, đáp án phí từ `fees_clean`, sửa slang, ca injection kỳ vọng `apologize`, dùng tên đầy đủ, rà tay 50 ca. Sau đó chạy lại script audit (Phụ lục A của `MERGE_PLAN.md`); mọi dòng §2.5 phải về 0 hoặc có giải thích.

### Ngoài phạm vi (làm sau)
Golden set cho System 4 Friendly; injection gián tiếp qua tài liệu tải lên; điền bảng kiểm dữ liệu 50 bản ghi; log người dùng thật; sửa `amount_value` trong `data/build.py`; bỏ số 1350 cứng trong `test_nv4.py`.

---

## 5. Claim được phép nói, theo từng đợt

| Claim | Được nói sau |
|---|---|
| HOLDOUT-4 top-1 / behaviour / clarify trên code hiện tại | Ngay bây giờ (số của merge) |
| MRR / nDCG trên code hiện tại; CI cho mọi số | Đợt 1 (A2–A5) |
| "Lỗi che số do bộ safety phát hiện, đã sửa, có test hồi quy" | Đợt 1 (A6–A7) |
| Số RAGAS bất kỳ | Đợt 2, chỉ metric qua control và κ |
| "Expert-reviewed" | Chỉ cho những ca thực sự được rà tay (D7 a). Chế độ ít chấm tay (D7 b) chỉ được nói "LLM-audited" kèm tỷ lệ đồng ý với người trên mẫu đối chứng |
| "Blind" | Chỉ HOLDOUT-3/4, h5, h6, pseudo_real 1–3, team set; không bao giờ cho bộ sinh tự động hay bộ real-log đã đọc |
| Chất lượng câu trả lời theo LLM | Cho tới khi xong Đợt 2: ghi "chưa đo đáng tin" |

**Không trình bày:** số RAGAS của draft (0.40 / 0.38 / 0.81 / 0.68); "0% số bịa trên 394 ca" như bằng chứng; "blind holdout" hay "expert-reviewed" cho bộ sinh tự động; các ngưỡng của draft như chuẩn trong văn liệu.

**Sửa khi thuyết trình:** Paper 18 (CRAG) chỉ là phép so sánh, vì "Ambiguous" của nó không hỏi lại người dùng; Paper 25 (RouteLLM) không nói về rò rỉ tập test, dùng Paper 09 và 12 thay thế; Paper 23 là bài về fine-tuning, không dùng để chống đỡ cho CI.

---

## 6. Quy tắc làm việc
- Làm trên branch `eval-merge`; commit nhỏ; việc sửa `policy.py` là commit riêng.
- Trước mỗi commit: chạy gate trong `docs/CONTRIBUTING.md`; với A7 thêm `eval/run_all.py --quick` và bộ safety.
- Không push, không mở PR khi chưa được bạn đồng ý.
- Nếu một phase cho kết quả bất ngờ (ví dụ MRR giảm mạnh sau A4), dừng và báo trước khi đi tiếp.

---

## 7. Kết quả Đợt 2 (2026-10-14): RAGAS-lite, giám khảo qwen2.5:7b, chế độ ít chấm tay

**Cách làm (D2 c, D6 a, D7 b).** `eval/run_ragas_lite.py` chia hai pha: `--phase build` sinh câu trả lời bằng model của hệ thống (không đổi model giữa chừng), `--phase score --judge-model qwen2.5:7b` chấm. Mẫu 92 ca (100 ca chọn, 8 ca hệ thống từ chối nên bỏ): 35 ca composer, 34 ca khuôn, 23 ca golden blind. Mỗi ca chấm ~95–110 giây trên GTX 1660 SUPER 6 GB (7B chạy 21% CPU / 79% GPU), tổng ~2,8 giờ; chấm xong 92/92 ca, không lỗi giám khảo.

| Chỉ số | Giá trị | Ca chấm được | Ghi chú |
|---|---|---|---|
| Faithfulness | 0,825 | 92/92 | Xem đối chứng: không dùng được |
| Answer relevancy | 0,777 | 92/92 | Giám khảo cho 0 ở 16/92 ca |
| Context precision | 0,443 | 66/92 | 26 ca giám khảo không trả đủ giá trị |
| Context recall | 0,896 | 81/92 | Tham chiếu lấy từ cùng DB nên gần như tự động; không đo nhiều |
| Số tiền/ngày/giờ trong câu trả lời có trong ngữ cảnh (luật) | 87% (80/92) | 92/92 | Chỉ số luật, không dùng LLM; xem `numbers_ok` |

**Đối chứng giám khảo (C2)**

| Phép thử | Kết quả |
|---|---|
| Chèn ý bịa ("miễn phí hoàn toàn, giải quyết trong 1 giờ"): faithfulness phải giảm | giảm ở **47/92 (51%)**. 4B trước đó là 9/30 (30%). Giám khảo 7B vẫn bỏ sót gần một nửa ý bịa |
| Ghép câu trả lời với câu hỏi của ca khác: relevancy phải giảm | giảm ở **74/76 (97%)**. Phân biệt lạc đề tốt |
| Relevancy trên câu trả lời đúng bị chấm 0 | 16/92 (17%) |

**Hiệu chuẩn (C3b, 30 ca phân tầng, chuẩn là LLM: Claude chấm theo thang trong `eval/ragas_calib.py`)**

| Chỉ số | Đồng ý | Cohen's κ |
|---|---|---|
| Faithfulness (giám khảo ≥ 0,8 so với "faithful") | 17/30 | **0,02** |
| Relevancy (giám khảo ≥ 0,5 so với rel ≥ 1) | 24/30 | **0,20** |

Cả hai κ thấp hơn nhiều ngưỡng ~0,6 đặt ra ở C6. Chuẩn LLM chấm 28/30 ca là faithful (chỉ `pr-21` và `tpl-legal-37`, nơi câu trả lời nêu thời hạn/lệ phí hoặc căn cứ pháp lý không nằm trong ngữ cảnh), còn giám khảo 7B chấm thấp nhiều ca mà câu trả lời chép nguyên văn ngữ cảnh. Nguyên nhân phổ biến: giám khảo tách "tiêu đề thủ tục", dòng nguồn, link thành ý rồi gắn nhãn không có trong ngữ cảnh.

**Kết luận được phép nói**
- Chất lượng câu trả lời theo RAGAS-lite với giám khảo 7B **chưa đo đáng tin**: faithfulness và relevancy không qua đối chứng ý bịa (51%) và có κ thấp (0,02 và 0,20). Không đưa 0,825 / 0,777 vào báo cáo như điểm chất lượng.
- Chỉ số luật (`numbers_ok` 87%) và rule-based `run.py` (bịa số, focus) vẫn là bằng chứng chính cho chất lượng câu trả lời.
- Context precision chưa có đối chứng riêng; chỉ ghi như số tham khảo.
- Nguồn từng con số: giám khảo = `LLM (qwen2.5:7b)`; chuẩn hiệu chuẩn = `LLM (Claude)`; số luật = `máy`. **Chưa có chấm tay của người**: phiếu 15 ca bất đồng ở `eval/results/ragas_calib_human_sheet_d2.md`; xong thì chạy lệnh trong phiếu để có κ theo người (C3d). Tới lúc đó chỉ được nói "LLM-audited".

**Phát hiện thêm trong lúc chấm**
- Ngữ cảnh đưa cho giám khảo chỉ là các trường mà `chunks_of` lấy, không phải đúng thứ Answerer đã dùng: ca `pr-21` câu trả lời nêu thời hạn và lệ phí nhưng ngữ cảnh chỉ có phần mô tả. Cần sửa ở bước dựng dataset (C1) nếu muốn faithfulness có nghĩa.
- Dữ liệu `p18-p18_B_single-12` ghi "5.000 đồng" ở phần số nhưng "7.000 đồng" trong mô tả cho cùng mục phí; hệ thống chép nguyên nên đúng với nguồn, nhưng là điểm lệch dữ liệu nguồn.
- Nhiều ca so sánh ("So sánh A với B") chỉ trả lời về A: relevancy 1/2 theo chuẩn LLM. Liên quan lỗi so sánh đã biết, ngoài phạm vi Đợt 2.

**File kết quả (thư mục `eval/results/`, bị `.gitignore`):** `ragas_dataset_d2.json`, `ragas_lite_d2.json`, `ragas_partial_d2.jsonl`, `ragas_score_d2.log`, `ragas_calib_d2.json`, `ragas_calib_llm_d2.json`, `ragas_calib_human_sheet_d2.md`.

---

## 8. Kết quả Đợt 3 (2026-10-14): tài liệu

| Bước | Kết quả |
|---|---|
| D1 | `eval/report.py` in thêm mục D' (an toàn: chạy `test_pii_injection.py --e2e`) và mục F (trích kết quả RAGAS mới nhất cùng đối chứng giám khảo, kèm cảnh báo chưa đủ tin cậy). Đã chạy thử: 113 giây |
| D2 | `eval/CRITERIA.md` viết lại: khung 4 tầng A–D của draft cộng công cụ của merge, mọi số lấy từ Đợt 1–2, ngưỡng ghi là mục tiêu của nhóm, bảng paper đã sửa (CRAG, RouteLLM, ngưỡng, Paper 23) |
| D3 | Dùng **một** cách đánh số: `docs/research paper/PAPER_LIST_33.md` và `paper_summaries/` (33 tệp, chép từ draft). `docs/research paper/README.md` có mục cảnh báo ba cách đánh số lệch nhau (ví dụ LegalBench-RAG là thư mục 06 nhưng là Paper 08) |
| D4 | Chọn D3(b): không chép đầu ra cũ của draft (22 MB); `eval/archive/draft-2026-10-13/README.md` giữ bảng số cũ và lý do không dùng; lịch sử ở commit `c829392` |
| D5 | `docs/TOM_TAT_EVAL_CHO_MENTOR.md`: bản nói 1 phút, bảng số cần nhớ, danh sách được nói và không được nói, chỉ dùng claim cho phép ở mục 5 |

Còn lại: phiếu chấm tay 15 ca (C3d) để nâng "LLM-audited" lên "có đối chiếu người"; Phase B (golden đa lĩnh vực) chưa làm theo D1c; `check_docs` còn 8 lỗi từ trước (số trong README, "số sự kiện" 11 so với 12).

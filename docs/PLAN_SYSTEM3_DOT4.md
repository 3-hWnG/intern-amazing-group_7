# Plan System 3 — đợt 4 (cập nhật 2026-10-06, hướng hybrid)

## Bối cảnh đổi hướng
Nhóm đã phản hồi sau vòng test (`System-3-Feedback-lan-1/2.pdf`) và muốn System 3 theo kiến trúc G7 (`He-thong-3_Semantic-Planner_Slide-4.docx`): LLM (Qwen3-4B) là Semantic Planner, Direct + RAG, Answer Composer, Verifier.

Điểm yếu nhóm nêu: chưa **concise** (dư thủ tục, dư bước), **multi-intent bắt lung tung** ("quá nhạy"), teencode/gõ đời thường làm break, thiếu thông tin được hỏi (vd thời hạn), nút "chủ đề mới" không chạy, config không có chỉ báo AI bật hay tắt, cần nút "Tạo bảng full" (System 2) thay "đọc thêm ở Dịch vụ công". Điểm tốt: multi-intent bắt được, không bị lừa sang chủ đề khác, usability tốt.

**Quyết định (người dùng đồng ý 2026-10-06):** huỷ quyết định "bỏ LLM khỏi Planner". Chuyển sang **hybrid**:
- Luật cho kế hoạch mặc định (nhanh, ổn định, đã đo).
- Qwen3-4B chạy **nền**, timeout **7 s**, chỉ đề xuất sửa kế hoạch. Mặc định **bị từ chối**; chỉ được thêm/sửa/xoá khi tự đánh giá cực chắc (confidence rất cao, ngưỡng đặt bằng số đo, ví dụ >= 0,95–0,99) **và** verifier đồng ý.
- Kết luận cũ "LLM không giúp Planner" bị nhiễu bởi timeout 2,5 s (đa số lần gọi rơi về luật). Phải đo lại công bằng.
- Answer Composer và Verifier giữ như hiện tại (LLM chỉ sinh chữ có trích dẫn, qua verifier), mở rộng khi cần cho concise.

Nguyên tắc chung (EVAL.md): không tune trên HOLDOUT-3; giao việc cho agent chỉ bằng nhóm lỗi chung; mỗi phase ghi số trước/sau.

## Kết quả cuối đợt 4 (2026-10-06)
| Phase | Kết quả |
|---|---|
| 14 | Xong. |
| 15 | Xong (pseudo_real). |
| 16a | Xong: gate xanh. |
| 17 | Xong: chỉ số concise (`run_concise.py`). |
| 18 | Xong: DEV focus 70% → 99%, task thừa 0; bộ team 3/10 → 7/10. |
| 19 | Xong, **hybrid không đạt gate** (không có lần sửa nào đúng hơn) → mặc định luật. |
| 20 | Xong: Tạo bảng full, chỉ báo/panel AI, sửa reset, UI gọn, `knowledge/`. |
| 21 | Xong, **không đạt mục tiêu**: HOLDOUT-4 top-1 75% (mục tiêu 80%), hành vi 82% (mục tiêu 88%), hỏi lại 8/16. Hybrid kém luật 2 câu. |
| 22 | Xong: README, docs, báo cáo nhóm (`BAO_CAO_DOT4.md`), dọn `eval/results/`. |

## Trạng thái (ghi lúc đầu đợt, giữ để tham khảo)
| Phase | Việc | Trạng thái |
|---|---|---|
| 14 | Dọn nợ kỹ thuật | **Xong.** DEV top-1 91,5%, bịa số 2,9%, synth TEST 93,1%. Chưa thử cài venv sạch (pip lỗi SSL). |
| 15 | Bộ pseudo_real (agent mới, 30 câu đơn + 4 hội thoại) | **Xong.** Số gốc: hành vi 30/42 (71%), top-1 11/30 (37%), top-3 15/30, hỏi lại 1/6, xin lỗi 6/6. Đã bị xem lỗi → không tune trên bộ này. |
| 16 | Sửa nhóm lỗi chung | **Tạm dừng, kết quả mất.** Agent có sửa `context.py`, `rank.py`, `refs.py`, `orchestrator.py`, `main.py` nhưng không có báo cáo; chưa kiểm. Xem Phase 16a. |
| 18 | Sửa theo nhóm lỗi chung (A–F, xem dưới) | **Xong (2026-10-06)**, báo cáo: `eval/P18_REPORT.md`. DEV focus 70% → 97,5%, HOLDOUT cũ 59% → 96%, task thừa 11 → 0; gate hồi quy xanh. Chờ nghiệm thu bằng bộ mù/team/pseudo_real. |

## Phase 16a — Kiểm lại hiện trạng (làm trước)
- Chạy lại toàn bộ gate: `test_data`, `memory_test`, `context_test`, `answer_llm_test`, `smoke_test`, `selftest`, `run.py --split all`, `run_ctx.py`, `synth_retrieval.py`.
- So với mốc sau Phase 14 (DEV top-1 91,5%, bịa số 2,9%, ngoài phạm vi 30/30, ctx 88/91, synth TEST 93,1%).
- Tụt gate → khoanh vùng thay đổi dở và hoàn tác phần gây tụt; không tụt → giữ và ghi lại chúng làm gì (đọc diff các file trên).
- **Gate:** có báo cáo trung thực về trạng thái; mọi gate hồi quy xanh.

## Phase 17 — Chỉ số concise / đúng trọng tâm (ưu tiên cao nhất)
Nhóm đánh giá chủ yếu ở đây mà ta chưa có số.
- Thêm vào bộ chấm (`rules_scorer.py` hoặc scorer mới), chấm bằng luật trên cấu trúc câu trả lời:
  - **Đúng trọng tâm:** câu hỏi một field (vd thời hạn) thì câu trả lời chứa field đó và không kèm các field khác (trừ khi hỏi).
  - **Không thừa thủ tục:** số thủ tục/khối trong câu trả lời so với số ý (task) hợp lệ.
  - **Ngắn:** số ký tự/dòng so với trần theo loại câu; không có bước thực hiện khi không được hỏi.
  - **Đủ thông tin được hỏi:** vd hỏi "bao lâu" thì có thời hạn.
- Chấm cả bộ DEV, bộ hội thoại và pseudo_real; ghi số gốc trước khi sửa.
- **Gate:** có số concise gốc (DEV + pseudo_real) và ngưỡng mục tiêu được người dùng duyệt.

**Định nghĩa và ngưỡng (duyệt 2026-10-06):** concise = trả lời đúng ý người hỏi, hỏi field nào thì chỉ trả field đó. Mục tiêu: DEV focus ≥ 90% (gốc 70%), HOLDOUT cũ ≥ 85% (gốc 59%), task thừa DEV ≤ 2% (gốc 4,8%), team (chấm luật) ≥ 7/10 (gốc 3/10). Độ dài ký tự chỉ theo dõi, không đặt ngưỡng. Số gốc: `eval/results/concise_base.json`.

## Phase 18 — Sửa theo nhóm lỗi chung (thay cho Phase 16 cũ)
Mỗi nhóm một lượt, chạy tuần tự, kiểm DEV + ctx + synth sau mỗi nhóm. Không dùng câu/chủ đề của bộ mù. Cách mô tả nhóm cho agent: chỉ nêu nhóm chung (không nêu câu hay chủ đề của pseudo_real).
- **A. Concise:** câu trả lời trả đúng field được hỏi, bỏ thủ tục và bước thừa; bản đầy đủ chuyển sang nút "Tạo bảng full" (Phase 20).
- **B. Multi-intent bớt nhạy:** chỉ tách task thứ hai khi có tín hiệu rõ (từ nối, hai đối tượng khác nhau, hai field khác loại); không kéo thủ tục lân cận khi người dùng chỉ hỏi một việc.
- **C. Hỏi lại khi mơ hồ** (≥ 3 bản gần nhau, thiếu yếu tố phân biệt); thẻ nút + gõ tự do; không hỏi lần hai.
- **D. Từ chối nhầm** (kho có thủ tục nhưng xin lỗi) và **chọn nhầm anh em** (cùng họ thủ tục khác loại).
- **E. Gõ đời thường:** teencode, không dấu, viết tắt, lỗi chính tả, câu kể hoàn cảnh.
- **F. Hội thoại nhiều lượt:** "cái thứ n", "à không ý tôi là", câu nối, bổ sung hoàn cảnh.
- **G. Bảng sự kiện đời sống** dựng từ dữ liệu thay `_EVENTS` viết tay (nếu gọn).
- **Gate:** DEV top-1 ≥ 91%, bịa số ≤ 3%, ngoài phạm vi 30/30, ctx ≥ 88/91, synth TEST ≥ 92% và chênh TRAIN/TEST ≤ 5 điểm; số concise không tụt, cải thiện theo ngưỡng Phase 17.

## Phase 19 — Planner hybrid (Qwen3-4B nền, timeout 7 s) — ĐÃ LÀM: gate không đạt, giữ tắt mặc định (eval/P19_REPORT.md)
- Planner luật chạy trước và trả kế hoạch ngay (đường chính). Song song, Qwen3-4B (tắt chế độ nghĩ) sinh kế hoạch JSON (`tasks[]`, `procedure_id`, `fields`, `conditions`, `relation`, `confidence`).
- **Cơ chế hợp nhất:** mặc định giữ kế hoạch luật. LLM chỉ được:
  - **thêm** một task, **sửa** field/proc, hoặc **xoá** một task khi `confidence` ≥ ngưỡng **và** đề xuất qua kiểm của Policy (thủ tục tồn tại trong kho, field hợp lệ, phạm vi). Ví dụ điển hình: "đây không phải multi-intent, 99%" → xoá task thừa.
  - Quá 7 s hoặc lỗi → giữ kế hoạch luật.
- Câu trả lời đợi tối đa 7 s cho LLM; có log trong `trace` (đề xuất gì, chấp nhận hay từ chối, vì sao) để giải thích được.
- **Đo công bằng:** cùng bộ DEV + ctx + pseudo_real, bật/tắt LLM; ghi số top-1, hành vi, bịa số, multi-intent, concise, p50/p95, tỉ lệ timeout, số lần LLM sửa đúng/sửa sai. Quét ngưỡng confidence trên DEV (không dùng HOLDOUT-3 hay pseudo_real để chọn ngưỡng).
- **Gate:** có bảng so sánh; chỉ bật mặc định nếu LLM tăng điểm có ý nghĩa (≥ 2 điểm trên chỉ số chính) và không tăng bịa số; không thì để tắt mặc định, giữ cờ bật, ghi vào tài liệu. p95 tổng ≤ 10 s khi bật.

## Phase 20 — Tính năng chất lượng sống (nhóm đã yêu cầu) — ĐÃ LÀM (eval/P20_REPORT.md)
Làm dạng tháo/lắp, không phá bản cũ.
- Nút **"Tạo bảng full"** (System 2) thay "đọc thêm ở Dịch vụ công": hiển thị toàn bộ field của thủ tục đang nói. Không dùng MCQ trước.
- **UI cấu hình** có chỉ báo nhìn thấy được: AI Planner (bật/tắt), Answer Composer (bật/tắt), timeout, ngưỡng confidence, trạng thái model đã nạp. Bật/tắt qua UI, không chỉ biến môi trường.
- Kiểm lại nút "Bắt đầu chủ đề mới" trên giao diện (đã sửa lỗi reset hôm nay, cần nhóm xác nhận trên bản của họ).
- Chuẩn bị cho Box 5B/6B (RAG, import PDF/DOC): chỉ **thiết kế giao diện** (interface, thư mục `knowledge/`), không build RAG trong đợt này.
- **Gate:** từng nút/chỉ báo chạy được, kiểm bằng trình duyệt; test hồi quy xanh.

## Phase 21 — Bộ mù mới và nghiệm thu
- Agent mới soạn **HOLDOUT-4** (~90 câu, không thấy mã và lỗi cũ), đáp án tra DB. Ghi giả định vào `H4_ASSUMPTIONS.md`. Kèm pseudo_real thứ hai (30 câu mới) cho đời thường.
- Chạy một lần cho cả hai chế độ: luật thuần và hybrid.
- **Gate mục tiêu (chưa hứa):** top-1 ≥ 80%, đúng hành vi ≥ 88%, bịa số ≤ 5%; concise đạt ngưỡng Phase 17. Không đạt thì báo trung thực, không vá theo câu; quay Phase 18 với nhóm lỗi chung mới.
- Bộ `real`: khi có câu thật từ người dân, đưa vào `eval/cases_real.jsonl` và chạy làm bộ kiểm cuối.

## Phase 22 — Chốt đợt 4
- Cập nhật README (số đo, giới hạn), ARCHITECTURE (box nào theo G7, box nào khác), EVAL, CONTRIBUTING, SETUP (cài venv sạch khi có mạng).
- Báo cáo ngắn và báo nhóm: Box 1–4 làm đến đâu, Planner hybrid có lợi không, mục nào còn thiếu (5B RAG, 6B import).
- Người dùng tự push GitHub.

## Thứ tự
16a → 17 → 18 → 19 → 20 → 21 → 22. Phase 20 có thể làm song song với 19 vì khác file (UI và server config), miễn gate hồi quy xanh.

## So khớp với G7
| Box | Đợt này |
|---|---|
| 1, 2 | giữ; thêm UI config (Phase 20) |
| 3 Semantic Planner | hybrid luật + Qwen3-4B nền (Phase 19) |
| 4 Validate/Policy/Router | giữ; là cổng cho đề xuất của LLM |
| 5A, 6A | giữ |
| 5B, 6B (RAG, import) | chưa làm; chỉ chuẩn bị giao diện |
| 7 Evidence bundle | giữ (Direct); gộp RAG khi có 5B |
| 8 Answer Composer | giữ + chuyển sang concise (Phase 18A) |
| 9 Verifier | giữ; cân nhắc kiểm nghĩa nếu còn thời gian |
| 10 Phản hồi | giữ; thêm nút "Tạo bảng full" |

## Rủi ro
- LLM nhỏ "khờ": đề xuất sai đẩy số xuống. Luôn cần Policy kiểm và ngưỡng cao; có công tắc tắt.
- Thêm 2–7 s độ trễ cho GTX 1660 Super; cần chế độ tắt nhanh.
- Bộ mù/pseudo_real vẫn do model soạn; chỉ câu thật mới là bằng chứng ngoài.
- Sửa nhóm lỗi dễ tune quá khớp: bắt buộc đối chiếu synth TRAIN/TEST.

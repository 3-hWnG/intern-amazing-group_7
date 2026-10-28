# Điểm mạnh nhất để xoáy sâu (bước c)

Phân tích để chọn trục cho bài 1. Mọi số lấy từ:

- `docs/BAO_CAO_CAU_KHO_2026-10-25.md`: test real_v2, mục 4–6;
- `eval/saved_results/2026-10-22_real_v1/report.md`: số của bản gốc trên real_v1, đo trước khi viết luật mới;
- `eval/hard/results/`.

Repo nguồn: `intern-amazing-group_7-merge_sys_3_4`, commit kết quả `7d199f3`.

## 1. Kết luận ngắn

Trục mạnh nhất là **khoảng cách giữa bộ test do nhóm tự viết và câu hỏi thật của người dân, và cách đóng khoảng cách đó**. Một lớp luật minh bạch quyết định trả lời / hỏi lại / từ chối đóng được phần lớn khoảng cách này trên bộ test thật đã khoá. Hai thành phần học máy (reranker, model 4B đọc câu) chạy cùng giao thức thì kém hơn khi đứng một mình và gần như không thêm gì khi ghép vào lớp luật.

Ba bằng chứng đỡ trục này:

| # | Bằng chứng | Số | Độ chắc |
|---|---|---|---|
| E1 | Bản gốc làm tốt trên bộ nhóm tự viết nhưng kém hẳn trên câu thật | Cùng code đã đóng băng (`b7010d1`), mọi cờ tắt, tức trùng bản gốc ở từng câu:<br>• hành vi đúng: golden blind 400/518 (77,2%) → test real_v2 56,5% (177/313)<br>• top-1: 274/381 (71,9%) → 20/59 (33,9%)<br>• từ chối đúng: 52/58 (89,7%) → 132/248 (53,2%)<br>Dev real_v1 (22/10) cho cùng chiều: 158/282 (56,0%), top-1 7/55 (12,7%), từ chối đúng 116/220 (52,7%) | Mạnh: cùng code, cùng DB, ba bộ. Ghi chú: golden do nhóm viết, nhiều câu nhiều lượt; khi so phải nói rõ khác biệt về loại câu |
| E2 | Trên câu thật, phần lớn công việc là **từ chối cho đúng** | 220/282 câu dev và 248/313 câu test có nhãn "từ chối" (78–79%). Bộ nhóm tự viết chỉ 58/518 (11%) | Mạnh |
| E3 | Lớp luật (A) tăng mạnh trên test đã khoá | Cân bằng 0,647 → 0,814; trả lời đúng trọn 19/59 → 35/59. McNemar hành vi +96/−10 (p ≈ 9·10⁻¹⁹); trả lời đúng trọn +22/−6 (p = 0,004) | Mạnh: test đã khoá, chạy một lần |
| E4 | Lớp luật không làm hỏng bộ cũ | Golden: hành vi 400 → 400, top-1 274 → 275 | Mạnh |
| E5 | Học máy một mình kém luật | Reranker B: cân bằng 0,692, đúng trọn 21/59. Model 4B đọc câu C: 0,785, 25/59. Luật A: 0,814, 35/59 | Vừa: cùng giao thức, nhưng B và C chỉ chỉnh trên dev 282 câu |
| E6 | Ghép học máy vào luật gần như không thêm gì | A → A + B: +1/−0 (p = 1). A → A + C (chỉ tên): đúng trọn +8/−4 (p = 0,39) | Vừa: "không thêm có ý nghĩa", không phải "vô ích" |

Điểm đáng nói: **lớp luật không đổi gì trên bộ nhóm tự viết** (E4) nhưng **gần như nhân đôi số câu trả lời đúng trên câu thật** (E3). Bộ tự viết không bắt được loại khó của câu thật. Đây là bài học về cách đánh giá, đáng đưa vào Discussion.

## 2. Các trục đã cân nhắc và vì sao không chọn

| Trục | Vì sao không làm trục chính |
|---|---|
| Kiến trúc hai engine (Strict + Friendly) | Phần Friendly là bài 2. Ghép cả hai vào một bài thì quá rộng, và trưởng nhóm đã chọn "một điểm mạnh" (21/10) |
| Hội thoại nhiều lượt, cô lập lượt hỏi lại | Không có bộ câu thật nhiều lượt. Lớp hỏi lại trên test chỉ có 6 câu (0/6 đúng) |
| Tốc độ và chạy tại chỗ | Có số (luật: p50 vài chục ms một người), nhưng không phải đóng góp khoa học. Chỉ để ở phần Setup |
| Chống bịa phí, thời hạn | Bản draft cũ ghi "0%" mà không có phép đo trên câu thật. Phải đo lại thì mới nói được |
| Model 4B đọc câu (C) | Một mình kém luật; ghép vào chưa có ý nghĩa thống kê. Dùng làm phân tích phụ và hướng tiếp theo |

## 3. Câu hỏi nghiên cứu đề xuất (2–4 câu, theo khuôn B4)

- **RQ1.** Đánh giá trên bộ câu nhóm tự viết lệch bao nhiêu so với câu hỏi thật của người dân, ở các mặt: hành vi đúng, top-1, tỷ lệ từ chối đúng? (E1, E2)
- **RQ2.** Trên câu hỏi thật đã khoá, một lớp luật minh bạch quyết định trả lời / hỏi lại / từ chối cải thiện được bao nhiêu, và có làm tụt bộ cũ không? (E3, E4)
- **RQ3.** Hai thành phần học máy có sẵn (cross-encoder reranker và model 4B chạy tại chỗ đọc câu), khi dùng một mình và khi ghép với lớp luật, so với lớp luật thế nào? (E5, E6)

## 4. Đóng góp có thể ghi (bản nháp, sẽ viết lại bằng tiếng Anh)

1. Một giao thức đánh giá trên câu hỏi thật của người dân về thủ tục cấp xã:
   - hai tầng mẫu (ngẫu nhiên / theo chủ đề);
   - ba lớp hành vi;
   - dev và test tách nhau, khoá trước khi sửa code;
   - mỗi cấu hình chạy một lần.
2. Số đo khoảng cách giữa bộ tự viết và câu thật trên cùng một hệ thống (RQ1).
3. Một lớp luật đọc thư của người dân, gồm bỏ phần chào hỏi, từ điển từ dân dùng, cổng ý định ngoài phạm vi, và mặc định cá nhân hay tổ chức. Lớp này gần gấp đôi số câu trả lời đúng mà không làm tụt bộ cũ (RQ2).
4. So sánh có kiểm soát với reranker và model 4B, kể cả các cấu hình thua (RQ3).

Câu định vị theo khuôn môn (B9): bài không đề xuất model mới. Bài đánh giá cách ghép model có sẵn với luật trong một hệ thống thật.

## 5. Không được viết (vượt quá bằng chứng)

- "Luật tốt hơn LLM" nói chung. Chỉ được nói: trên bộ này, với model 4B này và cách dùng này.
- "B hay C vô ích". Chỉ được nói: không thêm có ý nghĩa thống kê khi đã có A, trên 313 câu.
- Bất cứ điều gì về câu hỏi lại (6 câu) ngoài việc báo số và nói là quá ít.
- Khái quát sang ngôn ngữ hay lĩnh vực khác. Luật viết riêng cho tiếng Việt và thủ tục cấp xã; chỉ được nêu thành hướng tiếp theo.
- Số System 4.

## 6. Điểm yếu reviewer sẽ hỏi, và cách trả lời

| Điểm yếu | Cách xử lý |
|---|---|
| Nhãn test do một người gán, và người đó là AI, cũng là bên sửa hệ thống | **Đã làm.** Lượt B gán lại 100 câu (Gemini 4 Argon gán trước, trưởng nhóm kiểm từng câu, không xem nhãn A): κ = 0,685 (95% CI 0,55–0,82), khớp 79/91 câu. Chấm lại bằng nhãn B thì kết luận không đổi: bản gốc → A +24/−1 câu, A + B = A (`eval/real_v2/relabel/`). Ghi trong Limitations và mục khai báo AI |
| Chỉ một bộ test | **Đã làm (25/10).** Bộ test thứ hai real_v4: thứ tự khoá `5499d0f`, 400 câu đầu được gán (Gemini 4 Argon đề xuất, trưởng nhóm duyệt), nhãn khoá `a79ec5f`, còn 363 câu (21 answer, 7 clarify, 335 refuse). Chạy một lần ở code `88cabd6`. Lớp luật lặp lại phần tăng từ chối (175 → 297/335); vòng 2 không lặp lại (A2 + B hoà A + B, +3/−3) |
| Nhãn dev (real_v1) do hai lượt AI gán, chưa có người kiểm | Dev chỉ dùng để chỉnh. Ghi trong Limitations |
| Chỉ một bộ test; lớp answer chỉ 59 câu | Báo Wilson CI; báo thêm bộ sạch 302 câu và từng tầng (kết luận không đổi) |
| Chưa so với hệ thống bên ngoài | Xem `05_methodology/baseline.md`: bài trước làm nhiệm vụ khác (chỉ câu trả lời được). Đã thêm baseline "RAG + model 4B tự quyết" (trưởng nhóm duyệt 25/10): cân bằng 0,489 trên test 1 và 0,413 trên test 2, không hơn luôn từ chối |
| Dev và test cùng một nguồn | Cùng phân phối là có chủ đích (test = phân phối thật). Ghi là giới hạn về khái quát |
| Luật có phải "khớp với test" không? | Luật viết trước khi mở test, chỉ từ dev và từ dữ liệu thủ tục. Có commit và sha256 chứng minh thứ tự |

## 7. Tên bài (gợi ý ngày 25/10)

**Tên đã chọn (27/10):** *Answer, Clarify or Refuse? Rules, a Reranker and a Small LLM on Real Citizen Questions about Commune-Level Administrative Procedures in Vietnam*.

Các gợi ý ban đầu:

1. *When Rules Should Decide: Answering, Clarifying and Refusing Real Citizen Questions on Vietnamese Administrative Procedures*
2. *Closing the Gap Between Team-Written and Real Citizen Questions in a Vietnamese Administrative-Procedure Assistant*
3. *Rules, Rerankers or a Small Local LLM? A Held-Out Evaluation on Real Citizen Questions about Vietnamese Administrative Procedures*

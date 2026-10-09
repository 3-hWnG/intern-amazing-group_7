# System 4 — NV5: Tốc độ, đổi model, độ chính xác, chào hỏi khi bật dữ liệu

Phần A = lời người dùng (nguyên văn, chỉ thêm tiêu đề). Phần B = ý của Claude. Phần C = kế hoạch đã duyệt. Phần D = kết quả đo.

## Phần A — Yêu cầu gốc (nguyên văn)

### A1. Phản hồi cuối phiên trước (2026-10-07)
> It worked thanks though I want to change a lot, it's time is bad, it's accuracy is bad, it can't say hello/goodbye when has a dataset on. Please note it all down so you can quickly catch up. We will meet in another session since we ran out of context windows. Mark my priority now is Improve time, change model if necessary, improve accuracy radically (clarify with trade-offs like I specified above if the new you forget the rule to work with me)

### A2. Mở việc (2026-10-08)
> Okay, now let's get back on the job. List me a list of solution and trade-offs, let's go through this 1 by 1

### A3. Trả lời danh sách giải pháp (2026-10-08)
> On speed, Keep the planning and organization, accuracy is another point I want to optimize so don't compromise it for speed, the rest sound Okay. On model, I'm leaning strongly toward Qwen Instruct and ready to download now, make a script and I'll download it. On accuracy, sound good to me. On Greetings, G1,2,3 are all bad, but G2 seems the least bad here, actually check if the messge is short (less than 5 words for example) then check if it include greetings word list (so it can handle cases like Hi, I want to help with X, what is Y in X -> procedure, not greetings, also benchmark if G2 actually need these handicap before giving it). the options you listed didn't my above description. So I want the pareto optimal point of (1. accuracy, 2. speed, 3. not having wrong behavior) and a convoluted plan is better than optimizing 1 by 1 I think. Use more thinking.

### A4. Trả lời kế hoạch + trade-off (2026-10-08)
> First, Evething download in Set up first time.bat please (I am running the qwen download BTW, not done yet) (So my teammate can quickly catch up). Second the plan "No speed change is kept if it costs accuracy" is too absolutist, if small drop in accuracy can help reduce speed/wrong behavior dramatically then we can consider it (We are making usable product, the metrics optimization should help it, not take reigns). The test and settings UI doesn't seems to need AI so proceed. But I want to check greetings both way (code first, AI intervene VS AI first, code intervene AND AI only) see what better. Stop after you have built these, the download seems to take a lot of time. I will type "continue" when the download is done. 1D 2A 3A 4 answered_above 5B. Some small change and Approve the rest

> This is a queued message, seems like the download completed so if everything as planned "continue" else reject and stop.

### A5. Trade-off đã chọn
| Câu | Lựa chọn | Nghĩa |
|---|---|---|
| 1. Model nào làm gì | **D** | Đo cả hai: (A) Instruct cho trả lời nhanh, "Suy nghĩ kỹ" giữ qwen3:4b, Strict giữ nguyên; (B) Instruct cho mọi thứ kể cả Strict |
| 2. Chi tiết không có trong dữ liệu | **A** | AI viết lại một lần, được báo rõ chi tiết nào không có; chat thường: kiểm số điện thoại / email / web của doanh nghiệp |
| 3. Số lần chạy mỗi câu | **A** | 1 lần ở các vòng so sánh, 3 lần ở bài thi cuối |
| 4. Câu chào | (trả lời ở A4) | So 3 cách: code trước + AI can thiệp / AI trước + code can thiệp / chỉ AI |
| 5. Danh sách lớp thật trên GitHub công khai | **B** | Dùng bản sao tên giả, cùng bố cục khó (`system4/eval/fake_class.py`) |

## Phần B — Ý của Claude

- **Thời gian đi đâu** (6 câu thật gần nhất trước NV5, có bật dữ liệu): tìm 1,0–2,5 s; AI 3,6–12,8 s kể cả câu trả lời 70 ký tự → phần lớn là AI *đọc* lời dặn dài (quy tắc + 4 đoạn dữ liệu + tối đa 20 tin cũ), không phải viết. "Chào bạn" mất 6,5 s.
- **Model:** `qwen3:4b` trên máy là bản luôn suy nghĩ; chế độ Nhanh phải ép JSON để tắt suy nghĩ. `qwen3:4b-instruct-2507-q4_K_M` (2,5 GB) là bản không suy nghĩ của cùng model (đã kiểm tên trên Ollama).
- **Bằng chứng bịa ở chế độ Nhanh hiện tại** (lần chạy thử bộ đo, cấu hình hôm nay): "Thủ đô của Úc là Sydney", "Truyện Kiều của Huy Cận", hotline "0909 888 888", email "team7.support@example.com", địa chỉ "Số 123 Đường ABC", giá "15.990.000".
- **Quy tắc chọn cấu hình** (sửa theo A4, không còn tuyệt đối):
  1. Tính "biên Pareto" theo 3 trục: đúng % (accuracy + không bịa), thời gian cả câu (trung vị), số lỗi hành vi (chào hỏi + 22 tình huống).
  2. Mặc định chọn cấu hình đúng nhất trên biên.
  3. Nếu một cấu hình khác trên biên chỉ kém đúng **≤ 2 điểm %** (khoảng 1 câu trên 50) mà **nhanh hơn ≥ 20 %** hoặc **ít lỗi hành vi hơn ≥ 30 %** → đưa người dùng chọn (bảng so sánh), không tự quyết.
- **Bộ đo do Claude soạn**, chưa phải câu hỏi thật; 1/3 là "bài thi cuối" (split exam) không xem khi chỉnh để số cuối trung thực.
- Mọi tính năng mới là **công tắc trong ⚙** (nhóm "Tốc độ & độ chính xác"), mặc định = như trước NV5; chỉ đổi mặc định sau khi đo.

## Phần C — Kế hoạch đã duyệt (2026-10-08)

| Bước | Việc | Trạng thái |
|---|---|---|
| 0 | `Download Qwen Instruct.bat`; `Set up first time.bat` tải đủ mọi model (bước 6/9) | Xong |
| 1 | Bộ đo `system4/eval/bench.py`: server riêng (cổng 8399, dữ liệu riêng), 77 câu (45 dev / 32 exam) + 22 tình huống hành vi; chấm luật; bảng Pareto; đo đổi model; chạy bộ đo System 3 với model khác | Xong |
| 2 | Công tắc: `THINK_MODEL`, `KEEP_MODELS_LOADED`, `PROMPT_CACHE_ORDER`, `FAST_FORMAT` (json/text), `PLAN_MAX_CHARS`, `GREETING_MODE` (off/code_first/ai_first/ai_only), `GREETING_MAX_WORDS`, `GREETING_WORDS`, `GROUNDING_CHECK`, `AMBIGUITY_CHECK`, `AMBIGUITY_MAX`, `TABLE_TOOL`; tìm kiếm song song + số đo từng bước; bộ đọc tệp v3 (tiêu đề hai tầng, bảng ngang, nhiều bảng một trang, chọn dòng tiêu đề trong "Cách đọc") | Xong, test `test_nv5.py` |
| 3A | So: hôm nay / Instruct 0,7 / Instruct 0,2 + đo đổi model | Xong (D1) |
| 3B | Trên cấu hình thắng: JSON vs chữ × kế hoạch 300 vs 600 (bật thứ tự lời dặn) | Xong (D2) |
| 3C | Trên cấu hình thắng: tính năng chính xác, câu chào 3 cách, S2 (ít tin cũ / đoạn ngắn), S4 (reranker 8 ứng viên) | Xong (D3, D4); S2/S4 bỏ (D2) |
| 3D | Strict: bộ đo System 3 với qwen3:4b vs Instruct (câu 1D) | Xong (D6), chờ quyết định |
| 3E | Bài thi cuối: thắng vs hôm nay, 3 lần mỗi câu | Xong (D5) |
| 4 | Đặt mặc định, cập nhật tài liệu, báo cáo | Xong (D7) |

### Câu chào — 3 cách (GREETING_MODE)
| Cách | Code làm gì | AI làm gì |
|---|---|---|
| `code_first` | Tin ≤ 4 chữ + có từ chào + AI không vừa hỏi lại → bỏ qua tìm kiếm, trả lời kiểu xã giao | Các tin còn lại: AI được đánh dấu "xã giao" (bỏ chốt "chỉ trả lời từ dữ liệu", không hiện nguồn) |
| `ai_first` | Kiểm lại AI: AI nói xã giao mà tin có dấu hỏi / từ hỏi / dài → bác bỏ; tin là câu chào ngắn mà AI trả lời "không có trong dữ liệu" → viết lại kiểu xã giao | Luôn tìm dữ liệu; AI tự đánh dấu xã giao |
| `ai_only` | Không can thiệp | Luôn tìm dữ liệu; AI tự đánh dấu xã giao |

## Phần D — Kết quả đo

### D1. Vòng A — model × temperature (split dev, 1 lần mỗi câu, chưa bật tính năng mới nào)
| Cấu hình | Đúng % | Không bịa % | Chào % (chưa bật) | Hành vi | Sai hành vi | Chữ đầu | Cả câu (trung vị) | Cả câu p90 |
|---|---|---|---|---|---|---|---|---|
| Hôm nay (qwen3:4b, JSON) | 66,7 | 33 | 25 | 21/22 | 10 | 1,5 s | 3,2 s | 4,8 s |
| Instruct, 0,7 | 66,7 | 44 | 33 | 22/22 | 8 | 1,1 s | 2,9 s | 4,6 s |
| **Instruct, 0,2** | 66,7 | 33 | 50 | 21/22 | 7 | **1,0 s** | **2,6 s** | 5,0 s |

- Chọn **Instruct 0,2** làm nền cho vòng B (nhanh nhất, đúng ngang nhau, nằm trên biên Pareto). Khác biệt 1 câu là trong mức ngẫu nhiên (mỗi câu chạy 1 lần).
- **Đổi model Strict ↔ Friendly** (`bench.py swap`): mỗi lần đổi Ollama nạp lại **4,4–5,5 s**; card 6 GB chỉ giữ được một model cùng bge-m3.
- Lỗi chung của cả 3 cấu hình (tính năng sửa đã có công tắc, đo ở vòng C): trùng tên "bé An" trả lời gộp thay vì hỏi lại; đếm / liệt kê cả bảng ("16 bạn nữ") không làm được; bịa số điện thoại / email / địa chỉ / năm thành lập Team 7; câu chào bị thay bằng "không có trong dữ liệu".
- **Lỗi tìm kiếm phát hiện khi đo** (thêm công tắc mới, đo ở vòng C):
  - "Hạng Vàng?": tìm từ khoá và tìm theo nghĩa đều xếp bản ghi "Vàng" hạng 1, nhưng reranker chấm −5,7 (< ngưỡng −3) nên AI không thấy → `RERANK_RESCUE`.
  - "Còn số điện thoại thì sao?": 6 chữ nên không được ghép câu hỏi trước (luật cũ: dưới 6 chữ) → tìm sai người → `SEARCH_FOLLOWUP`.
  - Bịa địa chỉ / năm thành lập ở chat thường (bộ kiểm chi tiết chỉ bắt số điện thoại / email / web) → `STRICT_BUSINESS_FACTS` (một dòng lời dặn).
- Bản Instruct đôi khi viết lẫn "ask_back = true / choices = [...]" vào câu trả lời (lỗi khuôn JSON) → so với dạng chữ ở vòng B.
- Sửa bộ chấm sau vòng A (lỗi của bộ đo, không phải của web): "ruộng lúa bậc thang" chưa được tính là đúng; mẫu số điện thoại chưa nhận "1900 8939" (8 số).

### D2. Vòng B — cách viết và độ dài kế hoạch (nền Instruct 0,2; split dev, 1 lần)
| Cấu hình | Đúng % | Không bịa % | Chào % | Hành vi | Sai hành vi | Chữ đầu | Cả câu | p90 |
|---|---|---|---|---|---|---|---|---|
| Instruct 0,2 (chạy lại) | 69,7 | 33 | 33 | 21/22 | 9 | 1,05 s | 2,5 s | 5,0 s |
| **B1** = + sắp lời dặn + giữ model nạp sẵn | 72,7 | 56 | 50 | 21/22 | 7 | 1,04 s | 2,7 s | 6,6 s |
| B2 = B1 + dạng chữ | 75,8 | 56 | 25 | 20/22 | 11 | 1,73 s | 3,0 s | 5,2 s |
| B3 = B1 + kế hoạch 600 | 69,7 | 44 | 25 | 21/22 | 10 | 1,51 s | 3,7 s | 6,7 s |
| B4 = B2 + kế hoạch 600 | 69,7 | 33 | 42 | 20/22 | 9 | 1,71 s | 3,1 s | 5,8 s |

- **Độ nhiễu:** cùng cấu hình Instruct 0,2 chạy 2 lần: 66,7 % rồi 69,7 %. Chênh 1–3 câu (3–9 điểm %) giữa các cấu hình là ngẫu nhiên → chỉ tin khác biệt lớn, và bài thi cuối chạy 3 lần.
- **Chọn B1** (JSON, kế hoạch 300). Dạng chữ (B2) đúng hơn 1 câu (trong mức nhiễu) nhưng sai hành vi nhiều hơn (bỏ lỡ "Trả lời nhanh", hỏi lại điều đã nhớ) và chữ đầu chậm hơn 0,7 s (kế hoạch viết hết rồi mới hiện chữ). Kế hoạch 600 chậm hơn, không đúng hơn.
- **Thời gian thật sự đi đâu** (số đo Ollama trong mỗi câu): đọc lời dặn chỉ **0,03–0,7 s**; **viết** chiếm phần lớn (~55 token/giây; câu trả lời dài 300+ token về thủ tục mất 5–6 s); tìm ~0,45 s (tạo vector câu hỏi 0,2–0,35 s, reranker 0,15 s, từ khoá 4 ms). → Các câu 7–12 s người dùng thấy trước NV5 chủ yếu do **nạp lại model** (câu đầu sau khi bật, đổi qua lại với System 3), không phải do đọc. Sắp lời dặn (S1) gần như không đổi tốc độ; giữ model nạp sẵn (S5) là phần có ích.
- **Bỏ S2 / S4** (ít tin cũ / đoạn ngắn / reranker 8 ứng viên): đọc chỉ ~0,25 s và reranker ~0,15 s, nên tiết kiệm tối đa ~0,1 s — không "đáng kể" theo quy tắc A4, không đáng rủi ro độ chính xác.
### D3. Vòng C — tính năng chính xác + câu chào 3 cách (nền B1; split dev, 1 lần)
"Gói chính xác" = `SEARCH_FOLLOWUP`, `RERANK_RESCUE`, `STRICT_BUSINESS_FACTS`, `AMBIGUITY_CHECK`, `TABLE_TOOL`, `GROUNDING_CHECK=rewrite`.

| Cấu hình | Đúng % | Không bịa % | Chào % | Sai hành vi (*) | Chữ đầu | Cả câu |
|---|---|---|---|---|---|---|
| B1 (chưa có gói) | 72,7 | 56 | 50 | 7 | 1,0 s | 2,7 s |
| C1 = B1 + gói chính xác | 93,9 | 89 | 50 | 8 | 1,0 s | 2,8 s |
| C2 = sau khi sửa các lỗi dưới đây, chào tắt — **⚠ chạy nhầm model cũ qwen3:4b, 0,6** | 84,8 | 67 | 42 | 8 | 1,8 s | 3,6 s |
| C2 + code_first ⚠ qwen3:4b | **93,9** | **89** | **100** | **0** | 1,7 s | 2,9 s |
| C2 + ai_first ⚠ qwen3:4b | 87,9 | 67 | 100 | 0 | 1,6 s | 2,9 s |
| C2 + ai_only ⚠ qwen3:4b | **93,9** | **89** | **100** | **0** | 1,7 s | 2,9 s |

**⚠ Lỗi của Claude khi đo:** bộ đo chọn cài đặt theo tên cấu hình; tên "C2…" / "D…" không bắt đầu bằng "inst02" nên 6 lần chạy này dùng model MẶC ĐỊNH (qwen3:4b, 0,6), không phải Instruct. Kết quả đổi tên thành `qwen3_*.json`; bộ đo nay dừng hẳn nếu tên lạ. Những lần chạy này vẫn có ích: **model cũ + gói chính xác + chào code_first** cũng đạt 93,9 % đúng, 100 % chào, 22/22 hành vi. Kết luận chọn cấu hình được đo lại trên Instruct ở D4.

(*) 3 dòng cuối chỉ tính câu chào (22 tình huống hành vi không phụ thuộc cách chào). Chênh "đúng %" giữa 3 cách chào đến từ câu kiến thức chung (Úc → "Sydney", Truyện Kiều → "Nguyễn Đình Chiểu") — model 4B lúc đúng lúc sai, không do cách chào.

**Gói chính xác sửa được (đúng ở mọi lần chạy sau khi bật):** hỏi lại "bé An nào?" có nút họ tên; "16 bạn nữ", "5 bạn sinh năm 2019", liệt kê đủ 10 bạn Ấp Phú Thạnh; không còn bịa số điện thoại / email / năm thành lập Team 7; "Còn số điện thoại thì sao?" đúng số.

**Lỗi tìm thấy trong vòng C và đã sửa** (vì vậy có C2):
1. Kiểm chi tiết bịa: 6/6 lần viết lại ở C1 là **báo nhầm** (ghép tên qua xuống dòng: "Võ Thị Kim Loan" + "Nguồn"; qua dấu chấm: "Thứ Bảy. Chủ nhật" → "Bảy Chủ"; "8:00" ≠ "8 giờ"; chữ IN HOA). Mỗi lần viết lại tốn thêm 2–3 s. Đã sửa; còn 1–2 lần/45 câu. Chỗ bịa thật về Team 7 là do lời dặn `STRICT_BUSINESS_FACTS` chặn, không phải bộ kiểm.
2. `SEARCH_FOLLOWUP` không chạy: lỗi của Claude khi chèn code (dấu `\b` trong biểu thức bị đổi thành ký tự điều khiển). Đã sửa + thêm test.
3. `STRICT_BUSINESS_FACTS` làm AI từ chối cả số điện thoại CÓ trong dữ liệu ("liên hệ nhân viên Team 7") → nay chỉ áp dụng khi không bật dữ liệu.
4. "Hạng Vàng?" lúc đúng lúc sai dù bản ghi đã được gửi: bản ghi chỉ ghi "Vàng / Ưu đãi: …", thiếu tên cột → bộ đọc v4 ghi "Hạng thành viên: Vàng" ở dòng đầu mỗi bản ghi bảng.
5. **Bộ nhớ ghi rác:** "Bạn còn nhớ mình tên gì không?" làm AI ghi điều nhớ "Người dùng hỏi tên mình", các câu sau trả lời "bạn tên là người dùng hỏi tên mình". Đã lọc bằng code (bỏ điều nhớ dạng "Người dùng hỏi / muốn biết / chào / cảm ơn …"); bộ đo xoá bộ nhớ tài khoản đo trước mỗi câu.
6. **Kế hoạch ẩn không có tác dụng phần lớn thời gian đo:** Ollama 0.40 không giữ thứ tự trường của khuôn JSON — từ vòng A đến C1 model viết `{"answer": …, "plan": …}` (kế hoạch viết SAU câu trả lời); ở C2 lại viết kế hoạch trước — vì C2 chạy nhầm qwen3:4b (model cũ hay viết plan trước; Instruct gần như luôn viết answer trước, kiểm trực tiếp 6/6). Thử thêm lời dặn "viết plan trước": vẫn 6/6 lần answer trước. Cách chắc chắn: đặt tên trường `a_plan`, `b_small_talk`, `c_answer`… (thứ tự chữ cái = thứ tự mong muốn) → 6/6 lần kế hoạch đứng đầu. Công tắc `JSON_PLAN_FIRST`. Hệ quả: "chữ đầu 1,0 s" của Instruct ở vòng A–C1 là nhờ KHÔNG lập kế hoạch (kế hoạch viết sau câu trả lời). Chi phí thật của việc lập kế hoạch trước: đo ở D4.

### D4. Vòng D — Instruct + kế hoạch thật sự viết trước (JSON_PLAN_FIRST) + câu chào 3 cách (split dev, 1 lần)
| Cấu hình (Instruct 0,2 + gói chính xác) | Đúng % | Không bịa % | Chào % | Hành vi | Chữ đầu | Cả câu | p90 | Viết lại nhầm |
|---|---|---|---|---|---|---|---|---|
| C1 + code_first (kế hoạch viết SAU câu trả lời) | 93,9 | 89 | 92 | — | 1,0 s | 3,5 s | 7,4 s | 5 |
| **D + code_first** (kế hoạch viết TRƯỚC) | **97,0** | 89 | **100** | 21/22 | 1,25 s | **2,5 s** | **5,3 s** | **0** |
| D + ai_only | 97,0 | 89 | 92 | — | 1,27 s | 2,3 s | 6,0 s | 0 |
| D + ai_first | 97,0 | 89 | 92 | — | 1,54 s | 2,6 s | 5,6 s | 1 |

- **Lập kế hoạch thật trước khi trả lời có lợi ở cả 3 trục:** đúng hơn (+1 câu), cả câu nhanh hơn (câu trả lời gọn hơn), chữ đầu chỉ chậm thêm ~0,25 s.
- **Câu chào: chọn code_first.** Cả 3 cách đúng như nhau ở câu hỏi dữ liệu; chỉ code_first xử lý đúng "Ok cảm ơn bạn" ngay sau một câu trả lời có dữ liệu (2 cách kia lặp lại câu trả lời cũ kèm nguồn), và câu chào ngắn không phải chờ tìm kiếm.
- Còn sai: "nhà thơ Trần Văn Khuyết" (người bịa) — model kể tiểu sử giả; bộ kiểm chi tiết không bắt được vì ở chat thường chỉ kiểm số điện thoại / email / web. 21/22 hành vi: câu "Team 7 là ai?" trả lời "đội ngũ hỗ trợ khách hàng của tôi" (không xưng "chúng tôi/mình") — lỗi câu chữ, lúc có lúc không ở mọi cấu hình.

### D5. Bài thi cuối (split exam, 32 câu chưa từng dùng khi chỉnh, mỗi câu 3 lần = 96 lượt + 22 tình huống hành vi)
| | Hôm nay (qwen3:4b, như trước NV5) | **NV5 (cấu hình mới)** |
|---|---|---|
| Đúng (độ chính xác + không bịa) | 73,1 % | **92,3 %** |
| Không bịa (riêng nhóm bịa) | 55,6 % | **83,3 %** |
| Câu chào khi bật dữ liệu | 50 % | **100 %** |
| Hành vi (22 tình huống) | 22/22 | 21/22 |
| Lỗi hành vi tổng (chào + 22 tình huống) | 9 | **1** |
| Chữ đầu / cả câu (trung vị, mọi câu) | 1,1 s / 2,7 s | 1,6 s / 2,9 s |
| Cả câu p90 | 4,3 s | 4,9 s |
| — câu có dữ liệu thường | 3,1 s | 3,6 s |
| — câu đếm / liệt kê cả bảng (công cụ bảng) | 0 % đúng | 100 % đúng, 4,9 s |
| — chat thường (không bật dữ liệu) | 2,2 s | **1,4 s** |
| — câu chào | 2,0 s | **1,3 s** |
| "Suy nghĩ kỹ" (2 tình huống) | 47 s | 26 s |

- Câu cải thiện rõ nhất (đúng ở 3/3 lần, trước 0–1/3): đếm bạn nam (17), liệt kê bạn sinh 2019, đếm Ấp Tân Hòa (14), web / giá / giám đốc Team 7 không còn bịa, mọi câu chào.
- Còn sai trong bài thi: "Bé Bảo sinh ngày nào?" (0/3, không hỏi lại "Bảo nào?") — **lỗi code đã sửa sau bài thi** (từ "bao" của "bao nhiêu" bị coi là từ chung nên tên "Bảo" bị bỏ; nay gộp "bao nhiêu" thành một từ, thêm test); số này trong bảng là TRƯỚC khi sửa. "Nước nào diện tích lớn nhất?" → "Việt Nam" (0/3, kiến thức sai của model Instruct; model cũ trả lời đúng "Nga").
- Đánh đổi (theo quy tắc A4): đúng +19 điểm %, lỗi hành vi 9 → 1, đổi lại câu có dữ liệu chậm thêm ~0,5 s (lập kế hoạch trước + lời dặn dài hơn), câu đếm cả bảng thêm ~1,9 s; vẫn dưới ngân sách 5 s (p90 4,9 s).

### D6. Strict với model Instruct (câu 1D, bộ đo System 3, 449 câu DEV, `bench.py strict`)
| | qwen3:4b (hiện tại) | Instruct |
|---|---|---|
| top-1 / top-3 | 97,4 % / 99,0 % | 97,4 % / 99,0 % |
| Đúng hành vi | 97,8 % | 97,8 % |
| Bịa số | 0,5 % | 0,5 % |
| Thời gian trung vị / p90 | 29 ms / 2,5 s | 31 ms / 3,8 s |

- Đúng y hệt (Strict chủ yếu trả lời bằng luật, AI chỉ viết lại một phần). p90 chậm hơn 1,3 s với Instruct (một lần đo, chưa rõ là nhiễu hay thật).
- Lợi nếu đổi Strict sang Instruct: hết **4,4–5,5 s nạp lại model** mỗi lần chuyển Strict ↔ Friendly.
- **Đo lại (câu 1A, 2026-10-08):** cả hai model chạy lần 2 — đúng y hệt; p90 qwen3:4b 2,4 s, Instruct **2,2 s** → 3,8 s lần đầu là nhiễu.
- **Quyết định (nguyên văn): "1A then push it to https://github.com/3-hWnG/intern-amazing-group_7/tree/System_4 and commit on machine"** → `Launch web.bat` đặt `LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M` cho Strict (không đổi code System 3). Chỉ còn nạp lại model khi bấm "Suy nghĩ kỹ" (vẫn qwen3:4b, vốn ~26 s).

### D7. Mặc định mới (config.py, nút ⚙ vẫn đổi được)
`FRIENDLY_MODEL = qwen3:4b-instruct-2507-q4_K_M`, `FRIENDLY_TEMPERATURE = 0.2`, `THINK_MODEL = qwen3:4b`, `KEEP_MODELS_LOADED`, `PROMPT_CACHE_ORDER`, `JSON_PLAN_FIRST`, `GREETING_MODE = code_first`, `GROUNDING_CHECK = rewrite`, `AMBIGUITY_CHECK`, `TABLE_TOOL`, `SEARCH_FOLLOWUP`, `RERANK_RESCUE`, `STRICT_BUSINESS_FACTS` = bật. `FAST_FORMAT = json`, `PLAN_MAX_CHARS = 300` giữ nguyên. Test NV1–NV3 chạy với các cài đặt NV5 tắt (`system4/tests/nv5_off.py`); `test_nv5.py` kiểm từng tính năng và cả cấu hình mặc định mới.

### D8. Việc ngoài kế hoạch đã làm / lỗi cũ tìm thấy
- `system4/scraper/normalize.py` (NV4, phiên trước): biểu thức tìm năm trong số hiệu văn bản chứa ký tự điều khiển thay cho `\b` (cùng loại lỗi chèn code như `SEARCH_FOLLOWUP`) nên nhánh dự phòng không bao giờ khớp → đã sửa, test_nv4 xanh.
- Bộ nhớ ghi câu hỏi thành "điều nhớ" (D3 mục 5) → đã lọc.

### D9. Còn lại / hướng sau
| Việc | Lợi ước tính | Ghi chú |
|---|---|---|
| Đổi Strict sang Instruct | bỏ 4,4–5,5 s mỗi lần chuyển chế độ | **Đã làm** (D6) |
| Giảm ngữ cảnh model Friendly (8192 → 4096/6144) để card 6 GB không đầy | ~0,25 s mỗi câu có dữ liệu (tạo vector câu hỏi 0,2–0,35 s → ~0,03 s) | chưa đo; hội thoại rất dài dựa vào tóm tắt sớm hơn |
| Kiến thức chung sai của model 4B (Úc → Sydney, diện tích lớn nhất → Việt Nam, nhà thơ bịa) | — | code không kiểm được; cần model lớn hơn hoặc nguồn tra cứu |
| Câu trả lời dài về thủ tục (300+ token, 5–6 s) | tốc độ | có thể thêm lời dặn "trả lời gọn" — chưa đo ảnh hưởng độ chính xác |

- Ghi chú để sau: tạo vector câu hỏi trong server mất 0,2–0,35 s, chạy riêng chỉ 0,03 s — có thể do card 6 GB đầy (model trả lời + bge-m3 + reranker), một phần bị đẩy sang CPU. Hướng sửa: giảm ngữ cảnh model Friendly (giờ khác model với System 3 nên không còn cần 8192). Lợi ~0,25 s mỗi câu Chuyên gia.

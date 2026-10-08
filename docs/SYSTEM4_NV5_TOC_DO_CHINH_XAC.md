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
| 3A | So: hôm nay / Instruct 0,7 / Instruct 0,2 + đo đổi model | Đang chạy |
| 3B | Trên cấu hình thắng: JSON vs chữ × kế hoạch 300 vs 600 (bật thứ tự lời dặn) | |
| 3C | Trên cấu hình thắng: tính năng chính xác, câu chào 3 cách, S2 (ít tin cũ / đoạn ngắn), S4 (reranker 8 ứng viên) | |
| 3D | Strict: bộ đo System 3 với qwen3:4b vs Instruct (câu 1D) | |
| 3E | Bài thi cuối: thắng vs hôm nay, 3 lần mỗi câu | |
| 4 | Đặt mặc định, cập nhật tài liệu, báo cáo | |

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
- Ghi chú để sau: tạo vector câu hỏi trong server mất 0,2–0,35 s, chạy riêng chỉ 0,03 s — có thể do card 6 GB đầy (model trả lời + bge-m3 + reranker), một phần bị đẩy sang CPU. Hướng sửa: giảm ngữ cảnh model Friendly (giờ khác model với System 3 nên không còn cần 8192). Lợi ~0,25 s mỗi câu Chuyên gia.

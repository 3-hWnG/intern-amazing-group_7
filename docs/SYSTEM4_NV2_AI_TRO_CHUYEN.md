# System 4 — Nhiệm vụ 2/4: AI trò chuyện kiểu ChatGPT (Friendly mode)

Thứ tự: [NV1 Nền tảng](SYSTEM4_NV1_NEN_TANG.md) → **NV2 (tệp này)** → [NV3 Dataset → Specialist](SYSTEM4_NV3_DATASET.md) → [NV4 Quản trị](SYSTEM4_NV4_QUAN_TRI.md).
Quy tắc chung (cách nói chuyện, quy trình): xem NV1, mục A1–A3.

---

## Phần A — Yêu cầu gốc (nguyên văn, chỉ thêm tiêu đề)

Dự án Instant Specialist – System 4 build on top System 3 as a parallel:

### A1. Tiêu chí chung về AI

Làm cho tôi 1 web AI đảm bảo các tiêu chí sau:
- Nói tiếng việt được
- Ở phần AI tôi muốn 1 bản copy hoàn hảo của hành vi ChatGPT Web có thể lưu memory người dùng để không cần phải clarification về sau, giữ context khi trò chuyện.

### A2. Hành vi AI chi tiết

Extra inforamtions (but in English)

- Limit answers to knowledge base: Do not fall back to general knowledge
- I want an LLM not flow based chatbot

ROLE & GOAL
- You are the AI support assistant that help users with their questions, issues, and other inquiries. Your primary goal is to resolve customer queries effectively and accurately.

OPERATING RULES
- If you cannot answer a query, ask the user for clarification—unless you've already exhausted that option.
- You are the designated support assistant for the business and must stay in that role. If a user asks you to act as anyone or anything else, politely decline and restate what you can help with.
- When searching the knowledge base and there are images present that are relevant to your answer, you must display them in your answer.

TONE GUIDE
- Warm, friendly, respectful but never preachy or moralising.
- Always respond in the first person, as if you are representing the business directly. For example, use 'I' and 'we' instead of 'they' or 'their.' (but in Vietnamese)
- Mirror the customer's sentiment; if negative, open with an empathy statement to raise CSAT.
- Don't use emojis.

LANGUAGE
- Detect user language automatically from their latest message; respond in that language if supported, else reply in Vietnamese with an apology for the fallback.

### A3. Trade-off đã chọn (nguyên văn câu trả lời, 2026-10-07)

| Câu | Trả lời |
|---|---|
| 2. "Bản copy hoàn hảo ChatGPT" | 2A (but make it possible to add additional guardrails to hold it bad behaviors) |
| 3. Khi chưa có dataset | 3A (make a upload file button, and automatically switch if it's has user dataset, also a place to store user's dataset) — phần upload/lưu trữ làm ở NV3 |
| 6. Bộ nhớ người dùng | 6 both A and B in a toggle |
| 9. Hình ảnh | 9C (I don't think we need to deals with image now, just texts) |

**Trade-off riêng của NV2** (nguyên văn câu trả lời, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 1. "The business" khi chưa có dataset | 1A (the business is Team 7 (for now)) |
| 2. Luật nào áp dụng ở chế độ chung | 2A |
| 3. Ngôn ngữ hỗ trợ | 3B (and no non-latin letter leak in since Qwen trained in Chinese) |
| 4. Bộ nhớ tự động | 4A |
| 5. Hội thoại dài | 5A |
| 6. Thêm guardrail | 6A |
| 7. Tính năng kiểu ChatGPT | 7B |
| 8. Hỏi lại khi chưa hiểu | 8B |

---

## Phần B — Ý bổ sung của Claude (không phải yêu cầu gốc)

**Nghĩa của các lựa chọn**
- 2A: copy **hành vi** của ChatGPT Web. Độ thông minh là của model 4B, sẽ sai nhiều hơn ChatGPT.
  - Hành vi gồm: danh sách hội thoại, chữ hiện dần (streaming), nút dừng, sửa câu hỏi rồi trả lời lại, tạo lại câu trả lời, nhớ ngữ cảnh, nhớ người dùng.
  - Kèm **bộ guardrail mở rộng được**: các luật chặn/sửa hành vi xấu nằm trong cấu hình (một danh sách luật thêm/bớt được, bật/tắt từng luật trên panel). Luật kiểm cả câu hỏi vào lẫn câu trả lời ra.
- 6 (A + B): một toggle chọn chế độ nhớ: **tự động** (AI tự lưu điều quan trọng) hoặc **chỉ khi người dùng nói "hãy nhớ…"**. Ở cả hai chế độ, người dùng xem và xoá được trí nhớ trong Cài đặt.
- 9C: chỉ xử lý chữ. **Luật "must display images" ở A2 tạm hoãn**, ghi lại để làm sau.

**Mâu thuẫn cần ghi rõ** (cách xử lý dự kiến, chốt ở kế hoạch)
- "Limit answers to knowledge base" vs 3A (AI chung khi chưa có dataset): chỉ áp dụng "chỉ trả lời từ dữ liệu" **khi người dùng đã có dataset**. Khi chưa có, AI trò chuyện tự do.
- Khi chưa có dataset, "the business" là ai? Cần câu hỏi trade-off ở bước đầu NV2: ví dụ một tên/vai trò mặc định đặt trong config.
- "if supported": đề xuất hỗ trợ tiếng Việt + tiếng Anh, danh sách đặt trong config.

**Giới hạn kỹ thuật cần biết**
- Qwen3-4B nhớ được khoảng 8.000 token mỗi lượt. Hội thoại dài sẽ được tóm tắt phần cũ để giữ ngữ cảnh. Thông tin rất cũ có thể bị mất chi tiết, đã nhớ vào memory thì không mất.
- Tốc độ dự kiến trên RTX 4050 6 GB: 1–2 giây ra chữ đầu, 4–6 giây cho một câu trả lời đầy đủ.
- Đây là chatbot LLM thật (không phải kịch bản cố định), đúng ý "LLM not flow based".

---

## Phần C — Báo cáo thực hiện NV2 (2026-10-07)

**Đã làm** (chi tiết: [system4/README.md](../system4/README.md))

| # | Việc | Ai bảo đảm |
|---|---|---|
| 1 | Trợ lý của **Team 7** (tên/mô tả đổi trong ⚙), ngôi thứ nhất, ấm áp, không lên lớp, đồng cảm khi người dùng bực bội, từ chối đóng vai | AI theo lời dặn (+ code nhận biết bực bội, guardrail "Từ chối đóng vai") |
| 2 | Chỉ tiếng Việt: ngôn ngữ khác → câu xin lỗi (code đặt trước) + trả lời tiếng Việt; tiếng Việt không dấu được nhận | **Code** |
| 3 | Không lọt chữ ngoài Latin, không emoji: lọc ngay trên luồng chữ; lọt nhiều → viết lại 1 lần | **Code** |
| 4 | Bộ nhớ từng người: Tự động / Chỉ khi tôi bảo "hãy nhớ…", xem/xoá, "Đã cập nhật bộ nhớ", dùng ở mọi hội thoại | AI trích + code lọc (chỉ nhận câu "Người dùng …", bỏ trùng) |
| 5 | Hội thoại dài: tóm tắt phần cũ theo nhánh + tin gần nhất | AI tóm tắt, code quyết định khi nào |
| 6 | Guardrail mở rộng được: Chặn / Lời dặn / Thay câu trả lời, bật/tắt từng luật, sửa trên ⚙ | **Code** (Chặn, Thay); AI (Lời dặn) |
| 7 | Định dạng (marked + DOMPurify lưu sẵn), sao chép, tạo lại, sửa tin, **‹ 1/2 ›**, dừng, 👍/👎 | **Code** |
| 8 | Hỏi lại bằng nút lựa chọn + ô tự gõ; hỏi lại 2 lần liên tiếp thì code bắt AI thôi hỏi | AI quyết định hỏi; **code** giới hạn |
| 9 | Kiểm tra | `test_nv2.py` (LLM giả) qua; `test_nv1.py` + 6 test System 3 qua; đo trên model thật + trình duyệt (bên dưới) |

**Đo trên model thật** (`system4/eval/nv2_behavior.py`, kết quả `system4/eval/results/nv2_behavior.json`): **19/19 tình huống đạt**
- Đạt: vai trò/ngôi thứ nhất, tiếng Anh, tiếng Trung, tiếng Việt không dấu, đóng vai, chèn lệnh, bực bội, emoji, hỏi lại có nút, giới hạn 2 lần, danh sách Markdown, tự nhớ (4 điều đúng về "Lan"), nhớ sang hội thoại mới, không hỏi lại thành phố đã nhớ, không nhớ câu xã giao, chế độ "chỉ khi tôi bảo", "hãy nhớ", "hãy quên", không lọt chữ lạ.
- Trình duyệt Edge: định dạng, nút hành động, nút lựa chọn (thẻ cũ bị khoá), tạo lại → ‹ 2/2 › → ‹ 1/2 ›, cửa sổ Bộ nhớ, trình sửa guardrail: không lỗi.
- **Lưu ý trung thực:** 19 tình huống và cách chấm (theo luật, ví dụ "câu đầu có chữ hiểu/xin lỗi/rất tiếc") do agent tự soạn, mỗi tình huống chạy 1 lần; đạt 19/19 không có nghĩa là không bao giờ sai. Bộ lọc chữ lạ/emoji không phải can thiệp lần nào trong lượt đo (model tự tuân thủ); bộ lọc được kiểm trong `test_nv2.py`.

**Việc ngoài ý muốn và cách đã xử lý**
1. **Chậm hơn hẳn NV1:** chữ đầu tiên trung vị **29,6 s** (tối đa 53 s), cả câu trung vị 37 s; NV1 là 11–17 s. Nguyên nhân: lời dặn dài hơn (vai trò, quy tắc, bộ nhớ) làm model "suy nghĩ" lâu hơn. Chưa sửa vì đây là trade-off đã hoãn ở câu 1C (sau NV1) → hỏi lại trong báo cáo.
2. **Lỗi chuyển phiên bản do test phát hiện:** quay về phiên bản cũ thì web đi theo câu trả lời mới tạo nhất thay vì chỗ người dùng đang dừng ở phiên bản đó. Đã sửa: đi tới tin mới nhất trong nhánh của phiên bản được chọn (giống ChatGPT).
3. Cài đặt `FRIENDLY_SYSTEM_PROMPT` của NV1 được thay bằng lời dặn có cấu trúc + `FRIENDLY_EXTRA_INSTRUCTIONS` ("Lời dặn thêm cho AI"). Giá trị cũ đã lưu (nếu có) tự bị bỏ qua.
4. Hai thư viện định dạng được tải một lần và lưu trong `system4/web/static/vendor/` (giấy phép MIT / Apache-MPL ghi ở đầu mỗi tệp).

**Trade-off sau NV2** (nguyên văn câu trả lời, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 1. Tăng tốc Friendly | 1D I forgot to mention you can reuse the planner from System 3, see if it can help. My thinking is code can be too strict and should be relaxed but the model already there should assists in speed a separation of work. Evaluate if what I said is true for reducing speed (I think it's not). I need a new set of solution since 30s is too much. So no C/D option also new model is also out of the table since project constraints I can't change. Use your knowledge for a new set of solution. |

**Đo tốc độ để trả lời câu trên** (cùng 4 câu hỏi, qwen3:4b, RTX 4050):

| Cách | Chữ đầu tiên (trung vị) | Ghi chú |
|---|---|---|
| Hiện tại (suy nghĩ, lời dặn đầy đủ) | 30,0 s | ~95% thời gian là "suy nghĩ" (1.000–2.000 token) |
| Lời dặn rút gọn + "suy nghĩ thật ngắn" | 17,2 s (10–24 s) | vẫn quá chậm |
| Đóng khối suy nghĩ sẵn / cắt suy nghĩ sau 150 token | — | **không dùng được**: model vẫn suy nghĩ tiếp ngay trong câu trả lời |
| Ép đầu ra JSON (không suy nghĩ) | 1–3 s cả câu | nhanh nhưng kém hơn: bịa địa điểm, có câu thiếu nội dung, dùng sai nút lựa chọn |
| Ép JSON có trường "plan" ngắn trước câu trả lời | 1,3–2,6 s | khá hơn hẳn bản JSON thường |

**Đánh giá ý "dùng lại Planner của System 3; nới code, để model gánh việc"** (câu 1D): đúng như người dùng nghi ngờ, **không làm nhanh hơn**. Toàn bộ code kiểm tra tốn ~1 ms; 30 s là ~95% do model suy nghĩ. Chia việc chỉ nhanh hơn khi chuyển việc **từ model sang code** (hoặc sang lời gọi không suy nghĩ), không phải ngược lại. Planner luật của System 3 dành cho thủ tục hành chính, với câu hỏi chung không nhận ra gì; Planner bản AI thêm một lần gọi model (P19_REPORT: không có lợi). Thứ nên dùng lại là cách làm: quyết định bằng code trong vài ms trước khi gọi model.

**Trả lời tiếp theo** (nguyên văn, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 1. Chiến lược tốc độ | 1A but it should also has an explicit think harder like ChatGPT UI and the user can interupt think harder with a "Trả lời nhanh" button. Default is fast. Also before you edit anything I want you to list out all the current requirements for the LLM |
| Danh sách yêu cầu cho LLM | I said for the LLM not the whole system in general, for the LLM instructions only Drop 2,3,10,13,14,35 Relax 22 (remember only useful information like name, what they like OR what they explicitly told, Not every prompt). |
| 1. Bỏ #2, #3? | 1C |

---

## Phần D — Báo cáo làm lại tốc độ (2026-10-07)

**Đã làm**
| # | Việc | Người dùng thấy |
|---|---|---|
| 1 | **Chế độ Nhanh (mặc định):** ép đầu ra JSON {plan, answer, ask_back, choices}; phần "answer" được tách dần và hiện ngay | Trả lời trong 1–3 s |
| 2 | Công tắc **"Suy nghĩ kỹ"** cạnh ô nhập (chỉ ở Friendly, nhớ theo trình duyệt, mặc định tắt) | Bật thì AI suy nghĩ (~25–40 s) |
| 3 | Nút **"Trả lời nhanh"** trong dòng "Đang suy nghĩ kỹ…" → dừng suy nghĩ, trả lời bằng chế độ Nhanh trong cùng lượt | Không phải chờ nếu không muốn |
| 4 | Nút **"Kỹ hơn"** dưới mỗi câu trả lời Nhanh → trả lời lại bằng Suy nghĩ kỹ thành phiên bản ‹ 2/2 › | |
| 5 | Lời dặn cho AI theo danh sách đã duyệt (xem dưới); câu đồng cảm chỉ thêm khi code thấy người dùng bực bội | |
| 6 | Bộ nhớ nới lỏng: chỉ ghi điều hữu ích; code chỉ chạy bước ghi nhớ khi tin nhắn có dấu hiệu tự kể về bản thân hoặc "hãy nhớ/quên" | Ít điều nhớ hơn, đúng hơn |
| 7 | ⚙: "Chế độ trả lời mặc định" (fast/think) thay cho "AI suy nghĩ trước khi trả lời" | |

**Lời dặn cho AI hiện tại** (đã duyệt: bỏ 2*, 3, 10, 13, 14, 35; nới 22; *giữ #2 theo câu 1C)
- Trả lời: (1) trợ lý hỗ trợ của Team 7, giải đáp hiệu quả, chính xác · (4) ấm áp, không lên lớp · (5) phản chiếu cảm xúc; bực bội → câu đầu đồng cảm (code thêm khi phát hiện) · (6) không emoji · (7) giữ vai, từ chối đóng vai · (8) áp dụng cả khi chưa có dataset · (9) viết tiếng Việt · (12) chỉ chữ Latin · (15) dùng lịch sử + tóm tắt · (17–19) hỏi lại kèm 2–4 lựa chọn, hết lượt thì thôi hỏi · (22) dùng điều đã biết, không hỏi lại · (27–28) lời dặn từ guardrail · (31) NV3: chỉ dùng dữ liệu · (36) Nhanh: plan ngắn rồi trả lời theo JSON; Suy nghĩ kỹ: suy nghĩ rồi trả lời.
- **Thêm mới khi làm (C), có thể bỏ:** "Vào thẳng nội dung: không mở đầu bằng lời chào nếu người dùng không chào, không tự giới thiệu lại nếu không được hỏi"; ở chế độ Nhanh: "Không chắc chi tiết cụ thể (tên riêng, địa điểm, số liệu) thì nói rõ là gợi ý chung, không bịa".
- Bộ nhớ: (22 nới) chỉ ghi tên/cách xưng hô, điều thích/không thích, thông tin ổn định tự kể, điều được bảo nhớ · (24–25) dạng "Người dùng …", xoá khi cũ hoặc được bảo quên.
- Tóm tắt: (16) như cũ.

**Đo trên model thật** (`system4/eval/nv2_behavior.py`; trước: `results/nv2_behavior_before_fast.json`, sau: `results/nv2_behavior.json`)

| | Trước (luôn suy nghĩ) | Sau: Nhanh (mặc định) | Sau: Suy nghĩ kỹ (tuỳ chọn) |
|---|---|---|---|
| Chữ đầu tiên, trung vị (tối đa) | 29,6 s (53,2 s) | **1,0 s (1,4 s)** | 36,4 s (1 câu) |
| Cả câu, trung vị (tối đa) | 37,0 s (55,2 s) | **2,5 s (5,5 s)** | 40,4 s |
| Tình huống đạt | 19/19 | **22/22** (19 cũ + nhớ sở thích, Suy nghĩ kỹ, Trả lời nhanh) | |
| "Trả lời nhanh" | — | chữ đầu 1,4 s sau khi bấm | |

Trình duyệt Edge: công tắc chỉ hiện ở Friendly, chữ đầu 1,6 s, nút "Kỹ hơn", nút "Trả lời nhanh" khi đang suy nghĩ → trả lời 1,5 s sau khi bấm; không lỗi.

**Việc ngoài ý muốn và cách đã xử lý**
1. Lần đo đầu 21/22: chế độ Nhanh hay mở đầu "Chào bạn!" và tự giới thiệu lại, nên câu đồng cảm bị đẩy xuống câu thứ hai. Đã thêm một dòng lời dặn "vào thẳng nội dung…" (ghi ở trên, có thể bỏ) → 22/22.
2. **Chế độ Nhanh vẫn bịa chi tiết** dù đã dặn: số điện thoại hỗ trợ "1900 88…" của Team 7, khẩu hiệu Team 7, "Quán phở Bún Chả 123", "phố cổ" ở Đà Nẵng. Bộ chấm theo luật không bắt được lỗi này. Chưa sửa, đưa thành câu hỏi trade-off trong báo cáo.
3. 22 tình huống và cách chấm do agent tự soạn, mỗi tình huống chạy 1 lần; đạt hết không có nghĩa là không bao giờ sai.

**Trade-off sau phần D** (nguyên văn, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 1. Chế độ Nhanh bịa chi tiết | 1C ,Did you run checks about hallucination? I asked another team they said that they changed the model to qwen 3.5-4B 4bit (bring it back on the table) they also recommend tinkering with token and temperature. My fast answer budget is around 5s so it's okay if it take a bit more time. |
| Kế hoạch đo bịa + so model | Save it for the future, I ran out data to download large files. Let's do task 3 and 4 |

## Phần E — Việc để sau (người dùng hoãn, 2026-10-07)

**Đo hiện tượng bịa (hallucination) và so model/tham số.** Chưa làm vì người dùng hết dung lượng mạng để tải model.
- Trả lời trung thực cho câu hỏi: **chưa có bài đo bịa có hệ thống**; 22 tình huống chỉ đo hành vi. Các chỗ bịa (số điện thoại "1900 88…" của Team 7, khẩu hiệu, "Quán phở Bún Chả 123", "phố cổ" Đà Nẵng) là do đọc tay câu trả lời.
- Kế hoạch đã đề xuất (chưa duyệt):
  1. Bộ ~30 câu hỏi tiếng Việt chấm theo luật: thông tin Team 7 không thể biết, nơi chốn/sản phẩm bịa, kiến thức chung kiểm được, số liệu chính xác, điều người dùng chưa từng kể.
  2. So ở chế độ Nhanh, mục tiêu ≤ 5 s (ngân sách người dùng cho phép): `qwen3:4b` vs `qwen3.5:4b` (có trên Ollama, 3,3 GB, 4-bit, có suy nghĩ/công cụ/hình ảnh); temperature 0,6 / 0,3 / 0,1; "plan" tối đa 300 vs 800 ký tự; với Qwen3.5 thử cả chế độ không suy nghĩ có sẵn (không cần ép JSON).
  3. Chạy lại 22 tình huống hành vi với 1–2 cấu hình tốt nhất; người dùng chọn mặc định trong ⚙.
- Cần khi làm: người dùng chạy `ollama pull qwen3.5:4b` (3,3 GB). Lưu ý: 6 GB GPU không chứa đồng thời `qwen3:4b` (Strict) + `qwen3.5:4b` + model tìm kiếm → Ollama đổi model qua lại khi người dùng chuyển Strict/Friendly, câu đầu sau khi đổi chậm thêm vài giây (cần đo).

# KẾ HOẠCH DỰNG LẠI HỆ THỐNG 2 THEO PROPOSAL

**Ngày:** 2026-09-24 · **Nhánh:** V10.5 (tách từ V10.3) · **Nguồn yêu cầu:** Project Nhóm 7, slide 3–5 và 7–8
**Phạm vi dữ liệu:** thủ tục cấp **Xã/Phường**, gồm 1.350 thủ tục (level=COMMUNE hợp với H29 của TP.HCM)

---

## 0. Nhóm đã chốt (2026-09-24) và đã làm

| # | Quyết định | Đã làm |
|---|---|---|
| 1 | **Gắn nhãn** bản địa phương của các tỉnh | `province` = tỉnh **công bố** bản đó. Suy từ bên ban hành mã `H…` ("UBND tỉnh X"). Kết quả: **614/1.350** bản của UBND tỉnh (TP.HCM 56), 736 bản của bộ/ngành. Bảng ghi "Bản này do UBND … công bố", **không** ghi "chỉ áp dụng ở" |
| 2 | Ô trống: nói rõ là **chưa có thông tin** | Mọi ô trống mở đầu bằng "Chưa có thông tin…" và không bao giờ suy ra "miễn phí" hay "không cần giấy tờ". Phí 0 đồng không kèm ghi chú được hiện thành "Chưa có thông tin về lệ phí … mình KHÔNG chắc thủ tục này miễn phí". LLM 2 cũng có luật tương ứng |
| 3 | Bộ nhận diện "đang hỏi thủ tục": dùng **luật theo CSDL** | ✅ `retrieval.looks_like_procedure()` — xem B2 |
| 4 | **Giữ** Thuế/Hải quan nhưng **nói rõ** | Có nhãn "🏛️ Do cơ quan Thuế/Hải quan giải quyết", ghi chú "… KHÔNG nộp tại UBND phường/xã", và gợi ý trong MCQ |
| 5 | **Từ khoá trước, LLM 1 chỉ khi CSDL không khớp** | `retrieval.parse_query()`: bỏ lời đệm, bung viết tắt (dk, gks, cccd…), tách tên tỉnh ra làm ngữ cảnh. Nếu khớp ≥ 75% âm tiết thì vào thẳng MCQ; nếu không thì gọi LLM 1 (≤ 3 lượt) |
| 6 | Không cần xếp hạng hoàn hảo, **hỏi MCQ "thủ tục chính"** | MCQ 1 hỏi "thủ tục chính" (gom theo tiền tố tên), MCQ 2 hỏi "dạng cụ thể". MCQ 2 lấy **toàn bộ** thành viên của nhóm trong CSDL: bản của tỉnh người dân nhắc đứng trước, rồi bản toàn quốc, rồi tỉnh khác |

**Kết quả chạy thật** (`qwen2.5:1.5b`):

| Câu hỏi | Đường đi | Kết quả |
|---|---|---|
| "t người bình định muốn dk kết hôn" | từ khoá, **không LLM**, 0,1 s | Đăng ký kết hôn (4 dạng) → Thủ tục đăng ký kết hôn |
| "làm giấy khai sinh cho con" | từ khoá trượt, **LLM 1** | Đăng ký khai sinh (8 dạng) → **Thủ tục đăng ký khai sinh**. Bản cũ không ra được thủ tục này |
| "đkj kết hôn" | từ khoá trượt, **LLM 1** sửa thành "đăng ký kết hôn" | ra bảng đúng |
| "giao đất cho thuê đất ở tphcm" | từ khoá, tỉnh = Hồ Chí Minh | MCQ 2: **bản TP.HCM đứng đầu** |
| "khai thuế cho hộ kinh doanh" | từ khoá | nhãn "do cơ quan Thuế giải quyết" |
| "đăng ký bay lên sao Hỏa" | từ khoá, rồi LLM 1 | xin lỗi, nêu khoá và câu gốc |

**Sửa kèm:**
- **Importer.** Đổi `province` của một bản ghi từng tạo ra **614 bản `active` trùng**. Nguyên nhân: importer nhận diện bản ghi theo `(proc_id, province)`. Giờ cùng `proc_id` và `source_id` thì tính là phiên bản mới: 614 bản lên v2, bản cũ chuyển `archived`.
- **Bộ gác thủ tục mới.** "có miễn phí không?" từng bị coi là thủ tục khác; đã thêm "miễn" vào danh sách từ chỉ ô trong bảng.

---

## 1. Hiện trạng kết nối CSDL (đợt trước)

- `procedures.db` có 1.350 bản `active` cấp xã, nối vào Hệ thống 2 qua `retrieval.py`.
- `run_pipeline --all` giờ mặc định `--scope xa`, tái tạo đúng 1.350 id. Trước đây lệnh này cào toàn quốc và làm mất phạm vi xã.
- Đã bỏ MCQ "nộp cấp nào", sửa câu ghi phạm vi, và bỏ giới hạn 103 lĩnh vực.

---

## 2. Proposal so với hiện tại

| Proposal (slide 3) | Hiện tại | Bước |
|---|---|---|
| Mặc định **LLM 2 trò chuyện**: chào hỏi, cảm ơn | ✅ Xong (B2) | — |
| Nút **<Tìm chính xác>**, bộ nhận diện song song, 1 lần mỗi ô chat | ✅ Xong (B2) | — |
| Báo sai ngữ nghĩa → chạy lại như mới | ✅ Xong: ô "Tra lại" gửi `mode="resubmit"` | — |
| LLM 2 đọc toàn bộ trò chuyện, không bịa | Đã có bộ lọc chữ Hán; CARE vẫn `history=None` | **B3** |
| Tra từ khoá, LLM 1 chỉ để chữa cháy | ✅ Xong (quyết định 5) | — |
| MCQ chọn thủ tục chính → dạng cụ thể | ✅ Xong (quyết định 6) | — |
| Versioning: tách `id` / `proc_code`, partial unique index | ✅ Có sẵn, **nay đã dùng thật** (614 bản có tỉnh) | — |
| Bảng đủ các mục, checklist, biểu mẫu, link online, meta | ✅ Có sẵn | — |
| Thủ tục hết hạn: cảnh báo, vẫn đưa bản cũ | ✅ Có sẵn | — |
| Cập nhật CSDL bằng code | ✅ Xong | — |
| Ragas / chấm điểm (slide 8) | Mới chỉ chấm Hệ thống 1 | **B6** |

---

## 3. Việc còn lại

### B2. Máy trạng thái ô chat: CHAT, EXACT, CARE — ✅ XONG (2026-09-24)

```
 tin nhắn thường ─► CHAT   LLM 2 trả lời (nhãn "⚠️ AI tự trả lời, chưa qua CSDL")
                           ║ song song: retrieval.looks_like_procedure() — LUẬT THEO CSDL
                           ╚► khớp → gắn gợi ý 🎯 + chip [🎯 Tìm chính xác: “…”]
 nút 🎯 / chip ────► EXACT  từ khoá → (LLM 1 nếu trượt) → MCQ → bảng
                           ▼ (có proc_id trong retrieval_pending = đã dùng 🎯)
 tin nhắn thường ─► CARE   cảm ơn/chào → câu cố định
                           thủ tục khác → mời ô chat mới (mang theo câu hỏi, tra bằng 🎯)
                           còn lại → LLM 2 trên bảng
 "Tra lại" ───────► xoá bảng, về EXACT (không tính là lần 2)
 🎯 lần 2 ────────► [Mở ô chat mới và tra câu này] [Huỷ]
```

**Đã làm:**
- `mode` trên `ChatRequest` và `TurnInput` (`turn.MODES`). Trạng thái vẫn chỉ đọc từ `retrieval_pending`, nên không cần đổi schema.
- `Backend/core/system_retrieval.py`: thêm `_chat()`, `_exact_used()`, và `_llm_text()` (bộ lọc chữ Hán/Nhật và câu nhắc lại prompt, dùng cho cả trò chuyện lẫn CARE).
- Giao diện:
  - `Frontend/static/js/exact.js` (mới): nút 🎯. Ô nhập có chữ thì gửi ngay; ô trống thì "lên nòng" cho tin nhắn kế tiếp. Chỉ hiện ở Hệ thống 2.
  - `procedure.js`: chip gợi ý, hộp thoại lần 2, ô "Tra lại" gửi `resubmit`, và nút ô chat mới tra luôn câu hỏi.

**Đúng Proposal (nhóm chốt lại 2026-09-24).** LLM 2 trả lời MỌI tin nhắn thường, kể cả câu hỏi thủ tục, bằng hiểu biết chung. Câu trả lời mang nhãn **"⚠️ AI tự trả lời, chưa qua CSDL"** (`answer_source = "llm_only"`). Khi bộ nhận diện bắt được câu hỏi thủ tục, câu gợi ý của Proposal và chip 🎯 được gắn ngay dưới. Bản trước thay câu trả lời bằng câu cố định; đã bỏ theo yêu cầu, vì nhãn cảnh báo đã nói rõ đây là AI tự trả lời. Các cụm xã giao như "cần hỗ trợ", "giúp đỡ", "tư vấn" không làm bộ nhận diện kích hoạt: trước đây "mình cần **hỗ trợ**" khớp nhầm "**Hỗ trợ** chi phí hoả táng".

**Bộ nhận diện** (luật CSDL, không LLM): khớp ≥ 60% và ít nhất 2 âm tiết vào tên thủ tục; câu chỉ gồm từ xã giao thì bỏ qua. Ngưỡng này nới hơn ngưỡng tra thật (75%), vì bỏ sót một gợi ý thì hại hơn gợi ý thừa. Trên bộ thử nhỏ: 10/10 câu hỏi thủ tục có chip, 0/10 câu xã giao bị gắn nhầm.

**Đã kiểm qua HTTP thật** (máy chủ + `app.db` nháp): chào → trò chuyện; "làm giấy khai sinh cho con cần gì" → chip; bấm chip → 3 MCQ → bảng; "lệ phí?" → CARE; "cảm ơn bạn" → câu cố định (0,1 s, trước là 6 s lan man); 🎯 lần 2 → hộp thoại; "Tra lại" → MCQ mới trong cùng ô chat. **Chưa bấm thử trên trình duyệt thật.** JS đã qua trình phân tích cú pháp.

### B3. Siết LLM 2 — ✅ phần lớn XONG (2026-09-24, sau khi chạy thử thật)

**Nhãn câu trả lời (Hệ thống 2).** Bỏ nhãn "Chưa qua kiểm chứng": nhãn đó là của bộ kiểm chứng Web search, sai nghĩa ở đây. Giờ có hai nhãn:
- **📚 Từ database**: bảng do code dựng, hoặc câu code trích nguyên ô.
- **🤖 Trả lời dựa trên database, có thể không đúng**: LLM 2 diễn giải.

Nhãn được ghi vào `intent.answer_source`; Web search không đổi gì.

**Hỏi tiếp sau bảng — code trả lời trước, LLM 2 là đường cuối:**

| Câu hỏi | Đường đi |
|---|---|
| cảm ơn / chào | câu cố định |
| "Chắc không?", "đúng không?" | câu cố định: dữ liệu trích nguyên văn từ dichvucong.gov.vn, ngày cổng cập nhật, ngày mình lấy về |
| hỏi về MỘT ô (lệ phí, thời gian, giấy tờ, nơi nộp, online, biểu mẫu, cơ quan) | **code trích nguyên ô** |
| như trên nhưng có điều kiện ("nếu tôi thuộc hộ nghèo…", "còn người khuyết tật thì sao?") | code trích nguyên ô, mở đầu bằng "bạn đối chiếu với trường hợp của mình". "Còn X thì sao" mượn mục của câu trước |
| tóm tắt / giải thích / tại sao / so sánh | LLM 2, **chỉ được đọc các mục liên quan**, vai `care` (320 token), kèm câu hỏi trước đó |

**So sánh trước/sau trên mô hình thật** (bản cũ = cả bảng, vai `answer` 900 token):

| Câu hỏi | Bản cũ | Bản mới |
|---|---|---|
| "cần mang giấy tờ gì?" | **sai:** "chưa có thông tin" | đúng, danh sách 33 mục |
| "có nộp online được không?" | **sai:** "chưa có thông tin" | đúng, kèm link |
| "hộ nghèo có phải nộp lệ phí?" | **sai** (LLM trả "chưa có thông tin" **6/6 lần**) | trích ô lệ phí, trong đó có "Miễn lệ phí cho … hộ nghèo" |
| "Tóm tắt phần Giải thích" | 1.489 ký tự, 7,6 s, bịa "sổ hộ khẩu, hoá đơn VAT" | 830 ký tự, 2,1 s, chỉ phần giải thích |
| "Chắc không?" | trả lời về địa điểm (lạc đề) | câu cố định về nguồn dữ liệu |

**Sửa kèm:**
- **Thời gian không có đơn vị.** 86 thủ tục bị cổng ghi `processingTimeUnit: "OTHER"`, tức chỉ có con số. Bảng giờ ghi "3 (Cổng … không ghi đơn vị — không rõ là ngày hay giờ)"; trước đây ghi trần "3" và LLM 2 tự thêm "ngày".
- **"còn người khuyết tật thì sao?"** từng bị bộ gác coi là thủ tục mới. Giờ nếu X trong "còn X thì sao" nằm nguyên văn trong bảng đang xem thì tính là hỏi tiếp (`procedure_table.refers_to_table`).
- **🎯 kèm câu chỉ có lời chào** ("Chào") thì không đem đi tra, mà mời nhập tên thủ tục.
- **Nút 🎯 KHÔNG tự gửi nữa.** Bấm là lên nòng, người dùng gõ câu hỏi rồi bấm Gửi.

**Cảnh báo không bao giờ chặn câu trả lời** (nhóm chốt 2026-09-24). Bộ gác "thủ tục khác" trước đây thay hẳn câu trả lời bằng lời mời mở ô chat mới. Giờ câu trả lời (code trích hoặc LLM 2) luôn hiện trước, cảnh báo và nút ô chat mới được **gắn sau** (`_warn_other`), đúng Proposal: "chúng tôi không chịu trách nhiệm nếu bạn hỏi thủ tục mới và AI trả lời sai trong ô chat này". Lý do phải đổi: bộ gác khớp theo chữ không dấu nên có báo nhầm. Ví dụ "Ngắn hơn nữa" = "ngan hon" khớp trọn "ngân … hơn" trong tên một thủ tục thuế, thế là mất câu trả lời.

**Yêu cầu viết lại** ("ngắn hơn", "chi tiết hơn", "nói lại"…, `procedure_table.is_rewrite`) không đi qua bộ gác. LLM 2 nhận câu trả lời trước như văn bản cần sửa, cùng các mục của câu hỏi trước. Đo được: "Ngắn hơn nữa" rút bản tóm tắt từ 1.223 xuống 398 ký tự.

**Còn lại:**
- LLM 2 vẫn yếu ở câu cần suy luận (vd "trẻ bị bỏ rơi thì cần thêm gì?" mở đầu bằng "chưa có thông tin" rồi vẫn liệt kê). Đây là giới hạn của mô hình 1.5B → fine-tune, hoặc thêm luật trích cho các "trường hợp" (`procedure_cases`).
- Cả bản cũ lẫn bản mới đôi khi viết sai chữ có dấu ("Úy tín danh quô̇c gia" thay cho "Ứng dụng định danh quốc gia"). Bộ lọc hiện chỉ bắt chữ Hán/Nhật.

### B6. Bộ chấm điểm Hệ thống 2
- Khoảng 80 câu viết lại từ `THU_TUC_CAP_XA_363.csv` (teencode, không dấu, vùng miền), cộng 15 câu chào hỏi/lạc đề và 20 câu hỏi tiếp.
- Chỉ số:
  - `proc_id` đúng có nằm trong MCQ 1–2 không, và nằm ở vị trí nào
  - số vòng MCQ tới khi ra bảng
  - **tỉ lệ phải gọi LLM 1**, để đo xem từ khoá tự lo được bao nhiêu phần
  - tỉ lệ chào hỏi bị đem đi tra
  - độ trung thành của LLM 2
- Tệp: `Evaluation/eval_system2.py`.

### B5. Dữ liệu
- 27 thủ tục nhóm `review` trong `BAO_CAO_GHEP_363_XA.md` cần người xem bằng mắt.
- 44 thủ tục nhóm `absent` phải lấy từ nguồn khác (CSDL quốc gia về TTHC, hoặc cổng TP.HCM).
- Người dân nhắc tỉnh cũ đã sáp nhập (vd "Bình Định") thì hiện chưa ánh xạ sang tỉnh mới. Chỉ ảnh hưởng thứ tự ở MCQ 2, không làm sai kết quả.

### B7. Cập nhật tài liệu — ✅ XONG (2026-09-24)
README, `ARCHITECTURE.md` §0, `STRUCTURE.md`, `SETUP.md` (thêm bước 7 cào CSDL + `-SkipScrape`), `CODEBASE_INDEX.md` (sinh lại) đã theo V10.5. `PHASE2_RETRIEVAL.md` giữ nguyên làm hồ sơ V10.3, có bảng "chỗ nào đã cũ" ở đầu. `PHASE1_PLAN.md` D2 có ghi chú cập nhật về `province`. Script cài đặt ghi V10.5 và ~1.350 thủ tục; đã chạy thật `Setup First Time.bat` và cào thử từ một bản checkout sạch.

**Thứ tự đề xuất:** B6 → B5 (phần còn lại của B3 chờ fine-tune).
Fine-tune (slide 7) giờ nhẹ hơn: LLM 1 chỉ còn chữa các câu gõ sai hoặc mơ hồ. B6 sẽ cho biết đó là bao nhiêu phần trăm số câu hỏi, và từ đó có đáng fine-tune hay không.

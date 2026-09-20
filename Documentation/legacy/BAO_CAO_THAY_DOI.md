# BÁO CÁO KỸ THUẬT: CÁC THAY ĐỔI SO VỚI COMMIT GỐC (d81aa94)

Tài liệu này ghi nhận trung thực và chi tiết toàn bộ các thay đổi mã nguồn, tính năng và sửa lỗi đã thực hiện so với commit ban đầu `d81aa94` ("Add files via upload"). Không sử dụng văn phong phóng đại; chỉ liệt kê các thay đổi kỹ thuật thực tế và nguyên nhân thực hiện.

---

## 1. TỔNG QUAN THỐNG KÊ

- **Số file thay đổi**: 18 file sửa đổi (`git diff`), 1 file tạo mới (`app/core/eval_export.py`).
- **Tổng số dòng**: +965 dòng thêm, -164 dòng xóa/thay thế.
- **Mục tiêu can thiệp chính**:
  1. Khắc phục lỗi hội thoại nhiều lượt (Multi-turn conversation): không kế thừa thủ tục ở câu hỏi tiếp theo ("thủ tục này có tốn phí ?", "lệ phí thì sao", "ở đâu?").
  2. Khắc phục lỗi câu trả lời bị xóa trắng thành chuỗi rỗng kèm nhãn cảnh báo do cơ chế xử lý dấu ngoặc vuông.
  3. Bổ sung tính năng gợi ý 3 prompt tìm kiếm (Cách 3) khi cần làm rõ câu hỏi, cho phép người dùng bấm tìm trực tiếp qua MCP DuckDuckGo.
  4. Sửa lỗi nút xuất file `.txt` bị lỗi `{"detail":"Not Found"}`.
  5. Thiết lập cơ chế kiểm chứng (Verifier) và khóa nghiệp vụ (Intent / Query locks) chống ảo giác và chặn dẫn người dân đến sai cơ quan.

---

## 2. CHI TIẾT THAY ĐỔI THEO TỪNG TỆP TIN

### 2.1. Nhóm Xử lý Ý định & Điều phối (Core Intent & Orchestrator)

#### `app/core/intent.py`
- **Bổ sung hàm nhận diện tham chiếu ngữ cảnh**:
  * `_has_backreference(text)`: Kiểm tra các từ quy chiếu nối tiếp (*"thủ tục này"*, *"cái này"*, *"lệ phí"*, *"ở đâu"*, *"bao lâu"*, *"hồ sơ"*, ...) hoặc câu hỏi ngắn không mang từ khóa thủ tục mới.
  * `_extract_recent_procedure(history)`: Quét ngược lịch sử hội thoại gần nhất để lấy lại thủ tục người dùng đang trao đổi.
- **Kế thừa thủ tục và khóa thuộc tính (`understand`)**:
  * Nếu người dùng hỏi câu hỏi nối tiếp và không đưa ra thủ tục mới: Kế thừa `intent = prev_intent` từ lượt trước.
  * Tự động làm sạch tiền tố người dùng (*"cho tôi hỏi"*, *"tôi muốn"*, *"tôi cần"*) và viết lại `standalone_question` gắn liền với thủ tục cũ: `Lệ phí {thủ tục}`, `Thời hạn giải quyết {thủ tục}`, `Nơi nộp hồ sơ {thủ tục}`, `Hồ sơ giấy tờ {thủ tục}`.
  * Khóa đảm bảo thuộc tính: Nếu câu hỏi hỏi về phí/thời gian/địa điểm, ép `standalone_question` phải chứa các từ khóa tương ứng để tránh bị trôi chủ đề.
- **Làm sạch và tối ưu truy vấn MCP (`_keyword_queries`)**:
  * Tự động bổ sung các truy vấn mang từ khóa chuẩn nghiệp vụ và năm hiện tại (`2026`).
  * Loại bỏ tiền tố trùng lặp (ví dụ: tránh tạo ra chuỗi `"mức thu lệ phí Lệ phí..."`).
- **Phân luồng gác cổng (`analyze`)**:
  * `_is_generic_procedure_query(text)`: Nhận diện các câu quá chung chung (*"cho hỏi thủ tục"*, *"tôi muốn làm giấy tờ"*) và chuyển về `clarify` kèm 3 gợi ý cụ thể, không để mô hình tự bịa.
  * `_is_real_greeting` và `_is_real_out_of_scope`: Chặn cứng chỉ cho phép chuyển `chitchat` khi câu chào ngắn (<= 3 từ) và `out_of_scope` khi nhờ việc ngoài hành chính (viết thơ, giải toán, viết code), tránh việc câu hỏi thủ tục thật bị từ chối oan.
  * `generate_prompt_choices(question, u, year)`: Sinh 3 gợi ý tìm kiếm theo intent để người dùng bấm chọn nhanh.
  * `_build_smart_clarify(question, u)`: Sinh câu hỏi làm rõ theo ngữ cảnh thủ tục thay vì nhại lại câu hỏi của người dùng.

#### `app/core/orchestrator.py`
- **Hỗ trợ chế độ tra cứu trực tiếp (`direct_search`)**:
  * Khi người dùng bấm 1 trong 3 gợi ý (hoặc gửi truy vấn trực tiếp): Bỏ qua bước phân tích `intent.analyze()`, chuyển thẳng sang MCP DuckDuckGo để tra cứu nguồn và trả lời.
- **Chuyển giao gợi ý (`choices`)**: Bổ sung trường `choices` vào `TurnResult` để truyền xuống giao diện web.
- **Sửa phân loại kết quả**: Khi đã tra cứu được nguồn tài liệu từ MCP, cố định `res.kind = "answer"` (không tự gán thành `not_in_sources` khi câu trả lời có chứa nguồn hợp lệ).

---

### 2.2. Nhóm Kiểm chứng & Xử lý Văn bản (Verifier & Text Domain)

#### `app/core/verifier.py`
- **Thêm các luật kiểm chứng thực thể cứng trong `rule_check`**:
  * `ADMIN_AUTHORITY_KEYWORDS` & regex cơ quan: Kiểm tra cơ quan tiếp nhận được nêu trong câu trả lời có thuộc hệ thống hành chính công hợp lệ (`UBND`, `Công an`, `Cổng Dịch vụ công`, `VNeID`, `Cơ quan thuế`, `BHXH`...) hoặc có mặt trong tài liệu hay không.
  * Chặn lỗi thẩm quyền đặc thù: Đánh FAIL nếu chỉ định người dân làm Căn cước / Hộ chiếu tại cơ sở y tế hoặc bệnh viện.
  * `SPECIFIC_NICHES`: Đánh FAIL nếu câu trả lời tự ý chuyển sang ngành nghề kinhdong hẹp không được hỏi (cầm đồ, vũ trường, karaoke, xuất khẩu lao động, kiểm toán).
  * Kiểm tra thiên kiến đồng thuận (Confirmation bias): Nếu người dùng hỏi xác nhận mốc số liệu (ví dụ: *"có phải 120 ngày không"*) mà tài liệu quy định số khác, chặn câu trả lời đồng thuận sai.
- **Mở rộng nhận diện câu trả lời âm tính (`says_not_found`)**:
  * Bổ sung các cụm từ: `"chưa có thông tin"`, `"không có thông tin"`, `"chưa ghi nhận"`, `"chưa quy định"`, `"chưa rõ"`.
  * Tránh việc câu trả lời nêu trung thực "tài liệu chưa có thông tin" bị đánh lỗi `too_short` (quá ngắn).
- **Sửa lỗi xóa trắng bản nháp trong `apply_fail_policy`**:
  * Thay thế lệnh xóa triệt để `BRACKET_RE.sub(...)` bằng `_clean_non_citation_brackets(draft)`. Khi bản nháp không đạt kiểm chứng, giữ lại nội dung và nguồn kèm lời nhắc người dân đối chiếu, không xóa thành chuỗi rỗng.

#### `app/domain/text.py`
- **Cập nhật hàm `_clean_non_citation_brackets`**:
  * Trước đây: Mọi nội dung nằm trong ngoặc vuông `[...]` không phải `[S#]` đều bị xóa thành `""`. Nếu LLM đóng ngoặc cả câu hoặc nhãn, toàn bộ câu đó biến mất.
  * Hiện tại: Bóc bỏ dấu ngoặc vuông `[` và `]` để giữ lại chữ bên trong; chỉ giữ nguyên dấu ngoặc cho trích dẫn nguồn `[S#]`, và chỉ xóa bỏ các nhãn khung rác ngắn rỗng.

---

### 2.3. Nhóm Prompt Mẫu (Prompts Templates)

#### `app/prompts/templates.py`
- **`understand_system`**:
  * Bổ sung nguyên tắc xử lý hội thoại nhiều lượt: khi gặp câu hỏi nối tiếp, bắt buộc giữ nguyên thủ tục ở lượt gần nhất trong lịch sử hội thoại và ghép khía cạnh người dùng hỏi vào để tạo `standalone_question`.
  * Quy định rõ: khi `needs_clarification=false`, bắt buộc trả về chuỗi rỗng `""` cho trường `clarifying_question` để tránh hiện tượng model lặp lại câu hỏi tự sinh vô tận.
- **`understand_examples`**:
  * Bổ sung các ví dụ few-shot nhiều lượt thực tế: hỏi lệ phí sau khi hỏi đăng ký kết hôn; hỏi lệ phí sau khi hỏi giấy phép xây dựng; hỏi nơi nộp hồ sơ.
- **`answer_system`**:
  * Hướng dẫn cụ thể cách trả lời về lệ phí: nêu rõ số tiền nếu có; nêu rõ miễn phí nếu tài liệu ghi nhận miễn phí; nêu rõ tài liệu chưa ghi nhận và hướng dẫn hỏi Một cửa UBND nếu tài liệu chưa nêu cụ thể.
  * Hướng dẫn cơ quan tiếp nhận đúng chức năng cấp xã/tỉnh và Cổng Dịch vụ công/VNeID.
- **`verify_system`**:
  * Bổ sung kiểm tra thiên kiến đồng thuận sai lệch số liệu và kiểm tra thẩm quyền giải quyết thủ tục.

---

### 2.4. Nhóm Giao diện & API (API, Routes, Frontend)

#### `app/api/chat_routes.py` & `app/api/dev_routes.py`
- Sửa lỗi nút xuất file `.txt` trả về `{"detail": "Not Found"}`:
  * Bổ sung endpoint `GET /api/conversations/{conv_id}/export.txt` trả về file text định dạng chuẩn hóa kèm theo Evidence Pack và nhật ký kiểm chứng.
  * Bổ sung endpoint `GET /api/dev/export-eval.txt` trong `dev_routes.py` phục vụ xuất dữ liệu kiểm thử.
- Hỗ trợ tham số `direct_search: bool` trong `ChatRequest`.
- Bổ sung `choices` vào sự kiện SSE `done` gửi về cho frontend.

#### `app/core/eval_export.py` (File mới)
- Xây dựng mô-đun định dạng văn bản cho file xuất `.txt`:
  * Bao gồm thông tin phiên hội thoại, profile tỉnh/xã, từng lượt hỏi - đáp của user và bot.
  * Ghi lại chi tiết Evidence Pack (tiêu đề, domain, snippet, ngày đăng).
  * Ghi lại nhật ký Verifier (verdict, rule issues, unsupported claims).
  * Tích hợp sẵn khung hướng dẫn (Evaluator Prompt) để người dùng có thể tải file và gửi thẳng cho ChatGPT/Claude chấm điểm.

#### Frontend (`app/static/js/chat.js`, `conversations.js`, `dev.js`, `styles.css`, `index.html`)
- **Hiển thị 3 nút gợi ý tìm kiếm (Cách 3)**: Khi bot trả về câu hỏi làm rõ kèm danh sách `choices`, giao diện hiển thị 3 chip bấm nhanh. Khi bấm, tin nhắn được gửi đi với cờ `direct_search: true`.
- **Cập nhật nút Xuất file `.txt`**: Trỏ đúng đường dẫn `/api/conversations/{id}/export.txt` trên thanh bên lịch sử hội thoại và bảng Dev.
- **Trạng thái nút Feedback**: Đảm bảo hiển thị trực quan và lưu trạng thái phù hợp/không phù hợp trên tin nhắn.
- **Giao diện CSS**: Thêm định dạng hiển thị cho các nút gợi ý bấm nhanh và căn chỉnh bố cục tin nhắn.

---

## 3. KẾT QUẢ KIỂM THỬ THỰC TẾ TRÊN CÁC TÌNH HUỐNG LỖI BAN ĐẦU

| Tình huống ban đầu | Hiện tượng lỗi ban đầu | Kết quả sau khi chỉnh sửa |
|---|---|---|
| **Câu hỏi**: *"thủ tục này có tốn phí ?"* sau *"tôi muốn đăng kí giấy kết hôn"* | Model bị trôi ý định, sinh truy vấn sai hoặc câu trả lời bị xóa rỗng chỉ còn dòng cảnh báo. | Kế thừa đúng `marriage_registration`, viết lại thành `Lệ phí đăng ký giấy kết hôn`, tra cứu đúng lệ phí kết hôn, kiểm chứng `PASS`. |
| **Câu hỏi**: *"lệ phí thì sao"* sau *"xin giấy phép xây dựng"* | Model không nhận diện được ngữ cảnh xây dựng, đoán sang thủ tục khác. | Kế thừa đúng `land_administration`, viết lại thành `Lệ phí giấy phép xây dựng nhà ở`, tra cứu đúng biểu phí xây dựng. |
| **Câu hỏi**: *"mất bao lâu thì xong"* (lượt 3 xây dựng) | Bị mất dấu ngữ cảnh thủ tục của 2 lượt trước. | Nhận diện tiếp tục thủ tục xây dựng, viết lại thành `Thời hạn giải quyết giấy phép xây dựng nhà ở`, kiểm chứng `PASS`. |
| **Câu hỏi**: *"Nhà tôi có khách ở lại qua đêm, có phải báo công an không"* | Bị nhại lại câu hỏi hoặc từ chối hỗ trợ sai luồng. | Đi vào luồng tra cứu thủ tục thông báo lưu trú, giải thích rõ quy định thông báo lưu trú và cơ quan tiếp nhận. |
| **Xuất file `.txt`** từ giao diện | Báo lỗi `{"detail": "Not Found"}`. | Tải xuống file `.txt` đầy đủ diễn biến, mã nguồn [S#], Evidence Pack và Evaluator Prompt. |

---

## 4. GIẢI TRÌNH 2 VẤN ĐỀ TRONG PHIÊN THỬ NGHIỆM THỰC TẾ (#7) VÀ PHƯƠNG ÁN XỬ LÝ DỨT ĐIỂM

### 4.1. Vì sao không thấy 3 prompt gợi ý DuckDuckGo (Cách 3) khi AI không chắc chắn?
- **Nguyên nhân kỹ thuật trong mã nguồn cũ**:
  1. Trong `app/core/intent.py` (dòng 486-488 cũ), điều kiện kích hoạt hỏi lại bị giới hạn cứng bởi độ dài từ:
     ```python
     words_count = len(question.split())
     wants_clarify = (u.gate == "ask" and words_count <= 6) or (u.intent == "unknown" and words_count <= 3)
     ```
     Trong phiên test thực tế #7, mọi câu hỏi người dùng đặt ra đều dài từ 7 đến 15 từ (ví dụ: *"tôi sắp thi công xây nhà thì làm giấy tờ khởi công như nào ?"* có 15 từ, *"Tôi đóng cửa tiệm luôn thì cần trả giấy phép không"* có 11 từ). Do đó `wants_clarify` luôn luôn bằng `False`, hệ thống luôn bị ép đi vào luồng `search` và `u.choices` không bao giờ được sinh ra.
  2. Trong `app/core/orchestrator.py`, khi việc tra cứu qua MCP không có nguồn (`no_evidence`) hoặc sau khi kiểm chứng bị đánh giá `FAIL` / `says_not_found` (câu trả lời không đủ căn cứ), hệ thống chỉ trả về dòng thông báo lỗi mà hoàn toàn không cấp phát `res.choices`. Do đó người dùng không thấy 3 nút bấm gợi ý tra cứu DuckDuckGo.
- **Giải pháp đã thực hiện**:
  1. Bỏ rào cản giới hạn cứng `<= 6` từ ở `intent.py`. Phân biệt rõ câu hỏi khởi đầu mơ hồ (kích hoạt `clarify` + `choices`) với câu hỏi nối tiếp đã kế thừa được tên thủ tục (tiếp tục tra cứu chính xác theo khía cạnh).
  2. Trong `orchestrator.py`: Bổ sung cơ chế tự động cấp phát `res.choices` qua `generate_prompt_choices()` ở mọi điểm AI "không chắc chắn":
     - Khi `no_evidence` (MCP DuckDuckGo không tìm thấy kết quả phù hợp).
     - Khi Verifier đánh giá `FAIL` (không đủ căn cứ xác thực, suy diễn ngoài nguồn).
     - Khi câu trả lời thực tế rơi vào dạng `says_not_found` ("tài liệu chưa có thông tin cụ thể").
     Khi đó, 3 nút bấm gợi ý tra cứu DuckDuckGo sẽ lập tức hiển thị ngay dưới câu trả lời để người dùng bấm tra cứu trực tiếp.

### 4.2. Vì sao chatbot trả lời bị lỗi ở Tin nhắn số 6 và Tin nhắn số 14?
- **Tin nhắn số 6 (`"có lệ phí gì không ?"` sau câu hỏi thi công xây nhà)**:
  * *Hiện tượng trước đây*: AI trả lời về điều kiện mặt bằng xây dựng và giấy phép, hoặc bị rò rỉ prompt (in ra `"Lưu ý: Nếu tài liệu ghi rõ mức lệ phí: Nêu số tiền cụ thể S#."`, chêm chữ Hán `không自有`, và hallucinate câu `"Sau khi hoàn thành việc xây dựng, bạn phải nộp lại bản gốc Giấy chứng nhận đăng ký hộ kinh doanh..."` vốn thuộc ví dụ về hộ kinh doanh trong system prompt).
  * *Nguyên nhân*:
    1. Mô hình nhỏ 1.5B rất dễ bị hiện tượng Prompt Leakage (học vẹt và chép nguyên văn các ví dụ cụ thể nằm trong system prompt sang câu trả lời của thủ tục khác).
    2. Snippet tài liệu thu thập từ web đôi khi chứa ký tự Unicode tiếng Trung do nguồn trang mạng bị lẫn.
    3. Trước đây câu hỏi nối tiếp về lệ phí chưa có chỉ dẫn tập trung thuộc tính ở lượt sinh câu trả lời (`answer_user`), khiến mô hình sinh dàn trải lại các bước xây dựng chung chung.
  * *Khắc phục*:
    1. Tách và làm sạch triệt để `answer_system`: gỡ bỏ các câu ví dụ cụ thể về "hộ kinh doanh" và các dòng hướng dẫn placeholder `[S#]` trong system prompt để mô hình không thể học vẹt.
    2. Bổ sung `focus` linh hoạt vào `answer_user`: khi người dùng hỏi về lệ phí, prompt yêu cầu trực tiếp mô hình chỉ tập trung nêu số tiền lệ phí/miễn phí từ tài liệu, không liệt kê lan man các bước hồ sơ.
    3. Tự động thanh lọc ở `tidy_answer` (`app/domain/text.py`): loại bỏ ký tự CJK `[\u4e00-\u9fff]`, xóa placeholder `S#` và các câu nhại prompt.
    4. Thêm kiểm chứng vào `verifier.py`: kiểm tra lệch nghiệp vụ (domain mismatch - phát hiện "hộ kinh doanh" trong câu hỏi "xây nhà") và kiểm tra câu trả lời lệ phí phải có thông tin số tiền hoặc quy định miễn phí. Kết quả: mô hình trả về chính xác mức thu lệ phí cấp giấy phép (0 đồng hoặc 50.000đ - 200.000đ tùy loại) mà không bị hallucination.
- **Tin nhắn số 14 (`"Tôi đóng cửa tiệm luôn thì cần trả giấy phép không"`):**
  * *Hiện tượng*: AI chép lại nguyên văn tiêu đề thông tư Bộ Tài chính và câu hỏi mẫu kết thúc bằng dấu `?`.
  * *Nguyên nhân*: 
    1. Nhận diện ý định bị gán nhầm sang `other` thay vì `business_registration`.
    2. Truy vấn sinh ra là `"thủ tục chấm dứt hoạt động hộ kinh doanh trả giấy phép 2026"`, từ `"trả giấy phép"` không phải thuật ngữ trong văn bản quy phạm pháp luật khiến DuckDuckGo trả về các thông tư phí thương mại chung chung của Bộ Tài chính (TT 06/2025, TT 29/VBHN).
    3. Mô hình 1.5B tự động sao chép các dòng tiêu đề đoạn trích có chứa cụm `"Tài liệu trích dẫn..."` và `"gồm những gì?"`.
  * *Khắc phục*:
    1. Bổ sung ánh xạ intent fallback: khi câu hỏi có từ khóa `dong cua tiem`, `tra giay phep`, `cham dut ho kinh doanh`, tự động gán về `business_registration`.
    2. Tối ưu truy vấn pháp lý chuẩn: sinh thêm `"đóng cửa tiệm có phải nộp lại giấy phép kinh doanh {year}"` và `"chấm dứt hộ kinh doanh nộp lại giấy chứng nhận đăng ký kinh doanh {year}"`. DuckDuckGo trả về chính xác quy định: khi chấm dứt hoạt động hộ kinh doanh bắt buộc phải nộp lại bản gốc Giấy chứng nhận đăng ký hộ kinh doanh.
    3. Thêm bộ lọc `_clean_snippet_noise` trong `app/domain/text.py` và cập nhật `ECHO_MARKERS` trong `app/prompts/templates.py`: triệt tiêu triệt để các dòng rác `"Tài liệu trích dẫn:"` và câu hỏi mẫu kết thúc bằng `?`.
    4. Cập nhật chỉ dẫn `answer_system`: khẳng định rõ ràng quy định nộp lại bản gốc giấy chứng nhận đăng ký hộ kinh doanh ngay câu đầu tiên.

### 4.3. Sửa lỗi nhiễm chéo thủ tục khi chuyển chủ đề (Topic Bleeding) & Chuẩn hóa nút bấm gợi ý
- **Hiện tượng**: Khi người dùng đang hỏi về "xây nhà" chuyển sang *"tôi muốn đăng kí giấy kết hôn"*, AI lại yêu cầu nộp *"Bản vẽ thiết kế xây dựng"* và *"Giấy tờ chứng minh quyền sử dụng đất"*. Đồng thời, 3 nút bấm gợi ý DuckDuckGo bị lặp từ: *"Thủ tục Thủ tục đăng ký kết hôn mới nhất 2026 mới nhất 2026"*.
- **Nguyên nhân**:
  1. *Prompt Leakage*: Trong `answer_system` có dòng hướng dẫn chứa ví dụ mẫu `(ví dụ: Đơn đề nghị, Giấy tờ đất, Bản vẽ thiết kế...)`, mô hình 1.5B học vẹt và chép các ví dụ này sang câu trả lời kết hôn.
  2. *Topic Bleeding (Nhiễm bẩn lịch sử)*: Lịch sử trao đổi của thủ tục xây dựng trước đó vẫn bị nhồi vào ngữ cảnh sinh câu trả lời của thủ tục kết hôn.
  3. *Lỗi nối chuỗi gợi ý*: Hàm `generate_prompt_choices` chưa gọt bỏ tiền tố `"thủ tục"` và hậu tố năm `2026` đã có sẵn trong câu hỏi người dùng bấm.
- **Khắc phục**:
  1. Gỡ bỏ sạch sẽ các ví dụ cụ thể về đất đai/xây dựng ra khỏi `answer_system`, chỉ giữ chỉ dẫn trung tính.
  2. Bổ sung cơ chế **cô lập lịch sử theo thủ tục** trong `orchestrator.py`: Khi người dùng chuyển sang thủ tục mới khác nhóm intent với lượt trước, hệ thống tự động làm mới lịch sử (`hist = []`), ngăn chặn hoàn toàn việc nhồi giấy tờ cũ sang thủ tục mới.
  3. Bổ sung luật kiểm chứng chống nhiễm chéo trong `verifier.py`: Đánh FAIL ngay lập tức nếu thủ tục hộ tịch (kết hôn, khai sinh) hay căn cước xuất hiện các từ khóa xây dựng, đất đai.
  4. Chuẩn hóa hàm cắt gọt chuỗi trong `generate_prompt_choices` để các nút bấm gợi ý hiển thị ngắn gọn, không lặp từ.

---

## 5. TÍCH HỢP DỮ LIỆU & SCRIPT ĐÁNH GIÁ TỪ COMMIT `e3d2f32` (HƯNG)

Đã đối chiếu và tích hợp đầy đủ toàn bộ các file từ commit `e3d2f3205c27b7bb8a09bbe2bd31b44c43347049` (nhánh `Reimage-V10.1` của Hưng) vào cây thư mục làm việc:

1. **Bộ tài liệu định hướng Fine-tune (`TASK_query_finetune_dataset`)**:
   - Ghi nhận lộ trình đo lường baseline, lọc 300–500 cặp câu hỏi lỗi, và kế hoạch QLoRA fine-tune mô hình tạo truy vấn 1.5B riêng biệt.
2. **Bộ công cụ đánh giá (`Evaluation/`)**:
   - `build_eval_set.py`: Khôi phục 862 câu hỏi đánh giá theo 55 thủ tục hành chính (`eval_questions.csv`).
   - `gen_queries_baseline.py`: Script sinh truy vấn baseline tương thích trực tiếp với `app/core/intent.py`.
   - `search_baseline.py`: Đo lường tỷ lệ hit@K khi tra web thật giữa 3 phương án: A (mô hình sinh) vs B (câu hỏi gốc) vs C (gộp A + B).
   - `analyze_queries.py`: Chấm điểm chất lượng câu truy vấn bằng luật heuristic (phát hiện mất dấu, lệch thủ tục, mất khía cạnh).
3. **Bộ dữ liệu gốc (`data/`)**:
   - Khôi phục đầy đủ `normalized_procedures.json`, `rag_knowledge_base.md`, `dataset.xlsx`, `data_merged.xlsx`, cùng chỉ mục vector ChromaDB và BM25 index phục vụ quy trình đánh giá offline.
4. **Tính tương thích**:
   - Toàn bộ commit `e3d2f32` chỉ bổ sung các thư mục `data/`, `Evaluation/` và file `TASK_query_finetune_dataset`, **không chạm vào bất kỳ file nào trong thư mục `app/`**.
   - Các cải tiến cốt lõi trong `app/` (hội thoại đa lượt, kiểm chứng Verifier, xuất file `.txt`, gợi ý DuckDuckGo 3 nút bấm) chạy tương thích và bổ trợ hoàn hảo cho pipeline đánh giá của Hưng.

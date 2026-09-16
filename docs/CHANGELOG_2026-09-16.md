# Báo cáo chỉnh sửa — 16/09/2026

**Phạm vi:** branch mới kéo từ GitHub của nhóm, chạy test local (chưa phải bản giao cuối).
**Người thực hiện:** Claude (Cowork), sửa trực tiếp trong `D:\reimagine`. **Chưa commit git.**
**Quy mô:** 10 file trong `app/`, khoảng 230 dòng thay đổi. Giữ nguyên kiểu xuống dòng CRLF của file gốc.

---

## 1. Bối cảnh — lỗi quan sát khi test chat (mô hình `qwen2.5:1.5b`)

| # | Câu hỏi | Hiện tượng | Nguyên nhân |
|---|---|---|---|
| 1 | `hello` | Trả lời bằng tiếng Anh | Mô hình 1.5B trả lời theo ngôn ngữ của người dùng, bỏ qua system prompt |
| 2 | `t cần làm giấy khai sinh` | Hỏi lại "bạn muốn làm thủ tục gì" dù đã nói là khai sinh | Câu hỏi lại **chép nguyên** ví dụ mẫu số 6 trong `understand_examples`; bộ gác xếp câu này vào `ask` |
| 3 | `giấy khai sinh` | "Tài liệu chưa nêu rõ…" | Không đọc được trang nào, chỉ có đoạn trích vụn; `dichvucong.gov.vn` dựng bằng JavaScript nên trả về 0 ký tự |
| 4 | Đăng ký kết hôn | Nội dung bịa ("Giấy chứng nhận kết hôn của vợ") vẫn hiển thị, chỉ kèm cảnh báo | Cả 6 trang "quá hạn 6s"; chính sách `warn` chỉ lược dòng có **con số** sai, không lược ý bịa bằng chữ |
| 5 | Căn cước trẻ dưới 14 tuổi | Câu trả lời cụt: "bạn sẽ cần:" rồi hết | Sau khi lược bỏ chỉ còn câu dẫn, nhưng vẫn dài hơn 60 ký tự nên không chuyển sang câu "chưa nêu rõ" |
| 6 | GPLX mất, phí 500.000đ đúng không? | Tự mâu thuẫn, không trả lời đúng/sai, trộn TT 63/2023 (đã hết hạn) với mốc 01/01/2026 | Đoạn trích ddgs **gộp nhiều bài** khác ngày; 3 cổng tỉnh đã sáp nhập (kontum, vinhphuc, yenbai) lỗi DNS; tra bổ sung không ưu tiên `.gov.vn` |
| 7 | Xoá thường trú mất bao lâu? | Trả lời "chưa nêu rõ" mà vẫn được đánh **PASS**; ngày đăng nguồn = ngày tra | Không phân biệt câu "không có thông tin" với câu trả lời thật; thư viện đọc ngày lấy ngày hôm nay khi trang không ghi ngày |
| 8 | Lệ phí khai sinh (hỏi nối tiếp) | Đúng, hiểu ngữ cảnh tốt | Phí 6.000đ lấy từ nguồn Huế nhưng không ghi rõ là theo tỉnh đó |

---

## 2. Chi tiết chỉnh sửa theo file

### 2.1. Tìm kiếm và đọc trang

**`app/mcp_search/engine.py`**
- Thêm `warm_up()`: import sẵn `trafilatura` và `extract_metadata`, rồi chạy thử một lần.
- Thêm `clean_snippet()`: tách đoạn trích theo tem ngày của công cụ tìm kiếm (`Mar 4, 2025 · …`, `March 20, 2025 - …`), **chỉ giữ đoạn có ngày mới nhất** và dùng ngày đó làm `published_at`.
- Thêm `_clean_title()`: cắt tiêu đề bị gộp kiểu "Bài A ...Bài B ...".
- Thêm `plausible_date()`: bỏ ngày đăng ở tương lai hoặc trùng đúng ngày tra. Áp dụng cho cả ngày từ kết quả tìm kiếm và ngày đọc được từ trang.
- `fetch_page()`: lỗi phân giải tên miền (`getaddrinfo failed`…) được đánh dấu `dead`. `build_evidence_pack()` loại các nguồn này nếu vẫn còn nguồn khác.
- Ngày đăng đọc từ trang được ưu tiên hơn ngày từ kết quả tìm kiếm.

**`app/mcp_search/server.py`**
- Gọi `engine.warm_up()` trước khi server nhận yêu cầu.

**`app/core/mcp_client.py`**
- `connect()`: khi dùng `direct` hoặc bật `MCP_FALLBACK_DIRECT`, chạy `engine.warm_up()` trong một luồng nền.

### 2.2. Hiểu ý định và hỏi lại

**`app/core/intent.py`**
- Thêm `_copied_clarify()`: phát hiện câu hỏi lại chép nguyên từ ví dụ mẫu. Khi đó xoá câu hỏi lại; nếu đã biết thủ tục cụ thể thì đặt `needs_clarification = False` để đi tra luôn.
- Thêm `_keyword_queries()`: với ý định thủ tục, bỏ dấu `?` ở cuối truy vấn và thêm năm nếu truy vấn chưa có.

**`app/prompts/templates.py`** (bộ gác)
- Thêm 2 ví dụ `search`: `t cần làm giấy khai sinh`, `tôi muốn làm hộ chiếu`.
- `GATE_SYSTEM`: ghi rõ các thủ tục có hồ sơ chung (khai sinh, kết hôn, hộ chiếu, căn cước) thì chọn `search`; chỉ những thủ tục chia nhiều trường hợp (như thường trú) mới chọn `ask`.

### 2.3. Kiểm chứng

**`app/core/verifier.py`**
- `apply_fail_policy()` lược thêm các dòng trùng từ 60% trở lên với `unsupported_claims` của LLM kiểm chứng, để bắt được ý bịa bằng chữ.
- Thêm `_drop_empty_headings()`: bỏ tiêu đề mà các ý bên dưới đã bị lược hết.
- Thêm `detail_lines()` và `has_substance()`: không tính câu dẫn cụt (kết thúc bằng `:`), câu "chưa nêu rõ" và lời chỉ đường ("truy cập…", "để biết thêm…"). Không còn nội dung thật thì trả `NOT_IN_SOURCES_TEXT`.
- Thêm `is_not_found_answer()`: nhận diện câu trả lời chỉ nói "tài liệu chưa nêu rõ".
- Luật mới trong `rule_check()`: câu đầu nói "chưa nêu rõ" mà phía sau lại liệt kê chi tiết thì **FAIL**. Trường `contradiction` mới sinh ghi chú sửa lỗi tương ứng.

**`app/core/orchestrator.py`**
- Câu trả lời chỉ nói "chưa nêu rõ" được gán `kind = "not_in_sources"`, không còn tính là câu trả lời PASS.
- Lượt tra bổ sung sau khi kiểm chứng trượt giờ **có** truy vấn `site:gov.vn` (bỏ `official_bias=False`).

### 2.4. Prompt trả lời

**`app/prompts/templates.py`** (`answer_system`)
- Câu hỏi xác nhận ("… đúng không?") thì câu đầu phải nói rõ **Đúng / Không đúng** kèm con số.
- Chỉ viết "chưa nêu rõ" khi tài liệu **hoàn toàn** không nhắc tới điều được hỏi.
- Không dùng quy định có thời hạn áp dụng đã qua; không ghép con số của văn bản này với ngày hiệu lực của văn bản khác.
- Lệ phí và nơi nộp lấy từ trang của một tỉnh thì phải nói rõ là theo tỉnh đó.

**`app/core/answer.py`**
- `chitchat()`: thêm lời nhắc "Trả lời bằng tiếng Việt, kể cả khi tin nhắn viết bằng tiếng Anh."

### 2.5. Giao diện và CSDL

**`app/static/js/chat.js`**
- Thêm nhãn `not_in_sources` → "Nguồn chưa có thông tin này" (màu xám).

**`app/db/schema.sql`**
- Chỉ cập nhật chú thích danh sách `kind`. **Không đổi cấu trúc bảng**, không cần migration.

---

## 3. Cấu hình `.env` (người dùng tự sửa)

Công cụ truy cập từ xa không được phép ghi `.env`, nên dòng này cần sửa tay:

```diff
- LLM_MODEL=qwen2.5:1.5b
+ LLM_MODEL=3b_finetune_v2:latest
```

Hai biến nên cân nhắc thêm:
- `UNDERSTAND_FEWSHOT`: đặt `false` nếu `3b_finetune_v2` được train bằng pipeline trong `finetune/`.
- `VERIFIER_MODEL`: có thể đặt `qwen2.5:3b` để bước kiểm chứng dùng mô hình gốc. Tốn thêm khoảng 2,4 GB VRAM.

---

## 4. Tình trạng kiểm thử

| Hạng mục | Kết quả |
|---|---|
| Biên dịch (`py_compile`) các file Python đã sửa | ✅ |
| `clean_snippet` / `plausible_date` với đoạn trích thật của lượt 6 | ✅ giữ đoạn 2026, bỏ ngày = hôm nay |
| Dựng Evidence Pack với kết quả tìm kiếm giả lập (có nguồn lỗi DNS) | ✅ nguồn lỗi bị loại, ngày lấy từ tem |
| `verifier` với văn bản thật của lượt 4, 5, 6, 7 | ✅ lược ý bịa, câu cụt → "chưa nêu rõ", bắt mâu thuẫn, lượt 7 không bị bắt nhầm |
| Định tuyến lượt 2 với LLM giả lập | ✅ `search`, truy vấn có năm |
| **Chạy cả luồng với web thật và Ollama** | ⚠️ **Chưa chạy**: môi trường cloud bị chặn truy cập công cụ tìm kiếm |

Việc cần làm trên máy local:
1. Khởi động lại app (`.\run.ps1`) để MCP server nạp code mới.
2. Hỏi lại các câu ở mục 1, nhất là câu kết hôn và câu GPLX 500.000đ.
3. Chạy `.\run.ps1 -EvalIntent` và so với số cũ (1.5B: 84,4% ý định; 100% đúng luồng hỏi lại, trò chuyện, từ chối).

---

## 5. Giữ lại hoặc hoàn tác

```powershell
cd D:\reimagine
git status                      # 10 file modified (+ file báo cáo này)
git diff                        # xem chi tiết

# giữ lại (nên dùng branch riêng)
git switch -c fix/chat-quality
git add app docs/CHANGELOG_2026-09-16.md
git commit -m "Sửa chất lượng trả lời: đọc trang, hỏi lại, kiểm chứng"

# hoàn tác toàn bộ
git restore app
```

## 6. Chưa xử lý (ghi nhận, để sau)

- Trang dựng bằng JavaScript (`dichvucong.gov.vn`) vẫn chỉ dùng được đoạn trích.
- Cổng các tỉnh đã sáp nhập có tên miền **vẫn hoạt động** nhưng nội dung cũ thì chưa bị hạ điểm.
- Các lỗi bảo mật và hàng đợi đã nêu khi quét code được hoãn lại vì hiện chỉ test local.

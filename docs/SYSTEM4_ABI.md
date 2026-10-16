# System 4 — Lĩnh vực ABI (abi.com.vn)

Lĩnh vực cứng thứ ba của System 4 trả lời thông tin trên web **abi.com.vn**: Trung tâm Ươm tạo Doanh nghiệp Nông nghiệp Công nghệ cao TP.HCM.
Phạm vi gồm sự kiện, cơ cấu tổ chức, cán bộ, liên hệ, chương trình và chính sách hỗ trợ, đối tác, sản phẩm, dịch vụ, tin tức và các trang giới thiệu.
Kế hoạch và các sự thật đã kiểm về API nằm ở [PLAN_ABI_LINH_VUC.md](PLAN_ABI_LINH_VUC.md). Tài liệu này mô tả phần **đã làm** (16/10/2026).

## 1. Cách dùng
| Ai | Làm gì |
|---|---|
| Mọi người | Chọn lĩnh vực **«ABI – Trung tâm Ươm tạo»** trên thanh lĩnh vực rồi hỏi. Không cần tải tệp. |
| Dev | Nút **Lĩnh vực** (quản lý lĩnh vực) → dòng ABI có nút **Đồng bộ ngay** (đồng bộ bằng tay, hiện tiến độ) và công tắc **"Hỏi thêm trợ lý của web khi dữ liệu không có"**. Quản trị → tab **Dữ liệu ABI**: cũng có "Đồng bộ ngay", số bản ghi từng loại, lịch sử đồng bộ. ⚙ Cài đặt → nhóm **Lĩnh vực ABI** (mục 4). Có thể đổi tên lĩnh vực; không xoá được, không đổi được sang lĩnh vực mềm. |
| Dòng lệnh | `python run_server.py -m system3.system4.abi.sync` đồng bộ dữ liệu và dựng chỉ mục (cần Ollama); thêm `--no-index` để chỉ lấy dữ liệu. |

**`Set up first time.bat` bước [9/10]** tải sẵn snapshot dữ liệu: lần đầu khoảng 3 phút, những lần chạy lại chỉ tải phần đổi, khoảng 25 giây.
Lệnh: `python -m system3.system4.abi.sync --no-index`. Lỗi mạng thì bước này chỉ báo và cài đặt chạy tiếp.
Lần đầu khởi động server, lĩnh vực ABI được **tạo tự động**. Tìm lĩnh vực này theo `engine = 'abi'`, không theo id cố định (DB đang chạy có thể đã dùng id 3, 4).
Khoảng 20 giây sau khi khởi động, nếu chưa có dữ liệu thì server **tự đồng bộ**: khoảng 2,5 phút tải dữ liệu, cộng khoảng 1 phút tạo vector cho 1.567 đoạn.
Chỉ mục tìm kiếm cần **Ollama** (bge-m3) và **tài khoản dev**, vì bộ dữ liệu dùng chung phải đứng tên dev.
Các câu đếm và liệt kê chỉ cần `data.json`, không cần chỉ mục.

## 2. Luồng một câu hỏi
```
tin nhắn ─► chat.run (System 4) ─ guardrail chặn? ─ câu chào? (code_first) ─► abi/turn.prepare
   ① abi/router: nhận ý định bằng code, < 1 ms
      ├─ hiểu trọn câu hỏi (sau khi bỏ từ của ý định + từ đệm không còn chữ nào) ─► abi/tools: câu trả lời bằng CODE, không gọi AI, ~0,1 s
      └─ còn điều kiện lạ / hỏi về một mục cụ thể ─► "thẻ dữ kiện" [1] do code tính
   ② search.search (BM25 + bge-m3 + reranker) trên bộ dữ liệu "abi.com.vn (tự đồng bộ)" ─► các đoạn [2], [3]…
   ③ không có gì và ⚙ ABI_REMOTE_RAG bật ─► hỏi trợ lý RAG của web (giới hạn tần suất)
   ─► AI (Chuyên gia) trả lời kèm lời dặn: ngày hôm nay, giờ đồng bộ, guardrail của lĩnh vực, "trả lời đúng trọng tâm"
```
Mọi nguồn [n] đều là link về trang gốc trên abi.com.vn.
**"Sắp diễn ra" được tính lúc hỏi** từ `startsAt` / `endsAt`, theo giờ Việt Nam. Code không dùng `lifecycleStatus` đã lưu lúc đồng bộ.
Câu hỏi tiếp kiểu "còn tháng 11 thì sao?" được ghép với câu trước. Router xét câu hiện tại trước, chỉ dùng câu đã ghép khi câu hiện tại không đủ ý.
**"Trung tâm"** không kèm tên khác được hiểu là Trung tâm Ươm tạo: khi tìm, code ghép tên đầy đủ của trung tâm vào câu tìm (`turn.search_text`), và AI được dặn thêm điều này.
Lý do: lần đo 11:36, câu "Trung tâm được thành lập năm nào?" tìm trúng trang đối tác "Trung tâm Nghiên cứu và Phát triển NN CNC" (2005), nên AI trả lời sai trung tâm.

Các ý định code trả lời trọn:
- sự kiện sắp, đang, đã diễn ra; sự kiện theo tháng; sự kiện theo thành phố (Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Hải Phòng); số sự kiện
- số phòng ban, số cán bộ, Ban Giám đốc
- liên hệ: địa chỉ, hotline, email, giờ làm việc
- số và danh sách doanh nghiệp ươm tạo, đối tác, sản phẩm, dịch vụ, chương trình hỗ trợ; tin mới

Các trường hợp code chỉ đưa thẻ dữ kiện cho AI:
- câu nhắc tên một sự kiện, một phòng, một cán bộ
- câu có điều kiện mà code chưa hiểu, ví dụ "sự kiện nào có hình thức trực tuyến?"

## 3. Dữ liệu
| Tệp / chỗ | Nội dung |
|---|---|
| `system4/runtime/abi/raw.json` | Bản API gốc (≈2,7 MB). Lần sau chỉ tải lại chi tiết tin có `updatedAt` đổi: **298 request lần đầu, 28 request các lần sau**. |
| `system4/runtime/abi/data.json` | Bản đã chuẩn hoá (≈1,7 MB). Code đọc một lần rồi giữ trong bộ nhớ, đọc lại khi tệp đổi. |
| `system4/runtime/abi/status.json` | 30 lần đồng bộ gần nhất: kết quả, số request, thay đổi theo loại. |
| Bộ dữ liệu "abi.com.vn (tự đồng bộ)" | Bản ghi + vector trong `system4.db` / Qdrant, gắn `mapping.source = "abi_sync"`. Dựng bộ mới xong mới xoá bộ cũ. Nội dung không đổi thì bỏ qua. `datasets.py` không xử lý lại bộ này như tệp tải lên; nút "Thử lại" và "Cách đọc" trả 422. |

Số liệu ngày 16/10/2026:
- 9 đơn vị (Ban Giám đốc + 8 phòng), 66 cán bộ
- 10 sự kiện (4 sắp diễn ra)
- 58 chương trình
- 149 mục danh mục: 127 đối tác (73 doanh nghiệp ươm tạo), 14 sản phẩm, 8 dịch vụ
- 266 tin và tài liệu, 11 trang giới thiệu

**An toàn khi đồng bộ.** Code giữ bản cũ khi API đổi cấu trúc, ví dụ thiếu phòng ban, thiếu `startsAt` hoặc tin rỗng. Bản cũ cũng được giữ khi số mục tụt hơn một nửa so với lần trước.
Chỉ gọi GET các API công khai, tối đa 2 request/giây. Không đụng các đường `/admin`.
Lần đồng bộ lỗi (mất mạng…) thì thử lại sau 30 phút. Có dữ liệu mà chưa có chỉ mục (lúc đó chưa có tài khoản dev, hoặc Ollama chưa chạy) thì lịch tự dựng chỉ mục ở vòng kiểm sau, 10 phút một lần.

**Bài bị loại** (`normalize.excluded`) không vào chỉ mục và không vào "tin mới". Nếu trợ lý của web dẫn những bài này thì câu trả lời của nó cũng bị bỏ:
- Bài **"Cơ Cấu Tổ Chức"** (03/2025, ghi 7 phòng): đã có dữ liệu chính thức `/organization` (8 phòng). Trợ lý của web đọc bài này nên trả lời sai số phòng ban.
- Mọi bài chứa chữ mẫu của giao diện web (`myYahoo`, `mySkype`, `myViber`), ví dụ bài **"Thông Tin Liên"**. Bài này là trang mẫu chưa sửa: "Phòng Chăm sóc khách hàng", "Phòng Kỹ thuật", fax "08 38.000.003", email info@abi.com.vn — đều không phải thông tin thật. Liên hệ thật lấy từ `/site/settings`.

## 4. Cài đặt (⚙ nhóm "Lĩnh vực ABI")
| Khoá | Mặc định | Ý nghĩa |
|---|---|---|
| `ABI_SYNC_HOURS` | 6 | Tự đồng bộ mỗi N giờ (0 = tắt) |
| `ABI_CODE_ANSWER` | bật | Code hiểu trọn câu hỏi thì trả lời bằng code. Tắt thì code vẫn tính, AI diễn đạt lại. |
| `ABI_REMOTE_RAG` | **tắt** | Hỏi trợ lý RAG của web khi dữ liệu đồng bộ không có đoạn nào khớp. Bật / tắt ở ⚙ hoặc bằng công tắc trong Quản lý lĩnh vực. Câu hỏi tiếp được gửi kèm `context` đúng định dạng khung chat của web (mục 8). |
| `ABI_REMOTE_MAX_PER_5MIN` | 3 | Số câu tối đa hỏi trợ lý web trong 5 phút. Gặp `service_error` thì nghỉ 5 phút. |
| `ABI_SHOW_STAFF_CONTACT` | **tắt** | Cho AI nêu email / điện thoại riêng của cán bộ. Web công khai email của 12/66 cán bộ. |

Biến môi trường `S4_ABI_SYNC=0` tắt lịch tự đồng bộ. Khi không đặt, biến này theo `S4_WARMUP`; các test đặt `S4_WARMUP=0`, nên test không gọi mạng.

## 5. Đo (16/10/2026, `system4/eval/abi/golden.py` — mọi bài kiểm ABI ở `system4/eval/abi/`, xem README trong đó)
**Bộ câu hỏi.** 46 câu do code sinh từ dữ liệu đã đồng bộ, nên đáp án tự đổi theo web. Các câu chia thành 8 nhóm:
- sự kiện (5)
- chi tiết sự kiện (8)
- tổ chức (3)
- từng phòng (17)
- liên hệ (4)
- danh mục (4)
- câu tự do (4)
- ngoài phạm vi (1)

**Cách chấm.** Câu trả lời phải chứa đúng con số, tên, email, ngày hoặc cụm chữ. Chuỗi được so sau khi bỏ dấu.

**Điều kiện chạy.** Model `qwen3:4b-instruct-2507-q4_K_M` qua Ollama, bge-m3 + bge-reranker-v2-m3, máy dev, server thật (`--target web`).

| Hệ thống | Đúng | Ghi chú |
|---|---|---|
| **Lĩnh vực ABI (System 4)** | **46 / 46** | bản cuối (11:42 và 11:45) chạy 2 lần liền đều 46/46 |
| — câu do code trả lời (16) | 16 / 16 | trung vị **0,08 s** |
| — câu do AI trả lời (30) | 30 / 30 | khi model đã nạp: trung vị 5,8 s, p90 7,1 s. Lần chạy ngay sau khởi động server: p90 13,6 s (nạp model) |
| Trợ lý RAG của abi.com.vn (`--target remote`) | 15 / 46 | Hỏi 90 giây / câu (10:52–12:10). Theo nhóm: sự kiện 11/13, tổ chức 0/20, liên hệ 1/4, danh mục 1/4, câu tự do 1/4, ngoài phạm vi 1/1. 18 câu "không tìm thấy", 6 câu hỏi ngược "trung tâm nào?", 1 lỗi mạng. Câu có câu trả lời: trung vị 5,1 s |

Chế độ `--target router` (chỉ code, không AI): 41/41 câu có thẻ hoặc câu trả lời chứa đúng dữ kiện. 5 câu tự do và ngoài phạm vi đi qua bước tìm kiếm.

**Thời gian.** Phần chậm nhất của câu trả lời bằng AI là **lúc AI viết** (khoảng 55 token/giây). Đọc thẻ và tìm kiếm chỉ mất khoảng 0,5–1 giây.
Lời dặn "trả lời đúng trọng tâm" giảm p90 từ 8,1 xuống 7,5 giây mà không giảm độ đúng (lần đo cuối: 7,1 giây).
Mục tiêu p90 ≤ 5 giây trong kế hoạch **chưa đạt** cho câu do AI trả lời; **leader đã chấp nhận khoảng 7,5 giây** (16/10). Câu do code trả lời thì đạt.

## 6. Giới hạn đã biết
- Router dùng luật. Câu có điều kiện mà code chưa hiểu sẽ đi qua AI, và model 4B có thể tự mâu thuẫn khi tự lọc danh sách. Trước khi thêm lọc theo thành phố, câu "sự kiện nào ở Hà Nội" từng bị AI trả lời "có AgroViet" rồi "không có sự kiện nào". Gặp mẫu câu hay hỏi thì thêm vào `router.py` + `tools.py`.
- Bước text-to-SQL trên một bảng rộng (kế hoạch P5) **chưa làm**, vì bộ đo chưa cho thấy cần.
- Chỉ đồng bộ tiếng Việt (`locale=vi`). Bản tiếng Anh của web còn ít, ví dụ chỉ 5/58 chương trình.
- 2/266 tin không có nội dung, chỉ có tóm tắt. Tài liệu đính kèm (PDF, Word; 4 tệp) chỉ được biết tên, chưa đọc nội dung.

## 7. Tệp
`system4/abi/`:
- `client.py`: lớp mạng duy nhất
- `sync.py`: đồng bộ, có dòng lệnh
- `normalize.py`: chuẩn hoá
- `store.py`: lưu dữ liệu
- `index.py`: bộ dữ liệu tìm kiếm
- `router.py`: nhận ý định
- `tools.py`: code tính
- `turn.py`: chat.py gọi vào đây
- `remote.py`: trợ lý web
- `scheduler.py`: lịch + API `/s4/abi/status`, `/s4/abi/sync`

Sửa trong System 4:
- `server/chat.py`: nhánh `abi_mode`, câu trả lời bằng code
- `db.py`: tạo lĩnh vực
- `routes.py`, `domains.py`: cho chat với engine `abi`, chặn tải lên và đổi loại
- `datasets.py`: không xử lý lại bộ tự đồng bộ
- `hook.py`: lịch + router
- `config.py`: 5 cài đặt
- `web/`: tab Quản trị "Dữ liệu ABI"; trong Quản lý lĩnh vực: nhãn, nút "Đồng bộ ngay", công tắc trợ lý web (`app.js` `abiPanel`)

Bài kiểm: thư mục **`system4/eval/abi/`** ([README](../system4/eval/abi/README.md)).
- `test_abi.py`: test tự động, model giả, không gọi mạng. Dùng dữ liệu mẫu `fixtures/abi_raw.json` rút gọn từ API thật; tên cán bộ đã thay bằng tên giả.
- `golden.py`: 46 câu hỏi vàng.
- `saved_results/`: tóm tắt các lần đo.

## 8. Trả lời của chủ web (16/10) và cách xử lý
| Câu hỏi | Trả lời / cách xử lý |
|---|---|
| Hạn mức của `/rag/query` | Chủ web có chỉnh, nhưng **hạn mức vẫn còn**. Kiểm lúc 11:18: 8 câu liên tiếp thì câu thứ 4 bị chặn ("Trợ lý đã chạm hạn mức", vẫn HTTP 201). Hỏi 90 giây một câu thì không bị chặn. Giữ nguyên `ABI_REMOTE_MAX_PER_5MIN = 3` + nghỉ 5 phút khi bị chặn. |
| Khoá API riêng | Không có. |
| Đồng bộ định kỳ từ API công khai | **Đồng ý.** Giữ 6 giờ một lần, chỉ tải phần đổi (28 request). |
| Định dạng `context` (không hỏi, tự xử lý) | Đọc từ mã khung chat của web (`RagConversation-*.js`, hàm `M`): danh sách `{"role": "user" \| "assistant", "content"}` của tối đa 3 lượt hỏi đáp gần nhất, mỗi tin ≤ 2.000 ký tự, tổng ≤ 8.000, bỏ câu chào / câu lỗi. `remote.context()` dựng đúng như vậy. Câu có context không dùng bộ nhớ đệm. |
| Bài "Cơ cấu tổ chức" cũ (không hỏi, tự xử lý) | Loại ở phía mình (mục 3, "Bài bị loại"); kèm trang mẫu "Thông Tin Liên" phát hiện thêm. |
| Webhook / API "đổi từ thời điểm X" (không hỏi, tự xử lý) | Không dùng. Đồng bộ định kỳ chỉ tải lại tin có `updatedAt` đổi, đủ rẻ. Cần ngay thì bấm "Đồng bộ ngay". |

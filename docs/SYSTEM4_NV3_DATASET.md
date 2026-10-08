# System 4 — Nhiệm vụ 3/4: Dataset → Specialist (tải dữ liệu, tự chuyển đổi, tìm kiếm)

Thứ tự: [NV1 Nền tảng](SYSTEM4_NV1_NEN_TANG.md) → [NV2 AI trò chuyện](SYSTEM4_NV2_AI_TRO_CHUYEN.md) → **NV3 (tệp này)** → [NV4 Quản trị](SYSTEM4_NV4_QUAN_TRI.md).
Quy tắc chung (cách nói chuyện, quy trình): xem NV1, mục A1–A3.

---

## Phần A — Yêu cầu gốc (nguyên văn, chỉ thêm tiêu đề)

Dự án Instant Specialist – System 4 build on top System 3 as a parallel:

### A1. AI chung trở thành Specialist

Làm cho tôi 1 web AI đảm bảo các tiêu chí sau:
- 1 web AI General có thể trở thành 1 con Specialist khi nhận được dataset, giống như ChatGPT Web hay Claude Web nhưng chạy trên 1 model nhỏ hơn rất nhiều là Qwen 4B

### A2. Cấu trúc dataset và UI nhập dataset

- Câu hỏi: bạn muốn dùng Dataset structure bất kỳ vs Dataset structure định sẵn cái nào ổn hơn cho 1 con AI nhỏ như thế. Nếu làm Dataset định sẵn thì mình muốn là có 1 UI để nhập dataset bất kỳ + biến dataset bất kỳ thành 1 dataset định sẵn để hệ thống hỗ trợ LLM.

### A3. Quy mô dữ liệu

- Database mình đưa có thể có lên đến vài nghìn records, phải xử lý được vấn đề đó.

### A4. Trade-off đã chọn (nguyên văn câu trả lời, 2026-10-07)

| Câu | Trả lời |
|---|---|
| 3. Khi chưa có dataset | 3A (make a upload file button, and automatically switch if it's has user dataset, also a place to store user's dataset) |
| 4. Nhập dataset | 4A (but I won't confirm the system should figure out if it can map it or option C at worst case) |
| 8. Model trên GPU 6 GB | 8B for friendly mode but it's also toggle-able to see what trade off worth more so build both |
| 10 (phần dung lượng) | Dev has unlimited upload, limit user to 1GB or delete existing please. |

**Trade-off riêng của NV3** (nguyên văn câu trả lời, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 1. Bật nhiều dataset cùng lúc | 1A but make a warning limit so the user don't overflow the system |
| 2. Ai xem được dataset | 2B |
| 3. Không có trong dữ liệu | 3A |
| 4. Nguồn dưới câu trả lời | 4A |
| 5. Reranker mặc định | 5A |
| Duyệt kế hoạch | Approve, but some small change first: Don't use 📎use +, and to clarify futher Admin page and chat GPT features also apply to system 3 as universal. What i meant when said don't touch system 3 is don't mess with the architecture, these are add-ons features so it's fine. |

---

## Phần B — Ý bổ sung của Claude (không phải yêu cầu gốc)

**Trả lời câu hỏi ở A2**: **Dataset định sẵn** tốt hơn cho model nhỏ. Model 4B trả lời tốt hơn hẳn khi dữ liệu đã được chia thành ô rõ ràng (tên, mô tả, các trường, nguồn).

**Nghĩa của các lựa chọn**
- 3A: có nút **Tải file lên** trong khung chat.
  - Khi người dùng có dataset đang bật, AI **tự chuyển** sang Specialist (chỉ trả lời từ dữ liệu). Không có thì về AI chung.
  - Mỗi người dùng có **kho dataset riêng** (xem, bật/tắt, xoá).
- 4A **không cần xác nhận**: hệ thống tự đoán cách khớp cột vào cấu trúc định sẵn (luật + Qwen gợi ý + tự kiểm). Không khớp được thì **tự rơi về phương án C**: lưu nguyên dạng đoạn chữ, vẫn tìm và trả lời được nhưng kém hơn. Màn hình kho dataset ghi rõ file nào đã khớp cấu trúc, file nào đang ở dạng C.
- 8B + toggle: xây **cả hai** đường tìm kiếm: có và không có bước xếp hạng lại (reranker). Toggle trên panel để so sánh. Kèm một bài đo nhỏ để thấy bên nào đáng hơn: độ đúng so với độ chậm.
- Dung lượng: dev không giới hạn. User tối đa **1 GB**; vượt thì chặn tải lên và nhắc xoá dataset cũ.

**Kỹ thuật dự kiến** (chốt ở kế hoạch)
- Loại file: CSV, Excel, JSON, TXT/MD, DOCX, PDF (chỉ lấy chữ, theo 9C).
- Tìm kiếm lai: từ khoá + nghĩa (BGE-M3). Vài nghìn bản ghi là nhẹ, tìm trong < 1 giây.
- Nạp dữ liệu chạy nền, có thanh tiến độ, không làm đứng khung chat. Vài nghìn bản ghi mất khoảng vài phút lần đầu.
- Bộ nhớ GPU 6 GB phải chứa cả Qwen3-4B + BGE-M3 + reranker. Khi chật, reranker sẽ chạy bằng CPU (chậm hơn) thay vì làm sập máy.

**Câu hỏi mở cho bước kế hoạch**
- Một người dùng bật được nhiều dataset cùng lúc, hay chỉ một?
- Dataset của user là riêng tư hoàn toàn, hay có thể chia sẻ cho user khác?
  → đã trả lời: 1A (nhiều bộ, có cảnh báo + giới hạn cứng), 2B (riêng tư, dev mở được nội dung).

---

## Phần C — Báo cáo thực hiện NV3 (2026-10-07)

**Đã làm**

| # | Việc | Người dùng thấy |
|---|---|---|
| 1 | Nút **"+"** cạnh ô nhập (Friendly), kéo thả tệp vào khung chat: CSV, Excel (.xlsx), JSON, TXT/MD, Word (.docx), PDF có chữ | Thanh tiến độ "Đang tải lên… → Đang xử lý… → Đã sẵn sàng" |
| 2 | Tự đổi sang **cấu trúc định sẵn** (bản ghi = tiêu đề + trường + chữ + nguồn): code chọn cột tiêu đề, AI kiểm lại (chế độ JSON, ~1 s), code duyệt; không khớp → dạng dòng chữ (phương án C); văn bản chia đoạn | "Bảng: cột tiêu đề "X" (N trường)" / "Văn bản: N đoạn" |
| 3 | Nạp chạy nền: chỉ mục từ khoá (SQLite FTS5, không phân biệt dấu) + vector bge-m3 trong **Qdrant local mode**; tắt server giữa chừng → khởi động lại tự nạp tiếp | Chat không bị chặn khi nạp |
| 4 | Cửa sổ **"Dữ liệu của tôi"** (nút "Dữ liệu" hoặc nhãn Chuyên gia): bật/tắt, xem bản ghi, xử lý lại, xoá; thanh dung lượng; **cảnh báo** > 5 bộ / > 10.000 bản ghi đang bật, **giới hạn cứng** 20 bộ / 50.000 bản ghi (đổi trong ⚙) | |
| 5 | **Tự chuyển Chuyên gia** khi có bộ dữ liệu đang bật; nhãn "AI chung" / "Chuyên gia · n bộ dữ liệu" | |
| 6 | Trả lời từ dữ liệu: từ khoá + nghĩa (RRF) → **reranker GPU** (bật mặc định, tắt được) → 4 đoạn tốt nhất → AI "chỉ dùng dữ liệu"; số nguồn [n] bấm được + chip nguồn; không có → nói không có + hỏi lại | Nguồn dưới câu trả lời, bấm xem bản ghi gốc |
| 7 | Quyền: user chỉ thấy dữ liệu của mình (1 GB, tệp ≤ 200 MB); dev không giới hạn, mở được dữ liệu mọi người (2B, tab Quản trị) | |

**Đo trên model thật** (`system4/eval/nv3_specialist.py`, kết quả `system4/eval/results/nv3_specialist.json`; dữ liệu: `MAU_100_THU_TUC.xlsx` của V10.3 + một tệp Word tự tạo; câu hỏi sinh tự động từ ô dữ liệu)
- Nạp `MAU_100_THU_TUC.xlsx` (9 trang tính, 2.334 bản ghi): 85–102 s, khớp đúng cột tiêu đề ở mọi trang tính ("name", "tên thủ tục", "tên văn bản"; trang README thành văn bản).
- **Đúng đáp án 17/17, nguồn đúng 17/17** (12 câu cơ quan / thời hạn từ Excel, 3 câu từ Word, 2 câu ngoài dữ liệu → "không có trong dữ liệu").
- Tốc độ (sau khi chỉnh, xem mục 4 dưới): câu ngắn chữ đầu ~2,3 s, cả câu ~4,5 s; câu hỏi chứa tên thủ tục rất dài: chữ đầu trung vị 3,6 s, cả câu trung vị 5,7 s (vượt nhẹ ngân sách 5 s).
- Trình duyệt Edge: "+", tiến độ tải, cửa sổ Dữ liệu, chip nguồn → cửa sổ bản ghi gốc: không lỗi.

**Việc ngoài ý muốn và cách đã xử lý**
1. **Bộ nhớ GPU đổi model qua lại:** nạp bge-m3 làm Ollama gỡ Qwen, nạp lại mất 6,9 s; đổi độ dài ngữ cảnh làm nạp lại 13 s. Khi đã nạp đủ, cả 3 model (Qwen 3,8 GB + bge-m3 0,7 GB + reranker 1,1 GB) ở yên trên GPU. Đã xử lý: **nạp sẵn lúc khởi động** (bge-m3 + reranker) và ghi chú trong ⚙ phải giữ độ dài ngữ cảnh 8192 như System 3.
2. **Bảng thật lộn xộn:** dòng ghi chú trên dòng tiêu đề, trang README một cột, cột mã băm (content_hash) bị chọn làm tiêu đề. Đã thêm luật: bỏ dòng ghi chú, bảng một cột câu dài → văn bản, cột mã/băm/đường dẫn không được làm tiêu đề.
3. CSV có ô rất dài (> 128 KB) làm hỏng việc đọc → đã nâng giới hạn.
4. **Lần đo đầu chậm hơn ngân sách** (cả câu 6,4 s): tìm kiếm tốn 1–1,4 s (reranker chấm 30 đoạn dài) và gửi 5 đoạn × 1.200 ký tự. Đã đổi mặc định: 4 đoạn × 700 ký tự, 15 ứng viên → chữ đầu 2,3 s, cả câu 4,5 s, độ chính xác giữ 17/17 (đổi lại trong ⚙ được).
5. **Vi phạm "không dùng kiến thức chung":** ở một lần đo, tìm không thấy gì mà AI vẫn tự trả lời "Ai là tác giả truyện Kiều?" — và **sai** ("Nguyễn Đình Chiểu"). Đã thêm chốt bằng code: Chuyên gia + không tìm thấy đoạn liên quan + AI viết câu trả lời có nội dung mà không nói "không có trong dữ liệu" → thay bằng câu cố định (sửa được trong ⚙, "Câu trả lời khi dữ liệu không có thông tin"). Câu xã giao ngắn ("dạ, không có gì ạ") không bị thay. Lần đo lại: đúng.
6. Giới hạn chưa làm: PDF ảnh quét (không có chữ) báo lỗi rõ ràng, chưa OCR; Excel cũ .xls chưa hỗ trợ (báo lưu thành .xlsx); hình ảnh trong tệp bị bỏ qua (theo 9C).

**Trade-off sau NV3** (nguyên văn, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 1. Câu hỏi dài vượt 5 s | 1A, it's okay also can you check create new account? |


**Sửa sau báo lỗi của người dùng (2026-10-07): "Ngày sinh của bạn Hiếu" trả lời "không có trong dữ liệu"** (tệp `DS LỚP 1.5.xlsx`)
- Nguyên nhân: dòng 1 của tệp là tên bảng ("DANH SÁCH HỌC SINH LỚP MỘT/ 5 NĂM HỌC: 2025 - 2026") nhưng bị nhận nhầm là dòng tiêu đề cột → tiêu đề thật (STT, Tên, Ngày sinh…) thành một bản ghi, các cột mang tên vô nghĩa ("Cột 5: 17/9/2020"); họ tên lại tách 2 cột ("Danh Minh" | "Hiếu"). Reranker chấm bản ghi của Hiếu −3,14, dưới ngưỡng −3 → bị loại → không có đoạn nào → AI nói đúng là "không có".
- Đã sửa: dòng tiêu đề = dòng đầu có nhãn chữ ngắn phủ ≥ một nửa số cột (bỏ qua dòng tên bảng); cột không nhãn ngay trước cột "Tên" = "Họ và tên đệm", tiêu đề bản ghi = họ tên đầy đủ ghép 2 cột. Điểm reranker sau sửa: +0,30. Dữ liệu đã nạp bằng cách đọc cũ được **tự xử lý lại khi khởi động server** (giữ trạng thái bật/tắt); thêm nút "Xử lý lại" cho bộ dữ liệu đã sẵn sàng.
- Kiểm trên model thật với đúng tệp: "Ngày sinh của bạn Hiếu" → "17/9/2020", nguồn "Danh Minh Hiếu" (cả Nhanh và Suy nghĩ kỹ).
- Còn yếu (chưa sửa): (1) câu hỏi đếm / tổng hợp cả bảng ("lớp có bao nhiêu bạn nữ?" — đúng là 16/33) không làm được vì AI chỉ nhận 4 đoạn tìm được; (2) tên trùng ("bé An": có 2 bạn tên An) — AI trả lời một bạn và bỏ sót bạn kia thay vì hỏi lại. Xem mục D.

**Trả lời tiếp theo** (nguyên văn, 2026-10-07): `1C 2A 3C (document it carefully instead)` — câu 3 = "có sửa hai điểm yếu trên không" → **không sửa, ghi tài liệu kỹ** (mục D dưới). Câu 1–2 thuộc bộ công cụ dev: xem docs/SYSTEM4_NV4_QUAN_TRI.md, phần D.

---

## Phần D — Giới hạn đã biết của chế độ Chuyên gia (ghi theo yêu cầu 3C, 2026-10-07)

Cách đọc mỗi mục: **Hiện tượng** (người dùng thấy gì) · **Vì sao** (cơ chế) · **Nhận ra bằng bộ công cụ dev** · **Cách né cho người dùng** · **Hướng sửa sau này**. Mức độ: Cao = trả lời sai / bỏ sót mà người dùng khó biết; Trung bình = trả lời "không có" dù có; Thấp = chậm hoặc báo lỗi rõ.

### D1. Câu hỏi đếm / tổng hợp trên cả bảng — mức Cao
- **Hiện tượng:** "Lớp có bao nhiêu bạn nữ?", "Có mấy bạn sinh năm 2019?", "Tổng lệ phí các thủ tục là bao nhiêu?", "Liệt kê tất cả học sinh ở Ấp Mỹ Phát". Trả lời "không có dữ liệu", hoặc đếm sai (chỉ đếm trong vài dòng nhìn thấy), hoặc liệt kê thiếu. Ví dụ thật với `DS LỚP 1.5.xlsx`: hỏi số bạn nữ → AI nói không có dữ liệu; đúng là **16/33** (cột "Nữ" có dấu x).
- **Vì sao:** chế độ Chuyên gia là "tìm rồi đọc": mỗi câu chỉ lấy tối đa `RETRIEVAL_TOP_K` (mặc định 4) đoạn liên quan nhất gửi cho AI. AI không bao giờ thấy cả bảng, nên không thể đếm / cộng / lọc toàn bộ. Tăng số đoạn không giải quyết được (bảng vài nghìn dòng không vừa ngữ cảnh 8.192 token, và chậm hơn ngân sách 5 s).
- **Nhận ra:** 🔍 Soi → tab "Tìm kiếm": chỉ vài dòng được gửi (xanh) trong khi câu hỏi cần cả bảng.
- **Cách né cho người dùng:** hỏi theo từng đối tượng ("Ngày sinh của bạn Hiếu", "Mẹ của Đỗ Thị Bảo An tên gì"); hoặc mở "Dữ liệu" → "Xem" để tự tìm / lọc trong danh sách bản ghi.
- **Hướng sửa sau này:** thêm "công cụ bảng": code nhận biết câu hỏi dạng đếm / tổng / lọc / sắp xếp, AI chỉ dịch câu hỏi thành phép lọc trên các trường (vd. `Nữ = x` → đếm), code tính trên toàn bộ bản ghi rồi AI diễn đạt kết quả kèm danh sách nguồn. Cần thêm trường kiểu số / ngày khi đọc tệp. Ước lượng: một nhiệm vụ cỡ vừa.

### D2. Tên (hoặc tiêu đề) trùng nhau — mức Cao
- **Hiện tượng:** "Mẹ của bé An tên gì?" khi lớp có 2 bạn tên An (Đỗ Thị Bảo An, Nguyễn Bình An) và một bạn có chữ "An" trong tên (Nguyễn An Lành). AI trả lời về 1–2 bạn, có lần bỏ sót Đỗ Thị Bảo An, thay vì hỏi "bạn muốn hỏi An nào?".
- **Vì sao:** việc tìm kiếm **đúng** (phòng Thử tìm kiếm cho thấy cả 3 bản ghi được gửi cho AI). Lỗi ở AI: model 4B, chế độ Nhanh (không suy nghĩ), chọn trả lời ngay thay vì nhận ra câu hỏi mơ hồ. Lời dặn hiện có ("chưa đủ rõ thì hỏi lại") không đủ mạnh cho trường hợp này; code chưa có bước kiểm "nhiều bản ghi cùng khớp tên".
- **Nhận ra:** 🔍 Soi → "Tìm kiếm": nhiều dòng xanh có tiêu đề khớp cùng một tên; tab "AI nghĩ gì" → kế hoạch ẩn chỉ nhắc một người.
- **Cách né cho người dùng:** gọi đủ họ tên ("Đỗ Thị Bảo An"); hoặc bật "Suy nghĩ kỹ" / bấm "Kỹ hơn" (chậm hơn, hay nhận ra trùng tên hơn — chưa đo).
- **Hướng sửa sau này:** code đếm các đoạn được gửi có tiêu đề cùng chứa tên được hỏi; ≥ 2 → buộc hỏi lại kèm nút lựa chọn là các họ tên đầy đủ (giống cách Strict mode hỏi lại khi ≥ 3 thủ tục gần nhau).

### D3. Bảng có cấu trúc lạ — mức Trung bình
- **Hiện tượng:** câu hỏi đúng là có trong tệp nhưng AI nói "không có" (như lỗi "ngày sinh của bạn Hiếu" trước khi sửa).
- **Vì sao:** bộ đọc đoán dòng tiêu đề và cột tiêu đề bằng luật. Đã xử lý: dòng tên bảng phía trên, cột họ / tên tách đôi, trang README một cột, cột mã / băm. **Chưa xử lý:** tiêu đề cột hai tầng (gộp ô theo nhóm, vd. "Điểm" trên "Toán | Văn"), bảng nằm ngang (tên trường ở cột đầu), nhiều bảng trong một trang tính, ô gộp dọc.
- **Nhận ra:** "Dữ liệu" → "Cách đọc" (hoặc Quản trị → Dữ liệu người dùng → "Cách đọc"): xem dòng tiêu đề đã chọn, các dòng bị bỏ qua, cột tiêu đề, và đúng đoạn chữ AI thấy. Tên trường kiểu "Cột 5" là dấu hiệu đọc sai.
- **Cách né:** sửa tệp cho một dòng tiêu đề đơn giản ở trên cùng rồi tải lại.
- **Hướng sửa:** nhận tiêu đề nhiều tầng / bảng ngang; cho người dùng chọn lại dòng tiêu đề trong "Cách đọc" (hiện chỉ xem được).

### D4. Các giới hạn khác (mức Thấp)
| Giới hạn | Hiện tượng | Cách né |
|---|---|---|
| PDF ảnh quét | báo "PDF không có chữ" | chuyển sang PDF có chữ / Word |
| Excel cũ `.xls` | báo chưa hỗ trợ | lưu thành `.xlsx` |
| Hình trong tệp | bị bỏ qua (theo 9C) | — |
| Câu hỏi chứa tên rất dài | cả câu ~5,7 s (vượt nhẹ 5 s, đã chấp nhận 1A) | — |
| Câu đầu tiên sau khi bật server | tìm kiếm chậm vài giây vì model đang nạp sẵn | đợi ~30 s sau khi bật |
| Chốt "chỉ trả lời từ dữ liệu" nhận biết câu từ chối qua cụm từ ("không có thông tin", "không tìm thấy"…) | nếu AI từ chối bằng cách nói khác và câu dài > 60 ký tự, câu từ chối đó bị thay bằng câu cố định (vẫn đúng ý) | — |
| Ngưỡng reranker −3 cố định cho mọi loại dữ liệu | dữ liệu viết khác hẳn câu hỏi có thể bị loại | chỉnh "Điểm reranker tối thiểu" trong ⚙; thử trước ở Quản trị → Thử tìm kiếm |

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

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

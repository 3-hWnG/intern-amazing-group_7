# System 4 — Nhiệm vụ 4/4: Quản trị (database thủ tục của Strict mode + người dùng)

Thứ tự: [NV1 Nền tảng](SYSTEM4_NV1_NEN_TANG.md) → [NV2 AI trò chuyện](SYSTEM4_NV2_AI_TRO_CHUYEN.md) → [NV3 Dataset → Specialist](SYSTEM4_NV3_DATASET.md) → **NV4 (tệp này)**.
Quy tắc chung (cách nói chuyện, quy trình): xem NV1, mục A1–A3.

---

## Phần A — Yêu cầu gốc (nguyên văn, chỉ thêm tiêu đề)

Dự án Instant Specialist – System 4 build on top System 3 as a parallel:

### A1. Một web, UI quản trị

Thông tin thêm:
- Mình muốn sản phẩm cuối chỉ có 1 web duy nhất, UI quản lý database thủ tục và quản lý người dùng (database thủ tục này của phần đã built, nhưng chưa có UI nhé, có vẻ chưa có code cào trong file đúng không, copy ở D:\Claude\LLM for Procedures V10.3\Database nha check coi nó có giống nhau không mới copy còn đâu hủy làm trên cái bạn vừa tạo thôi).

### A2. Trade-off đã chọn (nguyên văn câu trả lời, 2026-10-07)

| Câu | Trả lời |
|---|---|
| 7. Người dùng | 7A |
| 10. Database thủ tục | 10A It's for the database for procedures only (strict mode) not other files (your wording worry me) and not only a scrape button but a full on database UI with scrape, version, preview, delete/edit available for dev while the user can only see their uploaded one. Dev has unlimited upload, limit user to 1GB or delete existing please. |

**Trade-off riêng của NV4** (nguyên văn câu trả lời, 2026-10-07):

| Câu | Trả lời |
|---|---|
| 6. "Áp dụng phiên bản" | 6 what do you mean it's shared between system 3 and 4, a tab for the controlled strict mode with strict data standard (system 3) and 1 tab is to admin the user datasets. Maybe A for this question |
| 7. Sửa / xoá thủ tục | 7A |
| 8. Cào dữ liệu | 8A |
| 9. Quản lý người dùng | 9A |
| Duyệt kế hoạch | Approve, but some small change first: Don't use 📎use +, and to clarify futher Admin page and chat GPT features also apply to system 3 as universal. What i meant when said don't touch system 3 is don't mess with the architecture, these are add-ons features so it's fine. |
| 1. Tính năng ChatGPT cho Strict | 1A now do it |

**Kết quả kiểm tra (2026-10-07):** dữ liệu `D:\Claude\LLM for Procedures V10.3\Database\staging\procedures.jsonl` **giống hệt** `data/snapshot/procedures.jsonl` (1.350 bản ghi, mọi trường bằng nhau, schema giống nhau) → không chép dữ liệu, chỉ đưa code cào (`pipeline/`) sang thư mục System 4.

---

## Phần B — Ý bổ sung của Claude (không phải yêu cầu gốc)

**Phạm vi (làm rõ theo câu 10)**: UI này chỉ dành cho **database thủ tục của Strict mode (System 3)**. Dataset người dùng tải lên ở Friendly mode là chuyện riêng của NV3 và không trộn vào đây.

**Hiện trạng đã kiểm (2026-10-07)**
- Dữ liệu System 3 đang dùng (`data/snapshot/procedures.jsonl`, 1.350 thủ tục) được chép từ repo **V10.6** (`D:\Finale_architect\repo\Database\`), **không phải V10.3**.
- Đúng là System 3 **chưa có code cào**. Thư mục V10.3 `Database\pipeline` có code cào (`client.py`, `fetch_catalog.py`, `fetch_details.py`, `run_pipeline.py`...).
- Theo yêu cầu A1: so sánh dữ liệu và code V10.3 với bản hiện tại trước. Giống thì không chép. Khác thì chép phần cần.

**Phân quyền**

| Việc | dev | user |
|---|---|---|
| Cào dữ liệu mới từ cổng | ✅ | ❌ |
| Xem các phiên bản, xem trước, so sánh | ✅ | ❌ |
| Sửa / xoá thủ tục, khôi phục phiên bản cũ | ✅ | ❌ |
| Quản lý người dùng (tạo, khoá, đổi vai trò, đặt lại mật khẩu) | ✅ | ❌ |
| Xem dataset của chính mình | ✅ | ✅ (chỉ của mình) |
| Dung lượng tải lên | không giới hạn | 1 GB |

**Cách giữ an toàn cho System 3** (dự kiến)
- Bản dữ liệu hiện tại được giữ làm **phiên bản 0**, không bao giờ bị ghi đè.
- Mỗi lần cào/sửa/xoá tạo một **phiên bản mới**. Phải bấm "Áp dụng" thì System 3 mới dùng bản đó, qua đúng lệnh build có sẵn (`system3.data.build`). Code System 3 không đổi.
- Lỗi thì quay lại phiên bản trước bằng một nút bấm.

**Lưu ý**
- Cào dữ liệu **cần internet**. Đây là ngoại lệ duy nhất với "Chạy Local 100%": nút cào chỉ chạy khi có mạng, mọi phần khác vẫn chạy offline.
- Sau khi áp dụng phiên bản mới nên chạy lại bộ test của System 3 để biết điểm có tụt không. Có thể đặt thành bước tự động.

**Câu hỏi mở cho bước kế hoạch**
- Dev có được xem nội dung dataset của user không, hay chỉ thấy tên và dung lượng?
  → đã trả lời: 2B (dev mở được nội dung).

---

## Phần C — Báo cáo thực hiện NV4 (2026-10-07)

**Đã làm** — trang **Quản trị** (`/s4/admin`, nút "Quản trị" trên thanh trên, chỉ dev), 3 tab:

| Tab | Có gì |
|---|---|
| **Dữ liệu Strict (thủ tục)** | Phiên bản (Gốc = bản chép của `data/snapshot/procedures.jsonl`, luôn giữ), xem / tìm thủ tục theo phiên bản, sửa / xoá vào **bản nháp** (kiểm **chuẩn dữ liệu**: đúng các trường và kiểu như dữ liệu gốc, không đổi mã), **so sánh** (mới / không còn / thay đổi, xem từng trường cũ → mới), **Lưu thành phiên bản**, **Áp dụng** (Strict mode chuyển sang ngay), quay lại bản cũ = áp dụng bản cũ, **Cào dữ liệu mới** (chạy nền, có tiến độ, nhật ký; xong thành phiên bản mới, KHÔNG tự áp dụng) |
| **Dữ liệu người dùng** | Mọi bộ dữ liệu: chủ, loại, bản ghi, dung lượng, trạng thái; mở xem nội dung (2B); xoá |
| **Người dùng** | Tạo, đổi vai trò, khoá / mở khoá (khoá = đăng xuất ngay), đặt lại mật khẩu, xoá (kèm hội thoại, dữ liệu, bộ nhớ); không tự hạ quyền / tự xoá; luôn còn ít nhất một dev |

**Tính năng kiểu ChatGPT cho Strict (1A):** sao chép, tạo lại, sửa tin đã gửi, ‹ 1/2 ›, 👍/👎, Dừng, xuất theo nhánh đang xem. Câu trả lời vẫn do System 3 tạo (gọi đúng API `/chat` của System 3). Sửa / tạo lại = hội thoại System 3 mới (nhánh, ẩn khỏi danh sách) + **phát lại** các câu trước (kể cả lựa chọn đã bấm ở thẻ hỏi lại và lệnh "chủ đề mới"). Hội thoại Strict cũ được dựng cây khi mở lần đầu.

**Cài đặt:** `Set up first time.bat` sau bước dựng DB chạy thêm `python -m system3.system4.server.procs reapply` → nếu đang dùng phiên bản khác Gốc thì dựng lại theo phiên bản đó (không âm thầm quay về Gốc).

**Kiểm tra**
- `system4/tests/test_nv4.py` qua: quyền dev, quản lý người dùng, nháp + chuẩn dữ liệu (thiếu trường / sai kiểu / đổi mã bị chặn), so sánh, **Áp dụng thật** (dựng bằng `system3.data.build` trên **bản sao** DB: 1.350 → 1.349 thủ tục, tên đã sửa có trong DB, Planner System 3 dùng dữ liệu mới) rồi quay lại Gốc, cào (giả lập tiến trình, không mạng), phiên bản Strict (tạo lại, sửa, chuyển, chủ đề mới, thẻ hỏi lại + phát lại, xoá kèm nhánh), xoá người dùng kéo theo dữ liệu.
- Toàn bộ test System 3 (7 bộ + selftest eval + test_data) vẫn qua. DB thủ tục thật không bị đụng (test dùng bản sao).
- Trình cào chạy thật với **3 thủ tục** (83 KB) qua API dichvucong.gov.vn: lấy danh mục, chi tiết, chuẩn hoá đều được.
- Trình duyệt Edge: Strict có nút sao chép / tạo lại / 👍👎, tạo lại → ‹ 2/2 ›; trang Quản trị 3 tab, cửa sổ sửa thủ tục 47 trường: không lỗi.

**Việc ngoài ý muốn và cách đã xử lý**
1. **Planner của System 3 giữ một kết nối DB mở suốt đời tiến trình và một chỉ mục tên thủ tục trong bộ nhớ** (`server/planner/planner.py`: `_conn`, `_idx`). Hệ quả: không thay được tệp DB khi server đang chạy (Windows khoá; Linux thì Planner vẫn đọc tệp cũ), và kể cả DB mới thì Planner vẫn chọn thủ tục theo danh sách cũ. Đã xử lý **không sửa code System 3**: (a) chép DB mới **vào chính tệp đang dùng** bằng SQLite backup; (b) sau khi áp dụng, đặt lại biến đệm `_idx` của Planner từ bên ngoài để lượt sau dựng lại chỉ mục. Lưu ý: nếu sau này System 3 đổi tên biến này, bước (b) sẽ không còn tác dụng (Planner dùng danh sách cũ tới khi khởi động lại server) — test NV4 sẽ báo.
2. **Chưa chạy cào toàn bộ** (~1.350 thủ tục, ước ~35 MB tải về) vì người dùng đang hết dung lượng mạng; chỉ thử 3 thủ tục. Chưa bấm "Áp dụng" trên DB thật của người dùng — chỉ trên bản sao.
3. Strict không trả lời theo luồng như Friendly: nút **Dừng** chỉ dừng chờ; System 3 vẫn trả lời ở nền và câu trả lời hiện khi mở lại hội thoại.
4. Phát lại khi sửa / tạo lại: mỗi câu phát lại mất vài ms (bước AI của System 3 tắt) tới ~5 s (bật) — đúng như đã báo ở câu 1A.

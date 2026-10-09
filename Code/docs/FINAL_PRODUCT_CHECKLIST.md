# Danh sách "đừng quên cho bản cuối" (Phase 25)

**Giả định hiện tại: mọi thứ đang chạy là chế độ nhà phát triển (developer mode).** Chưa có người dùng thật, chưa có đăng nhập. Những điều dưới đây là các chỗ hệ thống hôm nay **chưa an toàn cho người dùng thường**. Chưa build (quyết định của nhóm, 2026-10-07: làm bản đầy đủ trước); chỉ ghi để không rơi mất.

Cách tìm chỗ trong code: `grep -rn "FINAL-PRODUCT:" .` (mỗi thẻ ghi mã mục `[B2]`, `[B3]`, `[B4]`, `[AI]`, `[MEM]` và số mục của file này). `python eval/check_docs.py` bắt khi một file có thẻ mà không được nhắc ở đây.

Chế độ người dùng = chế độ nhà phát triển với **ít quyền và ít thông tin hơn**. Mọi mục dưới đây là việc phải làm trước khi cho người ngoài nhóm dùng.

## 1. Tách chế độ người dùng và nhà phát triển (B2)
Hiện tại: `S3_DEV=0` mặc định, nhưng việc chặn mới nằm ở vài chỗ (`/chat` khối `dev`, `POST /config`, `/dev/*`); các chỗ còn lại để mở.

| Chỗ | Tình trạng hôm nay | Bản cuối |
|---|---|---|
| `server/main.py` `GET /conversations/{id}/messages` | trả `plan` của từng tin trợ lý, không kiểm dev | bỏ `plan` khi không dev |
| `server/main.py` `GET /conversations/{id}/messages/{mid}/trace` | trả trace, không kiểm dev, không kiểm chủ hộp thoại | chỉ dev (403/404 với người thường) |
| `server/main.py` `GET /config` | ai cũng đọc được mode, model, timeout, ngưỡng, model đã nạp | người thường chỉ thấy "AI bật/tắt" |
| `server/main.py` `POST /config` | chỉ chặn bằng `S3_DEV=1`; không có vai trò admin | vai trò admin do server cấp, hoặc bỏ |
| `server/main.py` `/dev/*`, khối `dev` trong `/chat` | chặn bằng `DEV_MODE` toàn cục (cả tiến trình) | chặn theo vai trò của người gọi |
| `web/static/js/chat.js` `?dev=1` | cờ phía trình duyệt, ai gõ URL cũng bật được khung plan/trace | dev theo vai trò server cấp, không theo URL |
| `server/db/store.py` `get_messages`, `add_trace` | trả/lưu plan và trace | chỉ dev được đọc; đặt hạn xoá trace |

Việc cần làm: một khái niệm vai trò (`user` | `dev`) do server quyết (đăng nhập hoặc khóa dev), dùng chung cho mọi endpoint trên; test API cho từng endpoint với vai trò người thường (phải bị chặn).

## 2. Che CCCD/SĐT trong dữ liệu lưu (B3)
Hiện tại: `policy.mask_pii` che CCCD/CMND/SĐT **chỉ trong `trace["question"]`**. Những chỗ sau lưu nguyên văn:

| Chỗ | Chứa gì |
|---|---|
| `messages.content` (user) | nguyên văn người dùng gõ (`server/main.py` `/chat`, `store.add_message`) |
| `messages.plan_json` | plan của lượt (có thể mang đoạn câu hỏi) |
| `conversations.title` | 60 ký tự đầu của câu đầu tiên (`store.set_title_if_new`) |
| `session_facts.text` | lời người dùng kể về hoàn cảnh (`store.add_fact`) |
| `turn_traces.trace_json` | trace (câu hỏi đã che; các phần khác chưa rà) |
| xuất hộp thoại (`conv_export`) | đi theo `messages.content` |

Việc cần làm: che trước khi ghi (gọi `mask_pii` ở một cửa duy nhất trong `store`), rà thêm CCCD 9/12 số, SĐT +84/0x, email, họ tên khi người dùng nêu; test có số giả (không dùng dữ liệu thật). Quyết định còn mở: giữ bản gốc có mã hoá và hạn dùng hay chỉ giữ bản đã che.

## 3. Phiên và quyền sở hữu hộp thoại (B4)
Hiện tại: phiên ẩn danh, `conversation_id` do trình duyệt giữ ở `localStorage`; `conversations` không có cột chủ sở hữu; mọi người cùng một DB.

- `GET /conversations` liệt kê **mọi** hộp thoại trong DB.
- Nút "Xóa tất cả" gọi `DELETE /conversations` = `DELETE FROM conversations` **của mọi người**.
- Biết `conversation_id` là đọc, sửa, xoá, xuất được (không kiểm chủ).

Việc cần làm: thêm `user_id` (hoặc id phiên có chữ ký) vào `conversations`, lọc mọi truy vấn theo người gọi, "Xóa tất cả" chỉ xóa của người đó, ID hộp thoại không đoán được và có kiểm chủ ở mọi endpoint; test hai người dùng không thấy hộp thoại của nhau. Phase 26 (bộ nhớ người dùng) lưu theo phiên và để chỗ cho tài khoản, cũng gắn thẻ ở đây.

## 4. Công tắc AI cho người dùng thường (AI)
Hiện tại: `S3_USE_LLM` (bước sinh chữ) là **biến môi trường của tiến trình**; `POST /config {answer_llm}` đổi nó cho **tất cả** người dùng; UI hiện nút "AI: bật/tắt" cho mọi người (chỉ xem nếu không dev). Nhóm đã quyết (2026-10-07): **bật mặc định, giữ công tắc**.

Cần nhóm chọn trước bản cuối: người dùng thường có được tắt AI không? Nếu có, phải là tuỳ chọn **theo người dùng** (không đổi biến của tiến trình); nếu không, ẩn công tắc và chỉ giữ chỉ báo. Timeout AI (`ANSWER_LLM_TIMEOUT`, `PLANNER_LLM_TIMEOUT`, mặc định 7 s) là cấu hình vận hành, không để người thường đổi.

## 5. Điều kiện chạy chung cho bản cuối (nhắc, không có thẻ trong code)
- Nhiều worker: công tắc AI và `POST /config` là trạng thái tiến trình, sẽ không đồng bộ giữa các worker.
- `Cache-Control: no-cache` cho static là mặc định cho bản dev (`server/main.py`, `ponytail:`); thêm hash tên file khi lên production.
- Không đưa dữ liệu cá nhân thật vào bộ test hay log.

## 6. Bộ nhớ người dùng gắn tài khoản (Phase 26, MEM)
Hiện tại: hồ sơ nhẹ (tỉnh, xã/phường, loại người dùng, ghi chú) và lựa chọn MCQ đã nhớ (`subject`) lưu theo **`client_id` do trình duyệt tự sinh** (UUID ở `localStorage`, gửi qua header `X-Client-Id`; thiếu thì 'default'), bảng `user_memory(client_id, key, value, updated_at)`. Không có xác thực.

| Chỗ | Tình trạng hôm nay | Bản cuối |
|---|---|---|
| `server/user_memory.py`, `server/main.py` `/memory*` | tin `X-Client-Id` tự khai: ai biết hoặc đoán được id là đọc, sửa, xoá được hồ sơ người khác; thiếu header thì dùng chung 'default' (mọi người không có id chung một hồ sơ) | lấy người dùng từ phiên đăng nhập; bỏ 'default' (không đăng nhập thì không lưu, chỉ giữ trong phiên) |
| `server/db/schema.sql` `user_memory` | cột `client_id` | đổi thành `user_id` (di chuyển dữ liệu: gộp theo tài khoản khi người dùng đăng nhập lần đầu); đặt hạn xoá |
| `web/static/js/chat.js` `CLIENT` | UUID tự sinh, mất khi xoá dữ liệu trình duyệt; đổi trình duyệt/máy là mất hồ sơ | hồ sơ theo tài khoản, đồng bộ giữa thiết bị |
| `server/user_memory.py` `PROVINCES` | danh sách 63 tỉnh trước sáp nhập 01/07/2025, chỉ để hiển thị (không lọc) | danh mục 34 tỉnh/thành hiện hành và xã/phường; nếu muốn lọc theo địa phương thì dữ liệu thủ tục phải có chiều tỉnh |

Việc cần làm cùng lúc với mục 3 (quyền sở hữu): test hai tài khoản không thấy hồ sơ của nhau; "Quên tất cả" chỉ xoá của tài khoản đó; không ghi CCCD/SĐT (đã từ chối ở API, giữ khi chuyển sang tài khoản).

## Các file mang thẻ `FINAL-PRODUCT:`
`server/config.py`, `server/main.py`, `server/orchestrator.py`, `server/user_memory.py`, `server/db/store.py`, `server/db/schema.sql`, `server/policy/policy.py`, `web/static/js/chat.js`.

# Chế độ khách và giới hạn lượt hỏi (20/10/2026)

Code: `system4/server/guest.py`, `system4/server/ratelimit.py`. Test: `python run_server.py system4/tests/guest_limit_test.py`.

## 1. Khách (không đăng nhập)

- Trang đăng nhập có nút **"Dùng thử không cần đăng nhập"**. Bật/tắt ở ⚙ Cài đặt → "Giới hạn sử dụng" → `GUEST_ENABLED`.
  Máy mới chưa có tài khoản nào thì không hiện nút (tài khoản đầu tiên phải là dev).
- **Thông tin khách chỉ nằm trong cookie** `s4_guest` = mã khách ngẫu nhiên + lúc tạo + chữ ký HMAC. Không có dòng nào trong
  `users`, `sessions`, cũng không có hội thoại nào trong `system4.db` hay `system3.db`.
- Hội thoại của khách (cả Thủ tục/System 3 lẫn các lĩnh vực Friendly) chạy đúng pipeline như tài khoản thường, chỉ khác chỗ lưu:
  trong lượt của khách, các bảng hội thoại được chuyển sang một SQLite **trong RAM**. Bị xoá sau **24 giờ** hoặc khi tắt server.
  Khoá ký cookie sinh mới mỗi lần khởi động, nên tắt server thì cookie khách cũ cũng hết hiệu lực.
- Khách được: hỏi, sửa tin, tạo lại, xem/đổi tên/ghim/xoá/xuất hội thoại của mình, xem nguồn trích dẫn, "Vì sao?".
  Khách **không** được: tải dữ liệu, 👍/👎, bộ nhớ, tài khoản, bảng điều khiển lĩnh vực, cài đặt, quản trị (API trả 403).
- Đăng nhập / đăng ký xong thì cookie khách bị xoá. Hội thoại lúc làm khách **không** chuyển sang tài khoản.

## 2. Giới hạn theo vai trò

Một **câu hỏi** = một lần gửi cho AI hoặc System 3: tin mới, sửa tin, tạo lại (Strict phát lại nhiều câu bên trong vẫn tính 1).

| Vai trò    | Câu / phút | Câu / ngày | Đang trả lời cùng lúc | Độ dài 1 câu | Mọi yêu cầu API / phút |
|------------|-----------:|-----------:|----------------------:|-------------:|-----------------------:|
| Khách      | 3          | 20         | 1                     | 1.000 ký tự  | 60                     |
| Người dân  | 10         | 200        | 1                     | 4.000 ký tự  | 300                    |
| Cán bộ     | 30         | 2.000      | 3                     | 16.000 ký tự | 1.200                  |
| Dev        | 60         | 10.000     | 5                     | 16.000 ký tự | 3.000                  |

Thêm cho khách: một **IP** tối đa gấp 5 lần một khách (15 câu/phút, 100 câu/ngày), và tối đa **20 phiên khách mới / IP / giờ**.
"Ngày" tính theo lịch, làm mới lúc 0 giờ. Hai cột đầu chỉnh ở ⚙ Cài đặt (`LIMIT_*`); các cột còn lại là hằng số trong `ratelimit.py`.

### Vì sao chọn các con số này

- **Máy chỉ có một GPU, trả lời từng câu một.** Model 4B mất khoảng 1–3 giây/câu khi có GPU, 7–40 giây khi chạy CPU, nên cả
  máy phục vụ được khoảng 20–40 câu/phút. Hàng chờ GPU có `FRIENDLY_QUEUE_MAX` = 20 chỗ cho tất cả mọi người.
- **Cột "đang trả lời cùng lúc" là chỗ chặn chính để một người không làm sập server.** Không có nó, một người mở 20 tab
  (hoặc viết script gửi song song) là chiếm hết 20 chỗ, mọi người khác nhận "Hệ thống đang bận". Có nó, khách và người dân
  chỉ giữ được 1 chỗ mỗi người, cán bộ 3, dev 5.
- **Khách 3 câu/phút, 20 câu/ngày:** khách ẩn danh, lạm dụng không mất gì, nên chặt nhất. Người thật đọc một câu trả lời ít nhất
  15–20 giây, nên 3 câu/phút không cản người dùng thật. 20 câu đủ thử 3–5 cuộc trò chuyện, rồi mời đăng ký (miễn phí).
- **Người dân 10 câu/phút, 200 câu/ngày:** 10 câu/phút là nhanh hơn tốc độ gõ của người thật. Người dùng nhiều một ngày khoảng
  50–100 câu, 200 là dư; một tài khoản bị dùng làm script thì cũng chỉ lấy được 200 lượt GPU mỗi ngày.
- **Cán bộ 30/2.000, dev 60/10.000:** "rất thoải mái": cán bộ thử nhiều câu suốt ngày làm việc, dev test liên tục. Vẫn có trần
  để một tài khoản bị lộ mật khẩu hay script lỗi chạy vòng lặp không chiếm cả máy.
- **Độ dài câu:** ngữ cảnh model 8.192 token (`FRIENDLY_NUM_CTX`); 1.000 ký tự (khách) và 4.000 (người dân) đủ cho câu hỏi thật,
  chặn kiểu dán cả tài liệu vào để làm chậm máy.
- **Giới hạn theo IP của khách:** xoá cookie là có mã khách mới, nên cần đếm thêm theo IP. Lấy gấp 5 lần vì cả nhà / cả phòng
  có thể dùng chung một IP.

## 3. Ghi chú vận hành

- Bộ đếm nằm trong RAM của tiến trình (không ghi DB): khởi động lại server thì đếm lại từ 0.
- Chạy sau nginx thì để nginx gửi `X-Forwarded-For`. Uvicorn mặc định tin header này khi proxy ở `127.0.0.1`, nếu không thì mọi
  khách sẽ chung một IP và hết 100 câu/ngày rất nhanh.
- Test (`S4_WARMUP=0`) tự tắt giới hạn; `bench.py` và `load_test.py` đặt `S4_RATE_LIMIT=0`. Muốn bật riêng: `S4_RATE_LIMIT=1`.
- Quá giới hạn thì API trả **429** (hoặc **413** khi câu quá dài) kèm câu báo tiếng Việt và header `Retry-After`. Giao diện hiện
  câu báo đó; khách luôn thấy dòng "còn N/20 câu hỏi hôm nay", tài khoản chỉ thấy khi còn ≤ 10 câu.

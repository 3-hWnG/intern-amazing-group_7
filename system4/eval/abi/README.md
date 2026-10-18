# Bộ test lĩnh vực ABI (abi.com.vn)

Mọi bài kiểm cho lĩnh vực ABI nằm trong thư mục này. Cách hoạt động của lĩnh vực: [docs/SYSTEM4_ABI.md](../../../docs/SYSTEM4_ABI.md).

⛔ **Không bài kiểm nào được gọi trợ lý AI của web (`/rag/...`)**, vì tốn token (tiền) của chủ web; leader cấm từ 17/10/2026.
- `test_abi.py` chạy trên API **giả** ngay trên máy và báo lỗi nếu có ai gọi `/rag`.
- `golden.py` chỉ chấm hệ thống của mình.

| Tệp | Là gì | Chạy (từ thư mục gốc repo) |
|---|---|---|
| `test_abi.py` | Test tự động: model giả, API giả, không gọi mạng, không cần Ollama, khoảng 30 giây. Kiểm các phần ở danh sách dưới bảng | `python run_server.py system4/eval/abi/test_abi.py` |
| `fixtures/abi_raw.json` | Dữ liệu cho `test_abi.py`: bản rút gọn của API thật ngày 16/10/2026. **Tên cán bộ là tên giả**, đã bỏ email và điện thoại cá nhân. Test tự dựng bản "staging" từ tệp này (bớt một phòng, tên "Trung tâm AAAA") | — |
| `golden.py` | Bộ câu hỏi vàng: **46 câu do code sinh từ phiên bản dữ liệu đang dùng**, nên đáp án tự đổi theo web. Chấm bằng cách so con số, tên, email, ngày, cụm chữ, sau khi bỏ dấu | xem bên dưới |
| `results/` | Kết quả thô của `golden.py`. **Không đưa lên git** vì có tên cán bộ thật | — |
| `saved_results/` | Bản tóm tắt các lần đo: chỉ có điểm và thời gian, không có tên người | — |

`test_abi.py` kiểm các phần:
- **Lớp mạng:**
  - chặn `/rag` và chỉ gọi được GET;
  - khoá API: thiếu khoá thì báo 401 kèm chỗ điền; gửi khoá bằng `Authorization: Bearer`;
  - khoá không lộ ra giao diện và không bao giờ bị ghi vào `config.py`;
  - User-Agent định danh; gọi đúng dạng endpoint chính thức;
  - tối đa 2 request/giây; bỏ email / SĐT riêng của cán bộ.
- **Phiên bản:**
  - lần đầu tạo phiên bản 1; dữ liệu không đổi thì không tạo phiên bản mới; dữ liệu đổi thì có phiên bản mới;
  - giữ 2 bản mỗi nguồn và tự xoá bản cũ; bản đang dùng đi theo bản mới nhất;
  - dev chọn bản cũ hơn thì giữ nguyên; bản đang dùng bị xoá thì chuyển sang bản mới nhất;
  - staging có link riêng; không xoá được bản đang dùng; API hỏng thì không tạo phiên bản;
  - chuyển bố cục cũ thành phiên bản 1.
- **Chỉ mục:** mỗi phiên bản một bộ, dùng lại vector; không bật hay xoá thẳng được bộ dữ liệu ABI.
- **Lịch:** chỉ abi.com.vn tự đồng bộ, tối thiểu 6 giờ; nút đồng bộ nghỉ 10 phút.
- **Router và code tính:** 2 câu mẫu và các cách hỏi khác.
- **Nối vào chat:** chuyển qua lại giữa bản thật và staging; quyền dev / người dùng.

## Chạy bộ câu hỏi vàng
```bat
:: 1. cần dữ liệu đã đồng bộ (cần khoá API: set ABI_API_KEY=... hoặc ô Khoá API trong ⚙ của web):
python run_server.py -m system3.system4.abi.sync --source prod
:: 2. chọn đối tượng chấm (chấm trên phiên bản ĐANG DÙNG)
python run_server.py -m system3.system4.eval.abi.golden --target router        :: chỉ code (router + tools), vài giây
python run_server.py -m system3.system4.eval.abi.golden --target web --base http://127.0.0.1:8300 --user <dev> --password <mật khẩu>
python run_server.py -m system3.system4.eval.abi.golden --dump                  :: chỉ ghi bộ câu hỏi + đáp án ra results/
```
- `--target web`: hỏi qua web thật (server đang chạy, model trên máy). Thời gian đo tới lúc câu trả lời hiện xong.
- `--only su_kien,to_chuc`: chỉ chạy một số nhóm.

## Các nhóm câu hỏi (46 câu)
| Nhóm | Số câu | Ví dụ | Đáp án lấy từ |
|---|---|---|---|
| `su_kien` | 5 | "Các sự kiện sắp diễn ra" (**câu mẫu 1**), số sự kiện sắp tới, sự kiện đã qua, sự kiện theo tháng, sự kiện ở Hà Nội | `/events`, tính theo giờ VN lúc chạy |
| `su_kien_chi_tiet` | 8 | "<tên sự kiện> bắt đầu ngày nào?", "… tổ chức ở đâu?" (4 sự kiện sắp tới) | `/events` |
| `to_chuc` | 3 | "Có bao nhiêu phòng ban" (**câu mẫu 2**), số cán bộ, Giám đốc | `/organization` |
| `to_chuc_phong` | 17 | trưởng phòng, số người, email của từng phòng | `/organization` |
| `lien_he` | 4 | hotline, địa chỉ, giờ làm việc, email | `/site/settings` |
| `danh_muc` | 4 | số doanh nghiệp ươm tạo, sản phẩm, dịch vụ, chương trình | `/catalog`, `/programs` |
| `tu_do` | 4 | năm thành lập, cơ quan chủ quản, quy trình ươm tạo, Nghị quyết 64/2026 | trang giới thiệu, chương trình |
| `ngoai_pham_vi` | 1 | "Thời tiết hôm nay thế nào?" (phải từ chối) | — |

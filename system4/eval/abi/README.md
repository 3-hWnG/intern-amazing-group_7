# Bộ test lĩnh vực ABI (abi.com.vn)

Mọi bài kiểm cho lĩnh vực ABI nằm trong thư mục này. Cách hoạt động của lĩnh vực: [docs/SYSTEM4_ABI.md](../../../docs/SYSTEM4_ABI.md).

| Tệp | Là gì | Chạy (từ thư mục gốc repo) |
|---|---|---|
| `test_abi.py` | Test tự động, dùng model giả, không gọi mạng, không cần Ollama, khoảng 30 giây. Kiểm các phần: chuẩn hoá dữ liệu; router + code tính (2 câu mẫu và các cách hỏi khác); đồng bộ qua API giả (tải lại phần đổi, API hỏng thì giữ bản cũ); lịch đồng bộ; trợ lý web (hạn mức, `context`, bỏ câu dẫn bài cũ); loại bài cũ / trang mẫu khỏi chỉ mục; nối vào chat; nút "Đồng bộ ngay"; công tắc trợ lý web; quyền dev / người dùng | `python run_server.py system4/eval/abi/test_abi.py` |
| `fixtures/abi_raw.json` | Dữ liệu cho `test_abi.py`: bản rút gọn của API thật ngày 16/10/2026. **Tên cán bộ là tên giả**, đã bỏ email và điện thoại cá nhân | — |
| `golden.py` | Bộ câu hỏi vàng: **46 câu do code sinh từ dữ liệu đã đồng bộ**, nên đáp án tự đổi theo web (sự kiện mới, cán bộ đổi…). Chấm bằng cách so con số, tên, email, ngày, cụm chữ, sau khi bỏ dấu | xem bên dưới |
| `results/` | Kết quả thô của `golden.py`. **Không đưa lên git** vì có tên cán bộ thật | — |
| `saved_results/` | Bản tóm tắt các lần đo, chỉ có điểm và thời gian, không có tên người | — |

## Chạy bộ câu hỏi vàng
```bat
:: 1. cần dữ liệu đã đồng bộ (server tự làm; hoặc bấm "Đồng bộ ngay"; hoặc chạy tay):
python run_server.py -m system3.system4.abi.sync
:: 2. chọn đối tượng chấm
python run_server.py -m system3.system4.eval.abi.golden --target router        :: chỉ code (router + tools), vài giây
python run_server.py -m system3.system4.eval.abi.golden --target web --base http://127.0.0.1:8300 --user <dev> --password <mật khẩu>
python run_server.py -m system3.system4.eval.abi.golden --target remote --gap 90 :: trợ lý RAG của abi.com.vn (mốc so sánh, ~70 phút)
python run_server.py -m system3.system4.eval.abi.golden --dump                  :: chỉ ghi bộ câu hỏi + đáp án ra results/
```
- `--target web`: hỏi qua web thật (server đang chạy, model thật). Thời gian đo tới lúc câu trả lời hiện xong.
- `--target remote`: hỏi chậm (mặc định 90 giây / câu) vì trợ lý của web chỉ cho khoảng 3 câu liên tiếp. Gặp báo hạn mức thì chờ 5 phút rồi hỏi lại.
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

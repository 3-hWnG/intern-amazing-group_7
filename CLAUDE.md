# Quy tắc bắt buộc cho dự án System 3 + 4 (chép từ JD_BAI_BAO_2_SYSTEM4_2026-10-25.docx, mục 4)

Áp dụng cho toàn repo, mọi nhánh. Đọc trước khi sửa bất cứ gì liên quan tới System 4 / bài báo 2.

- **Không bao giờ gọi trợ lý AI của abi.com.vn** (/rag) hay thứ gì tốn token của chủ trang, kể cả để thử. Khoá API ABI chỉ nằm trong cài đặt lúc chạy, không đưa vào git, tài liệu, log.

- **Khoá bộ mù trước khi sửa code; đóng băng code trước khi đo; mỗi cấu hình một lần; mở kết quả một lần.** Không sửa đáp án theo kết quả hệ thống. Cần sửa thì làm bộ mới.

- **Chọn cấu hình chỉ trên dev**, theo tiêu chí viết trước. Báo mọi cấu hình đã chạy, kể cả cấu hình thua.

- **Bài 2 không dùng lại số của bài 1** (System 3, real_v2) và ngược lại: hai bài phải có đóng góp và số liệu riêng.

- Không đưa dữ liệu không rõ giấy phép, tên thật, SĐT, CCCD vào repo hay vào bài.

- Không tải model mới hay bộ dữ liệu lớn khi chưa hỏi trưởng nhóm (hạn chế dung lượng mạng).

- **Máy không quá 70 °C.** Không đổi thiết lập nguồn hay công suất của máy khi chưa được phép.

- **Git:** commit ở máy; chỉ push khi trưởng nhóm đồng ý; không viết lại lịch sử khi chưa hỏi; không commit tệp người khác đang sửa dở.

- Chạy test đơn vị với TMP / TEMP trỏ sang ổ còn chỗ: mỗi test để lại khoảng 45 MB tệp tạm.

- Viết tài liệu và trả lời bằng tiếng Việt; bản nháp bài báo bằng tiếng Anh.

## Hỏi trưởng nhóm trước khi

- Push lên GitHub, hay viết lại lịch sử git.
- Tải bộ dữ liệu hay model mới; dùng dữ liệu của công ty (ABI) trong bộ đo hay trong bài.
- Đổi tiêu chí đo hay câu hỏi nghiên cứu sau khi đã khoá bộ mù.
- Chạy đo khi máy có nguy cơ vượt 70 °C; giới hạn công suất máy.
- Danh sách tác giả và nơi nộp bài 2.

*Nguồn: JD_BAI_BAO_2_SYSTEM4_2026-10-25.docx, mục 4 và 8. Xem docs/KE_HOACH_BAI_BAO_2_SYSTEM4_2026-10-25.md cho kế hoạch đầy đủ.*

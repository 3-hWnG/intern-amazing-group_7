# Topic Revision Log

Nhật ký ghi nhận quá trình tiến hóa và tinh chỉnh đề tài:

| Phiên bản | Ngày | Thay đổi chính | Lý do thực hiện | Người thực hiện |
|---|---|---|---|---|
| **v1.0** | 2026-10-05 | Khởi tạo đề tài: "Chatbot tra cứu thủ tục hành chính công bằng FTS5" | Đánh giá baseline V10.6 cho thấy độ chính xác Top-1 chỉ đạt 10.6% vì bỏ dấu tiếng Việt làm lẫn lộn từ ("hộ chiếu" trùng "hỗ trợ gạo"). | Cả nhóm |
| **v1.1** | 2026-10-06 | Nâng cấp lên System 3: Xếp hạng âm tiết IDF + Phạt lệch dấu thanh (`ACCENT_MISMATCH = 0.35`) + Tách tên lõi `_core_name`. | Giải quyết triệt để lỗi tìm kiếm tiếng Việt có dấu/không dấu, nâng Top-1 lên 84.0% với độ trễ 7-15ms. | Trịnh Hoàng Nhân |
| **v1.2** | 2026-10-07 | Tích hợp System 4: Bổ sung kiến trúc Vector Qdrant, mô hình nhúng BGE-M3, RRF fusion và giao diện trò chuyện thân thiện. | Người dùng có nhu cầu tải tài liệu riêng và muốn AI trò chuyện giải thích thay vì chỉ tra cứu bảng tĩnh. | Nguyễn Việt Hùng |
| **v1.3** | 2026-10-08 | Hợp nhất Sys_3_4 (Dual-Engine) + Bộ nhớ ngữ cảnh đa lượt có cô lập trạng thái hỏi lại (`Clarify State Isolation`). | Khắc phục hiện tượng suy giảm ngữ cảnh sau nhiều lượt chat và chống ô nhiễm bộ nhớ khi AI hỏi lại lựa chọn. Đạt 88/91 ca kiểm thử ngữ cảnh (96.7%). | Phạm Lê Thiên Đan |
| **v1.4** | 2026-10-09 | Chuẩn hóa cấu trúc thư mục học thuật theo chuẩn 8 phần nghiên cứu của nhóm Git và xuất bản bài báo hoàn chỉnh. | Đáp ứng quy chuẩn nộp bài hội thảo khoa học và quản lý dự án nghiên cứu AI. | Cả nhóm |

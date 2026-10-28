# Weekly Report - Week 01

Thời gian: 07/09 – 13/09/2026

## Group Information

Class: Không có (thực tập)
Group: Nhóm 7
Leader: Trịnh Hoàng Nhân
Members: Nguyễn Viết Hưng, Phạm Lê Thiên Dấn
Mentor: Trương Long

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Nguyễn Viết Hưng | Khởi tạo repo nhóm (09/09); README, hướng dẫn cài đặt và khởi tạo CSDL; checklist tiến độ; tài liệu BREAKDOWN | Repo và tài liệu ban đầu |
| Nguyễn Viết Hưng | Bản demo FastAPI: cải tiến giao diện, xử lý lỗi; changelog main.py từ V1 tới V3 | Demo chạy được |
| Phạm Lê Thiên Dấn | Tìm kiếm web bằng duckduckgo-search; phân loại ý định theo ngữ nghĩa (luat_emb, classify_intent_semantic); prompt cho câu luật, ngoài phạm vi, xã giao | Giảm trả lời nhầm câu ngoài phạm vi |
| Phạm Lê Thiên Dấn | Tăng tốc chatbot; thử nâng model lên 3B, kèm dữ liệu cào và tệp dữ liệu gộp | Lần đầu phải hoàn tác (12/09), làm lại ngày 13/09 |
| Trịnh Hoàng Nhân | Thêm bộ câu đánh giá đầu tiên (13/09) | Có bộ đánh giá để so các phiên bản |

## Git Commits

Tổng số commit trong tuần: 23 (Trịnh Hoàng Nhân: 1, Nguyễn Viết Hưng: 15, Phạm Lê Thiên Dấn: 7). Nhánh: AllProc_V10.3. Bảng dưới chỉ liệt kê các commit tiêu biểu; danh sách đầy đủ xem bằng `git log --all` trên repo nhóm.

| Commit ID | Message | Author |
|---|---|---|
| 4160a87 | Update project name and installation instructions | Nguyễn Viết Hưng |
| ebf2db0 | Create progress checklist for project features | Nguyễn Viết Hưng |
| 2080061 | Refactor FastAPI app with UI improvements and error handling | Nguyễn Viết Hưng |
| a59f330 | thêm duckduckgo-search | Phạm Lê Thiên Dấn |
| 8bc6d90 | update luat_emp, classify_intent_semantic(), promt LUAT + NGOAI + XA GIAO | Phạm Lê Thiên Dấn |
| 190f0b8 | Revert "up model lên 3b" | Phạm Lê Thiên Dấn |
| 183e551 | up model lên 3b, thêm file cào và data cào, tạo file data merge | Phạm Lê Thiên Dấn |
| 79e6296 | Thêm Evaluation set | Trịnh Hoàng Nhân |

## Current Problems

- Chatbot trả lời nhầm câu ngoài phạm vi; phải sửa phần phân loại ý định.
- Nâng model lên 3B lỗi, phải hoàn tác một lần.
- Chưa có bộ đánh giá chung; bộ đầu tiên mới có vào cuối tuần.

## Plan for Next Week

- Thử fine-tune model nhỏ (1.5B, 3B, 7B).
- Làm lại phần truy hồi và tìm kiếm web (MCP).
- Gộp các chức năng của từng người vào code chính.

## Questions for Instructor

- Không có.

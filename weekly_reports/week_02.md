# Weekly Report - Week 02

Thời gian: 14/09 – 20/09/2026

## Group Information

Class: Không có (thực tập)
Group: Nhóm 7
Leader: Trịnh Hoàng Nhân
Members: Nguyễn Viết Hưng, Phạm Lê Thiên Dấn
Mentor: Trương Long

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Nguyễn Viết Hưng | Hướng dẫn cài đặt và chạy fine-tune cho model 1.5B, 3B, 7B; tệp trả lời của bản 7B | Có quy trình fine-tune (sau này sản phẩm cuối không dùng fine-tune) |
| Nguyễn Viết Hưng | Tối ưu MCP Search, Intent Router và Verifier chống ảo giác (nhánh Re-imagine-V10) | Bản sửa lõi |
| Nguyễn Viết Hưng | Dữ liệu fine-tune cho truy vấn tìm kiếm; script đo và phục hồi dữ liệu; tài liệu V10.1.x | Nhánh Reimage-V10.1 |
| Phạm Lê Thiên Dấn | Gộp các chức năng của Nhân vào code chính và sửa logic; MCP tự sinh 3 lựa chọn prompt khi không chắc; sửa luật lệ phí hộ tịch | Chạy được trên nhánh chính |
| Trịnh Hoàng Nhân | Revamp: truy hồi lai, thang bậc A/B/C/D, đăng nhập, hàng đợi, phiên (nhánh revamp) | R@1 từ 0,527 lên 0,856 trên bộ đánh giá lúc đó |
| Trịnh Hoàng Nhân | Thử bộ điều phối agent (v6); V10: MCP web search + Evidence Pack + kiểm chứng; V11; V10.3: cấu trúc thư mục mới | Các nhánh thử nghiệm |

## Git Commits

Tổng số commit trong tuần: 25 (Trịnh Hoàng Nhân: 6, Nguyễn Viết Hưng: 15, Phạm Lê Thiên Dấn: 4). Nhánh: AllProc_V10.3, revamp, Re-imagine, Re-imagine-V10, Reimage-V10.1. Bảng dưới chỉ liệt kê các commit tiêu biểu; danh sách đầy đủ xem bằng `git log --all` trên repo nhóm.

| Commit ID | Message | Author |
|---|---|---|
| 9f209ce | Revamp: hybrid retrieval (R@1 0.527 -> 0.856), tier ladder A/B/C/D, auth, queue, sessions | Trịnh Hoàng Nhân |
| 8cf289f | V10: MCP web search + Evidence Pack + kiem chung thay cho router cu | Trịnh Hoàng Nhân |
| 6754d9a | V10.3: cấu trúc thư mục mới, dễ đọc cho người | Trịnh Hoàng Nhân |
| db30664 | Add installation instructions for finetune3B model | Nguyễn Viết Hưng |
| 5f3987e | Fix core: Tối ưu MCP Search, Intent Router và Verifier chống Ảo giác | Nguyễn Viết Hưng |
| e3d2f32 | Add: Script đo lường và phục hồi Data | Nguyễn Viết Hưng |
| 8551d4c | tui thêm mấy cái chức năng của Ông nhân vô code chính với sửa logic | Phạm Lê Thiên Dấn |
| 2f29302 | feat: auto 3 lựa chọn prompt choices cho MCP search | Phạm Lê Thiên Dấn |

## Current Problems

- Nhiều nhánh thử nghiệm chạy song song (revamp, Re-imagine, Reimage-V10.1), chưa thống nhất một hướng.
- Câu trả lời dựa trên kết quả tìm kiếm web có ảo giác; phải thêm bước kiểm chứng.
- Chưa rõ có dùng model fine-tune hay không (sản phẩm cuối không dùng).

## Plan for Next Week

- Dựng cơ sở dữ liệu thủ tục (System 2).
- Tách luồng tìm kiếm web và truy hồi.
- Giới hạn phạm vi thủ tục.

## Questions for Instructor

- Không có.

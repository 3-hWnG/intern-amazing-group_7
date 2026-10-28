# Weekly Report - Week 03

Thời gian: 21/09 – 27/09/2026

## Group Information

Class: Không có (thực tập)
Group: Nhóm 7
Leader: Trịnh Hoàng Nhân
Members: Nguyễn Viết Hưng, Phạm Lê Thiên Dấn
Mentor: Trương Long

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Nguyễn Viết Hưng | Khởi tạo kiến trúc System 2: lược đồ SQLite FTS5, trigger, importer | Nhánh Re-imagine-V10 |
| Nguyễn Viết Hưng | Dual-System V10.2.1 với CSDL 758 thủ tục, rerank, grounding guard, xếp theo cấp thẩm quyền; V10.5.1 tối ưu nhận diện thủ tục, tách synonyms, bộ test 92 mục; ẩn khối suy nghĩ trên giao diện | Nhánh V10.2.1, V10.5.1 |
| Trịnh Hoàng Nhân | Tách luồng tìm kiếm web (System 1) và truy hồi (System 2), nút chuyển hệ thống | Hai hệ thống chạy riêng |
| Trịnh Hoàng Nhân | Pipeline ETL thủ tục hành chính: 1.407 thủ tục, SQLite + FTS5; nối System 2 vào CSDL | Phase 1–2 |
| Trịnh Hoàng Nhân | Giới hạn phạm vi cấp xã/phường (lọc level = COMMUNE); V10.5: tài liệu và script cài đặt | Phạm vi được chốt ngày 23/09 |
| Phạm Lê Thiên Dấn | Tìm và đọc bài báo liên quan (kết quả commit ngày 28/09: 25 bài) *(ước theo khoảng thời gian: tuần này không có commit, việc được chia đều theo hướng dẫn của trưởng nhóm)* | Danh sách bài báo |

## Git Commits

Tổng số commit trong tuần: 12 (Trịnh Hoàng Nhân: 6, Nguyễn Viết Hưng: 6, Phạm Lê Thiên Dấn: 0). Nhánh: Re-imagine-V10, AllProc_V10.3-phase2, V10.2.1, V10.5, V10.5.1. Bảng dưới chỉ liệt kê các commit tiêu biểu; danh sách đầy đủ xem bằng `git log --all` trên repo nhóm.

| Commit ID | Message | Author |
|---|---|---|
| 4661f0e | feat(system2): Khởi tạo kiến trúc System 2, SQLite FTS5 Schema, Triggers, Importer | Nguyễn Viết Hưng |
| 22b8104 | feat(v10.2.1): hoan thien Dual-System V10.2.1 voi CSDL 758 thu tuc | Nguyễn Viết Hưng |
| de50a4d | feat(v10.5.1): toi uu nhan dien thu tuc, tach synonyms json va bo test 92 muc | Nguyễn Viết Hưng |
| 29e67eb | System 1/2: tách luồng websearch và retrieval, thêm nút chuyển hệ thống | Trịnh Hoàng Nhân |
| a27ed4e | Phase 1: pipeline ETL thủ tục hành chính (1.407 thủ tục, SQLite + FTS5) | Trịnh Hoàng Nhân |
| 98d038d | Phạm vi cấp Xã/Phường: lọc level=COMMUNE, pipeline biết giới hạn phạm vi | Trịnh Hoàng Nhân |

## Current Problems

- Hai bản System 2 làm song song (CSDL 758 thủ tục và 1.407 thủ tục), phải chọn một.
- Phạm vi quá rộng nếu nhận mọi thủ tục; nhóm quyết định chỉ phục vụ cấp xã/phường.

## Plan for Next Week

- Hoàn thiện tài liệu nghiên cứu (danh sách bài báo).
- Sửa lỗi quản trị người dùng của bản V10.6.

## Questions for Instructor

- Không có.

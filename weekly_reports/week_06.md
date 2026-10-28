# Weekly Report - Week 06

Thời gian: 12/10 – 18/10/2026

## Group Information

Class: Không có (thực tập)
Group: Nhóm 7
Leader: Trịnh Hoàng Nhân
Members: Nguyễn Viết Hưng, Phạm Lê Thiên Dấn
Mentor: Trương Long

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Trịnh Hoàng Nhân | Xuất Excel CSDL thủ tục; sửa link tới trang thủ tục trên Cổng; miền ABI cho System 4 theo điều khoản API của chủ trang | Tính năng mới |
| Trịnh Hoàng Nhân | Kiểm toán codebase, đánh giá kiến trúc, quyết định của trưởng nhóm và kế hoạch G0–G4; thực hiện kế hoạch: lệ phí đúng đơn vị, che dữ liệu cá nhân, dữ liệu thủ tục theo phiên bản, đếm và liệt kê bằng text-to-SQL, hỏi tỉnh khi thủ tục có bản riêng tỉnh, fast path cho dữ liệu tải lên, hàng đợi GPU chung | 3 lượt đánh giá đầy đủ (lượt 3 cho kết quả trùng lượt 2) |
| Trịnh Hoàng Nhân | Cập nhật thư mục Code của repo môn | Repo môn khớp merge_sys_3_4 |
| Nguyễn Viết Hưng | Công cụ tìm kiếm web, định tuyến miền, liệt kê thủ tục; xử lý góp ý của trưởng nhóm (hỏi lệ phí, nhật ký góp ý, quản lý bộ dữ liệu) | Nhánh merge_sys_3_4, Code |
| Nguyễn Viết Hưng | MRR/nDCG@5 và khoảng Wilson, bộ kiểm an toàn, RAGAS-lite; che số điện thoại và số giấy tờ có dấu phân cách; xuất phản hồi thích/không thích; tài liệu số liệu cho slide | Bộ đánh giá mới |
| Phạm Lê Thiên Dấn | Cập nhật phân tích tổng quan tài liệu (repo môn); bộ đánh giá 4 tầng (RAGAS 394 ca, golden đa miền, MRR/nDCG); cập nhật bản nháp bài báo và LaTeX với số liệu mới và phần System 4 | Bản nháp bài báo ngày 15/10 |

## Git Commits

Tổng số commit trong tuần: 78 (Trịnh Hoàng Nhân: 63, Nguyễn Viết Hưng: 12, Phạm Lê Thiên Dấn: 3). Nhánh: merge_sys_3_4, Code, draft, exec/2026-10-19-audit-fixes; repo môn. Bảng dưới chỉ liệt kê các commit tiêu biểu; danh sách đầy đủ xem bằng `git log --all` trên repo nhóm.

| Commit ID | Message | Author |
|---|---|---|
| 096c3e2 | feat: add "Xuất Excel" export of the Strict procedure database to the admin page | Trịnh Hoàng Nhân |
| 257cd5c | docs: codebase audit, architecture review, leader decisions and execution plan for 19-23 | Trịnh Hoàng Nhân |
| 8d9465c | feat(G4.2): list / count procedures with text-to-SQL on proc_flat (P12, ADR-09) | Trịnh Hoàng Nhân |
| 0a6a1e3 | feat(G4.4): ask which province when a procedure has province-specific versions (D5) | Trịnh Hoàng Nhân |
| eb96fea | eval(G4): full eval #2 (2/3) after G4.1-G4.8 — numbers and attribution | Trịnh Hoàng Nhân |
| a9c8f3b | feat: add websearch tool, domain routing, procedure listing and system4 updates | Nguyễn Viết Hưng |
| 6740c10 | feat(eval): MRR/nDCG@5 + Wilson CI, safety suite, real-log cases, two-phase RAGAS-lite | Nguyễn Viết Hưng |
| 90e2dc4 | fix(policy): mask PII with separators (spaces, dashes, dots) in phone/ID numbers | Nguyễn Viết Hưng |
| c829392 | feat(eval): hoan thien bo evaluation 4 tang (RAGAS 394 ca, golden set da domain, MRR/nDCG) | Phạm Lê Thiên Dấn |
| 5a8cfe9 | docs(paper): update paper draft and LaTeX source with revised empirical metrics and System 4 evaluation | Phạm Lê Thiên Dấn |

## Current Problems

- Đánh giá chủ yếu trên bộ câu do nhóm tự viết; chưa biết hệ thống làm thế nào với câu hỏi thật của người dân.
- Kiểm toán thấy nhiều tài liệu lệch với code.
- Bản nháp bài báo mô tả cả những thành phần không có trong code (phát hiện ngày 25/10).

## Plan for Next Week

- Đánh giá trên câu hỏi thật của người dân.
- Khoá bộ test trước khi sửa code.
- Sửa lỗi fast path trên dữ liệu thật.

## Questions for Instructor

- Không có.

# Weekly Report - Week 07

Thời gian: 19/10 – 25/10/2026

## Group Information

Class: Không có (thực tập)
Group: Nhóm 7
Leader: Trịnh Hoàng Nhân
Members: Nguyễn Viết Hưng, Phạm Lê Thiên Dấn
Mentor: Trương Long

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Trịnh Hoàng Nhân | Hoàn tác G4.8 (gây hồi quy); sửa 4 lỗi fast path trên dữ liệu thật; miền FLM và dữ liệu thật cho y tế, giáo dục, du lịch; dữ liệu thủ tục bản 3 (1.517 thủ tục) đưa vào git; chế độ khách; kế hoạch nộp bài (chỉ tạp chí) | Bản cho đồng đội cài một lần là chạy |
| Nguyễn Viết Hưng | Bộ câu hỏi thật real_v1 cho System 3 (300 câu) và System 4 (200 câu): nhãn hai lượt, kiểm đồng thuận, khoá sha256; kết quả chạy một lần cho cả hai hệ thống | Thấy khoảng cách lớn giữa bộ tự viết và câu thật |
| Trịnh Hoàng Nhân | Khoá hai bộ test trước mọi sửa code (24/10); câu hỏi khó: ba phương án cho System 3, đóng băng code, chạy test một lần và báo cáo | Bản gốc 0,647 → lớp luật 0,814 (độ chính xác cân bằng, test 1) |
| Trịnh Hoàng Nhân | Baseline RAG + model 4B tự quyết; mẫu 100 câu cho lượt nhãn thứ hai (trưởng nhóm kiểm từng câu, κ = 0,685) | Kết luận không đổi khi dùng nhãn lượt hai |
| Trịnh Hoàng Nhân | Bộ test thứ hai real_v4: khoá thứ tự, trưởng nhóm duyệt nhãn 400 câu, khoá nhãn; luật vòng 2 (đóng băng 88cabd6); chạy một lần | Vòng 2 hoà vòng 1 trên câu mới |
| Trịnh Hoàng Nhân | Bản nháp bài 1 (System 3) và code công khai (nhánh paper1-vjcs-draft); JD cho thành viên làm bài 2; báo cáo tiến độ cho nhóm | Bản nháp cho nhóm đọc |
| Phạm Lê Thiên Dấn | Bài 2 (System 4), bước J1: khoá bản đầu của bộ mù real_v4_s4 (dữ liệu bảng, câu phần A và B, nhãn, sha256) trên nhánh JD-system4 | Bản khoá đầu; hoàn tất ở tuần 8 |

## Git Commits

Tổng số commit trong tuần: 35 (Trịnh Hoàng Nhân: 31, Nguyễn Viết Hưng: 3, Phạm Lê Thiên Dấn: 1). Nhánh: exec/2026-10-19-audit-fixes, merge_sys_3_4, paper1-vjcs-draft, JD-system4, exec/2026-10-24-hard-questions (chưa đẩy). Bảng dưới chỉ liệt kê các commit tiêu biểu; danh sách đầy đủ xem bằng `git log --all` trên repo nhóm.

| Commit ID | Message | Author |
|---|---|---|
| 2eb6328 | data: procedure data version 3 (scraped 13/10, 1,517 procedures) in git | Trịnh Hoàng Nhân |
| 9620d9f | eval(real_v1): two-pass labels, agreement check and sha256 lock | Nguyễn Viết Hưng |
| 83a1251 | eval(real_v1): one-shot results for both systems, scoring scripts and docs | Nguyễn Viết Hưng |
| 7e78438 | eval: lock two held-out test sets before any code change (checkpoint 2) | Trịnh Hoàng Nhân |
| b7010d1 | hard questions: three approaches for System 3, SQL route for System 4, frozen before test runs | Trịnh Hoàng Nhân |
| 7d199f3 | hard questions: test-set results for both systems and the report (checkpoint 4) | Trịnh Hoàng Nhân |
| 83b33b4 | eval(real_v2): second-pass labels for 100 test questions, agreement (kappa 0.685) and a rescoring check | Trịnh Hoàng Nhân |
| a79ec5f | eval(real_v4): lock the labels of the second test set before the final run | Trịnh Hoàng Nhân |
| 536d2be | eval(real_v4): one run of each configuration on the second locked test set | Trịnh Hoàng Nhân |
| ea454a5 | eval: lock real_v4_s4 blind benchmark (data, cases A/B, labels, sha256) | Phạm Lê Thiên Dấn |
| 18eab7e | docs: paper 1 (System 3) draft and code for the team to read | Trịnh Hoàng Nhân |

## Current Problems

- Trên câu hỏi thật, 79% câu phải từ chối, và hệ thống gốc trả lời nhầm 114/248 câu đáng lẽ phải từ chối.
- Nhãn dev và test 1 do chính trợ lý AI viết luật đề xuất; phải thêm lượt nhãn thứ hai để kiểm.
- Luật vòng 2 tốt trên dev nhưng không lặp lại trên bộ test mới.
- Bản nháp bài báo cũ có ít nhất 11 trích dẫn sai, phải viết lại từ đầu.

## Plan for Next Week

- Phản biện nội bộ và hoàn thiện bài 1.
- Biên dịch trên Overleaf.
- Chuẩn bị nộp VJCS.

## Questions for Instructor

- Không có.

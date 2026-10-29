# Weekly Report - Week 08

Thời gian: 26/10 – 01/11/2026 (tính tới 29/10)

## Group Information

Class: Không có (thực tập)
Group: Nhóm 7
Leader: Trịnh Hoàng Nhân
Members: Nguyễn Viết Hưng, Phạm Lê Thiên Dấn
Mentor: Trương Long

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Trịnh Hoàng Nhân | 7 vòng phản biện nội bộ (agent rà checklist và agent phản biện) và sửa bài theo từng vòng | Kết luận cuối: "nộp được"; phản biện khuyến nghị nhận sau khi sửa câu chữ |
| Trịnh Hoàng Nhân | Phân tích sau (post hoc): bỏ từng luật, chỉ dùng cổng, cổng học naive Bayes và hồi quy logistic trên BGE-M3, McNemar cặp và khoảng bootstrap; chạy lại bộ tự viết ở code đóng băng | Không cổng học nào tốt hơn có ý nghĩa |
| Trịnh Hoàng Nhân | Biên dịch Overleaf, sửa trình bày theo template ws-vjcs; hoàn thiện thư mục bài báo (báo cáo tuần, sơ đồ, bảng, hình, tóm tắt 29 tài liệu) | Bản Overleaf ngày 27/10: 12 trang |
| Trịnh Hoàng Nhân | Điền ORCID của ba sinh viên và URL mã công khai vào bài; dựng lại gói Overleaf | Biên dịch lại ngày 28/10: 12 trang, ở `08_final_submission/final_paper.pdf`; mentor chưa có ORCID trong bài |
| Nguyễn Viết Hưng | Không có commit trên các nhánh của nhóm trong tuần (tính tới 29/10). | — |
| Phạm Lê Thiên Dấn | Bài 2 (System 4), bước J1: hoàn tất và khoá bộ mù real_v4_s4: 216 câu (128 câu sinh theo khuôn, 88 câu người viết) trên 8 bảng Wikipedia; nhãn hai người cho phần người viết; sha256 | κ hành vi phần người viết 0,952; đồng thuận đáp án 95,5% |
| Phạm Lê Thiên Dấn | Bài 2, bước J2–J4: đẩy bản sửa 4 lỗi S4-1…S4-4 của đường nhanh (theo báo cáo của bài 2, phần sửa engine do Trịnh Hoàng Nhân nhận làm), chạy bộ mù 7 cấu hình, mỗi cấu hình một lần; đo hành vi và thời gian nạp bảng; báo cáo tiếng Việt và bản nháp bài 2 tiếng Anh | Sau sửa 113/216 (52,3%), không khác trước sửa (115/216); đường cũ dùng công cụ bảng cao nhất 131/216 (60,6%) |

## Git Commits

Tổng số commit trong tuần (tính tới 29/10): 10 (Trịnh Hoàng Nhân: 8, Nguyễn Viết Hưng: 0, Phạm Lê Thiên Dấn: 2), gồm 5 commit trên exec/2026-10-24-hard-questions, 3 commit trên paper1-vjcs-draft (`311a593`, `9ab02ca`, `53f6aa2`) và 2 commit trên JD-system4 (`539bdc5`, `4d4d51e`). Nhánh: exec/2026-10-24-hard-questions (chưa đẩy), paper1-vjcs-draft, JD-system4. Bảng dưới chỉ liệt kê các commit tiêu biểu; danh sách đầy đủ xem bằng `git log --all` trên repo nhóm.

| Commit ID | Message | Author |
|---|---|---|
| 4bb4cfc | eval(golden): rerun the team-written set at the frozen code | Trịnh Hoàng Nhân |
| a870122 | eval(hard): post-hoc ablations and a learned out-of-scope gate, after referee review | Trịnh Hoàng Nhân |
| 89e077e | eval(hard): a logistic-regression gate on BGE-M3 embeddings, post-hoc | Trịnh Hoàng Nhân |
| c7e47da | eval(hard): one script for the paired tests and bootstrap intervals in the paper | Trịnh Hoàng Nhân |
| 9daef1c | fix(eval): keep the unrounded balanced-accuracy difference in paired_stats | Trịnh Hoàng Nhân |
| 311a593 | docs: complete paper 1 folder in the course-repo layout | Trịnh Hoàng Nhân |
| 9ab02ca | docs: add the authors' ORCID iDs and rebuild the Overleaf package | Trịnh Hoàng Nhân |
| 53f6aa2 | docs: add the final paper PDF compiled on Overleaf | Trịnh Hoàng Nhân |
| 539bdc5 | eval: finalize and lock real_v4_s4 blind benchmark (216 cases, 8 tables) | Phạm Lê Thiên Dấn |
| 4d4d51e | J2-J4: S4-1..S4-4 fix pass, J3 blind eval (7 configs) + behavior + load-time, VI/EN reports | Phạm Lê Thiên Dấn |

## Current Problems

- Bài dài 12 trang, trong khi mục tiêu ban đầu là khoảng 10 trang (trưởng nhóm chấp nhận 11–12 trang).
- Bài đã có ORCID của ba sinh viên; mentor chưa có ORCID trong bài (không bắt buộc).
- Bài 2: trên bộ mù mới real_v4_s4, bản sửa 4 lỗi không hơn bản trước sửa, và đường nhanh SQL vẫn thấp hơn đường cũ dùng công cụ bảng (52,3% so với 60,6%), dù nhanh hơn (trung vị 1,1 s so với 5,6 s).
- Cần chốt chế độ hiển thị của repo nhóm và nơi đặt mã công khai cho bài (trưởng nhóm đang hỏi cấp trên). Các commit của tuần 7–8 trên máy chưa được đẩy lên GitHub.

## Plan for Next Week

- Chốt nơi đặt mã công khai.
- Nộp bài lên VJCS.
- Làm slide trình bày.

## Questions for Instructor

- Thầy duyệt cho nhóm nộp bài 1 lên Vietnam Journal of Computer Science chưa ạ?
- Thầy xác nhận giúp nhóm việc thầy đứng tên tác giả cuối, với đơn vị Department of Artificial Intelligence, FPT University? Nếu thầy có ORCID, nhóm xin mã để ghi vào bài.
- Mã công khai của bài nên đặt ở repo nhóm hay repo môn, và repo đó có được để public khi nộp không ạ?

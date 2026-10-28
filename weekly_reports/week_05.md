# Weekly Report - Week 05

Thời gian: 05/10 – 11/10/2026

## Group Information

Class: Không có (thực tập)
Group: Nhóm 7
Leader: Trịnh Hoàng Nhân
Members: Nguyễn Viết Hưng, Phạm Lê Thiên Dấn
Mentor: Trương Long

## Tasks Completed This Week

| Member | Task | Result |
|---|---|---|
| Nguyễn Viết Hưng | Dựng nhánh system3: truy hồi lai BM25 + ngữ nghĩa, orchestrator, planner, API, giao diện chat, dữ liệu thủ tục | System 3 chạy được |
| Nguyễn Viết Hưng | Bộ benchmark, ca đánh giá và chỉ số; báo cáo hiệu năng System 3 và báo cáo ngày; trích trường được hỏi, định tuyến nhiều truy vấn; planner LLM lai; bộ nhớ người dùng; chịu nhiễu; chọn biến thể thủ tục | Các đợt cải tiến dot4–dot6 |
| Nguyễn Viết Hưng | merge_sys_3_4: một model chung cho Strict và Friendly, chọn trong Settings | Gộp hai hệ thống |
| Trịnh Hoàng Nhân | System 4 (nhánh System_4): NV1 đăng nhập và chuyển Strict/Friendly, NV2 Friendly kiểu ChatGPT, NV3 tải dữ liệu → chế độ chuyên gia, NV4 trang admin, NV5 benchmark; bộ công cụ cho dev | System 4 bản đầu |
| Trịnh Hoàng Nhân | Đưa bản nháp bài báo (Overleaf V0.1) và code lên repo môn (09/10) | Repo môn có nội dung |
| Phạm Lê Thiên Dấn | Báo cáo đồng bộ merge_sys_3_4; tài liệu bài báo, tổng quan tài liệu, kiến trúc; đồng bộ ngữ cảnh nhiều lượt và chọn biến thể từ system3 | Tài liệu cho bản nháp |

## Git Commits

Tổng số commit trong tuần: 66 (Trịnh Hoàng Nhân: 23, Nguyễn Viết Hưng: 40, Phạm Lê Thiên Dấn: 3). Nhánh: system3, System_4, merge_sys_3_4; repo môn (main, Code). Bảng dưới chỉ liệt kê các commit tiêu biểu; danh sách đầy đủ xem bằng `git log --all` trên repo nhóm.

| Commit ID | Message | Author |
|---|---|---|
| a3d090a | feat(retrieval): implement hybrid BM25 and semantic ranking pipeline | Nguyễn Viết Hưng |
| 9e8a6b0 | feat(eval): add benchmarking suite, evaluation cases and metrics | Nguyễn Viết Hưng |
| c3d6853 | feat(server): add hybrid LLM planner, runtime config toggle and conversation export | Nguyễn Viết Hưng |
| d9ed6ec | feat: one shared model for Strict and Friendly, chosen in Settings (gear) | Nguyễn Viết Hưng |
| 4e6410b | feat(system4): NV1 foundation - login/signup, Strict/Friendly toggle, settings panel | Trịnh Hoàng Nhân |
| 9151ca8 | feat(system4): NV3 dataset upload -> Specialist mode with sources | Trịnh Hoàng Nhân |
| 8eb193e | feat(system4): NV5 defaults = benchmark winner; final exam + Strict comparison results | Trịnh Hoàng Nhân |
| 1a49e10 | Source Overleaf V0.1 | Trịnh Hoàng Nhân |
| b197f75 | docs: add research paper assets, literature reviews, and system architecture documentation | Phạm Lê Thiên Dấn |
| 614efc2 | Initial commit (repo môn, mentor Trương Long tạo) | Trương Long |

## Current Problems

- System 3 và System 4 phát triển trên hai nhánh riêng, phải gộp thành merge_sys_3_4.
- Bản nháp bài báo đầu tiên (Overleaf V0.1) mô tả cả hai hệ thống; sau này phải viết lại vì có trích dẫn sai.

## Plan for Next Week

- Xử lý góp ý của trưởng nhóm.
- Bộ đánh giá đầy đủ hơn (MRR/nDCG, Wilson, RAGAS-lite).
- Kiểm toán codebase và lập kế hoạch sửa.

## Questions for Instructor

- Không có.

# Bài báo 1: System 3 — *Answer, Clarify or Refuse?*

**Answer, Clarify or Refuse? Rules, a Reranker and a Small LLM on Real Citizen Questions about Commune-Level Administrative Procedures in Vietnam**

- **Nhóm:** Nhóm 7 (thực tập).
- **Thành viên:** Trịnh Hoàng Nhân (trưởng nhóm, tác giả liên hệ), Nguyễn Viết Hưng, Phạm Lê Thiên Dấn.
- **Mentor:** Trương Long.
- **Đơn vị:** Khoa Trí tuệ nhân tạo, Trường Đại học FPT, TP. Hồ Chí Minh.
- **Nơi nộp dự kiến:** Vietnam Journal of Computer Science (World Scientific).

Bài là một nghiên cứu đánh giá. Đối tượng là một trợ lý chỉ phục vụ **thủ tục hành chính cấp xã/phường**, không phải mọi thủ tục trên toàn quốc. Bài hỏi trợ lý này nên trả lời, hỏi lại hay từ chối khi gặp câu hỏi thật của người dân.

Trên hai bộ test khoá trước khi sửa code, một lớp luật minh bạch nâng độ chính xác cân bằng từ 0,647 lên 0,814 (test 1), và số câu từ chối đúng từ 175 lên 297/335 (test 2). Reranker, model 4B chạy tại máy và các cổng học không cải thiện có ý nghĩa. Để model tự quyết thì không hơn luôn từ chối.

## Cấu trúc (theo khuôn của repo môn)

| Thư mục | Nội dung |
|---|---|
| `01_topic_proposal/` | Đề xuất đề tài, nhật ký đổi đề tài |
| `02_related_work/` | Từ khoá tìm kiếm, danh sách tài liệu đã kiểm, ma trận tổng quan, 29 tệp tóm tắt (`paper_summaries/`) |
| `03_problem_and_gap/` | Phát biểu vấn đề, khoảng trống nghiên cứu, 3 câu hỏi nghiên cứu, phân tích đóng góp |
| `04_proposed_system/` | Tổng quan, kiến trúc, tích hợp model, luồng dữ liệu, sơ đồ (`diagrams/`) |
| `05_methodology/` | Phương pháp, dữ liệu, baseline, chỉ số |
| `06_experiment_results/` | Cài đặt thí nghiệm, kết quả, bảng (`tables/`), hình (`figures/`) |
| `07_paper_draft/` | Bài báo: LaTeX (`latex/`, bản chuẩn), gói Overleaf, bản Markdown từng phần, dàn ý, ràng buộc khi viết (`constraints.md`) |
| `08_final_submission/` | Bản nộp: PDF từ Overleaf, bản Word |
| `weekly_reports/` | Báo cáo tuần 01–08 (07/09 – 01/11/2026) |
| `Code/` | Bản code công khai đi kèm bài: System 3, script đánh giá, kết quả từng câu (không có văn bản câu hỏi) |

## Đọc nhanh

- Bài: `08_final_submission/final_paper.pdf`. Khi chưa có tệp này thì đọc `07_paper_draft/paper1_draft_readable.pdf` (bản nháp dựng từ LaTeX) hoặc các tệp `.md` trong `07_paper_draft/`.
- Kết quả: `06_experiment_results/results.md`, Bảng 1 ở `06_experiment_results/tables/summary_table.md`.
- Tái lập: `Code/README.md`.

## Biên dịch bài

Tải `07_paper_draft/paper1_overleaf.zip` lên Overleaf; tệp chính là `main.tex`, template `ws-vjcs.cls`. Bản ngày 27/10/2026 dài 12 trang, trong đó 9 trang là nội dung.

## Dữ liệu và quyền riêng tư

- **Câu hỏi:** lấy từ hai bộ dữ liệu công khai trên Hugging Face. Hai bộ này không ghi giấy phép, nên văn bản câu hỏi không được phát hành lại; repo chỉ có mã câu và nhãn. Thông tin cá nhân đã được che trước khi gán nhãn.
- **Dữ liệu thủ tục:** thu từ Cổng Dịch vụ công Quốc gia ngày 13/10/2026, không chứa dữ liệu cá nhân.

## Việc còn lại trước khi nộp

- Biên dịch lại trên Overleaf bằng gói `paper1_overleaf.zip` mới (28/10, đã có ORCID và URL), rồi đặt PDF vào `08_final_submission/`.
- ORCID của mentor, nếu thầy có (không bắt buộc; bài hiện ghi ORCID của ba sinh viên).
- URL trong mục Data Availability trỏ tới nhánh `paper1-vjcs-draft`; nếu mã chuyển sang chỗ khác thì phải sửa URL trước khi nộp.

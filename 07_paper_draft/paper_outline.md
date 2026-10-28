# Paper Outline: bài 1 (System 3)

**Tên bài.** *Answer, Clarify or Refuse? Rules, a Reranker and a Small LLM on Real Citizen Questions about Commune-Level Administrative Procedures in Vietnam*

**Tác giả.** Trịnh Hoàng Nhân (tác giả liên hệ, trưởng nhóm), Nguyễn Viết Hưng, Phạm Lê Thiên Dấn, Trương Long (mentor). Khoa Trí tuệ nhân tạo, Trường Đại học FPT, TP. Hồ Chí Minh.

**Nơi nộp.** Vietnam Journal of Computer Science (World Scientific), template `ws-vjcs.cls`. Ràng buộc ở `constraints.md`.

**Bản chuẩn.** `latex/` (main.tex, sections/*.tex, refs.bib). Gói tải lên Overleaf: `paper1_overleaf.zip`. Các tệp `.md` trong thư mục này sinh tự động từ LaTeX, chỉ để đọc trên GitHub.

## Cấu trúc

| Mục | Tệp LaTeX | Tệp đọc | Nội dung chính |
|---|---|---|---|
| Abstract, Keywords | `sections/abstract.tex` | `abstract.md` | 150 từ, 6 từ khoá |
| 1. Introduction | `introduction.tex` | `introduction.md` | Bài toán ba lựa chọn; phạm vi chỉ thủ tục cấp xã/phường; bốn phát hiện |
| 2. Related Work | `related.tex` | `related_work.md` | Hỏi đáp dịch vụ công tiếng Việt; từ chối và câu ngoài phạm vi; ai quyết định (model hay luật) |
| 3. Task and Data | `data.tex` | `methodology.md` | Định nghĩa nhãn; dữ liệu thủ tục; câu hỏi thật, ba bộ dev/test; nhãn và κ = 0,685; bộ tự viết |
| 4. System and Variants | `method.tex` | `methodology.md` | Bản gốc; lớp luật A; vòng 2 A2; reranker B; LLM reader C; cổng học L (*post hoc*); baseline RAG R |
| 5. Evaluation Protocol | `protocol.tex` | `methodology.md` | Thứ tự làm; quy tắc chọn và so sánh chính; chỉ số; máy chạy |
| 6. Results | `results.tex` | `results.md` | 6.1 bộ tự viết so với câu thật; 6.2 hai bộ test khoá trước, độ chính xác câu trả lời; Bảng 1 |
| 7. Discussion | `discussion.tex` | `discussion.md` | Luật làm gì; phần còn lại; vì sao vòng 2 không lặp lại; giới hạn (i)–(vii) |
| 8. Conclusion | `conclusion.tex` | `conclusion.md` | Kết luận và hướng tương lai |
| Ethics and Data Availability, Competing Interests, Declaration of AI Use, Acknowledgments, ORCID | `ethics.tex`, `ai_declaration.tex`, `main.tex` | `back_matter.md` | Phần cuối theo yêu cầu của World Scientific |
| References (29) | `refs.bib` | `references.md` | Đánh số theo thứ tự trích |

Đối chiếu với khuôn của môn (constraints.md B6): mục 3–5 của bài gộp "Proposed System / Methodology" và "Experimental Setup"; "Conclusion" gồm cả hướng tương lai (trưởng nhóm chọn giữ tên "Conclusion", 28/10).

## Câu hỏi nghiên cứu và nơi trả lời

| RQ | Nội dung | Trả lời ở |
|---|---|---|
| RQ1 | Bộ câu tự viết lệch bao nhiêu so với câu thật? | §6.1 |
| RQ2 | Lớp luật minh bạch cải thiện bao nhiêu trên câu thật đã khoá, có làm tụt bộ cũ không? | §6.2, Bảng 1 |
| RQ3 | Reranker, model 4B, RAG để model tự quyết, và cổng học (*post hoc*) so với lớp luật thế nào? | §6.2, Bảng 1, §7 |

## Bảng và hình

- **Bảng 1** (trong bài): hai bộ test, mọi cấu hình chạy, cân bằng / từ chối đúng / đúng trọn / độ chính xác câu trả lời.
- Ngoài bài (thư mục khuôn): `04_proposed_system/diagrams/architecture.png`, `workflow.png`; `06_experiment_results/figures/balanced_accuracy.png`; `06_experiment_results/tables/`.

## Tình trạng (28/10/2026)

- Phản biện nội bộ 7 vòng: agent checklist kết luận "nộp được"; agent phản biện khuyến nghị nhận sau khi sửa câu chữ (đã sửa).
- Bản Overleaf ngày 27/10: 12 trang (9 trang nội dung, phần còn lại là tài liệu tham khảo). Ngày 28/10 sửa trình bày theo template, cần biên dịch lại.
- Còn thiếu: ORCID của các tác giả (bắt buộc với tác giả liên hệ).
- Còn chờ: chọn nơi đặt mã công khai (URL trong mục Data Availability).

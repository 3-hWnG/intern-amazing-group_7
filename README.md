# Bài báo 1 (System 3): bản nháp + code — branch `paper1-vjcs-draft`

**Bản nháp chưa hoàn thiện, chưa nộp, không phát tán.** Cập nhật ngày 25/10/2026.

Bài: *When Rules Should Decide: Answering, Clarifying and Refusing Real Citizen Questions about Commune-Level Administrative Procedures in Vietnam*. Bài dự kiến nộp tạp chí Vietnam Journal of Computer Science.

Tác giả:
- Trịnh Hoàng Nhân (tác giả liên hệ)
- Nguyễn Viết Hưng
- Phạm Lê Thiên Dấn
- Trương Long

Phạm vi bài: trợ lý chỉ phục vụ thủ tục do **cấp xã/phường** giải quyết, không phải mọi thủ tục hành chính.

## Đọc nhanh

- `paper/paper1_draft_2026-10-25.pdf`: bản đọc được, dựng tự động từ nguồn LaTeX bằng `tools/tex_to_html.py` và LibreOffice. Dàn trang của bản này **khác** template VJCS.
- `paper/latex/` và `paper/paper1_overleaf.zip`: nguồn LaTeX theo template `ws-vjcs`. Tải tệp zip lên Overleaf để biên dịch ra bản thật.

Bài còn thiếu:
- ORCID của các tác giả;
- URL repo công khai;
- một vòng phản biện cuối;
- biên dịch trên Overleaf để kiểm số trang (mục tiêu ≤ 10 trang).

## Kết quả chính

Mỗi bộ test được khoá (hash + commit) trước khi sửa code; mỗi cấu hình chỉ chạy một lần.

| Bộ test | Bản gốc | Lớp luật A | RAG + 4B tự quyết |
|---|---|---|---|
| Test 1 (313 câu): độ chính xác cân bằng | 0,647 | 0,814 | 0,489 |
| Test 1: số câu trả lời đúng trọn | 19/59 | 35/59 | 28/59 |
| Test 2 (363 câu mới): số câu từ chối đúng | 175/335 | 297/335 | 197/335 |

Vòng luật thứ hai (A2) tốt hơn A trên dev (+25 câu), nhưng **hoà** với A trên test 2.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `Code/` | Code System 3 và kết quả từng câu của mọi lượt chạy. Xem `Code/README.md`. |
| `paper/` | Bản nháp bài (PDF đọc được và nguồn LaTeX). |
| `tools/` | `make_public_code.py` (cách dựng `Code/` từ repo phát triển); `tex_to_html.py` (cách dựng bản PDF đọc được). |

## Không có trong branch này

- Văn bản câu hỏi của người dân. Hai dataset gốc trên Hugging Face không ghi giấy phép. Có thể dựng lại bằng `Code/eval/rebuild_questions.py`.
- Tên người thật.
- Dữ liệu hay khoá của bên thứ ba.
- Dữ liệu thủ tục đã thu từ Cổng Dịch vụ công.
- Lịch sử phát triển: branch này là một commit độc lập. Code phát triển nằm ở branch `merge_sys_3_4`.

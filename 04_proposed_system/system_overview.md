# System Overview (khuôn bước 7)

## Người dùng chính
- **Người dân:** hỏi về thủ tục hành chính **cấp xã/phường**, ví dụ khai sinh, kết hôn, cư trú, căn cước, chứng thực, trợ cấp.
- **Cán bộ một cửa cấp xã:** dùng trợ lý để tra nhanh thủ tục.

Phạm vi chỉ là thủ tục cấp xã/phường. Đây không phải trợ lý cho mọi thủ tục hành chính toàn quốc (D13).

## Chức năng chính
1. Đọc câu hỏi, kể cả câu viết như thư: có lời chào, kể chuyện, viết tắt, không dấu.
2. Quyết định một trong ba hành vi:
   - **trả lời**: một thủ tục;
   - **hỏi lại**: nêu các thủ tục ứng viên để người hỏi chọn;
   - **từ chối**: kèm lý do ngắn.
3. Khi trả lời, ghép câu trả lời bằng code từ đúng các mục người hỏi cần trong bản ghi thủ tục (giấy tờ, lệ phí, thời hạn, nơi nộp…), kèm nguồn.
4. Hội thoại nhiều lượt: nhớ thủ tục đã nói tới và xử lý câu hỏi nối tiếp như "còn lệ phí thì sao".

## Dữ liệu đầu vào
- **Câu hỏi:** văn bản tiếng Việt, có thể không dấu.
- **Dữ liệu thủ tục:** 1.517 thủ tục của Cổng Dịch vụ công Quốc gia, thu một lần ngày 13/10/2026. Trong đó 542 thủ tục cấp xã không phân theo tỉnh nằm trong phạm vi.

## AI model sử dụng
Chi tiết ở `ai_model_integration.md`.
- Bản chính, lớp luật A, **không dùng model** để quyết định.
- Các phương án so sánh dùng:
  - BGE-M3 và bge-reranker-v2-m3 (phương án B);
  - Qwen3-4B-Instruct-2507 chạy tại máy (phương án C và baseline RAG).

## Output
JSON gồm `kind` (answer / clarify / refuse), các khối trả lời có nguồn, và thẻ hỏi lại nếu có. Giao diện web hiển thị từ JSON này.

## Điểm chính của thiết kế
Luật quyết định; model chỉ là thành phần phụ có thể bật hoặc tắt.

Mỗi luật nằm sau một cờ. Tắt hết cờ thì hệ thống trả về đúng kết quả của bản gốc trên mọi câu test. Nhờ vậy, mọi so sánh trong bài đều có kiểm soát.

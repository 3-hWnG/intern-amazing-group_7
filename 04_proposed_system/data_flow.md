# Data Flow

Toàn bộ quy trình luân chuyển dữ liệu từ khi người dùng đặt câu hỏi đến khi nhận kết quả phản hồi trải qua 7 bước:

```
[1. Người dùng gửi câu hỏi]
          │
          ▼
[2. Chuẩn hóa & Tiền xử lý] ──► Tách âm tiết, gập dấu (_fold), sửa lỗi chính tả bigram, tách từ dính (kethon -> ket hon)
          │
          ▼
[3. Phân tích Ngữ cảnh]     ──► Bóc tách đại từ, nhận diện 12 Field Intent, kiểm tra trạng thái hội thoại trước
          │
          ▼
[4. Phân luồng Quyết định]
          ├──► (a) Xã giao (Chitchat) ──► Trả lời câu chào/cảm ơn ngay
          ├──► (b) Ngoài phạm vi (OOS) ──► Từ chối lịch sự (chỉ hỗ trợ thủ tục cấp xã)
          ├──► (c) Hỏi 1 mục đơn giản  ──► Bốc thẳng field_chunk từ SQLite -> Trả về bằng Code (7-15ms)
          └──► (d) Câu hỏi phức tạp    ──► Chuyển sang Bước 5
          │
          ▼
[5. Đóng gói Bằng chứng]    ──► Chọn các chunk liên quan, gắn nhãn [d1], [d2], cắt trần độ dài MAX_PASSAGE
          │
          ▼
[6. Mô hình Sinh Phản hồi]  ──► Qwen2.5-7B sinh JSON points kèm mảng cites theo Prompt dặn dò nghiêm ngặt
          │
          ▼
[7. Lớp Kiểm chứng Hậu kỳ]  ──► verify_point(): Rà soát số tiền, ngày, văn bản, từ "miễn phí".
                                    Ý nào vi phạm -> Bỏ ngay. Hết ý -> Fallback sang câu trả lời Code.
          │
          ▼
[8. Hiển thị Giao diện]     ──► Truyền streaming qua Server-Sent Events (SSE) tới Web UI
```

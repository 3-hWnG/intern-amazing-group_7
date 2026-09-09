# CHECKLIST TIẾN ĐỘ THỰC TẾ vs SƠ ĐỒ KIẾN TRÚC


## TẦNG 1: GIAO TIẾP & TIẾP NHẬN
- [x] **B1. Giao diện Client Demo:** Đã Code xong bằng HTML/JS. Có khung Chat, nút Gửi.
- [ ] **B2. Hàng đợi (Message Queue):** Chưa làm. Hiện tại Demo chỉ có 1 User nên bỏ qua phần RabbitMQ/Redis để tiết kiệm thời gian.
- [ ] **B3. Xác thực (Login):** Chưa làm. Chưa ghép Database User SĐT/Email.

## TẦNG 2: NGỮ CẢNH & PHÂN LOẠI
- [ ] **B4. Quản lý Session:** Chưa làm. Khung chat đang hỏi đáp 1-1, chưa tự động load lịch sử trò chuyện cũ.
- [ ] **B5. AI Summarizer (Chống tràn RAM):** Chưa làm. Chờ khi làm xong phần Session mới test được.
- [x] **B6. Phân loại Ý định (Semantic Router):** Hoàn thành cực mạnh. Đã nâng cấp thuật toán từ bám Keyword lên băm Vector (Cosine Similarity) để bẻ nhánh tự động 3 đường: `LUAT`, `NGOAI`, `XAGIAO` mượt mà, không phụ thuộc LLM.

## TẦNG 3: KHAI THÁC DỮ LIỆU
- [x] **B7. Xử lý Xã Giao:** Hoàn thành. Trò chuyện cơ bản không tốn Token tra DB.
- [x] **B8. Tra RAG Nội bộ (Vector DB):** Hoàn thành cốt lõi. Đã dùng Python băm 42 thủ tục, nhúng Vector `keepitreal/vietnamese-sbert` vào ChromaDB. Chạy cực mượt.
- [x] **B9. Tra dữ liệu Ngoài (MCP Search):** Hoàn thành. Đã giả lập chuẩn MCP thông qua thư viện `duckduckgo_search` bốc data trực tiếp từ Internet (Không cần API Key).
- [ ] **B10. Đánh giá (Evaluator / Hỏi ngược lại):** Chưa làm. Hiện tại thiếu thông tin (VD hỏi "Thủ tục A") nó sẽ tự trả lời, chưa biết hỏi vặn lại "Bạn ở Tỉnh nào?".

## TẦNG 4: XUẤT BẢN & KIỂM ĐỊNH
- [x] **B11. Gói Bằng Chứng (Evidence Pack):** Hoàn thành. Đã đóng gói Context móc từ ChromaDB ghép thẳng vào Prompt.
- [x] **B12. Sinh văn bản (Local LLM):** Hoàn thành. Gọi thành công mô hình siêu nhẹ (`Ollama qwen2.5:1.5b`) nhai Evidence Pack.
- [ ] **B13. Kiểm định chéo (Fact-Checker):** Chưa làm. Đang để nguyên văn LLM sinh ra trả về luôn. Chưa có con AI thứ 2 bắt lỗi.
- [x] **B14. Trả kết quả (Formatter):** Hoàn thành. Trả gọn gàng lên màn hình.

---
**TỔNG KẾT (MVP DEMO):** Đã code xong xương sống **7/14 tính năng quan trọng nhất**. Đây gọi là Minimal Viable Product (Sản phẩm khả thi tối thiểu).

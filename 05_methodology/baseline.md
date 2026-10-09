# Baseline Systems

Để đánh giá khách quan đóng góp của Sys_3_4, nhóm thiết lập 3 hệ thống so sánh:

## 1. Baseline V10.6 (Hệ thống Kế thừa Ban đầu)
- **Phương pháp:** Sử dụng SQLite FTS5 thuần túy, bỏ toàn bộ dấu tiếng Việt thành chuỗi không dấu, phân loại câu hỏi dựa trên regex thô.
- **Hạn chế đã biết:**
  - Nhầm lẫn nghiêm trọng giữa các từ đồng âm khác dấu (*"hộ chiếu"* $\rightarrow$ *"hỗ trợ gạo"*).
  - Không nhận diện được tên lõi thủ tục khi có chú thích trong ngoặc đơn dài.
  - Tỷ lệ Top-1 chỉ đạt 10.6% trên tập kiểm thử mù.

## 2. Standard Dense Vector RAG
- **Phương pháp:** Chia chunk văn bản cố định 512 tokens, nhúng vector bằng mô hình BGE-M3, tìm kiếm Cosine Similarity trong Qdrant và prompt trực tiếp LLM.
- **Hạn chế đã biết:**
  - Gặp hiện tượng "trôi ngữ nghĩa" (semantic drift) trên các tên thủ tục có cấu trúc pháp lý tương tự nhau.
  - Thường xuyên bịa số tiền lệ phí khi tài liệu gốc để trống.
  - Thời gian phản hồi chậm (2-4 giây cho mọi truy vấn).

## 3. Direct LLM Prompting (Zero-shot / Few-shot)
- **Phương pháp:** Đưa trực tiếp câu hỏi người dùng vào mô hình ngôn ngữ lớn thương mại mà không có kho ngữ liệu cục bộ.
- **Hạn chế đã biết:**
  - Ảo giác nghiêm trọng về thủ tục hành chính Việt Nam (dẫn sai số hiệu nghị định, nhầm cấp xã với cấp huyện/tỉnh).
  - Không đảm bảo tính riêng tư dữ liệu theo quy định Đề án 06.

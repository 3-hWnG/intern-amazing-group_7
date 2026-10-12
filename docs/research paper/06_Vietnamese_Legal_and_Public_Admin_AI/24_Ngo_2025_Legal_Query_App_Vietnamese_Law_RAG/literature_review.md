# Literature Review: Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques

- **Tên bài báo:** Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques
- **Tác giả:** Ngô Tuấn Anh, Nguyễn Việt Hoàng, Ngô Thanh Tùng, Doãn Trung Tùng (Greenwich Vietnam)
- **Năm xuất bản:** 2025
- **Tạp chí / Hội nghị:** *The 10th International Conference on Intelligent Information Technology (ICIIT 2025)*, Session on Generative AI and Engineering Applications
- **Link Citation / DOI:** ICIIT 2025 Conference Proceedings
- **Tệp toàn văn (PDF):** Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques.pdf

---

## 1. Abstract Tóm tắt
Nghiên cứu tập trung giải quyết bài toán nâng cao tính chính xác và tốc độ truy vấn văn bản pháp luật Việt Nam bằng cách kết hợp Mô hình ngôn ngữ lớn (LLM) và kỹ thuật sinh tăng cường truy xuất (RAG). Nghiên cứu giải quyết thách thức cốt lõi về tính thứ bậc và sự thay đổi, bổ sung liên tục của các văn bản pháp quy Việt Nam. Hệ thống xây dựng quy trình phân đoạn (chunking) ngữ nghĩa theo Điều/Khoản luật thay vì chia nhỏ theo độ dài token thông thường, kết hợp trích xuất metadata phong phú nhằm loại bỏ ảo giác, cung cấp câu trả lời có trích dẫn điều khoản luật minh bạch cho cán bộ pháp chế, luật sư và người dân.

## 2. Phương pháp luận & Đóng góp kỹ thuật
1. **Phân đoạn có cấu trúc pháp lý (Legal Structural Chunking):** Phân chia văn bản pháp lý theo cấu trúc Điều - Khoản - Điểm nhằm bảo tồn ngữ cảnh trọn vẹn của quy định pháp luật.
2. **Metadata Enrichment:** Gắn thẻ metadata về ngày ban hành, hiệu lực thi hành và quan hệ văn bản sửa đổi/bổ sung, ngăn chặn việc dẫn chiếu văn bản hết hiệu lực.
3. **Prompt Ràng buộc trích dẫn (Strict Citation Guard):** Ép buộc mô hình ngôn ngữ chỉ được trả lời dựa trên các phân đoạn văn bản được truy xuất và luôn kèm nguồn dẫn chiếu điều khoản cụ thể.

## 3. Kết quả thực nghiệm
- Cải thiện đáng kể độ chính xác truy xuất (precision & recall) so với phân đoạn cố định theo token.
- Giảm thiểu tối đa hiện tượng mô hình tự bịa đặt số điều luật hoặc chế tài không tồn tại.

## 4. Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm:** Phương pháp phân đoạn theo cấu trúc văn bản pháp luật Việt Nam rất trực quan, hiệu quả cao trong việc bảo toàn ngữ cảnh điều luật.
- **Hạn chế:** Cần kết hợp thêm mô hình tìm kiếm từ khóa toàn văn (full-text keyword search) để xử lý triệt để các câu hỏi sử dụng từ ngữ đời thường, tiếng lóng của người dân.

## 5. Ánh xạ trực tiếp tới Dự án V10.6
- **Kế thừa thiết kế dữ liệu:** Trực tiếp củng cố phương pháp lưu trữ dữ liệu thủ tục trong CSDL SQLite của V10.6 (phân tách rõ ràng tên thủ tục, trình tự, thành phần hồ sơ, lệ phí, căn cứ pháp lý).
- **Kế thừa kiểm soát trích dẫn:** Đồng thuận với nguyên tắc bắt buộc dẫn xuất nguồn gốc thủ tục (source_url, mã thủ tục, cơ quan có thẩm quyền) trong phản hồi của V10.6.

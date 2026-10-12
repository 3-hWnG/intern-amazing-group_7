# Literature Review: ViGPTQA - State-of-the-Art LLMs for Vietnamese Question Answering

- **Tên bài báo:** ViGPTQA - State-of-the-Art LLMs for Vietnamese Question Answering: System Overview, Core Models Training, and Evaluations
- **Tác giả:** Minh-Thuan Nguyen, Khanh-Tung Tran, Vincent Nguyen, Xuan-Son Vu
- **Năm xuất bản:** 2023
- **Tạp chí / Hội nghị:** *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing: Industry Track (EMNLP 2023)*, pages 754–764
- **Link Citation / DOI:** [https://aclanthology.org/2023.emnlp-industry.71/](https://aclanthology.org/2023.emnlp-industry.71/)
- **Tệp toàn văn (PDF):** ViGPTQA - State-of-the-Art LLMs for Vietnamese Question Answering.pdf

---

## 1. Abstract Tóm tắt
Các mô hình ngôn ngữ lớn (LLM) và ứng dụng hỏi đáp cho ngôn ngữ tài nguyên thấp như tiếng Việt thường bị hạn chế do thiếu dữ liệu huấn luyện và tập dữ liệu benchmark chuẩn. Bài báo giới thiệu ViGPTQA - một hệ thống hỏi đáp thực tế cho tiếng Việt ứng dụng LLM, đồng thời đề xuất và mã nguồn mở mô hình ViGPT (tinh chỉnh chỉ dẫn chuyên biệt cho tiếng Việt). Nhóm tác giả xây dựng bộ benchmark mới gồm các kịch bản thực tế (luật pháp, hành chính, tài chính), chứng minh mô hình đạt độ chính xác cao và khả năng hiểu ngữ cảnh tiếng Việt vượt trội so với các mô hình đa ngôn ngữ cùng kích thước.

## 2. Phương pháp luận & Kiến trúc kỹ thuật
1. **Kiến trúc hệ thống ViGPTQA:** Kết hợp mô hình ngôn ngữ tiếng Việt chuyên biệt với cơ chế trích xuất ngữ cảnh nghiệp vụ, xử lý tiền kỳ câu hỏi tiếng Việt và hậu kỳ kiểm soát định dạng.
2. **Instruction Fine-Tuning:** Tinh chỉnh mô hình nền tảng trên tập dữ liệu chỉ dẫn tiếng Việt chất lượng cao được lọc sạch, bảo đảm năng lực trả lời văn phong hành chính và pháp lý chuẩn mực.
3. **Bộ Benchmark chuẩn:** Đánh giá đa chiều trên các tác vụ hỏi đáp chuyên ngành, khả năng bám sát ngữ cảnh thực tế và kháng nhiễu từ vựng địa phương.

## 3. Kết quả thực nghiệm
- ViGPT đạt điểm đánh giá vượt trội so với các baseline mã nguồn mở đa ngôn ngữ trên tập câu hỏi tiếng Việt thực tế.
- Khả năng suy luận ngữ cảnh và sinh câu trả lời tự nhiên, chính xác về cấu trúc ngữ pháp và thuật ngữ hành chính công.

## 4. Đánh giá Ưu điểm & Hạn chế
- **Ưu điểm:** Khẳng định tầm quan trọng sống còn của việc hỗ trợ tiếng Việt bản địa (Vietnamese native understanding) trong các hệ thống hỏi đáp thay vì dựa hoàn toàn vào mô hình dịch máy hoặc mô hình thuần tiếng Anh.
- **Hạn chế:** Hệ thống chưa tích hợp cơ chế kiểm chứng số liệu thời gian thực (grounding guard) tại thời điểm công bố.

## 5. Ánh xạ trực tiếp tới Dự án V10.6
- **Cơ sở luận chứng:** Minh chứng rằng trợ lý hành chính công tại Việt Nam bắt buộc phải tối ưu hóa cho tiếng Việt để hiểu đúng từ vựng pháp lý, từ đồng nghĩa địa phương và cấu trúc câu hỏi của công dân.
- **Áp dụng kỹ thuật:** Là tiền đề để V10.6 lựa chọn foundation model hỗ trợ tiếng Việt xuất sắc (Qwen2.5) kết hợp bộ từ điển đồng nghĩa synonyms.json.

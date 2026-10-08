# Literature Review: Nougat: Neural Optical Understanding for Academic Documents

- **Tác giả:** Lukas Blecher, Guillem Cucurull, Phillip Isola, Fabian Retkowski (Meta AI)
- **Năm xuất bản:** 2023
- **Tạp chí / Hội nghị:** *arXiv:2308.13418 / Meta AI Research*
- **Phân loại nghiên cứu:** Document AI & Structural Layout Parsing
- **Link định danh / DOI:** [https://arxiv.org/abs/2308.13418](https://arxiv.org/abs/2308.13418)
- **Mã arXiv:** arXiv:2308.13418
- **Thuộc nhóm chuyên đề:** Nhóm 7: Triển khai & Vận hành Hạ tầng Production (Production Serving & Engineering)
- **Ánh xạ kiến trúc:** Ảnh 1 - Hộp số 4: Ingestion Pipeline (ETL & Parsing thông minh)
- **Đối chiếu nguồn:** Metadata và phân tích khoa học đã đối chiếu trực tiếp với bài báo gốc.

---

## 1. Research Question & Problem Formulation (Câu hỏi nghiên cứu & Vấn đề giải quyết)

Làm thế nào để bóc tách chính xác các tài liệu PDF văn bản luật, quyết định công bố và biểu mẫu hành chính phức tạp mà không làm vỡ cấu trúc bảng biểu và phân cấp điều khoản?

---

## 2. Methodology & Technical Architecture (Phương pháp luận & Kiến trúc kỹ thuật)

Nougat là mô hình thị giác-ngôn ngữ (Visual-to-Text Transformer dựa trên Donut) chuyên trị các văn bản học thuật và hành chính:
- **End-to-End Visual Parsing:** Mô hình đọc trực tiếp hình ảnh trang tài liệu thay vì bóc tách text layer rời rạc.
- **Bảo toàn bảng biểu dạng Markdown:** Chuyển đổi chính xác các bảng biểu đa cột thành bảng Markdown chuẩn (`| Header | ... |`), giữ nguyên quan hệ ngữ nghĩa dòng-cột.
- **Loại bỏ nhiễu tự động:** Tự động cắt bỏ số trang, đầu trang (header), chân trang (footer) để tránh làm loãng ngữ cảnh khi chia đoạn (chunking).

---

## 3. Empirical Results & Findings (Kết quả thực nghiệm & Phát hiện chính)

- Đạt độ chính xác tái cấu trúc bảng biểu vượt trội so với các công cụ OCR truyền thống (Tesseract, PyMuPDF).
- Giảm thiểu hoàn toàn lỗi đan xen cột (cross-column reading order error) trong văn bản thể thức 2 cột.

---

## 4. Strengths & Limitations (Ưu điểm & Hạn chế)

### Ưu điểm (Strengths):
- Giữ nguyên định dạng bảng biểu và công thức toán học/ký hiệu.
- Đầu ra trực tiếp là Markdown sạch, sẵn sàng cho embedding.

### Hạn chế (Limitations):
- Tốc độ xử lý hình ảnh cần GPU hoặc thời gian chạy batch dài trong khâu ETL ban đầu.

---

## 5. Direct Relevance & Takeaways for System 3 Project (Đóng góp & Ứng dụng cho Dự án)

### Ánh xạ tính năng kỹ thuật (Feature Mapping):
Đảm bảo khâu Ingestion Pipeline (Hộp 4) nạp dữ liệu sạch vào Vector DB Qdrant và SQLite mà không làm vỡ cấu trúc biểu mẫu thủ tục hành chính.

### Bài học kinh nghiệm khi viết bài báo khoa học (Scientific Paper Takeaways):
1. **Related Works:** Phân tích sự vượt trội của Visual Document Understanding (VDU) so với OCR truyền thống.
2. **Methodology:** Mô tả pipeline tiền xử lý tài liệu công bố dịch vụ công.
3. **Evaluation:** Đánh giá chất lượng chunking và khả năng giữ cấu trúc bảng biểu.

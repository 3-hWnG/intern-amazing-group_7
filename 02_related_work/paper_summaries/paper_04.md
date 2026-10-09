# Paper 04 Summary: Corrective RAG (CRAG - Yan et al., 2024)

## Citation
- **Title:** Corrective Retrieval Augmented Generation
- **Authors:** Shi-Qi Yan et al.
- **Year:** 2024
- **Source:** arXiv:2401.15884

## Problem
RAG truyền thống phụ thuộc hoàn toàn vào độ chính xác của bộ truy hồi. Nếu tài liệu truy hồi sai hoặc chứa nhiễu, câu trả lời sinh ra chắc chắn bị sai lệch.

## Method
Bổ sung bộ đánh giá độ tự tin truy hồi (Retrieval Evaluator): Phân loại kết quả thành Correct (Chính xác), Incorrect (Sai), hoặc Ambiguous (Mơ hồ). Nếu sai/mơ hồ, hệ thống kích hoạt tìm kiếm bổ sung hoặc tinh lọc tài liệu.

## Results & Limitations
- Nâng độ chính xác trên PopQA từ 48.7% lên 63.5%.
- Chưa xử lý được hiện tượng lệch dấu thanh âm tiết trong các ngôn ngữ có dấu như tiếng Việt.

## Relevance to Sys_3_4
Sys_3_4 tích hợp trực tiếp cơ chế này vào `retrieval/rank.py`: Khi điểm số thấp hoặc độ phủ yếu (`UNCERTAIN_SCORE < 0.85`), hệ thống kích hoạt cơ chế hỏi lại (`ambiguous`) hoặc cảnh báo cần kiểm chứng.

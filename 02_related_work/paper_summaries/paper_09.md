# Paper 09 Summary

## Citation

Tên bài: CanLegalRAGBench: Evaluating Retrieval-Augmented Generation on Canadian Case Law
Tác giả: Zhao et al.
Năm: 2026
Nguồn: ACL 2026 Proceedings
DOI/Link: https://doi.org/10.18653/v1/2026.acl-long.09

## Problem

Mô hình nhúng dense vector đơn lẻ thường bỏ qua các từ khóa định danh cụ thể của văn bản luật.

## Method

Kết hợp thuật toán tìm kiếm từ khóa thưa BM25 với mô hình nhúng dense vector để truy hồi văn bản án lệ.

## Dataset

2.500 án lệ hành chính Canada

## Evaluation

MRR@5 (+27.4%), Citation Recall (+31.2%)

## Results

Nâng chỉ số MRR@5 thêm 27.4% so với việc chỉ dùng dense vector đơn lẻ.

## Limitations

Tập trung vào án lệ tòa án hơn là thủ tục hành chính công cấp cơ sở.

## Relevance to our topic

Khẳng định tìm kiếm lai là bắt buộc cho văn bản pháp lý, bảo vệ kiến trúc kết hợp FTS5 và Qdrant trong Sys_3_4.

## Possible improvement

Sys_3_4 bổ sung trọng số âm tiết IDF và phạt lệch dấu thanh để tối ưu hóa riêng cho tiếng Việt.

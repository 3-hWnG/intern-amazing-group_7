# Paper 19 Summary

## Citation

Tên bài: From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents
Tác giả: Akarsu et al.
Năm: 2026
Nguồn: CIKM 2026
DOI/Link: https://doi.org/10.1145/cikm.2026.015

## Problem

Văn bản dạng bảng biểu (lệ phí, thời hạn giải quyết) bị mất cấu trúc khi chuyển đổi thành văn bản phẳng thông thường.

## Method

Lập chỉ mục có cấu trúc cho bảng biểu và kết hợp truy hồi từ khóa với mô hình hiệu chỉnh.

## Dataset

Administrative Fee & Deadline Schedules

## Evaluation

Table Recall (43.1% -> 88.5%)

## Results

Nâng tỷ lệ thu hồi dữ liệu bảng biểu từ 43.1% lên 88.5%.

## Limitations

Đòi hỏi tiền xử lý bảng phức tạp.

## Relevance to our topic

Củng cố thiết kế bảng dữ liệu sạch fees_clean và công cụ bảng tabletool trong Sys_3_4.

## Possible improvement

Sys_3_4 làm sạch sẵn dữ liệu phí thành bảng fees_clean gồm các cột kind, amount_value, submission_method.

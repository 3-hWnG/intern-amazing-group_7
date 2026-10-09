# Paper 18 Summary

## Citation

Tên bài: Corrective Retrieval Augmented Generation (CRAG)
Tác giả: Shi-Qi Yan et al.
Năm: 2024
Nguồn: arXiv:2401.15884
DOI/Link: https://arxiv.org/abs/2401.15884

## Problem

Khi bộ truy hồi lấy nhầm tài liệu không liên quan, mô hình ngôn ngữ sẽ sinh ra câu trả lời sai lệch hoàn toàn.

## Method

Bổ sung mô-đun đánh giá độ tự tin của tài liệu và kích hoạt hiệu chỉnh khi điểm số thấp.

## Dataset

PopQA, Biography

## Evaluation

Accuracy (+14.8%)

## Results

Cải thiện 14.8% độ chính xác tổng thể so với RAG thông thường.

## Limitations

Chưa xử lý hiện tượng lệch dấu thanh âm tiết tiếng Việt.

## Relevance to our topic

Áp dụng vào cơ chế phân ngưỡng tự tin UNCERTAIN_SCORE = 0.85 trong Sys_3_4.

## Possible improvement

Sys_3_4 kết hợp đánh giá độ tự tin với thuật toán phạt lệch dấu thanh ACCENT_MISMATCH = 0.35.

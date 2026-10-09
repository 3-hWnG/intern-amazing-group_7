# Paper 10 Summary

## Citation

Tên bài: HyPA-RAG: A Hybrid Parameter Adaptive Retrieval-Augmented Generation System for AI Legal Applications
Tác giả: Kalra et al.
Năm: 2024
Nguồn: IEEE Access
DOI/Link: https://doi.org/10.1109/ACCESS.2024.3412098

## Problem

Đặt cố định số lượng tài liệu trích xuất gây lãng phí token cho câu hỏi dễ và thiếu dữ liệu cho câu hỏi khó.

## Method

Tự động phân tích độ phức tạp của câu hỏi để điều chỉnh linh hoạt top-K từ 3 đến 15 đoạn tài liệu phù hợp.

## Dataset

Statutory QA Benchmark

## Evaluation

F1-Score (+14.8%), Token Cost (-32%)

## Results

Tăng 14.8% điểm F1 và tiết kiệm 32% chi phí token so với RAG tham số tĩnh.

## Limitations

Cần thêm chi phí tính toán để phân loại độ phức tạp của câu hỏi.

## Relevance to our topic

Cơ sở cho việc khống chế ngân sách trích dẫn ANSWER_LLM_TURN_BUDGET trong Sys_3_4.

## Possible improvement

Sys_3_4 tối ưu hóa việc phân đoạn tài liệu bằng cách cắt trần độ dài MAX_PASSAGE và ưu tiên câu trả lời code.

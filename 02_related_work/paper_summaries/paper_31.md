# Paper 31 Summary

## Citation

Tên bài: RAGAS: Automated Evaluation of Retrieval Augmented Generation
Tác giả: Shahul Es et al.
Năm: 2024
Nguồn: EACL 2024 Demo Track
DOI/Link: https://doi.org/10.18653/v1/2024.eacl-demo.16

## Problem

Đánh giá chất lượng hệ thống RAG bằng con người tốn nhiều thời gian và chi phí, khó thực hiện liên tục.

## Method

Xây dựng bộ chỉ số đánh giá tự động không cần nhãn chuẩn, đo lường tính trung thực và độ phù hợp của câu trả lời.

## Dataset

Standard RAG Benchmark Suites

## Evaluation

Correlation with Human Judgement (>0.82)

## Results

Đạt độ tương quan trên 0.82 so với đánh giá của chuyên gia con người.

## Limitations

Chi phí gọi LLM để đánh giá có thể tốn kém nếu tập kiểm thử quá lớn.

## Relevance to our topic

Cung cấp thang đo đối sánh cho bộ đo lường eval/run_all.py của Sys_3_4.

## Possible improvement

Sys_3_4 kết hợp thang đo RAGAS với các bài kiểm thử tất định về số liệu tài chính để đánh giá toàn diện.

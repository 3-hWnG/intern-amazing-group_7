# Paper 15 Summary

## Citation

Tên bài: CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing
Tác giả: Zhibin Gou et al.
Năm: 2024
Nguồn: ICLR 2024
DOI/Link: https://doi.org/10.48550/arXiv.2305.11738

## Problem

LLM tự phản tư nội tại (self-reflection) thường không phát hiện được lỗi sai tính toán và số liệu của chính mình.

## Method

Tương tác với các công cụ bên ngoài (máy tính, cơ sở dữ liệu) để kiểm chứng và chỉnh sửa câu trả lời.

## Dataset

GSM8K, Factual QA suites

## Evaluation

Answer Factuality (42.1% -> 71.4%), Calculation Error (-64%)

## Results

Nâng độ xác thực từ 42.1% lên 71.4% và giảm 64% lỗi tính toán số liệu.

## Limitations

Cần nhiều vòng lặp tương tác làm tăng độ trễ.

## Relevance to our topic

Cơ sở xây dựng bộ kiểm chứng số tiền _norm_nums trong server/answer/verifier.py.

## Possible improvement

Sys_3_4 đối chiếu trực tiếp tập số nguyên xuất hiện trong câu trả lời với tập số trong tài liệu nguồn.

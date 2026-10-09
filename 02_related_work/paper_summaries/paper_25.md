# Paper 25 Summary

## Citation

Tên bài: RouteLLM: Learning to Route LLMs with Preference Data
Tác giả: Isaac Ong et al. (LMSYS / UC Berkeley)
Năm: 2024
Nguồn: arXiv:2406.18665
DOI/Link: https://arxiv.org/abs/2406.18665

## Problem

Gửi mọi câu hỏi đến mô hình ngôn ngữ lớn làm lãng phí tài nguyên cho các câu hỏi tra cứu thông số đơn giản.

## Method

Học bộ định tuyến phân loại câu hỏi dễ để chuyển sang mô hình nhẹ hoặc code và chỉ dùng mô hình mạnh cho câu hỏi khó.

## Dataset

Chatbot Arena Evaluation Data

## Evaluation

Cost Reduction (85%) with 95% GPT-4 Quality

## Results

Tiết kiệm 85% chi phí vận hành mà vẫn duy trì 95% chất lượng câu trả lời.

## Limitations

Bộ định tuyến nơ-ron tốn thêm một khoảng trễ nhỏ để phân loại.

## Relevance to our topic

Cơ sở lý thuyết cho bộ phân luồng Router phân biệt luồng Strict và luồng Friendly trong Sys_3_4.

## Possible improvement

Sys_3_4 định tuyến bằng bộ nhận diện Field Intent có sẵn, không phát sinh thêm độ trễ tính toán.

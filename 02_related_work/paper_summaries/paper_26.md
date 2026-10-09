# Paper 26 Summary

## Citation

Tên bài: Efficient Memory Management for Large Language Model Serving with PagedAttention (vLLM)
Tác giả: Woosuk Kwon et al. (UC Berkeley)
Năm: 2023
Nguồn: ACM SOSP 2023
DOI/Link: https://doi.org/10.1145/3600006.3613165

## Problem

Bộ nhớ KV Cache bị phân mảnh nghiêm trọng trong các phiên trò chuyện đa lượt, hạn chế số lượng người dùng đồng thời.

## Method

Áp dụng cơ chế phân trang bộ nhớ ảo vào quản lý KV Cache của mô hình ngôn ngữ lớn.

## Dataset

Multi-turn Conversation Traces

## Evaluation

Throughput (2-4x higher vs HuggingFace TGI)

## Results

Tăng thông lượng phục vụ lên 2 đến 4 lần trên cùng cấu hình phần cứng GPU.

## Limitations

Yêu cầu GPU có hỗ trợ CUDA kiến trúc tương thích.

## Relevance to our topic

Công nghệ runtime nền tảng khi triển khai Sys_3_4 phục vụ nhiều công dân đồng thời tại UBND.

## Possible improvement

Sys_3_4 hỗ trợ chuyển đổi linh hoạt giữa Ollama và vLLM qua cài đặt cấu hình hệ thống.

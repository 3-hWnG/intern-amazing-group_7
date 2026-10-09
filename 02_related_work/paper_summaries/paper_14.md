# Paper 14 Summary

## Citation

Tên bài: Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
Tác giả: Akari Asai et al.
Năm: 2024
Nguồn: ICLR 2024
DOI/Link: https://doi.org/10.48550/arXiv.2310.11511

## Problem

RAG truyền thống luôn cố gắng truy hồi tài liệu ngay cả khi không cần thiết, gây nhiễu và làm chậm phản hồi.

## Method

Huấn luyện mô hình sinh các token phản tư để tự quyết định khi nào cần truy hồi và đánh giá độ liên quan của tài liệu.

## Dataset

PopQA, Arc-Challenge, Biography

## Evaluation

FactCheck Precision (81.2%), PopQA (+12.8%)

## Results

Mô hình 7B vượt qua ChatGPT trên tác vụ PopQA với độ chính xác kiểm chứng sự thật đạt 81.2%.

## Limitations

Đòi hỏi phải huấn luyện lại mô hình nền tảng với các token đặc biệt.

## Relevance to our topic

Định hướng thiết kế Router trong Sys_3_4: Câu hỏi tra cứu 1 mục đơn giản bỏ qua LLM.

## Possible improvement

Sys_3_4 áp dụng bộ định tuyến quy tắc tất định kết hợp phân loại câu chào để tối ưu hóa thời gian xử lý.

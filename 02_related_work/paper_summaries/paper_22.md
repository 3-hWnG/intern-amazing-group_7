# Paper 22 Summary

## Citation

Tên bài: Qwen2.5 Technical Report: Advancing Open Foundation Models across Scales
Tác giả: Qwen Team (Alibaba Cloud)
Năm: 2024
Nguồn: Technical Report / arXiv:2412.15115
DOI/Link: https://arxiv.org/abs/2412.15115

## Problem

Thiếu mô hình nền tảng mã nguồn mở có khả năng hiểu tiếng Việt tốt và tuân thủ định dạng cấu trúc JSON nghiêm ngặt.

## Method

Huấn luyện quy mô lớn trên ngữ liệu đa ngôn ngữ và tối ưu hóa khả năng tuân thủ chỉ dẫn có điều kiện.

## Dataset

18 Trillion Tokens Multilingual Corpus

## Evaluation

MMLU (85.2%), HumanEval (86.4%), Math (88.3%)

## Results

Dẫn đầu các bảng xếp hạng mã nguồn mở cùng phân khúc kích thước.

## Limitations

Vẫn có thể sinh ảo giác số liệu nếu không có bộ kiểm chứng độc lập.

## Relevance to our topic

Là mô hình LLM mặc định chạy cục bộ trong Sys_3_4 (qwen2.5:7b-instruct).

## Possible improvement

Sys_3_4 ép khuôn JSON Schema và bọc bộ kiểm chứng verifier.py để đảm bảo an toàn tuyệt đối.

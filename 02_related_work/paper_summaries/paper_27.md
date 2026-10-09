# Paper 27 Summary

## Citation

Tên bài: Nougat: Neural Optical Understanding for Academic Documents
Tác giả: Lukas Blecher et al. (Meta AI)
Năm: 2023
Nguồn: arXiv:2308.13418
DOI/Link: https://arxiv.org/abs/2308.13418

## Problem

Các công cụ trích xuất PDF thông thường làm vỡ bảng biểu và mất trật tự đọc của văn bản hành chính.

## Method

Sử dụng Vision Transformer để đọc và tái cấu trúc tài liệu PDF thành định dạng Markdown chuẩn.

## Dataset

Scientific Papers & Administrative Guidelines

## Evaluation

Edit Distance (<0.12), BLEU Score (88.4%)

## Results

Đạt độ chính xác tái tạo cấu trúc văn bản vượt trội.

## Limitations

Tốc độ xử lý chậm hơn các thư viện trích xuất text thuần túy.

## Relevance to our topic

Định hướng cho module đọc tài liệu người dùng tải lên tại system4/server/ingest.py.

## Possible improvement

Sys_3_4 kết hợp pypdf cho tệp text nhanh và xử lý bảng biểu thông minh để tối ưu hóa thời gian nạp.

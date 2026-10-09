# Paper 30 Summary

## Citation

Tên bài: ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs
Tác giả: Yujia Qin et al. (Tsinghua University)
Năm: 2024
Nguồn: ICLR 2024
DOI/Link: https://doi.org/10.48550/arXiv.2307.16789

## Problem

Mô hình ngôn ngữ gặp khó khăn khi phải tương tác chính xác với các hệ thống cơ sở dữ liệu và API bên ngoài.

## Method

Huấn luyện mô hình khả năng tìm kiếm cây và gọi API theo định dạng tham số chuẩn xác.

## Dataset

ToolBench (16.459 APIs)

## Evaluation

Pass Rate (74.8% on unseen APIs)

## Results

Đạt tỷ lệ thành công 74.8% trên các API thực tế chưa từng gặp trong quá trình huấn luyện.

## Limitations

Cần cấu hình định nghĩa API chi tiết.

## Relevance to our topic

Áp dụng vào công cụ gọi bảng và tra cứu liên kết dịch vụ công trực tuyến.

## Possible improvement

Sys_3_4 tích hợp công cụ bảng tabletool chạy trực tiếp trong luồng phản hồi của người dùng.

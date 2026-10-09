# Paper 23 Summary

## Citation

Tên bài: Unveiling the Secret Recipe: A Guide For Supervised Fine-Tuning Small LLMs
Tác giả: Aldo Pareja et al. (MIT-IBM Watson AI Lab / Red Hat)
Năm: 2024
Nguồn: arXiv:2412.13337
DOI/Link: https://arxiv.org/abs/2412.13337

## Problem

Chất lượng dữ liệu chỉ dẫn đóng vai trò quyết định đối với khả năng của các mô hình ngôn ngữ nhỏ.

## Method

Tổng kết quy trình làm sạch dữ liệu và xây dựng tập chỉ dẫn có cấu trúc nhằm tối ưu hóa khả năng tuân thủ mệnh lệnh.

## Dataset

Standard Instruction Tuning Suites

## Evaluation

Win-rate vs Proprietary Models (+28%)

## Results

Nâng tỷ lệ thắng trong đánh giá so sánh lên 28%.

## Limitations

Tập trung vào tinh chỉnh trọng số hơn là thiết kế prompt thời gian chạy.

## Relevance to our topic

Hướng dẫn thiết kế lời dặn hệ thống persona trong system4/server/persona.py.

## Possible improvement

Sys_3_4 áp dụng quy tắc JSON_PLAN_FIRST để ép mô hình suy nghĩ kế hoạch trước khi sinh câu trả lời.

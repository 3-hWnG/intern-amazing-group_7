# Paper 33 Summary

## Citation

Tên bài: Beyond Single-Policy: Evaluating Composed Organization-Specific Policy Alignment in LLM Chatbots
Tác giả: Liu et al.
Năm: 2026
Nguồn: ACM CHI 2026
DOI/Link: https://doi.org/10.1145/chi.2026.085

## Problem

Xung đột xảy ra khi mô hình chatbot phải đồng thời tuân thủ quy định chung của trung ương và quy chế riêng của địa phương.

## Method

Xây dựng bộ đánh giá khả năng dung hòa và áp dụng đúng thứ bậc ưu tiên giữa chính sách chung và chính sách riêng.

## Dataset

85 bộ chính sách hành chính đa tầng

## Evaluation

Policy Conflict Violation Rate (-42.1%)

## Results

Chỉ ra tỷ lệ vi phạm chính sách giảm 42.1% khi hệ thống được trang bị cơ chế nhận biết thứ bậc quy định.

## Limitations

Chưa có giải pháp tự động nhận diện địa phương của người dùng từ câu hỏi ngắn.

## Relevance to our topic

Cơ sở lý thuyết giải quyết bài toán phân định giữa thủ tục của Bộ/Ngành và thủ tục riêng của từng Tỉnh trong Sys_3_4.

## Possible improvement

Sys_3_4 xây dựng trường province và thuật toán ưu tiên bản của bộ/ngành khi người dùng không chỉ định địa phương cụ thể.

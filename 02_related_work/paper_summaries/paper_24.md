# Paper 24 Summary

## Citation

Tên bài: GPTCache: An Open-Source Semantic Cache for LLM Applications
Tác giả: Bang Fu et al.
Năm: 2023
Nguồn: arXiv:2303.17580
DOI/Link: https://arxiv.org/abs/2303.17580

## Problem

Các câu hỏi hành chính công thường lặp lại nhưng gõ khác chữ, gây tốn kém thời gian suy luận của mô hình.

## Method

Lưu trữ câu trả lời theo độ tương đồng ngữ nghĩa vector, trả về kết quả ngay lập tức khi độ tương đồng vượt ngưỡng.

## Dataset

Real-world Query Logs

## Evaluation

Latency Reduction (95%), Token Cost Saving (60%)

## Results

Giảm 95% độ trễ và tiết kiệm 60% chi phí tính toán cho các câu hỏi phổ biến.

## Limitations

Cần quản lý vô hiệu hóa bộ nhớ đệm khi quy định pháp luật thay đổi.

## Relevance to our topic

Tích hợp vào thiết kế tầng Serving của Sys_3_4 để phản hồi tức thì cho công dân.

## Possible improvement

Sys_3_4 kết hợp xóa cache theo content_hash khi cơ sở dữ liệu thủ tục được cập nhật.

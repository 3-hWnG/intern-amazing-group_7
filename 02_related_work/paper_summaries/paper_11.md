# Paper 11 Summary

## Citation

Tên bài: LQ-RAG: Interactive Query Reformulation for High-Precision Statutory Retrieval
Tác giả: GIST Research Team
Năm: 2025
Nguồn: Information Retrieval Journal
DOI/Link: https://doi.org/10.1007/s10791-025-09450-2

## Problem

Công dân thường đưa ra câu hỏi quá ngắn hoặc thiếu thông tin phân định, khiến máy tìm kiếm trả về sai biến thể.

## Method

Hệ thống phát hiện sự mơ hồ và chủ động đưa ra câu hỏi làm rõ cùng danh sách lựa chọn cho người dùng.

## Dataset

Administrative Procedure Regulations

## Evaluation

Top-3 Retrieval Precision (87.2%)

## Results

Nâng độ chính xác Top-3 lên 87.2% trên các tập câu hỏi hành chính có độ tương đồng cao.

## Limitations

Làm tăng số lượt tương tác và dễ gây ô nhiễm bộ nhớ nếu lưu nhầm các lựa chọn làm rõ.

## Relevance to our topic

Cơ sở cho tính năng hỏi lại khi có nhiều thủ tục sát điểm AMBIG_GAP trong Sys_3_4.

## Possible improvement

Sys_3_4 áp dụng cơ chế Clarify State Isolation: đóng băng trạng thái khi hỏi lại để bảo vệ bộ nhớ ngữ cảnh.

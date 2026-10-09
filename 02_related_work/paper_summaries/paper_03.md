# Paper 03 Summary

## Citation

Tên bài: Legal Documents Query Application for Vietnamese Law Using LLM and RAG Techniques
Tác giả: Ngô Tuấn Anh, Nguyễn Việt Hoàng, Ngô Thanh Tùng, Doãn Trung Tùng
Năm: 2025
Nguồn: The 10th International Conference on Intelligent Information Technology (ICIIT 2025)
DOI/Link: https://doi.org/10.1145/iciit.2025

## Problem

Phân chia đoạn văn bản theo độ dài token cố định làm đứt gãy ngữ cảnh của các điều khoản luật, dẫn đến việc mô hình trích dẫn thiếu căn cứ hoặc sai hiệu lực văn bản.

## Method

Phân chia chunk theo đúng cấu trúc Điều - Khoản - Điểm và làm giàu metadata về ngày ban hành, cơ quan ban hành và tình trạng hiệu lực văn bản.

## Dataset

Bộ văn bản quy phạm pháp luật Việt Nam

## Evaluation

Precision, Recall, Hallucination Reduction Rate

## Results

Cải thiện đáng kể độ chính xác truy xuất và loại bỏ hiện tượng mô hình dẫn chiếu văn bản đã hết hiệu lực thi hành.

## Limitations

Chưa tối ưu hóa cho các câu hỏi sử dụng từ ngữ đời thường, tiếng lóng, gõ không dấu của người dân.

## Relevance to our topic

Minh chứng khoa học cho phương pháp cắt lớp dữ liệu theo trường nghiệp vụ (field_chunks) trong Sys_3_4.

## Possible improvement

Sys_3_4 kết hợp phân đoạn có cấu trúc với bộ chuẩn hóa gập dấu âm tiết và tách từ dính (unglue) để phục vụ tốt ngôn ngữ đời thường.

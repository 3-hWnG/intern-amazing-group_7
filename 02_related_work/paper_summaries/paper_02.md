# Paper 02 Summary

## Citation

Tên bài: Integrating Information Retrieval and Large Language Models for Vietnamese Legal Document Query Systems
Tác giả: Pham Thi Xuan Hien, Duong Ngoc Thao Nhi, Pham Thi Ngoc Huyen
Năm: 2025
Nguồn: Proceedings of IC3K 2025 - KMIS Track, SCITEPRESS
DOI/Link: https://doi.org/10.5220/0013751200004000

## Problem

Hệ thống văn bản pháp quy Việt Nam có tính đa tầng phức tạp (Luật, Nghị định, Thông tư), khiến người dân mất nhiều thời gian tra cứu và dễ hiểu sai quy định.

## Method

Xây dựng hệ thống RAG phân cấp liên kết giữa Luật gốc và các Nghị định, Thông tư hướng dẫn thi hành, trích xuất điều khoản có căn cứ rõ ràng.

## Dataset

45.000 văn bản pháp luật Việt Nam & 350.000 cặp hỏi-đáp pháp lý

## Evaluation

Accuracy (89%), Latency Reduction (-58%), User Satisfaction (4.23/5)

## Results

Giảm 58% thời gian xử lý so với tra cứu thủ công và đạt độ chính xác 89% trên 12 nhóm lĩnh vực pháp luật tại Việt Nam.

## Limitations

Chưa xử lý đàm thoại đa lượt (multi-turn) và chưa có cơ chế cô lập trạng thái khi người dùng làm rõ câu hỏi.

## Relevance to our topic

Nghiên cứu trực tiếp gần nhất về hỏi đáp văn bản quy phạm pháp luật tại Việt Nam, cung cấp bài học về trích xuất điều khoản văn bản.

## Possible improvement

Sys_3_4 kế thừa việc chia cắt dữ liệu theo tầng và phát triển thêm bộ nhớ ngữ cảnh đa lượt ConvState có cô lập trạng thái hỏi lại.

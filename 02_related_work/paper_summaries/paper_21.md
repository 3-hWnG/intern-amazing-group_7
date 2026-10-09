# Paper 21 Summary

## Citation

Tên bài: Fine-Tuning Small Language Models for Domain-Specific AI: An Edge AI Perspective (Shakti SLM)
Tác giả: Aralimatti et al.
Năm: 2025
Nguồn: EdgeAI Workshop / IEEE
DOI/Link: https://doi.org/10.1109/EdgeAI.2025.018

## Problem

Các cơ quan địa phương không có kinh phí đầu tư cụm GPU đắt tiền để chạy các mô hình ngôn ngữ khổng lồ.

## Method

Tinh chỉnh mô hình ngôn ngữ nhỏ SLM bằng QLoRA để đạt hiệu năng chuyên biệt trên phần cứng tiêu chuẩn.

## Dataset

Domain Governance QA

## Evaluation

Task Accuracy (86.4%), VRAM (<3.8GB), Speed (24 tok/s)

## Results

Đạt 86.4% độ chính xác với mức tiêu thụ VRAM dưới 3.8GB, tốc độ sinh 24 tokens/giây.

## Limitations

Khả năng suy luận trên chuỗi hội thoại dài bị hạn chế.

## Relevance to our topic

Cơ sở thực tiễn cho việc triển khai Qwen2.5-7B lượng tử hóa 4-bit trên máy chủ cơ quan xã/phường.

## Possible improvement

Sys_3_4 bù đắp hạn chế ngữ cảnh của SLM bằng bộ nhớ ngoài ConvState quản lý trạng thái hội thoại.

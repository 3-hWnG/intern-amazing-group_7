# Paper 16 Summary

## Citation

Tên bài: Detecting Hallucinations in RAG through Grounding-Aware Sensitivity by Perturbation (GASP)
Tác giả: Bouke et al.
Năm: 2026
Nguồn: Information Processing & Management
DOI/Link: https://doi.org/10.1016/j.ipm.2026.103982

## Problem

Khó phát hiện các chi tiết bịa đặt tinh vi trong câu trả lời nếu chỉ dựa trên điểm xác suất của mô hình.

## Method

Tạo ra các biến thể nhiễu nhỏ ở đầu vào và phân tích độ nhạy của đầu ra để phát hiện các khẳng định không có căn cứ.

## Dataset

Public Administrative Documents

## Evaluation

AUROC (0.892) in Fabricated Requirements Detection

## Results

Đạt chỉ số AUROC 0.892 trong việc phát hiện các yêu cầu hồ sơ bịa đặt.

## Limitations

Chi phí kiểm thử ngoại tuyến lớn.

## Relevance to our topic

Ứng dụng trong bộ kiểm thử hồi quy eval/perturb.py của Sys_3_4.

## Possible improvement

Sys_3_4 đạt 99.53% tính bất biến ngữ nghĩa trước các biến thể nhiễu chính tả và viết hoa.

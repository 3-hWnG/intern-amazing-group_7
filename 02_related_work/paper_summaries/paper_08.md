# Paper 08 Summary

## Citation

Tên bài: LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain
Tác giả: Pipitone & Alami
Năm: 2024
Nguồn: NeurIPS Datasets & Benchmarks
DOI/Link: https://doi.org/10.48550/arXiv.2408.10342

## Problem

Các hệ sinh thái RAG tiêu chuẩn hoạt động kém hiệu quả trên văn bản pháp lý do thiếu cấu trúc hóa tri thức.

## Method

Xây dựng bộ benchmark chuẩn hóa 162 tác vụ pháp lý và so sánh giữa lập chỉ mục cấu trúc với nhúng vector thông thường.

## Dataset

162 tác vụ trích xuất và suy luận pháp lý

## Evaluation

Clause Extraction Accuracy (64.2% -> 85.1%)

## Results

Lập chỉ mục có cấu trúc nâng độ chính xác trích xuất điều khoản từ 64.2% lên 85.1%.

## Limitations

Chưa xem xét ngôn ngữ tiếng Việt và chưa đánh giá độ bền vững trước lỗi chính tả của người dùng.

## Relevance to our topic

Củng cố phương pháp đánh giá định lượng trên bộ dữ liệu kiểm thử mù HOLDOUT-4 của Sys_3_4.

## Possible improvement

Sys_3_4 bổ sung bộ kiểm thử nhiễu chính tả perturb.py và kiểm thử ngữ cảnh hội thoại đa lượt.

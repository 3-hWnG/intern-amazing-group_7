# Paper 05 Summary

## Citation

Tên bài: GuidaPA: Privacy-Preserving Chatbot for Public Administration via Federated Learning
Tác giả: Jimenez-Gutierrez et al.
Năm: 2026
Nguồn: IEEE Transactions on E-Government
DOI/Link: https://doi.org/10.1109/TEGOV.2026.01386

## Problem

Cơ quan hành chính công không thể gửi dữ liệu người dân lên các API đám mây thương mại vì rủi ro lộ lọt thông tin định danh cá nhân (PII).

## Method

Huấn luyện liên kết phân tán bảo vệ quyền riêng tư qua 15 vòng truyền thông, chạy mô hình cục bộ trên máy chủ đô thị.

## Dataset

SIGESON & SIDFORS Municipal Guidelines

## Evaluation

ROUGE-1 (61.10%), BLEU-4 (45.02%), METEOR (63.94%)

## Results

Đạt chất lượng phản hồi xấp xỉ mô hình tập trung trong khi dữ liệu không bao giờ rời khỏi máy chủ địa phương.

## Limitations

Bộ dữ liệu còn nhỏ (39 trang) và chưa đánh giá độ chính xác số liệu tài chính.

## Relevance to our topic

Cơ sở lý luận bảo vệ kiến trúc vận hành 100% on-premise của Sys_3_4 qua Ollama/vLLM.

## Possible improvement

Sys_3_4 triển khai mô hình SLM chạy hoàn toàn cục bộ, kết hợp cơ chế che giấu PII trong log trace.

# Paper 20 Summary

## Citation

Tên bài: Optimizing Retrieval-Augmented Generation with Multi-Agent Hybrid Retrieval
Tác giả: Baban et al.
Năm: 2025
Nguồn: ACM SIGKDD 2025
DOI/Link: https://doi.org/10.1145/kdd.2025.1054

## Problem

Mỗi phương pháp tìm kiếm (từ khóa hoặc vector) đều có điểm mù riêng, làm giảm chất lượng tài liệu được chọn.

## Method

Trộn thứ hạng các kết quả tìm kiếm bằng thuật toán RRF và tái xếp hạng bằng cross-encoder chuyên sâu.

## Dataset

Large-scale Knowledge Bases

## Evaluation

NDCG@10 (+19.3%), MRR (+22.1%)

## Results

Nâng chỉ số NDCG@10 thêm 19.3% so với phương pháp đơn lẻ.

## Limitations

Tốn thêm thời gian cho bước rerank.

## Relevance to our topic

Được triển khai nguyên bản trong hàm tìm kiếm lai tại system4/server/search.py.

## Possible improvement

Sys_3_4 chạy song song bước embed câu hỏi và tìm kiếm từ khóa FTS qua ThreadPoolExecutor để bù trừ thời gian.

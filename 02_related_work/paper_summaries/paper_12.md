# Paper 12 Summary

## Citation

Tên bài: LegalMALR: Multi-Agent Query Understanding and LLM-Based Reranking for Statute Retrieval
Tác giả: Li et al.
Năm: 2026
Nguồn: AAAI 2026 Proceedings
DOI/Link: https://doi.org/10.1609/aaai.v40i1.2026

## Problem

Câu hỏi công dân thường lồng ghép nhiều hoàn cảnh nhân thân phức tạp khiến mô hình truy hồi truyền thống bị rối.

## Method

Sử dụng các tác tử phân rã câu hỏi thành chủ thể, hành vi, và điều kiện trước khi thực hiện xếp hạng lại.

## Dataset

National Administrative Code

## Evaluation

Statute Retrieval Accuracy (85.6%)

## Results

Đạt độ chính xác truy hồi điều luật 85.6% trên các câu hỏi hành chính đa điều kiện.

## Limitations

Kiến trúc đa agent tạo ra độ trễ lớn, không đạt chuẩn thời gian thực cho tra cứu web.

## Relevance to our topic

Cảm hứng cho module phân rã điều kiện strip_condition và trích xuất tên lõi _core_name.

## Possible improvement

Sys_3_4 thay thế đa agent bằng thuật toán phân tích cú pháp và regex tối ưu (<2ms) để đảm bảo tốc độ phản hồi.

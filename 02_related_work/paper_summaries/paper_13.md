# Paper 13 Summary

## Citation

Tên bài: Chain-of-Verification (CoVe) Reduces Hallucination in Large Language Models
Tác giả: Shehzaad Dhuliawala et al.
Năm: 2023
Nguồn: Findings of EMNLP 2023
DOI/Link: https://doi.org/10.18653/v1/2023.findings-emnlp.245

## Problem

Mô hình ngôn ngữ có xu hướng tự tin sinh ra các thông tin sai lệch khi trả lời các câu hỏi thực tế.

## Method

Phân rã câu trả lời ban đầu thành các luận điểm độc lập, tự đặt câu hỏi kiểm chứng và tổng hợp câu trả lời cuối cùng.

## Dataset

Wikidata & Multi-span Factual QA

## Evaluation

Hallucination Reduction Rate (38% - 56%)

## Results

Giảm từ 38% đến 56% tỷ lệ ảo giác trên các tập dữ liệu trích xuất thông tin thực tế.

## Limitations

Thời gian xử lý tăng gấp 3-4 lần do phải gọi LLM qua nhiều vòng trung gian.

## Relevance to our topic

Nền tảng cho cấu trúc xuất JSON points: [{text, cites}] của Sys_3_4.

## Possible improvement

Sys_3_4 thực thi kiểm chứng từng point bằng code tất định verify_point thay vì gọi lại LLM.

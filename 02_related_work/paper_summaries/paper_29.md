# Paper 29 Summary

## Citation

Tên bài: DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines
Tác giả: Omar Khattab et al. (Stanford University)
Năm: 2024
Nguồn: ICLR 2024
DOI/Link: https://doi.org/10.48550/arXiv.2310.03714

## Problem

Viết prompt thủ công dễ bị gãy vỡ khi thay đổi mô hình nền tảng hoặc điều chỉnh nghiệp vụ.

## Method

Thay thế prompt thủ công bằng mã lập trình module hóa có kiểm chứng và tự động tối ưu hóa tham số.

## Dataset

HotpotQA, GSM8K

## Evaluation

Accuracy (+20-30% vs manual prompts)

## Results

Nâng cao độ chính xác từ 20% đến 30% so với kỹ thuật prompt kỹ thuật thông thường.

## Limitations

Cần dữ liệu gán nhãn để chạy bộ tối ưu hóa teleprompter.

## Relevance to our topic

Định hình cấu trúc hàm sinh văn bản compose và render trong server/answer/llm_answer.py.

## Possible improvement

Sys_3_4 cố định cấu trúc đầu ra bằng JSON Schema để kiểm soát tuyệt đối định dạng phản hồi.

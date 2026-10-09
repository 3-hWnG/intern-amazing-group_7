# Paper 01 Summary

## Citation

Tên bài: ViGPTQA: State-of-the-Art LLMs for Vietnamese Question Answering
Tác giả: Minh-Thuan Nguyen, Khanh-Tung Tran, Vincent Nguyen, Xuan-Son Vu
Năm: 2023
Nguồn: Proceedings of EMNLP 2023 (Industry Track)
DOI/Link: https://aclanthology.org/2023.emnlp-industry.71/

## Problem

Các mô hình ngôn ngữ lớn đa ngôn ngữ thường thiếu dữ liệu chuẩn cho tiếng Việt, dẫn đến hiểu sai thuật ngữ pháp lý và văn phong hành chính công tại Việt Nam.

## Method

Đề xuất kiến trúc ViGPTQA kết hợp mô hình nền tảng ViGPT được tinh chỉnh chỉ dẫn chuyên sâu cho tiếng Việt với cơ chế trích xuất ngữ cảnh nghiệp vụ hành chính.

## Dataset

Bộ Benchmark Hỏi - Đáp Pháp lý & Hành chính tiếng Việt

## Evaluation

Exact Match, F1-Score, Human Evaluation

## Results

ViGPT đạt độ chính xác vượt trội so với các baseline mã nguồn mở cùng kích thước trên các bài toán hỏi đáp pháp lý và hành chính công tiếng Việt.

## Limitations

Chưa tích hợp cơ chế kiểm chứng số liệu thời gian thực (post-hoc verification) để chống ảo giác số liệu tài chính.

## Relevance to our topic

Bài báo nền tảng khẳng định mô hình trợ lý phải tối ưu hóa năng lực ngôn ngữ tiếng Việt bản địa thay vì dùng dịch máy tiếng Anh; định hướng việc chọn Qwen2.5 trong Sys_3_4.

## Possible improvement

Sys_3_4 bổ sung cơ chế kiểm chứng tất định verify_point và kiểm soát ngân sách trích dẫn để đảm bảo 0% ảo giác số tiền lệ phí.

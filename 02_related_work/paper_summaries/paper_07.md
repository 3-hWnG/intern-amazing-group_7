# Paper 07 Summary

## Citation

Tên bài: LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters
Tác giả: van der Meer & Rossi
Năm: 2026
Nguồn: ICAIL 2026 (AI & Law)
DOI/Link: https://doi.org/10.1145/icail.2026.005

## Problem

Mô hình ngôn ngữ tự ý sáng tác ra các điều khoản quy định không có trong văn bản hành chính đô thị khi trả lời công dân.

## Method

Tích hợp bộ kiểm chứng điều khoản đối chiếu từng khẳng định của mô hình với danh mục quy định đã được phê duyệt.

## Dataset

184 hồ sơ tư vấn pháp lý tại thành phố Amsterdam

## Evaluation

Clause Precision (81.3%), Factual Consistency (84.1%)

## Results

Nâng độ chính xác điều khoản lên 81.3% và độ nhất quán sự thật đạt 84.1%.

## Limitations

Độ trễ cao do sử dụng thêm vòng gọi LLM để tự kiểm chứng, không phù hợp cho phản hồi tức thì.

## Relevance to our topic

Nền tảng lý thuyết cho bộ kiểm chứng hậu kỳ verify_point của Sys_3_4.

## Possible improvement

Sys_3_4 chuyển đổi việc kiểm chứng sang thuật toán Regex và so khớp chuỗi tất định bằng code (<1ms) thay vì gọi lại LLM.

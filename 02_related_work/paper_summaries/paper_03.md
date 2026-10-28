# Paper 03 Summary — Rajpurkar2018 — Câu hỏi không trả lời được (SQuAD 2.0)

Nhóm khuôn B2: **liên quan trực tiếp**.
Kiểm chứng: đọc PDF trên ACL Anthology ngày 25/10/2026; số liệu lấy từ tóm tắt và Bảng 3.
Bản ACL gọi bộ dữ liệu là SQuADRUn; bản phát hành công khai mang tên SQuAD 2.0.

## Citation
- **Tên bài:** Know What You Don't Know: Unanswerable Questions for SQuAD
- **Tác giả:** P. Rajpurkar, R. Jia, P. Liang
- **Năm:** 2018
- **Nguồn:** ACL 2018 (Short Papers), trang 784–789
- **DOI:** 10.18653/v1/P18-2124

## Problem
Các bộ dữ liệu đọc hiểu trước đây chỉ có câu hỏi trả lời được. Vì vậy, model chỉ cần chọn đoạn văn "trông liên quan" mà không phải kiểm xem câu trả lời có thực sự nằm trong văn bản hay không.

## Method
Crowdworker viết câu hỏi không trả lời được theo cách đối kháng: câu hỏi trông giống câu trả lời được, và văn bản có sẵn một đáp án "nghe hợp lý" nhưng sai.

## Dataset
SQuAD cũ cộng thêm 53.775 câu hỏi không trả lời được.

## Evaluation
- Đo bằng EM và F1.
- Với câu không trả lời được, model chỉ được điểm khi không đưa ra câu trả lời nào.

## Results
- Một model mạnh đạt 86% F1 trên SQuAD nhưng chỉ đạt 66% trên bộ mới.
- Model tốt nhất đạt 66,3 F1 trên tập test, trong khi con người đạt 89,5 F1.

## Limitations
- Câu hỏi do crowdworker viết.
- "Không trả lời được" chỉ xét trong phạm vi một đoạn văn.

## Relevance to our topic
Bài cho thấy chỉ cần thêm câu không có đáp án là điểm của hệ thống mạnh đã giảm rõ. Bài 1 gặp cùng hiện tượng ở mức hệ thống: trên câu hỏi thật, độ chính xác hành vi giảm từ 77,2% xuống 56,5%.

## Possible improvement
Bài 1 có thể thêm một tập "câu khó đối kháng": câu ngoài phạm vi nhưng có chứa tên thủ tục. Tập này đo riêng khả năng không bị từ khoá đánh lừa.

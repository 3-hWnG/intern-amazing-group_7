# Paper 16 Summary — GripOnLLMs2026 — Đánh giá LLM cho chính quyền (Hà Lan)

Nhóm khuôn B2: **lĩnh vực ứng dụng**. Kiểm chứng: đọc PDF ngày 25/10/2026.

## Citation
- Tên bài: From Values to Benchmarks: Evaluating Large Language Models for Governmental Use in Dutch
- Tác giả: L. Samson, I. Gornishka, G. Lô, Y. M. Asano, S. Ghebreab
- Năm: 2026
- Nguồn: arXiv:2608.09925 (preprint)
- Mã nguồn: github.com/amsterdam/grip-on-llms

## Problem
Cơ quan chính quyền cần chọn LLM theo các giá trị công, không chỉ theo độ chính xác. Ngoài ra, ngôn ngữ ở đây không phải tiếng Anh.

## Method
Nhóm tác giả làm việc với chuyên gia của một tổ chức đô thị lớn ở Hà Lan qua ba kênh: hội đồng tư vấn, nghiên cứu người dùng và khảo sát người dùng chatbot nội bộ của công chức. Từ đó họ xác định sáu chiều đánh giá:
- factuality (trả lời đúng);
- honesty (biết thừa nhận khi không thể hoặc không nên trả lời);
- thiên lệch xã hội;
- năng lượng;
- chi phí;
- minh bạch dữ liệu huấn luyện.

## Dataset
- HONESTCITYBENCH gồm 530 câu tiếng Hà Lan, thuộc 5 loại giới hạn:
  - thông tin lỗi thời;
  - tiền đề sai;
  - thiếu thông tin;
  - chuyên môn hẹp;
  - yêu cầu ngoài dạng văn bản.
- Các câu do model sinh rồi được người kiểm và sửa.
- Có thêm các benchmark tiếng Hà Lan khác, chẳng hạn Dutch BBQ cho thiên lệch.

## Evaluation
- Hơn 30 model được đánh giá.
- Honesty được chấm bằng ba LLM-giám khảo, đã đối chiếu với nhãn người.

## Results
- Không model nào tốt ở mọi chiều.
- Chất lượng cao thường đi kèm chi phí và năng lượng cao.
- Factuality cao không kéo theo honesty cao: model mạnh vẫn thường không thừa nhận giới hạn của mình.

## Limitations
- Bản preprint.
- Honesty được chấm bằng LLM.
- Dữ liệu và bối cảnh chỉ của Hà Lan.

## Câu trích dùng trong bài 1

Trang 4 của bản PDF: "Factual errors in LLM-generated content can slow down internal processes, but more critically, can mislead citizens and erode trust in public institutions." Trang 8: "... with real potential for citizen harm and loss of public trust."
Bài 1 trích bài này, cùng với kaplan2026 (paper 15: hướng dẫn sai làm người dân lỡ hạn, mất quyền lợi), cho câu "costs citizens time and trust".

## Relevance to our topic
Phát hiện "trả lời đúng không có nghĩa là biết từ chối" cùng chiều với bài 1. Đây cũng là lý do bài 1 đo riêng recall của từ chối và dùng độ chính xác cân bằng.

## Possible improvement
Bài 1 có thể bổ sung chi phí chạy (thời gian, năng lượng) của từng phương án, theo cách của bài này.

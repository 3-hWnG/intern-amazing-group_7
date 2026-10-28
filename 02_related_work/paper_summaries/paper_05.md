# Paper 05 Summary — Aliannejadi2019 — Đặt câu hỏi làm rõ

Nhóm khuôn B2: **liên quan trực tiếp**.

Kiểm chứng: đọc PDF arXiv:1907.06554 ngày 25/10/2026. Số liệu lấy từ phần tóm tắt.

## Citation
- **Tên bài:** Asking Clarifying Questions in Open-Domain Information-Seeking Conversations
- **Tác giả:** M. Aliannejadi, H. Zamani, F. Crestani, W. B. Croft
- **Năm:** 2019
- **Nguồn:** SIGIR 2019, trang 475–484
- **DOI:** 10.1145/3331184.3331265

## Problem
Người dùng thường không diễn đạt đủ nhu cầu trong một câu truy vấn. Hệ thống hội thoại chỉ trả về được ít kết quả, nên cần chủ động hỏi lại.

## Method
- Đề xuất cách đánh giá offline cho nhiệm vụ hỏi lại.
- Khung truy hồi gồm ba phần: tìm câu hỏi làm rõ, chọn câu hỏi, rồi truy hồi tài liệu.

## Dataset
Bộ Qulac, thu bằng crowdsourcing trên dữ liệu TREC Web Track 2009–2012. Bộ này có hơn 10 nghìn cặp hỏi–đáp, thuộc 198 chủ đề với 762 khía cạnh (facet).

## Evaluation
Các chỉ số truy hồi như P@1, so sánh trước và sau khi hỏi lại.

## Results
- Với một mô hình oracle, chỉ cần hỏi đúng một câu là P@1 tăng hơn 170%.
- Mô hình chọn câu hỏi của tác giả vượt các baseline.

## Limitations
- Tìm kiếm web bằng tiếng Anh.
- Câu trả lời cho câu hỏi làm rõ do crowdworker viết.

## Relevance to our topic
Hỏi lại là lựa chọn thứ ba, nằm giữa trả lời và từ chối. Bài 1 có hành vi `clarify` khi nhiều thủ tục cùng khớp. Tuy vậy, câu hỏi thật hiếm khi cần hỏi lại: chỉ 6 trên 313 câu test. Vì thế bài 1 không kết luận được gì về hỏi lại.

## Possible improvement
Thu thêm câu hỏi thật cần hỏi lại, ví dụ những câu có thủ tục theo từng tỉnh, rồi đo xem câu hỏi làm rõ có thật sự dẫn tới đúng thủ tục hay không.

# Paper 06 Summary — Wen2025 — Khảo sát về việc LLM từ chối trả lời (abstention)

- Nhóm theo khuôn B2: **liên quan trực tiếp**.
- Kiểm chứng: đã đọc PDF arXiv:2407.18418 (bản TACL) ngày 25/10/2026.

## Citation
- Tên bài: Know Your Limits: A Survey of Abstention in Large Language Models
- Tác giả: B. Wen, J. Yao, S. Feng, C. Xu, Y. Tsvetkov, B. Howe, L. L. Wang
- Năm: 2025
- Nguồn: Transactions of the Association for Computational Linguistics 13 (2025) 529–556
- DOI: 10.1162/tacl_a_00754

## Problem
Hệ thống hoá các nghiên cứu về việc LLM từ chối trả lời, một cách để giảm ảo giác và tăng an toàn.

## Method
Bài đề xuất một khung nhìn vấn đề từ ba góc:
- **Câu hỏi**: có trả lời được không.
- **Model**: có đủ hiểu biết để trả lời không.
- **Giá trị con người**: câu hỏi và câu trả lời có phù hợp không.

Các phương pháp được xếp theo giai đoạn: tiền huấn luyện, căn chỉnh (alignment) và suy luận. Giai đoạn suy luận chia tiếp thành ba nhóm: xử lý đầu vào, xử lý trong lúc sinh và hậu xử lý.

## Dataset
Bài khảo sát nên không có bộ dữ liệu riêng. Mục 4.1 liệt kê các benchmark về từ chối.

## Evaluation
Mục 4.2 tổng hợp các chỉ số:
- abstention precision;
- abstention recall;
- abstention rate;
- đánh đổi giữa độ chính xác và độ phủ (coverage).

## Results
- Các phương pháp căn chỉnh có thể khiến model từ chối quá mức (over-abstention).
- Việc từ chối ở các ngôn ngữ ít tài nguyên còn kém; tác giả nêu đây là một hướng cần nghiên cứu tiếp.

## Limitations
- Không có thực nghiệm mới.
- Phần lớn các công trình được khảo sát là tiếng Anh.

## Relevance to our topic
Lớp luật của bài 1 thuộc nhóm "xử lý đầu vào": nó quyết định dựa trên việc câu hỏi có trả lời được bằng dữ liệu thủ tục hay không. Bài khảo sát này cũng là căn cứ để đo việc từ chối bằng các chỉ số riêng, không chỉ bằng độ chính xác chung.

## Possible improvement
Bài 1 đã báo recall của từng lớp. Có thể báo thêm abstention precision, tức tỉ lệ từ chối đúng trong số các lần từ chối, theo định nghĩa ở mục 4.2.

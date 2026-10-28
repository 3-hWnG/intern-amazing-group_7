# Paper 18 Summary — Geifman2017: phân loại có chọn lọc cho mạng nơ-ron sâu

- Nhóm khuôn B2: từ chối / phát hiện ngoài phạm vi.
- Kiểm chứng: đọc trang tóm tắt arXiv:1705.08500 ngày 27/10/2026; nơi đăng NeurIPS 2017 theo DBLP (conf/nips/GeifmanE17). Số liệu dưới đây chỉ lấy từ phần tóm tắt.
- Lý do thêm: phản biện vòng 2 gợi ý trích cho ý "chỉ trả lời khi đủ tin cậy".

## Citation
- Tên bài: Selective Classification for Deep Neural Networks
- Tác giả: Yonatan Geifman, Ran El-Yaniv
- Năm: 2017
- Nguồn: NeurIPS 2017; arXiv:1705.08500

## Problem
Mạng nơ-ron sâu luôn đưa ra dự đoán, kể cả khi dễ sai. Ứng dụng quan trọng cần một bộ phân loại được phép từ chối, để đổi độ phủ (coverage) lấy rủi ro (risk) thấp hơn.

## Method
- Từ một mạng đã huấn luyện, dựng bộ phân loại có chọn lọc: bộ phân loại kèm một hàm từ chối dựa trên mức tin cậy.
- Người dùng đặt mức rủi ro mong muốn; ngưỡng tin cậy được chọn sao cho, với xác suất cao, rủi ro thật không vượt mức đó.

## Dataset
CIFAR và ImageNet.

## Evaluation
Rủi ro (tỉ lệ lỗi) trên phần được giữ lại và độ phủ (tỉ lệ mẫu không bị từ chối).

## Results
- Ví dụ trong tóm tắt: top-5 trên ImageNet, bảo đảm lỗi 2% với xác suất 99,9%, giữ được gần 60% mẫu test.

## Limitations
- Chỉ xét phân loại ảnh; không xét câu ngoài phạm vi, không xét hỏi lại.
- Mức tin cậy lấy từ chính mạng, nên phụ thuộc vào việc điểm tin cậy có xếp hạng đúng hay không.

## Relevance to our topic
Bài 1 trích bài này ở mục Discussion: độ chính xác của câu trả lời trên câu hỏi ngẫu nhiên thấp, nên trợ lý nên chuyển câu trả lời cho cán bộ xác nhận, hoặc chỉ trả lời khi đủ tin cậy. Đây cũng là một hướng tương lai trong phần Conclusion.

## Possible improvement
Áp dụng cho bài 1: dùng điểm của bộ xếp hạng hoặc bộ xếp lại làm điểm tin cậy, chọn ngưỡng trên dev theo mức rủi ro cho trước, rồi báo đường cong rủi ro–độ phủ trên tập test khoá.

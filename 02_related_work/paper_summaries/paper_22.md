# Paper 22 Summary — Brodersen2010: độ chính xác cân bằng

- Nhóm khuôn B2: phương pháp đánh giá.
- Kiểm chứng: thông tin xuất bản kiểm qua Semantic Scholar và DOI ngày 28/10/2026. Nhà xuất bản không cho xem tóm tắt qua API, nên phần dưới chỉ mô tả phương pháp chuẩn mà bài đưa ra và cách bài 1 dùng nó; không lấy số nào từ bài.

## Citation
- Tên bài: The Balanced Accuracy and Its Posterior Distribution
- Tác giả: K. H. Brodersen, C. S. Ong, K. E. Stephan, J. M. Buhmann
- Năm: 2010
- Nguồn: Proc. 20th Int. Conf. Pattern Recognition (ICPR 2010), pp. 3121–3124, DOI 10.1109/ICPR.2010.764

## Problem
Khi các lớp lệch nhau, độ chính xác thường (accuracy) cho kết quả lạc quan: một bộ phân loại chỉ đoán lớp đông nhất vẫn đạt điểm cao.

## Method
- Dùng độ chính xác cân bằng: trung bình recall của các lớp.
- Đưa ra phân phối hậu nghiệm của chỉ số này để có khoảng tin cậy.

## Dataset
Không áp dụng (bài phương pháp).

## Evaluation
So sánh accuracy và balanced accuracy trên dữ liệu lệch lớp.

## Results
- Balanced accuracy tránh được lợi thế của việc đoán lớp đông nhất.

## Limitations
- Bài xét phân loại nhiều lớp nói chung; bài 1 chỉ dùng hai lớp answer và refuse cho chỉ số này vì lớp clarify quá ít.

## Relevance to our topic
Bài 1 trích ở Metrics: 79% (test 1) và 92% (test 2) câu thật phải từ chối, nên luôn từ chối đã đạt 79,2% và 92,3% độ chính xác hành vi. Chỉ số chính vì vậy là độ chính xác cân bằng (trung bình recall của answer và refuse).

## Possible improvement
Báo thêm khoảng hậu nghiệm theo cách của bài này, bên cạnh khoảng bootstrap cặp mà bài 1 đang dùng.

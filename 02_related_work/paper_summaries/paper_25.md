# Paper 25 Summary — Cohen1960: hệ số đồng thuận κ

- Nhóm khuôn B2: phương pháp đánh giá.
- Kiểm chứng: thông tin xuất bản kiểm qua Semantic Scholar và DOI ngày 28/10/2026. Nhà xuất bản không cho xem tóm tắt qua API, nên phần dưới chỉ mô tả phương pháp chuẩn mà bài đưa ra và cách bài 1 dùng nó; không lấy số nào từ bài.

## Citation
- Tên bài: A Coefficient of Agreement for Nominal Scales
- Tác giả: J. Cohen
- Năm: 1960
- Nguồn: Educational and Psychological Measurement 20(1) (1960) 37–46, DOI 10.1177/001316446002000104

## Problem
Tỉ lệ hai người gán nhãn khớp nhau bị thổi phồng bởi những lần khớp do ngẫu nhiên, nhất là khi một nhãn chiếm đa số.

## Method
- Hệ số κ = (tỉ lệ khớp quan sát − tỉ lệ khớp kỳ vọng do ngẫu nhiên) / (1 − tỉ lệ khớp kỳ vọng).

## Dataset
Không áp dụng (bài phương pháp).

## Evaluation
Không áp dụng.

## Results
- Đưa ra hệ số κ cho thang định danh.

## Limitations
- κ phụ thuộc vào phân bố nhãn; khi một lớp chiếm đa số, κ có thể thấp dù tỉ lệ khớp cao.

## Relevance to our topic
Bài 1 tính κ giữa lượt nhãn thứ nhất và lượt nhãn thứ hai (Gemini 4 Argon đề xuất, trưởng nhóm kiểm) trên 91 câu test 1: κ = 0,685, khoảng bootstrap 95% 0,55–0,82, khớp 79/91 câu.

## Possible improvement
Báo thêm κ cho bộ test 2 nếu sau này có lượt nhãn độc lập.

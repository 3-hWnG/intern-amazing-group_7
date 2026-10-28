# Paper 24 Summary — McNemar1947: so hai tỉ lệ ghép cặp

- Nhóm khuôn B2: phương pháp đánh giá.
- Kiểm chứng: thông tin xuất bản kiểm qua Semantic Scholar và DOI ngày 28/10/2026. Nhà xuất bản không cho xem tóm tắt qua API, nên phần dưới chỉ mô tả phương pháp chuẩn mà bài đưa ra và cách bài 1 dùng nó; không lấy số nào từ bài.

## Citation
- Tên bài: Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages
- Tác giả: Q. McNemar
- Năm: 1947
- Nguồn: Psychometrika 12 (1947) 153–157, DOI 10.1007/BF02295996

## Problem
Khi hai tỉ lệ đo trên cùng một nhóm đối tượng, chúng tương quan với nhau, nên các phép kiểm cho hai mẫu độc lập không dùng được.

## Method
- Chỉ dùng các cặp bất đồng: số đối tượng đúng ở phép đo này mà sai ở phép đo kia, và ngược lại. Dưới giả thuyết không, hai số này bằng nhau.

## Dataset
Không áp dụng (bài phương pháp).

## Evaluation
Không áp dụng.

## Results
- Đưa ra phép kiểm nay gọi là phép kiểm McNemar.

## Limitations
- Chỉ cho biết có khác biệt hay không, không cho cỡ hiệu ứng; bài 1 báo thêm khoảng bootstrap cặp.

## Relevance to our topic
Bài 1 dùng dạng chính xác hai phía (nhị thức trên các cặp bất đồng) cho mọi so sánh cặp, cả hành vi lẫn đúng trọn, và ghi số câu +/−, ví dụ bản gốc → A trên test 1: +96/−10, p ≈ 9·10⁻¹⁹. Code: `eval/hard/metrics.py`, `eval/hard/paired_stats.py`.

## Possible improvement
Không cần cải tiến cho mục đích của bài 1.

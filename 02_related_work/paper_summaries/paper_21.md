# Paper 21 Summary — Dwork2015: tập giữ lại dùng lại được

- Nhóm khuôn B2: phương pháp đánh giá.
- Kiểm chứng: thông tin xuất bản kiểm qua Semantic Scholar và DOI ngày 28/10/2026. Nhà xuất bản không cho xem tóm tắt qua API, nên phần dưới chỉ mô tả phương pháp chuẩn mà bài đưa ra và cách bài 1 dùng nó; không lấy số nào từ bài.

## Citation
- Tên bài: The Reusable Holdout: Preserving Validity in Adaptive Data Analysis
- Tác giả: C. Dwork, V. Feldman, M. Hardt, T. Pitassi, O. Reingold, A. Roth
- Năm: 2015
- Nguồn: Science 349(6248) (2015) 636–638, DOI 10.1126/science.aaa9375

## Problem
Khi người phân tích nhìn kết quả trên tập giữ lại (holdout) rồi chọn bước tiếp theo, tập đó không còn độc lập; ước lượng trên nó bị lạc quan.

## Method
- Cơ chế truy cập tập giữ lại có kiểm soát (Thresholdout), dựa trên ý tưởng của quyền riêng tư vi phân, để dùng lại tập giữ lại mà vẫn giữ tính đúng của ước lượng.

## Dataset
Không áp dụng (bài phương pháp).

## Evaluation
Phân tích lý thuyết và minh hoạ.

## Results
- Chỉ ra rằng dùng lại tập giữ lại một cách thích nghi gây quá khớp, và đưa ra cách giới hạn sai lệch đó.

## Limitations
- Cơ chế cần thêm nhiễu và giới hạn số lần truy vấn; bài 1 không dùng cơ chế này mà dùng cách đơn giản hơn: khoá test và chạy một lần.

## Relevance to our topic
Bài 1 trích ở Evaluation Protocol làm lý do không dùng tập test để chọn gì: mỗi bộ test khoá bằng SHA-256 và commit, mỗi cấu hình chạy một lần. Vòng 2 (A2) tốt trên dev nhưng hoà trên test 2, đúng với cảnh báo của bài này.

## Possible improvement
Khi cần nhiều vòng cải thiện, có thể dùng một cơ chế kiểu Thresholdout thay vì phải gán nhãn một bộ test mới mỗi vòng.

# Paper 27 Summary — HF-mps: hỏi đáp Cổng DVC Bộ Công an (dữ liệu)

- Nhóm khuôn B2: tài nguyên dữ liệu.
- Kiểm chứng: mở trang dữ liệu trên Hugging Face ngày 25/10/2026 (ghi ở `paper_list.md` mục 6).

## Citation
- Tên: vn-mps-public-service-qa
- Tác giả: doanhieung (Hugging Face)
- Năm: 2026 (ngày truy cập 18/10/2026)
- Nguồn: https://huggingface.co/datasets/doanhieung/vn-mps-public-service-qa

## Problem
Không áp dụng (bộ dữ liệu). Đây là các câu người dân gửi tới Cổng Dịch vụ công Bộ Công an, kèm câu trả lời.

## Method
- Bài 1 chỉ lấy câu hỏi.

## Dataset
Khoảng 809 dòng.

## Evaluation
Không áp dụng.

## Results
- Không áp dụng.

## Limitations
- Thẻ dữ liệu không ghi giấy phép; bài 1 không công bố lại văn bản câu hỏi.
- Nhiều câu hỏi về chế độ nội bộ ngành công an, nên nằm ngoài phạm vi thủ tục cấp xã.

## Relevance to our topic
Nguồn câu hỏi thật thứ hai của bài 1. Trên test 1, phần tăng của lớp luật lớn hơn ở nguồn này (0,618 → 0,875) so với nguồn Bình Định (0,649 → 0,751).

## Possible improvement
Như HF-dvc.

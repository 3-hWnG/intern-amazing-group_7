# Paper 28 Summary — DVC: Cổng Dịch vụ công Quốc gia (nguồn tri thức)

- Nhóm khuôn B2: tài nguyên dữ liệu.
- Kiểm chứng: thu dữ liệu trực tiếp từ cổng ngày 13/10/2026.

## Citation
- Tên: Cổng Dịch vụ công Quốc gia (National Public Service Portal)
- Tác giả: Chính phủ Việt Nam
- Năm: 2026 (thu ngày 13/10/2026)
- Nguồn: https://dichvucong.gov.vn

## Problem
Không áp dụng (nguồn tri thức). Cổng công bố bản ghi của từng thủ tục hành chính.

## Method
- Thu một lần qua các JSON endpoint công khai, không cần đăng nhập, mà chính trang web của cổng dùng; 2 yêu cầu/giây. Cổng không có API chính thức.

## Dataset
1.517 thủ tục; 542 thủ tục cấp xã không phân theo tỉnh tạo thành phạm vi của bài 1.

## Evaluation
Không áp dụng.

## Results
- Không áp dụng.

## Limitations
- Là ảnh chụp tại một thời điểm; thủ tục có thể đổi sau ngày thu.

## Relevance to our topic
Nguồn duy nhất của câu trả lời: hệ thống ghép câu trả lời bằng code từ bản ghi thủ tục. Bản ghi không chứa dữ liệu cá nhân.

## Possible improvement
Thu lại định kỳ và ghép mã thủ tục cũ với mã mới.

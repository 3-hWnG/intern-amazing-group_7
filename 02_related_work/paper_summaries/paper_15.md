# Paper 15 Summary — GovAIPipe2026 — Quy trình quản trị AI cho chatbot chính phủ điện tử (Thổ Nhĩ Kỳ)

- **Nhóm khuôn B2:** lĩnh vực ứng dụng.
- **Kiểm chứng:** đã đọc PDF ngày 25/10/2026.
- **Lưu ý:** bản nháp ngày 25/10 từng mô tả sai bài này là "lọc phạm vi trước truy hồi"; câu đó trong bài 1 đã được sửa.

## Citation
- **Tên bài:** GovAI-Pipe: A Layered AI Governance Pipeline for Citizen-Facing AI in Turkey's e-Government Gateway
- **Tác giả:** Ahmet Kaplan (Istanbul Medipol University)
- **Năm:** 2026
- **Nguồn:** arXiv:2606.01417 (preprint)

## Problem
Cổng e-Devlet có hơn 68 triệu người dùng và hơn 9.200 dịch vụ, và đang đưa AI vào các ứng dụng cho công dân. Tuy vậy, chưa có hạ tầng kỹ thuật nào nối các khung chính sách (EU AI Act, OECD, chiến lược AI quốc gia) với việc vận hành thực tế.

## Method
Bài dùng phương pháp Design Science Research để đề xuất một quy trình 4 lớp:
1. **Kiểm định trước triển khai:** kiểm thiên lệch, khả năng giải thích, đánh giá tác động riêng tư.
2. **Quản trị triển khai:** phân hạng rủi ro, quy trình phê duyệt.
3. **Giám sát khi chạy:** phát hiện trôi dữ liệu, theo dõi công bằng, chuyển cho người xử lý.
4. **Xử lý sau sự cố:** lưu vết kiểm toán, khôi phục bản cũ, khắc phục cho công dân.

## Dataset
Không có. Bài minh hoạ bằng hai tình huống (chatbot e-Devlet Asistan và đánh giá điều kiện hưởng trợ cấp), dựng từ thông tin công khai.

## Evaluation
Chỉ phân tích, không có thực nghiệm.

## Results
- Mỗi lớp được gắn với điều khoản cụ thể của EU AI Act và luật bảo vệ dữ liệu.
- Ví dụ ngưỡng giám sát cho chatbot: báo động khi tỉ lệ hướng dẫn bịa vượt 2%.

## Limitations
Theo chính tác giả:
- Đây là khung khái niệm, chưa được triển khai hay đánh giá thực nghiệm.
- Các tình huống chỉ mang tính minh hoạ.

## Relevance to our topic
- Bài nêu rủi ro của chatbot dịch vụ công: hướng dẫn sai có thể làm người dân lỡ hạn hoặc mất quyền lợi.
- Đây là lý do bài 1 coi việc từ chối đúng quan trọng ngang trả lời đúng.
- Lớp luật minh bạch của bài 1 cũng dễ kiểm toán hơn một model tự quyết định.

## Possible improvement
- Bài 1 có thể nêu cách tích hợp vào một quy trình quản trị như vậy: lưu vết quyết định theo từng luật, và chuyển câu bị từ chối cho cán bộ.
- Đây chỉ là gợi ý; bài 1 không triển khai phần này.

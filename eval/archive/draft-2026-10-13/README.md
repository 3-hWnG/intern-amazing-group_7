# Số đo cũ của branch `draft` (2026-10-13) và vì sao không dùng

Các file đầu ra của bộ evaluation bên branch `draft` (`cases_golden_dev.jsonl`, `cases_golden_holdout.jsonl`, `ragas_dataset_*.json` khoảng 22 MB, các file `.bak`) **không được chép sang đây**. Lịch sử nằm ở commit `c829392` của https://github.com/3-hWnG/intern-amazing-group_7/tree/draft. Chỉ giữ bảng tóm tắt dưới đây để so "trước và sau".

| Số đo cũ (draft) | Giá trị | Code | Vì sao không dùng làm số báo cáo |
|---|---|---|---|
| RAGAS thật (394 ca, giám khảo qwen2.5:7b): faithfulness | 0,40 (chỉ 309/394 ca chấm được) | cũ | Ngữ cảnh là bản tóm tắt dựng lại, không phải thứ hệ thống đã dùng; giám khảo chưa được kiểm chứng |
| answer relevancy | 0,38 | cũ | như trên |
| context precision | 0,81 | cũ | Định nghĩa khác (tóm tắt thủ tục ứng viên, không phải đoạn trường) |
| context recall | 0,68 | cũ | Đáp án mẫu là placeholder ở 77% số ca |
| "0% số bịa trên 394 ca" | 0% | cũ | Chỉ kiểm 3 con số ngẫu nhiên có xuất hiện không; bằng chứng yếu |
| Golden set sinh tự động | 2.168 ca, 122 lĩnh vực | cũ | Holdout không mù (309/311 thủ tục trùng dev), đáp án placeholder, nhãn "miễn lệ phí" sai hoặc có điều kiện, ca chèn lệnh gắn nhãn `answer`, không ca nào được người rà (`needs_human_review: true` ở mọi ca) |
| HOLDOUT-4: MRR / nDCG@5 | 0,810 / 0,785 | cũ | Đã đo lại trên code hiện tại: 0,824 / 0,805 |
| Real-log v1: top-1, MRR | 16/23, 0,751 | cũ | Đã đo lại trên code hiện tại: 17/23, 0,773 |
| An toàn: che PII có dấu phân cách | 0/3 trước vá, 3/3 sau vá | cũ + vá | **Dùng được**: đã đo lại và đã port bản vá sang `server/policy/policy.py` |

Danh sách đầy đủ lỗi của golden set draft (11 mục) và cách kiểm lại: `D:\merged_sys3_4\MERGE_PLAN.md` mục 2.5 và Phụ lục A.

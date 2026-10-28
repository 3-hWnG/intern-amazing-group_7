# Methodology

## Thiết kế thí nghiệm

Cùng một hệ thống, các phần được bật hoặc tắt bằng cờ. Có 4 nhóm cấu hình:

| Cấu hình | Mô tả |
|---|---|
| Base (mọi cờ tắt) | Hệ thống trước nghiên cứu này |
| A | Lớp luật: bỏ phần chào hỏi, từ điển từ dân dùng, lọc tên yếu, cổng ngoài phạm vi, tập trung đoạn hỏi, mặc định cá nhân |
| B, A+B | Reranker chạy một mình, hoặc chạy trên lớp luật |
| C, A+C, A+C-name | Model 4B đọc câu: chạy một mình, hoặc trên lớp luật; bản C-name chỉ lấy tên thủ tục |
| R | Baseline RAG: BGE-M3 lấy 5 thủ tục, model 4B tự quyết định, không dùng luật nào |
| A2, A2 + B | Vòng 2 (cờ `S3_R2`), chỉ chạy trên test 2 |
| Gate only, L | Thêm sau (*post hoc*): chỉ cổng ngoài phạm vi của A, đặt trên bản gốc; và hai cổng học đặt vào chỗ đó |

Mô tả chi tiết từng phần: `04_proposed_system/`.

## Giao thức (chống "chọn theo test")

1. Lấy mẫu và gán nhãn bộ test, rồi khoá bằng sha256 và một commit.
2. Viết luật và chọn ngưỡng **chỉ trên dev**.
3. Đóng băng code bằng một commit.
4. Chạy mỗi cấu hình **một lần** trên test, rồi mở kết quả một lần.
5. Kiểm tra đối chứng: tắt hết cờ thì kết quả phải trùng bản gốc trên mọi câu.

**Quy tắc chọn cấu hình** (viết trước khi chạy test): chọn cấu hình có độ chính xác cân bằng cao nhất trên dev, với điều kiện số câu trả lời đúng trọn không thấp hơn lớp luật A chạy một mình; hoà thì lấy cấu hình có số câu đúng trọn cao hơn. Vòng 1 chọn A + B, vòng 2 chọn A2 + B.

**Baseline R** được thêm sau khi test 1 đã mở, và bài nói rõ điều này. Cách làm:
- prompt v1 viết trước lượt chạy dev đầu tiên;
- v1 hỏi lại quá nhiều, nên viết thêm đúng hai biến thể và ghi lại trước khi chạy: v2 (quy tắc quyết định theo thứ tự) và v3 (v2 cộng mô tả thủ tục);
- chọn biến thể trên dev theo độ chính xác cân bằng, hoà thì xét số câu đúng trọn: v1 0,343, v2 0,445, v3 0,432, nên chọn v2;
- chạy mỗi bộ test một lần.

**Kế hoạch so sánh.** Test 1: so bản gốc với từng phương án và với bản chọn. Test 2 khai báo trước ba so sánh chính (`eval/real_v4/RUN_PLAN.md`): A + B → A2 + B, bản gốc → A2 + B, và A2 + B → R. Mọi so sánh khác là mô tả.

**Phân tích sau (*post hoc*).** Chạy trên code đã đóng băng, không dùng để chọn gì:
- bỏ từng luật của A (`eval/hard/ablation_runs.sh`);
- chỉ dùng cổng;
- hai cổng học (`learned_gate.py`, `learned_gate_emb.py`);
- thống kê cặp (`paired_stats.py`).

## Vòng cải thiện thứ hai (trưởng nhóm cho phép)

- **Dev mới:** real_v1 + real_v2 = 595 câu.
- **Thay đổi:** nằm sau cờ `S3_R2`, mặc định tắt.
- **Test mới:** real_v4, đã khoá thứ tự trước khi sửa code. Nhãn do Gemini 4 Argon đề xuất và trưởng nhóm kiểm. Người viết code (Claude) không đọc câu hỏi hay nhãn trước lượt chạy cuối.
- **Trước khi chạy test:** kiểm hồi quy trên bộ golden và chạy unit test.

## Kiểm định thống kê

Xem `evaluation_metrics.md`: Wilson 95%, McNemar chính xác, bootstrap cặp, κ.

# Evaluation Metrics (khuôn bước 9)

| Chỉ số | Định nghĩa | Vì sao dùng |
|---|---|---|
| **Độ chính xác cân bằng** (chỉ số chính) | Trung bình recall của lớp answer và lớp refuse | 79% câu thật phải từ chối, nên một hệ "luôn từ chối" đã đạt 79,2% độ chính xác hành vi. Chỉ số cân bằng loại được lợi thế đó (Brodersen 2010) |
| Độ chính xác hành vi | Tỉ lệ câu có quyết định đúng trong 3 lớp | Chỉ số dễ hiểu, nhưng không đủ khi dùng một mình |
| Recall từng lớp | answer, clarify, refuse | Lớp clarify chỉ có 6 câu test, nên báo riêng và không gộp vào chỉ số cân bằng |
| **Trả lời đúng trọn** (end-to-end) | Tỉ lệ câu answer được hệ thống trả lời với thủ tục đúng đứng đầu | Chỉ số cân bằng vẫn tính đúng một câu trả lời sai thủ tục; chỉ số này thì không |
| Top-1 | Thủ tục đầu tiên hệ thống đưa ra (khi trả lời, hoặc ứng viên đầu tiên khi hỏi lại) là thủ tục đúng, tính trên các câu answer. Câu bị từ chối tính là sai | Tách riêng chất lượng xếp hạng khỏi chất lượng quyết định |
| Top-3, MRR@5 | Như trên, trong 3 hoặc 5 ứng viên đầu | Có trong `metrics.py`, không báo trong bài |
| **Độ chính xác câu trả lời** (answer precision) | Số câu trả lời đúng trọn chia cho mọi câu hệ thống trả lời | Cho biết người dân nhận được câu trả lời thì đúng bao nhiêu phần |
| Khoảng tin cậy Wilson 95% | Cho mọi tỉ lệ | Mẫu nhỏ (59 câu answer) |
| McNemar chính xác hai phía | So từng cặp cấu hình trên cùng các câu, cả hành vi lẫn đúng trọn | Kiểm định phù hợp khi so hai bộ phân loại trên cùng dữ liệu (Dietterich 1998; bài chỉ còn trích McNemar 1947) |
| Khoảng bootstrap cặp 95% | Hiệu độ chính xác cân bằng giữa hai cấu hình; lấy mẫu lại theo câu, 4.000 lần, SEED 20261027 (`eval/hard/paired_stats.py`) | Cho biết cỡ hiệu ứng, không chỉ có hay không ý nghĩa |
| Cohen's κ, bootstrap 2.000 lần | Độ đồng thuận giữa hai lượt nhãn | Đo độ tin cậy của nhãn |

## Mốc tầm thường (phải báo cùng kết quả)
- Luôn từ chối: cân bằng 0,500, trả lời đúng trọn 0/59.
- Luôn trả lời (giữ thủ tục đứng đầu của bản gốc): cân bằng 0,500, trả lời đúng trọn 20/59.

## Mã nguồn
- `eval/hard/metrics.py`: tóm tắt, khoảng tin cậy, McNemar, các mốc tầm thường.
- `eval/real_v1/real_v1_agree.py` và `eval/real_v2/relabel/read_relabel.py`: tính κ.

## Nhiệt độ máy

Các lượt chạy có canh nhiệt (`eval/thermal.py`), ghi log vào `eval/results/thermal.csv`. Bài sẽ báo trung thực các lần nhiệt vượt ngưỡng; xem `06_experiment_results/experimental_setup.md`.

# Bảng 1: hai bộ test đã khoá (mỗi cấu hình chạy một lần)

Test 1: real_v2, 313 câu (59 trả lời, 6 hỏi lại, 248 từ chối). Test 2: real_v4, 363 câu (21 / 7 / 335).

| Cấu hình | T1 cân bằng | T1 từ chối đúng | T1 đúng trọn | T1 chính xác câu trả lời (%) | T2 cân bằng | T2 từ chối đúng | T2 đúng trọn | T2 chính xác câu trả lời (%) |
|---|---|---|---|---|---|---|---|---|
| Luôn từ chối | 0,500 | 248 | 0 | – | 0,500 | 335 | 0 | – |
| Bản gốc | 0,647 | 132 | 19 | 11,7 | 0,571 | 175 | 5 | 3,0 |
| B: reranker một mình | 0,692 | 175 | 21 | 17,9 | – | – | – | – |
| C: model 4B đọc câu một mình | 0,785 | 213 | 25 | 30,9 | – | – | – | – |
| R: RAG + model 4B tự quyết | 0,489 | 104 | 28 | 43,8 | 0,413 | 197 | 4 | 10,5 |
| L: cổng naive Bayes* | 0,765 | 224 | 14 | 21,9 | 0,579 | 308 | 2 | 6,9 |
| L: cổng embedding* | 0,801 | 225 | 17 | 25,4 | 0,586 | 313 | 2 | 8,0 |
| Chỉ cổng (gate only)* | 0,770 | 218 | 15 | 20,8 | 0,666 | 287 | 5 | 9,1 |
| A: lớp luật | 0,814 | 219 | 35 | 45,5 | 0,705 | 297 | 9 | 19,6 |
| A + C (ý định, tên) | 0,817 | 237 | 32 | 58,2 | – | – | – | – |
| A + C (chỉ tên) | 0,834 | 216 | 39 | 47,0 | – | – | – | – |
| A + B (chọn vòng 1) | 0,823 | 219 | 36 | 46,2 | 0,683 | 298 | 8 | 17,4 |
| A2 + B (chọn vòng 2) | – | – | – | – | 0,729 | 297 | 10 | 20,0 |

A2 + B không chạy trên test 1, vì A2 được viết dựa trên chính các câu đó.

Nguồn: kết quả từng câu trong `eval/hard/results/` và `eval/hard/results/paired_stats.json` của repo code (bản công khai ở `Code/`). * là phân tích sau (*post hoc*).

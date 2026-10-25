# Dev của vòng cải thiện 2 (25/10/2026): real_v1 + real_v2 = 595 câu

real_v2 đã mở kết quả (bộ test của vòng 1, số đã đóng băng ở `7d199f3`), nên từ vòng 2 nó là dev cùng real_v1. Bộ test của vòng 2 là `eval/real_v4` (Claude không đọc).

- `cases_dev_r1r2.json`: ghép `eval/real_v1/cases_real_v1_labeled.json` (282) + `eval/real_v2/cases_real_v2_labeled.json` (313).
- `reader_cache_r1r2.jsonl`: đầu ra model 4B (phương án C) đã lưu của hai bộ, để đo lại không gọi model.

    python run_server.py eval/hard/dev.py --set hard/dev595/cases_dev_r1r2.json --name d2_<cấu hình>

## Kết quả trên dev595 (25/10/2026)

Kết quả của từng cấu hình nằm ở `eval/hard/results/dev/d2_*.json`. Cách chọn bản cuối ghi ở `eval/real_v4/RUN_PLAN.md`.

| Cấu hình | Cân bằng | Trả lời đúng trọn |
|---|---|---|
| tắt hết cờ (`d2_off`) | 0,642 | 25/114 |
| A (`d2_A`) | 0,856 | 73/114 |
| A+B (`d2_AB`) | 0,865 | 74/114 |
| A+R2, bản nháp đầu (`d2_AR2`) | 0,876 | 76/114 |
| A+R2 (`d2_AR2c`) | 0,916 | 87/114 |
| A+R2+C, chỉ dùng tên (`d2_AR2Cname`) | 0,925 | 84/114 |
| **A+R2+B** (`d2_AR2B`, đã chọn) | 0,916 | 88/114 |

- Các luật R2 được viết dựa trên chính bộ dev này, nên các số trên có lợi cho R2. Muốn biết R2 có thật sự tốt hơn thì phải xem kết quả trên real_v4.
- Có một lượt trung gian chạy trước khi sửa real_v1-199: cân bằng 0,916, trả lời đúng trọn 86/114; so với A, lượt này đúng thêm 29 câu và sai đi 1 câu (real_v1-199).
  - Tệp kết quả từng câu của lượt này đã bị `d2_AR2B.json` ghi đè. Lý do: Windows không phân biệt chữ hoa chữ thường trong tên tệp, nên `d2_AR2b` và `d2_AR2B` là cùng một tệp.
  - Chỉ còn dòng tóm tắt, lưu ở `results/dev/d2_AR2_intermediate_summary.txt`.
  - Lượt `d2_AR2c` là sau khi sửa câu real_v1-199.

Kiểm hồi quy:
- Golden (`regress/golden_AR2.json`), so với A:
  - hành vi đúng trên phần blind 518 câu tăng từ 400 lên 405;
  - top-1 tăng từ 275 lên 277;
  - từ chối đúng giữ nguyên 55;
  - hỏi lại đúng giảm từ 37 xuống 34. Nguyên nhân: R2 không hỏi tỉnh nữa khi thủ tục đã có bản toàn quốc.
- Unit test (`regress/unit_tests_summary_r2.txt`): 0 test trượt, 1 lỗi hồi quy đã biết từ trước.

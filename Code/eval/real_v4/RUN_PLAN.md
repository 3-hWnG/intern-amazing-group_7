# Kế hoạch chạy real_v4 (khai báo trước, commit cùng lúc đóng băng code)

Nhãn đã khoá ở `a79ec5f` (hash trước khi sửa message: `ae1fd25`; xem `eval/hard/results/test_v4/COMMIT_MAP.md`). Code đóng băng ở commit ghi trong `eval/hard/results/test_v4/stamp.txt`. Mỗi cấu hình chạy **một lần** với `--final real_v4`. Không cấu hình nào được chọn hay chỉnh theo real_v4.

## Cấu hình

| Tên | Là gì | Vai trò |
|---|---|---|
| `off` | Mọi cờ của A tắt, R2 tắt | Bản gốc. Kiểm chứng rằng mọi thay đổi đều nằm sau cờ |
| `A` | Lớp luật vòng 1 (cờ mặc định, R2 tắt) | Mốc của vòng 1 |
| `AB` | A + B (ngưỡng `semAseg`: τ_oos −8, τ_swap 2, không rescue) | Bản cuối vòng 1, đã chọn trên dev real_v1 |
| `R2final` | Bản cuối vòng 2: A+R2+B, chọn trên dev595 theo quy tắc bên dưới | Bản cải thiện |
| `R` | RAG + 4B tự quyết (`eval/hard/rag4b.py`, prompt v2) | Baseline ngoài |

## Quy tắc chọn `R2final`

Quy tắc chọn giống vòng 1 và được ghi lại trước khi chạy test:

- Chỉ dùng dev595, tức `eval/hard/dev595/cases_dev_r1r2.json` gồm real_v1 + real_v2.
- Các ứng viên:
  - A+R2;
  - A+R2+B (ngưỡng như AB);
  - A+R2+C chỉ dùng tên (đọc từ cache của model, không gọi lại model).
- Chọn ứng viên có độ chính xác cân bằng cao nhất, với điều kiện số câu trả lời đúng trọn không thấp hơn A+R2.

Hoà về độ chính xác cân bằng thì lấy ứng viên có số câu trả lời đúng trọn cao hơn, giống `eval/hard/sem_grid.py` của vòng 1.

### Kết quả chọn trên dev595 (25/10/2026; bảng này được sửa sau lượt chạy: hai số làm tròn 0,8563 → 0,8564 và 0,9251 → 0,9252, kết quả chọn không đổi)

| Cấu hình (dev595) | Cân bằng | answer | refuse | Trả lời đúng trọn |
|---|---|---|---|---|
| A (vòng 1) | 0,8564 | 91/114 | 428/468 | 73/114 |
| A+B (vòng 1, bản cuối) | 0,8651 | 93 | 428 | 74 |
| A+R2 | 0,9163 | 101 | 443 | 87 |
| A+R2+C tên | 0,9252 | 104 | 439 | 84 (< 87, **loại**) |
| **A+R2+B** | 0,9163 | 101 | 443 | **88** (**chọn**) |

`R2final` là A+R2+B. Đây là số trên dev, chính là bộ dùng để viết các luật của R2, nên số có lợi cho hệ thống. Chỉ real_v4 mới cho biết mức cải thiện thật.

## So sánh chính (McNemar chính xác hai phía, trên các câu không phải skip)

1. `AB` → `R2final`: vòng 2 có cải thiện so với vòng 1 trên câu mới không.
2. `off` → `R2final`.
3. `R2final` → `R`.

Báo cả độ chính xác hành vi, độ chính xác cân bằng, recall từng lớp, top-1/top-3, trả lời đúng trọn, khoảng tin cậy Wilson 95%.

Lớp answer chỉ có 21 câu, nên mọi kết luận về phía trả lời đều yếu. Bài phải nói rõ điều này.

## Chạy

Script `eval/hard/final_runs_v4.sh` chạy với canh nhiệt `THERMAL_LIMIT=60 THERMAL_RESUME=52 THERMAL_DUTY=1.0`, ghi log nhiệt riêng. Thứ tự chạy:
1. các cấu hình chỉ dùng luật;
2. các cấu hình có B;
3. R (dùng GPU).

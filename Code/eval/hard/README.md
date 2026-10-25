# Đợt sửa câu khó (24–25/10/2026) — công cụ đo và kết quả DEV

Bộ **dev** là `eval/real_v1` (282 câu thật, đã xem từng câu sai để sửa luật). Bộ **test** là `eval/real_v2` (313 câu, khoá ở commit `7e78438` trước mọi thay đổi code); `dev.py` không chạy real_v2 nếu thiếu `--final`.

| Tệp | Việc |
|---|---|
| `metrics.py` | Chỉ số đã ghi trước (eval/real_v2/README.md): hành vi đúng, recall từng lớp, cân bằng (answer + apologize), top-1 / top-3, MRR@5, trả lời đúng trọn, Wilson 95%, hai mốc ngây thơ |
| `dev.py` | Chạy một cấu hình (biến môi trường) trên real_v1 (mặc định) hoặc real_v2 (`--final real_v2`), canh nhiệt |
| `sem_grid.py` | Phương án B: chấm reranker MỘT lần (`score`), mô phỏng lưới ngưỡng không gọi lại model (`grid`) |
| `report.py` | Bảng Markdown: cả bộ / bộ sạch / tầng random / chude |
| `paced.py` | Chạy script đo có sẵn (`run_golden.py` ...) có canh nhiệt |
| `dev_queue.sh`, `dev_queue2.sh` | Các lượt dev đã chạy (A chốt, B, C, bóc tách) |
| `regress.sh` | Hồi quy: golden thu-tuc (cờ tắt / A bật) + toàn bộ test đơn vị |
| `final_runs.sh` | Lượt TEST trên real_v2: mỗi cấu hình đúng một lần, sau khi đóng băng code |
| `results/dev/` | Kết quả dev (bản sao của eval/results/, thư mục đó bị .gitignore) + đệm đầu ra model C trên real_v1 |
| `results/regress/` | Golden trước / sau và tóm tắt test đơn vị |

## Ba phương án (cờ môi trường, mặc định trong ngoặc)

- **A — luật đọc câu dân** (bật): `S3_LETTER_STRIP` bỏ lời chào / cảm ơn; `S3_LEXICON2` từ dân dùng -> tên thủ tục chính thức; `S3_WEAK_NAME` đoạn chỉ trùng vài chữ của tên rất dài không phải gọi tên thủ tục; `S3_SCOPE_GATE` (+ `S3_SCOPE_A6`) cổng ý định ngoài phạm vi (server/policy/scope.py); `S3_FOCUS` thư dài chỉ giữ đoạn câu hỏi; `S3_ORG_DEFAULT` không nhắc tổ chức thì lấy bản "hộ gia đình, cá nhân". Tắt hết = bản gốc (kiểm trên dev: 0 câu khác).
- **B — truy hồi theo nghĩa + reranker** (tắt; `S3_SEMANTIC=1`): bge-m3 (Ollama) lấy ứng viên trong 542 thủ tục cấp xã ∪ ứng viên của luật, bge-reranker-v2-m3 chấm; `S3_SEM_QUERY=seg` chấm đoạn câu hỏi thay vì cả thư; ngưỡng `S3_SEM_TAU_OOS` (từ chối), `S3_SEM_TAU_SWAP` (đổi thủ tục), `S3_SEM_TAU_RESCUE` (cứu câu luật đã từ chối).
- **C — model 4B đọc ý định** (tắt; `S3_READER=1`): qwen3:4b-instruct phân loại 6 ý định + gọi tên thủ tục bằng chữ, luật xếp hạng tên đó; `S3_READER_INTENT=0` bóc tách chỉ dùng tên.

## Tiêu chí chọn trên dev (ghi trước lượt test)

Tối đa độ chính xác cân bằng **với ràng buộc** số câu "trả lời đúng trọn" không thấp hơn cấu hình chỉ dùng luật; hoà thì đúng trọn cao hơn, rồi ngưỡng bảo thủ hơn. Lý do: cân bằng thường tính "trả lời" là đúng cả khi trả lời SAI thủ tục (lượt lưới đầu, khi bộ mô phỏng còn lỗi "cứu" mọi câu bị từ chối: ngưỡng chọn ra làm top-1 rơi 65% -> 35%); "cân bằng chặt" (trung bình đúng trọn và recall từ chối) chọn cấu hình từ chối gần hết. Theo tiêu chí này: B một mình = `seg, -3.5 / 0.5 / 0.0`; B trên A = `seg, -8 / 2.0 / 99`; **bản cuối = A + B**.

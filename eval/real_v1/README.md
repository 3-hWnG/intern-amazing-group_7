# Bộ real_v1 cho System 3 (Strict)

Câu hỏi thật của người dân (Hugging Face), nhãn do hai lượt AI gán và đã duyệt. **Đã khoá ngày 21/10/2026** (xem `LOCK.md`).

| File | Là gì |
|---|---|
| `collect_real_v1.py` | Sinh `cases_real_v1.json` từ kho thô (cùng `SEED` cho tệp giống hệt) |
| `cases_real_v1.json` | 300 câu hỏi, chưa nhãn |
| `real_v1_labels_A.json`, `real_v1_labels_B.json` | Nhãn hai lượt gán độc lập (A: Claude, B: subagent) |
| `real_v1_agree.py` | Tính độ đồng thuận A/B (`--s4` cho System 4, `--selftest`) |
| `real_v1_labels_final.json` | Nhãn cuối sau thống nhất và duyệt (300 câu, có `status`, `review`) |
| `REAL_V1_ASSUMPTIONS.md` | Lý do từng câu bất đồng và kiểm sâu 22 câu |
| `cases_real_v1_labeled.json` | **Bộ để chạy**: 282 câu (bỏ 18 `skip`), cùng định dạng `eval/cases_h4.json` |
| `LOCK.md` | Mã băm sha256 lúc khoá |

Chạy: `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 python run_server.py eval/run_pseudo.py real_v1/cases_real_v1_labeled.json real_v1`.
Tài liệu: `docs/eval 3 ngày/`.

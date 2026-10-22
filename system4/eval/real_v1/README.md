# Bộ real_v1 cho System 4 (Friendly)

Du lịch văn bản (UIT-ViQuAD2.0), Y tế (hungnm/vietnamese-medical-qa) và 40 câu phần bảng. **Đã khoá ngày 21/10/2026** (xem `LOCK.md`).

| File | Là gì |
|---|---|
| `collect_real_v1_s4.py` | Sinh `cases_real_v1_s4.json` (cùng `SEED`) |
| `cases_real_v1_s4.json` | 160 câu hỏi (75 Du lịch văn bản + 85 Y tế) |
| `cases_real_v1_s4_bang.json` | 40 câu phần bảng (Y tế 14, Giáo dục 13, Du lịch 13) |
| `real_v1_s4_labels_A.json`, `real_v1_s4_labels_B.json` | Nhãn hai lượt gán độc lập |
| `real_v1_s4_labels_final.json` | Nhãn cuối (200 câu, có `drop`) |
| `cases_real_v1_s4_labeled.json` | **Bộ để chạy**: 177 câu (bỏ 23 `drop`); mỗi câu có `check` (`any`, `all`, `refusal`, `ask_back`, `num`) hoặc `urgent`/`needs_image` (Y tế) |
| `LOCK.md` | Mã băm sha256 lúc khoá |

Chưa có runner cho bộ này; cần adapter cho `system4/eval/bench.py` (phải hỏi trưởng nhóm trước khi chạy GPU/LLM). Độ đồng thuận: `python eval/real_v1/real_v1_agree.py --s4`.
Tài liệu: `docs/eval 3 ngày/`.

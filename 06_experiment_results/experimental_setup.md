# Experimental Setup

- **Máy chạy:** một laptop có NVIDIA GeForce RTX 4050 (6 GB). Model chạy tại máy qua Ollama: `qwen3:4b-instruct-2507-q4_K_M` và `bge-m3`. Reranker `bge-reranker-v2-m3` chạy bằng transformers trên GPU. Không gọi API nào bên ngoài.
- **Dữ liệu thủ tục:** `data/runtime/knowledge/3-423eff02f8.db`, bản thu ngày 13/10/2026.
- **Canh nhiệt:** chạy bằng `eval/thermal.py`. Máy tạm dừng giữa các câu khi CPU hoặc GPU đạt ngưỡng `THERMAL_LIMIT`, và chạy tiếp khi nhiệt về `THERMAL_RESUME`.
  - Từ ngày 25/10 dùng ngưỡng 60/52 °C, `THERMAL_DUTY=1.0`.
  - Lượt real_v4: CPU cao nhất 68,1 °C, không có lần đọc nào từ 70 °C trở lên.
  - Phân tích sau (27/10): ngưỡng 65/57 °C. Lượt bỏ từng luật đạt đỉnh 69,1 °C. Lượt tính embedding cho cổng học: GPU 52 °C.
  - Trần cho phép: 70 °C tới 26/10, 80 °C từ 27/10 (trưởng nhóm duyệt).
  - Các lượt trước đó trong ngày 25/10 có 52 lần đọc từ 70 °C trở lên. Đỉnh 87 °C xảy ra lúc 15:39–15:45 khi lượt đánh giá đang tạm dừng (xem `eval/results/thermal.csv`).
- **Code đóng băng theo từng lượt test:**

| Lượt | Bộ test | Commit code | Khoá bộ test |
|---|---|---|---|
| Vòng 1, các cấu hình A/B/C | real_v2 (313) | `b7010d1` | `7e78438` |
| Baseline RAG, prompt v2 | real_v2 | `65b55af` | `7e78438` |
| Vòng 2: off, A, A+B, A2+B, RAG | real_v4 (363) | `88cabd6` | thứ tự `5499d0f`, nhãn `a79ec5f` |
| Golden 518 câu, chạy lại ở code đóng băng | golden blind | `4bb4cfc` | — |
| Sau (*post hoc*): bỏ từng luật, chỉ cổng, cổng naive Bayes | real_v2, real_v4 | `a870122` | như trên |
| Sau: cổng hồi quy logistic trên BGE-M3 | real_v2, real_v4 | `89e077e` | như trên |
| Sau: McNemar cặp và khoảng bootstrap | (đọc kết quả đã có) | `c7e47da`, sửa làm tròn `9daef1c` | — |

- **Lệnh chạy:**
  - `bash eval/hard/final_runs.sh` (vòng 1)
  - `python run_server.py eval/hard/rag4b.py --final real_v2 --name real_v2_rag4b`
  - `bash eval/hard/final_runs_v4.sh` (vòng 2; kế hoạch ghi ở `eval/real_v4/RUN_PLAN.md`)
  - `bash eval/hard/ablation_runs.sh`, `python run_server.py eval/hard/learned_gate.py`, `python run_server.py eval/hard/learned_gate_emb.py`, `python eval/hard/paired_stats.py` (phân tích sau)
- **Kiểm hồi quy:**
  - Golden thu-tuc (`eval/hard/regress.sh`): hàng blind có 518 câu.
  - Unit test (`eval/run_tests.py`): chạy với TMP đặt trên ổ D:.

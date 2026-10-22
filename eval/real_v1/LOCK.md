# Khoá bộ real_v1 System 3 (2026-10-21)

Từ thời điểm này **không sửa** câu hỏi và nhãn theo kết quả của hệ thống. Cần chỉnh thì làm bộ mới. Mã băm bên dưới chứng minh nội dung lúc khoá; đổi một ký tự là mã băm đổi.

| File | sha256 |
|---|---|
| `eval/real_v1/cases_real_v1.json` (300 câu hỏi, chưa nhãn) | `72a5e2dc34fbffd348ed77eff7b5faaad14cc79001808b2c8454c62bca1ff8e7` |
| `eval/real_v1/real_v1_labels_A.json` (nhãn lượt A) | `dbf81f2a25e60b403cef16619ca0b4c3a6adce6c96d574b25c7a301e1587871b` |
| `eval/real_v1/real_v1_labels_B.json` (nhãn lượt B) | `1bbdfba2be62ddccf1baf8dfddfd5bd5b0003fbae25743de8c7a7589ae9b4da1` |
| `eval/real_v1/real_v1_labels_final.json` (nhãn cuối, 300 câu) | `c9639bd38dffeaee3508ac55d017232db0a235d3b2f68acd9a6a5895976cb719` |
| `eval/real_v1/cases_real_v1_labeled.json` (bộ để chạy, bỏ `skip`) | `06c3e96d9e101de513d9b7f41bf012cd5b23533131601b9610120bfbd01ab8a1` |

Bộ để chạy: 282 câu (`answer` 55, `clarify` 7, `apologize` 220); 18 câu `skip` bị loại.

Dữ liệu thủ tục dùng để gán nhãn và để chạy: **bản 3** (cào 13/10/2026, 1.517 thủ tục), `content_sha256` `70c42af175762bb5e91616ecf9f07cdef218ac557b195e7e00898bdafdaa36bd`; `data/snapshot/procedures_v3.jsonl` sha256 `60aea05f28daef36c7fef550d64470f1fc8633b817f3e0e4c5361ab4e0106b30`.

Nhãn do hai lượt AI gán (A: Claude, B: subagent Claude, độc lập), κ ba lớp 0,753, thống nhất và duyệt bởi chủ dự án ngày 21/10; chưa có lượt kiểm của người trên mẫu. Chi tiết: `docs/eval 3 ngày/BAO_CAO_GAN_NHAN_A_B.md`, lý do từng câu: `eval/real_v1/REAL_V1_ASSUMPTIONS.md`.

Việc tiếp theo: chạy hệ thống **một lần** (`S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`, `run_pseudo.py`), lưu kết quả thô vào `eval/saved_results/`.

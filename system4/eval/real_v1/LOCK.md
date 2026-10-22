# Khoá bộ real_v1 System 4 (2026-10-21)

Từ thời điểm này **không sửa** câu hỏi và nhãn theo kết quả của hệ thống. Cần chỉnh thì làm bộ mới.

| File | sha256 |
|---|---|
| `system4/eval/real_v1/cases_real_v1_s4.json` (160 câu hỏi Du lịch văn bản và Y tế) | `f3494a5551b0a9cb91b5aefa95c3de97136d2bebbf22d9d400616f4881b6c82f` |
| `system4/eval/real_v1/cases_real_v1_s4_bang.json` (40 câu phần bảng) | `35d113cc8e4ff47f27a272509a25e80a41febc6164dd0ae8ef428e229fec99aa` |
| `system4/eval/real_v1/real_v1_s4_labels_A.json` | `44ddb8c73b6c2bbc37f335a675a797a310cf3bfa09ef74c80e11e569b8079fee` |
| `system4/eval/real_v1/real_v1_s4_labels_B.json` | `36a9d1db055165e926ad2d0e0889cf7ee9916dddacb5514f3aada8586694a103` |
| `system4/eval/real_v1/real_v1_s4_labels_final.json` (nhãn cuối, 200 câu) | `eb49b01c0e020823df5360e8c3b662b2228785b96f7d3cf912d7572c193b4036` |
| `system4/eval/real_v1/cases_real_v1_s4_labeled.json` (bộ để chạy, bỏ `drop`) | `c3c1e70eb9e7aed0491ccc5a92efd1c7aa9aa053cbc4d5b2a67ce0255dd73881` |

Bộ để chạy: 177 câu (Du lịch văn bản 53, Y tế 85, bảng 39); 23 câu `drop` bị loại.

Dữ liệu hệ thống dùng: `system4/eval/real_domains/data/` (Wikipedia tiếng Việt tải 10/2026: 3 bảng Excel, `du_lich_diem_den.md`, `y_te_hoi_dap_bac_si.md`, Luật Giáo dục 2019); mã băm trong `system4/eval/real_domains/data/manifest.json`.

Nguồn câu hỏi: UIT-ViQuAD2.0 (Du lịch văn bản), hungnm/vietnamese-medical-qa (Y tế), 40 câu phần bảng soạn khi chỉ nhìn tên cột và được `hwng` duyệt từng câu. Nhãn do hai lượt AI gán độc lập, thống nhất và duyệt ngày 21/10. Chi tiết: `docs/eval 3 ngày/BAO_CAO_GAN_NHAN_A_B.md`.

Lưu ý khi chạy: bộ này chưa có runner riêng; cần adapter cho `bench.py` (chạy cần Ollama và model, phải hỏi trưởng nhóm trước khi chạy GPU/LLM).

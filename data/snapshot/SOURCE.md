# Nguồn snapshot
- Repo V10.6: `D:\Finale_architect\repo\Database\`
- `procedures.jsonl` <- `staging\procedures.jsonl` (1.350 bản ghi cấp Xã/Phường)
- `schema_procedures.sql` <- `pipeline\schema_procedures.sql`
- Chép nguyên văn ngày 2026-10-05. Cập nhật dữ liệu: chép đè hai tệp rồi chạy `python -m system3.data.build`.
- `team_corpus.json` <- nhánh `V10.6` (commit 83567403), `Database/corpus/normalized_procedures.json` (70 thủ tục tuyển chọn của nhóm, lệ phí chuẩn hóa). Chép bằng `git show V10.6:Database/corpus/normalized_procedures.json` ngày 2026-10-07. Dùng bởi `data/team_overlay.py`: chỉ bù lệ phí cho thủ tục cổng không có lệ phí, khớp tên chính xác.
- `procedures_v3.jsonl` <- **thủ tục phiên bản 3** (dữ liệu chính thức, quyết định D4): `system4/runtime/procs/versions/3.jsonl`, nhãn "Cào 13/10/2026 15:45", cào từ dichvucong.gov.vn, 1.517 thủ tục, 34 tỉnh, link Cổng dạng UUID. sha256 tệp `60aea05f28daef36c7fef550d64470f1fc8633b817f3e0e4c5361ab4e0106b30`; content_sha256 sau khi dựng `70c42af1…36bd` (khớp số eval trong `docs/KET_QUA_THUC_THI_2026-10-23.md`). Chép vào git ngày 2026-10-20. Chỉ là bản lưu trong git; code chưa tự nạp tệp này (System 4 đọc bản 3 từ `system4/runtime/procs/versions/3.jsonl`).

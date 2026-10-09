# Nguồn snapshot
- Repo V10.6: `D:\Finale_architect\repo\Database\`
- `procedures.jsonl` <- `staging\procedures.jsonl` (1.350 bản ghi cấp Xã/Phường)
- `schema_procedures.sql` <- `pipeline\schema_procedures.sql`
- Chép nguyên văn ngày 2026-10-05. Cập nhật dữ liệu: chép đè hai tệp rồi chạy `python -m system3.data.build`.
- `team_corpus.json` <- nhánh `V10.6` (commit 83567403), `Database/corpus/normalized_procedures.json` (70 thủ tục tuyển chọn của nhóm, lệ phí chuẩn hóa). Chép bằng `git show V10.6:Database/corpus/normalized_procedures.json` ngày 2026-10-07. Dùng bởi `data/team_overlay.py`: chỉ bù lệ phí cho thủ tục cổng không có lệ phí, khớp tên chính xác.

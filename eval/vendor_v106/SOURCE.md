# Nguồn mã V10.6 (vendor)

Mã retrieval cũ của repo nhóm, lấy lại để `eval/build_cases.py`, `eval/baseline_adapter.py` dựng lại được mà không cần `repo/` cạnh `system3`.

- Repo: clone của repo nhóm (`<ROOT>/repo`, chỉ đọc), nhánh/tag `V10.6`
- Commit: `83567403c61b65a9f447b13f8f023527dc15fb97`
- Ngày lấy: 2026-10-07
- Giấy phép: repo nguồn không có file LICENSE ở gốc (`git ls-tree V10.6` không có LICENSE/COPYING); mã của chính nhóm, chép nguyên văn.

## File (đường dẫn giữ nguyên `Database/pipeline/` để `from Database.pipeline import ...` chạy y nguyên)
| file | byte |
|---|---|
| `Database/pipeline/__init__.py` | 85 |
| `Database/pipeline/retrieval.py` | 40.405 |
| `Database/pipeline/search.py` | 7.571 (retrieval import) |
| `Database/pipeline/textutil.py` | 2.265 |
| `Database/pipeline/paths.py` | 4.338 (import_db import; `SCHEMA_PATH` = cạnh file) |
| `Database/pipeline/import_db.py` | 13.350 |
| `Database/pipeline/schema_procedures.sql` | 12.456 |

Tổng ~80 KB. Hai file `normalize` và `vocabulary` của V10.6 KHÔNG chép: không file nào trong chuỗi import của `build_cases.py`/`baseline_adapter.py` dùng chúng (normalize chỉ dùng khi cào dữ liệu thô; `retrieval.py` thử `from db.repositories import ProcedureSynonyms` (bảng từ đồng nghĩa admin, thuộc `Backend/`) và bắt lỗi nên chạy được không có; baseline vốn đo thế, xem `eval/BASELINE.md`).

## Lệnh đã dùng (từ `<ROOT>/repo`, không checkout)
```
git show V10.6:Database/pipeline/__init__.py          > eval/vendor_v106/Database/pipeline/__init__.py
git show V10.6:Database/pipeline/retrieval.py         > .../retrieval.py
git show V10.6:Database/pipeline/search.py            > .../search.py
git show V10.6:Database/pipeline/textutil.py          > .../textutil.py
git show V10.6:Database/pipeline/paths.py             > .../paths.py
git show V10.6:Database/pipeline/import_db.py         > .../import_db.py
git show V10.6:Database/pipeline/schema_procedures.sql > .../schema_procedures.sql
```

## Sửa đổi so với nguồn
**Không có.** Nội dung nguyên văn (có thể kiểm: `git -C repo show V10.6:Database/pipeline/<file> | cmp - <file>`). Import chạy tại chỗ nhờ `eval/_v106.py` thêm `eval/vendor_v106` vào `sys.path` (không phải sửa file vendor).
Lưu ý: tên package top-level `Database` chỉ xuất hiện khi `eval/_v106.py` đã được import; đừng thêm `eval/vendor_v106` vào `PYTHONPATH` chung.

## Dùng
`python run_server.py eval/rebuild_v106_db.py [--force]` dựng `eval/runtime/v106.db` (1.350 thủ tục) từ `data/snapshot/procedures.jsonl` bằng `import_db.import_records`. DB này không commit (`.gitignore`: `eval/runtime/`, `*.db`).

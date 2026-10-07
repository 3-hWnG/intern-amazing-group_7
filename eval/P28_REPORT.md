# Báo cáo Phase 28 — Dựng lại được từ Git (B7), 2026-10-07

Chế độ luật (`S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1`), không gọi Ollama. Không đụng `repo/` (chỉ `git show`), `server/`, `retrieval/`, `data/*`, bộ mù/team, `PLAN_*.md`. Không đổi hành vi/thuật toán.

## Đã làm
1. **`eval/vendor_v106/`**: 7 file `Database/pipeline/` của V10.6 (commit `83567403`): `__init__`, `retrieval`, `search`, `textutil`, `paths`, `import_db`, `schema_procedures.sql` = 83 KB. Chép bằng `git show V10.6:...`, đã `cmp` với nguồn: **không sửa file nào** (import chạy được nhờ `eval/_v106.py` thêm thư mục vào `sys.path`). `normalize.py`/`vocabulary.py` (plan dự kiến) **không chép** vì không nằm trong chuỗi import của `build_cases.py`/`baseline_adapter.py` (`retrieval -> search, import_db -> paths, textutil`). Không có LICENSE trong repo nguồn. `SOURCE.md` ghi commit, ngày, lệnh.
2. **`eval/rebuild_v106_db.py`** dựng `eval/runtime/v106.db` (33 MB, 1.350 thủ tục, ~7 s) từ `data/snapshot/procedures.jsonl` qua `import_db.import_records`; `build_cases.py`/`baseline_adapter.py` tự gọi nó nếu thiếu DB. Mặc định `eval/runtime/v106.db`, đổi bằng `S3_V106_DB`; `S3_REPO` còn để trỏ clone V10.6 thật. Không còn `D:\...` trong `eval/*.py` (đã thêm kiểm vào `check_docs.py`).
3. **Dựng lại bộ ca**: `build_cases.py` + `build_p16/18/19/23.py` chạy lại ra `cases.jsonl` (590 dòng) và `cases_p16_aside.jsonl` **giống từng byte** bản trước (đã `cmp`). Lưu ý: `build_cases.py` ghi đè `cases.jsonl` còn 276 dòng rồi phải chạy tiếp 4 file p*; đã ghi trong REPRODUCE.md. Tôi không đọc/chạy gì của bộ mù (`cases_h*` v.v.).
4. **`eval/run_all.py` + `REPRODUCE.md`**: dựng 2 DB, test_data, 7 test server + smoke_test + selftest, DEV (`run.py`), run_ctx (+ctx-p23), run_concise `--no-blind`, run_p26, synth, perturb, baseline V10.6, check_docs; in bảng số kèm ngưỡng, exit 0 nếu đạt hết. `--quick` bỏ synth+perturb. `--with-blind` (mặc định tắt) chỉ gọi `run_pseudo.py`/`run_team.py`, bỏ đầu ra. Một bước hỏng không làm dừng các bước sau.
5. **Sửa phát hiện từ kiểm clone**: `answer_adapter`, `planner_adapter`, `policy_adapter`, `run_p26` ghi cứng `ROOT/system3/server` vào `sys.path` nên hỏng ngay khi thư mục clone không tên `system3` (Phase 24 mới sửa `run_server.py` chứ chưa chạy `run.py` ở thư mục lạ, đúng như P24_REPORT thừa nhận). Đổi thành `eval/../server`. Chỉ đường dẫn import, không đổi hành vi.
6. **Docs**: README (dòng baseline, mục dựng lại, bảng thư mục), docs/SETUP, CONTRIBUTING, EVAL, KNOWN_ISSUES (hạn chế), eval/README (biến môi trường, mục Phase 28), `build_p16.py` (docstring cũ nói repo không còn); `check_docs.py` thêm REPRODUCE/SOURCE vào danh sách, kiểm không còn đường dẫn cứng trong `eval/*.py`, kiểm vendor đủ file + commit, và bỏ qua `v106*.json` khi chọn "kết quả DEV mới nhất". `.gitignore`: thêm `eval/runtime/`.

## Số chạy lại vs số cũ
**Baseline V10.6** (`baseline_adapter`, mã vendor + DB dựng lại, 185 câu gốc trong `results/baseline.json`):
| | top-1 | top-3 | hành vi |
|---|---|---|---|
| `baseline.json` (cũ) | 10,6% (15/141) | 17,7% (25/141) | 31,9% (59/185) |
| chạy lại | 10,7% (15/140) | 17,1% (24/140) | 31,4% (58/185) |
Lệch lớn nhất 0,59 điểm % (< 2). Nguyên nhân khác biệt: **đầu ra retrieval giống hệt ở cả 185 câu** (kiểm `extra.top` + `is_strong`); chỉ 1 ca (`typo-15`) đổi điểm vì đáp án của ca đó đã đổi sau baseline (nay `behavior=clarify`, không chấm top-1). Không phải do khác snapshot/phiên bản. Trên DEV cũ 209: 9,1% / 15,2% / 30,6% (số tham khảo, baseline.json không có các ca rule).
**Gate DEV/ctx/…** (main và bản clone giống nhau): DEV cũ 209 top-1 97,0% (159/164), hành vi 97,6%, bịa 0,0%, ngoài phạm vi 30/30; ctx 89/91, ctx-p23 26/26; focus 349/353, task thừa 0/451; synth TRAIN/TEST 96,3%/96,4%, glued TEST 96,1%; perturb 99,44% (7.056/7.096); p26 92/92; mọi test xanh. **Khớp số P24/P26, không đổi.**

## Kiểm đầu-cuối
Sao chép `system3` theo `.gitignore` (kể cả whitelist `eval/results`) sang `%TEMP%\xyz_clone\intern_x` (không có `repo/`, không `data/runtime`, `eval/runtime`, `__pycache__`), không đặt `PYTHONPATH`: `python run_server.py eval/run_all.py` -> **37/37 đạt, 438 s** (synth 109 s, perturb 222 s). Lần chạy đầu thất bại ở `run.py` vì mục 5 (đã sửa), rồi chạy lại sạch. Đã xoá thư mục tạm. Bản `--quick` ở cây chính: 29/29, ~90 s. Không cần thêm file nào vào whitelist: bảng chỉ dùng `baseline.json` (đã có trong whitelist). `check_docs.py`: 0 lỗi.

## Chưa làm / nói thẳng
- Số bộ mù/team không dựng lại được bằng script (cố ý); `run_all.py` không kiểm README về chúng.
- Chưa chạy `run_all.py` trên máy/venv sạch khác Python 3.12.2 này.
- `eval/build_composer_set.py` (của việc khác đang làm song song, Phase 27) còn `ROOT/system3/server` cứng như bốn file đã sửa; không đụng để khỏi chồng chéo. `data/DATA_NOTES.md`, `data/snapshot/SOURCE.md` vẫn ghi `D:\...` (không được sửa `data/*`).
- `retrieval.py` V10.6 vẫn thiếu bảng từ đồng nghĩa admin (thuộc `Backend/`): giống lúc đo baseline, nên số baseline là "không có synonyms admin".
- `ollama ps` cuối phiên **không trống**: có `qwen3:4b` nạp (hết sau ~29 phút) do tiến trình khác, không phải của phase này (mọi lệnh của tôi `S3_USE_LLM=0`, `smoke_test` cũng vậy).

## File đổi/mới và dung lượng thêm vào Git
Mới: `eval/vendor_v106/` (7 file + `SOURCE.md`, 83 KB), `eval/_v106.py`, `rebuild_v106_db.py`, `run_all.py`, `p28_baseline_cmp.py`, `REPRODUCE.md`, `P28_REPORT.md`. Sửa: `baseline_adapter.py`, `build_cases.py`, `answer_adapter.py`, `planner_adapter.py`, `policy_adapter.py`, `run_p26.py`, `build_p16.py` (docstring), `check_docs.py`, `.gitignore`, `README.md`, `eval/README.md`, `docs/{SETUP,CONTRIBUTING,EVAL,KNOWN_ISSUES}.md`. Thêm vào Git khoảng **100 KB** (vendor 83 KB + ~20 KB script/tài liệu); không có file lớn: `eval/runtime/v106.db` (33 MB) và `results/ra_*.json`, `v106_rerun.json` đã bị ignore. Không commit git.

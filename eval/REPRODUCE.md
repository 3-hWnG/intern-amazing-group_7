# Dựng lại đường đo từ Git (Phase 28)

Mục tiêu: clone `system3` về thư mục tên gì cũng được, **không cần `repo/` (V10.6) cạnh nó, không GPU, không Ollama**, chạy một lệnh và ra bảng số kèm ngưỡng gate.

## Một lệnh
```bash
cd <SYSTEM3>                       # thư mục có run_server.py
pip install -r requirements.txt    # xem docs/SETUP.md
python run_server.py eval/run_all.py            # đầy đủ (~6-8 phút: synth ~3 phút, perturb ~2 phút)
python run_server.py eval/run_all.py --quick    # bỏ synth + perturb (~2 phút)
python run_server.py eval/run_all.py --skip-build   # dùng DB đã có, khỏi dựng lại
python run_server.py eval/run_all.py --only dev,ctx # chỉ vài nhóm: build,tests,dev,ctx,concise,p26,synth,perturb,baseline,docs
```
`run_all.py` tự đặt `S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1` và `PYTHONIOENCODING=utf-8`; exit 0 = mọi gate đạt. Kết quả ghi `eval/results/ra_*.json` (không commit).

## Nó làm gì (theo thứ tự)
| Bước | Lệnh tương đương |
|---|---|
| dựng data DB (`data/runtime/system3.db`, 58 MB) | `python run_server.py -m system3.data.build` |
| dựng DB V10.6 (`eval/runtime/v106.db`, 33 MB) từ `data/snapshot/procedures.jsonl` bằng mã vendor | `python run_server.py eval/rebuild_v106_db.py --force` |
| test | `test_data`, 7 test trong `server/tests/`, `server/smoke_test.py`, `eval/selftest.py` |
| DEV | `eval/run.py --adapter answer_adapter:adapter --split all`; gate DEV cũ 209 (id không bắt đầu `p16/p18/p19/p23`) |
| ctx | `run_ctx.py` (91) và `--split ctx-p23` (26) |
| focus | `run_concise.py --no-blind` |
| p26 | `run_p26.py` |
| synth, perturb | `synth_retrieval.py` (ghi `results/synth.txt`), `perturb.py` |
| baseline V10.6 | `run.py --adapter baseline_adapter:adapter --split dev` rồi `p28_baseline_cmp.py` (so `results/baseline.json`) |
| docs | `check_docs.py` |

## Ngưỡng gate (bảng ở cuối lần chạy)
DEV cũ 209: top-1 >= 95%, hành vi >= 96%, bịa số <= 3%, ngoài phạm vi 30/30. ctx >= 89/91 và ctx-p23 26/26. synth TEST >= 94% (TRAIN-TEST <= 5 điểm, `glued` >= 90%). DEV focus >= 95%, task thừa <= 2%. `perturb` >= 98%. p26 đạt hết. Baseline V10.6 chạy lại lệch <= 2 điểm % so với `baseline.json`. `check_docs` sạch.
Số hiện tại (2026-10-07): DEV cũ 97,0% (159/164) / 97,6% (204/209) / 0,0%; ctx 89/91, ctx-p23 26/26; focus 349/353 (98,9%), task thừa 0/451; p26 92/92; baseline chạy lại 10,7% / 31,4% (cũ 10,6% / 31,9% trên 185 câu): xem `P28_REPORT.md`.

## Mã V10.6 và baseline
`eval/vendor_v106/` là bản chép nguyên văn 7 file `Database/pipeline/` của V10.6 (commit `83567403`, ~80 KB; `SOURCE.md`). `eval/_v106.py` thêm nó vào `sys.path`; `build_cases.py` và `baseline_adapter.py` dùng nó và tự dựng `eval/runtime/v106.db` nếu chưa có. Biến môi trường: `S3_V106_DB` (đổi chỗ đặt DB), `S3_REPO` (dùng một clone V10.6 thật thay vì vendor).
Bộ ca dựng lại: `python run_server.py eval/build_cases.py` rồi `build_p16.py`, `build_p18.py`, `build_p19.py`, `build_p23.py` ra `cases.jsonl` (590 dòng) giống từng byte bản trong Git. **Cẩn thận:** `build_cases.py` GHI ĐÈ `cases.jsonl` (chỉ còn 276 ca gốc + holdout) và các `build_p*.py` nối lại; chạy cả chuỗi, đừng chạy riêng lẻ.

## Bộ mù và bộ team: KHÔNG nằm trong `run_all.py`
HOLDOUT-3/4, pseudo_real 1/2 và bộ team (`cases_h*`, `cases_pseudo_real*`, `cases_team.json`) là bộ nghiệm thu (xem [../docs/EVAL.md](../docs/EVAL.md)): chỉ người điều phối chạy, số ghi vào README. `run_all.py --with-blind` (mặc định TẮT) chỉ gọi `run_pseudo.py` và `run_team.py` rồi bỏ qua đầu ra; không dùng để tune. Số của chúng không dựng lại bằng script ở đây.

## Không commit
`data/runtime/*.db`, `eval/runtime/` (DB V10.6), `eval/results/*` trừ các file mốc nhỏ (`.gitignore`). Commit: `eval/vendor_v106/`, `cases*.jsonl` (mỗi file < 1 MB).

## Hạn chế
- Số bộ mù/bộ team trong README không được `run_all.py` kiểm.
- Thời gian đo trên máy dev (Windows 10, CPU thường); `smoke_test` dùng cổng 8391 (cần cổng rảnh).
- `perturb`/`synth` lệch vài phần mười nếu đổi phiên bản Python/thư viện (chưa thấy trên máy này).

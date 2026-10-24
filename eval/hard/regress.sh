#!/usr/bin/env bash
# Hồi quy cho đợt sửa câu khó: golden thu-tuc (1352 ca) ở chế độ mọi cờ tắt (~ bản gốc) và mặc định mới (A bật), cùng DB bản 3,
# rồi toàn bộ test đơn vị (eval/run_tests.py, DB cố định). Canh nhiệt như các lượt đo.
#   bash eval/hard/regress.sh <thư mục log>
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$REPO/../_bench_v3/regress}"
mkdir -p "$OUT"
cd "$REPO"
export PYTHONIOENCODING=utf-8 THERMAL_LIMIT=66 THERMAL_RESUME=62 THERMAL_DUTY=1.0 THERMAL_LOG="$OUT/thermal.csv"
export TMP="D:/Claude/System 3/_test_tmp" TEMP="D:/Claude/System 3/_test_tmp"
export S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 S3_DATA_DB="$REPO/data/runtime/knowledge/3-423eff02f8.db"
OFF="S3_SCOPE_GATE=0 S3_LEXICON2=0 S3_LETTER_STRIP=0 S3_WEAK_NAME=0 S3_FOCUS=0 S3_ORG_DEFAULT=0"
PY=.venv/Scripts/python.exe
echo "start $(git rev-parse --short HEAD) $(date '+%T')" > "$OUT/stamp.txt"
[ -f eval/results/golden_thu-tuc.json ] && cp -n eval/results/golden_thu-tuc.json "$OUT/golden_thu-tuc.before_24-10.json"   # bản cũ của nhóm (ghi đè bên dưới)
env $OFF $PY run_server.py eval/hard/paced.py eval/run_golden.py thu-tuc --by status > "$OUT/golden_off.log" 2>&1
echo "golden_off $? $(date '+%T')" >> "$OUT/stamp.txt"; cp eval/results/golden_thu-tuc.json "$OUT/golden_off.json"
$PY run_server.py eval/hard/paced.py eval/run_golden.py thu-tuc --by status > "$OUT/golden_A.log" 2>&1
echo "golden_A $? $(date '+%T')" >> "$OUT/stamp.txt"; cp eval/results/golden_thu-tuc.json "$OUT/golden_A.json"
unset S3_DATA_DB S3_PLANNER_MODE
TEST_THERMAL=1 $PY run_server.py eval/run_tests.py > "$OUT/tests.log" 2>&1
echo "tests $? $(date '+%T')" >> "$OUT/stamp.txt"
echo "done $(date '+%T')" >> "$OUT/stamp.txt"

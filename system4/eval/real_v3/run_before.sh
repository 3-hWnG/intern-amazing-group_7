#!/usr/bin/env bash
# Bộ mù real_v3: 4 cấu hình TRƯỚC khi sửa engine (FASTPATH_SQL=false = đúng đường đi của code lúc khoá 7e78438), runtime riêng, kết quả
# niêm phong (system4/eval/results/bench/inst02+v3b_*.json, không mở tới báo cáo cuối). Một lần mỗi cấu hình.
#   bash system4/eval/real_v3/run_before.sh
set -u
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="$REPO/../_bench_v3/sealed_before"
mkdir -p "$OUT"
cd "$REPO"
export PYTHONIOENCODING=utf-8 TMP="D:/Claude/System 3/_test_tmp" TEMP="D:/Claude/System 3/_test_tmp"
export THERMAL_LIMIT=66 THERMAL_RESUME=62 THERMAL_LOG="$OUT/thermal.csv" BENCH_RUNTIME="$REPO/../_bench_v3/before2"
echo "commit $(git rev-parse --short HEAD) $(date '+%F %T')" > "$OUT/stamp.txt"
for cfg in "v3b_rag --set FASTPATH_ENABLED=false --set TABLE_TOOL=false" \
           "v3b_old --set FASTPATH_ENABLED=false" \
           "v3b_fp" \
           "v3b_fpagg --set FASTPATH_AGGREGATE=true"; do
  name="${cfg%% *}"; rest="${cfg#"$name"}"
  # shellcheck disable=SC2086
  .venv/Scripts/python.exe -u system4/eval/bench.py run "inst02+$name" --set FASTPATH_SQL=false $rest --split blind --suites real3 --no-behavior > "$OUT/$name.log" 2>&1
  echo "$name exit=$? $(date '+%T')" >> "$OUT/stamp.txt"
done
echo "all done $(date '+%T')" >> "$OUT/stamp.txt"

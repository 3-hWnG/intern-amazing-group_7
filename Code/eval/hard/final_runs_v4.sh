#!/usr/bin/env bash
# Chạy MỘT lần mỗi cấu hình trên bộ TEST thứ hai real_v4 (System 3), SAU khi đóng băng code. Kế hoạch khai báo trước: eval/real_v4/RUN_PLAN.md.
# Nhãn khoá ở a79ec5f (trước khi sửa message: ae1fd25). Bản cuối vòng 2 (R2FINAL) chọn trên dev595 (real_v1 + real_v2) theo quy tắc ghi trong RUN_PLAN.md, TRƯỚC lượt chạy này.
#   bash eval/hard/final_runs_v4.sh
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$REPO/eval/hard/results/test_v4"
mkdir -p "$OUT"
cd "$REPO"
export PYTHONIOENCODING=utf-8 THERMAL_LIMIT=60 THERMAL_RESUME=52 THERMAL_DUTY=1.0 THERMAL_LOG="$OUT/thermal.csv"
export TMP="D:/Claude/System 3/_test_tmp" TEMP="D:/Claude/System 3/_test_tmp"
echo "commit $(git rev-parse --short HEAD) dirty=$(git status --porcelain -- server retrieval eval/hard data/api.py | wc -l) $(date '+%F %T')" > "$OUT/stamp.txt"
OFF="S3_SCOPE_GATE=0 S3_LEXICON2=0 S3_LETTER_STRIP=0 S3_WEAK_NAME=0 S3_FOCUS=0 S3_ORG_DEFAULT=0"
B_ON_A="S3_SEMANTIC=1 S3_SEM_QUERY=seg S3_SEM_TAU_OOS=-8.0 S3_SEM_TAU_SWAP=2.0 S3_SEM_TAU_RESCUE=99"      # lưới semAseg (vòng 1)
R2FINAL="S3_R2=1 $B_ON_A"      # chọn trên dev595: A+R2+B (cân bằng 0,9163 = A+R2, hoà -> trả lời đúng trọn 88 > 87); A+R2+C tên bị loại (84 < 87)
run() {   # tên, biến môi trường...
  local name="$1"; shift
  env "$@" .venv/Scripts/python.exe run_server.py eval/hard/dev.py --final real_v4 --name "real_v4_$name" > "$OUT/$name.log" 2>&1
  echo "$name exit=$? $(date '+%T')" >> "$OUT/stamp.txt"
  cp "eval/results/real_v4_$name.json" "$OUT/real_v4_$name.json"
}
run off      $OFF                 # bản gốc (mọi cờ tắt)
run A        S3_SEMANTIC=0         # lớp luật vòng 1
run R2final  $R2FINAL              # bản cuối vòng 2
run AB       $B_ON_A               # bản cuối vòng 1 (A + B)
RAG4B_PROMPT=v2 .venv/Scripts/python.exe run_server.py eval/hard/rag4b.py --final real_v4 --name real_v4_rag4b > "$OUT/rag4b.log" 2>&1
echo "rag4b exit=$? $(date '+%T')" >> "$OUT/stamp.txt"
cp eval/results/real_v4_rag4b.json "$OUT/real_v4_rag4b.json"
echo "all done $(date '+%T')" >> "$OUT/stamp.txt"

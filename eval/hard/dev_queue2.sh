#!/usr/bin/env bash
# Hàng đợi DEV (real_v1) thứ hai, sau lượt 1 (dev_queue.sh): bóc tách C (chỉ tên thủ tục, bỏ phân loại ý định), B chấm theo ĐOẠN câu hỏi,
# và kiểm chứng "mọi cờ tắt" ~ bản gốc. Mỗi lúc một việc nặng, canh nhiệt như lượt 1.
#   bash eval/hard/dev_queue2.sh <thư mục log>
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$REPO/../_bench_v3/dev_queue}"
mkdir -p "$OUT"
cd "$REPO"
export PYTHONIOENCODING=utf-8 THERMAL_LIMIT=66 THERMAL_RESUME=62 THERMAL_DUTY=1.0 THERMAL_LOG="$OUT/thermal2.csv"
export TMP="D:/Claude/System 3/_test_tmp" TEMP="D:/Claude/System 3/_test_tmp"
OFF="S3_SCOPE_GATE=0 S3_LEXICON2=0 S3_LETTER_STRIP=0 S3_WEAK_NAME=0 S3_FOCUS=0 S3_ORG_DEFAULT=0"
CACHE="$OUT/reader_cache.jsonl"
echo "start2 $(git rev-parse --short HEAD) $(date '+%T')" >> "$OUT/stamp.txt"
step() {   # tên, lệnh...
  local name="$1"; shift
  "$@" > "$OUT/$name.log" 2>&1
  echo "$name $? $(date '+%T')" >> "$OUT/stamp.txt"
}
PY=.venv/Scripts/python.exe
step dev_off    env $OFF $PY run_server.py eval/hard/dev.py --name dev_off
step dev_Cname  env $OFF S3_READER=1 S3_READER_INTENT=0 S3_READER_CACHE="$CACHE" $PY run_server.py eval/hard/dev.py --name dev_Cname
step dev_ACname env S3_READER=1 S3_READER_INTENT=0 S3_READER_CACHE="$CACHE" $PY run_server.py eval/hard/dev.py --name dev_ACname
ollama stop qwen3:4b-instruct-2507-q4_K_M >/dev/null 2>&1
step semAseg    env S3_SEM_QUERY=seg $PY run_server.py eval/hard/sem_grid.py score --name semAseg
step sem0seg    env $OFF S3_SEM_QUERY=seg $PY run_server.py eval/hard/sem_grid.py score --name sem0seg
echo "done2 $(date '+%T')" >> "$OUT/stamp.txt"

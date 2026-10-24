#!/usr/bin/env bash
# Hàng đợi lượt đo DEV (real_v1) cho phương án B và C, chạy lần lượt (máy không quá 70 °C: mỗi lúc một việc nặng).
#   bash eval/hard/dev_queue.sh <thư mục log>
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$REPO/../_bench_v3/dev_queue}"
mkdir -p "$OUT"
cd "$REPO"
export PYTHONIOENCODING=utf-8 THERMAL_LIMIT=66 THERMAL_RESUME=62 THERMAL_DUTY=1.0 THERMAL_LOG="$OUT/thermal.csv"
export TMP="D:/Claude/System 3/_test_tmp" TEMP="D:/Claude/System 3/_test_tmp"
OFF="S3_SCOPE_GATE=0 S3_LEXICON2=0 S3_LETTER_STRIP=0 S3_WEAK_NAME=0 S3_FOCUS=0 S3_ORG_DEFAULT=0"
echo "start $(git rev-parse --short HEAD) $(date '+%T')" > "$OUT/stamp.txt"
# A chốt (luật, CPU): số dev cuối của phương án A
.venv/Scripts/python.exe -u run_server.py eval/hard/dev.py --name dev_Afinal --dump "$OUT/dev_Afinal.jsonl" > "$OUT/dev_Afinal.log" 2>&1; echo "dev_Afinal $? $(date '+%T')" >> "$OUT/stamp.txt"
ollama stop qwen3:4b-instruct-2507-q4_K_M >/dev/null 2>&1   # nhường VRAM (6 GB) cho bge-m3 + reranker
# B: chấm reranker MỘT lần (A bật / A tắt), rồi mô phỏng lưới ngưỡng
.venv/Scripts/python.exe run_server.py eval/hard/sem_grid.py score --name semA > "$OUT/semA.log" 2>&1; echo "semA $? $(date '+%T')" >> "$OUT/stamp.txt"
env $OFF .venv/Scripts/python.exe run_server.py eval/hard/sem_grid.py score --name sem0 > "$OUT/sem0.log" 2>&1; echo "sem0 $? $(date '+%T')" >> "$OUT/stamp.txt"
# C: model đọc ý định (A tắt), ghi đệm để lượt A+C dùng lại không gọi model
env $OFF S3_READER=1 S3_READER_CACHE="$OUT/reader_cache.jsonl" .venv/Scripts/python.exe run_server.py eval/hard/dev.py --name dev_C > "$OUT/dev_C.log" 2>&1
echo "dev_C $? $(date '+%T')" >> "$OUT/stamp.txt"
S3_READER=1 S3_READER_CACHE="$OUT/reader_cache.jsonl" .venv/Scripts/python.exe run_server.py eval/hard/dev.py --name dev_AC > "$OUT/dev_AC.log" 2>&1
echo "dev_AC $? $(date '+%T')" >> "$OUT/stamp.txt"
echo "done $(date '+%T')" >> "$OUT/stamp.txt"

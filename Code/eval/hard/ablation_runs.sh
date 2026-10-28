#!/usr/bin/env bash
# Phân tích sau (post-hoc, phản biện 27/10): tắt TỪNG luật của A (và "chỉ cổng ngoài phạm vi") trên hai bộ test, code đóng băng (R2 tắt).
# Không cấu hình nào được chọn theo các lượt này; chỉ để biết phần cải thiện của A đến từ đâu. Canh nhiệt 65/57 (trần 80 °C từ 27/10).
#   bash eval/hard/ablation_runs.sh
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"
export PYTHONIOENCODING=utf-8 THERMAL_LIMIT=65 THERMAL_RESUME=57 THERMAL_DUTY=1.0 THERMAL_LOG="$REPO/eval/hard/results/ablation_thermal.csv"
OFF="S3_SCOPE_GATE=0 S3_LEXICON2=0 S3_LETTER_STRIP=0 S3_WEAK_NAME=0 S3_FOCUS=0 S3_ORG_DEFAULT=0"
GATE_ONLY="S3_LEXICON2=0 S3_LETTER_STRIP=0 S3_WEAK_NAME=0 S3_FOCUS=0 S3_ORG_DEFAULT=0"
echo "commit $(git rev-parse --short HEAD) dirty=$(git status --porcelain -- server retrieval | wc -l) $(date '+%F %T')" > eval/hard/results/ablation_stamp.txt
for set in real_v2 real_v4; do
  dir=test; [ "$set" = real_v4 ] && dir=test_v4
  for cfg in "no_strip|S3_LETTER_STRIP=0" "no_lex|S3_LEXICON2=0" "no_weak|S3_WEAK_NAME=0" "no_gate|S3_SCOPE_GATE=0" "no_focus|S3_FOCUS=0" "no_org|S3_ORG_DEFAULT=0" "gate_only|$GATE_ONLY"; do
    n="${cfg%%|*}"; e="${cfg#*|}"
    env S3_SEMANTIC=0 $e .venv/Scripts/python.exe run_server.py eval/hard/dev.py --final $set --name "${set}_abl_$n" > /dev/null 2>&1
    cp "eval/results/${set}_abl_$n.json" "eval/hard/results/$dir/${set}_abl_$n.json"
    echo "$set $n exit=$? $(date '+%T')" >> eval/hard/results/ablation_stamp.txt
  done
done
echo "done $(date '+%T')" >> eval/hard/results/ablation_stamp.txt

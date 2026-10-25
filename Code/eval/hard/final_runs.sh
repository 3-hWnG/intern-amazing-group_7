#!/usr/bin/env bash
# Chạy MỘT lần mỗi cấu hình trên bộ TEST real_v2 (System 3), SAU khi đóng băng code (ghi mã commit vào stamp).
# Bản gốc (base) đã chạy niêm phong ngay sau khi khoá bộ test (commit 7e78438): eval/results/real_v2_base.json.
# Mọi ngưỡng / lựa chọn dưới đây chốt trên DEV real_v1 (eval/hard/sem_grid.py, dev.py) TRƯỚC lượt chạy này; bản cuối = A + B(đoạn)
# theo tiêu chí ghi trong sem_grid.py (cân bằng cao nhất, ràng buộc số câu trả lời đúng trọn không thấp hơn A).
#   bash eval/hard/final_runs.sh <thư mục ghi log>
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$REPO/../_bench_v3/final_s3}"
mkdir -p "$OUT"
cd "$REPO"
export PYTHONIOENCODING=utf-8 THERMAL_LIMIT=62 THERMAL_RESUME=55 THERMAL_DUTY=1.0 THERMAL_LOG="$OUT/thermal.csv"   # 25/10: chặt hơn (lượt có model vượt 70 °C)
export TMP="D:/Claude/System 3/_test_tmp" TEMP="D:/Claude/System 3/_test_tmp"
echo "commit $(git rev-parse --short HEAD) dirty=$(git status --porcelain -- server retrieval eval/hard | wc -l) $(date '+%F %T')" > "$OUT/stamp.txt"
OFF="S3_SCOPE_GATE=0 S3_LEXICON2=0 S3_LETTER_STRIP=0 S3_WEAK_NAME=0 S3_FOCUS=0 S3_ORG_DEFAULT=0"
B_ALONE="S3_SEMANTIC=1 S3_SEM_QUERY=seg S3_SEM_TAU_OOS=-3.5 S3_SEM_TAU_SWAP=0.5 S3_SEM_TAU_RESCUE=0.0"     # lưới sem0seg
B_ON_A="S3_SEMANTIC=1 S3_SEM_QUERY=seg S3_SEM_TAU_OOS=-8.0 S3_SEM_TAU_SWAP=2.0 S3_SEM_TAU_RESCUE=99"        # lưới semAseg
CACHE="$OUT/reader_cache.jsonl"
run() {   # tên, biến môi trường...
  local name="$1"; shift
  env "$@" .venv/Scripts/python.exe run_server.py eval/hard/dev.py --final real_v2 --name "real_v2_$name" > "$OUT/$name.log" 2>&1
  echo "$name exit=$? $(date '+%T')" >> "$OUT/stamp.txt"
}
run off    $OFF                                             # kiểm chứng: code mới, mọi cờ tắt ~ bản gốc niêm phong (thay đổi chỉ nằm sau cờ)
run A      S3_SEMANTIC=0                                    # phương án A: luật đọc câu dân (A1-A6, mặc định bật)
run C      $OFF S3_READER=1 S3_READER_CACHE="$CACHE"        # phương án C: model 4B đọc ý định + tên thủ tục (A tắt)
run AC     S3_READER=1 S3_READER_CACHE="$CACHE"             # bóc tách: A + C đầy đủ
run ACname S3_READER=1 S3_READER_INTENT=0 S3_READER_CACHE="$CACHE"   # bóc tách: A + C chỉ dùng tên thủ tục
ollama stop qwen3:4b-instruct-2507-q4_K_M >/dev/null 2>&1   # nhường VRAM cho bge-m3 + reranker
run B      $OFF $B_ALONE                                    # phương án B: reranker theo nghĩa + ngưỡng (A tắt)
run final  $B_ON_A                                          # BẢN CUỐI (chọn trên dev): A + B
echo "all done $(date '+%T')" >> "$OUT/stamp.txt"

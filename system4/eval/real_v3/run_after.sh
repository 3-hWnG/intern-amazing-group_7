#!/usr/bin/env bash
# Bộ mù real_v3: cấu hình "SAU khi sửa" (README mục đo), chạy MỘT lần mỗi cấu hình, sau khi đóng băng code.
# Runtime: bản sao runtime của lượt "trước" (../_bench_v3/before2: cùng 5 bộ dữ liệu, cùng lượt nạp / chỉ mục), XOÁ kết quả biên dịch đường nhanh
# để server biên dịch + tự kiểm lại với code mới (lộ trình SQL bật). Hai bên trước / sau chỉ khác code biên dịch + trả lời, không khác dữ liệu nạp.
#   v3a_new     engine mới (FASTPATH_SQL=true: SQL trên bảng phẳng đã biên dịch, bật theo bài tự kiểm từng bảng)
#   v3a_sqlraw  mốc bỏ bước biên dịch: AI viết SQL trên bảng thô (cột chữ nguyên văn, không kiểu số, không giá trị mẫu), bật cho mọi bảng
#   bash system4/eval/real_v3/run_after.sh
set -u
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$REPO/../_bench_v3/before2"
RT="$REPO/../_bench_v3/after2"
OUT="$REPO/../_bench_v3/sealed_after"
mkdir -p "$OUT"
cd "$REPO"
if [ -e "$RT" ]; then echo "đã có $RT — không ghi đè"; exit 1; fi
mkdir -p "$RT"
for x in abi chinh_sach_team7.docx datasets fastpath_cues.json knowledge procs qdrant s3.db system4.db; do cp -r "$SRC/$x" "$RT/"; done
.venv/Scripts/python.exe -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); n=c.execute('DELETE FROM fastpath').rowcount; c.commit(); print('xoá', n, 'kết quả biên dịch')" "$RT/system4.db"
export PYTHONIOENCODING=utf-8 TMP="D:/Claude/System 3/_test_tmp" TEMP="D:/Claude/System 3/_test_tmp"
export THERMAL_LIMIT=62 THERMAL_RESUME=55 THERMAL_LOG="$OUT/thermal.csv" BENCH_RUNTIME="$RT"   # 25/10: chặt hơn lượt "trước" (66/62 vượt 70 °C 36% số lần đọc)
echo "commit $(git rev-parse --short HEAD) dirty=$(git status --porcelain -- system4/server system4/eval/bench.py | wc -l) $(date '+%F %T')" > "$OUT/stamp.txt"
for cfg in "v3a_new --set FASTPATH_SQL=true" \
           "v3a_sqlraw --set FASTPATH_SQL=false --set FASTPATH_SQL_RAW=true"; do
  name="${cfg%% *}"; rest="${cfg#"$name"}"
  # shellcheck disable=SC2086
  .venv/Scripts/python.exe -u system4/eval/bench.py run "inst02+$name" $rest --split blind --suites real3 --no-behavior > "$OUT/$name.log" 2>&1
  echo "$name exit=$? $(date '+%T')" >> "$OUT/stamp.txt"
done
echo "all done $(date '+%T')" >> "$OUT/stamp.txt"

"""Chạy LẠI chỉ phần "22 tình huống hành vi" (nv2_behavior.py) cho MỘT cấu hình J3, KHÔNG chạy lại 216 câu.

Vì sao có script này: bench.py và nv2_behavior.py đều thiếu retry khi loopback rớt kết nối thoáng qua (27/10)
-> cả 6 lần chạy J3 chính thức mất trắng dữ liệu hành vi trong im lặng (behavior: None ở mọi file kết quả,
xem LOCK.md mục 4). Cả hai script đã được vá retry sau đó. Chưa từng có kết quả hành vi HỢP LỆ nào được "thấy"
cho 6 cấu hình này -> chạy lại đây là ĐO LẦN ĐẦU cho phần hành vi, không phải chạy lại cấu hình đã có kết quả
(không vi phạm luật "không re-run sau khi đã thấy số"). Script tự chặn nếu file đã có behavior hợp lệ rồi.

Dùng với CÙNG cờ --set đã dùng khi chạy 216 câu của cấu hình đó (xem bảng ở LOCK.md mục 1), ví dụ:

    python system4/eval/behavior_only.py inst02+v4a_before ^
        --set FASTPATH_SQL=true --set FASTPATH_WIDE_TABLE=false --set FASTPATH_ACCENT_FIRST=false ^
        --set FASTPATH_ATTR_GUARD=false --set FASTPATH_CLEAN_SHOW=false

Ghi kết quả hành vi vào ĐÚNG file cũ (system4/eval/results/bench/<tên>.json), giữ nguyên "runs"/"summary" cũ,
chỉ cập nhật field "behavior".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--set", action="append")
    args = ap.parse_args()

    base = re.split(r"[+@]", args.name)[0]
    if base not in bench.PRESETS:
        raise SystemExit(f"tên cấu hình phải bắt đầu bằng một trong {list(bench.PRESETS)}, không phải {args.name!r}")
    settings = dict(bench.PRESETS[base])
    for kv in args.set or []:
        k, v = kv.split("=", 1)
        try:
            settings[k] = json.loads(v)
        except ValueError:
            settings[k] = v

    result_path = bench.OUT_DIR / f"{args.name}.json"
    if not result_path.exists():
        raise SystemExit(f"không thấy file kết quả cũ: {result_path} — chạy 216 câu trước bằng bench.py run")
    res = json.loads(result_path.read_text(encoding="utf-8"))
    if res.get("behavior") is not None:
        raise SystemExit(f"{args.name} ĐÃ CÓ dữ liệu hành vi hợp lệ rồi — không chạy lại (luật không re-run sau khi đã thấy số).")

    print(f"[{args.name}] cài đặt: {settings}")
    bench.unload_models()
    srv = bench.start_server(settings, args.name + "_behavioronly")
    behavior = None
    try:
        out = bench.OUT_DIR / f"{args.name}_nv2.json"
        env = dict(os.environ, PYTHONIOENCODING="utf-8", NV2_OUT=str(out), PYTHONPATH=str(bench.PYROOT))   # cung ly do nhu bench.py
        print("  22 tình huống hành vi (nv2_behavior.py)…")
        proc = subprocess.run([str(bench.PY), str(bench.HERE / "nv2_behavior.py"), bench.BASE], env=env,
                               capture_output=True, timeout=3600, text=True, encoding="utf-8", errors="replace")
        if out.exists():
            behavior = json.loads(out.read_text(encoding="utf-8"))
            print(f"  hành vi: {behavior['summary']['passed']}/{behavior['summary']['total']}")
        else:
            print(f"  !! nv2_behavior.py không ghi được file kết quả (returncode={proc.returncode}).")
            if proc.stdout:
                print(f"  --- stdout (3000 ký tự cuối) ---\n{proc.stdout[-3000:]}")
            if proc.stderr:
                print(f"  --- stderr (3000 ký tự cuối) ---\n{proc.stderr[-3000:]}")
            raise SystemExit(1)
    finally:
        bench.stop_server(srv)

    res["behavior"] = behavior
    result_path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"đã ghi hành vi vào {result_path}")


if __name__ == "__main__":
    main()

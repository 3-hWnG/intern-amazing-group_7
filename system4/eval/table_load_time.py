"""Đo riêng thời gian nạp mỗi bảng của real_v4_s4 (yêu cầu JD mục 3, J3: "thời gian nạp mỗi bảng") —
KHÔNG đụng tới 216 câu/behavior đã đo của 6 cấu hình J3 (dùng runtime riêng, xoá sau khi xong).

    python system4/eval/table_load_time.py

In ra, cho mỗi bảng: thời gian từ lúc POST /s4/datasets tới lúc status="ready" VÀ fastpath (biên dịch + tự
kiểm) xong (ready/error/skipped) — tức đúng mốc mà ensure_datasets() của bench.py tự chờ trước khi nạp bảng
kế tiếp. Dùng cài đặt giống `v4a_after` (đã sửa đủ 4 lỗi, FASTPATH_SQL bật) vì đó là cấu hình chính của bài.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ["BENCH_RUNTIME"] = str(HERE / "bench_runtime_loadtime_probe")   # đặt TRƯỚC khi import bench (bench.py đọc biến này 1 lần lúc import)

sys.path.insert(0, str(HERE))
import bench  # noqa: E402

RUNTIME_PROBE = bench.RUNTIME


def main() -> None:
    settings = dict(bench.PRESETS["inst02"])
    settings.update({"FASTPATH_SQL": True, "FASTPATH_WIDE_TABLE": True, "FASTPATH_ACCENT_FIRST": True,
                      "FASTPATH_ATTR_GUARD": True, "FASTPATH_CLEAN_SHOW": True})
    print(f"[table_load_time] runtime riêng: {RUNTIME_PROBE} (không đụng bench_runtime của J3)")
    print(f"[table_load_time] cài đặt: {settings}")

    bench.unload_models()
    srv = bench.start_server(settings, "table_load_time_probe")
    cl = bench.Client()
    try:
        sys.path.insert(0, str(bench.REPO / "eval"))
        from thermal import guard

        results = []
        for key, path in bench.REAL_V4_S4_FILES.items():
            guard(every=0, label="đo nạp " + path.name)
            t0 = time.time()
            with open(path, "rb") as f:
                r = cl.c.post("/s4/datasets", files={"file": (path.name, f)})
            assert r.status_code == 200, r.text
            ds_id = None
            while time.time() - t0 < 1800:
                d = {x["filename"]: x for x in cl._get("/s4/datasets").json()["datasets"]}.get(path.name, {})
                ds_id = d.get("id")
                fp = cl._get(f"/s4/fastpath/{ds_id}").json().get("status") if ds_id and d.get("status") == "ready" else None
                if d.get("status") == "error" or fp in ("ready", "error", "skipped"):
                    break
                time.sleep(1)
            elapsed = time.time() - t0
            msg = cl._get(f"/s4/fastpath/{ds_id}").json().get("message", "") if ds_id else "(lỗi nạp)"
            print(f"  {path.name:<32} {elapsed:6.1f}s  — {msg[:90]}")
            results.append((key, path.name, round(elapsed, 1)))
    finally:
        bench.stop_server(srv)

    print("\n== Tổng hợp (giây) ==")
    for key, name, elapsed in results:
        print(f"  {key:<18} {name:<32} {elapsed}s")
    print(f"\nTrung vị: {sorted(e for _, _, e in results)[len(results)//2]}s")


if __name__ == "__main__":
    main()

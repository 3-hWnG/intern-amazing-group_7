"""Canh nhiệt khi chạy eval dài (24/10/2026): trưởng nhóm yêu cầu máy không quá 70 °C.

- CPU: vùng nhiệt ACPI `\\_TZ.TZ01` đọc qua bộ đếm hiệu năng Windows (PDH, không cần quyền admin), đơn vị 0,1 K.
  Số này nhảy nhanh (đo lúc rảnh: 56 -> 70 °C trong vài giây), nên dùng trung vị 3 lần đọc liên tiếp, không dùng một lần đọc.
- GPU: `nvidia-smi --query-gpu=temperature.gpu`.

    from thermal import guard          # gọi guard() giữa các câu: nóng >= LIMIT thì ngủ tới khi <= RESUME
    python eval/thermal.py 30          # đọc thử 30 giây, in từng giây

Mọi lần đọc ghi vào `THERMAL_LOG` (CSV, mặc định eval/results/thermal.csv) để báo cáo nhiệt độ thật của cả đợt chạy.
"""
from __future__ import annotations

import csv
import ctypes
import os
import statistics
import subprocess
import sys
import time
from ctypes import wintypes

LIMIT = float(os.environ.get("THERMAL_LIMIT", "68"))     # dừng khi trung vị CPU hoặc GPU >= mức này (chừa 2 °C dưới 70)
RESUME = float(os.environ.get("THERMAL_RESUME", "60"))   # chạy tiếp khi cả hai <= mức này
LOG = os.environ.get("THERMAL_LOG") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "thermal.csv")

_pdh = None


def _cpu_query():
    global _pdh
    if _pdh is None:
        lib = ctypes.WinDLL("pdh.dll")
        q, c = wintypes.HANDLE(), wintypes.HANDLE()
        if lib.PdhOpenQueryW(None, None, ctypes.byref(q)) != 0:
            raise OSError("PdhOpenQueryW")
        path = "\\Thermal Zone Information(\\_TZ.TZ01)\\High Precision Temperature"
        if lib.PdhAddEnglishCounterW(q, ctypes.c_wchar_p(path), None, ctypes.byref(c)) != 0:
            raise OSError("PdhAddEnglishCounterW")
        _pdh = (lib, q, c)
    return _pdh


class _Val(ctypes.Structure):
    _fields_ = [("CStatus", wintypes.DWORD), ("doubleValue", ctypes.c_double)]


def cpu_c() -> float | None:
    try:
        lib, q, c = _cpu_query()
        if lib.PdhCollectQueryData(q) != 0:
            return None
        v = _Val()
        if lib.PdhGetFormattedCounterValue(c, 0x00000200, None, ctypes.byref(v)) != 0:   # PDH_FMT_DOUBLE
            return None
        return round(v.doubleValue / 10 - 273.15, 1)
    except OSError:
        return None


def gpu_c() -> float | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return float(out.stdout.strip().splitlines()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


def _log(row: list) -> None:
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "cpu_c", "gpu_c", "event"])
        w.writerow(row)


def read(n: int = 3, gap: float = 0.4) -> tuple[float | None, float | None]:
    """(trung vị CPU của n lần đọc, GPU). Ghi log."""
    xs = []
    for i in range(n):
        x = cpu_c()
        if x is not None:
            xs.append(x)
        if i < n - 1:
            time.sleep(gap)
    cpu = statistics.median(xs) if xs else None
    gpu = gpu_c()
    _log([time.strftime("%Y-%m-%d %H:%M:%S"), cpu, gpu, ""])
    return cpu, gpu


_last = 0.0


def guard(every: float = 5.0, label: str = "") -> float:
    """Gọi giữa các bước. Đọc nhiệt tối đa mỗi `every` giây; nóng thì ngủ tới khi nguội. Trả số giây đã ngủ."""
    global _last
    now = time.time()
    if now - _last < every:
        return 0.0
    _last = now
    cpu, gpu = read()
    hot = max(x for x in (cpu, gpu, 0.0) if x is not None)
    if hot < LIMIT:
        return 0.0
    t0 = time.time()
    _log([time.strftime("%Y-%m-%d %H:%M:%S"), cpu, gpu, f"pause {label}"])
    print(f"[thermal] {hot:.1f} °C >= {LIMIT} -> tạm dừng ({label})", file=sys.stderr, flush=True)
    while True:
        time.sleep(10)
        cpu, gpu = read()
        hot = max(x for x in (cpu, gpu, 0.0) if x is not None)
        if hot <= RESUME:
            break
    slept = time.time() - t0
    _log([time.strftime("%Y-%m-%d %H:%M:%S"), cpu, gpu, f"resume after {slept:.0f}s"])
    print(f"[thermal] {hot:.1f} °C, chạy tiếp sau {slept:.0f} s", file=sys.stderr, flush=True)
    _last = time.time()
    return slept


def low_priority() -> None:
    """Hạ ưu tiên tiến trình (BELOW_NORMAL) và số luồng tính toán: máy đỡ nóng, người dùng vẫn dùng được."""
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
    except (AttributeError, OSError):
        pass
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(k, "4")


def summary(path: str | None = None) -> dict:
    """Tóm tắt log: số lần đọc, CPU/GPU lớn nhất, số lần đọc >= 70, số lần tạm dừng."""
    rows = list(csv.DictReader(open(path or LOG, encoding="utf-8")))
    cpu = [float(r["cpu_c"]) for r in rows if r["cpu_c"] not in ("", "None")]
    gpu = [float(r["gpu_c"]) for r in rows if r["gpu_c"] not in ("", "None")]
    return {"n": len(rows), "cpu_max": max(cpu, default=None), "cpu_median": statistics.median(cpu) if cpu else None,
            "gpu_max": max(gpu, default=None), "cpu_ge70": sum(x >= 70 for x in cpu), "gpu_ge70": sum(x >= 70 for x in gpu),
            "pauses": sum(r["event"].startswith("pause") for r in rows)}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print(summary(sys.argv[2] if len(sys.argv) > 2 else None))
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "log":          # python eval/thermal.py log <giờ>: ghi nhiệt mỗi 15 s suốt phiên (bằng chứng cho báo cáo)
        end = time.time() + float(sys.argv[2] if len(sys.argv) > 2 else 12) * 3600
        while time.time() < end:
            read()
            time.sleep(15)
        sys.exit()
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    for _ in range(secs):
        print(time.strftime("%H:%M:%S"), "CPU", cpu_c(), "GPU", gpu_c(), flush=True)
        time.sleep(1)

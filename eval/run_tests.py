"""Chạy lần lượt mọi test (server/tests, system4/tests, data/tests, eval/safety, system4/eval/abi) trên DB thủ tục CỐ ĐỊNH
(eval/fixture_db.py), mỗi test một tiến trình, mọi thứ ghi ra thư mục tạm. Không cần mạng, không cần Ollama, không gọi abi.com.vn.
Chạy: python run_server.py eval/run_tests.py [lọc theo tên ...] [--live]
  --live   đọc DB thủ tục đang chạy (data/runtime/system3.db) thay vì fixture — chỉ để xem test nào phụ thuộc dữ liệu.
Mã thoát 0 khi mọi test đạt, trừ các hồi quy đã biết trong KNOWN_FAIL (in riêng)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import fixture_db  # noqa: E402

# (đường dẫn, cách chạy): "path" = run_server.py <path>; "mod" = run_server.py -m <module>
TESTS = [("data/tests/test_data.py", "mod:system3.data.tests.test_data")]
TESTS += [(f"server/tests/{p.name}", "path") for p in sorted((ROOT / "server" / "tests").glob("*_test.py"))]
TESTS += [(f"system4/tests/{p.name}", "path") for p in sorted((ROOT / "system4" / "tests").glob("*test*.py"))]
TESTS += [("system4/eval/abi/test_abi.py", "path"), ("eval/safety/test_pii_injection.py", "path")]

# Hồi quy đã biết, có việc sửa riêng trong kế hoạch: tên test -> việc sửa.
KNOWN_FAIL: dict[str, str] = {"server/tests/p23_input_test.py": "câu khai tử bị tách >1 ý (sửa ở G4.8)"}
# test in "OK" rồi crash lúc tắt (torch/qdrant atexit, P31): coi là đạt nếu đã in dòng kết thúc.
CRASH_ON_EXIT_OK = {"system4/tests/test_nv3.py"}
TIMEOUT = 900


def isolated_env(data_db: str, tmp: str) -> dict:
    env = dict(os.environ)
    env.pop("ABI_API_KEY", None)
    env.update(TEMP=tmp, TMP=tmp, TMPDIR=tmp)   # mọi tempfile của test nằm trong tmp, xoá sau khi chạy (mỗi test S4 chép DB ~60 MB)
    env.update(PYTHONIOENCODING="utf-8", S3_DATA_DB=data_db, S3_DB_PATH=os.path.join(tmp, "s3.db"),
               S4_RUNTIME_DIR=os.path.join(tmp, "s4"), OLLAMA_HOST="http://127.0.0.1:1", S3_USE_LLM="0",
               S3_NO_WARMUP="1", S4_WARMUP="0", S4_ABI_SYNC="0")
    return env


def run_one(path: str, how: str, data_db: str) -> tuple[bool, float, str]:
    tmp = tempfile.mkdtemp(prefix="s3test_")
    args = ["-m", how[4:]] if how.startswith("mod:") else [path]
    t = time.time()
    try:
        r = subprocess.run([sys.executable, str(ROOT / "run_server.py"), *args], cwd=str(ROOT),
                           env=isolated_env(data_db, tmp), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
        out, code = (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired as e:
        out, code = f"HẾT GIỜ {TIMEOUT}s\n{e.stdout or ''}", -1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = code == 0
    if not ok and path in CRASH_ON_EXIT_OK and code not in (0, 1, -1) and "Traceback" not in out:
        ok = True
    return ok, time.time() - t, out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    live = "--live" in sys.argv
    filt = [a for a in sys.argv[1:] if not a.startswith("--")]
    data_db = str(ROOT / "data" / "runtime" / "system3.db") if live else str(fixture_db.ensure(quiet=True))
    print(f"DB thủ tục: {data_db}")
    fails, known = [], []
    for path, how in TESTS:
        if filt and not any(f in path for f in filt):
            continue
        ok, dt, out = run_one(path, how, data_db)
        tag = "PASS" if ok else ("KNOWN" if path in KNOWN_FAIL else "FAIL")
        print(f"{tag:5s} {dt:6.1f}s  {path}", flush=True)
        if not ok:
            (known if path in KNOWN_FAIL else fails).append(path)
            if path not in KNOWN_FAIL or "-v" in sys.argv:
                print("      " + "\n      ".join(out.strip().splitlines()[-15:]))
    for p in known:
        print(f"hồi quy đã biết: {p} — {KNOWN_FAIL[p]}")
    print(f"\n{'ĐẠT' if not fails else 'TRƯỢT'}: {len(fails)} test trượt, {len(known)} hồi quy đã biết")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

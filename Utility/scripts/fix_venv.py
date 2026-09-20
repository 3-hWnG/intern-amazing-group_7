r"""Sua duong dan tuyet doi ben trong .venv sau khi COPY/DI CHUYEN thu muc.
Repoint an absolute-path-baked .venv after it was copied or moved.

    .venv\Scripts\python.exe Utility\scripts\fix_venv.py

Python tren Windows nhung duong dan TUYET DOI vao 3 cho khi tao .venv:
  1. pyvenv.cfg          -> dong "command = ..."
  2. Scripts/activate*   -> bien VIRTUAL_ENV
  3. Scripts/*.exe       -> dong "#!<...>\python.exe" nhung trong file .exe
Copy .venv ma khong sua (3) thi pip.exe / uvicorn.exe chay NHAM .venv cu mot
cach am tham. Script nay sua ca ba, roi tu kiem tra lai bang pip.exe --version.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

VENV = Path(__file__).resolve().parents[2] / ".venv"
ACTIVATE_FILES = ("activate", "activate.bat", "Activate.ps1", "activate.fish",
                  "activate.csh", "activate.nu", "deactivate.bat")


def old_root_from_cfg(cfg: Path) -> str | None:
    """Duong dan .venv CU, doc tu dong 'command = ... -m venv <path>'."""
    for line in cfg.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("command"):
            m = re.search(r"-m\s+venv\s+(.+?)\s*$", line)
            if m:
                return m.group(1).strip().rstrip("\\")
    return None


def main() -> int:
    cfg = VENV / "pyvenv.cfg"
    if not cfg.is_file():
        print(f"[FAIL] khong thay {cfg}")
        return 1

    new = str(VENV)
    old = old_root_from_cfg(cfg)
    if not old:
        print("[SKIP] pyvenv.cfg khong co dong 'command' -> khong biet duong dan cu")
        return 0
    if old.lower() == new.lower():
        print(f"[OK] .venv da dung cho: {new}")
        return 0

    print(f"  cu  : {old}")
    print(f"  moi : {new}")

    # 1 -------------------------------------------------------- pyvenv.cfg --
    cfg.write_text(cfg.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    print("  [1/3] pyvenv.cfg")

    # 2 --------------------------------------------------- activate scripts --
    touched = 0
    for name in ACTIVATE_FILES:
        p = VENV / "Scripts" / name
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if old in text:
            p.write_text(text.replace(old, new), encoding="utf-8")
            touched += 1
    print(f"  [2/3] activate scripts: {touched}")

    # 3 ----------------------------------------------------- .exe shebangs --
    old_b, new_b = old.encode("utf-8"), new.encode("utf-8")
    backups: dict[Path, bytes] = {}
    fixed = 0
    for exe in (VENV / "Scripts").glob("*.exe"):
        data = exe.read_bytes()
        if old_b not in data:
            continue
        backups[exe] = data
        try:
            exe.write_bytes(data.replace(old_b, new_b))
            fixed += 1
        except OSError as err:                      # dang chay -> khong ghi duoc
            print(f"        ! bo qua {exe.name}: {err}")
    print(f"  [3/3] .exe shims: {fixed}")

    # ---------------------------------------------------------- tu kiem tra --
    pip = VENV / "Scripts" / "pip.exe"
    if pip.is_file():
        try:
            out = subprocess.run([str(pip), "--version"], capture_output=True,
                                 text=True, timeout=90).stdout.strip()
        except Exception as err:                    # noqa: BLE001
            out = f"<loi: {err}>"
        if new.lower() in out.lower():
            print(f"  [kiem tra] OK -> {out}")
        else:
            for p, data in backups.items():         # hoan nguyen, khong de hong
                p.write_bytes(data)
            print(f"  [kiem tra] THAT BAI -> {out}")
            print("  Da hoan nguyen cac file .exe. Van dung duoc bang:")
            print(r"      .venv\Scripts\python.exe -m pip ...")
            return 2
    print("[OK] xong.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

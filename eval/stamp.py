"""Dấu phiên bản cho mọi tệp kết quả đo (G0.3): biết số đo nào thuộc code nào, dữ liệu nào, model nào, cài đặt nào.
    from stamp import stamp; stamp(db_path) -> {git, data_version, n_procedures, data_sha256, model, settings_hash}
Chạy riêng: python run_server.py eval/stamp.py [db]
- data_sha256: sha256 của danh sách (proc_id, content_hash) các thủ tục còn hiệu lực — ổn định khi dựng lại cùng dữ liệu
  (khác sha của tệp .db, vốn đổi theo từng lần dựng).
- settings_hash: sha256 các biến môi trường S3_/S4_/LLM_/PLANNER_/OLLAMA_ (bỏ đường dẫn tạm và khoá bí mật)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "eval" / "runtime" / "fixture_snapshot.db"
LIVE = ROOT / "data" / "runtime" / "system3.db"
_ENV_KEEP = re.compile(r"^(S3_|S4_|LLM_|PLANNER_|OLLAMA_)")
_ENV_DROP = re.compile(r"(_DB|_PATH|_DIR|KEY|TOKEN|SECRET|PASSWORD)$|_DB_|RUNTIME")


def _ro(path: Path) -> sqlite3.Connection:
    """Kết nối chỉ đọc; URI dựng bằng as_uri() để đường dẫn có dấu cách / ổ đĩa Windows vẫn đúng."""
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def _git() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", ".", ":!.gitignore"], cwd=ROOT, capture_output=True,
                               text=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except OSError:
        return "unknown"


def _data_version(db: Path) -> str:
    """Tên phiên bản dữ liệu: manifest.json cạnh DB (DB theo phiên bản, G2.1) > fixture > con trỏ của System 4 cho DB đang chạy."""
    man = db.parent / "manifest.json"
    if man.is_file():
        try:
            m = json.loads(man.read_text(encoding="utf-8"))
            for vid, info in (m.get("versions") or {}).items():
                if Path(info.get("file", "")).name == db.name:
                    return f"v{vid} {info.get('label', '')}".strip()
        except (OSError, ValueError):
            pass
    try:
        if db.resolve() == FIXTURE.resolve():
            return "fixture: data/snapshot/procedures.jsonl"
    except OSError:
        pass
    s4 = Path(os.environ.get("S4_RUNTIME_DIR") or ROOT / "system4" / "runtime") / "system4.db"
    if db.resolve() == LIVE.resolve() and s4.is_file():
        try:
            c = _ro(s4)
            r = c.execute("SELECT v FROM meta WHERE k='proc_active'").fetchone()
            c.close()
            return f"live, proc_active={r[0] if r else '?'}"
        except sqlite3.Error:
            pass
    return "unknown: " + db.name


def stamp(db=None, model: str | None = None) -> dict:
    if db is None:
        from system3.data import DB_PATH as db
    db = Path(db)
    n, h = None, None
    try:
        c = _ro(db)
        rows = c.execute("SELECT proc_id, content_hash FROM procedures WHERE status='active' ORDER BY proc_id, content_hash").fetchall()
        c.close()
        n = len(rows)
        h = hashlib.sha256("\n".join(f"{a}\t{b}" for a, b in rows).encode()).hexdigest()
    except sqlite3.Error:
        pass
    if model is None:
        model = (os.environ.get("LLM_MODEL") or "qwen3:4b (mặc định server/config.py)") if os.environ.get("S3_USE_LLM", "1") == "1" else "off (chỉ luật)"
    env = {k: v for k, v in sorted(os.environ.items()) if _ENV_KEEP.search(k) and not _ENV_DROP.search(k)}
    return {"git": _git(), "data_version": _data_version(db), "n_procedures": n, "data_sha256": h, "model": model,
            "settings_hash": hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest()[:16], "settings": env,
            "db": str(db)}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(stamp(sys.argv[1] if len(sys.argv) > 1 else None), ensure_ascii=False, indent=1))

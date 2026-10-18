"""DB thủ tục CỐ ĐỊNH cho test: dựng data/snapshot/procedures.jsonl (1.350 thủ tục, bản Gốc) vào
eval/runtime/fixture_snapshot.db bằng system3.data.build. Không đụng data/runtime/system3.db (DB đang chạy).
Chỉ dựng lại khi snapshot hoặc mã dựng (data/*.py) đổi, hoặc khi có --force.
Chạy: python run_server.py eval/fixture_db.py [--force]"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "eval" / "runtime" / "fixture_snapshot.db"
STAMP = FIXTURE.with_suffix(".sha256")


def source_hash() -> str:
    """sha256 của mọi thứ quyết định nội dung DB: snapshot + mã dựng."""
    h = hashlib.sha256()
    files = [ROOT / "data" / "snapshot" / n for n in ("procedures.jsonl", "schema_procedures.sql", "team_corpus.json")]
    files += sorted((ROOT / "data").glob("*.py"))
    for f in files:
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def ensure(force: bool = False, quiet: bool = False) -> Path:
    """Trả đường dẫn fixture, dựng nếu chưa có hoặc đã cũ."""
    want = source_hash()
    if not force and FIXTURE.exists() and STAMP.exists() and STAMP.read_text().strip() == want:
        if not quiet:
            print(f"fixture còn mới: {FIXTURE}")
        return FIXTURE
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FIXTURE.with_name(FIXTURE.stem + ".building.db")
    env = dict(os.environ, S3_DATA_DB=str(tmp), PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "run_server.py"), "-m", "system3.data.build"],
                       cwd=str(ROOT), env=env, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"dựng fixture lỗi:\n{r.stdout}\n{r.stderr}")
    if not quiet:
        print(r.stdout.strip())
    os.replace(tmp, FIXTURE)
    rep = tmp.with_name(tmp.name + ".report.json")   # báo cáo kiểm của bước dựng (data/checks.py)
    if rep.is_file():
        os.replace(rep, FIXTURE.with_name(FIXTURE.name + ".report.json"))
    STAMP.write_text(want)
    if not quiet:
        print(f"đã dựng fixture: {FIXTURE}")
    return FIXTURE


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ensure(force="--force" in sys.argv)

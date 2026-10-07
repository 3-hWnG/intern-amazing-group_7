"""Dựng DB kiểu V10.6 (retrieval cũ) từ data/snapshot/procedures.jsonl bằng pipeline vendor (import_db).
python rebuild_v106_db.py [--out PATH] [--force]   -> eval/runtime/v106.db (hoặc $S3_V106_DB). Không GPU, ~vài giây."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v106
from Database.pipeline import import_db

SNAP = os.path.join(_v106.HERE, "..", "data", "snapshot", "procedures.jsonl")


def build(out=_v106.DB, force=False):
    if os.path.isfile(out):
        if not force:
            return out
        for ext in ("", "-wal", "-shm"):
            if os.path.isfile(out + ext):
                os.remove(out + ext)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    recs = [json.loads(l) for l in open(SNAP, encoding="utf-8") if l.strip()]
    conn = import_db.connect(out)
    try:
        st = import_db.import_records(conn, recs)
        n = conn.execute("SELECT COUNT(*) FROM procedures WHERE status='active'").fetchone()[0]
    finally:
        conn.close()
    print(f"v106 db: {n} thu tuc active, {st} -> {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=_v106.DB)
    ap.add_argument("--force", action="store_true", help="dựng lại dù đã có")
    a = ap.parse_args()
    build(a.out, a.force)

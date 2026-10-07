"""Quản trị dữ liệu thủ tục của Strict mode (System 3) — NV4, tab "Dữ liệu Strict". Chỉ dev.

- Phiên bản: mỗi phiên bản là một tệp procedures.jsonl (cùng định dạng data/snapshot của System 3) trong runtime/procs/versions.
  Phiên bản đầu tiên = bản chép của data/snapshot/procedures.jsonl ("Gốc"), không bao giờ bị sửa hay xoá.
- Bản nháp: sửa / xoá thủ tục gom vào nháp (bảng proc_draft) dựa trên một phiên bản; "Lưu thành phiên bản" mới tạo tệp mới.
- Chuẩn dữ liệu: bản ghi sửa phải có ĐÚNG các trường và kiểu dữ liệu như dữ liệu gốc (hồ sơ kiểu lấy từ phiên bản Gốc).
- Áp dụng: chạy CHÍNH lệnh dựng DB của System 3 (`system3.data.build`, không sửa) với tệp của phiên bản, ra DB tạm,
  kiểm số thủ tục, rồi thay DB đang dùng (data/runtime/system3.db). System 3 mở kết nối mới mỗi câu hỏi nên dùng ngay.
- Cào: chạy system4/scraper (code V10.3) ở tiến trình riêng; xong thì tạo phiên bản mới + so sánh với bản đang dùng.
"""
from __future__ import annotations
import datetime
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import config, db

DIR = config.RUNTIME_DIR / "procs"
VERSIONS = DIR / "versions"
SCRAPE_DIR = config.RUNTIME_DIR / "scrape"
_lock = threading.Lock()
_cache: dict[int, tuple[list[dict], dict]] = {}
_job: dict = {"kind": None, "state": "idle", "message": "", "started": None}

SCHEMA = """
CREATE TABLE IF NOT EXISTS proc_versions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  label       TEXT NOT NULL,
  source      TEXT NOT NULL,            -- original | edit | scrape
  parent_id   INTEGER,
  n_records   INTEGER NOT NULL DEFAULT 0,
  note        TEXT NOT NULL DEFAULT '',
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS proc_draft (
  proc_id     TEXT PRIMARY KEY,
  data        TEXT                      -- JSON bản ghi mới; NULL = xoá
);
"""


def _s3_data():
    """Module system3.data (chỉ đọc hằng số đường dẫn của System 3)."""
    import system3.data as d
    return d


def init() -> None:
    c = db.conn()
    c.executescript(SCHEMA)
    c.commit()
    c.close()
    VERSIONS.mkdir(parents=True, exist_ok=True)
    if not db.run("SELECT 1 FROM proc_versions LIMIT 1", one=True):
        src = _s3_data().SNAPSHOT / "procedures.jsonl"
        recs = _read(src)
        vid = db.run("INSERT INTO proc_versions(label,source,n_records,note) VALUES ('Gốc','original',?,?)",
                     (len(recs), "Chép từ data/snapshot/procedures.jsonl của System 3"))
        shutil.copy2(src, VERSIONS / f"{vid}.jsonl")
        _meta_set("proc_active", str(vid))


def _meta_get(k: str, default: str = "") -> str:
    r = db.run("SELECT v FROM meta WHERE k=?", (k,), one=True)
    return r["v"] if r else default


def _meta_set(k: str, v: str) -> None:
    db.run("INSERT OR REPLACE INTO meta(k,v) VALUES (?,?)", (k, v))


def _read(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def versions() -> list[dict]:
    return db.run("SELECT * FROM proc_versions ORDER BY id DESC", many=True)


def active_id() -> int:
    return int(_meta_get("proc_active", "0") or 0)


def original_id() -> int:
    return db.run("SELECT MIN(id) id FROM proc_versions", one=True)["id"]


def load(vid: int) -> tuple[list[dict], dict]:
    with _lock:
        if vid not in _cache:
            recs = _read(VERSIONS / f"{vid}.jsonl")
            _cache[vid] = (recs, {r["proc_id"]: r for r in recs})
        return _cache[vid]


# ------------------------------------------------------------- bản nháp
def draft_base() -> int:
    return int(_meta_get("proc_draft_base", "0") or 0) or active_id()


def draft_changes() -> dict[str, dict | None]:
    return {r["proc_id"]: (json.loads(r["data"]) if r["data"] is not None else None)
            for r in db.run("SELECT proc_id, data FROM proc_draft", many=True)}


def view(which: str) -> tuple[list[dict], dict, dict]:
    """which = id phiên bản hoặc 'draft'. Trả (danh sách, theo id, thay đổi của nháp)."""
    if which == "draft":
        recs, by_id = load(draft_base())
        ch = draft_changes()
        out = [ch.get(r["proc_id"], r) for r in recs if not (r["proc_id"] in ch and ch[r["proc_id"]] is None)]
        return out, {r["proc_id"]: r for r in out}, ch
    recs, by_id = load(int(which))
    return recs, by_id, {}


def profile() -> dict[str, list[str]]:
    """Chuẩn dữ liệu: các trường và kiểu (tên kiểu Python) thấy trong phiên bản Gốc."""
    recs, _ = load(original_id())
    prof: dict[str, set] = {}
    for r in recs:
        for k, v in r.items():
            prof.setdefault(k, set()).add(type(v).__name__)
    return {k: sorted(v) for k, v in prof.items()}


def validate(proc_id: str, rec: dict) -> list[str]:
    errs = []
    if not isinstance(rec, dict):
        return ["Bản ghi phải là một đối tượng JSON"]
    prof = profile()
    missing = [k for k in prof if k not in rec]
    extra = [k for k in rec if k not in prof]
    if missing:
        errs.append("Thiếu trường: " + ", ".join(missing))
    if extra:
        errs.append("Trường không có trong chuẩn dữ liệu: " + ", ".join(extra))
    for k, v in rec.items():
        if k in prof and type(v).__name__ not in prof[k]:
            errs.append(f"Trường \"{k}\" phải là kiểu {' / '.join(prof[k])}, đang là {type(v).__name__}")
    if rec.get("proc_id") != proc_id:
        errs.append("Không được đổi mã thủ tục (proc_id)")
    if not str(rec.get("name") or "").strip():
        errs.append("Tên thủ tục không được trống")
    return errs


def draft_put(proc_id: str, rec: dict) -> None:
    if not db.run("SELECT 1 FROM meta WHERE k='proc_draft_base'", one=True):
        _meta_set("proc_draft_base", str(active_id()))
    db.run("INSERT OR REPLACE INTO proc_draft(proc_id,data) VALUES (?,?)",
           (proc_id, None if rec is None else json.dumps(rec, ensure_ascii=False)))


def draft_revert(proc_id: str) -> None:
    db.run("DELETE FROM proc_draft WHERE proc_id=?", (proc_id,))


def draft_discard() -> None:
    db.run("DELETE FROM proc_draft")
    db.run("DELETE FROM meta WHERE k='proc_draft_base'")


def _new_version(recs: list[dict], label: str, source: str, parent: int | None, note: str = "") -> int:
    vid = db.run("INSERT INTO proc_versions(label,source,parent_id,n_records,note) VALUES (?,?,?,?,?)",
                 (label, source, parent, len(recs), note))
    tmp = VERSIONS / f"{vid}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(VERSIONS / f"{vid}.jsonl")
    return vid


def draft_save(label: str) -> int:
    recs, _, ch = view("draft")
    if not ch:
        raise ValueError("Bản nháp chưa có thay đổi nào")
    n_del = sum(1 for v in ch.values() if v is None)
    vid = _new_version(recs, label.strip() or f"Sửa {len(ch)} thủ tục", "edit", draft_base(),
                       f"{len(ch) - n_del} sửa, {n_del} xoá so với phiên bản {draft_base()}")
    draft_discard()
    return vid


def delete_version(vid: int) -> None:
    if vid == original_id():
        raise ValueError("Không xoá được phiên bản Gốc")
    if vid == active_id():
        raise ValueError("Không xoá được phiên bản đang dùng")
    if vid == draft_base() and draft_changes():
        raise ValueError("Bản nháp đang dựa trên phiên bản này")
    db.run("DELETE FROM proc_versions WHERE id=?", (vid,))
    (VERSIONS / f"{vid}.jsonl").unlink(missing_ok=True)
    _cache.pop(vid, None)


# ------------------------------------------------------------- so sánh
def diff(a: str, b: str, limit: int = 300) -> dict:
    _, A, _ = view(a)
    _, B, _ = view(b)
    added = sorted(set(B) - set(A))
    removed = sorted(set(A) - set(B))
    changed = []
    for pid in sorted(set(A) & set(B)):
        if A[pid] != B[pid]:
            changed.append({"proc_id": pid, "name": B[pid].get("name", ""),
                            "fields": sorted(k for k in set(A[pid]) | set(B[pid]) if A[pid].get(k) != B[pid].get(k))})
    return {"added": [{"proc_id": p, "name": B[p].get("name", "")} for p in added[:limit]],
            "removed": [{"proc_id": p, "name": A[p].get("name", "")} for p in removed[:limit]],
            "changed": changed[:limit],
            "counts": {"added": len(added), "removed": len(removed), "changed": len(changed)}}


def diff_record(a: str, b: str, proc_id: str) -> dict:
    _, A, _ = view(a)
    _, B, _ = view(b)
    ra, rb = A.get(proc_id), B.get(proc_id)
    keys = sorted(set(ra or {}) | set(rb or {}))
    return {"proc_id": proc_id, "fields": [{"field": k, "old": (ra or {}).get(k), "new": (rb or {}).get(k)}
                                           for k in keys if (ra or {}).get(k) != (rb or {}).get(k)]}


# ------------------------------------------------------------ việc chạy nền
def job() -> dict:
    out = dict(_job)
    if out["kind"] == "scrape":
        out["progress"] = _scrape_progress()
    return out


def _start(kind: str, target) -> None:
    with _lock:
        if _job["state"] == "running":
            raise ValueError(f"Đang chạy việc khác ({_job['kind']}), hãy đợi xong")
        _job.update(kind=kind, state="running", message="Đang bắt đầu…", started=time.time(), result=None)
    threading.Thread(target=_guard(target), name=f"s4-procs-{kind}", daemon=True).start()


def _guard(fn):
    def run():
        try:
            fn()
        except Exception as e:
            _job.update(state="error", message=f"Lỗi: {e}")
    return run


def _env() -> dict:
    """Môi trường cho tiến trình con: cùng PYTHONPATH với server để import được system3.*"""
    env = dict(os.environ)
    root = str(Path(_s3_data().__file__).parents[2])   # thư mục chứa gói system3 (pyroot); không resolve: system3 là liên kết thư mục
    env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def build_db(src: Path, out: Path) -> int:
    """Dựng DB System 3 từ một tệp procedures.jsonl bằng chính system3.data.build (không sửa), ra tệp `out`."""
    out.unlink(missing_ok=True)
    code = ("import sys, pathlib, system3.data.load as L, system3.data.build as B; p = pathlib.Path(sys.argv[1]); "
            "B.load_snapshot = lambda path=None: L.load_snapshot(p); raise SystemExit(B.main())")
    env = _env()
    env["S3_DATA_DB"] = str(out)
    r = subprocess.run([sys.executable, "-c", code, str(src)], env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800)
    if r.returncode != 0 or not out.is_file():
        raise RuntimeError("Dựng DB thất bại: " + (r.stderr or r.stdout)[-800:])
    import sqlite3
    c = sqlite3.connect(str(out))
    try:
        return c.execute("SELECT COUNT(*) FROM procedures").fetchone()[0]
    finally:
        c.close()


def _swap(new: Path, target: Path) -> None:
    """Đưa DB mới vào CHÍNH tệp DB System 3 đang dùng bằng SQLite backup (chép từng trang), không thay tệp:
    Planner của System 3 giữ một kết nối mở suốt đời tiến trình (planner.py, _conn) nên thay tệp sẽ bị Windows khoá,
    còn trên Linux thì kết nối cũ vẫn đọc tệp cũ. Backup ghi vào tệp đang mở -> mọi kết nối thấy dữ liệu mới."""
    import sqlite3
    last = None
    for _ in range(20):
        src = sqlite3.connect(str(new))
        dst = sqlite3.connect(str(target), timeout=30)
        try:
            src.backup(dst)
            break
        except sqlite3.OperationalError as e:   # đang có lượt đọc giữ khoá: chờ rồi thử lại
            last = e
            time.sleep(0.5)
        finally:
            src.close()
            dst.close()
    else:
        raise RuntimeError(f"Không ghi được vào DB đang dùng: {last}")
    new.unlink(missing_ok=True)


def _reset_s3_caches() -> None:
    """Planner System 3 dựng chỉ mục tên thủ tục trong bộ nhớ một lần (planner.py, _idx). Bỏ chỉ mục đó để lượt hỏi sau
    dựng lại từ DB mới — chỉ đặt lại biến đệm từ bên ngoài, không sửa code System 3."""
    m = sys.modules.get("planner.planner")
    if m is not None and getattr(m, "_idx", None) is not None:
        m._idx = None


def apply(vid: int, wait: bool = False) -> None:
    """Strict mode chuyển sang phiên bản vid."""
    load(vid)   # kiểm tồn tại

    def work():
        _job["message"] = "Đang dựng DB thủ tục từ phiên bản đã chọn (khoảng 1 phút)…"
        target = Path(_s3_data().DB_PATH)
        tmp = target.with_name(target.stem + ".next.db")
        n = build_db(VERSIONS / f"{vid}.jsonl", tmp)
        expected = db.run("SELECT n_records FROM proc_versions WHERE id=?", (vid,), one=True)["n_records"]
        if n != expected:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"DB dựng ra có {n} thủ tục, phiên bản có {expected}: không áp dụng")
        _job["message"] = "Đang thay DB đang dùng…"
        _swap(tmp, target)
        _reset_s3_caches()
        _meta_set("proc_active", str(vid))
        _job.update(state="done", message=f"Strict mode đang dùng phiên bản {vid} ({n} thủ tục).", result={"version": vid, "n": n})

    if wait:
        work()
    else:
        _start("apply", work)


def _scrape_progress() -> dict:
    cat = SCRAPE_DIR / "raw" / "catalog.jsonl"
    total = sum(1 for l in cat.read_text(encoding="utf-8").splitlines() if l.strip()) if cat.is_file() else 0
    det = SCRAPE_DIR / "raw" / "details"
    done = len(list(det.glob("*.json"))) if det.is_dir() else 0
    st = {}
    try:
        st = json.loads((DIR / "scrape_status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {"catalog": total, "details": done, "step": st.get("step"), "message": st.get("message")}


def scrape_log_tail(n: int = 30) -> list[str]:
    p = DIR / "scrape.log"
    if not p.is_file():
        return []
    return p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]


def scrape(limit: int = 0, rps: float = 2.0) -> None:
    """Cào Cổng Dịch vụ công (cần internet). Xong: tạo phiên bản mới, so sánh với phiên bản đang dùng."""
    def work():
        DIR.mkdir(parents=True, exist_ok=True)
        status = DIR / "scrape_status.json"
        status.unlink(missing_ok=True)
        env = _env()
        env["S4_SCRAPE_DIR"] = str(SCRAPE_DIR)
        args = [sys.executable, "-m", "system3.system4.scraper.run", "--status", str(status), "--rps", str(rps)]
        if limit:
            args += ["--limit", str(limit)]
        _job["message"] = "Đang cào (cần internet)…"
        with open(DIR / "scrape.log", "w", encoding="utf-8") as log:
            rc = subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=6 * 3600).returncode
        st = json.loads(status.read_text(encoding="utf-8")) if status.is_file() else {"step": "error", "message": "Không có trạng thái"}
        if rc != 0 or st.get("step") != "done":
            raise RuntimeError(st.get("message") or "Cào thất bại, xem nhật ký")
        recs = _read(Path(st["staging"]))
        if not recs:
            raise RuntimeError("Cào xong nhưng không có thủ tục nào")
        label = "Cào " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M") + (f" (thử {limit})" if limit else "")
        vid = _new_version(recs, label, "scrape", active_id(), f"{len(recs)} thủ tục từ dichvucong.gov.vn")
        d = diff(str(active_id()), str(vid))
        c = d["counts"]
        _job.update(state="done", result={"version": vid, "diff": c},
                    message=f"Đã tạo phiên bản {vid}: {len(recs)} thủ tục · so với bản đang dùng: +{c['added']} mới, "
                            f"−{c['removed']} không còn, {c['changed']} thay đổi. Chưa áp dụng.")

    _start("scrape", work)


def reapply_active() -> str:
    """Dùng sau khi `Set up first time.bat` dựng lại DB từ snapshot: nếu đang dùng phiên bản khác Gốc thì dựng lại theo nó."""
    db.init_db()
    init()
    vid = active_id()
    if vid == original_id():
        return "Đang dùng phiên bản Gốc, không cần làm gì."
    apply(vid, wait=True)
    return _job["message"]


if __name__ == "__main__":   # python -m system3.system4.server.procs reapply   (Set up first time.bat gọi)
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.argv[1:] == ["reapply"]:
        print("  " + reapply_active())
    else:
        print("Dùng: python -m system3.system4.server.procs reapply")

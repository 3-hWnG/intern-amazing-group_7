"""Quản trị dữ liệu thủ tục của Strict mode (System 3) — NV4, tab "Dữ liệu Strict". Chỉ dev.

- Phiên bản: mỗi phiên bản là một tệp procedures.jsonl (cùng định dạng data/snapshot của System 3) trong runtime/procs/versions.
  Phiên bản đầu tiên = bản chép của data/snapshot/procedures.jsonl ("Gốc"), không bao giờ bị sửa hay xoá.
- Bản nháp: sửa / xoá thủ tục gom vào nháp (bảng proc_draft) dựa trên một phiên bản; "Lưu thành phiên bản" mới tạo tệp mới.
- Chuẩn dữ liệu: bản ghi sửa phải có ĐÚNG các trường và kiểu dữ liệu như dữ liệu gốc (hồ sơ kiểu lấy từ phiên bản Gốc).
- G2.1 DB bất biến theo phiên bản: mỗi phiên bản được dựng (CHÍNH lệnh `system3.data.build`) thành một tệp riêng
  data/runtime/knowledge/<vid>-<mã bản dựng>.db, ghi vào knowledge/manifest.json (số thủ tục, sha256, thời gian, báo cáo kiểm).
  Con trỏ DUY NHẤT tới bản đang dùng: system4.db meta.proc_active. System 3 hỏi đường dẫn qua system3.data.active_db_path()
  (hook đăng ký active_db), mọi đệm khoá theo đường dẫn -> đổi bản / quay lui tức thì, không khởi động lại, không ghi đè tệp đang mở.
  Tên tệp kèm mã bản dựng (hash mã nguồn data/*.py): sửa mã dựng thì phiên bản được dựng lại ra tệp mới.
- Giữ bản Gốc + 2 bản cào mới nhất (+ bản đang dùng, bản trước đó để quay lui, gốc của nháp); bản cũ hơn tự dọn sau mỗi lần cào.
- Cào: chạy system4/scraper (code V10.3) ở tiến trình riêng; xong thì tạo phiên bản mới + so sánh với bản đang dùng.
"""
from __future__ import annotations
import datetime
import hashlib
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
    _drop_build(vid)
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
    """Dựng DB System 3 từ một tệp procedures.jsonl bằng chính system3.data.build (không sửa), ra tệp `out`.
    Tiến trình con tự đăng ký gói system3 (run_server.register_package) nên không cần junction/PYTHONPATH."""
    from . import procs_xlsx
    return procs_xlsx.db_from_jsonl(src, out)


# ------------------------------------------------------- DB theo phiên bản (G2.1)
_man_lock = threading.Lock()
_man_cache: dict = {"mtime": None, "data": None}


def knowledge_dir() -> Path:
    """data/runtime/knowledge; S3_KNOWLEDGE_DIR đổi được; runtime System 4 đặt chỗ khác (test, bộ đo) thì nằm cạnh system4.db."""
    if os.environ.get("S3_KNOWLEDGE_DIR"):
        return Path(os.environ["S3_KNOWLEDGE_DIR"])
    if os.environ.get("S4_RUNTIME_DIR"):
        return config.RUNTIME_DIR / "knowledge"
    return Path(_s3_data().ROOT) / "runtime" / "knowledge"


def build_hash() -> str:
    """Mã của bộ dựng (mã nguồn data/*.py + schema): đổi mã dựng -> tệp DB mới cho cùng phiên bản."""
    root = Path(_s3_data().ROOT)
    h = hashlib.sha256()
    for f in sorted(root.glob("*.py")) + [root / "snapshot" / "schema_procedures.sql", root / "snapshot" / "team_corpus.json"]:
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:10]


def manifest() -> dict:
    p = knowledge_dir() / "manifest.json"
    try:
        mt = p.stat().st_mtime_ns
    except OSError:
        return {"versions": {}}
    if _man_cache["mtime"] != mt:
        try:
            _man_cache.update(mtime=mt, data=json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return {"versions": {}}
    return _man_cache["data"]


def _manifest_put(vid: int, info: dict | None) -> None:
    with _man_lock:
        m = json.loads(json.dumps(manifest()))
        m.setdefault("versions", {})
        if info is None:
            m["versions"].pop(str(vid), None)
        else:
            m["versions"][str(vid)] = info
        m["active"] = active_id()   # chỉ để đọc; con trỏ thật ở system4.db meta.proc_active
        p = knowledge_dir() / "manifest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)
        _man_cache["mtime"] = None


def db_path_of(vid: int) -> Path | None:
    """Tệp DB đã dựng của phiên bản, None nếu chưa dựng."""
    info = manifest().get("versions", {}).get(str(vid))
    if not info:
        return None
    p = knowledge_dir() / info["file"]
    return p if p.is_file() else None


def active_db() -> Path | None:
    """Đăng ký cho system3.data.set_active_provider: DB của phiên bản đang dùng."""
    try:
        return db_path_of(active_id())
    except Exception:   # system4.db chưa sẵn sàng: System 3 dùng DB mặc định
        return None


def _content_sha(rows) -> str:
    return hashlib.sha256("\n".join(f"{a}\t{b}" for a, b in sorted(rows)).encode()).hexdigest()


def _ro(path: Path):
    import sqlite3
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def _db_content(path: Path) -> tuple[int, str]:
    c = _ro(path)
    try:
        rows = c.execute("SELECT proc_id, content_hash FROM procedures WHERE status='active'").fetchall()
        return len(rows), _content_sha(rows)
    finally:
        c.close()


def _has_current_schema(path: Path) -> bool:
    c = _ro(path)
    try:
        return "amount_ok" in {r[1] for r in c.execute("PRAGMA table_info(fees_clean)")}
    finally:
        c.close()


def ensure_built(vid: int, msg=None) -> Path:
    """Dựng DB của phiên bản nếu chưa có bản dựng ứng với mã dựng hiện tại. Trả đường dẫn tệp."""
    bh = build_hash()
    info = manifest().get("versions", {}).get(str(vid))
    if info and info.get("build") == bh and db_path_of(vid):
        return db_path_of(vid)
    src = VERSIONS / f"{vid}.jsonl"
    if not src.is_file():
        raise FileNotFoundError(f"không có tệp của phiên bản {vid}")
    kd = knowledge_dir()
    kd.mkdir(parents=True, exist_ok=True)
    out = kd / f"{vid}-{bh}.db"
    tmp = kd / f"{vid}-{bh}.building.db"
    recs, _ = load(vid)
    want = _content_sha([(r["proc_id"], r.get("content_hash") or "") for r in recs])
    seed = os.environ.get("S3_DATA_DB")   # test / bộ đo: DB cố định dựng bằng đúng mã này và đúng dữ liệu -> chép thay vì dựng lại
    if seed and Path(seed).is_file() and _has_current_schema(Path(seed)) and _db_content(Path(seed)) == (len(recs), want):
        shutil.copy2(seed, tmp)
        n = len(recs)
    else:
        if msg:
            msg(f"Đang dựng DB thủ tục của phiên bản {vid} (khoảng 1 phút)…")
        n = build_db(src, tmp)
    if n != len(recs):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"DB dựng ra có {n} thủ tục, phiên bản có {len(recs)}: không dùng")
    rep_p = tmp.with_name(tmp.name + ".report.json")   # báo cáo kiểm của bước dựng (G2.2), nếu có
    report = json.loads(rep_p.read_text(encoding="utf-8")) if rep_p.is_file() else {}
    rep_p.unlink(missing_ok=True)
    os.replace(tmp, out)
    h = hashlib.sha256()
    with open(out, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    old = info.get("file") if info else None
    label = db.run("SELECT label FROM proc_versions WHERE id=?", (vid,), one=True)
    _manifest_put(vid, {"file": out.name, "build": bh, "n": n, "sha256": h.hexdigest(), "content_sha256": want,
                        "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
                        "label": label["label"] if label else "", "report": report})
    if old and old != out.name:
        try:
            (kd / old).unlink(missing_ok=True)   # bản dựng cũ của chính phiên bản này (đang mở trên Windows thì để lại)
        except OSError:
            pass
    return out


def ensure_active(msg=None) -> Path:
    """Khởi động: DB của phiên bản đang dùng phải có (lần đầu sau khi nâng cấp: dựng, chặn tới khi xong)."""
    init()
    return ensure_built(active_id(), msg or (lambda m: print("  [procs] " + m, flush=True)))


def previous_id() -> int:
    return int(_meta_get("proc_prev", "0") or 0)


gate_fn = None   # G2.4: (db đang dùng, db mới) -> {"ok": bool, "reason": str, ...}; procs_gate.py gán khi nạp


def apply(vid: int, wait: bool = False, gate: bool = True) -> None:
    """Strict mode chuyển sang phiên bản vid: dựng DB bất biến của bản đó (nếu chưa có), chạy cổng kiểm (G2.4), rồi đổi con trỏ.
    Không ghi đè tệp đang mở; quay lui = apply(bản trước), tức thì vì tệp còn đó."""
    load(vid)   # kiểm tồn tại

    def work():
        _job["message"] = "Đang dựng DB thủ tục từ phiên bản đã chọn (khoảng 1 phút)…"
        path = ensure_built(vid, lambda m: _job.update(message=m))
        cur = active_id()
        report = None
        if gate and vid != cur and gate_fn is not None:
            _job["message"] = "Đang chạy cổng kiểm (mẫu so khớp + mẫu golden trên DB mới)…"
            report = gate_fn(db_path_of(cur) or ensure_built(cur), path)
            _manifest_put(vid, {**manifest()["versions"][str(vid)], "gate": report})
            if not report.get("ok"):
                raise RuntimeError("Cổng kiểm chặn, không áp dụng: " + report.get("reason", "chỉ số tụt quá ngưỡng"))
        if vid != cur:
            _meta_set("proc_prev", str(cur))
        _meta_set("proc_active", str(vid))
        info = manifest()["versions"][str(vid)]
        _manifest_put(vid, info)
        _job.update(state="done", message=f"Strict mode đang dùng phiên bản {vid} ({info['n']} thủ tục).",
                    result={"version": vid, "n": info["n"], "gate": report})

    if wait:
        work()
    else:
        _start("apply", work)


def cleanup(keep_per_source: int = 2) -> list[int]:
    """Giữ bản Gốc + `keep_per_source` bản mới nhất của mỗi nguồn (cào / sửa), bản đang dùng, bản trước đó, gốc của nháp.
    Xoá tệp .jsonl và DB đã dựng của các bản còn lại. Trả danh sách id đã xoá."""
    keep = {original_id(), active_id(), previous_id(), draft_base()}
    by_src: dict[str, list[int]] = {}
    for v in versions():
        by_src.setdefault(v["source"], []).append(v["id"])
    for ids in by_src.values():
        keep |= set(sorted(ids, reverse=True)[:keep_per_source])
    gone = []
    for v in versions():
        if v["id"] in keep:
            continue
        db.run("DELETE FROM proc_versions WHERE id=?", (v["id"],))
        (VERSIONS / f"{v['id']}.jsonl").unlink(missing_ok=True)
        _drop_build(v["id"])
        _cache.pop(v["id"], None)
        gone.append(v["id"])
    return gone


def _drop_build(vid: int) -> None:
    info = manifest().get("versions", {}).get(str(vid))
    if info:
        try:
            (knowledge_dir() / info["file"]).unlink(missing_ok=True)
        except OSError:
            pass
        _manifest_put(vid, None)


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
        args = [sys.executable, str(Path(_s3_data().__file__).parents[1] / "run_server.py"), "-m", "system3.system4.scraper.run", "--status", str(status), "--rps", str(rps)]
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
        cleanup()   # giữ Gốc + 2 bản cào mới nhất (+ bản đang dùng / bản trước đó)
        d = diff(str(active_id()), str(vid))
        c = d["counts"]
        _job.update(state="done", result={"version": vid, "diff": c},
                    message=f"Đã tạo phiên bản {vid}: {len(recs)} thủ tục · so với bản đang dùng: +{c['added']} mới, "
                            f"−{c['removed']} không còn, {c['changed']} thay đổi. Chưa áp dụng.")

    _start("scrape", work)


def reapply_active() -> str:
    """`Set up first time.bat`: dựng sẵn DB của phiên bản đang dùng (data/runtime/knowledge) để web khởi động nhanh."""
    db.init_db()
    p = ensure_active()
    return f"Phiên bản đang dùng: {active_id()} -> {p}"


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

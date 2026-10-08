"""Bộ dữ liệu người dùng (NV3): lưu tệp, dung lượng, giới hạn bật, và việc nạp chạy nền.

Tệp gốc lưu ở runtime/datasets/<user_id>/<dataset_id>/<tên tệp>. Nạp = đọc + đổi cấu trúc (ingest.py) -> ghi bản ghi
+ chỉ mục từ khoá -> tạo vector (bge-m3) -> Qdrant. Một luồng nạp duy nhất, lần lượt từng tệp, không chặn khung chat.
"""
from __future__ import annotations
import json
import logging
import queue
import re
import shutil
import threading
from pathlib import Path

from . import config, db, ingest, search, settings

log = logging.getLogger("system4.datasets")
_jobs: "queue.Queue[int]" = queue.Queue()
_worker: threading.Thread | None = None
EMBED_BATCH = 32


def folder(user_id: int, ds_id: int) -> Path:
    return config.RUNTIME_DIR / "datasets" / str(user_id) / str(ds_id)


def safe_name(name: str) -> str:
    name = Path(name or "tep").name
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)[:120] or "tep"


# --------------------------------------------------------- dung lượng, giới hạn
def quota(user: dict) -> dict:
    used = db.used_bytes(user["id"])
    limit = None if user["role"] == "dev" else settings.get("USER_QUOTA_MB") * 1024 * 1024
    return {"used": used, "limit": limit, "max_file": None if user["role"] == "dev" else settings.get("MAX_UPLOAD_MB") * 1024 * 1024}


def active_summary(user_id: int) -> dict:
    act = db.active_datasets(user_id)
    n_ds, n_rec = len(act), sum(d["n_records"] for d in act)
    warn = []
    if n_ds > settings.get("ACTIVE_WARN_DATASETS"):
        warn.append(f"Đang bật {n_ds} bộ dữ liệu (khuyên dùng tối đa {settings.get('ACTIVE_WARN_DATASETS')}): AI có thể chậm và tìm kém chính xác hơn.")
    if n_rec > settings.get("ACTIVE_WARN_RECORDS"):
        warn.append(f"Đang bật {n_rec:,} bản ghi (khuyên dùng tối đa {settings.get('ACTIVE_WARN_RECORDS'):,}).".replace(",", "."))
    return {"datasets": n_ds, "records": n_rec, "warnings": warn,
            "max_datasets": settings.get("ACTIVE_MAX_DATASETS"), "max_records": settings.get("ACTIVE_MAX_RECORDS")}


def can_activate(user_id: int, ds: dict) -> str | None:
    """Giới hạn cứng khi bật thêm một bộ dữ liệu. Trả câu báo lỗi hoặc None."""
    act = [d for d in db.active_datasets(user_id) if d["id"] != ds["id"]]
    if len(act) + 1 > settings.get("ACTIVE_MAX_DATASETS"):
        return f"Chỉ được bật tối đa {settings.get('ACTIVE_MAX_DATASETS')} bộ dữ liệu cùng lúc. Hãy tắt bớt một bộ."
    if sum(d["n_records"] for d in act) + ds["n_records"] > settings.get("ACTIVE_MAX_RECORDS"):
        return f"Tổng số bản ghi đang bật sẽ vượt {settings.get('ACTIVE_MAX_RECORDS'):,}. Hãy tắt bớt một bộ.".replace(",", ".")
    return None


# --------------------------------------------------------------- tải lên
def save_upload(user: dict, filename: str, stream, size_hint: int | None = None) -> dict:
    """Ghi tệp theo từng khúc, kiểm cỡ tệp và dung lượng còn lại. Lỗi -> ValueError (câu báo tiếng Việt)."""
    name = safe_name(filename)
    if Path(name).suffix.lower() not in ingest.SUPPORTED:
        raise ValueError(f"Chưa hỗ trợ tệp {Path(name).suffix or '(không đuôi)'}. Hỗ trợ: CSV, Excel (.xlsx), JSON, TXT/MD, Word (.docx), PDF.")
    q = quota(user)
    room = None if q["limit"] is None else q["limit"] - q["used"]
    ds_id = db.create_dataset(user["id"], Path(name).stem, name, 0)
    d = folder(user["id"], ds_id)
    d.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with open(d / name, "wb") as f:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if q["max_file"] is not None and size > q["max_file"]:
                    raise ValueError(f"Tệp quá lớn (tối đa {settings.get('MAX_UPLOAD_MB')} MB mỗi tệp).")
                if room is not None and size > room:
                    raise ValueError(f"Vượt dung lượng {settings.get('USER_QUOTA_MB')} MB. Hãy xoá bớt bộ dữ liệu cũ rồi tải lại.")
                f.write(chunk)
        if size == 0:
            raise ValueError("Tệp rỗng.")
    except Exception:
        shutil.rmtree(d, ignore_errors=True)
        db.run("DELETE FROM datasets WHERE id=?", (ds_id,))
        raise
    db.update_dataset(ds_id, size_bytes=size, status="queued", message="Đang chờ xử lý…")
    enqueue(ds_id)
    return db.get_dataset(ds_id)


def delete(ds: dict) -> None:
    try:
        search.delete_vectors(ds["id"])
    except Exception as e:
        log.warning("xoá vector: %s", e)
    db.delete_records(ds["id"])
    db.run("DELETE FROM datasets WHERE id=?", (ds["id"],))
    shutil.rmtree(folder(ds["user_id"], ds["id"]), ignore_errors=True)


# ------------------------------------------------------------- nạp chạy nền
def enqueue(ds_id: int) -> None:
    global _worker
    _jobs.put(ds_id)
    if _worker is None or not _worker.is_alive():
        _worker = threading.Thread(target=_work, name="s4-ingest", daemon=True)
        _worker.start()


def _work() -> None:
    while True:
        try:
            ds_id = _jobs.get(timeout=5)
        except queue.Empty:
            return   # hết việc: luồng tự dừng, lần tải sau tạo lại
        try:
            process(ds_id)
        except Exception as e:   # không để một tệp lỗi làm dừng cả hàng đợi
            log.exception("nạp dataset %s lỗi", ds_id)
            if db.get_dataset(ds_id):
                db.update_dataset(ds_id, status="error", message=f"Lỗi khi xử lý: {e}")


def process(ds_id: int) -> None:
    ds = db.get_dataset(ds_id)
    if not ds:
        return
    path = folder(ds["user_id"], ds_id) / ds["filename"]
    db.update_dataset(ds_id, status="processing", progress=5, message="Đang đọc tệp…")
    try:
        search.delete_vectors(ds_id)   # chạy lại (sau lỗi / khởi động lại): bỏ phần cũ
    except Exception:
        pass
    db.delete_records(ds_id)
    try:
        overrides = json.loads(ds.get("mapping") or "{}").get("overrides") or {}   # dòng tiêu đề người dùng tự chọn ("Cách đọc")
    except ValueError:
        overrides = {}
    try:
        recs, mapping = ingest.to_records(path, ds["filename"], overrides=overrides)
        if overrides:
            mapping["overrides"] = overrides
    except ingest.IngestError as e:
        db.update_dataset(ds_id, status="error", progress=0, message=str(e))
        return
    db.update_dataset(ds_id, progress=25, message=f"Đang lưu {len(recs)} bản ghi…", mapping=json.dumps(mapping, ensure_ascii=False))
    ids = db.insert_records(ds_id, recs)
    for i in range(0, len(recs), EMBED_BATCH):
        if not db.get_dataset(ds_id):
            return   # người dùng xoá giữa chừng
        batch = recs[i:i + EMBED_BATCH]
        vecs = search.embed([r["text"] for r in batch])
        search.add_vectors(ids[i:i + EMBED_BATCH], vecs, ds_id, ds["user_id"])
        db.update_dataset(ds_id, progress=30 + int(68 * min(len(recs), i + EMBED_BATCH) / len(recs)),
                          message=f"Đang tạo chỉ mục tìm theo nghĩa {min(len(recs), i + EMBED_BATCH)}/{len(recs)}…")
    active = 1 if ds["active"] else 0   # xử lý lại: giữ trạng thái bật/tắt người dùng đã chọn
    if active and can_activate(ds["user_id"], {**ds, "n_records": len(recs)}):
        active = 0   # vượt giới hạn cứng: vẫn sẵn sàng nhưng để tắt
    db.update_dataset(ds_id, status="ready", progress=100, n_records=len(recs), kind=mapping["kind"], active=active,
                      message=ingest.describe(mapping, len(recs)) + ("" if active else " · Đang TẮT vì vượt giới hạn bật"))


def resume_unfinished() -> None:
    """Khởi động server: tệp đang chờ / đang nạp dở (do tắt server) được nạp lại từ đầu; tệp đã đọc bằng cách đọc cũ
    (READER_VERSION nhỏ hơn) được xử lý lại để hưởng bản sửa (vd. nhận đúng dòng tiêu đề cột)."""
    for d in db.run("SELECT id, status, mapping FROM datasets", many=True):
        if d["status"] in ("queued", "processing"):
            enqueue(d["id"])
        elif d["status"] == "ready":
            try:
                reader = json.loads(d["mapping"] or "{}").get("reader", 1)
            except ValueError:
                reader = 1
            if reader < ingest.READER_VERSION:
                db.update_dataset(d["id"], status="queued", message="Đang xử lý lại theo cách đọc tệp mới…")
                enqueue(d["id"])

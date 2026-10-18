"""Nơi lưu dữ liệu ABI theo PHIÊN BẢN (giống "Dữ liệu Strict" của phần thủ tục), trong runtime/abi/:

    versions/<id>/raw.json    bản API gốc của một lần đồng bộ
    versions/<id>/data.json   bản đã chuẩn hoá (code + chỉ mục tìm kiếm đọc từ đây)
    versions.json             {"next_id", "active", "versions": [{id, source, synced_at, checked_at, hash, counts, …}]}
    status.json               lịch sử đồng bộ (HISTORY_KEEP lần gần nhất)

Hai nguồn: "prod" (abi.com.vn) và "staging" (staging.abi.com.vn). Mỗi nguồn chỉ giữ KEEP = 2 phiên bản mới nhất; cũ hơn bị
xoá tự động (versions.prune). data() = dữ liệu của phiên bản ĐANG DÙNG. Ghi kiểu nguyên tử (tệp tạm rồi os.replace).
Bố cục cũ (raw.json + data.json nằm thẳng trong runtime/abi, trước 17/10/2026) tự chuyển thành phiên bản 1 (nguồn prod).
"""
from __future__ import annotations

import json
import os
import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..server import config

KEEP = 2   # số phiên bản giữ lại cho MỖI nguồn
HISTORY_KEEP = 30
_lock = threading.RLock()
_cache: dict = {"key": None, "data": None}
VN = timezone(timedelta(hours=7))


def folder() -> Path:
    return config.RUNTIME_DIR / "abi"


def _path(name: str) -> Path:
    return folder() / name


def write_json(name: str, obj) -> None:
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def read_json(name: str):
    try:
        return json.loads(_path(name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------ danh sách phiên bản
def _now() -> str:
    return datetime.now(VN).isoformat(timespec="seconds")


def _migrate() -> dict:
    """Bố cục cũ -> phiên bản 1 (nguồn prod), đang dùng."""
    ix = {"next_id": 1, "active": None, "versions": []}
    old_raw, old_data = _path("raw.json"), _path("data.json")
    if old_raw.exists() and old_data.exists():
        d = read_json("data.json") or {}
        (folder() / "versions" / "1").mkdir(parents=True, exist_ok=True)
        os.replace(old_raw, folder() / "versions" / "1" / "raw.json")
        os.replace(old_data, folder() / "versions" / "1" / "data.json")
        ix = {"next_id": 2, "active": 1, "versions": [{"id": 1, "source": d.get("source") or "prod", "synced_at": d.get("synced_at"),
                                                       "checked_at": d.get("synced_at"), "created_at": _now(), "hash": None,
                                                       "counts": counts(d), "migrated": True}]}
    write_json("versions.json", ix)
    return ix


def index() -> dict:
    with _lock:
        ix = read_json("versions.json")
        return ix if ix is not None else _migrate()


def _save(ix: dict) -> None:
    write_json("versions.json", ix)


def counts(d: dict | None) -> dict:
    return {k: len((d or {}).get(k) or []) for k in ("departments", "people", "events", "programs", "catalog", "posts", "pages")}


def versions(source: str | None = None) -> list[dict]:
    """Mới nhất trước."""
    vs = sorted(index()["versions"], key=lambda v: v["id"], reverse=True)
    return [v for v in vs if source is None or v["source"] == source]


def get_version(vid: int | None) -> dict | None:
    return next((v for v in index()["versions"] if v["id"] == vid), None) if vid else None


def active_id() -> int | None:
    return index().get("active")


def set_active(vid: int | None) -> None:
    with _lock:
        ix = index()
        if vid is not None and not any(v["id"] == vid for v in ix["versions"]):
            raise ValueError(f"không có phiên bản {vid}")
        ix["active"] = vid
        _save(ix)


def raw(vid: int) -> dict | None:
    return read_json(f"versions/{vid}/raw.json")


def version_data(vid: int) -> dict | None:
    return read_json(f"versions/{vid}/data.json")


def add_version(source: str, raw_obj: dict, data_obj: dict, **meta) -> int:
    with _lock:
        ix = index()
        vid = ix["next_id"]
        write_json(f"versions/{vid}/raw.json", raw_obj)
        write_json(f"versions/{vid}/data.json", data_obj)
        ix["next_id"] = vid + 1
        ix["versions"].append({"id": vid, "source": source, "synced_at": data_obj.get("synced_at"), "checked_at": data_obj.get("synced_at"),
                               "created_at": _now(), "counts": counts(data_obj), **meta})
        _save(ix)
        return vid


def update_version(vid: int, **fields) -> None:
    with _lock:
        ix = index()
        for v in ix["versions"]:
            if v["id"] == vid:
                v.update(fields)
        _save(ix)


def remove_version(vid: int) -> None:
    """Xoá tệp + dòng của một phiên bản (chỉ mục tìm kiếm của nó do versions.py xoá). Không đổi "active"."""
    with _lock:
        ix = index()
        ix["versions"] = [v for v in ix["versions"] if v["id"] != vid]
        _save(ix)
        shutil.rmtree(folder() / "versions" / str(vid), ignore_errors=True)


def data() -> dict | None:
    """data.json của phiên bản đang dùng (None nếu chưa có). Đọc một lần, đọc lại khi đổi phiên bản / tệp đổi."""
    vid = active_id()
    if not vid:
        return None
    p = _path(f"versions/{vid}/data.json")
    try:
        key = (vid, p.stat().st_mtime)
    except OSError:
        return None
    with _lock:
        if _cache["key"] != key:
            _cache.update(key=key, data=read_json(f"versions/{vid}/data.json"))
        return _cache["data"]


# ------------------------------------------------------------------ lịch sử đồng bộ
def status() -> dict:
    return read_json("status.json") or {"runs": []}


def add_run(run: dict) -> None:
    with _lock:
        st = status()
        st["runs"] = ([run] + st.get("runs", []))[:HISTORY_KEEP]
        write_json("status.json", st)

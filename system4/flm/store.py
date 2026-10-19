"""Sổ phiên bản dữ liệu FLM (system4/runtime/flm/versions.json) — giống ABI: mỗi lần đồng bộ mà dữ liệu ĐỔI là một phiên bản,
giữ KEEP = 2 bản mới nhất, đúng một bản "đang dùng". Mỗi phiên bản = một bộ dữ liệu (tệp Excel) trong lĩnh vực FLM.
Dữ liệu tải thêm vào lĩnh vực FLM (không có trong sổ) không bị bật / tắt / xoá theo phiên bản."""
from __future__ import annotations

import json
import threading
from pathlib import Path

from ..server import config

KEEP = 2
_lock = threading.RLock()


def root() -> Path:
    return config.RUNTIME_DIR / "flm"


def _path() -> Path:
    return root() / "versions.json"


def load() -> dict:
    try:
        d = json.loads(_path().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(d: dict) -> None:
    with _lock:
        root().mkdir(parents=True, exist_ok=True)
        tmp = _path().with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(_path())


def versions() -> list[dict]:
    """Mới nhất trước."""
    return sorted(load().get("versions", []), key=lambda v: -v["id"])


def active_id() -> int | None:
    return load().get("active")


def get(vid: int | None) -> dict | None:
    return next((v for v in versions() if v["id"] == vid), None)


def ids_of(v: dict) -> list[int]:
    """Bộ dữ liệu của một phiên bản: tệp bảng (dataset_id) + tệp lịch học (extra_ids, chế độ đăng nhập)."""
    return [i for i in [v.get("dataset_id")] + list(v.get("extra_ids") or []) if i]


def dataset_ids() -> set[int]:
    return {i for v in versions() for i in ids_of(v)}


def is_flm_dataset(ds: dict) -> bool:
    return ds.get("id") in dataset_ids()


def runs() -> list[dict]:
    return load().get("runs", [])


def add_run(r: dict) -> None:
    with _lock:
        d = load()
        d["runs"] = ([r] + d.get("runs", []))[:20]
        save(d)

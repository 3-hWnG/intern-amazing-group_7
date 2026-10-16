"""Nơi lưu dữ liệu ABI: runtime/abi/raw.json (bản API gốc), data.json (đã chuẩn hoá), status.json (lịch sử đồng bộ).

Ghi kiểu nguyên tử (tệp tạm rồi os.replace): đồng bộ hỏng giữa chừng không làm hỏng dữ liệu đang dùng.
data.json đọc một lần rồi giữ trong bộ nhớ, đọc lại khi tệp đổi (đồng bộ xong).
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from ..server import config

_lock = threading.Lock()
_cache: dict = {"mtime": None, "data": None}
HISTORY_KEEP = 30


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


def data() -> dict | None:
    """data.json hiện tại (None nếu chưa đồng bộ lần nào)."""
    p = _path("data.json")
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return None
    with _lock:
        if _cache["mtime"] != mtime:
            _cache.update(mtime=mtime, data=read_json("data.json"))
        return _cache["data"]


def status() -> dict:
    return read_json("status.json") or {"runs": []}


def add_run(run: dict) -> None:
    with _lock:
        st = status()
        st["runs"] = ([run] + st.get("runs", []))[:HISTORY_KEEP]
        write_json("status.json", st)

"""Phiên bản dữ liệu ABI — giống cách "Dữ liệu Strict" quản lý phiên bản thủ tục, nhưng tự dọn:

- Mỗi lần đồng bộ một nguồn (abi.com.vn = "prod", staging.abi.com.vn = "staging") mà dữ liệu ĐỔI thì thành một phiên bản mới.
  Dữ liệu không đổi thì không tạo phiên bản (chỉ ghi "kiểm lúc"), để bản cũ có ý nghĩa không bị đẩy ra.
- Mỗi nguồn giữ store.KEEP = 2 phiên bản mới nhất; cũ hơn bị XOÁ TỰ ĐỘNG cùng chỉ mục tìm kiếm của nó (chỉ trong lĩnh vực ABI).
- Đúng một phiên bản "đang dùng": lĩnh vực ABI trả lời từ phiên bản đó. Chuyển phiên bản tức thì (mỗi phiên bản có chỉ mục riêng).
- Phiên bản mới của một nguồn tự thành "đang dùng" nếu bản đang dùng là bản MỚI NHẤT của chính nguồn đó (đang theo bản mới nhất);
  nếu dev đang chọn bản cũ hơn hoặc nguồn khác thì giữ nguyên lựa chọn. Bản đang dùng bị xoá (quá 2 bản) -> chuyển sang bản mới
  nhất của cùng nguồn.
"""
from __future__ import annotations

import threading

from . import index, store
from .client import SOURCES

_lock = threading.RLock()


def label(source: str) -> str:
    return SOURCES.get(source, {}).get("label", source)


def activate(vid: int) -> None:
    with _lock:
        if not store.get_version(vid):
            raise ValueError(f"không có phiên bản {vid}")
        store.set_active(vid)
        index.set_active(vid)


def follows_latest(source: str) -> bool:
    """Bản đang dùng là bản mới nhất của nguồn này (hoặc chưa có bản nào đang dùng)."""
    act = store.get_version(store.active_id())
    if not act:
        return True
    newest = (store.versions(source) or [None])[0]
    return act["source"] == source and newest is not None and act["id"] == newest["id"]


def prune(source: str) -> list[int]:
    """Giữ store.KEEP phiên bản mới nhất của nguồn; xoá phần còn lại (tệp + chỉ mục). Trả các id đã xoá."""
    with _lock:
        vs = store.versions(source)
        gone = [v["id"] for v in vs[store.KEEP:]]
        act = store.active_id()
        for vid in gone:
            index.drop(vid)
            store.remove_version(vid)
        if act in gone:   # bản đang dùng bị xoá: chuyển sang bản mới nhất của cùng nguồn
            activate(vs[0]["id"])
        return gone


def delete(vid: int) -> None:
    """Xoá tay một phiên bản (không xoá được bản đang dùng)."""
    with _lock:
        if vid == store.active_id():
            raise ValueError("Không xoá được phiên bản đang dùng; chuyển sang phiên bản khác trước")
        if not store.get_version(vid):
            raise ValueError(f"không có phiên bản {vid}")
        index.drop(vid)
        store.remove_version(vid)


def ensure() -> None:
    """Khởi động / trước khi hiện danh sách: chuyển bố cục cũ thành phiên bản, gán chỉ mục cũ, đặt cờ bật đúng bộ dữ liệu."""
    with _lock:
        act = store.active_id()   # store.index() tự chuyển bố cục cũ
        if act is None and store.versions():
            act = store.versions()[0]["id"]
            store.set_active(act)
        index.adopt_legacy(act)
        index.set_active(act)


def listing() -> list[dict]:
    act = store.active_id()
    newest = {s: (store.versions(s) or [{}])[0].get("id") for s in SOURCES}
    out = []
    for v in store.versions():
        ds = index.dataset_of(v["id"])
        out.append({**{k: v.get(k) for k in ("id", "source", "synced_at", "checked_at", "created_at", "counts", "requests", "privacy")},
                    "label": label(v["source"]), "active": v["id"] == act, "newest": newest.get(v["source"]) == v["id"],
                    "dataset": {k: ds[k] for k in ("id", "status", "progress", "n_records", "message")} if ds else None})
    return out

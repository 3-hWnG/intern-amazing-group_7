"""Tự đồng bộ ABI theo ⚙ ABI_SYNC_HOURS (0 = tắt) và API cho trang Quản trị (chỉ dev).

hook.install() gọi start() khi khởi động server (test đặt S4_ABI_SYNC=0 để tắt). Một luồng nền: lúc khởi động và mỗi 10 phút
kiểm tra lần đồng bộ cuối; quá hạn thì chạy sync.run() (bản thân sync.run() không cho hai lần chạy chồng nhau).
"""
from __future__ import annotations

import logging
import threading
import time

from fastapi import APIRouter, HTTPException, Request

from ..server import db, settings
from . import index, normalize, remote, store, sync

log = logging.getLogger("system4.abi.scheduler")
CHECK_EVERY = 600
_thread: threading.Thread | None = None


RETRY_AFTER_ERROR = 1800   # giây: lần đồng bộ trước lỗi (mất mạng…) thì thử lại sau 30 phút, không chờ đủ ABI_SYNC_HOURS


def due() -> bool:
    hours = settings.get("ABI_SYNC_HOURS")
    if hours <= 0:
        return False
    last = next((r for r in store.status().get("runs", []) if r.get("ok") or r.get("error")), None)
    if not last:
        return True
    started = normalize.dt(last.get("started"))
    wait = hours * 3600 if last.get("ok") else min(hours * 3600, RETRY_AFTER_ERROR)
    return not started or (time.time() - started.timestamp()) >= wait


def index_missing() -> bool:
    """Có dữ liệu nhưng chưa có chỉ mục tìm kiếm (lần đồng bộ đầu chạy khi chưa có tài khoản dev / Ollama chưa chạy)."""
    dom = index.domain()
    if not store.data() or not dom or not db.run("SELECT 1 FROM users WHERE role='dev' LIMIT 1", one=True):
        return False
    return not any(d["status"] == "ready" and index.is_abi_dataset(d)
                   for d in db.run("SELECT * FROM datasets WHERE domain_id=?", (dom["id"],), many=True))


def _loop() -> None:
    time.sleep(20)   # để server khởi động xong, model nạp xong
    while True:
        try:
            if due():
                log.info("đồng bộ ABI theo lịch")
                sync.run()
            elif index_missing() and not sync.state()["running"]:
                log.info("dựng chỉ mục ABI còn thiếu")
                index.rebuild(store.data())
        except Exception as e:   # thiếu Ollama…: thử lại ở vòng sau
            log.warning("lịch đồng bộ ABI: %s", e)
        time.sleep(CHECK_EVERY)


def start() -> None:
    global _thread
    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=_loop, name="s4-abi-sync", daemon=True)
        _thread.start()


def start_now() -> bool:
    if sync.state()["running"]:
        return False
    threading.Thread(target=sync.run, name="s4-abi-sync-now", daemon=True).start()
    for _ in range(40):   # chờ luồng nhận việc (tối đa 2 giây) để trạng thái trả về đã là "đang đồng bộ" -> giao diện theo dõi tiếp
        if sync.state()["running"]:
            break
        time.sleep(0.05)
    return True


def summary() -> dict:
    data = store.data() or {}
    dom = index.domain()
    ds = [d for d in db.run("SELECT * FROM datasets WHERE domain_id=?", (dom["id"],), many=True) if index.is_abi_dataset(d)] if dom else []
    return {"state": sync.state(), "runs": store.status().get("runs", [])[:10], "synced_at": data.get("synced_at"),
            "counts": {k: len(data.get(k) or []) for k in ("departments", "people", "events", "programs", "catalog", "posts", "pages")},
            "domain": {"id": dom["id"], "name": dom["name"]} if dom else None,
            "datasets": [{k: d[k] for k in ("id", "status", "progress", "n_records", "message", "active")} for d in ds],
            "remote": remote.status(), "settings": {k: settings.get(k) for k in ("ABI_SYNC_HOURS", "ABI_CODE_ANSWER", "ABI_REMOTE_RAG",
                                                                                  "ABI_SHOW_STAFF_CONTACT", "ABI_REMOTE_MAX_PER_5MIN")}}


def make_router() -> APIRouter:
    r = APIRouter(prefix="/s4/abi")

    def dev(request: Request) -> None:
        u = getattr(request.state, "user", None)
        if not u or u["role"] != "dev":
            raise HTTPException(403, "Chỉ tài khoản dev")

    @r.get("/status")
    def status(request: Request):
        dev(request)
        return summary()

    @r.post("/sync")
    def sync_now(request: Request):
        dev(request)
        return {"started": start_now(), **summary()}

    return r

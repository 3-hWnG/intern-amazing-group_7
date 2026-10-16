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
from . import client, index, normalize, remote, store, sync

log = logging.getLogger("system4.abi.scheduler")
CHECK_EVERY = 600
_thread: threading.Thread | None = None

# Thoả thuận với chủ web (16/10/2026): quét định kỳ 6 tiếng, tối đa 2 request/giây (client.MAX_RPS)
MIN_HOURS = 6              # ⚙ ABI_SYNC_HOURS đặt 1–5 vẫn tính là 6
RETRY_AFTER_ERROR = 3600   # giây: lần trước lỗi (mất mạng…) thì thử lại sau 1 giờ, không chờ đủ 6 giờ
MANUAL_GAP = 600           # giây: nút "Đồng bộ ngay" không chạy lại trong 10 phút sau lần đồng bộ trước


def _last_run() -> dict | None:
    return next((r for r in store.status().get("runs", []) if r.get("ok") or r.get("error")), None)


def _age(run: dict | None) -> float | None:
    started = normalize.dt((run or {}).get("started"))
    return time.time() - started.timestamp() if started else None


def due() -> bool:
    hours = settings.get("ABI_SYNC_HOURS")
    if hours <= 0:
        return False
    last = _last_run()
    if not last:
        return True
    hours = max(hours, MIN_HOURS)
    wait = hours * 3600 if last.get("ok") else min(hours * 3600, RETRY_AFTER_ERROR)
    age = _age(last)
    return age is None or age >= wait


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


def start_now() -> tuple[bool, str]:
    """Nút "Đồng bộ ngay". Trả (đã bắt đầu?, lý do nếu không)."""
    if sync.state()["running"]:
        return False, "Đang đồng bộ, đợi lần này xong."
    age = _age(_last_run())
    if age is not None and age < MANUAL_GAP:   # giữ đúng thoả thuận tần suất với chủ web
        return False, f"Vừa đồng bộ {int(age // 60)} phút trước; đợi thêm {int((MANUAL_GAP - age) // 60) + 1} phút rồi bấm lại."
    threading.Thread(target=sync.run, name="s4-abi-sync-now", daemon=True).start()
    for _ in range(40):   # chờ luồng nhận việc (tối đa 2 giây) để trạng thái trả về đã là "đang đồng bộ" -> giao diện theo dõi tiếp
        if sync.state()["running"]:
            break
        time.sleep(0.05)
    return True, ""


def summary() -> dict:
    data = store.data() or {}
    dom = index.domain()
    ds = [d for d in db.run("SELECT * FROM datasets WHERE domain_id=?", (dom["id"],), many=True) if index.is_abi_dataset(d)] if dom else []
    return {"state": sync.state(), "runs": store.status().get("runs", [])[:10], "synced_at": data.get("synced_at"),
            "counts": {k: len(data.get(k) or []) for k in ("departments", "people", "events", "programs", "catalog", "posts", "pages")},
            "domain": {"id": dom["id"], "name": dom["name"]} if dom else None,
            "datasets": [{k: d[k] for k in ("id", "status", "progress", "n_records", "message", "active")} for d in ds],
            "remote": remote.status(), "settings": {k: settings.get(k) for k in ("ABI_SYNC_HOURS", "ABI_CODE_ANSWER", "ABI_REMOTE_RAG",
                                                                                  "ABI_BOT_CONTACT", "ABI_REMOTE_MAX_PER_5MIN")},
            "user_agent": client.user_agent()}


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
        started, reason = start_now()
        return {"started": started, "reason": reason, **summary()}

    return r

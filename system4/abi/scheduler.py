"""Tự đồng bộ ABI theo ⚙ ABI_SYNC_HOURS (0 = tắt) và API quản lý phiên bản (chỉ dev).

hook.install() gọi start() khi khởi động server (test tắt bằng S4_ABI_SYNC=0 / S4_WARMUP=0). Một luồng nền: lúc khởi động và mỗi
10 phút kiểm tra; bản thật (prod) quá hạn thì sync.run("prod"). Staging (môi trường thử nghiệm của đội làm web) CHỈ đồng bộ khi
bấm nút. Phiên bản đang dùng chưa có chỉ mục (lúc đó chưa có dev / Ollama tắt) thì dựng.
"""
from __future__ import annotations

import logging
import threading
import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..server import settings
from . import client, index, normalize, store, sync, versions

log = logging.getLogger("system4.abi.scheduler")
CHECK_EVERY = 600
_thread: threading.Thread | None = None

# Thoả thuận với chủ web (16/10/2026): quét định kỳ 6 tiếng, tối đa 2 request/giây (client.MAX_RPS)
MIN_HOURS = 6              # ⚙ ABI_SYNC_HOURS đặt 1–5 vẫn tính là 6
RETRY_AFTER_ERROR = 3600   # giây: lần trước lỗi (mất mạng…) thì thử lại sau 1 giờ, không chờ đủ 6 giờ
MANUAL_GAP = 600           # giây: nút đồng bộ một nguồn không chạy lại trong 10 phút sau lần đồng bộ trước của nguồn đó
AUTO_SOURCE = "prod"


def _last_run(source: str) -> dict | None:
    return next((r for r in store.status().get("runs", [])
                 if (r.get("source") or "prod") == source and (r.get("ok") or r.get("error"))), None)


def _age(run: dict | None) -> float | None:
    started = normalize.dt((run or {}).get("started"))
    return time.time() - started.timestamp() if started else None


def due(source: str = AUTO_SOURCE) -> bool:
    hours = settings.get("ABI_SYNC_HOURS")
    if hours <= 0:
        return False
    last = _last_run(source)
    if not last:
        return True
    hours = max(hours, MIN_HOURS)
    wait = hours * 3600 if last.get("ok") else min(hours * 3600, RETRY_AFTER_ERROR)
    age = _age(last)
    return age is None or age >= wait


def index_missing() -> bool:
    """Phiên bản đang dùng chưa có chỉ mục tìm kiếm sẵn sàng (và đã có dev để đứng tên bộ dữ liệu)."""
    from ..server import db
    vid = store.active_id()
    if not vid or not index.domain() or not db.run("SELECT 1 FROM users WHERE role='dev' LIMIT 1", one=True):
        return False
    ds = index.dataset_of(vid)
    return not ds or ds["status"] != "ready"


def build_active_index() -> dict:
    vid = store.active_id()
    v = store.get_version(vid)
    out = index.build(vid, store.version_data(vid), versions.label(v["source"]))
    index.set_active(vid)
    return out


def _loop() -> None:
    time.sleep(20)   # để server khởi động xong, model nạp xong
    try:
        versions.ensure()
    except Exception as e:
        log.warning("chuẩn bị phiên bản ABI: %s", e)
    while True:
        try:
            if due(AUTO_SOURCE):
                log.info("đồng bộ ABI theo lịch")
                sync.run(AUTO_SOURCE)
            elif index_missing() and not sync.state()["running"]:
                log.info("dựng chỉ mục ABI còn thiếu")
                build_active_index()
        except Exception as e:   # thiếu Ollama…: thử lại ở vòng sau
            log.warning("lịch đồng bộ ABI: %s", e)
        time.sleep(CHECK_EVERY)


def start() -> None:
    global _thread
    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=_loop, name="s4-abi-sync", daemon=True)
        _thread.start()


def start_now(source: str) -> tuple[bool, str]:
    """Nút "Đồng bộ". Trả (đã bắt đầu?, lý do nếu không)."""
    if source not in client.SOURCES:
        return False, f"nguồn lạ: {source}"
    if sync.state()["running"]:
        return False, "Đang đồng bộ, đợi lần này xong."
    if not client.api_key():
        return False, "Chưa có khoá API của abi.com.vn: điền ở ⚙ Cài đặt → Lĩnh vực ABI → Khoá API."
    age = _age(_last_run(source))
    if age is not None and age < MANUAL_GAP:   # giữ đúng thoả thuận tần suất với chủ web
        return False, f"Vừa đồng bộ {versions.label(source)} {int(age // 60)} phút trước; đợi thêm {int((MANUAL_GAP - age) // 60) + 1} phút rồi bấm lại."
    threading.Thread(target=sync.run, args=(source,), name="s4-abi-sync-now", daemon=True).start()
    for _ in range(40):   # chờ luồng nhận việc (tối đa 2 giây) để trạng thái trả về đã là "đang đồng bộ" -> giao diện theo dõi tiếp
        if sync.state()["running"]:
            break
        time.sleep(0.05)
    return True, ""


def summary() -> dict:
    versions.ensure()
    data = store.data() or {}
    act = store.get_version(store.active_id())
    return {"state": sync.state(), "runs": store.status().get("runs", [])[:10], "versions": versions.listing(),
            "active": {"id": act["id"], "source": act["source"], "label": versions.label(act["source"]), "synced_at": data.get("synced_at")} if act else None,
            "synced_at": data.get("synced_at"), "counts": store.counts(data),
            "sources": [{"id": k, "label": v["label"], "site": v["site"], "auto": k == AUTO_SOURCE} for k, v in client.SOURCES.items()],
            "keep": store.KEEP, "domain": ({"id": index.domain()["id"], "name": index.domain()["name"]} if index.domain() else None),
            "api_key": client.key_hint(), "user_agent": client.user_agent(),
            "settings": {k: settings.get(k) for k in ("ABI_SYNC_HOURS", "ABI_CODE_ANSWER", "ABI_BOT_CONTACT")}}


class SyncIn(BaseModel):
    source: str = AUTO_SOURCE


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
    def sync_now(request: Request, body: SyncIn | None = None):
        dev(request)
        started, reason = start_now((body or SyncIn()).source)
        return {"started": started, "reason": reason, **summary()}

    @r.post("/versions/{vid}/activate")
    def activate(vid: int, request: Request):
        """Chuyển lĩnh vực ABI sang phiên bản này (tức thì)."""
        dev(request)
        try:
            versions.activate(vid)
        except ValueError as e:
            raise HTTPException(404, str(e)) from None
        return summary()

    @r.delete("/versions/{vid}")
    def delete(vid: int, request: Request):
        dev(request)
        try:
            versions.delete(vid)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        return summary()

    return r

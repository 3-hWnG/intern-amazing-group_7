"""Đồng bộ FLM (flm.fpt.edu.vn) -> phiên bản dữ liệu của lĩnh vực FLM, và API cho nút "Đồng bộ FLM" (dev / cán bộ).

Các bước của một lần đồng bộ (luồng nền, một lần một lúc):
  ① mở Chrome riêng (browser.py) ở trang khách của FLM; còn phiên khách thì đi thẳng, hết phiên thì CHỜ người bấm captcha (≤ 10 phút)
  ② scrape.collect: khung chương trình mới nhất của mỗi ngành trong ⚙ FLM_PROGRAMS + đề cương từng môn (1 request/giây)
  ③ không đổi so với phiên bản mới nhất (băm dữ liệu) -> chỉ ghi "kiểm lúc"; đổi -> build.write_xlsx thành tệp Excel
  ④ nạp tệp như một bộ dữ liệu của dev trong lĩnh vực FLM (ingest + đường nhanh, như tệp tải lên), chờ nạp xong
  ⑤ phiên bản mới thành "đang dùng" nếu đang theo bản mới nhất; giữ store.KEEP bản, xoá bản cũ hơn cùng bộ dữ liệu của nó.
Không có lịch tự đồng bộ: captcha cần người bấm (leader 19/10/2026: chế độ khách, không dùng tài khoản đăng nhập).
"""
from __future__ import annotations

import json
import logging
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from ..server import datasets, db, settings
from . import build, scrape, store
from .browser import Browser, BrowserError

log = logging.getLogger("system4.flm")
VN = timezone(timedelta(hours=7))
CAPTCHA_WAIT = 600   # giây
INGEST_WAIT = 1800
SITE = "flm.fpt.edu.vn"

_state = {"running": False, "step": "", "started": None, "captcha": False}
_run_lock = threading.Lock()
BROWSER = Browser   # test thay bằng trình duyệt giả


def state() -> dict:
    return dict(_state)


def _step(msg: str, captcha: bool = False) -> None:
    _state["step"], _state["captcha"] = msg, captcha
    log.info(msg)


def domain() -> dict | None:
    return db.run("SELECT * FROM domains WHERE engine='flm' ORDER BY id LIMIT 1", one=True)


def programs() -> list[str]:
    return [p.strip() for p in str(settings.get("FLM_PROGRAMS") or "").split(",") if p.strip()]


def now() -> datetime:
    return datetime.now(VN)


# ------------------------------------------------------------------ phiên bản
def set_active(vid: int | None) -> None:
    """Chỉ bộ dữ liệu của phiên bản vid được bật (bộ tải thêm của lĩnh vực không đổi)."""
    d = store.load()
    d["active"] = vid
    store.save(d)
    for v in store.versions():
        ds = db.get_dataset(v["dataset_id"])
        if ds:
            on = 1 if v["id"] == vid and ds["status"] == "ready" else 0
            if ds["active"] != on:
                db.update_dataset(ds["id"], active=on)


def activate(vid: int) -> None:
    if not store.get(vid):
        raise ValueError(f"không có phiên bản {vid}")
    set_active(vid)


def delete_version(vid: int, force: bool = False) -> None:
    if vid == store.active_id() and not force:
        raise ValueError("Không xoá được phiên bản đang dùng; chuyển sang phiên bản khác trước")
    v = store.get(vid)
    if not v:
        raise ValueError(f"không có phiên bản {vid}")
    ds = db.get_dataset(v["dataset_id"]) if v.get("dataset_id") else None
    if ds:
        datasets.delete(ds)
    d = store.load()
    d["versions"] = [x for x in d.get("versions", []) if x["id"] != vid]
    if d.get("active") == vid:
        d["active"] = None
    store.save(d)


def prune() -> list[int]:
    gone = [v["id"] for v in store.versions()[store.KEEP:]]
    for vid in gone:
        delete_version(vid, force=True)
    if store.active_id() is None and store.versions():
        set_active(store.versions()[0]["id"])
    return gone


def label(v: dict) -> str:
    t = datetime.fromisoformat(v["synced_at"]).strftime("%H:%M %d/%m/%Y")
    return f"{SITE} · phiên bản {v['id']} · {t}"


# ------------------------------------------------------------------ đồng bộ
def _wait_captcha(b) -> None:
    """Chờ tới khi tab của Chrome không còn ở trang captcha (người dùng đã tích captcha + Continue)."""
    t0 = time.time()
    shown = False
    while time.time() - t0 < CAPTCHA_WAIT:
        try:
            loc = b.location()
            text = b.eval("document.documentElement ? document.documentElement.outerHTML.slice(0, 20000) : ''") or ""
        except BrowserError as e:
            if "đóng" in str(e) or "closed" in str(e).lower():
                raise scrape.FlmError("Cửa sổ Chrome của FLM đã bị đóng trước khi qua captcha") from None
            loc, text = "", ""
        if loc.startswith(scrape.BASE) and not scrape.captcha_page(text, loc):
            if b.eval("document.readyState") == "complete":   # đã qua captcha (hoặc phiên khách còn hạn)
                return
        elif scrape.captcha_page(text, loc) and not shown:
            _step("Đang chờ giải captcha: chuyển sang cửa sổ Chrome vừa mở, tích \"I'm not a robot\" rồi bấm Continue (tối đa 10 phút)…", True)
            shown = True
        time.sleep(1)
    raise scrape.FlmError("Quá 10 phút chưa qua captcha của FLM; bấm Đồng bộ lại khi sẵn sàng")


def _wait_ingest(ds_id: int) -> dict:
    t0 = time.time()
    while time.time() - t0 < INGEST_WAIT:
        ds = db.get_dataset(ds_id)
        if not ds or ds["status"] in ("ready", "error"):
            return ds or {}
        _step(f"Đang nạp dữ liệu FLM vào lĩnh vực: {ds.get('message') or ''} ({ds.get('progress') or 0}%)")
        time.sleep(1)
    raise scrape.FlmError("Nạp tệp FLM quá lâu (30 phút)")


def install(raw: dict, dom: dict, dev_id: int, synced_at: str | None = None) -> dict:
    """Dữ liệu thô (scrape.collect / bản chụp) -> phiên bản: không đổi thì ghi "kiểm lúc"; đổi thì dựng Excel, nạp như tệp của dev,
    chờ nạp xong, theo bản mới nhất nếu đang theo, giữ store.KEEP bản. Trả phần kết quả của lần chạy."""
    h = build.digest(raw)
    newest = (store.versions() or [None])[0]
    if newest and newest.get("hash") == h and db.get_dataset(newest["dataset_id"]):
        d = store.load()
        for v in d.get("versions", []):
            if v["id"] == newest["id"]:
                v["checked_at"] = now().isoformat(timespec="seconds")
        store.save(d)
        return {"ok": True, "result": "unchanged", "version": newest["id"]}
    follow = store.active_id() is None or (newest is not None and store.active_id() == newest["id"])
    vid = max([v["id"] for v in store.versions()] + [0]) + 1
    folder = store.root() / "versions" / str(vid)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "raw.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    xlsx = folder / f"flm_v{vid}.xlsx"
    _step("Dựng tệp Excel từ dữ liệu FLM…")
    counts = build.write_xlsx(raw, xlsx)
    user = db.run("SELECT * FROM users WHERE id=?", (dev_id,), one=True)
    with open(xlsx, "rb") as f:
        ds = datasets.save_upload(user, xlsx.name, f, None, dom["id"])
    v = {"id": vid, "dataset_id": ds["id"], "synced_at": synced_at or now().isoformat(timespec="seconds"), "hash": h, "counts": counts,
         "requests": raw.get("requests", 0), "curricula": [{"code": c["code"], "curid": c["curid"], "subjects": len(c["subjects"])}
                                                          for c in raw["curricula"]]}
    d = store.load()
    d.setdefault("versions", []).append(v)
    store.save(d)
    db.update_dataset(ds["id"], name=label(v))
    ready = _wait_ingest(ds["id"])
    if ready.get("status") != "ready":
        delete_version(vid, force=True)
        raise scrape.FlmError(f"Nạp tệp FLM lỗi: {ready.get('message')}")
    set_active(vid if follow else store.active_id())   # dev đang chọn bản cũ: giữ lựa chọn, bản mới để tắt
    return {"ok": True, "result": "new", "version": vid, "counts": counts, "pruned": prune()}


SNAPSHOT = Path(__file__).resolve().parent / "snapshot" / "flm_2026-10-19.json"


def import_snapshot() -> dict | None:
    """Máy mới (chưa có phiên bản FLM nào): nạp bản chụp trong git làm phiên bản 1 — dùng được ngay, không cần captcha.
    Đã có phiên bản / không có lĩnh vực / chưa có dev / đang đồng bộ: không làm gì (trả None)."""
    dom, dev_id = domain(), db.first_dev_id()
    if store.versions() or not dom or not dev_id or not SNAPSHOT.exists() or not _run_lock.acquire(blocking=False):
        return None
    try:
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        rec = {"started": now().isoformat(timespec="seconds"), "programs": snap["raw"].get("programs", []), "snapshot": SNAPSHOT.name,
               **install(snap["raw"], dom, dev_id, snap.get("synced_at"))}
        rec["finished"] = now().isoformat(timespec="seconds")
        store.add_run(rec)
        return rec
    finally:
        _state.update(running=False, step="", captcha=False)
        _run_lock.release()


def run() -> dict:
    """Một lần đồng bộ (chặn tới khi xong). Trả bản ghi của lần chạy (cũng lưu trong store.runs())."""
    if not _run_lock.acquire(blocking=False):
        return {"ok": False, "error": "Đang đồng bộ"}
    started = now()
    _state.update(running=True, started=started.isoformat(timespec="seconds"), captcha=False, step="Mở Chrome…")
    rec: dict = {"started": _state["started"], "programs": programs()}
    b = None
    try:
        dom = domain()
        dev_id = db.first_dev_id()
        if not dom or not dev_id:
            raise scrape.FlmError("Chưa có lĩnh vực FLM hoặc chưa có tài khoản dev")
        if not rec["programs"]:
            raise scrape.FlmError("⚙ FLM_PROGRAMS trống: điền tiền tố ngành, vd. BIT_SE, BIT_AI")
        b = BROWSER(store.root() / "chrome_profile")
        b.start(scrape.BASE + scrape.LIST + rec["programs"][0])
        _step("Kiểm phiên khách của FLM…")
        _wait_captcha(b)
        raw = scrape.collect(lambda p: b.fetch(scrape.BASE + p), rec["programs"], _step)
        b.close()
        b = None
        rec["requests"] = raw["requests"]
        rec.update(install(raw, dom, dev_id))
        return rec
    except Exception as e:   # mất mạng, captcha, FLM đổi giao diện…
        log.warning("đồng bộ FLM lỗi: %s", e)
        rec.update(ok=False, error=str(e), trace=traceback.format_exc()[-1500:])
        return rec
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        rec["finished"] = now().isoformat(timespec="seconds")
        store.add_run({k: v for k, v in rec.items() if k != "trace"})
        _state.update(running=False, step="", captcha=False)
        _run_lock.release()


def start_now() -> tuple[bool, str]:
    if _state["running"]:
        return False, "Đang đồng bộ, đợi lần này xong."
    if not domain():
        return False, "Chưa có lĩnh vực FLM"
    threading.Thread(target=run, name="s4-flm-sync", daemon=True).start()
    for _ in range(40):
        if _state["running"]:
            break
        time.sleep(0.05)
    return True, ""


def summary() -> dict:
    act = store.active_id()
    out = []
    for v in store.versions():
        ds = db.get_dataset(v["dataset_id"])
        out.append({**{k: v.get(k) for k in ("id", "synced_at", "checked_at", "counts", "requests", "curricula")}, "label": label(v),
                    "active": v["id"] == act, "dataset": {k: ds[k] for k in ("id", "status", "progress", "n_records", "message")} if ds else None})
    dom = domain()
    return {"state": state(), "runs": store.runs()[:10], "versions": out, "active": act, "keep": store.KEEP, "programs": programs(),
            "site": scrape.BASE, "domain": {"id": dom["id"], "name": dom["name"]} if dom else None}


def make_router() -> APIRouter:
    r = APIRouter(prefix="/s4/flm")

    def staff(request: Request) -> None:
        u = getattr(request.state, "user", None)
        if not u or u["role"] not in ("dev", "can_bo"):
            raise HTTPException(403, "Chỉ dev và cán bộ")

    @r.get("/status")
    def status(request: Request):
        staff(request)
        return summary()

    @r.post("/sync")
    def sync_now(request: Request):
        staff(request)
        started, reason = start_now()
        return {"started": started, "reason": reason, **summary()}

    @r.post("/versions/{vid}/activate")
    def activate_api(vid: int, request: Request):
        staff(request)
        try:
            activate(vid)
        except ValueError as e:
            raise HTTPException(404, str(e)) from None
        return summary()

    @r.delete("/versions/{vid}")
    def delete_api(vid: int, request: Request):
        staff(request)
        try:
            delete_version(vid)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        return summary()

    return r


if __name__ == "__main__":   # python -m system3.system4.flm.sync [--snapshot]   (TẮT server trước: Qdrant cục bộ khoá thư mục)
    import socket
    import sys
    try:
        socket.create_connection(("127.0.0.1", 8300), timeout=1).close()
        sys.exit("Server đang chạy: dùng nút Đồng bộ FLM trong web (Quản lý lĩnh vực -> FLM), hoặc tắt server rồi chạy lại lệnh này.")
    except OSError:
        pass
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    db.init_db()
    if not db.first_dev_id():
        sys.exit("Chưa có tài khoản dev: mở web, đăng ký tài khoản đầu tiên (thành dev) rồi chạy lại.")
    out = import_snapshot() if "--snapshot" in sys.argv else run()
    print(json.dumps(out, ensure_ascii=False, indent=1) if out else "Đã có phiên bản FLM: bản chụp không nạp lại (dùng lệnh không có --snapshot để đồng bộ thật).")

"""Đồng bộ FLM (flm.fpt.edu.vn) -> phiên bản dữ liệu của lĩnh vực FLM, và API cho nút "Đồng bộ FLM" (dev / cán bộ).

Các bước của một lần đồng bộ (luồng nền, một lần một lúc):
  ① mở Chrome riêng (browser.py) ở trang khách của FLM; còn phiên khách thì đi thẳng, hết phiên thì CHỜ người bấm captcha (≤ 10 phút)
  ② scrape.collect: khung chương trình mới nhất của mỗi ngành trong ⚙ FLM_PROGRAMS + đề cương từng môn (1 request/giây)
  ③ không đổi so với phiên bản mới nhất (băm dữ liệu) -> chỉ ghi "kiểm lúc"; đổi -> build.write_xlsx thành tệp Excel
  ④ nạp tệp như một bộ dữ liệu của dev trong lĩnh vực FLM (ingest + đường nhanh, như tệp tải lên), chờ nạp xong
  ⑤ phiên bản mới thành "đang dùng" nếu đang theo bản mới nhất; giữ store.KEEP bản, xoá bản cũ hơn cùng bộ dữ liệu của nó.
Không có lịch tự đồng bộ: captcha / đăng nhập cần người bấm.

Hai chế độ (leader 19/10/2026):
  - "guest" (mặc định): trang khách, các ngành trong ⚙ FLM_PROGRAMS, không tài liệu / lịch buổi học.
  - "full" (đăng nhập): server mở Chrome riêng ở trang ĐĂNG NHẬP của FLM, người dùng tự đăng nhập TRONG cửa sổ đó (Google @fpt.edu.vn hoặc
    /SignIn) — mật khẩu chỉ đi tới FLM / Google, hệ thống không thấy, không lưu. Phiên (cookie) giữ trong hồ sơ Chrome tạm tới khi TẮT
    server, rồi xoá. Lấy khung mới nhất của MỌI ngành + combo / tự chọn + đề cương đầy đủ (tài liệu, lịch từng buổi, câu hỏi; tệp đính
    kèm chỉ lấy LINK). ~30–40 phút ở 1 request/giây; đề cương đã đọc giữ 7 ngày ở runtime/flm/cache/full (bị ngắt thì chạy lại đi tiếp).
"""
from __future__ import annotations

import atexit
import json
import logging
import shutil
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
LOGIN_WAIT = 900
INGEST_WAIT = 3600
LOGIN_PORT = 9334   # Chrome đăng nhập: khác cổng Chrome khách (9333)
SITE = "flm.fpt.edu.vn"

_state = {"running": False, "step": "", "started": None, "captcha": False, "mode": None}
_login = {"browser": None}   # Chrome đăng nhập còn mở (giữ phiên tới khi tắt server)
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
        for i in store.ids_of(v):
            ds = db.get_dataset(i)
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
    for i in store.ids_of(v):
        ds = db.get_dataset(i)
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
    return f"{SITE} · phiên bản {v['id']}{' (đầy đủ, đăng nhập)' if v.get('mode') == 'full' else ''} · {t}"


# ------------------------------------------------------------------ Chrome đăng nhập: giữ phiên tới khi tắt server
def login_profile() -> Path:
    return store.root() / "login_profile"


def close_login() -> None:
    """Đóng Chrome đăng nhập và XOÁ hồ sơ của nó (cookie, phiên). Gọi khi tắt server (atexit) và lúc khởi động (lần trước tắt đột ngột)."""
    b = _login.pop("browser", None)
    _login["browser"] = None
    try:
        if b is None:
            b = BROWSER(login_profile(), port=LOGIN_PORT)
            b._targets()   # còn Chrome đăng nhập của lần chạy trước?
            from .browser import _WS
            b.ws = _WS(next(t for t in b._targets() if t.get("type") == "page")["webSocketDebuggerUrl"])
        b.call("Browser.close")
    except Exception:
        pass
    try:
        b.close()
    except Exception:
        pass
    for _ in range(10):   # Chrome nhả khoá tệp chậm vài giây
        if not login_profile().exists():
            break
        shutil.rmtree(login_profile(), ignore_errors=True)
        time.sleep(0.5)



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


def _logged_in(b) -> bool:
    loc = b.location()
    if not loc.startswith(scrape.BASE) or any(x in loc for x in ("/Login", "/SignIn", "guest-captcha")):
        return False
    html = b.eval("document.documentElement ? document.documentElement.outerHTML : ''") or ""
    return "lbtnSignOut" in html and b.eval("document.readyState") == "complete"


def _wait_login(b) -> None:
    """Chờ người dùng tự đăng nhập trong cửa sổ Chrome (đã đăng nhập từ lần trước thì đi thẳng)."""
    t0, shown = time.time(), False
    while time.time() - t0 < LOGIN_WAIT:
        try:
            if _logged_in(b):
                return
        except BrowserError as e:
            if "đóng" in str(e) or "closed" in str(e).lower():
                raise scrape.FlmError("Cửa sổ Chrome đăng nhập FLM đã bị đóng trước khi đăng nhập xong") from None
        if not shown:
            _step("Đang chờ đăng nhập FLM: chuyển sang cửa sổ Chrome vừa mở, chọn FPTU rồi đăng nhập (Google @fpt.edu.vn hoặc Sign In). "
                  "Mật khẩu chỉ nhập vào trang của FLM / Google, hệ thống không thấy và không lưu (tối đa 15 phút)…", True)
            shown = True
        time.sleep(1.5)
    raise scrape.FlmError("Quá 15 phút chưa đăng nhập FLM; bấm Đồng bộ đầy đủ lại khi sẵn sàng")


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
    files = [xlsx]
    if raw.get("mode") == "full":   # lịch từng buổi + câu hỏi: tệp văn bản riêng (chia theo môn)
        md = folder / f"flm_v{vid}_lich_hoc.md"
        md.write_text(build.schedule_md(raw), encoding="utf-8")
        counts["Lịch học (môn)"] = sum(1 for s in raw["syllabi"].values() if s.get("schedule"))
        files.append(md)
    user = db.run("SELECT * FROM users WHERE id=?", (dev_id,), one=True)
    ids = []
    for fp in files:
        with open(fp, "rb") as f:
            ids.append(datasets.save_upload(user, fp.name, f, None, dom["id"])["id"])
    v = {"id": vid, "dataset_id": ids[0], "extra_ids": ids[1:], "mode": raw.get("mode", "guest"),
         "synced_at": synced_at or now().isoformat(timespec="seconds"), "hash": h, "counts": counts,
         "requests": raw.get("requests", 0), "curricula": [{"code": c["code"], "curid": c["curid"], "subjects": len(c["subjects"])}
                                                          for c in raw["curricula"]]}
    d = store.load()
    d.setdefault("versions", []).append(v)
    store.save(d)
    db.update_dataset(ids[0], name=label(v))
    if len(ids) > 1:
        db.update_dataset(ids[1], name=label(v) + " · lịch học, câu hỏi")
    for i in ids:
        ready = _wait_ingest(i)
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


def run(mode: str = "guest") -> dict:
    """Một lần đồng bộ (chặn tới khi xong). mode "guest" | "full" (đăng nhập). Trả bản ghi của lần chạy (cũng lưu trong store.runs())."""
    if not _run_lock.acquire(blocking=False):
        return {"ok": False, "error": "Đang đồng bộ"}
    if mode == "full":
        return _run_full()
    started = now()
    _state.update(running=True, started=started.isoformat(timespec="seconds"), captcha=False, step="Mở Chrome…", mode="guest")
    rec: dict = {"started": _state["started"], "mode": "guest", "programs": programs()}
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


def _run_full() -> dict:
    """Chế độ đăng nhập (đã giữ _run_lock). Chrome đăng nhập KHÔNG đóng sau khi xong: phiên giữ tới khi tắt server (close_login)."""
    _state.update(running=True, started=now().isoformat(timespec="seconds"), captcha=False, step="Mở Chrome đăng nhập…", mode="full")
    rec: dict = {"started": _state["started"], "mode": "full", "programs": ["mọi ngành"]}
    try:
        dom, dev_id = domain(), db.first_dev_id()
        if not dom or not dev_id:
            raise scrape.FlmError("Chưa có lĩnh vực FLM hoặc chưa có tài khoản dev")
        b = _login.get("browser")
        if b is None:
            b = BROWSER(login_profile(), port=LOGIN_PORT)
            _login["browser"] = b
            if not _login.get("atexit"):   # chỉ tiến trình đã mở Chrome đăng nhập mới đóng nó khi thoát (test / lệnh khác không đụng tới)
                atexit.register(close_login)
                _login["atexit"] = True
        try:
            b.start(scrape.BASE + "/Login")
        except BrowserError:   # cửa sổ cũ đã bị đóng: mở lại
            b = _login["browser"] = BROWSER(login_profile(), port=LOGIN_PORT)
            b.start(scrape.BASE + "/Login")
        _step("Kiểm phiên đăng nhập FLM…")
        _wait_login(b)
        _step("Đã đăng nhập: bắt đầu tải mọi ngành…")
        raw = scrape.collect_full(lambda p: b.fetch(scrape.BASE + p), _step, cache=scrape.SylCache(store.root() / "cache" / "full"))
        rec.update(requests=raw["requests"], cached=raw.get("cached"), programs=raw["programs"], seconds=raw.get("seconds"),
                   skipped=raw.get("skipped") or [])   # trang tài khoản không có quyền xem: bỏ qua, ghi lại
        rec.update(install(raw, dom, dev_id))
        return rec
    except Exception as e:
        log.warning("đồng bộ FLM (đăng nhập) lỗi: %s", e)
        rec.update(ok=False, error=str(e), trace=traceback.format_exc()[-1500:])
        return rec
    finally:
        rec["finished"] = now().isoformat(timespec="seconds")
        store.add_run({k: v for k, v in rec.items() if k != "trace"})
        _state.update(running=False, step="", captcha=False, mode=None)
        _run_lock.release()


def start_now(mode: str = "guest") -> tuple[bool, str]:
    if _state["running"]:
        return False, "Đang đồng bộ, đợi lần này xong."
    if not domain():
        return False, "Chưa có lĩnh vực FLM"
    if mode not in ("guest", "full"):
        return False, f"chế độ lạ: {mode}"
    threading.Thread(target=run, args=(mode,), name="s4-flm-sync", daemon=True).start()
    for _ in range(40):
        if _state["running"]:
            break
        time.sleep(0.05)
    return True, ""


def summary() -> dict:
    act = store.active_id()
    out = []
    for v in store.versions():
        dss = [d for d in (db.get_dataset(i) for i in store.ids_of(v)) if d]
        ds = dss[0] if dss else None
        if ds and len(dss) > 1:   # phiên bản đầy đủ: 2 bộ dữ liệu -> cộng số bản ghi, trạng thái của bộ chưa xong
            busy = next((d for d in dss if d["status"] != "ready"), None)
            ds = {**(busy or ds), "n_records": sum(d["n_records"] for d in dss)}
        out.append({**{k: v.get(k) for k in ("id", "synced_at", "checked_at", "counts", "requests", "curricula", "mode")}, "label": label(v),
                    "active": v["id"] == act, "dataset": {k: ds[k] for k in ("id", "status", "progress", "n_records", "message")} if ds else None})
    dom = domain()
    return {"state": state(), "runs": store.runs()[:10], "versions": out, "active": act, "keep": store.KEEP, "programs": programs(),
            "login_open": _login.get("browser") is not None,
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
    def sync_now(request: Request, body: dict | None = None):
        staff(request)
        started, reason = start_now((body or {}).get("mode") or "guest")
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
    out = import_snapshot() if "--snapshot" in sys.argv else run("full" if "--full" in sys.argv else "guest")
    print(json.dumps(out, ensure_ascii=False, indent=1) if out else "Đã có phiên bản FLM: bản chụp không nạp lại (dùng lệnh không có --snapshot để đồng bộ thật).")

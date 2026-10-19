"""Khởi tạo dữ liệu MỘT LẦN cho máy mới (19/10/2026): setup xong, bật web, đăng ký tài khoản đầu tiên (dev) là có dữ liệu, không phải chạy gì thêm.

hook.install() gọi start() (test tắt bằng S4_WARMUP=0 / S4_BOOTSTRAP=0). Luồng nền chờ tới khi có tài khoản dev, rồi:
  1. "real_domains": tạo lĩnh vực mềm Y tế / Giáo dục (Du lịch nếu chưa có) và nạp 6 bộ dữ liệu thật trong git
     (system4/eval/real_domains/data, dùng chung) — như `seed.py` nhưng chạy trong server (không phải tắt server);
  2. "flm_snapshot": lĩnh vực FLM chưa có phiên bản nào -> nạp bản chụp system4/flm/snapshot/ làm phiên bản 1 (không cần captcha).
Mỗi bước xong ghi vào runtime/bootstrap.json và KHÔNG chạy lại (dev xoá bộ dữ liệu thì nó không tự quay về).
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import threading
import time
from datetime import datetime

from . import config, db

log = logging.getLogger("system4.bootstrap")
SEED = config.S4_DIR / "eval" / "real_domains" / "seed.py"
_thread: threading.Thread | None = None


def _path():
    return config.RUNTIME_DIR / "bootstrap.json"


def done() -> dict:
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _mark(step: str, info) -> None:
    d = done()
    d[step] = {"at": datetime.now().isoformat(timespec="seconds"), "info": info}
    config.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _seed_module():
    spec = importlib.util.spec_from_file_location("s4_real_domains_seed", SEED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_once() -> dict:
    """Làm các bước chưa làm (cần có dev). Trả {bước: kết quả} của lần này."""
    out = {}
    if not db.first_dev_id():
        return out
    if "real_domains" not in done() and SEED.exists():
        ids = _seed_module().ensure(say=log.info)
        _mark("real_domains", ids)
        out["real_domains"] = ids
    if "flm_snapshot" not in done():
        from ..flm import store as flm_store, sync as flm_sync
        if flm_store.versions():   # máy đã đồng bộ FLM thật: không cần bản chụp
            _mark("flm_snapshot", "đã có phiên bản FLM")
        else:
            rec = flm_sync.import_snapshot()
            if rec is not None:
                _mark("flm_snapshot", {k: rec.get(k) for k in ("ok", "result", "version", "counts")})
                out["flm_snapshot"] = rec
    return out


def _loop() -> None:
    time.sleep(15)   # để server khởi động xong (nạp model, xử lý lại tệp cũ)
    while True:
        try:
            if db.first_dev_id():
                r = run_once()
                if r:
                    log.info("khởi tạo dữ liệu: %s", {k: (v if k != "flm_snapshot" else v.get("result")) for k, v in r.items()})
                if {"real_domains", "flm_snapshot"} <= set(done()):
                    return
        except Exception as e:   # thiếu Ollama, tệp hỏng…: thử lại ở vòng sau
            log.warning("khởi tạo dữ liệu: %s", e)
        time.sleep(30)


def start() -> None:
    global _thread
    if os.environ.get("S4_BOOTSTRAP", os.environ.get("S4_WARMUP", "1")) != "1":
        return
    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=_loop, name="s4-bootstrap", daemon=True)
        _thread.start()

"""Chạy trình cào cho tab "Dữ liệu Strict" (tiến trình riêng, do server System 4 khởi động).

    python -m system3.system4.scraper.run --status <tệp.json> [--limit N] [--rps 2]

Các bước của V10.3: ① danh mục cấp Xã/Phường -> ② chi tiết từng thủ tục (KHÔNG tải tệp đính kèm, đỡ tốn mạng)
-> ③ chuẩn hoá ra staging/procedures.jsonl. Chạy lại = tiếp tục (bước ② bỏ qua thủ tục đã tải, như bản gốc).
Tệp trạng thái: {"step": catalog|details|normalize|done|error, "message": ..., "staging": đường dẫn khi xong}.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

from . import fetch_catalog, fetch_details, normalize, paths


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = toàn bộ")
    ap.add_argument("--rps", type=float, default=2.0)
    a = ap.parse_args(argv)
    status = Path(a.status)

    def put(step: str, message: str, **extra) -> None:
        tmp = status.with_suffix(".tmp")
        tmp.write_text(json.dumps({"step": step, "message": message, "time": time.time(), **extra}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(status)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    paths.ensure_dirs()
    try:
        put("catalog", "Đang lấy danh mục thủ tục cấp Xã/Phường…")
        args1 = ["--scope", "xa", "--rps", str(a.rps)] + (["--limit", str(a.limit)] if a.limit else [])
        if fetch_catalog.main(args1) != 0:
            put("error", "Bước ① (danh mục) thất bại — xem nhật ký. Có thể Cổng Dịch vụ công đã đổi API hoặc mất mạng.")
            return 1
        put("details", "Đang lấy chi tiết từng thủ tục…")
        if fetch_details.main(["--rps", str(a.rps), "--no-files"]) != 0:
            put("error", "Bước ② (chi tiết) thất bại — xem nhật ký. Chạy lại sẽ tiếp tục từ chỗ dừng.")
            return 1
        put("normalize", "Đang chuẩn hoá dữ liệu…")
        if normalize.main([]) != 0:
            put("error", "Bước ③ (chuẩn hoá) thất bại — xem nhật ký.")
            return 1
        put("done", "Đã cào xong.", staging=str(paths.STAGING_PATH))
        return 0
    except Exception as e:
        traceback.print_exc()
        put("error", f"Lỗi: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

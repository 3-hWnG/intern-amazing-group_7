"""Chạy cả 4 bước của Phase 1.

    python -m Database.pipeline.run_pipeline --all             (phạm vi mặc định: cấp Xã/Phường)
    python -m Database.pipeline.run_pipeline --department bca --all   (bỏ phạm vi xã, lọc theo bộ)
    python -m Database.pipeline.run_pipeline --skip-fetch      (chỉ chạy lại ③④)

Mặc định `--scope xa` = cấp Xã/Phường + thủ tục riêng TP.HCM (paths.SCOPE_XA).
Truyền `--department` khác "all" thì bỏ phạm vi xã, lọc theo bộ như trước.

`--skip-fetch` là đường dùng nhiều nhất khi đang phát triển: đổi logic map trong
normalize.py rồi chạy lại, mất vài giây, KHÔNG đụng tới mạng.
"""

from __future__ import annotations

import argparse
import logging
import time

from Database.pipeline import fetch_catalog, fetch_details, import_db, normalize, paths

log = logging.getLogger("pipeline")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pipeline ETL Phase 1")
    ap.add_argument("--scope", default="xa", choices=["xa", "all"],
                    help="xa (mặc định) = cấp Xã/Phường + TP.HCM · all = không giới hạn cấp")
    ap.add_argument("--department", default="all", help="all (mặc định) | bca | btp | G01")
    ap.add_argument("--limit", type=int, default=50, help="số thủ tục (mặc định 50)")
    ap.add_argument("--all", action="store_true", help="bỏ giới hạn, cào toàn bộ")
    ap.add_argument("--rps", type=float, default=2.0)
    ap.add_argument("--no-files", action="store_true")
    ap.add_argument("--skip-fetch", action="store_true", help="chỉ chạy ③ và ④")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    paths.ensure_dirs()
    t0 = time.monotonic()
    limit = None if args.all else args.limit

    if not args.skip_fetch:
        by_scope = args.scope == "xa" and args.department == "all"
        log.info("═══ BƯỚC ① danh mục (%s, limit=%s) ═══",
                 "phạm vi xa" if by_scope else f"bộ={args.department}", limit)
        argv1 = (["--scope", "xa"] if by_scope else ["--department", args.department]) \
            + ["--rps", str(args.rps)]
        if limit is not None:
            argv1 += ["--limit", str(limit)]
        if fetch_catalog.main(argv1) != 0:
            return 1

        log.info("═══ BƯỚC ② chi tiết + tệp đính kèm ═══")
        argv2 = ["--rps", str(args.rps)]
        if args.no_files:
            argv2.append("--no-files")
        if fetch_details.main(argv2) != 0:
            return 1

    log.info("═══ BƯỚC ③ chuẩn hoá ═══")
    if normalize.main([]) != 0:
        return 1

    log.info("═══ BƯỚC ④ nạp DB ═══")
    if import_db.main([]) != 0:
        return 1

    log.info("✅ XONG trong %.0fs", time.monotonic() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

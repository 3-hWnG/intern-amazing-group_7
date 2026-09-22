"""BƯỚC ② — lấy CHI TIẾT từng thủ tục + tải tệp đính kèm.

Hai tính chất bắt buộc:

1. GHI NGUYÊN VĂN. JSON thô của cổng được lưu y hệt, không biến đổi gì.
   Tuần sau đổi schema thì chỉ chạy lại bước ③, KHÔNG phải cào lại mạng.

2. CHECKPOINT / RESUME. Chết ở bản ghi 500 thì lần sau chạy tiếp từ 501.
   Checkpoint được ghi sau MỖI bản ghi (flush ngay), không gom lô — mất điện
   giữa chừng vẫn không mất tiến độ.

Chạy:
    python -m Database.pipeline.fetch_details
    python -m Database.pipeline.fetch_details --no-files   (bỏ qua tải tệp)
"""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import time
from pathlib import Path

from Database.pipeline import paths
from Database.pipeline.client import DvcClient

log = logging.getLogger("pipeline.details")


def _load_checkpoint() -> dict:
    if paths.CHECKPOINT_PATH.exists():
        try:
            return json.loads(paths.CHECKPOINT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("checkpoint hỏng, bắt đầu lại từ đầu")
    return {"done": [], "failed": {}}


def _save_checkpoint(ck: dict) -> None:
    tmp = paths.CHECKPOINT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(ck, ensure_ascii=False), encoding="utf-8")
    tmp.replace(paths.CHECKPOINT_PATH)   # ghi nguyên tử, không bao giờ để file dở


def _iter_attachments(detail: dict):
    """Duyệt mọi tệp đính kèm ở mọi chỗ chúng có thể nằm."""
    buckets = [pc for ec in detail.get("executionCases") or []
               for pc in ec.get("profileComponents") or []]
    buckets += detail.get("profileComponents") or []
    for pc in buckets:
        for att in pc.get("attachments") or []:
            if isinstance(att, dict) and att.get("id"):
                yield att


def download_files(client: DvcClient, detail: dict, code: str) -> int:
    """Tải tệp của một thủ tục về raw/files/<code>/. Trả về số tệp tải mới."""
    out_dir = paths.RAW_FILES_DIR / paths.safe_name(code)
    n_new = 0
    for att in _iter_attachments(detail):
        # DÙNG CHUNG với normalize.py — hai bên phải ra y hệt một tên, xem paths.py
        name = paths.stored_filename(att.get("fileName") or att["id"])
        dest = out_dir / name
        if dest.exists() and dest.stat().st_size > 0:
            continue                      # đã có thì thôi — resume rẻ
        try:
            content, ctype = client.download_attachment(att["id"])
        except Exception as exc:
            log.warning("  tệp lỗi %s (%s): %s", name, att["id"], exc)
            continue
        if not content:
            log.warning("  tệp rỗng %s", name)
            continue
        # Chỉ đoán đuôi khi tên gốc THẬT SỰ không có đuôi nào.
        if not dest.suffix:
            ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) or ""
            dest = dest.with_name(dest.name + ext)
        out_dir.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        n_new += 1
    return n_new


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bước ②: chi tiết + tệp đính kèm")
    ap.add_argument("--rps", type=float, default=2.0)
    ap.add_argument("--no-files", action="store_true", help="không tải tệp đính kèm")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--categories-file", default=None,
                    help="JSON {tên lĩnh vực: nhóm} — chỉ cào thủ tục thuộc các lĩnh vực này")
    ap.add_argument("--files-only", action="store_true",
                    help="chỉ tải lại tệp từ raw/details đã có, KHÔNG gọi lại API chi tiết")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    paths.ensure_dirs()

    if not paths.CATALOG_PATH.exists():
        log.error("chưa có %s — chạy fetch_catalog trước", paths.CATALOG_PATH)
        return 1

    if args.files_only:
        # Vá tệp thì duyệt THEO RAW ĐÃ CÓ TRÊN ĐĨA, không theo catalog — catalog
        # có thể đã bị ghi đè bởi lần cào sau, sẽ bỏ sót thủ tục cào từ trước.
        rows = [{"id": None, "code": p.stem} for p in
                sorted(paths.RAW_DETAILS_DIR.glob("*.json"))]
    else:
        rows = [json.loads(line) for line in
                paths.CATALOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.categories_file:
        cat_path = Path(args.categories_file)
        if not cat_path.is_absolute() and not cat_path.exists():
            cat_path = paths.RAW_DIR / args.categories_file
        wanted = set(json.loads(cat_path.read_text(encoding="utf-8")))
        before = len(rows)
        rows = [r for r in rows
                if any(c in wanted for c in (r.get("categories") or []))]
        log.info("lọc theo lĩnh vực: %d → %d thủ tục (%d lĩnh vực)",
                 before, len(rows), len(wanted))

    if args.limit:
        rows = rows[:args.limit]

    ck = _load_checkpoint()
    done = set(ck["done"])
    log.info("%d thủ tục trong danh mục, %d đã xong trước đó", len(rows), len(done))

    n_ok = n_skip = n_err = n_files = 0
    t0 = time.monotonic()

    with DvcClient(rps=args.rps) as client:
        for i, row in enumerate(rows, 1):
            fid, code = row.get("id"), row.get("code") or row.get("id")
            dest = paths.RAW_DETAILS_DIR / f"{paths.safe_name(code)}.json"

            if args.files_only:
                # Chỉ vá lại tệp: đọc JSON thô đã có, không tốn request chi tiết.
                if not dest.exists():
                    n_skip += 1
                    continue
                detail = json.loads(dest.read_text(encoding="utf-8"))
                n_files += download_files(client, detail, code)
                n_ok += 1
                if n_ok % 20 == 0:
                    log.info("[%d/%d] vá tệp: %d thủ tục, %d tệp mới", i, len(rows), n_ok, n_files)
                continue

            if fid in done:
                n_skip += 1
                continue
            try:
                detail = client.get_detail(fid)
            except Exception as exc:
                n_err += 1
                ck["failed"][fid] = str(exc)[:300]
                log.error("[%d/%d] LỖI %s: %s", i, len(rows), code, exc)
                _save_checkpoint(ck)
                continue

            dest.write_text(json.dumps(detail, ensure_ascii=False, indent=1),
                            encoding="utf-8")

            if not args.no_files:
                n_files += download_files(client, detail, code)

            done.add(fid)
            ck["done"] = sorted(done)
            ck["failed"].pop(fid, None)
            _save_checkpoint(ck)          # ghi sau MỖI bản ghi
            n_ok += 1
            if n_ok % 10 == 0 or i == len(rows):
                log.info("[%d/%d] xong=%d bỏ qua=%d lỗi=%d tệp=%d (%.0fs)",
                         i, len(rows), n_ok, n_skip, n_err, n_files,
                         time.monotonic() - t0)

    log.info("HOÀN TẤT: mới=%d bỏ qua=%d lỗi=%d tệp tải mới=%d trong %.0fs",
             n_ok, n_skip, n_err, n_files, time.monotonic() - t0)
    if ck["failed"]:
        log.warning("còn %d bản ghi lỗi — chạy lại lệnh này để thử tiếp",
                    len(ck["failed"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

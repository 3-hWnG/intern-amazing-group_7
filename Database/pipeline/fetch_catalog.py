"""BƯỚC ① — lấy DANH MỤC thủ tục (nhẹ: id, mã, tên, lĩnh vực, bộ ban hành).

Phân trang bằng CON TRỎ `lastId`, không phải số trang.

⚠️ BỘ LỌC BỘ NGÀNH — đây là guardrail quan trọng:
Cổng DVC Quốc gia chứa TẤT CẢ 6.308 thủ tục của mọi bộ và mọi tỉnh (nông nghiệp,
giáo dục, hàng hải...). Không lọc thì tải về một đống không liên quan.
    --department bca   → G01, Bộ Công an   (329 thủ tục, đã kiểm chứng)
    --department btp   → G15, Bộ Tư pháp   (hộ tịch: kết hôn, khai sinh…)
    --department all   → không lọc (6.308)

Chạy:
    python -m Database.pipeline.fetch_catalog --department bca --limit 50
"""

from __future__ import annotations

import argparse
import json
import logging

from Database.pipeline import paths
from Database.pipeline.client import DvcClient

log = logging.getLogger("pipeline.catalog")

PAGE_SIZE = 20


def fetch_catalog(
    client: DvcClient,
    department_code: str = "",
    limit: int | None = None,
    category_id: str = "",
    level: str = "",
) -> list[dict]:
    """Lấy danh mục cho tới khi đủ `limit` hoặc hết dữ liệu."""
    rows: list[dict] = []
    last_id = ""
    total: int | None = None
    seen: set[str] = set()

    while True:
        page_size = PAGE_SIZE if limit is None else min(PAGE_SIZE, limit - len(rows))
        if page_size <= 0:
            break

        data = client.list_catalog_page(
            last_id=last_id, limit=page_size, level=level,
            department_code=department_code, category_id=category_id)

        items = data.get("items") or []
        if total is None:
            total = data.get("total")
            log.info("tổng số thủ tục khớp bộ lọc: %s", total)
        if not items:
            break

        # Chống lặp vô hạn nếu con trỏ đứng yên.
        fresh = [r for r in items if r.get("id") not in seen]
        if not fresh:
            log.warning("con trỏ không tiến thêm, dừng sớm ở %d bản ghi", len(rows))
            break
        for r in fresh:
            seen.add(r["id"])
        rows.extend(fresh)

        new_last = data.get("lastId") or ""
        if not new_last or new_last == last_id:
            break
        last_id = new_last
        log.info("đã lấy %d bản ghi...", len(rows))

    return rows if limit is None else rows[:limit]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bước ①: lấy danh mục thủ tục")
    ap.add_argument("--department", default="all",
                    help="all (mặc định) | bca | btp | mã thô như G01")
    ap.add_argument("--category", default="", help="categoryId nếu muốn lọc lĩnh vực")
    ap.add_argument("--level", default="", choices=["", "COMMUNE", "PROVINCE", "MINISTRY"],
                    help="cấp thực hiện. COMMUNE = cấp XÃ/PHƯỜNG (TP.HCM gọi Phường)")
    ap.add_argument("--scope", default="", choices=["", "xa"],
                    help="xa = cấp XÃ/PHƯỜNG + thủ tục riêng TP.HCM (paths.SCOPE_XA); "
                         "bỏ qua --department/--level")
    ap.add_argument("--limit", type=int, default=None, help="số bản ghi tối đa")
    ap.add_argument("--rps", type=float, default=2.0)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    paths.ensure_dirs()

    if args.scope == "xa":
        # Hợp nhiều bộ lọc của cổng, khử trùng theo `id`, giữ thứ tự gặp đầu tiên.
        dept, level = "xa", "COMMUNE+" + paths.DEPT_UBND_HCM
        log.info("phạm vi xa: %s", paths.SCOPE_XA)
        rows, seen = [], set()
        with DvcClient(rps=args.rps) as client:
            for d, lv in paths.SCOPE_XA:
                part = fetch_catalog(client, department_code=d, level=lv,
                                     category_id=args.category)
                fresh = [r for r in part if r["id"] not in seen]
                seen.update(r["id"] for r in fresh)
                rows.extend(fresh)
                log.info("  departmentCode=%r level=%r -> %d (mới %d)", d, lv, len(part), len(fresh))
        if args.limit is not None:
            rows = rows[:args.limit]
    else:
        dept, level = paths.resolve_department(args.department), args.level
        log.info("bộ lọc departmentCode=%r (%s)", dept, args.department)
        with DvcClient(rps=args.rps) as client:
            rows = fetch_catalog(client, department_code=dept, level=level,
                                 limit=args.limit, category_id=args.category)

    with paths.CATALOG_PATH.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Ghi lại bộ lọc đã dùng, để EDA biết "nhiều bộ ngành" là CỐ Ý hay LỖI.
    (paths.RAW_DIR / "_catalog_meta.json").write_text(
        json.dumps({"scope": args.scope, "department_arg": args.department,
                    "department_code": dept, "level": level, "limit": args.limit,
                    "n_rows": len(rows)}, ensure_ascii=False),
        encoding="utf-8")

    log.info("ĐÃ GHI %d bản ghi → %s", len(rows), paths.CATALOG_PATH)

    # Kiểm tra ngay: bộ lọc có thật sự sạch không? (phạm vi xa CỐ Ý gồm nhiều bộ ngành)
    depts = {r.get("departmentPromulgate") for r in rows}
    if dept and args.scope != "xa" and len(depts) > 1:
        log.warning("⚠️ bộ lọc ra NHIỀU bộ ngành: %s", depts)
    else:
        log.info("bộ ban hành trong kết quả: %s", depts or "(rỗng)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Đồng bộ dữ liệu web abi.com.vn về máy (lĩnh vực ABI).

    python -m system3.system4.abi.sync [--no-index]

Các bước: ① kéo mọi API công khai (docs/PLAN_ABI_LINH_VUC.md mục 1.3) -> ② kiểm cấu trúc (hỏng thì GIỮ bản cũ)
-> ③ chuẩn hoá (normalize.py) -> ④ ghi raw.json + data.json -> ⑤ dựng lại bộ dữ liệu tìm kiếm (index.py, cần Ollama).
Chi tiết tin chỉ tải lại khi updatedAt đổi: lần đầu ~300 request (~2,5 phút ở 2 request/giây), các lần sau ~25 request.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import threading
import time
import traceback
from datetime import datetime

from . import normalize, store
from .client import AbiError, Client

log = logging.getLogger("system4.abi.sync")

# Trang tĩnh có nội dung (routeKey trong /site/pages/{key}); trang chỉ là khung danh sách thì normalize bỏ (< 80 ký tự chữ)
PAGES = ("about", "functions", "business-incubation", "technology-incubation", "quy-trinh-tham-gia-uom-tao",
         "dieu-kien-tham-gia-uom-tao", "doi-tuong-tham-gia-uom-tao", "cong-nghe-vi-sinh", "cong-nghe-thuy-san",
         "cong-nghe-te-bao", "cong-nghe-cay-trong", "chuyen-doi-so", "doi-tac", "contact", "services", "products", "cooperation")
LOCALE = "vi"

_state = {"running": False, "step": "", "started": None}
_run_lock = threading.Lock()


def state() -> dict:
    return dict(_state)


def _step(msg: str) -> None:
    _state["step"] = msg
    log.info(msg)


def fetch(c: Client, prev: dict | None = None) -> dict:
    prev_details = (prev or {}).get("post_details") or {}
    prev_updated = {p.get("slug"): p.get("updatedAt") for p in (prev or {}).get("posts") or []}
    raw: dict = {"fetched_at": datetime.now(normalize.VN).isoformat(timespec="seconds"), "locale": LOCALE}
    _step("Thông tin trung tâm, cơ cấu tổ chức…")
    raw["settings"] = c.get("/site/settings", locale=LOCALE).get("data") or {}
    raw["organization"] = c.get("/organization", locale=LOCALE).get("data") or {}
    _step("Sự kiện, chương trình…")
    raw["events"] = c.paged("/events", 50, locale=LOCALE)
    raw["programs"] = c.paged("/programs", 50, locale=LOCALE)
    _step("Đối tác, sản phẩm, dịch vụ…")
    raw["catalog"] = c.paged("/catalog", 100, locale=LOCALE)
    raw["partner_categories"] = c.get("/catalog/partner-categories", locale=LOCALE).get("data") or []
    _step("Trang giới thiệu…")
    raw["pages"] = {}
    for key in PAGES:
        try:   # đúng dạng trong danh sách endpoint chính thức của chủ web: /site/pages/{routeKey}?locale=vi
            raw["pages"][key] = c.get(f"/site/pages/{key}", locale=LOCALE).get("data") or {}
        except AbiError as e:   # trang bị gỡ / đổi tên: bỏ qua trang đó
            if e.status != 404:
                raise
    _step("Danh sách tin…")
    raw["posts"] = c.paged("/content/posts", 100, locale=LOCALE)
    todo = [p for p in raw["posts"] if p.get("contentType") in ("news", "resource")]
    raw["post_details"] = {}
    for i, p in enumerate(todo, 1):
        slug = p.get("slug")
        if slug in prev_details and prev_updated.get(slug) == p.get("updatedAt"):
            raw["post_details"][slug] = prev_details[slug]
            continue
        _step(f"Nội dung tin {i}/{len(todo)}…")
        try:
            raw["post_details"][slug] = c.get(f"/content/posts/{slug}", locale=LOCALE).get("data") or {}
        except AbiError as e:   # một tin lỗi không làm hỏng cả lần đồng bộ: dùng tóm tắt trong danh sách
            log.warning("tin %s: %s", slug, e)
    return scrub_personal(raw)


HIDDEN = "[đã ẩn]"


def scrub_personal(raw: dict) -> dict:
    """Thoả thuận với chủ web: không dùng email / số điện thoại RIÊNG của cán bộ (hotline, email chung của trung tâm và
    các phòng thì được). Bỏ khỏi danh bạ ngay khi tải về — không lưu vào raw.json / data.json — và xoá chỗ chúng lỡ xuất hiện
    trong bài, trang, chương trình. Kiểm 16/10/2026: 12/66 cán bộ có email riêng, 0 có số điện thoại, không nằm ở chỗ khác."""
    org = raw.get("organization") or {}
    people = org.get("people") or []
    shared = {(d.get("email") or "").strip().lower() for d in org.get("departments") or []}
    shared.add(((raw.get("settings") or {}).get("publicEmail") or "").strip().lower())
    emails = {p["email"].strip() for p in people if (p.get("email") or "").strip() and p["email"].strip().lower() not in shared}
    phones = {re.sub(r"\D", "", p["phone"])[-9:] for p in people if len(re.sub(r"\D", "", p.get("phone") or "")) >= 9}
    n_people = sum(1 for p in people if (p.get("email") or "").strip() or (p.get("phone") or "").strip())
    for p in people:
        p["email"], p["phone"] = "", ""
    n_text = 0
    if emails or phones:
        s = json.dumps(raw, ensure_ascii=False)
        for e in emails:
            s, k = re.subn(re.escape(e), HIDDEN, s, flags=re.I)
            n_text += k
        for ph in phones:   # 9 số cuối, cho phép dấu cách / chấm / gạch giữa các số (0912 345 678, +84.912.345.678…)
            s, k = re.subn(r"(?<!\d)" + r"[\s.\-]?".join(ph) + r"(?!\d)", HIDDEN, s)
            n_text += k
        raw = json.loads(s)
    raw["privacy"] = {"people_contacts_removed": n_people, "text_mentions_removed": n_text}
    return raw


def validate(raw: dict, prev_data: dict | None) -> list[str]:
    """Lỗi cấu trúc / dữ liệu tụt bất thường (API đổi, trả rỗng) -> không thay bản đang dùng."""
    org = raw.get("organization") or {}
    bad = []
    if not org.get("departments") or not org.get("people"):
        bad.append("API /organization không có phòng ban / cán bộ")
    if not (raw.get("settings") or {}).get("centerName"):
        bad.append("API /site/settings thiếu tên trung tâm")
    if not raw.get("posts"):
        bad.append("API /content/posts rỗng")
    for e in raw.get("events") or []:
        if not isinstance(e.get("metadata"), dict) or "startsAt" not in e["metadata"]:
            bad.append("API /events thiếu metadata.startsAt (đổi cấu trúc?)")
            break
    if prev_data:   # tụt hơn một nửa so với lần trước: nghi API lỗi
        for key, now in (("departments", len(org.get("departments") or [])), ("posts", len(raw.get("posts") or [])),
                         ("catalog", len(raw.get("catalog") or [])), ("programs", len(raw.get("programs") or []))):
            before = len(prev_data.get(key) or [])
            if before >= 4 and now < before / 2:
                bad.append(f"Số {key} tụt từ {before} xuống {now}")
    return bad


def diff(old: dict | None, new: dict) -> dict:
    out = {}
    for key in ("departments", "people", "events", "programs", "catalog", "posts", "pages"):
        a = {x.get("id") or x.get("key"): x for x in (old or {}).get(key) or []}
        b = {x.get("id") or x.get("key"): x for x in new.get(key) or []}
        out[key] = {"total": len(b), "added": len(b.keys() - a.keys()), "removed": len(a.keys() - b.keys()),
                    "changed": sum(1 for k in a.keys() & b.keys() if a[k] != b[k])}
    return out


def run(client: Client | None = None, index: bool = True) -> dict:
    """Một lần đồng bộ. Đang chạy rồi -> trả {"skipped": True}. Không ném lỗi: lỗi ghi vào kết quả + status.json."""
    if not _run_lock.acquire(blocking=False):
        return {"skipped": True, "reason": "đang đồng bộ"}
    t0 = time.perf_counter()
    _state.update(running=True, started=datetime.now(normalize.VN).isoformat(timespec="seconds"), step="Bắt đầu…")
    res: dict = {"started": _state["started"], "ok": False}
    own = client is None
    c = client or Client()
    try:
        prev_raw, prev_data = store.read_json("raw.json"), store.data()
        raw = fetch(c, prev_raw)
        res["requests"] = c.requests
        res["privacy"] = raw.get("privacy")   # số email / SĐT riêng của cán bộ đã bỏ (thoả thuận với chủ web)
        bad = validate(raw, prev_data)
        if bad:
            res["error"] = "Giữ dữ liệu cũ: " + "; ".join(bad)
            return res
        _step("Chuẩn hoá…")
        data = normalize.build(raw)
        res["diff"] = diff(prev_data, data)
        store.write_json("raw.json", raw)
        store.write_json("data.json", data)
        res.update(ok=True, synced_at=data["synced_at"])
        if index:
            _step("Dựng lại chỉ mục tìm kiếm…")
            from . import index as idx
            try:
                res["index"] = idx.rebuild(data)
            except Exception as e:   # thiếu Ollama…: dữ liệu cho code vẫn dùng được, câu tự do dùng chỉ mục cũ
                log.exception("dựng chỉ mục ABI lỗi")
                res["index_error"] = str(e)
        return res
    except Exception as e:
        log.exception("đồng bộ ABI lỗi")
        res["error"] = f"{type(e).__name__}: {e}"
        res["trace"] = traceback.format_exc()[-2000:]
        return res
    finally:
        res["ms"] = int((time.perf_counter() - t0) * 1000)
        res.setdefault("requests", c.requests)
        if own:
            c.close()
        store.add_run({k: v for k, v in res.items() if k != "trace"})
        _state.update(running=False, step="")
        _run_lock.release()


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Đồng bộ dữ liệu abi.com.vn")
    ap.add_argument("--no-index", action="store_true", help="không dựng chỉ mục tìm kiếm (không cần Ollama)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if not a.no_index:
        from ..server import db
        db.init_db()
    r = run(index=not a.no_index)
    print({k: v for k, v in r.items() if k != "trace"})
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

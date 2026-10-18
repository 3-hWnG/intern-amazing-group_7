"""Đồng bộ dữ liệu abi.com.vn / staging.abi.com.vn về máy thành PHIÊN BẢN (lĩnh vực ABI).

    python -m system3.system4.abi.sync [--source prod|staging] [--no-index]

Các bước: ① kéo các endpoint chính thức (docs/SYSTEM4_ABI.md mục 8a; cần khoá API) -> ② kiểm cấu trúc (hỏng thì không tạo
phiên bản) -> ③ chuẩn hoá -> ④ dữ liệu ĐỔI so với bản mới nhất của nguồn thì thành phiên bản mới, không đổi thì chỉ ghi "kiểm lúc"
-> ⑤ dựng chỉ mục tìm kiếm cho phiên bản mới (dùng lại vector của đoạn không đổi; cần Ollama) -> ⑥ mỗi nguồn giữ 2 phiên bản
mới nhất (versions.prune). Chi tiết tin chỉ tải lại khi updatedAt đổi: lần đầu ~300 request (~2,5 phút ở 2 request/giây),
các lần sau ~28 request. Không gọi trợ lý AI của web.
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

import hashlib

from . import normalize, store, versions
from .client import SOURCES, AbiError, Client

log = logging.getLogger("system4.abi.sync")

# Trang tĩnh có nội dung (routeKey trong /site/pages/{key}); trang chỉ là khung danh sách thì normalize bỏ (< 80 ký tự chữ)
PAGES = ("about", "functions", "business-incubation", "technology-incubation", "quy-trinh-tham-gia-uom-tao",
         "dieu-kien-tham-gia-uom-tao", "doi-tuong-tham-gia-uom-tao", "cong-nghe-vi-sinh", "cong-nghe-thuy-san",
         "cong-nghe-te-bao", "cong-nghe-cay-trong", "chuyen-doi-so", "doi-tac", "contact", "services", "products", "cooperation")
LOCALE = "vi"

_state = {"running": False, "step": "", "started": None, "source": None}
_run_lock = threading.Lock()


def state() -> dict:
    return dict(_state)


def _step(msg: str) -> None:
    _state["step"] = msg
    log.info(msg)


def fetch(c: Client, prev: dict | None = None) -> dict:
    prev_details = (prev or {}).get("post_details") or {}
    prev_updated = {p.get("slug"): p.get("updatedAt") for p in (prev or {}).get("posts") or []}
    raw: dict = {"fetched_at": datetime.now(normalize.VN).isoformat(timespec="seconds"), "locale": LOCALE,
                 "source": c.source, "site_url": SOURCES[c.source]["site"]}
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


def content_hash(data: dict) -> str:
    """Mã băm nội dung (bỏ giờ đồng bộ): giống nhau = dữ liệu web không đổi -> không tạo phiên bản mới."""
    body = {k: v for k, v in data.items() if k != "synced_at"}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def run(source: str = "prod", client: Client | None = None, index: bool = True) -> dict:
    """Một lần đồng bộ một nguồn. Đang chạy rồi -> trả {"skipped": True}. Không ném lỗi: lỗi ghi vào kết quả + status.json."""
    if source not in SOURCES:
        return {"ok": False, "error": f"nguồn lạ: {source}"}
    if not _run_lock.acquire(blocking=False):
        return {"skipped": True, "reason": "đang đồng bộ", "source": source}
    t0 = time.perf_counter()
    _state.update(running=True, started=datetime.now(normalize.VN).isoformat(timespec="seconds"), step="Bắt đầu…", source=source)
    res: dict = {"started": _state["started"], "source": source, "ok": False}
    own = client is None
    c = None
    try:
        c = client or Client(source)
        versions.ensure()
        prev_v = (store.versions(source) or [None])[0]   # bản mới nhất của chính nguồn này
        prev_raw = store.raw(prev_v["id"]) if prev_v else None
        prev_data = store.version_data(prev_v["id"]) if prev_v else None
        raw = fetch(c, prev_raw)
        res["requests"] = c.requests
        res["privacy"] = raw.get("privacy")   # số email / SĐT riêng của cán bộ đã bỏ (thoả thuận với chủ web)
        bad = validate(raw, prev_data)
        if bad:
            res["error"] = "Không tạo phiên bản: " + "; ".join(bad)
            return res
        _step("Chuẩn hoá…")
        data = normalize.build(raw)
        h = content_hash(data)
        res["diff"] = diff(prev_data, data)
        res.update(ok=True, synced_at=data["synced_at"])
        follow = False
        if prev_v and prev_v.get("hash") == h:   # không đổi: giữ phiên bản cũ, chỉ ghi giờ kiểm
            store.update_version(prev_v["id"], checked_at=data["synced_at"])
            res.update(result="unchanged", version_id=prev_v["id"])
            vid = prev_v["id"]
        else:
            follow = versions.follows_latest(source)   # xét TRƯỚC khi thêm bản mới
            vid = store.add_version(source, raw, data, hash=h, requests=c.requests, privacy=raw.get("privacy"))
            res.update(result="new", version_id=vid)
        if index:   # dựng chỉ mục TRƯỚC khi chuyển sang bản mới: trong lúc dựng, câu tự do vẫn tìm trên bản đang dùng
            _step("Tạo chỉ mục tìm kiếm…")
            from . import index as idx
            try:
                res["index"] = idx.build(vid, store.version_data(vid), versions.label(source))
            except Exception as e:   # thiếu Ollama / chưa có dev: câu do code trả lời vẫn dùng được; lịch nền dựng lại sau
                log.exception("dựng chỉ mục ABI lỗi")
                res["index_error"] = str(e)
        if follow:
            versions.activate(vid)
        res["deleted_versions"] = versions.prune(source)   # mỗi nguồn giữ 2 phiên bản mới nhất
        res["active"] = store.active_id()
        return res
    except Exception as e:
        log.exception("đồng bộ ABI lỗi")
        res["error"] = f"{type(e).__name__}: {e}"
        res["trace"] = traceback.format_exc()[-2000:]
        return res
    finally:
        res["ms"] = int((time.perf_counter() - t0) * 1000)
        res.setdefault("requests", c.requests if c else 0)
        if own and c:
            c.close()
        store.add_run({k: v for k, v in res.items() if k != "trace"})
        _state.update(running=False, step="", source=None)
        _run_lock.release()


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Đồng bộ dữ liệu abi.com.vn / staging thành phiên bản")
    ap.add_argument("--source", choices=sorted(SOURCES), default="prod", help="prod = abi.com.vn (mặc định), staging = staging.abi.com.vn")
    ap.add_argument("--no-index", action="store_true", help="không dựng chỉ mục tìm kiếm (không cần Ollama; web tự dựng sau)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    from ..server import db
    db.init_db()   # versions.ensure / prune cần bảng datasets (chỉ mục cũ)
    from .client import api_key
    if not api_key():   # cài đặt lần đầu chưa có khoá: không phải lỗi, chỉ nhắc
        print("NOTE: chưa có khoá API của abi.com.vn (biến môi trường ABI_API_KEY hoặc ⚙ Cài đặt → Lĩnh vực ABI → Khoá API). "
              "Bỏ qua bước tải dữ liệu; điền khoá rồi bấm \"Đồng bộ abi.com.vn\" trong web.")
        return 0
    r = run(a.source, index=not a.no_index)
    print({k: v for k, v in r.items() if k != "trace"})
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

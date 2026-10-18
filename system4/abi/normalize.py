"""raw.json (đúng như API trả) -> data.json (gọn, đủ để code tính và để tạo bản ghi tìm kiếm).

- Nội dung bài / chương trình / sự kiện là tài liệu ProseMirror (TipTap): {"type": "doc", "content": [...]} -> chữ thường.
- Trang tĩnh là các khối {componentType, config{title, summary, items[...]}} -> lấy mọi chữ có nghĩa trong config.
- Ngày giờ API trả UTC ("...Z") -> giờ Việt Nam (UTC+7, không có giờ mùa hè).
- Link công khai dựng theo đường dẫn của web (đọc từ bộ định tuyến trong JS của web).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from .client import SITE_URL

VN = timezone(timedelta(hours=7))
DATA_VERSION = 2   # 2: có site_url / source (bản thật hoặc staging)

# Đường dẫn trang chi tiết (ghép sau địa chỉ web của nguồn: https://abi.com.vn hoặc https://staging.abi.com.vn)
P_EVENT = "/su-kien/{slug}"
P_NEWS = "/tin-tuc/{slug}"
P_RESOURCE = "/tai-lieu/{slug}"
P_PROGRAM = "/chuong-trinh-uom-tao/{slug}"
P_DEPARTMENT = "/gioi-thieu/co-cau-to-chuc/phong-ban/{id}"
P_PERSON = "/gioi-thieu/co-cau-to-chuc/can-bo/{id}"
P_ORG = "/gioi-thieu/co-cau-to-chuc"
P_CONTACT = "/lien-he"
P_CATALOG = {"partner": "/doi-tac/{slug}", "product": "/san-pham-dich-vu/san-pham/{slug}", "service": "/san-pham-dich-vu/{slug}"}


def link(where, path: str) -> str:
    """where: dữ liệu đã chuẩn hoá (có site_url) hoặc địa chỉ web; path: "/..." -> link đầy đủ trên đúng nguồn."""
    site = where.get("site_url") if isinstance(where, dict) else where
    return (site or SITE_URL).rstrip("/") + path
KIND_VI = {"partner": "Đối tác", "product": "Sản phẩm", "service": "Dịch vụ"}

# Khoá chứa chữ có nghĩa trong khối trang / thân chương trình; khoá kỹ thuật bị bỏ qua
_TEXT_KEYS = {"title", "name", "label", "kicker", "summary", "description", "about", "caption", "heading", "subtitle", "question",
              "answer", "value", "role", "organization", "statusLabel", "deadlineLabel", "mode", "organizer", "contactName",
              "contactEmail", "contactPhone", "quote", "author", "body", "text", "note", "content", "unit", "date"}
_SKIP_KEYS = {"id", "slug", "url", "href", "presetId", "presentation", "binding", "componentType", "mediaAssetId", "photoUrl",
              "logoMediaAssetId", "desktopMediaAssetId", "mobileMediaAssetId", "heroMediaAssetId", "imageUrl", "icon", "variant",
              "layout", "style", "tone", "theme", "align", "alignment", "columns", "rows", "order", "active", "revision", "websiteUrl"}


def clean(t) -> str:
    return re.sub(r"[ \t ]+", " ", str(t or "")).strip()


def dt(s) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(VN)
    except ValueError:
        return None


def iso(s) -> str | None:
    d = dt(s)
    return d.isoformat() if d else None


# ---------------------------------------------------------------- chữ
def pm_text(doc) -> str:
    """ProseMirror -> chữ: đoạn / tiêu đề mỗi cái một dòng, mục danh sách "- ", ô bảng cách nhau " | "."""
    lines: list[str] = []

    def inline(n) -> str:
        if not isinstance(n, dict):
            return ""
        if n.get("type") == "text":
            return n.get("text") or ""
        if n.get("type") == "hardBreak":
            return "\n"
        return "".join(inline(c) for c in n.get("content") or [])

    def block(n, prefix=""):
        if not isinstance(n, dict):
            return
        t = n.get("type")
        if t in ("paragraph", "heading", "blockquote_text"):
            s = clean(inline(n))
            if s:
                lines.append(prefix + s)
        elif t in ("bulletList", "orderedList"):
            for i, li in enumerate(n.get("content") or [], 1):
                for c in li.get("content") or []:
                    block(c, prefix + ("- " if t == "bulletList" else f"{i}. "))
        elif t == "tableRow":
            cells = [clean(" ".join(clean(inline(p)) for p in (cell.get("content") or []))) for cell in n.get("content") or []]
            if any(cells):
                lines.append(" | ".join(cells))
        elif t in ("attachment", "file", "fileAttachment") and clean(n.get("label") or n.get("name")):
            lines.append(prefix + "Tệp đính kèm: " + clean(n.get("label") or n.get("name")))
        elif t == "image" and clean((n.get("attrs") or {}).get("alt") or n.get("caption")):
            lines.append(prefix + "Hình: " + clean((n.get("attrs") or {}).get("alt") or n.get("caption")))
        elif t == "text":
            s = clean(n.get("text"))
            if s:
                lines.append(prefix + s)
        else:
            for c in n.get("content") or []:
                block(c, prefix)

    if isinstance(doc, dict):
        block(doc)
    elif isinstance(doc, str):
        return doc.strip()
    return "\n".join(lines).strip()


def any_text(obj, out: list[str] | None = None) -> list[str]:
    """Gom chữ có nghĩa từ một cấu trúc lồng nhau (khối trang, thân chương trình / sự kiện). Không lặp lại dòng."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        if obj.get("type") == "doc":
            s = pm_text(obj)
            if s:
                out.append(s)
            return out
        has_doc = isinstance(obj.get("aboutDocument"), dict) and pm_text(obj["aboutDocument"])
        for k, v in obj.items():
            if k in _SKIP_KEYS or k.endswith(("Id", "Url", "MediaAssetId")) or (k == "about" and has_doc):
                continue
            if isinstance(v, str):
                if k in _TEXT_KEYS and clean(v) and not v.startswith(("http://", "https://", "/api/")):
                    out.append(clean(v) if "\n" not in v else v.strip())
            elif isinstance(v, (dict, list)):
                any_text(v, out)
    elif isinstance(obj, list):
        for v in obj:
            any_text(v, out)
    seen, uniq = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    out[:] = uniq
    return out


def body_text(b: dict, skip: tuple = ()) -> str:
    """Thân chương trình / sự kiện: phần giới thiệu (aboutDocument, không có thì about) trước, rồi lợi ích, tiêu chí, lịch trình…"""
    intro = pm_text(b.get("aboutDocument")) if isinstance(b.get("aboutDocument"), dict) else ""
    intro = intro or clean(b.get("about"))
    rest = any_text({k: v for k, v in b.items() if k not in ("about", "aboutDocument", *skip)})
    return "\n".join([intro] * bool(intro) + [s for s in rest if s != intro])


def cats(items) -> list[str]:
    names = []
    for c in items or []:
        n = clean(c.get("name") or c.get("nameVi")) if isinstance(c, dict) else ""
        if n and n not in names:
            names.append(n)
    return names


# ---------------------------------------------------------------- từng loại
def center(s: dict, site: str = SITE_URL) -> dict:
    social = [x for x in s.get("socialLinks") or [] if x.get("active", True)]
    fb = next((x.get("url") for x in social if x.get("platform") == "facebook"), None)
    return {"name": clean(s.get("centerName")), "name_en": clean(s.get("brandSubtitle")),
            "address": clean(s.get("addressLine1")), "address2": clean(s.get("addressLine2")),
            "hotline": clean(s.get("hotline") or s.get("phone")), "email": clean(s.get("publicEmail")),
            "work_days": clean(s.get("workDays")), "work_hours": clean(s.get("workHours")),
            "owner": clean(s.get("footerCopy")), "facebook": fb, "map_url": s.get("mapUrl"), "url": link(site, P_CONTACT)}


def organization(o: dict, site: str = SITE_URL) -> tuple[list[dict], list[dict]]:
    titles = {t["id"]: t for t in o.get("titles") or []}
    depts = sorted(o.get("departments") or [], key=lambda d: (d.get("order") or 0, d.get("name") or ""))
    dname = {d["id"]: clean(d.get("name")) for d in depts}
    people = []
    for p in sorted(o.get("people") or [], key=lambda p: (titles.get(p.get("titleId"), {}).get("order", 99), p.get("order") or 0)):
        t = titles.get(p.get("titleId")) or {}
        people.append({"id": p["id"], "name": clean(p.get("name")), "degree": clean(p.get("degree")),
                       "title": clean(t.get("name")) or "Cán bộ", "title_order": t.get("order", 99), "leadership": bool(t.get("isLeadership")),
                       "department_id": p.get("departmentId"), "department": dname.get(p.get("departmentId"), ""),
                       "email": clean(p.get("email")), "phone": clean(p.get("phone")), "bio": clean(p.get("bio")),
                       "url": link(site, P_PERSON.format(id=p["id"]))})
    out = []
    for d in depts:
        staff = [p for p in people if p["department_id"] == d["id"]]
        out.append({"id": d["id"], "name": dname[d["id"]], "order": d.get("order") or 0, "leadership_unit": bool(d.get("isLeadershipUnit")),
                    "parent_id": d.get("parentId"), "email": clean(d.get("email")),
                    "summary": pm_text(d.get("summary")) if isinstance(d.get("summary"), dict) else clean(d.get("summary")),
                    "introduction": pm_text(d.get("introduction")) if isinstance(d.get("introduction"), dict) else clean(d.get("introduction")),
                    "n_people": len(staff), "url": link(site, P_DEPARTMENT.format(id=d["id"]))})
    return out, people


def event(e: dict, site: str = SITE_URL) -> dict:
    m, b = e.get("metadata") or {}, e.get("body") or {}
    org = ((b.get("organizations") or {}).get("primary") or {}).get("name")
    return {"id": e["id"], "slug": e.get("slug"), "title": clean(e.get("title")), "summary": clean(e.get("summary")),
            "starts": iso(m.get("startsAt")), "ends": iso(m.get("endsAt")), "location": clean(m.get("location")),
            "mode": clean(b.get("mode")), "organizer": clean(org), "categories": cats(e.get("categories")),
            "status_api": e.get("lifecycleStatus"), "registration": bool(b.get("registrationEnabled")),
            "text": body_text(b, ("mode", "organizations")),
            "url": link(site, P_EVENT.format(slug=e.get("slug") or e["id"])), "updated": e.get("updated_at")}


def program(p: dict, site: str = SITE_URL) -> dict:
    m, b = p.get("metadata") or {}, p.get("body") or {}
    return {"id": p["id"], "slug": p.get("slug"), "title": clean(p.get("title")), "summary": clean(p.get("summary")),
            "starts": iso(m.get("startsAt")), "ends": iso(m.get("endsAt")), "application_url": m.get("applicationUrl"),
            "categories": cats(p.get("categories")), "status_api": p.get("lifecycleStatus"),
            "organizer": clean(b.get("organizer")), "contact": ", ".join(x for x in (clean(b.get("contactName")), clean(b.get("contactEmail")),
                                                                                    clean(b.get("contactPhone"))) if x),
            "links": [{"label": clean(x.get("label")), "url": x.get("url")} for x in b.get("links") or [] if x.get("url")],
            "text": body_text(b, ("organizer", "contactName", "contactEmail", "contactPhone", "links")),
            "url": link(site, P_PROGRAM.format(slug=p.get("slug") or p["id"])), "updated": p.get("updated_at")}


def catalog_item(c: dict, site: str = SITE_URL) -> dict:
    kind = c.get("kind") or "partner"
    desc = c.get("description")
    return {"id": c["id"], "kind": kind, "kind_vi": KIND_VI.get(kind, kind), "slug": c.get("slug"), "name": clean(c.get("name")),
            "summary": clean(c.get("summary")), "description": pm_text(desc) if isinstance(desc, dict) else clean(desc),
            "categories": cats(c.get("categories")) or ([clean(c["category"])] if c.get("category") else []),
            "website": c.get("websiteUrl"), "email": clean(c.get("contactEmail")), "phone": clean(c.get("contactPhone")),
            "address": clean(c.get("address")), "url": link(site, P_CATALOG.get(kind, P_CATALOG["partner"]).format(slug=c.get("slug") or c["id"]))}


# Bài KHÔNG dùng để trả lời (chủ web chưa gỡ; kiểm 16/10/2026):
#  - bài cũ đã có dữ liệu chính thức thay thế: "Cơ Cấu Tổ Chức" (03/2025, 7 phòng) vs API /organization (8 phòng) — trợ lý của web
#    đọc bài này nên trả lời sai số phòng ban
#  - trang mẫu của giao diện web chưa sửa: "Thông Tin Liên" có "yahoo: myYahoo", "skype: mySkype", fax / email giả
SUPERSEDED_TITLES = {"co cau to chuc": "bài cũ: đã có cơ cấu tổ chức chính thức (API /organization)"}
_PLACEHOLDER = re.compile(r"\bmy(?:yahoo|skype|viber)\d*\b", re.I)


def excluded(title: str, text: str) -> str | None:
    from ..server.ground import fold
    t = " ".join(re.findall(r"[a-z0-9]+", fold(title)))
    if t in SUPERSEDED_TITLES:
        return SUPERSEDED_TITLES[t]
    if _PLACEHOLDER.search(text or ""):
        return "trang mẫu của giao diện web (myYahoo, mySkype…), thông tin liên hệ không thật"
    return None


def post(p: dict, detail: dict | None, site: str = SITE_URL) -> dict:
    t = p.get("contentType") or "news"
    body = (detail or {}).get("body")
    text = pm_text(body) if body else ""
    return {"id": p["id"], "slug": p.get("slug"), "type": t, "title": clean(p.get("title")), "summary": clean(p.get("summary")),
            "categories": cats(p.get("categories")), "published": iso(p.get("publishedAt")), "updated": p.get("updatedAt"),
            "text": text, "excluded": excluded(p.get("title") or "", text),
            "url": link(site, (P_RESOURCE if t == "resource" else P_NEWS).format(slug=p.get("slug") or p["id"]))}


def page(key: str, pg: dict, site: str = SITE_URL) -> dict:
    parts = []
    for b in sorted(pg.get("blocks") or [], key=lambda b: b.get("order") or 0):
        if b.get("active", True) and b.get("componentType") != "dynamic-content-grid":   # lưới tin tự động: không phải nội dung trang
            parts += any_text(b.get("config") or {})
    seen, text = set(), []
    for s in parts:
        if s not in seen:
            seen.add(s)
            text.append(s)
    return {"key": key, "path": pg.get("path") or "/", "title": clean(pg.get("title")), "text": "\n".join(text),
            "url": link(site, pg.get("path") or "/"), "updated": pg.get("updatedAt")}


def build(raw: dict) -> dict:
    site = raw.get("site_url") or SITE_URL
    depts, people = organization(raw.get("organization") or {}, site)
    details = raw.get("post_details") or {}
    posts = [post(p, details.get(p.get("slug")), site) for p in raw.get("posts") or [] if p.get("contentType") in ("news", "resource")]
    return {
        "version": DATA_VERSION,
        "source": raw.get("source") or "prod",
        "site_url": site,
        "synced_at": raw.get("fetched_at"),
        "center": center(raw.get("settings") or {}, site),
        "departments": depts,
        "people": people,
        "events": sorted((event(e, site) for e in raw.get("events") or []), key=lambda e: e["starts"] or ""),
        "programs": [program(p, site) for p in raw.get("programs") or []],
        "catalog": [catalog_item(c, site) for c in raw.get("catalog") or []],
        "partner_categories": [{"name": clean(c.get("nameVi")), "count": c.get("itemCount") or 0} for c in raw.get("partner_categories") or []],
        "posts": sorted(posts, key=lambda p: p["published"] or "", reverse=True),
        "pages": [pg for pg in (page(k, v, site) for k, v in (raw.get("pages") or {}).items()) if len(pg["text"]) >= 80],
    }

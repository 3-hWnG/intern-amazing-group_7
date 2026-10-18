"""Code tính trên data.json — model 4B không đếm / so ngày đáng tin, nên các câu đếm, liệt kê, theo thời gian do code làm.

Mỗi hàm trả một "dữ kiện" (Fact):
  title   : tên ngắn (hiện trong 🔍 và làm tiêu đề đoạn dữ liệu [1] cho AI)
  text    : thẻ dữ kiện đầy đủ, gửi cho AI khi câu hỏi có thêm điều kiện code chưa hiểu hết
  answer  : câu trả lời hoàn chỉnh bằng code (Markdown, ghi [n] theo sources) — dùng khi router hiểu trọn câu hỏi
  sources : [{"title", "url"}] — [n] trong answer trỏ tới sources[n-1]
"Sắp diễn ra" tính LÚC HỎI theo giờ Việt Nam từ startsAt/endsAt, không dùng lifecycleStatus đã lưu lúc đồng bộ.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from ..server.ground import fold
from . import normalize

VN = normalize.VN
WEEKDAYS = ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật")
LIST_MAX = 40


def now_vn() -> datetime:
    return datetime.now(VN)


# Thẻ dữ kiện gửi cho AI (khi code không trả lời trọn): tên + link của CẢ thẻ (thẻ sự kiện liệt kê mọi sự kiện -> trang danh sách)
# card_url là đường dẫn "/..." — turn.py ghép với địa chỉ web của nguồn dữ liệu đang dùng (bản thật / staging)
CARD = {"events": ("Danh sách sự kiện trên web (trạng thái tính theo hôm nay)", "/su-kien"),
        "org": ("Cơ cấu tổ chức Trung tâm", normalize.P_ORG)}


def fact(intent: str, title: str, text: str, answer: str | None, sources: list[dict], **extra) -> dict:
    card = CARD.get(intent.split("_")[0]) if intent != "event_detail" else None
    return {"intent": intent, "title": title, "text": text, "answer": answer, "sources": sources,
            "card_title": card[0] if card else title, "card_url": card[1] if card else (sources[0]["url"] if sources else None), **extra}


# ------------------------------------------------------------- định dạng
def d(s) -> datetime | None:
    return normalize.dt(s)


def fmt_dt(x: datetime | None) -> str:
    return x.strftime("%H:%M %d/%m/%Y") if x else "?"


def fmt_day(x: datetime) -> str:
    return x.strftime("%d/%m/%Y")


def fmt_range(s: datetime | None, e: datetime | None) -> str:
    if not s:
        return "chưa có ngày"
    if not e:
        return fmt_dt(s)
    if s.date() == e.date():
        return f"{s:%H:%M} – {e:%H:%M} {fmt_day(s)}"
    return f"{fmt_dt(s)} – {fmt_dt(e)}"


def today_line(now: datetime) -> str:
    return f"Hôm nay là {WEEKDAYS[now.weekday()]}, {now:%d/%m/%Y} (giờ Việt Nam, {now:%H:%M})."


def updated_line(data: dict) -> str:
    s = d(data.get("synced_at"))
    return f"_Theo dữ liệu abi.com.vn cập nhật lúc {fmt_dt(s)}._" if s else "_Theo dữ liệu abi.com.vn._"


def _src(title: str, url: str) -> dict:
    return {"title": title, "url": url}


# ------------------------------------------------------------- sự kiện
def event_status(e: dict, now: datetime) -> str:
    s, en = d(e.get("starts")), d(e.get("ends"))
    if not s:
        return "unknown"
    end = en or s.replace(hour=23, minute=59)
    if s > now:
        return "upcoming"
    return "ongoing" if end >= now else "past"


STATUS_VI = {"upcoming": "sắp diễn ra", "ongoing": "đang diễn ra", "past": "đã diễn ra", "unknown": "chưa rõ ngày"}


def _event_lines(evs: list[dict], start_n: int, now: datetime, with_status: bool = False) -> list[str]:
    out = []
    for i, e in enumerate(evs, start_n):
        where = e.get("location") or "chưa ghi địa điểm"
        if e.get("mode"):
            where += f" ({e['mode']})"
        st = f" — {STATUS_VI[event_status(e, now)]}" if with_status else ""
        out.append(f"{i - start_n + 1}. **{e['title']}** [{i}]{st}\n   - Thời gian: {fmt_range(d(e.get('starts')), d(e.get('ends')))}\n"
                   f"   - Địa điểm: {where}")
    return out


def event_card(e: dict, now: datetime) -> str:
    lines = [f"Sự kiện: {e['title']}", f"Trạng thái (so với hôm nay): {STATUS_VI[event_status(e, now)]}",
             f"Thời gian: {fmt_range(d(e.get('starts')), d(e.get('ends')))}", f"Địa điểm: {e.get('location') or 'chưa ghi'}"]
    for label, key in (("Hình thức", "mode"), ("Đơn vị tổ chức", "organizer"), ("Tóm tắt", "summary")):
        if e.get(key):
            lines.append(f"{label}: {e[key]}")
    if e.get("categories"):
        lines.append("Chuyên mục: " + ", ".join(e["categories"]))
    if e.get("text"):
        lines.append("Nội dung: " + e["text"][:1500])
    lines.append(f"Link: {e['url']}")
    return "\n".join(lines)


def _words(t: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", fold(t))


def in_place(e: dict, aliases: list[str]) -> bool:
    loc = " " + " ".join(_words(e.get("location") or "")) + " "
    return any(f" {a} " in loc for a in aliases)


def events_overview(data: dict, now: datetime, which: str = "upcoming", month: tuple[int, int] | None = None,
                    place: tuple[str, list[str]] | None = None) -> dict:
    """which: upcoming (sắp + đang diễn ra) | past | all | month (cần month=(tháng, năm)).
    place = (tên hiển thị, các cách viết không dấu) -> chỉ các sự kiện có địa điểm chứa một cách viết đó (vd. "Hà Nội")."""
    all_evs = data.get("events") or []
    evs = [e for e in all_evs if in_place(e, place[1])] if place else all_evs
    at = f" ở {place[0]}" if place else ""
    by = {k: [e for e in evs if event_status(e, now) == k] for k in ("upcoming", "ongoing", "past")}
    by["upcoming"].sort(key=lambda e: e.get("starts") or "")
    by["ongoing"].sort(key=lambda e: e.get("starts") or "")
    by["past"].sort(key=lambda e: e.get("starts") or "", reverse=True)
    card = [today_line(now), f"Tổng số sự kiện trên abi.com.vn: {len(all_evs)}."]
    if place:
        card.append(f"Sự kiện có địa điểm ở {place[0]}: {len(evs)} (sắp diễn ra {len(by['upcoming'])}, đang diễn ra {len(by['ongoing'])}, "
                    f"đã diễn ra {len(by['past'])}).")
    for e in sorted(all_evs, key=lambda e: e.get("starts") or ""):
        card.append(f"- {e['title']} | {STATUS_VI[event_status(e, now)]} | {fmt_range(d(e.get('starts')), d(e.get('ends')))} | "
                    f"{e.get('location') or 'chưa ghi địa điểm'}{' | ' + e['mode'] if e.get('mode') else ''} | {e['url']}")
    text = "\n".join(card)
    foot = updated_line(data)
    if which == "month" and month:
        m, y = month
        lo = datetime(y, m, 1, tzinfo=VN)
        hi = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=VN)
        sel = [e for e in sorted(evs, key=lambda e: e.get("starts") or "")
               if d(e.get("starts")) and d(e.get("starts")) < hi and (d(e.get("ends")) or d(e.get("starts"))) >= lo]
        title = f"Sự kiện trong tháng {m}/{y}{at}"
        if not sel:
            ans = f"Trên abi.com.vn không có sự kiện nào diễn ra trong tháng {m}/{y}{at}.\n\n{foot}"
            return fact("events_month", title, text, ans, [_src("Sự kiện", normalize.link(data, "/su-kien"))])
        ans = "\n".join([f"**{title}**: {len(sel)} sự kiện", *_event_lines(sel, 1, now, with_status=True), "", foot])
        return fact("events_month", title, text, ans, [_src(e["title"], e["url"]) for e in sel])
    if which == "past":
        sel = by["past"][:10]
        title = "Sự kiện đã diễn ra" + at
        if not sel:
            return fact("events_past", title, text, f"Trên abi.com.vn chưa có sự kiện nào đã diễn ra{at}.\n\n{foot}", [])
        more = f"\n\n(Liệt kê {len(sel)} sự kiện gần nhất trong tổng số {len(by['past'])}.)" if len(by["past"]) > len(sel) else ""
        ans = "\n".join([f"**Các sự kiện đã diễn ra{at} gần đây** ({len(by['past'])} sự kiện, mới nhất trước):",
                         *_event_lines(sel, 1, now)]) + more + f"\n\n{foot}"
        return fact("events_past", title, text, ans, [_src(e["title"], e["url"]) for e in sel])
    if which == "all":
        title = "Số sự kiện" + at
        ans = (f"Trên abi.com.vn hiện có **{len(evs)} sự kiện{at}** [1]: {len(by['upcoming'])} sắp diễn ra, {len(by['ongoing'])} đang diễn ra, "
               f"{len(by['past'])} đã diễn ra (tính đến {fmt_day(now)}).\n\n{foot}")
        return fact("events_count", title, text, ans, [_src("Sự kiện", normalize.link(data, "/su-kien"))])
    # sắp diễn ra (kèm đang diễn ra)
    title = "Sự kiện sắp diễn ra" + at
    parts, sources, n = [], [], 1
    if by["ongoing"]:
        parts += [f"**Đang diễn ra** ({len(by['ongoing'])}):", *_event_lines(by["ongoing"], n, now), ""]
        sources += [_src(e["title"], e["url"]) for e in by["ongoing"]]
        n += len(by["ongoing"])
    if by["upcoming"]:
        parts += [f"**Các sự kiện sắp diễn ra{at}** (tính từ {fmt_day(now)}): {len(by['upcoming'])} sự kiện", *_event_lines(by["upcoming"], n, now)]
        sources += [_src(e["title"], e["url"]) for e in by["upcoming"]]
    elif not by["ongoing"]:
        last = by["past"][0] if by["past"] else None
        parts.append(f"Hiện chưa có sự kiện sắp diễn ra{at} trên abi.com.vn (tính từ {fmt_day(now)}).")
        if last:
            parts.append(f"Sự kiện gần nhất đã diễn ra{at}: **{last['title']}** [1] ({fmt_range(d(last.get('starts')), d(last.get('ends')))}).")
            sources.append(_src(last["title"], last["url"]))
    else:
        parts.append(f"Ngoài các sự kiện đang diễn ra, chưa có sự kiện nào sắp diễn ra (tính từ {fmt_day(now)}).")
    return fact("events_upcoming", title, text, "\n".join(parts + ["", foot]), sources)


def event_detail(data: dict, events: list[dict], now: datetime) -> dict:
    text = "\n\n".join([today_line(now)] + [event_card(e, now) for e in events])
    return fact("event_detail", "Sự kiện: " + "; ".join(e["title"] for e in events)[:120], text, None,
                [_src(e["title"], e["url"]) for e in events])


# ------------------------------------------------------------- tổ chức
def _units(data: dict) -> tuple[list[dict], list[dict]]:
    deps = data.get("departments") or []
    return [x for x in deps if x.get("leadership_unit")], [x for x in deps if not x.get("leadership_unit")]


def _person(p: dict) -> str:
    return f"{p['degree'] + ' ' if p.get('degree') else ''}{p['name']}"


def org_card(data: dict) -> str:
    lead, rooms = _units(data)
    people = data.get("people") or []
    lines = [f"Cơ cấu tổ chức (abi.com.vn): {len(lead)} Ban Giám đốc + {len(rooms)} phòng = {len(lead) + len(rooms)} đơn vị; "
             f"tổng {len(people)} cán bộ."]
    for x in lead + rooms:
        heads = [p for p in people if p["department_id"] == x["id"] and p["title_order"] <= 4]
        lines.append(f"- {x['name']}: {x['n_people']} cán bộ"
                     + ("; lãnh đạo: " + ", ".join(f"{p['title']} {_person(p)}" for p in heads) if heads else "")
                     + (f"; email: {x['email']}" if x.get("email") else ""))
    by_title = Counter(p["title"] for p in people)
    lines.append("Theo chức vụ: " + ", ".join(f"{t} {n}" for t, n in by_title.most_common()))
    return "\n".join(lines)


def org_departments(data: dict) -> dict:
    lead, rooms = _units(data)
    people = data.get("people") or []
    lead_txt = " và ".join(f"**{x['name']}**" for x in lead) or "Ban Giám đốc"
    lines = [f"Trung tâm có **{len(rooms)} phòng** cùng {lead_txt} (tổng cộng {len(rooms) + len(lead)} đơn vị, {len(people)} cán bộ) [1]:"]
    lines += [f"{i}. {x['name']} — {x['n_people']} cán bộ" for i, x in enumerate(rooms, 1)]
    lines += [f"- {x['name']}: {x['n_people']} người" for x in lead]
    lines += ["", updated_line(data)]
    return fact("org_departments", "Cơ cấu tổ chức", org_card(data), "\n".join(lines), [_src("Cơ cấu tổ chức", normalize.link(data, normalize.P_ORG))])


def org_people(data: dict) -> dict:
    lead, rooms = _units(data)
    people = data.get("people") or []
    parts = ", ".join(f"{x['name']} {x['n_people']}" for x in lead + rooms)
    ans = f"Trung tâm có **{len(people)} cán bộ** [1], gồm: {parts}.\n\n{updated_line(data)}"
    return fact("org_people", "Số cán bộ", org_card(data), ans, [_src("Cơ cấu tổ chức", normalize.link(data, normalize.P_ORG))])


def org_leaders(data: dict) -> dict:
    people = [p for p in data.get("people") or [] if p.get("leadership")]
    people.sort(key=lambda p: p["title_order"])
    if not people:
        return fact("org_leaders", "Ban Giám đốc", org_card(data), None, [_src("Cơ cấu tổ chức", normalize.link(data, normalize.P_ORG))])
    lines = ["**Ban Giám đốc** Trung tâm [1]:"] + [f"- {p['title']}: {_person(p)}" for p in people] + ["", updated_line(data)]
    return fact("org_leaders", "Ban Giám đốc", org_card(data), "\n".join(lines), [_src("Cơ cấu tổ chức", normalize.link(data, normalize.P_ORG))])


# Thoả thuận với chủ web: KHÔNG nêu email / điện thoại riêng của cán bộ (sync.py đã bỏ khi tải về); chỉ email của đơn vị,
# hotline và email chung của trung tâm.
NO_PERSONAL = "Không cung cấp email / điện thoại riêng của cán bộ; liên hệ qua email đơn vị hoặc hotline, email chung của trung tâm."


def department_detail(data: dict, deps: list[dict]) -> dict:
    people = data.get("people") or []
    cards = []
    for x in deps:
        staff = [p for p in people if p["department_id"] == x["id"]]
        lines = [f"Đơn vị: {x['name']}", f"Số cán bộ: {len(staff)}"]
        if x.get("email"):
            lines.append(f"Email đơn vị: {x['email']}")
        lines.append(NO_PERSONAL)
        for p in staff:
            lines.append(f"- {p['title']}: {_person(p)}")
        if x.get("summary"):
            lines.append("Giới thiệu: " + x["summary"][:800])
        if x.get("introduction") and x["introduction"] != x.get("summary"):
            lines.append("Chức năng, nhiệm vụ: " + x["introduction"][:1200])
        lines.append(f"Link: {x['url']}")
        cards.append("\n".join(lines))
    return fact("department_detail", "Đơn vị: " + "; ".join(x["name"] for x in deps), "\n\n".join(cards), None,
                [_src(x["name"], x["url"]) for x in deps])


def person_detail(data: dict, ps: list[dict]) -> dict:
    dep_email = {x["id"]: x.get("email") for x in data.get("departments") or []}
    c = data.get("center") or {}
    cards = []
    for p in ps:
        lines = [f"Cán bộ: {_person(p)}", f"Chức vụ: {p['title']}", f"Đơn vị: {p['department']}", NO_PERSONAL]
        contact = [v for v in (dep_email.get(p["department_id"]) and f"email đơn vị {dep_email[p['department_id']]}",
                               c.get("hotline") and f"hotline {c['hotline']}", c.get("email") and f"email trung tâm {c['email']}") if v]
        if contact:
            lines.append("Liên hệ: " + ", ".join(contact))
        if p.get("bio"):
            lines.append("Giới thiệu: " + p["bio"][:800])
        lines.append(f"Link: {p['url']}")
        cards.append("\n".join(lines))
    return fact("person_detail", "Cán bộ: " + ", ".join(p["name"] for p in ps), "\n\n".join(cards), None,
                [_src(p["name"], p["url"]) for p in ps])


# ------------------------------------------------------------- liên hệ
def contact(data: dict) -> dict:
    c = data.get("center") or {}
    rows = [("Trụ sở", c.get("address")), ("Cơ sở 2", c.get("address2")), ("Hotline", c.get("hotline")), ("Email", c.get("email")),
            ("Giờ làm việc", ", ".join(v for v in (c.get("work_days"), c.get("work_hours")) if v)), ("Facebook", c.get("facebook")),
            ("Cơ quan chủ quản", (c.get("owner") or "").replace("Cơ quan chủ quản:", "").strip())]
    rows = [(k, v) for k, v in rows if v]
    text = "\n".join([f"Tên: {c.get('name')}"] + [f"{k}: {v}" for k, v in rows])
    ans = "\n".join([f"**{c.get('name') or 'Trung tâm'}** [1]"] + [f"- {k}: {v}" for k, v in rows] + ["", updated_line(data)])
    return fact("contact", "Thông tin liên hệ", text, ans, [_src("Liên hệ", c.get("url") or normalize.link(data, normalize.P_CONTACT))])


# ------------------------------------------------------------- chương trình, đối tác, tin
def programs(data: dict) -> dict:
    progs = data.get("programs") or []
    by_cat = Counter(c for p in progs for c in (p.get("categories") or ["Khác"]))
    text = "\n".join([f"Chương trình / chính sách hỗ trợ trên abi.com.vn: {len(progs)}"] +
                     [f"- {p['title']} | {', '.join(p.get('categories') or [])} | {p['url']}" for p in progs])
    shown = progs[:15]
    lines = [f"Trên abi.com.vn có **{len(progs)} chương trình, chính sách hỗ trợ** [1]"
             + (", theo nhóm: " + ", ".join(f"{c} ({n})" for c, n in by_cat.most_common()) if by_cat else "") + ".",
             "", "Một số chương trình nổi bật:" if len(progs) > len(shown) else "Danh sách:"]
    lines += [f"{i}. {p['title']} [{i + 1}]" for i, p in enumerate(shown, 1)]
    if len(progs) > len(shown):
        lines.append(f"\n…và {len(progs) - len(shown)} chương trình khác, xem đầy đủ tại trang Chương trình ươm tạo [1].")
    lines += ["", updated_line(data)]
    return fact("programs", "Chương trình hỗ trợ", text, "\n".join(lines),
                [_src("Chương trình ươm tạo", normalize.link(data, "/chuong-trinh-uom-tao"))] + [_src(p["title"], p["url"]) for p in shown])


INCUBATED = "Doanh nghiệp tham gia ươm tạo"


def catalog(data: dict, kind: str) -> dict:
    """kind: partner | product | service | incubated (đối tác thuộc nhóm "Doanh nghiệp tham gia ươm tạo")."""
    items = data.get("catalog") or []
    if kind == "incubated":
        sel, label, page = [x for x in items if INCUBATED in (x.get("categories") or [])], "doanh nghiệp tham gia ươm tạo", "/doanh-nghiep-uom-tao"
    else:
        sel = [x for x in items if x.get("kind") == kind]
        label, page = {"partner": ("đối tác", "/doi-tac"), "product": ("sản phẩm", "/san-pham-dich-vu/san-pham"),
                       "service": ("dịch vụ", "/san-pham-dich-vu")}[kind]
    text = "\n".join([f"Số {label} trên abi.com.vn: {len(sel)}"] +
                     [f"- {x['name']}{' — ' + x['summary'][:200] if x.get('summary') else ''} | {x['url']}" for x in sel])
    head = f"Trên abi.com.vn có **{len(sel)} {label}** [1]"
    if kind == "partner":
        groups = Counter(c for x in sel for c in (x.get("categories") or ["Chưa phân nhóm"]))
        head += ", gồm: " + ", ".join(f"{c} {n}" for c, n in groups.most_common())
    shown = sel[:LIST_MAX if kind != "partner" else 20]
    lines = [head + ":"] + [f"{i}. {x['name']}" for i, x in enumerate(shown, 1)]
    if len(sel) > len(shown):
        lines.append(f"…và {len(sel) - len(shown)} {label} khác (xem đầy đủ tại abi.com.vn{page} [1]).")
    lines += ["", updated_line(data)]
    return fact("catalog_" + kind, label.capitalize(), text, "\n".join(lines), [_src(label.capitalize(), normalize.link(data, page))])


def news_latest(data: dict, n: int = 6) -> dict:
    posts = [p for p in data.get("posts") or [] if p.get("type") == "news" and not p.get("excluded")][:n]
    text = "\n".join(f"- {p['title']} | đăng {fmt_day(d(p['published'])) if p.get('published') else '?'} | {p['url']}" for p in posts)
    lines = ["**Tin mới nhất trên abi.com.vn:**"] + [
        f"{i}. {p['title']} [{i}] — {fmt_day(d(p['published'])) if p.get('published') else ''}" for i, p in enumerate(posts, 1)]
    return fact("news_latest", "Tin mới", text, "\n".join(lines + ["", updated_line(data)]), [_src(p["title"], p["url"]) for p in posts])

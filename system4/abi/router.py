"""Nhận ý định câu hỏi ABI bằng code (không gọi AI, < 1 ms).

route(text, data, now) -> {"intent", "fact", "plain"} hoặc None (câu tự do -> tìm kiếm).
plain = True khi code hiểu TRỌN câu hỏi: bỏ các từ của ý định và từ đệm thì không còn chữ nào. Khi đó dùng câu trả lời bằng
code; còn chữ lạ (vd. "Sự kiện nào tổ chức ở Hà Nội?" còn "ha noi") thì đưa thẻ dữ kiện cho AI tự lọc, tránh trả lời lệch ý.
"""
from __future__ import annotations

import re
from datetime import datetime

from ..server.ground import fold
from . import tools

_W = re.compile(r"[a-z0-9]+")

# Từ đệm / hỏi chung: không làm đổi ý câu hỏi
FILLER = set("""a ad ah ai anh ban bao biet bo cac cai can chi cho chu co con cua cung da dang day de den di do duoc em gi giup ha hay
hien hoi hom ke khong la lam liet luc ma may minh mot nao nay nhe nhieu nho nhung nua o oi ong ra roi sach sao se so ta tai tat the
thi toi tren trong tu va vay ve voi vui long xem xin thong tin danh tat ca hien nay trung tam abi ahbi uom tao doanh nghiep nong
nghiep cong nghe cao tp hcm ho chi minh duoc khong a nhi vang da thua cam on biet hoi dc ko k j vs ntn nhu the nao gom co bao
hien tai luong tong cu the chinh xac day du giup toi cho minh hay cho xem ban oi bot liet ke ra""".split())

# không gồm "hoạt động": "Trung tâm có những hoạt động gì?" hỏi chức năng / nhiệm vụ, không phải lịch sự kiện
EVENT_NOUN = re.compile(r"\b(su kien|hoi thao|hoi cho|trien lam|toa dam|khoa tap huan|tap huan|workshop|events?|le hoi)\b")
EV_UPCOMING = re.compile(r"\b(sap toi|sap dien ra|sap to chuc|sap|tiep theo|upcoming|se dien ra|se to chuc|toi day|sap den|"
                         r"chuan bi|dang dien ra|dang to chuc|lich)\b")
EV_PAST = re.compile(r"\b(da dien ra|da to chuc|vua qua|vua roi|gan day|truoc day|da qua|da ket thuc|da xong|cu)\b")
EV_MONTH = re.compile(r"\bthang\s*(\d{1,2})(?:\s*(?:/|-|nam)\s*(\d{4}))?\b")
EV_MONTH_REL = re.compile(r"\bthang (nay|sau|toi)\b")
COUNT = re.compile(r"\b(bao nhieu|may|so luong|tong so|tong cong)\b")
LIST = re.compile(r"\b(liet ke|danh sach|nhung|cac|gom|ke ten|co gi|nao|gi)\b")

ORG = re.compile(r"\b(phong ban|cac phong|nhung phong|bao nhieu phong|may phong|co cau to chuc|so do to chuc|bo may|don vi truc thuoc|"
                 r"bo phan|phong chuc nang|phong chuyen mon)\b")
PEOPLE = re.compile(r"\b(bao nhieu|so luong|tong so|may) (can bo|nhan vien|nguoi|nhan su|vien chuc|cong chuc|thanh vien)\b")
LEADERS = re.compile(r"\b(giam doc|ban giam doc|lanh dao|ban lanh dao)\b")
DEPT_CTX = re.compile(r"\b(phong|truong phong|pho phong|pho truong phong|phu trach|can bo|nhan vien|email|lien he|ai)\b")
CONTACT = re.compile(r"\b(dia chi|so dien thoai|dien thoai|hotline|sdt|lien he|lien lac|email|gio lam viec|gio hanh chinh|"
                     r"lam viec|mo cua|facebook|fanpage|tru so|co so|o dau|nam o dau|ban do|co quan chu quan)\b")
PROGRAMS = re.compile(r"\b(chuong trinh|chinh sach)\b")   # không gồm "hỗ trợ": quá chung ("Nghị quyết X hỗ trợ những gì?")
INCUBATED = re.compile(r"\bdoanh nghiep (dang |duoc |da |tham gia )*(uom tao|duoc uom tao)\b|\bdoanh nghiep uom tao\b")
PARTNERS = re.compile(r"\bdoi tac\b")
PRODUCTS = re.compile(r"\bsan pham\b")
SERVICES = re.compile(r"\bdich vu\b")
NEWS = re.compile(r"\b(tin tuc|tin moi|bai viet moi|tin gan day|thong bao moi|tin moi nhat)\b")

# Bí danh phòng ban: phải gặp ĐÚNG cụm này (cụm ngắn như "ke hoach", "to chuc" dễ trùng "kế hoạch kinh doanh", "cơ cấu tổ chức")
DEPT_ALIASES = {
    "vi sinh": ["vi sinh"], "thuy san": ["thuy san"], "te bao": ["te bao"], "cay trong": ["cay trong"],
    "hanh chinh": ["hanh chinh", "to chuc hanh chinh"], "tai chinh": ["tai chinh", "ke hoach tai chinh", "phong ke hoach"],
    "doanh nghiep": ["ho tro doanh nghiep", "quan ly va ho tro"], "tong hop": ["tong hop", "khoa hoc tong hop"],
    "giam doc": ["ban giam doc"],
}
# Địa điểm hay hỏi: tên hiển thị -> các cách viết không dấu (so với địa điểm sự kiện đã bỏ dấu)
PLACES = {"Hà Nội": ["ha noi", "hn"], "TP. Hồ Chí Minh": ["ho chi minh", "hcm", "tphcm", "sai gon", "saigon"],
          "Đà Nẵng": ["da nang"], "Cần Thơ": ["can tho"], "Hải Phòng": ["hai phong"]}
PLACE_PAT = re.compile(r"\b(" + "|".join(a for v in PLACES.values() for a in v) + r"|tp)\b")


# Từ chung trong tên sự kiện: không dùng để nhận ra một sự kiện cụ thể
EV_COMMON = set("""su kien hoi thao hoi cho trien lam toa dam khoa tap huan nong nghiep cong nghe quoc te thanh pho ho chi minh lan thu
nam cho cac du an vao vong ban ket cuoc thi trong linh vuc ung dung cao giua doanh nghiep viet the va ve tai hang dau san pham may
moc thiet bi nganh thuc pham giai phap ben vung doanh khoi nghiep doi moi sang tao gioi thieu ket noi den 2026 2025 2027""".split())


def words(t: str) -> list[str]:
    return _W.findall(fold(t).replace("-", " "))


def _leftover(text: str, *patterns, extra: set[str] = frozenset()) -> list[str]:
    """Chữ còn lại sau khi bỏ cụm của ý định, từ đệm, số (ngày / tháng)."""
    t = " ".join(words(text))
    for p in patterns:
        t = p.sub(" ", t) if hasattr(p, "sub") else t
    return [w for w in t.split() if w not in FILLER and w not in extra and not w.isdigit()]


def _month(text: str, now: datetime) -> tuple[int, int] | None:
    t = " ".join(words(text))
    m = EV_MONTH.search(t)
    if m and 1 <= int(m.group(1)) <= 12:
        mo = int(m.group(1))
        yr = int(m.group(2)) if m.group(2) else (now.year if mo >= now.month - 6 else now.year + 1)
        return mo, yr
    r = EV_MONTH_REL.search(t)
    if r:
        mo, yr = (now.month, now.year) if r.group(1) == "nay" else ((now.month % 12) + 1, now.year + (now.month == 12))
        return mo, yr
    return None


def match_events(text: str, data: dict) -> list[dict]:
    """Sự kiện được nhắc tên: một từ / cặp từ chỉ có trong tên sự kiện đó (vd. "greco", "agroviet", "so huu tri tue")."""
    q = " ".join(words(text))
    qw = set(q.split())
    evs = data.get("events") or []
    grams: dict[str, set[str]] = {}
    for e in evs:
        ws = words(e["title"])
        g = {w for w in ws if w not in EV_COMMON and len(w) >= 4 and not w.isdigit()}
        g |= {f"{a} {b}" for a, b in zip(ws, ws[1:]) if not (a in EV_COMMON and b in EV_COMMON) and not (a.isdigit() or b.isdigit())}
        grams[e["id"]] = g
    count: dict[str, int] = {}
    for g in grams.values():
        for x in g:
            count[x] = count.get(x, 0) + 1
    hits = []
    for e in evs:
        uniq = {x for x in grams[e["id"]] if count[x] == 1}
        if any((x in qw) if " " not in x else (f" {x} " in f" {q} ") for x in uniq):
            hits.append(e)
    return hits


def match_departments(text: str, data: dict) -> list[dict]:
    q = f" {' '.join(words(text))} "
    out = []
    for x in data.get("departments") or []:
        name = " ".join(words(x["name"]))
        for key, aliases in DEPT_ALIASES.items():
            if key in name and any(f" {a} " in q for a in aliases):
                out.append(x)
                break
    return out


def match_people(text: str, data: dict) -> list[dict]:
    """Cán bộ được nhắc tên: đủ họ tên, hoặc hai chữ cuối (tên đệm + tên, vd. "hồng loan")."""
    q = f" {' '.join(words(text))} "
    out = []
    for p in data.get("people") or []:
        ws = words(p["name"])
        if len(ws) >= 2 and (f" {' '.join(ws)} " in q or f" {' '.join(ws[-2:])} " in q):
            out.append(p)
    return out


def route(text: str, data: dict | None, now: datetime) -> dict | None:
    if not data:
        return None
    t = " ".join(words(text))
    if not t:
        return None

    def done(f: dict, plain: bool) -> dict:
        return {"intent": f["intent"], "fact": f, "plain": plain and bool(f.get("answer"))}

    # 1. phòng ban được nhắc tên (cần ngữ cảnh "phòng / trưởng phòng / phụ trách…" để không nhầm "cây trồng" trong chương trình).
    #    Tên sự kiện cũng trùng thì chỉ chọn phòng khi có chữ "phòng" ("Phòng Kế hoạch - Tài chính" vs khoá "xây dựng kế hoạch kinh doanh")
    evs, deps = match_events(text, data), match_departments(text, data)
    if deps and (DEPT_CTX.search(t) or ORG.search(t)) and (not evs or re.search(r"\bphong\b", t)):
        return done(tools.department_detail(data, deps), False)
    # 2. sự kiện được nhắc tên -> thẻ chi tiết cho AI
    if evs:
        return done(tools.event_detail(data, evs, now), False)
    # 3. cán bộ được nhắc tên
    ps = match_people(text, data)
    if ps:
        return done(tools.person_detail(data, ps), False)
    # 4. sự kiện theo thời gian / đếm
    if EVENT_NOUN.search(t):
        month = _month(text, now)
        place = next(((name, al) for name, al in PLACES.items() if any(f" {a} " in f" {t} " for a in al)), None)
        pats = (EVENT_NOUN, EV_UPCOMING, EV_PAST, EV_MONTH, EV_MONTH_REL, COUNT, LIST, PLACE_PAT)
        left = _leftover(text, *pats, extra={"thang", "nam", "dien", "to", "chuc", "khi", "ngay", "o", "tai", "dia", "diem", "thanh", "pho"})
        if month:
            return done(tools.events_overview(data, now, "month", month, place), not left)
        if EV_PAST.search(t) and not EV_UPCOMING.search(t):
            return done(tools.events_overview(data, now, "past", place=place), not left)
        if COUNT.search(t) and not EV_UPCOMING.search(t):
            return done(tools.events_overview(data, now, "all", place=place), not left)
        return done(tools.events_overview(data, now, "upcoming", place=place), not left)
    # 5. tổ chức chung
    if ORG.search(t):
        left = _leftover(text, ORG, COUNT, LIST, extra={"phong", "ban", "don", "vi"})
        return done(tools.org_departments(data), not left)
    if PEOPLE.search(t):
        left = _leftover(text, PEOPLE, COUNT, LIST)
        return done(tools.org_people(data), not left)
    if LEADERS.search(t) and not re.search(r"\bphong\b", t):
        left = _leftover(text, LEADERS, LIST, extra={"pho", "la", "ai", "nhung", "gom"})
        return done(tools.org_leaders(data), not left)
    # 6. danh mục: doanh nghiệp ươm tạo / đối tác / sản phẩm / dịch vụ / chương trình / tin mới — chỉ khi hỏi đếm hoặc liệt kê
    # VÀ code hiểu trọn câu hỏi. Còn chữ lạ (vd. "Nghị quyết 64/2026 hỗ trợ những gì?") -> None: đi tìm kiếm, vì thẻ danh sách
    # quá dài để gửi cho AI (58 chương trình vượt ngữ cảnh 8192 token) và câu hỏi thường về MỘT mục.
    asks_list = COUNT.search(t) or LIST.search(t)
    for pat, kind in ((INCUBATED, "incubated"), (PARTNERS, "partner"), (PRODUCTS, "product"), (SERVICES, "service")):
        if pat.search(t) and asks_list:
            left = _leftover(text, pat, COUNT, LIST, extra={"cung", "cap", "trien", "khai", "hien", "co", "ung"})
            return None if left else done(tools.catalog(data, kind), True)
    if PROGRAMS.search(t) and asks_list:
        left = _leftover(text, PROGRAMS, COUNT, LIST, extra={"uom", "tao", "khoi", "nghiep", "ho", "tro", "danh"})
        return None if left else done(tools.programs(data), True)
    if NEWS.search(t):
        left = _leftover(text, NEWS, LIST, extra={"nhat", "moi", "gan"})
        return None if left else done(tools.news_latest(data), True)
    # 7. liên hệ chung của trung tâm (để cuối: "liên hệ phòng X" đã vào bước 1)
    if CONTACT.search(t):
        left = _leftover(text, CONTACT, LIST, extra={"nam", "dau", "lien", "he", "so"})
        return done(tools.contact(data), not left)
    return None

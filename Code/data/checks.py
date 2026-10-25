"""Bước dựng DB (G2.2): chuẩn hoá link Cổng, bảng phẳng `proc_flat` (G4.2 text-to-SQL) và báo cáo kiểm bất biến.

- Link: Cổng chỉ mở được bằng ID nội bộ (UUID = source_id), không phải mã TTHC (xem system4/scraper/normalize.py).
  Bản cào cũ ghi /thu-tuc-hanh-chinh/1.000005 (trang trống) -> dựng lại từ source_id cho MỌI phiên bản.
- proc_flat: mỗi thủ tục một dòng, các cột đã chuẩn hoá (phí theo data/fees.py, số ngày giải quyết, cờ phạm vi).
- report(): phí < 1.000 đồng không có chữ xác nhận, đơn vị tiền lạ, link sai dạng, mã trùng, trường rỗng.
  Tỉ lệ thủ tục biến mất so với bản đang dùng do System 4 (procs) tính khi dựng một phiên bản."""
from __future__ import annotations

import re

from .fees import CURRENCY
from .textutil import fold

PORTAL = "https://dichvucong.gov.vn/thu-tuc-hanh-chinh/{id}"
PORTAL_SUBMIT = "https://dichvucong.gov.vn/nop-ho-so?formalityId={id}"
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
URL_OK = re.compile(r"^https://dichvucong\.gov\.vn/thu-tuc-hanh-chinh/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
VERTICAL = {"Thuế", "Hải quan"}      # ngành dọc: cùng danh sách với server/policy (VERTICAL)
_DAYS = {"ngày": 1.0, "ngày làm việc": 1.0, "giờ": 1 / 24, "tháng": 30.0}

FLAT_SCHEMA = """
CREATE TABLE proc_flat (
    proc_id TEXT PRIMARY KEY, name TEXT NOT NULL, name_fold TEXT NOT NULL, domain TEXT NOT NULL DEFAULT '',
    levels TEXT NOT NULL DEFAULT '', province TEXT,
    commune_level INTEGER NOT NULL,   -- 1: cơ quan cấp xã/phường giải quyết
    nationwide INTEGER NOT NULL,      -- 1: bản dùng chung toàn quốc (không thuộc riêng tỉnh nào)
    vertical INTEGER NOT NULL,        -- 1: ngành dọc (Thuế, Hải quan)
    in_scope INTEGER NOT NULL,        -- 1: hệ thống trả lời được (cấp xã + toàn quốc + không ngành dọc)
    fee_min_vnd INTEGER, fee_max_vnd INTEGER,   -- mức phí bằng đồng đã đối chiếu (NULL: không có số đáng tin)
    fee_currency TEXT NOT NULL DEFAULT '',      -- VND / USD / '' (không có số)
    fee_free INTEGER NOT NULL DEFAULT 0,        -- 1: nguồn ghi rõ không thu phí / miễn phí cho mọi người
    days_min REAL, days_max REAL,               -- số ngày giải quyết (giờ quy ra ngày, tháng = 30 ngày)
    online INTEGER NOT NULL DEFAULT 0,          -- 1: có nộp trực tuyến
    subjects TEXT NOT NULL DEFAULT ''           -- đối tượng thực hiện, cách nhau bởi '; '
);
"""
_EXPLICIT_FREE = re.compile(r"^(khong thu|mien (le )?phi|khong co|khong mat|khong phai)")
_ONLY_FOR = re.compile(r"\b(cho nguoi|nguoi thuoc|truong hop|dien|doi tuong|doi voi tre|ngoai tru)\b")


def normalize_links(conn) -> dict:
    """portal_url / online_url dựng từ source_id (UUID). Trả số dòng đã đổi."""
    n_portal = n_online = 0
    for row_id, sid, purl, ourl in conn.execute("SELECT row_id, source_id, portal_url, online_url FROM procedures").fetchall():
        if not sid or not UUID.match(sid):
            continue
        p = PORTAL.format(id=sid)
        o = PORTAL_SUBMIT.format(id=sid) if (ourl or "").strip() else ""
        if p != purl or o != (ourl or ""):
            n_portal += p != purl
            n_online += o != (ourl or "")
            conn.execute("UPDATE procedures SET portal_url=?, online_url=? WHERE row_id=?", (p, o, row_id))
    return {"portal_url_rebuilt": n_portal, "online_url_rebuilt": n_online}


def _vertical(domain: str) -> bool:
    return any(p.strip() in VERTICAL for p in (domain or "").split(";"))


def build_flat(conn) -> int:
    conn.executescript(FLAT_SCHEMA)
    fees: dict[str, list] = {}
    for r in conn.execute("SELECT proc_id, kind, amount_text, currency, amount_vnd, amount_ok FROM fees_clean"):
        fees.setdefault(r[0], []).append(r)
    days: dict[int, list[float]] = {}
    for row_id, qty, unit in conn.execute("SELECT row_id, processing_time_qty, processing_time_unit FROM procedure_methods"):
        if qty and qty > 0 and (unit or "").strip() in _DAYS:
            days.setdefault(row_id, []).append(round(qty * _DAYS[unit.strip()], 2))
    subj: dict[int, list[str]] = {}
    for row_id, name in conn.execute("SELECT row_id, TRIM(subject_name) FROM procedure_subjects WHERE TRIM(subject_name)<>''"):
        if name not in subj.setdefault(row_id, []):
            subj[row_id].append(name)
    n = 0
    for p in conn.execute("SELECT row_id, proc_id, name, domain, agency_levels, province, has_online_submission FROM procedures"
                          " WHERE status='active'").fetchall():
        row_id, pid, name, dom, lv, prov, online = p
        commune = int("Xã/Phường" in (lv or ""))
        vert = int(_vertical(dom))
        vnd = [r[4] for r in fees.get(pid, []) if r[1] == "numeric" and r[5] and r[4]]
        usd = any(r[3] == "USD" and r[5] for r in fees.get(pid, []) if r[1] == "numeric")
        free = int(any(_EXPLICIT_FREE.match(fold(r[2] or "").strip(" -.(")) and not _ONLY_FOR.search(fold(r[2] or ""))
                       for r in fees.get(pid, [])))
        d = days.get(row_id, [])
        conn.execute("INSERT OR REPLACE INTO proc_flat VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (pid, name, fold(name), dom or "", lv or "", prov, commune, int(prov is None), vert,
                      int(commune and prov is None and not vert), min(vnd) if vnd else None, max(vnd) if vnd else None,
                      "VND" if vnd else ("USD" if usd else ""), free, min(d) if d else None, max(d) if d else None,
                      int(bool(online)), "; ".join(subj.get(row_id, []))))
        n += 1
    return n


def report(conn, examples: int = 5) -> dict:
    """Kiểm bất biến của DB vừa dựng. Mỗi mục: số lượng + vài ví dụ (mã thủ tục)."""
    def q(sql, *a):
        return conn.execute(sql, a).fetchall()

    out = {"n_procedures": q("SELECT COUNT(*) FROM procedures WHERE status='active'")[0][0]}
    small = q("SELECT DISTINCT proc_id FROM fees_clean WHERE kind='numeric' AND amount_value>0 AND amount_value<1000 AND amount_ok=0"
              " AND currency<>'USD'")
    out["fee_small_unconfirmed"] = {"n": len(small), "examples": [r[0] for r in small[:examples]],
                                    "note": "số < 1.000 mà chữ không xác nhận: chỉ in nguyên văn chữ của Cổng"}
    cur = q("SELECT DISTINCT p.proc_id, f.currency_id FROM procedure_fees f JOIN procedures p ON p.row_id=f.row_id"
            " WHERE f.currency_id<>''")
    odd = [(a, b) for a, b in cur if b not in CURRENCY]
    usd = q("SELECT DISTINCT proc_id FROM fees_clean WHERE currency='USD'")
    out["fee_currency_unknown_id"] = {"n": len(odd), "examples": [a for a, _ in odd[:examples]]}
    out["fee_usd"] = {"n": len(usd), "examples": [r[0] for r in usd[:examples]]}
    bad = q("SELECT proc_id, portal_url FROM procedures WHERE status='active'")
    bad = [a for a, u in bad if not URL_OK.match(u or "")]
    out["portal_url_bad"] = {"n": len(bad), "examples": bad[:examples]}
    dup = q("SELECT proc_id, COUNT(*) FROM procedures WHERE status='active' GROUP BY proc_id HAVING COUNT(*)>1")
    out["duplicate_proc_id"] = {"n": len(dup), "examples": [r[0] for r in dup[:examples]]}
    empty = {}
    for col in ("name", "domain", "agency_levels", "source_id"):
        rows = q(f"SELECT proc_id FROM procedures WHERE status='active' AND TRIM(COALESCE({col},''))=''")
        empty[col] = {"n": len(rows), "examples": [r[0] for r in rows[:examples]]}
    out["empty_fields"] = empty
    out["in_scope"] = q("SELECT COUNT(*) FROM proc_flat WHERE in_scope=1")[0][0]
    out["provinces"] = q("SELECT COUNT(DISTINCT province) FROM procedures WHERE status='active' AND province IS NOT NULL")[0][0]
    return out

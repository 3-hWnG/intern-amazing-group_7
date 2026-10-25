"""Đếm / liệt kê thủ tục theo phí ("có bao nhiêu thủ tục giá 20k", "thủ tục nào phí dưới 50 nghìn", "thủ tục nào miễn phí").
Truy vấn SQL thật trên `fees_clean`, không nhờ tìm kiếm gần đúng. Chỉ tính thủ tục trong phạm vi hệ thống trả lời được
(cấp xã/phường, bản dùng chung toàn quốc, không thuộc ngành dọc).

Quy tắc dữ liệu (DATA_NOTES.md): nguồn không ghi phí thì KHÔNG suy ra miễn phí. "Miễn phí" chỉ tính khi nguồn viết rõ
("Không thu lệ phí…", "Miễn phí"); câu "Miễn lệ phí cho người có công…" là miễn theo đối tượng, đếm riêng.
Số tiền: dùng `amount_vnd` (đã sửa "20.000" đọc thành 20, bỏ dòng USD và số không đối chiếu được — chuẩn hoá lúc dựng, data/fees.py).
ponytail: một thủ tục có nhiều mức tính là khớp nếu ÍT NHẤT một mức thoả; chưa lọc theo hình thức nộp hay loại phí."""
from __future__ import annotations

import re

from system3.data import api as data_api
from system3.data.textutil import fold

_SUBJECT = re.compile(r"\bthu tuc\b")
_FEE = re.compile(r"\b(phi|le phi|gia|tien|muc thu|chi phi|ton kem)\b")
_CUE = re.compile(r"\b(bao nhieu|may|nao|liet ke|danh sach|nhung)\b")
_FREE = re.compile(r"\b(mien (le )?phi|khong (thu|mat|ton|phai (nop|dong)|can (nop|dong)) (le )?(phi|tien)|khong mat tien|khong ton tien)\b")
_LT = re.compile(r"\b(duoi|it hon|nho hon|khong qua|toi da|re hon|thap hon)\b")
_GT = re.compile(r"\b(tren|nhieu hon|lon hon|cao hon|toi thieu|dat hon|dat hon)\b|\btro len\b")
_MONEY = r"(\d+(?:[.,]\d+)*)\s*(k|nghin|ngan|tr|trieu|ty)?\b"
_RANGE = re.compile(r"\btu\s+" + _MONEY + r"\s*(?:d|dong|vnd)?\s*(?:den|toi|-)\s*" + _MONEY)
_ONE = re.compile(_MONEY)
_UNIT = {"k": 1e3, "nghin": 1e3, "ngan": 1e3, "tr": 1e6, "trieu": 1e6, "ty": 1e9}


def _vnd(num: str, unit: str | None) -> int | None:
    """"20" + "k" -> 20000; "20.000" -> 20000; "1,5" + "triệu" -> 1500000; số trần dưới 1000 (không đơn vị) -> None (mơ hồ)."""
    if unit:
        v = float(num.replace(",", ".")) if re.fullmatch(r"\d+[.,]\d{1,2}", num) else float(re.sub(r"[.,]", "", num))
        return int(round(v * _UNIT[unit]))
    v = int(re.sub(r"[.,]", "", num)) if re.fullmatch(r"\d{1,3}([.,]\d{3})+|\d+", num) else None
    return v if v is not None and v >= 1000 else None


def parse(text: str) -> dict | None:
    """-> {"op": eq|lt|gt|between|free, "lo", "hi"} nếu là câu đếm/liệt kê thủ tục theo phí, ngược lại None."""
    f = fold(text)
    if not (_SUBJECT.search(f) and _CUE.search(f)):
        return None
    if _FREE.search(f):
        return {"op": "free"}
    if not _FEE.search(f):
        return None
    m = _RANGE.search(f)
    if m:
        a, b = _vnd(m.group(1), m.group(2)), _vnd(m.group(3), m.group(4) or m.group(2))
        if a and b:
            return {"op": "between", "lo": min(a, b), "hi": max(a, b)}
    vals = [v for v in (_vnd(n, u) for n, u in _ONE.findall(f)) if v]
    if not vals:
        return None
    v = vals[0]
    return {"op": "lt" if _LT.search(f) else "gt" if _GT.search(f) else "eq", "lo": v}


def _levels(rows: list[dict]) -> set[int]:
    """Các mức phí (đồng) của một thủ tục: amount_vnd đã chuẩn hoá lúc dựng (data/fees.py). DB cũ chưa có cột thì chuẩn hoá tại chỗ."""
    from system3.data import fees as F
    out = set()
    for r in rows:
        if r["kind"] != "numeric" or not r["amount_value"]:
            continue
        n = r if "amount_ok" in r else F.normalize(r["amount_value"], r["amount_text"], None)
        if n["amount_ok"] and n["amount_vnd"]:
            out.add(int(n["amount_vnd"]))
    return out


_EXPLICIT = re.compile(r"^(khong thu|mien (le )?phi|khong co|khong mat|khong phai)")
_ONLY_FOR = re.compile(r"\b(cho nguoi|nguoi thuoc|truong hop|dien|doi tuong|doi voi tre|ngoai tru)\b")


def _free_kind(rows: list[dict]) -> str:
    """"explicit": nguồn ghi rõ không thu phí; "partial": miễn theo đối tượng; "": không nói gì (không suy ra)."""
    kind = ""
    for r in rows:
        t = fold(r["amount_text"] or "").strip(" -.(")
        if not t:
            continue
        if _EXPLICIT.match(t) and not _ONLY_FOR.search(t):
            return "explicit"
        if re.search(r"\bmien\b", t):
            kind = "partial"
    return kind


def _scope(conn) -> list[tuple[str, str]]:
    from policy.policy import _vertical
    return [(r["proc_id"], r["name"]) for r in conn.execute(
        "SELECT proc_id, name, domain FROM procedures WHERE province IS NULL AND agency_levels LIKE '%Xã/Phường%' ORDER BY name")
        if not _vertical(r["domain"])]


def _short(name: str, n: int = 110) -> str:
    return name if len(name) <= n else name[:n].rstrip(" ,;") + "…"


def _money(v: int) -> str:
    return f"{v:,}".replace(",", ".") + "đ"


def run(conn, q: dict, show: int = 10) -> str:
    procs = _scope(conn)
    rows: dict[str, list[dict]] = {p: [] for p, _ in procs}
    for r in conn.execute("SELECT * FROM fees_clean"):
        if r["proc_id"] in rows:
            rows[r["proc_id"]].append(dict(r))
    names = dict(procs)
    n = len(procs)
    if q["op"] == "free":
        exp = [p for p in rows if _free_kind(rows[p]) == "explicit"]
        part = [p for p in rows if _free_kind(rows[p]) == "partial" and not _levels(rows[p])]
        out = [f"Trong {n} thủ tục cấp xã/phường mình có dữ liệu, nguồn ghi rõ **không thu phí / miễn phí** ở {len(exp)} thủ tục"
               + (":" if exp else ".")]
        out += [f"{i}. {_short(names[p])}" for i, p in enumerate(exp[:show], 1)]
        if len(exp) > show:
            out.append(f"… và {len(exp) - show} thủ tục khác.")
        out.append(f"Có thêm {len(part)} thủ tục chỉ miễn phí cho một số đối tượng (người có công, hộ nghèo…), không phải mọi người.")
        out.append("Phần còn lại nguồn không ghi mức phí nên mình không kết luận là miễn phí. Bạn hỏi tên thủ tục để xem chi tiết.")
        return "\n".join(out)
    lo, hi = q["lo"], q.get("hi")
    ok = {"eq": lambda x: x == lo, "lt": lambda x: x < lo, "gt": lambda x: x > lo, "between": lambda x: lo <= x <= hi}[q["op"]]
    what = {"eq": f"có mức phí {_money(lo)}", "lt": f"có mức phí dưới {_money(lo)}", "gt": f"có mức phí trên {_money(lo)}",
            "between": f"có mức phí từ {_money(lo)} đến {_money(hi or 0)}"}[q["op"]]
    hit = [(p, sorted(_levels(rows[p]))) for p in rows if any(ok(x) for x in _levels(rows[p]))]
    unknown = sum(1 for p in rows if not _levels(rows[p]))
    out = [f"Trong {n} thủ tục cấp xã/phường mình có dữ liệu, có **{len(hit)}** thủ tục {what}" + (":" if hit else ".")]
    for i, (p, lv) in enumerate(hit[:show], 1):
        out.append(f"{i}. {_short(names[p])}" + (f" (các mức: {', '.join(_money(x) for x in lv)})" if len(lv) > 1 else ""))
    if len(hit) > show:
        out.append(f"… và {len(hit) - show} thủ tục khác.")
    if any(len(lv) > 1 for _, lv in hit):
        out.append("Thủ tục có nhiều mức phí được tính nếu có ít nhất một mức khớp.")
    out.append(f"Lưu ý: {unknown} thủ tục không có số tiền cụ thể trong dữ liệu (mức do địa phương quyết định, hoặc nguồn không ghi) nên không tính ở đây. "
               "Bạn hỏi tên thủ tục để xem chi tiết.")
    return "\n".join(out)


def answer(text: str) -> str | None:
    """Câu trả lời cho câu hỏi đếm/liệt kê theo phí, hoặc None nếu không phải loại câu này."""
    q = parse(text)
    return run(data_api.connect(), q) if q else None

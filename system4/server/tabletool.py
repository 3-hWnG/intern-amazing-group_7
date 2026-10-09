"""NV5 (A4): công cụ bảng — đếm / cộng / trung bình / lớn nhất / nhỏ nhất / liệt kê trên TOÀN BỘ bảng.

Chế độ Chuyên gia bình thường chỉ gửi cho AI vài đoạn tìm được, nên "Lớp có bao nhiêu bạn nữ?" không trả lời được.
Ở đây: code thấy từ kiểu đếm / liệt kê -> AI (JSON, ~1 giây) đổi câu hỏi thành phép lọc trên tên trường thật
(vd. trường "Nữ" có giá trị -> đếm) -> code tính trên mọi dòng -> kết quả thành đoạn dữ liệu [1] để AI diễn đạt.
AI thấy câu hỏi chỉ về một đối tượng (vd. "lệ phí thủ tục X bao nhiêu?") thì trả use_table = false -> đi đường cũ.
"""
from __future__ import annotations
import json
import re

from . import db, llm
from .ground import fold

_TRIGGER = re.compile(r"\b(bao nhieu|may|tong|dem|liet ke|tat ca|danh sach|nhung ai|nhung ban|nhung nguoi|nhung muc|ai co|"
                      r"nhieu nhat|it nhat|lon nhat|nho nhat|cao nhat|thap nhat|trung binh|sap xep|how many|list|count|total|average)\b")
OPS = ["count", "list", "sum", "avg", "min", "max"]
FILTER_OPS = ["eq", "contains", "empty", "not_empty", "gt", "lt", "year"]
SCHEMA = {"type": "object", "properties": {
    "use_table": {"type": "boolean"},
    "table": {"type": "integer"},
    "op": {"type": "string", "enum": OPS},
    "field": {"type": "string"},
    "filters": {"type": "array", "maxItems": 4, "items": {"type": "object", "properties": {
        "field": {"type": "string"}, "op": {"type": "string", "enum": FILTER_OPS}, "value": {"type": "string"}},
        "required": ["field", "op", "value"]}}},
    "required": ["use_table", "table", "op", "field", "filters"]}
LIST_MAX = 40
_cache: dict[tuple, list] = {}


def triggered(text: str) -> bool:
    return bool(_TRIGGER.search(fold(text)))


def tables(dataset_ids: list[int]) -> list[dict]:
    """Các bảng đang bật: tên, trường (kèm vài giá trị mẫu), mọi dòng (trường + tiêu đề). Lưu đệm theo bộ dữ liệu."""
    out = []
    for ds_id in dataset_ids:
        ds = db.get_dataset(ds_id)
        if not ds:
            continue
        key = (ds_id, ds["n_records"], len(ds.get("mapping") or ""))
        if key not in _cache:
            try:
                parts = json.loads(ds.get("mapping") or "{}").get("parts", [])
            except ValueError:
                parts = []
            title_col = {p.get("sheet"): p.get("title_column") for p in parts if p.get("kind") == "table"}
            groups: dict[str, list] = {}
            for r in db.run("SELECT id, title, fields, source FROM records WHERE dataset_id=? AND fields != '{}' ORDER BY id",
                            (ds_id,), many=True):
                groups.setdefault(r["source"].rsplit(" · dòng", 1)[0], []).append(r)
            tabs = []
            for src, rows in groups.items():
                sheet = src.split(" · ", 1)[1] if " · " in src else src
                label = title_col.get(sheet) or "Tiêu đề"
                recs = []
                for r in rows:
                    f = json.loads(r["fields"] or "{}")
                    recs.append({"id": r["id"], "title": r["title"], "fields": {label: r["title"], **f} if label not in f else f})
                if len(recs) >= 2:
                    tabs.append({"name": f"{ds['name']} · {sheet}", "dataset": ds["name"], "title_label": label, "rows": recs})
            _cache[key] = tabs
        out += _cache[key]
    return out


def _fields(tab: dict) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for r in tab["rows"]:
        for k, v in r["fields"].items():
            vals = seen.setdefault(k, [])
            if v and v not in vals and len(vals) < 4:
                vals.append(str(v)[:30])
    return seen


def plan(question: str, tabs: list[dict]) -> dict:
    desc = []
    for i, t in enumerate(tabs):
        fs = "; ".join(f"\"{k}\" (vd: {', '.join(v) or 'trống'})" for k, v in _fields(t).items())
        desc.append(f"Bảng {i}: {t['name']} — {len(t['rows'])} dòng. Trường: {fs}")
    system = ("Bạn chuyển câu hỏi của người dùng thành MỘT phép tính trên bảng dữ liệu. "
              "use_table = true CHỈ khi câu hỏi cần xét CẢ bảng: đếm, cộng, trung bình, lớn nhất / nhỏ nhất, hoặc liệt kê các dòng thỏa điều kiện. "
              "Câu hỏi về MỘT đối tượng cụ thể (vd. lệ phí của một thủ tục, mẹ của một bạn) -> use_table = false.\n"
              "op: count (đếm) | list (liệt kê) | sum | avg | min | max (trên trường \"field\", là trường số). "
              "filters: mỗi điều kiện {field, op, value}; op: eq (bằng), contains (chứa chữ), empty (trống), not_empty (có giá trị, vd. cột đánh dấu x), "
              "gt / lt (lớn hơn / nhỏ hơn, so số), year (năm của trường ngày bằng value). Chỉ dùng tên trường đúng như danh sách. "
              "Không có điều kiện thì filters rỗng. Ví dụ: \"Có bao nhiêu bạn nữ?\" với trường \"Nữ\" (vd: x) -> op count, filters "
              "[{field: \"Nữ\", op: not_empty, value: \"\"}].")
    return llm.chat_json([{"role": "system", "content": system},
                          {"role": "user", "content": "\n".join(desc) + f"\n\nCâu hỏi: {question}"}], SCHEMA, timeout=30)


def _num(v) -> float | None:
    m = re.search(r"-?\d+(?:[.,]\d+)*", str(v or ""))
    if not m:
        return None
    s = m.group()
    if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    elif re.fullmatch(r"-?\d{1,3}(?:,\d{3})+", s):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _year(v) -> str | None:
    m = re.search(r"\b(19|20)\d{2}\b", str(v or ""))
    return m.group() if m else None


def _match(row: dict, f: dict) -> bool:
    v, target, op = row["fields"].get(f["field"], ""), f.get("value", ""), f.get("op")
    if op == "empty":
        return not str(v).strip()
    if op == "not_empty":
        return bool(str(v).strip())
    if op == "eq":
        return fold(str(v)).strip() == fold(target).strip()
    if op == "contains":
        return fold(target).strip() in fold(str(v))
    if op == "year":
        return _year(v) == (_year(target) or target.strip())
    a, b = _num(v), _num(target)
    if a is None or b is None:
        return False
    return a > b if op == "gt" else a < b


def execute(spec: dict, tab: dict) -> dict:
    fields = _fields(tab)
    filters = [f for f in spec.get("filters") or [] if f.get("field") in fields and f.get("op") in FILTER_OPS]
    rows = [r for r in tab["rows"] if all(_match(r, f) for f in filters)]
    op, field = spec.get("op") if spec.get("op") in OPS else "count", spec.get("field")
    res = {"op": op, "matched": len(rows), "total": len(tab["rows"]), "filters": filters, "rows": rows}
    if op in ("sum", "avg", "min", "max") and field in fields:
        nums = [(n, r) for r in rows if (n := _num(r["fields"].get(field))) is not None]
        res["field"], res["numeric_rows"] = field, len(nums)
        if nums:
            vals = [n for n, _ in nums]
            if op == "sum":
                res["value"] = sum(vals)
            elif op == "avg":
                res["value"] = sum(vals) / len(vals)
            else:
                best = min(vals) if op == "min" else max(vals)
                res["value"] = best
                res["rows"] = [r for n, r in nums if n == best]
    return res


def _fmt(x: float) -> str:
    return f"{x:,.2f}".rstrip("0").rstrip(".").replace(",", "X").replace(".", ",").replace("X", ".")


_OP_WORD = {"count": "Đếm", "list": "Liệt kê", "sum": "Tổng", "avg": "Trung bình", "min": "Nhỏ nhất", "max": "Lớn nhất"}
_F_WORD = {"eq": "bằng", "contains": "chứa", "empty": "trống", "not_empty": "có giá trị", "gt": "lớn hơn", "lt": "nhỏ hơn", "year": "năm"}


def evidence_text(res: dict, tab: dict) -> str:
    cond = "; ".join(f"{f['field']} {_F_WORD[f['op']]}" + (f" \"{f['value']}\"" if f['op'] not in ('empty', 'not_empty') else "")
                     for f in res["filters"]) or "tất cả các dòng"
    lines = [f"Kết quả do code tính trên TOÀN BỘ {res['total']} dòng của bảng \"{tab['name']}\" (chính xác, dùng được ngay).",
             f"Phép tính: {_OP_WORD[res['op']]}. Điều kiện: {cond}.",
             f"Số dòng thỏa điều kiện: {res['matched']}."]
    if "value" in res:
        lines.append(f"{_OP_WORD[res['op']]} của trường \"{res['field']}\" (trên {res['numeric_rows']} dòng có số): {_fmt(res['value'])}.")
    rows = res["rows"]
    if rows:
        shown = rows[:LIST_MAX]
        lines.append(f"Danh sách {tab['title_label']} ({len(shown)}/{len(rows)}): " + "; ".join(r["title"] for r in shown)
                     + ("; …" if len(rows) > len(shown) else ""))
    return "\n".join(lines)


def run(question: str, dataset_ids: list[int]) -> dict | None:
    """Trả {"evidence": đoạn dữ liệu [1] hoặc None, "info": chi tiết cho 🔍} hoặc None nếu không có bảng."""
    tabs = tables(dataset_ids)
    if not tabs:
        return None
    spec = plan(question, tabs)
    info = {"spec": spec, "tables": [t["name"] for t in tabs]}
    if not spec.get("use_table"):
        return {"evidence": None, "info": info}
    i = spec.get("table") if isinstance(spec.get("table"), int) and 0 <= spec.get("table") < len(tabs) else 0
    tab = tabs[i]
    res = execute(spec, tab)
    info.update(table=tab["name"], matched=res["matched"], total=res["total"], value=res.get("value"), filters=res["filters"])
    ev = {"id": None, "title": f"Tính trên cả bảng: {tab['name']}", "dataset": tab["dataset"], "text": evidence_text(res, tab),
          "score": None, "full": True, "record_ids": [r["id"] for r in res["rows"][:LIST_MAX]]}
    return {"evidence": ev, "info": info}

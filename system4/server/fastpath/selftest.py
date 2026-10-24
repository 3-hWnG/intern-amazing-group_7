"""Bài tự kiểm lúc biên dịch: code sinh câu hỏi + đáp án từ CHÍNH dữ liệu, chạy engine, bật / tắt từng loại câu cho từng bảng.

Loại câu (route) và câu sinh ra:
  field     "<tên trường> của <tiêu đề dòng> là gì?" (mẫu tối đa SAMPLE dòng × mọi trường có giá trị) + câu gợi ý của AI nếu có;
            đạt = trả đúng dòng (nguồn) + đúng trường. Thêm câu hỏi về một tên KHÔNG có ("Nguyễn Văn Không Tồn Tại"): đạt = không trả lời.
  aggregate "Có bao nhiêu <danh từ> <tên cột đánh dấu>?" và "... có <tên trường> là <giá trị>?" (cột enum); đạt = đúng con số
            (so bằng nguyên giá trị ô, nên cột mà "chứa chữ" khác "bằng" sẽ bị bắt).
  text      "<tiêu đề đoạn>?" ; đạt = trích đúng đoạn đó.
Loại câu đạt dưới ⚙ FASTPATH_MIN_PASS (và có ít nhất MIN_N câu) thì tắt cho bảng ấy: câu hỏi loại đó đi đường cũ (tìm kiếm + AI).
Giới hạn (ghi rõ để không hiểu nhầm): câu sinh ra dùng chính tên trường / gợi ý, nên bài này bắt lỗi CẤU TRÚC (tiêu đề trùng, tiêu đề lẫn
chữ của trường, cột lọc sai, đoạn văn tiêu đề chung chung), không đo được cách người thật hỏi.
"""
from __future__ import annotations

import re

from ..ground import fold
from .compile import words
from .engine import Engine

SAMPLE = 12
MIN_N = 3
GHOST = "Nguyễn Văn Không Tồn Tại"


def _sample(rows: list, n: int) -> list:
    if len(rows) <= n:
        return list(rows)
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def _q_field(t: dict) -> list[dict]:
    out = []
    # cột không có gợi ý nào (vd. "Tên" bị bỏ vì quá chung) không tra bằng loại câu này; cột đánh dấu x thuộc loại câu đếm
    fields = [(f, m) for f, m in t["fields"].items() if m["type"] not in ("empty", "flag") and m["cues"]]
    for r in _sample(t["rows"], SAMPLE):
        for f, m in fields:
            if not r["fields"].get(f):
                continue
            # tên cột bị vet_cues bỏ (vd. "địa điểm" nằm trong 7% tên di tích) thì engine cố ý không nhận nó: đừng hỏi bằng nó (19/10)
            if any(" ".join(fold(w) for w in c) == " ".join(fold(m["label"]).split()) for c in m["cues"]):
                out.append({"q": f"{m['label']} của {r['title']} là gì?", "row": r["id"], "field": f})
            alt = next((c for c in m["cues"] if c not in m.get("header", []) and " ".join(c) != fold(m["label"])), None)
            if alt:
                out.append({"q": f"{r['title']} {' '.join(alt)}?", "row": r["id"], "field": f})
    if fields:
        out.append({"q": f"{fields[0][1]['label']} của {GHOST} là gì?", "row": None, "field": None, "negative": True})
    return out


def _q_aggregate(t: dict) -> list[dict]:
    out, noun = [], t.get("entity_noun") or "dòng"
    rows = t["rows"]
    for f, m in t["fields"].items():
        vals = [str(r["fields"].get(f) or "") for r in rows]
        if m["type"] == "flag":
            out.append({"q": f"Có bao nhiêu {noun} có {m['label']}?", "count": sum(bool(v) for v in vals)})
        elif m["type"] == "enum" and not m.get("long"):
            norm = [" ".join(words(v)) for v in vals]   # so theo chữ đã chuẩn hoá: "Ấp Tân Hòa  - ĐT" = "Ấp Tân Hòa -DT"
            common = sorted({v for v in norm if v}, key=lambda v: -norm.count(v))[:2]
            for v in common:
                shown = next(x for x, n in zip(vals, norm) if n == v)
                out.append({"q": f"Có bao nhiêu {noun} có {m['label']} là {shown}?", "count": norm.count(v)})
                # dạng câu bỏ sót lần đầu (lỗi 18/10): liệt kê theo giá trị, và "bao nhiêu <danh từ> ở <giá trị>" không nêu tên trường
                out.append({"q": f"Liệt kê các {noun} có {m['label']} là {shown}", "count": norm.count(v)})
                out.append({"q": f"Có bao nhiêu {noun} ở {shown}?", "count": norm.count(v)})
    return out


def _q_sql(t: dict) -> list[dict]:
    """24/10 (lộ trình SQL): câu sinh từ KIỂU cột của chính bảng, đáp án tính bằng Python trên dữ liệu (không qua SQL):
    đếm theo một giá trị cột liệt kê, liệt kê 2-8 dòng theo giá trị đó, lớn nhất / nhỏ nhất của cột số, đếm vượt ngưỡng, tổng theo giá trị."""
    from . import sqlroute
    out, noun, rows = [], t.get("entity_noun") or "dòng", t["rows"]
    if len(rows) < 2:
        return out
    box = sqlroute.Box(t)
    enums = [c for c in box.cols if c["kind"] == "text" and 2 <= len(c["values"]) <= 15]
    nums = [c for c in box.cols if c["kind"] == "num"]
    cell = lambda r, c: str(r["fields"].get(c["field"]) or "")
    for c in enums[:2]:
        groups = sorted(c["values"], key=lambda v: -sum(cell(r, c) == v for r in rows))
        v = groups[0]
        hit = [r["title"] for r in rows if cell(r, c) == v]
        out.append({"q": f"Có bao nhiêu {noun} có {c['label']} là {v}?", "count": len(hit)})
        small = next((g for g in groups if 2 <= sum(cell(r, c) == g for r in rows) <= 8), None)
        if small:
            out.append({"q": f"Kể tên các {noun} có {c['label']} là {small}.", "titles": {r["title"] for r in rows if cell(r, c) == small}})
    for c in nums[:2]:
        vals = [(sqlroute.to_number(cell(r, c), c["style"]), r["title"]) for r in rows]
        vals = [(x, ti) for x, ti in vals if isinstance(x, (int, float))]
        if len(vals) < 3:
            continue
        top = max(vals)[1]
        if sum(1 for x, _ in vals if x == max(vals)[0]) == 1:
            out.append({"q": f"{noun.capitalize()} nào có {c['label']} cao nhất?", "titles": {top}})
        mid = sorted(x for x, _ in vals)[len(vals) // 2]
        out.append({"q": f"Có bao nhiêu {noun} có {c['label']} lớn hơn {sqlroute.fmt(mid)}?", "count": sum(1 for x, _ in vals if x > mid)})
        if enums:
            e = enums[0]
            g = sorted(e["values"], key=lambda v: -sum(cell(r, e) == v for r in rows))[0]
            tot = sum(x for x, ti in vals if any(r["title"] == ti and cell(r, e) == g for r in rows))
            out.append({"q": f"Tổng {c['label']} của các {noun} có {e['label']} là {g} là bao nhiêu?", "value": tot})
    return out


def _sql_good(c: dict, a: dict, t: dict) -> bool:
    if a.get("kind") != "answer" or a.get("route") != "sql" or a.get("table") != t["key"]:
        return False
    if "count" in c:
        return a.get("count") == c["count"] or re.search(rf"\*\*{c['count']}\*\*", a.get("content", "")) is not None
    if "titles" in c:
        return set(a.get("titles") or []) == c["titles"]
    v = a.get("value")
    return isinstance(v, (int, float)) and abs(v - c["value"]) <= 1e-6 * max(1.0, abs(c["value"]))


def run(tables: list[dict], texts: list[dict], min_pass: float, sql=None) -> dict:
    """Trả {"enabled": {table_key: {"field": bool, "aggregate": bool, "sql": bool}, "text:<ds>": bool}, "tables": {...chi tiết...}}.
    sql = hàm gọi model (24/10): có thì chấm thêm lộ trình SQL; không có thì không có route "sql" (tắt)."""
    eng = Engine(tables, texts, {})                                   # lộ trình cũ chấm riêng: SQL không chen vào câu đếm của code
    eng_sql = Engine(tables, texts, {t["key"]: {"sql": True} for t in tables}, sql=sql) if sql else None
    enabled, detail = {}, {}
    for t in eng.ents:
        res = {}
        routes = [("field", _q_field(t)), ("aggregate", _q_aggregate(t) if len(t["rows"]) >= 2 else [])]
        if sql:
            routes.append(("sql", _q_sql(t)))
        for route, qs in routes:
            ok, fails = 0, []
            for c in qs:
                a = (eng_sql if route == "sql" else eng).answer(c["q"], {})
                if route == "field":
                    if c.get("negative"):
                        good = a["kind"] != "answer"
                    else:
                        good = a["kind"] == "answer" and a.get("field") == c["field"] and any(s["record_id"] == c["row"] for s in a.get("sources", []))
                elif route == "sql":
                    good = _sql_good(c, a, t)
                else:   # đúng bảng, đúng số dòng (dạng đếm: **n**; dạng liệt kê giá trị: n dòng "- ")
                    good = a["kind"] == "answer" and a.get("table") == t["key"] and (
                        (a.get("route") == "aggregate" and re.search(rf"\*\*{c['count']}\*\*", a["content"]) is not None)
                        or (a.get("route") == "lookup" and a["content"].count("\n- ") == c["count"]))
                ok += good
                if not good and len(fails) < 5:
                    fails.append({"q": c["q"], "got": (a.get("content") or a.get("reason") or "")[:160]})
            n = len(qs)
            rate = ok / n if n else None
            res[route] = {"n": n, "pass": ok, "rate": None if rate is None else round(rate, 3), "fails": fails,
                          "on": n < MIN_N or rate >= min_pass}
        enabled[t["key"]] = {k: v["on"] for k, v in res.items()}
        detail[t["key"]] = res
    by_ds: dict = {}
    for x in eng.texts:
        by_ds.setdefault(x["dataset_id"], []).append(x)
    for ds_id, xs in by_ds.items():
        ok, fails = 0, []
        for x in xs[:SAMPLE]:
            a = eng.answer(f"{x['title']}?", {})
            good = a["kind"] == "answer" and a.get("route") == "text" and any(s["record_id"] == x["id"] for s in a.get("sources", []))
            ok += good
            if not good and len(fails) < 5:
                fails.append({"q": f"{x['title']}?", "got": (a.get("content") or a.get("reason") or "")[:160]})
        n = min(len(xs), SAMPLE)
        enabled[f"text:{ds_id}"] = n < MIN_N or ok / n >= min_pass
        detail[f"text:{ds_id}"] = {"text": {"n": n, "pass": ok, "rate": round(ok / n, 3) if n else None, "fails": fails,
                                            "on": enabled[f"text:{ds_id}"]}}
    return {"enabled": enabled, "tables": detail}

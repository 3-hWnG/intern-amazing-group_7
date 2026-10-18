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
    return out


def run(tables: list[dict], texts: list[dict], min_pass: float) -> dict:
    """Trả {"enabled": {table_key: {"field": bool, "aggregate": bool}, "text:<ds>": bool}, "tables": {...chi tiết...}}."""
    eng = Engine(tables, texts, {})
    enabled, detail = {}, {}
    for t in eng.ents:
        res = {}
        for route, qs in (("field", _q_field(t)), ("aggregate", _q_aggregate(t) if len(t["rows"]) >= 2 else [])):
            ok, fails = 0, []
            for c in qs:
                a = eng.answer(c["q"], {})
                if route == "field":
                    if c.get("negative"):
                        good = a["kind"] != "answer"
                    else:
                        good = a["kind"] == "answer" and a.get("field") == c["field"] and any(s["record_id"] == c["row"] for s in a.get("sources", []))
                else:
                    good = a["kind"] == "answer" and a.get("route") == "aggregate" and a.get("table") == t["key"] and \
                        re.search(rf"\*\*{c['count']}\*\*|Không có ", a["content"]) is not None and (c["count"] > 0 or "Không có " in a["content"])
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

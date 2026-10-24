"""Thử lộ trình SQL của đường nhanh (fastpath/sqlroute.py) trên dữ liệu DEV — KHÔNG dùng bộ mù real_v3.

    python system4/eval/real_v3/sql_dev.py [--raw] [-v]      # --raw: mốc "SQL không qua bước biên dịch"

Dữ liệu dev: 3 bảng Wikipedia đã dùng từ 19/10 (system4/eval/real_domains/data: bệnh viện TP.HCM, trường đại học, di tích quốc gia đặc biệt).
Engine dựng thẳng từ tệp (kiểu cột của compile.py, gợi ý chỉ từ tên cột), model thật qua Ollama (qwen3:4b-instruct, nhiệt độ 0), có canh nhiệt.
Đáp án tính bằng Python trên dữ liệu. Câu dev viết 24/10 khi sửa lộ trình SQL (xem được kết quả, dùng để sửa).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path[:0] = [str(REPO.parent / "pyroot_merge"), str(REPO / "server"), str(REPO / "eval")]
os.environ.setdefault("S4_RUNTIME_DIR", str(Path(os.environ.get("TMP", ".")) / "s4_sqldev"))
from system3.system4.server.fastpath import sqlroute  # noqa: E402
from system3.system4.server.fastpath.compile import header_cues, infer_type  # noqa: E402
from system3.system4.server.fastpath.engine import Engine  # noqa: E402
from system3.system4.server.ground import fold  # noqa: E402
from thermal import guard, low_priority  # noqa: E402

DEV = REPO / "system4" / "eval" / "real_domains" / "data"
MODEL = os.environ.get("SQLDEV_MODEL", "qwen3:4b-instruct-2507-q4_K_M")


def load(fname: str, noun: str) -> dict:
    ws = openpyxl.load_workbook(DEV / fname, read_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True)
    head = [str(h) for h in next(it)]
    rows = [{"id": k, "title": str(r[0]), "fields": {h: ("" if v is None else str(v)) for h, v in zip(head[1:], r[1:])}}
            for k, r in enumerate(it) if r[0]]
    fields = {h: {"type": infer_type(h, [x["fields"][h] for x in rows], len(rows)), "label": h, "long": False} for h in head[1:]}
    hc = header_cues(head[1:])
    for h, m in fields.items():
        m["cues"], m["header"], m["absent"] = list(hc[h]), list(hc[h]), []
    return {"key": fname, "dataset_id": 0, "dataset": fname, "name": ws.title, "title_label": head[0], "file": fname, "rows": rows,
            "fields": fields, "parent": None, "children": [], "entity_noun": noun}


def chat(messages, schema, timeout=60):
    import ollama
    r = ollama.Client(timeout=timeout).chat(model=MODEL, messages=messages, format=schema, think=False, keep_alive="10m",
                                            options={"temperature": 0, "num_ctx": 8192})
    try:
        return json.loads(r["message"]["content"] or "{}")
    except ValueError:
        return {}


def gold(t: dict, kind: str, pred, col: str | None = None):
    rows = [r for r in t["rows"] if pred(r)]
    style = sqlroute.number_style([r["fields"].get(col, "") for r in t["rows"]]) if col else "dot"      # 24/10: trước đây cố định "dot" -> "1.800" thành 1,8
    num = lambda r: sqlroute.to_number(r["fields"].get(col, ""), style) if col else None
    if kind == "count":
        return {"count": len(rows)}
    if kind == "titles":
        return {"titles": {r["title"] for r in rows}}
    if kind in ("max", "min"):
        vs = [(num(r), r["title"]) for r in rows if isinstance(num(r), (int, float))]
        return {"titles": {(max if kind == "max" else min)(vs)[1]}}
    if kind == "sum":
        return {"value": sum(v for v in (num(r) for r in rows) if isinstance(v, (int, float)))}


def has(r, col, s):
    return fold(s) in fold(r["fields"].get(col, ""))


def main():
    low_priority()
    raw = "--raw" in sys.argv
    bv = load("y_te_benh_vien_tphcm.xlsx", "bệnh viện")
    dh = load("giao_duc_truong_dai_hoc.xlsx", "trường")
    dt = load("du_lich_di_tich_dac_biet.xlsx", "di tích")
    yr = lambda r, c: int(m.group()) if (m := re.search(r"\d{4}", r["fields"].get(c, ""))) else None
    Q = [   # (bảng, câu, loại đáp án, điều kiện, cột số)
        (bv, "Có bao nhiêu bệnh viện tư nhân?", "count", lambda r: has(r, "Nhóm", "Tư nhân"), None),
        (bv, "Bệnh viện nào có nhiều giường nhất?", "max", lambda r: True, "Số giường"),
        (bv, "Liệt kê các bệnh viện thành lập trước năm 1900.", "titles", lambda r: (yr(r, "Năm thành lập") or 9999) < 1900, None),
        (bv, "Tổng số giường của các bệnh viện tư nhân là bao nhiêu?", "sum", lambda r: has(r, "Nhóm", "Tư nhân"), "Số giường"),
        (bv, "Có mấy bệnh viện có trên 1000 giường?", "count", lambda r: (sqlroute.to_number(r["fields"].get("Số giường", ""), "vi") or 0) > 1000, None),
        (bv, "Bệnh viện nào được thành lập sớm nhất?", "min", lambda r: True, "Năm thành lập"),
        (bv, "co bao nhieu benh vien nhi", "count", lambda r: "nhi" in fold(r["title"]).split() or "nhi dong" in fold(r["title"]), None),
        (dh, "Có bao nhiêu trường đại học tư thục?", "count", lambda r: has(r, "Loại hình", "Tư thục"), None),
        (dh, "Có bao nhiêu trường thuộc Đại học Quốc gia Hà Nội?", "count", lambda r: has(r, "Thuộc đại học", "Đại học Quốc gia Hà Nội"), None),
        (dh, "Kể tên các trường thuộc Đại học Huế.", "titles", lambda r: has(r, "Thuộc đại học", "Đại học Huế"), None),
        (dh, "Có bao nhiêu trường do Bộ Công an quản lý?", "count", lambda r: has(r, "Cơ quan chủ quản", "Bộ Công an"), None),
        (dt, "Có bao nhiêu di tích được xếp hạng năm 2012?", "count", lambda r: r["fields"].get("Năm xếp hạng", "").strip() == "2012", None),
        (dt, "Liệt kê các di tích ở Ninh Bình.", "titles", lambda r: has(r, "Địa điểm", "Ninh Bình"), None),
        (dt, "Có bao nhiêu di tích được UNESCO công nhận?", "count", lambda r: has(r, "Ghi chú", "UNESCO công nhận"), None),   # 24/10: 4 dòng "dự kiến đề cử ... UNESCO" chưa được công nhận
        (dt, "Những di tích nào được xếp hạng trong đợt 5?", "titles", lambda r: r["fields"].get("Đợt xếp hạng", "").strip() == "Đợt 5", None),
        (dt, "Có bao nhiêu di tích khảo cổ?", "count", lambda r: has(r, "Hạng mục", "khảo cổ"), None),
    ]
    tables = [bv, dh, dt]
    eng = Engine(tables, [], {t["key"]: {"sql": True} for t in tables}, aggregate=False, sql=chat, sql_compiled=not raw)
    ok, t0 = 0, time.time()
    for t, q, kind, pred, col in Q:
        guard(every=0, label=q[:30])
        g = gold(t, kind, pred, col)
        a = eng.answer(q, {})
        good = a.get("route") == "sql" and (
            (("count" in g) and a.get("count") == g["count"]) or (("titles" in g) and set(a.get("titles") or []) == g["titles"])
            or (("value" in g) and isinstance(a.get("value"), (int, float)) and abs(a["value"] - g["value"]) < 1e-6 * max(1, abs(g["value"]))))
        ok += good
        if "-v" in sys.argv or not good:
            print(f"{'PASS' if good else 'FAIL'} [{t['name'][:10]}] {q}\n     sql={a.get('sql')!r}\n     -> {str(a.get('content') or a.get('reason'))[:160]!r}"
                  f"\n     gold={str(g)[:160]}")
        time.sleep(1.0)
    print(f"== {'raw' if raw else 'compiled'}: {ok}/{len(Q)} đúng ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()

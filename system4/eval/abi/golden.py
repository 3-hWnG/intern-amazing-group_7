"""Bộ đánh giá lĩnh vực ABI (abi.com.vn) — docs/PLAN_ABI_LINH_VUC.md mục 5.

Câu hỏi vàng do CODE sinh từ PHIÊN BẢN dữ liệu đang dùng (runtime/abi/versions/<id>/data.json), nên đáp án tự đúng theo web.
Mỗi câu có "expect": các chuỗi phải có trong câu trả lời (so không dấu, không phân biệt hoa thường; số so nguyên con số).

    python run_server.py -m system3.system4.eval.abi.golden --target router               # chỉ code (router + tools), vài giây
    python run_server.py -m system3.system4.eval.abi.golden --target web --base http://127.0.0.1:8300 --user leader --password ...
    python run_server.py -m system3.system4.eval.abi.golden --dump                         # chỉ ghi bộ câu hỏi + đáp án ra tệp

Kết quả: system4/eval/abi/results/<target>_<giờ>.json (không đưa lên git: có tên cán bộ thật) + bảng tóm tắt theo nhóm.
Không còn chế độ hỏi trợ lý AI của web (--target remote, dùng ngày 16/10): tốn token của chủ web, leader cấm từ 17/10/2026.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ...abi import normalize, router, store, tools
from ...server.ground import fold

OUT = Path(__file__).resolve().parent / "results"


def _num_ok(n: str, ans: str) -> bool:
    return re.search(rf"(?<![\d.,]){re.escape(n)}(?![\d])", ans) is not None


def check(expect: list[str], answer: str) -> tuple[bool, list[str]]:
    """expect: "#66" = con số nguyên; "@digits" = so chỉ chữ số (số điện thoại); còn lại = cụm chữ (không dấu)."""
    words = lambda t: " ".join(re.findall(r"[a-z0-9]+", fold(t)))
    fa, fw, digits = fold(answer), f" {words(answer)} ", re.sub(r"\D", "", answer)

    def one(e: str) -> bool:
        if e.startswith("#"):
            return _num_ok(e[1:], answer)
        if e.startswith("@"):
            return e[1:] in digits
        if re.search(r"[@.:/]", e):   # email, ngày "19/10", giờ "7:30": so nguyên chuỗi
            return fold(e) in fa
        return f" {words(e)} " in fw  # tên, cụm chữ: so theo từ (dấu câu sau tên không làm trượt)

    miss = [e for e in expect if not any(one(x) for x in e.split("|"))]   # "a|b" = một trong các cách
    return not miss, miss


def _key(e: dict, data: dict) -> str:
    """Từ nhận ra một sự kiện trong câu trả lời: từ riêng dài nhất trong tên (vd. "agroviet"), không có thì 4 chữ đầu tên."""
    uniq = []
    for w in router.words(e["title"]):
        if len(w) >= 5 and not w.isdigit() and w not in router.EV_COMMON and \
                sum(w in router.words(x["title"]) for x in data["events"]) == 1:
            uniq.append(w)
    return max(uniq, key=len) if uniq else " ".join(router.words(e["title"])[:4])


def _loc_key(loc: str) -> str:
    """Các cặp chữ liền nhau đặc trưng của địa điểm (bỏ số, từ chung), nối bằng "|": trúng một cặp là đủ — AI hay viết lại địa chỉ."""
    generic = set("so duong phuong tang lau thanh pho ho chi minh tp viet nam city vietnam street hoi truong trung tam va".split())
    ws = router.words(loc)
    pairs = [f"{a} {b}" for a, b in zip(ws, ws[1:]) if not ({a, b} & generic) and not (a.isdigit() or b.isdigit())]
    return "|".join(dict.fromkeys(pairs)) or loc


def golden(data: dict, now: datetime) -> list[dict]:
    qs: list[dict] = []

    def add(group: str, q: str, expect: list[str], note: str = ""):
        qs.append({"id": len(qs) + 1, "group": group, "q": q, "expect": [x for x in expect if x], "note": note})

    evs = data["events"]
    up = sorted([e for e in evs if tools.event_status(e, now) in ("upcoming", "ongoing")], key=lambda e: e["starts"] or "")
    past = sorted([e for e in evs if tools.event_status(e, now) == "past"], key=lambda e: e["starts"] or "", reverse=True)
    # --- sự kiện
    add("su_kien", "Các sự kiện sắp diễn ra", [_key(e, data) for e in up] or ["chua co su kien"], "CÂU MẪU 1")
    add("su_kien", "Có bao nhiêu sự kiện sắp diễn ra?", [f"#{len(up)}"])
    if past:
        add("su_kien", "Các sự kiện đã diễn ra gần đây", [_key(past[0], data)])
    if up:
        m = normalize.dt(up[-1]["starts"])
        in_m = [e for e in evs if (normalize.dt(e["starts"]) or now).month == m.month and (normalize.dt(e["starts"]) or now).year == m.year]
        add("su_kien", f"Tháng {m.month} có sự kiện gì?", [_key(e, data) for e in in_m])
    hn = [e for e in up if tools.in_place(e, ["ha noi"])]
    add("su_kien", "Sự kiện nào sắp tổ chức ở Hà Nội?", [_key(e, data) for e in hn] or ["chua co su kien"])
    for e in up[:4]:   # gọi bằng tên đầy đủ như người dùng chép từ web (một từ như "INNOVATION" mơ hồ: cuộc thi hay vòng bán kết?)
        s = normalize.dt(e["starts"])
        add("su_kien_chi_tiet", f"{e['title']} bắt đầu ngày nào?", [f"{s.day}/{s.month}|{s:%d/%m}|{s.day} tháng {s.month}|{s:%d} tháng {s.month}"])
        add("su_kien_chi_tiet", f"{e['title']} tổ chức ở đâu?", [_loc_key(e["location"])])
    # --- tổ chức
    rooms = [x for x in data["departments"] if not x["leadership_unit"]]
    add("to_chuc", "Có bao nhiêu phòng ban", [f"#{len(rooms)}"], "CÂU MẪU 2")
    add("to_chuc", "Trung tâm có bao nhiêu cán bộ?", [f"#{len(data['people'])}"])
    director = next((p for p in data["people"] if p["title"] == "Giám đốc"), None)
    if director:
        add("to_chuc", "Giám đốc trung tâm là ai?", [director["name"]])
    for x in rooms:
        short = x["name"].replace("Phòng Hỗ trợ Công nghệ", "Phòng").replace("Phòng ", "Phòng ")
        head = next((p for p in data["people"] if p["department_id"] == x["id"] and p["title"] == "Trưởng phòng"), None)
        if head:
            add("to_chuc_phong", f"Trưởng {short[0].lower() + short[1:]} là ai?", [head["name"]])
        add("to_chuc_phong", f"{short} có bao nhiêu người?", [f"#{x['n_people']}"])
    for x in rooms[:3]:
        if x["email"]:
            add("to_chuc_phong", f"Email của {x['name']} là gì?", [x["email"]])
    # --- liên hệ
    c = data["center"]
    add("lien_he", "Hotline của trung tâm là gì?", ["@" + re.sub(r"\D", "", c["hotline"])[-8:]])
    add("lien_he", "Địa chỉ trụ sở trung tâm ở đâu?", ["tran hung dao"])
    add("lien_he", "Giờ làm việc của trung tâm?", [c["work_hours"][:5].lstrip("0")])
    add("lien_he", "Email liên hệ của trung tâm là gì?", [c["email"]])
    # --- danh mục, chương trình
    inc = [x for x in data["catalog"] if tools.INCUBATED in x["categories"]]
    add("danh_muc", "Có bao nhiêu doanh nghiệp đang được ươm tạo?", [f"#{len(inc)}"])
    add("danh_muc", "Trung tâm có bao nhiêu sản phẩm?", [f"#{sum(x['kind'] == 'product' for x in data['catalog'])}"])
    svc = [x for x in data["catalog"] if x["kind"] == "service"]
    add("danh_muc", "Trung tâm có những dịch vụ gì?", [f"#{len(svc)}|" + "|".join(x["name"] for x in svc)])
    add("danh_muc", "Có bao nhiêu chương trình, chính sách hỗ trợ?", [f"#{len(data['programs'])}"])
    # --- câu tự do (từ trang giới thiệu)
    add("tu_do", "Trung tâm được thành lập năm nào?", ["2009"])
    add("tu_do", "Trung tâm trực thuộc cơ quan nào?", ["ban quan ly khu nong nghiep cong nghe cao"])
    add("tu_do", "Quy trình tham gia ươm tạo gồm những bước nào?", ["tiep nhan nhu cau"])
    add("tu_do", "Nghị quyết 64/2026 hỗ trợ gì?", ["khong hoan lai"])
    # --- ngoài phạm vi
    add("ngoai_pham_vi", "Thời tiết hôm nay thế nào?", ["khong co|ngoai pham vi|chi ho tro|chu yeu ho tro|khong the|chua tim thay"])
    return qs


# ------------------------------------------------------------------ cách hỏi
def ask_router(q: str, data: dict, now: datetime) -> dict:
    r = router.route(q, data, now)
    if not r:
        return {"answer": "", "kind": "search (không chấm được ở chế độ router)", "skip": True}
    return {"answer": r["fact"]["answer"] if r["plain"] else r["fact"]["text"], "kind": r["intent"] + ("" if r["plain"] else " (thẻ cho AI)")}


class Web:
    def __init__(self, base: str, user: str, password: str):
        import httpx
        self.c = httpx.Client(base_url=base, timeout=240)
        r = self.c.post("/s4/auth/login", json={"username": user, "password": password})
        r.raise_for_status()
        self.dom = next(d for d in self.c.get("/s4/domains").json()["domains"] if d["engine"] == "abi")

    def __call__(self, q: str) -> dict:
        text, cid, t0, done_ms, revised = "", None, time.perf_counter(), None, False
        with self.c.stream("POST", "/s4/chat", json={"text": q, "domain_id": self.dom["id"]}) as r:
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                e = json.loads(line[6:])
                if e["type"] == "meta":
                    cid = e["conversation_id"]
                elif e["type"] == "delta":
                    text += e["text"]
                elif e["type"] == "replace":
                    text = e.get("text", "")
                elif e["type"] == "checking":   # viết lại sau khi kiểm: bản cuối không hiện dần, đọc từ hội thoại khi xong
                    revised = True
                elif e["type"] == "error":
                    text += "\n[LỖI] " + e["message"]
                elif e["type"] == "done":   # câu trả lời hiện xong; luồng còn mở tới khi bước ghi nhớ chạy xong
                    done_ms = int((time.perf_counter() - t0) * 1000)
        msg = self.c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1] if cid else {}
        meta = msg.get("meta") or {}
        if revised:
            text = msg.get("content", text)
        abi = meta.get("abi") or {}
        return {"answer": text, "kind": ("code" if abi.get("code_answer") else "ai") + (f":{abi['intent']}" if abi.get("intent") else ""),
                "sources": [s.get("url") for s in meta.get("sources") or []], "llm_ms": (meta.get("timing") or {}).get("llm_ms"), "done_ms": done_ms}


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["router", "web"], default="router")
    ap.add_argument("--base", default="http://127.0.0.1:8300")
    ap.add_argument("--user", default="")
    ap.add_argument("--password", default="")
    ap.add_argument("--only", default="", help="chỉ chạy các nhóm này (cách nhau bởi dấu phẩy)")
    ap.add_argument("--dump", action="store_true", help="chỉ ghi bộ câu hỏi + đáp án (sinh từ dữ liệu hiện tại) ra results/, không hỏi")
    a = ap.parse_args(argv)
    data = store.data()
    if not data:
        print("Chưa có runtime/abi/data.json: chạy đồng bộ trước (python run_server.py -m system3.system4.abi.sync --no-index)")
        return 1
    now = tools.now_vn()
    qs = golden(data, now)
    if a.only:
        qs = [x for x in qs if x["group"] in a.only.split(",")]
    if a.dump:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"golden_{datetime.now():%Y%m%d_%H%M}.json"
        path.write_text(json.dumps({"data_synced_at": data.get("synced_at"), "now": now.isoformat(), "questions": qs},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(qs)} câu -> {path}")
        return 0
    ask = {"router": lambda q: ask_router(q, data, now), "web": Web(a.base, a.user, a.password) if a.target == "web" else None}[a.target]
    rows = []
    for i, x in enumerate(qs):
        t0 = time.perf_counter()
        try:
            r = ask(x["q"])
        except Exception as e:
            r = {"answer": "", "kind": f"lỗi: {e}"}
        ms = r.get("done_ms") or int((time.perf_counter() - t0) * 1000)   # web: tới lúc câu trả lời hiện xong
        ok, miss = (None, []) if r.get("skip") else check(x["expect"], r["answer"])
        rows.append({**x, **r, "ok": ok, "miss": miss, "ms": ms})
        mark = "—" if ok is None else ("✓" if ok else "✗")
        print(f"{mark} [{x['group']}] {x['q']}  ({r['kind']}, {ms} ms){'  thiếu: ' + ', '.join(miss) if miss else ''}", flush=True)
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["ok"] is not None:
            by[r["group"]][0] += r["ok"]
            by[r["group"]][1] += 1
    tot = [sum(v[0] for v in by.values()), sum(v[1] for v in by.values())]
    print("\nNhóm                  đúng / chấm")
    for g, (k, n) in by.items():
        print(f"  {g:20s} {k:3d} / {n}")
    print(f"  {'TỔNG':20s} {tot[0]:3d} / {tot[1]}  ({100 * tot[0] / max(1, tot[1]):.0f}%)")
    lat = sorted(r["ms"] for r in rows)
    if lat:
        print(f"Thời gian: trung vị {lat[len(lat) // 2]} ms, p90 {lat[int(len(lat) * 0.9) - 1 if len(lat) > 1 else 0]} ms")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{a.target}_{datetime.now():%Y%m%d_%H%M}.json"
    path.write_text(json.dumps({"target": a.target, "data_synced_at": data.get("synced_at"), "now": now.isoformat(),
                                "score": {g: v for g, v in by.items()}, "total": tot, "rows": rows}, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("Đã lưu", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

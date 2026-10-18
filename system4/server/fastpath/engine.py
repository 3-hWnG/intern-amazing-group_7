"""Engine đường nhanh: trả lời bằng CODE trên các bảng đã biên dịch (không gọi AI lúc hỏi, vài mili giây).

Kết cục: answer (nguyên văn ô dữ liệu kèm nguồn) · ask (nhiều dòng ngang điểm -> nút lựa chọn) · refuse (gọi đích danh một tên riêng
không có trong dữ liệu; chỉ dùng ở lĩnh vực grounded) · decline (không chắc -> NHƯỜNG đường cũ: tìm kiếm + AI).
Ý lấy từ System 3: IDF theo chữ, chữ lạ mang trọng số lớn nên kéo độ phủ xuống (cổng phạm vi); tên >= 2 chữ nằm trọn trong câu thì chắc là
dòng đó (NAMED_PREC); so dấu khi người dùng gõ có dấu (ACCENT_MISMATCH); hỏi lại khi ngang điểm; nhớ dòng của lượt trước cho câu nối tiếp.
Loại câu nào của bảng nào được dùng do bài tự kiểm quyết định (selftest.py) — `enabled`.
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

from ..ground import fold
from .compile import tokens, words

STOP = set("""a ah ai anh ay ban be ben biet cac cai can cho chi chu co con cua cung da dang day de den di do duoc em gi giup hay hoi
hom khong la lam ma minh mot nao nay nhe nha nho nhi nua o oi ong ra roi sao se so ta tai the thi toi tren trong tu va vay ve voi xem xin
ok oke ten muon ho chau bac khi""".split())
AGG = re.compile(r"\b(bao nhieu|may|so luong|tong so|dem|liet ke|tat ca|danh sach|nhung|ke ten)\b")
AGG_STRONG = re.compile(r"\b(bao nhieu|so luong|tong so|dem|liet ke|tat ca|danh sach|nhung)\b")
COUNT = re.compile(r"\b(bao nhieu|may|so luong|tong so|dem)\b")
GREET = set("chao xin hello hi alo cam on thanks thank you tam biet bye khoe the nao hom nay ban nhe nha ok oke nhieu a vui qua tot".split())
YEAR = re.compile(r"\bnam ((?:19|20)\d\d)\b")
UPCOMING = re.compile(r"\b(sap dien ra|sap to chuc|sap toi|tiep theo|se dien ra|se to chuc|dang dien ra)\b")
PAST = re.compile(r"\b(da dien ra|da to chuc|vua qua|vua roi|da ket thuc)\b")
MONTH = re.compile(r"\bthang (\d{1,2})\b")
VN = timezone(timedelta(hours=7))
ACCEPT = 0.6     # độ phủ tối thiểu (theo IDF) của chữ nội dung trong câu hỏi
LIST_MAX = 40


def parse_date(v) -> datetime | None:
    v = str(v or "").strip()
    try:
        if re.match(r"\d{4}-\d{2}-\d{2}", v):
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return d.astimezone(VN) if d.tzinfo else d.replace(tzinfo=VN)
        m = re.match(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", v)
        if m:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), tzinfo=VN)
    except ValueError:
        return None
    return None


def show(v, typ: str) -> str:
    """Hiển thị theo kiểu cột: ngày ISO -> dd/mm/yyyy (giờ VN); số nguyên lớn -> 1.450.000."""
    s = str(v)
    if typ == "date" and re.match(r"\d{4}-\d{2}-\d{2}", s):
        d = parse_date(s)
        if d:
            return d.strftime("%d/%m/%Y %H:%M") if (d.hour or d.minute) else d.strftime("%d/%m/%Y")
    if typ == "number" and re.fullmatch(r"-?\d{4,}", s):
        return f"{int(s):,}".replace(",", ".")
    return s


def _accent_ok(q_raw: str, c_raw: str) -> bool:
    return q_raw == c_raw or fold(q_raw) == q_raw   # gõ có dấu thì phải đúng dấu; gõ không dấu thì so bỏ dấu


def _contig(q: list[str], phrase: list[str]) -> int | None:
    n = len(phrase)
    for i in range(len(q) - n + 1):
        if q[i:i + n] == phrase:
            return i
    return None


def _cap_words(text: str) -> list[list[str]]:
    out, cur = [], []
    for i, w in enumerate(re.findall(r"\w+", text)):
        if i > 0 and w[:1].isupper() and not w.isupper():
            cur.append(w)
            continue
        if len(cur) >= 2:
            out.append(cur)
        cur = []
    if len(cur) >= 2:
        out.append(cur)
    return out


class Engine:
    def __init__(self, tables: list[dict], texts: list[dict], enabled: dict):
        self.ents = [t for t in tables if t["parent"] is None and len(t["rows"]) >= 1]
        self.texts = texts
        self.enabled = enabled
        self.bykey = {t["key"]: t for t in tables}
        self.byrow = {}
        docs = []
        for t in self.ents:
            t["_tw"] = [words(r["title"]) for r in t["rows"]]
            t["_tt"] = [set(w) for w in t["_tw"]]
            stem = (t.get("file") or "").rsplit(".", 1)[0].replace("_", " ")
            t["_tok"] = set(words(" ".join([t["title_label"], t["name"], t.get("entity_noun", ""), stem]))) | {"dong", "muc"}   # "dòng" / "mục" = một dòng của bảng
            for i, (r, tt) in enumerate(zip(t["rows"], t["_tt"])):
                self.byrow[r["id"]] = (t, i)
                docs.append(tt | set(w for v in r["fields"].values() for w in words(str(v))))
        for x in self.texts:
            x["_w"] = set(words(x["title"] + " " + x["text"]))
            docs.append(x["_w"])
        self.vocab = set().union(*docs) if docs else set()
        self.N, self.df = len(docs) or 1, Counter(w for d in docs for w in d)

    def on(self, t: dict, route: str) -> bool:
        return self.enabled.get(t["key"], {}).get(route, True)

    def idf(self, w: str) -> float:
        return math.log((self.N + 1) / (self.df.get(w, 0) + 0.5))

    def mass(self, ws) -> float:
        return sum(self.idf(w) for w in ws)

    # ------------------------------------------------------------------ các bước
    def _field(self, t: dict, q: list[tuple[str, str]], skip: set[int]) -> tuple[str | None, set[int], bool]:
        best, pos, neg = None, set(), False
        for f, meta in t["fields"].items():
            if meta["type"] == "empty":
                continue
            for cue, is_neg in [(c, False) for c in meta["cues"]] + [(c, True) for c in meta.get("absent", [])]:
                fc, n = [fold(w) for w in cue], len(cue)
                for i in range(len(q) - n + 1):
                    if any(j in skip for j in range(i, i + n)) or [x[0] for x in q[i:i + n]] != fc:
                        continue
                    if all(_accent_ok(q[i + k][1], cue[k]) for k in range(n)) and n > len(pos):
                        best, pos, neg = f, set(range(i, i + n)), is_neg
                    break
        if best:   # mọi gợi ý khác của CÙNG trường có trong câu cũng là chữ của trường ("sinh ... ngày" đảo thứ tự)
            for cue in t["fields"][best]["cues"]:
                fc = [fold(w) for w in cue]
                i = _contig([x[0] for x in q], fc)
                if i is not None and not any(j in skip for j in range(i, i + len(fc))):
                    pos |= set(range(i, i + len(fc)))
        return best, pos, neg

    def _entities(self, t: dict, cand: list[str], qf: list[str]) -> list[tuple[float, float, int]]:
        out, tot = [], self.mass(cand) if cand else 0
        for i, tt in enumerate(t["_tt"]):
            m = [w for w in cand if w in tt]
            if not m:
                continue
            cov = self.mass(m) / tot if tot else 0
            if len(t["_tw"][i]) >= 2 and len(set(m)) == len(tt) and _contig(qf, t["_tw"][i]) is not None:
                cov = max(cov, ACCEPT)        # NAMED_PREC
            out.append((cov, len(set(m)) / max(1, len(tt)), i))
        out.sort(reverse=True)
        return out

    def _aggregate(self, t: dict, q: list[str], used: set[int], field, neg) -> dict | None:
        filters, used, rows = [], set(used), t["rows"]
        qs = " ".join(q)
        dates = [f for f, x in t["fields"].items() if x["type"] == "date"]
        m = YEAR.search(qs)
        if m and dates:
            f = field if field in dates else dates[0]
            filters.append((f"năm {m.group(1)} ({t['fields'][f]['label']})", lambda r, f=f, y=m.group(1): y in str(r["fields"].get(f, ""))))
            i = q.index(m.group(1)); used |= {i - 1, i}
        if dates:   # thời gian tương đối (sắp tới / đã qua / tháng N): code tính theo giờ hiện tại
            f = field if field in dates else next((d for d in dates if re.search(r"start|bat dau|tu ngay|ngay", fold(d))), dates[0])
            end = next((d for d in dates if re.search(r"end|ket thuc|den ngay", fold(d))), f)
            now = datetime.now(VN)
            for rx, up in ((UPCOMING, True), (PAST, False)):
                mm = rx.search(qs)
                if mm:
                    a = len(qs[:mm.start()].split()); used |= set(range(a, a + len(mm.group().split())))
                    if up:
                        filters.append(("sắp / đang diễn ra", lambda r, e=end: (parse_date(r["fields"].get(e)) or datetime.min.replace(tzinfo=VN)) >= now))
                    else:
                        filters.append(("đã diễn ra", lambda r, e=end: (parse_date(r["fields"].get(e)) or datetime.max.replace(tzinfo=VN)) < now))
                    break
            mm = MONTH.search(qs)
            if mm and 1 <= int(mm.group(1)) <= 12:
                a = len(qs[:mm.start()].split()); used |= {a, a + 1}
                filters.append((f"tháng {mm.group(1)} ({t['fields'][f]['label']})",
                                lambda r, f=f, k=int(mm.group(1)): getattr(parse_date(r["fields"].get(f)), "month", 0) == k))
        if field and t["fields"][field]["type"] == "flag":
            filters.append((f"{'không ' if neg else ''}{t['fields'][field]['label']}",
                            lambda r, f=field, n=neg: (not r["fields"].get(f)) if n else bool(r["fields"].get(f))))
        targets = [("__title__", None)] + [(f, x) for f, x in t["fields"].items()
                                           if x["type"] in ("text", "enum") and not x.get("long")]
        while True:   # điều kiện theo giá trị: mỗi lần lấy cụm chữ liền dài nhất nằm trong giá trị của một cột (không phải mọi dòng đều có)
            free = [i for i in range(len(q)) if i not in used and q[i] not in STOP]
            best = None
            for n in (4, 3, 2, 1):
                for s in free:
                    span = list(range(s, s + n))
                    if any(j not in free for j in span) or (n == 1 and self.idf(q[s]) < 1.5):
                        continue
                    ph = " " + " ".join(q[j] for j in span) + " "
                    for f, x in targets:
                        get = (lambda r: r["title"]) if f == "__title__" else (lambda r, f=f: str(r["fields"].get(f, "")))
                        hit = [r for r in rows if ph in " " + " ".join(words(get(r))) + " "]
                        if (2 if n == 1 else 1) <= len(hit) < len(rows) and (best is None or n > best[0]):
                            best = (n, f, ph.strip(), set(span), get, x)
                if best:
                    break
            if not best:
                break
            n, f, ph, span, get, x = best
            label = t["title_label"] if f == "__title__" else t["fields"][f]["label"]
            filters.append((f"«{label}» có «{ph}»", lambda r, g=get, p=ph: f" {p} " in " " + " ".join(words(g(r))) + " "))
            used |= span
        noun = words(t.get("entity_noun", ""))
        if not filters and COUNT.search(qs) and noun and _contig(q, noun) is not None:   # "bao nhiêu <danh từ>" -> đếm cả bảng
            a = _contig(q, noun); used |= set(range(a, a + len(noun)))
            filters.append(("cả bảng", lambda r: True))
        if not filters:
            return None
        hit = [r for r in rows if all(fn(r) for _, fn in filters)]
        return {"rows": hit, "desc": "; ".join(d for d, _ in filters), "used": used, "count": bool(COUNT.search(qs))}

    def _covered(self, q: list[str], used: set[int], extra: set[str], agg_pos: set[int]) -> float:
        content = [(i, w) for i, w in enumerate(q) if w not in STOP and w not in GREET and i not in agg_pos]
        if not content:
            return 1.0
        tot = self.mass(w for _, w in content)
        return self.mass(w for i, w in content if i in used or w in extra) / tot if tot else 1.0

    # ------------------------------------------------------------------ một lượt
    def answer(self, text: str, state: dict) -> dict:
        t0 = time.perf_counter()
        r = self._answer(text, state)
        r["ms"] = round((time.perf_counter() - t0) * 1000, 2)
        return r

    def _answer(self, text: str, state: dict) -> dict:
        qt = tokens(text)
        q = [f for f, _ in qt]
        qs = " ".join(q)
        if not q or all(w in GREET or w in STOP for w in q):
            return {"kind": "decline", "reason": "câu xã giao / rỗng"}
        agg_pos = set()
        for m in AGG.finditer(qs):
            a = len(qs[:m.start()].split()); agg_pos |= set(range(a, a + len(m.group().split())))
        quoted = re.search(r"[\"“”«](.+?)[\"“”»]", text)
        qspan = set()
        if quoted:
            a = len(words(text[:quoted.start()])); qspan = set(range(a, a + len(words(quoted.group(1)))))
        best, fhits = None, []
        for t in self.ents:
            base = [w for i, w in enumerate(q) if w not in STOP and w not in t["_tok"] and i not in agg_pos]
            cand = [q[i] for i in sorted(qspan)] if qspan else base
            ranks = self._entities(t, cand, q)
            skip = set(qspan)
            if ranks and ranks[0][1] >= 1.0:       # không cho gợi ý trường khớp BÊN TRONG tên của dòng
                i0 = _contig(q, t["_tw"][ranks[0][2]])
                if i0 is not None:
                    skip |= set(range(i0, i0 + len(t["_tw"][ranks[0][2]])))
            field, fpos, neg = self._field(t, qt, skip)
            if field:
                fhits.append((len(fpos), t, field, fpos, neg))
                if not qspan:
                    cand = [w for i, w in enumerate(q) if i not in fpos and w not in STOP and w not in t["_tok"] and i not in agg_pos]
                    ranks = self._entities(t, cand, q)
            if ranks and (best is None or ranks[0][:2] > best[0][:2]):
                best = (ranks[0], ranks, t, field, neg)
        fhits.sort(key=lambda x: -x[0])
        # 1) một dòng rõ ràng (+ trường được hỏi)
        if best and best[0][0] >= ACCEPT:
            (cov, tcov, i), ranks, t, field, neg = best
            tie = [x for x in ranks if x[0] >= cov - 1e-9]
            listing = AGG_STRONG.search(qs) and cov < 1
            if not (field and t["fields"][field]["type"] == "flag") and not listing:
                if not self.on(t, "field"):
                    return {"kind": "decline", "reason": f"bảng «{t['name']}»: loại câu tra trường đang tắt (tự kiểm chưa đạt)"}
                if len(tie) > 1 and not any(x[1] >= 1.0 for x in tie):
                    rows = [t["rows"][x[2]] for x in tie][:8]
                    state["pending"] = {"table": t["key"], "field": field}
                    noun = t.get("entity_noun") or "mục"
                    return {"kind": "ask", "route": "ask", "table": t["key"], "content": f"Có {len(tie)} {noun} khớp. Bạn hỏi về {noun} nào?",
                            "choices": [r["title"] for r in rows], "sources": []}
                if len(tie) > 1:
                    i = next(x[2] for x in tie if x[1] >= 1.0)
                if not field and state.get("pending", {}).get("table") == t["key"]:
                    field = state["pending"]["field"]
                state.pop("pending", None)
                state["entity"] = t["rows"][i]["id"]
                return self._fact(t, t["rows"][i], field)
        # 2) câu nối tiếp: có trường, không có dòng mới -> dòng của lượt trước
        ent = self.byrow.get(state.get("entity"))
        if ent and fhits:
            t, i = ent
            hit = next((h for h in fhits if h[1] is t), None)
            if hit and self.on(t, "field") and not [w for j, w in enumerate(q) if j not in hit[3] and w not in STOP and w not in t["_tok"] and w not in GREET]:
                return {**self._fact(t, t["rows"][i], hit[2]), "followup": True}
        # 3) bảng một dòng (thông tin chung): có trường được hỏi là đủ
        for h in fhits:
            if len(h[1]["rows"]) == 1 and not agg_pos and self.on(h[1], "field"):
                return self._fact(h[1], h[1]["rows"][0], h[2])
        # 4) đếm / liệt kê / tra theo thuộc tính trên cả bảng (code tính)
        for t in self.ents:
            if not self.on(t, "aggregate") or len(t["rows"]) < 2:
                continue
            field, fpos, neg = self._field(t, qt, set())
            agg = self._aggregate(t, q, fpos | agg_pos, field, neg)
            if not agg or self._covered(q, agg["used"], t["_tok"], agg_pos) < ACCEPT:
                continue
            if not agg_pos and not (field and 1 <= len(agg["rows"]) <= 5):
                continue   # không có từ đếm / liệt kê: chỉ tra theo thuộc tính khi biết trường được hỏi và ít dòng
            noun = t.get("entity_noun") or "mục"
            if not agg_pos and t["fields"][field]["type"] != "flag":
                ftype, lab = t["fields"][field]["type"], t["fields"][field]["label"]
                lines = [f"- {r['title']}: {show(r['fields'].get(field) or '(không ghi)', ftype)}" for r in agg["rows"]]
                return {"kind": "answer", "route": "lookup", "table": t["key"], "content": f"{lab[:1].upper() + lab[1:]} ({agg['desc']}):\n" + "\n".join(lines),
                        "sources": [self._src(t, r) for r in agg["rows"]]}
            names = [r["title"] for r in agg["rows"]]
            head = f"Có **{len(names)}** {noun} thỏa điều kiện ({agg['desc']}), trên tổng {len(t['rows'])} {noun}."
            if not names:
                head = f"Không có {noun} nào thỏa điều kiện ({agg['desc']}) trong {len(t['rows'])} {noun}."
            body = "" if agg["count"] and len(names) > LIST_MAX else "\n" + "\n".join(f"- {n}" for n in names[:LIST_MAX])
            more = f"\n- … và {len(names) - LIST_MAX} {noun} khác" if not agg["count"] and len(names) > LIST_MAX else ""
            return {"kind": "answer", "route": "aggregate", "table": t["key"], "content": head + body + more,
                    "sources": [self._src(t, r) for r in agg["rows"][:5]]}
        # 5) đoạn văn bản (Word / PDF / ghi chú): trích nguyên đoạn khớp nhất
        content = [w for i, w in enumerate(q) if w not in STOP and w not in GREET and i not in agg_pos]
        texts = [x for x in self.texts if self.enabled.get(f"text:{x['dataset_id']}", True)]
        if content and texts:
            tot = self.mass(content)
            sc = sorted(((self.mass(w for w in content if w in x["_w"]) / tot, k) for k, x in enumerate(texts)), reverse=True)
            if sc[0][0] >= ACCEPT:
                x = texts[sc[0][1]]
                return {"kind": "answer", "route": "text", "content": f"Theo «{x['title']}»: {x['text']}",
                        "sources": [{"record_id": x["id"], "title": x["title"], "dataset": x["dataset"]}]}
        # 6) gọi đích danh một tên riêng mà dữ liệu không có (có chữ không hề xuất hiện trong dữ liệu)
        for grp in _cap_words(text):
            gw = words(" ".join(grp))
            if not any(all(w in tt for w in gw) for t in self.ents for tt in t["_tt"]) and any(w not in self.vocab for w in gw):
                return {"kind": "refuse", "route": "refuse", "content": f"Mình không tìm thấy «{' '.join(grp)}» trong dữ liệu đang bật.", "sources": []}
        return {"kind": "decline", "reason": "không đủ chắc"}

    @staticmethod
    def _src(t: dict, r: dict) -> dict:
        return {"record_id": r["id"], "title": r["title"], "dataset": t["dataset"]}

    def _fact(self, t: dict, row: dict, field: str | None) -> dict:
        src = [self._src(t, row)]
        if field:
            m = t["fields"][field]
            label, v = m["label"], row["fields"].get(field)
            if v:
                return {"kind": "answer", "route": "field", "table": t["key"], "field": field,
                        "content": f"**{label[:1].upper() + label[1:]}** của {row['title']}: {show(v, m['type'])}", "sources": src}
            return {"kind": "answer", "route": "field-empty", "table": t["key"], "field": field,
                    "content": f"Dữ liệu không ghi {label} của {row['title']}.", "sources": src}
        shown = {k: m for k, m in t["fields"].items() if m["type"] != "empty"}
        card = "\n".join(f"- **{m['label']}**: {show(row['fields'][k], m['type'])[:300]}" for k, m in shown.items() if row["fields"].get(k))
        miss = [m["label"] for k, m in shown.items() if not row["fields"].get(k)]
        tail = f"\n\n_Dữ liệu không ghi: {', '.join(miss)}._" if miss else ""
        return {"kind": "answer", "route": "card", "table": t["key"], "content": f"**{row['title']}**\n{card}{tail}", "sources": src}

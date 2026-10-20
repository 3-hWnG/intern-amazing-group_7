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
LIST = re.compile(r"\b(liet ke|tat ca|danh sach|nhung|ke ten)\b")
COUNT = re.compile(r"\b(bao nhieu|may|so luong|tong so|dem)\b")
AGG_RAW = {"bao nhieu": "bao nhiêu", "may": "mấy", "so luong": "số lượng", "tong so": "tổng số", "dem": "đếm", "liet ke": "liệt kê",
           "tat ca": "tất cả", "danh sach": "danh sách", "nhung": "những", "ke ten": "kể tên"}
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


def show(v, typ: str, col: str = "") -> str:
    """Hiển thị theo kiểu cột: ngày ISO -> dd/mm/yyyy (giờ VN); số nguyên lớn -> 1.450.000. Cột năm ("Năm thành lập": 1900) giữ nguyên,
    không thành "1.900" (lỗi thấy 19/10 trên dữ liệu thật: bệnh viện, di tích)."""
    s = str(v)
    if typ == "date" and re.match(r"\d{4}-\d{2}-\d{2}", s):
        d = parse_date(s)
        if d:
            return d.strftime("%d/%m/%Y %H:%M") if (d.hour or d.minute) else d.strftime("%d/%m/%Y")
    if typ == "number" and re.fullmatch(r"\d{4}", s) and 1000 <= int(s) <= 2100 and re.search(r"\bnam\b", fold(col)):
        return s
    if typ == "number" and re.fullmatch(r"-?\d{4,}", s):
        return f"{int(s):,}".replace(",", ".")
    return s


def _accent_ok(q_raw: str, c_raw: str, accented: bool = False) -> bool:
    """Gõ có dấu thì phải đúng dấu; gõ không dấu thì so bỏ dấu. accented = cả câu có gõ dấu: chữ không dấu trong câu đó là chữ không dấu
    thật, không khớp gợi ý có dấu ("thông TIN" không phải "TÍN chỉ": "Cho mình thông tin môn PRF192" từng trả số tín chỉ, FLM 19/10)."""
    return q_raw == c_raw or (fold(q_raw) == q_raw and not (accented and fold(c_raw) != c_raw))


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
    def __init__(self, tables: list[dict], texts: list[dict], enabled: dict, aggregate: bool = True, refuse: bool = True):
        self.ents = [t for t in tables if t["parent"] is None and len(t["rows"]) >= 1]
        self.texts = texts
        self.enabled = enabled
        self.aggregate = aggregate   # ⚙ FASTPATH_AGGREGATE: tắt thì câu đếm / liệt kê nhường đường cũ (bài tự kiểm vẫn chấm để báo cáo)
        self.refuse = refuse         # False = có đoạn văn bản không lập chỉ mục (tự kiểm đã tắt): từ vựng không đủ để nói "không có tên này"
        self.bykey = {t["key"]: t for t in tables}
        self.byrow = {}
        docs = []
        for t in self.ents:
            t["_tw"] = [words(r["title"]) for r in t["rows"]]
            t["_tr"] = [[w for _, w in tokens(r["title"])] for r in t["rows"]]
            t["_tt"] = [set(w) for w in t["_tw"]]
            stem = (t.get("file") or "").rsplit(".", 1)[0].replace("_", " ")
            t["_tok"] = set(words(" ".join([t["title_label"], t["name"], t.get("entity_noun", ""), stem]))) | {"dong", "muc"}   # "dòng" / "mục" = một dòng của bảng
            t["_vocab"], t["_rawvocab"] = set(), set()   # chữ của RIÊNG bảng này (cổng _leftover), không lẫn chữ của đoạn văn bản
            for i, (r, tt) in enumerate(zip(t["rows"], t["_tt"])):
                self.byrow[r["id"]] = (t, i)
                docs.append(tt | set(w for v in r["fields"].values() for w in words(str(v))))
                t["_vocab"] |= docs[-1]
                t["_rawvocab"] |= {w for _, w in tokens(r["title"] + " " + " ".join(str(v) for v in r["fields"].values()))}
        for x in self.texts:
            x["_w"] = set(words(x["title"] + " " + x["text"]))
            docs.append(x["_w"])
        self.vocab = set().union(*docs) if docs else set()
        raw = [r["title"] + " " + " ".join(str(v) for v in r["fields"].values()) for t in self.ents for r in t["rows"]]
        self.rawvocab = {w for txt in raw + [x["title"] + " " + x["text"] for x in self.texts] for _, w in tokens(txt)}   # chữ có dấu
        self.cuewords = {fold(c[0]) for t in self.ents for m in t["fields"].values() for c in m["cues"] + m.get("absent", []) if len(c) == 1}
        self.N, self.df = len(docs) or 1, Counter(w for d in docs for w in d)

    @staticmethod
    def nouns(t: dict) -> list[list[str]]:
        """Danh từ chỉ một dòng: do AI đặt (vd. "khách sạn"), dự phòng là tên sheet nếu có nghĩa ("Tour", "Điểm đến"; không phải "Sheet1")."""
        out = [words(t.get("entity_noun", ""))]
        name = words(t["name"])
        if name and not any(w.startswith("sheet") or w.isdigit() for w in name) and len(name) <= 3:
            out.append(name)
        return [n for n in out if n]

    def on(self, t: dict, route: str) -> bool:
        if route == "aggregate" and not self.aggregate:
            return False
        return self.enabled.get(t["key"], {}).get(route, True)

    def idf(self, w: str) -> float:
        return math.log((self.N + 1) / (self.df.get(w, 0) + 0.5))

    def mass(self, ws) -> float:
        return sum(self.idf(w) for w in ws)

    # ------------------------------------------------------------------ các bước
    def _field(self, t: dict, q: list[tuple[str, str]], skip: set[int]) -> tuple[str | None, set[int], bool]:
        best, pos, neg = None, set(), False
        accented = any(fold(w) != w for _, w in q)
        for f, meta in t["fields"].items():
            if meta["type"] == "empty":
                continue
            for cue, is_neg in [(c, False) for c in meta["cues"]] + [(c, True) for c in meta.get("absent", [])]:
                fc, n = [fold(w) for w in cue], len(cue)
                for i in range(len(q) - n + 1):
                    if any(j in skip for j in range(i, i + n)) or [x[0] for x in q[i:i + n]] != fc:
                        continue
                    if all(_accent_ok(q[i + k][1], cue[k], accented) for k in range(n)) and n > len(pos):
                        best, pos, neg = f, set(range(i, i + n)), is_neg
                    break
        if best:   # mọi gợi ý khác của CÙNG trường có trong câu cũng là chữ của trường ("sinh ... ngày" đảo thứ tự)
            for cue in t["fields"][best]["cues"]:
                fc = [fold(w) for w in cue]
                i = _contig([x[0] for x in q], fc)
                if i is not None and not any(j in skip for j in range(i, i + len(fc))):
                    pos |= set(range(i, i + len(fc)))
        return best, pos, neg

    def _entities(self, t: dict, cand: list[str], qf: list[str], qraw: list[str] = ()) -> list[tuple[float, float, int, int]]:
        """[(độ phủ, phần tên khớp, độ dài tên nằm trọn trong câu, dòng)]. NAMED_PREC xét trên CÂU GỐC: tên "Khách sạn Cố Đô" nằm trọn
        trong câu thì chắc là dòng đó, dù "khách sạn" là danh từ của bảng và "cố" / "đô" bỏ dấu trùng từ dừng (lỗi tìm ra 18/10)."""
        out, tot = [], self.mass(cand) if cand else 0
        for i, (tt, tw) in enumerate(zip(t["_tt"], t["_tw"])):
            named = (len(tw) >= 2 and _contig(qf, tw) is not None) or (len(tw) == 1 and len(tw[0]) >= 2 and t["_tr"][i][0] in qraw
                                                                        and fold(t["_tr"][i][0]) != t["_tr"][i][0])
            m = [w for w in cand if w in tt]
            if not m and not named:
                continue
            cov, tcov = (self.mass(m) / tot if tot else 0), len(set(m)) / max(1, len(tt))
            if named:
                cov, tcov = max(cov, ACCEPT), 1.0
            out.append((cov, tcov, len(tw) if named else 0, i))
        # dòng được gọi ĐÍCH DANH (tên nằm trọn trong câu) đứng trước dòng chỉ khớp vài chữ: "Trường Đại học FPT … công lập hay tư thục"
        # từng chọn "Trường Đại học Công nghệ Swinburne - FPT" vì "công" (lập) trùng "Công" (nghệ) làm độ phủ cao hơn (dữ liệu thật 19/10)
        out.sort(key=lambda x: (x[2] > 0, x), reverse=True)
        return out

    def _named(self, t: dict, i: int, q: list[str], named_len: int) -> bool:
        """Câu có gọi rõ dòng i không: tên nằm trọn trong câu, có mã của dòng ("PRF192", "T01"), có trọn một phần tên ("Programming
        Fundamentals" của "PRF192 · Programming Fundamentals – Cơ sở lập trình", phần >= 2 chữ, >= 1/4 tên theo IDF), hoặc phủ >= nửa tên.
        Không hỏi trường nào thì chỉ trả nguyên thẻ khi gọi rõ: "Mình muốn học ngành kinh tế…" từng nhận thẻ môn JTE301
        "Dịch chuyên ngành Kinh tế - Thương mại" vì trùng 3 chữ trong tên dài 12 chữ (dữ liệu FLM thật 19/10)."""
        if named_len:
            return True
        tw, qs = t["_tw"][i], set(q)
        if any(w in qs and any(c.isdigit() for c in w) and any(c.isalpha() for c in w) for w in tw):
            return True
        tot = self.mass(set(tw))
        if not tot:
            return False
        for part in re.split(r"\s[·–-]\s|[_(),;/|]", t["rows"][i]["title"]):
            pw = words(part)
            if len(pw) >= 2 and _contig(q, pw) is not None and self.mass(set(pw)) / tot >= 0.25:
                return True
        return self.mass({w for w in tw if w in qs}) / tot >= 0.5

    def _aggregate(self, t: dict, q: list[str], used: set[int], field, neg) -> dict | None:
        filters, used, rows, filter_fields = [], set(used), t["rows"], set()
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
        targets = [(f, x) for f, x in t["fields"].items() if x["type"] in ("text", "enum") and not x.get("long")] + [("__title__", None)]
        while True:   # điều kiện theo giá trị: mỗi lần lấy cụm chữ liền dài nhất nằm trong giá trị của một cột (không phải mọi dòng đều có)
            free = [i for i in range(len(q)) if i not in used and q[i] not in t["_tok"]]
            best = None
            for n in (4, 3, 2, 1):
                for s in free:
                    span = list(range(s, s + n))
                    if any(j not in free for j in span) or all(q[j] in STOP for j in span) or (n == 1 and self.idf(q[s]) < 1.5):
                        continue
                    ph = " " + " ".join(q[j] for j in span) + " "
                    for f, x in targets:
                        get = (lambda r: r["title"]) if f == "__title__" else (lambda r, f=f: str(r["fields"].get(f, "")))
                        hit = [r for r in rows if ph in " " + " ".join(words(get(r))) + " "]
                        code = n == 1 and ((any(ch.isdigit() for ch in q[s]) and any(ch.isalpha() for ch in q[s]))   # mã ngắn: "t01", "sp07"
                                           or any(" ".join(words(get(r))) == q[s] for r in hit))                 # hoặc bằng nguyên ô: "Huế"
                        if (2 if n == 1 and not code else 1) <= len(hit) < len(rows) and (best is None or n > best[0]):
                            best = (n, f, ph.strip(), set(span), get, x)
                if best:
                    break
            if not best:
                break
            n, f, ph, span, get, x = best
            label = t["title_label"] if f == "__title__" else t["fields"][f]["label"]
            filters.append((f"«{label}» có «{ph}»", lambda r, g=get, p=ph: f" {p} " in " " + " ".join(words(g(r))) + " "))
            filter_fields.add(f)
            used |= span
        if not filters:   # "bao nhiêu <danh từ>" (danh từ đứng NGAY sau từ đếm) -> đếm cả bảng; "khách sạn X hạng bao nhiêu" thì không
            for mm in COUNT.finditer(qs):
                a = len(qs[:mm.end()].split())
                noun = next((nw for nw in self.nouns(t) if q[a:a + len(nw)] == nw), None)
                if noun:
                    used |= set(range(a, a + len(noun)))
                    filters.append(("cả bảng", lambda r: True))
                    break
        if not filters:
            return None
        hit = [r for r in rows if all(fn(r) for _, fn in filters)]
        return {"rows": hit, "desc": "; ".join(d for d, _ in filters), "used": used, "count": bool(COUNT.search(qs)), "filter_fields": filter_fields}

    def _leftover(self, q: list[str], qt: list, t: dict, i: int, fpos: set[int], agg_pos: set[int], field) -> bool:
        """Cổng phạm vi cho câu tra một dòng: còn chữ KHÔNG HỀ có trong dữ liệu (vd. "vé MÁY BAY đi Phú Quốc")
        -> câu hỏi điều dữ liệu không ghi: nhường đường cũ. >= 2 chữ lạ, hoặc 1 chữ lạ khi không nhận ra trường được hỏi.
        "Có trong dữ liệu" = có trong CHÍNH BẢNG đó: lĩnh vực có cả bảng di tích lẫn bài viết về Vịnh Hạ Long thì "truyền thuyết về tên gọi
        Vịnh Hạ Long" từng được trả bằng thẻ dòng di tích vì "truyền thuyết" có trong bài viết (dữ liệu thật 19/10)."""
        title = set(t["_tw"][i])
        def known(j, w):   # gõ có dấu thì so chữ có dấu ("máy" bay khác "Mây" Ngàn); gõ không dấu thì so bỏ dấu
            return w in t["_vocab"] if fold(qt[j][1]) == qt[j][1] else qt[j][1] in t["_rawvocab"]
        unknown = [w for j, w in enumerate(q) if j not in fpos and j not in agg_pos and w not in title and w not in STOP and w not in GREET
                   and w not in t["_tok"] and not known(j, w) and not w.isdigit()]
        return len(unknown) >= 2 or (len(unknown) == 1 and not field)

    def _aggregate_best(self, q: list[str], qt: list, agg_pos: set[int]) -> dict | None:
        """Đếm / liệt kê / tra theo thuộc tính trên bảng hợp nhất: bảng được nhắc tên ("tour", "khách sạn") thắng, rồi tới độ phủ."""
        best = None
        for t in self.ents:
            if not self.on(t, "aggregate") or len(t["rows"]) < 2:
                continue
            field, fpos, neg = self._field(t, qt, set())
            agg = self._aggregate(t, q, fpos | agg_pos, field, neg)
            if not agg:
                continue
            cov = self._covered(q, agg["used"], t["_tok"], agg_pos)
            if cov < ACCEPT or (agg["filter_fields"] == {"__title__"} and len(agg["rows"]) == 1 and len(agg["desc"].split(";")) == 1):
                continue
            if not agg_pos and not (field and 1 <= len(agg["rows"]) <= 5):
                continue   # không có từ đếm / liệt kê: chỉ tra theo thuộc tính khi biết trường được hỏi và ít dòng
            mention = len({w for w in q if w in t["_tok"] and w not in STOP and w not in ("dong", "muc")})
            key = (mention, round(cov, 3), len(agg["used"]))
            if best is None or key > best[0]:
                best = (key, t, agg, field)
        if not best:
            return None
        _, t, agg, field = best
        noun = t.get("entity_noun") or "mục"
        if field and field not in agg["filter_fields"] and t["fields"][field]["type"] != "flag" and not agg["count"] and 1 <= len(agg["rows"]) <= 5:
            ftype, lab = t["fields"][field]["type"], t["fields"][field]["label"]   # "Hạng Kim cương được những ưu đãi nào?": liệt kê GIÁ TRỊ
            lines = [f"- {r['title']}: {show(r['fields'].get(field) or '(không ghi)', ftype, field)}" for r in agg["rows"]]
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
        qraw = [w for _, w in qt]
        qs = " ".join(q)
        if not q or all(w in GREET or w in STOP for w in q):
            return {"kind": "decline", "reason": "câu xã giao / rỗng"}
        agg_pos = set()
        for m in AGG.finditer(qs):
            a = len(qs[:m.start()].split()); span = range(a, a + len(m.group().split()))
            if all(_accent_ok(qt[j][1], w) for j, w in zip(span, AGG_RAW.get(m.group(), m.group()).split())):   # "máy" (bay) không phải "mấy"
                agg_pos |= set(span)
        quoted = re.search(r"[\"“”«](.+?)[\"“”»]", text)
        qspan = set()
        if quoted:
            a = len(words(text[:quoted.start()])); qspan = set(range(a, a + len(words(quoted.group(1)))))
        best, fhits = None, []
        for t in self.ents:
            base = [w for i, w in enumerate(q) if w not in STOP and w not in t["_tok"] and i not in agg_pos and w not in self.cuewords]
            cand = [q[i] for i in sorted(qspan)] if qspan else base
            ranks = self._entities(t, cand, q, qraw)
            skip = set(qspan)
            if ranks and ranks[0][1] >= 1.0:       # không cho gợi ý trường khớp BÊN TRONG tên của dòng
                i0 = _contig(q, t["_tw"][ranks[0][3]])
                if i0 is not None:
                    skip |= set(range(i0, i0 + len(t["_tw"][ranks[0][3]])))
            field, fpos, neg = self._field(t, qt, skip)
            if field:
                fhits.append((len(fpos), t, field, fpos, neg))
                if not qspan:
                    cand = [w for i, w in enumerate(q) if i not in fpos and w not in STOP and w not in t["_tok"] and i not in agg_pos
                            and w not in self.cuewords]
                    ranks = self._entities(t, cand, q, qraw)
            if ranks and (best is None or ranks[0][:3] > best[0][:3]):
                best = (ranks[0], ranks, t, field, neg, fpos)
        fhits.sort(key=lambda x: -x[0])
        numeric_field = any(h[1]["fields"][h[2]]["type"] in ("number", "id") for h in fhits)
        noun_after = any(q[len(qs[:mm.end()].split()):len(qs[:mm.end()].split()) + len(nw)] == nw
                         for mm in COUNT.finditer(qs) for t in self.ents for nw in self.nouns(t))
        clear_row = bool(best) and best[0][0] >= ACCEPT and bool(best[3])
        count_q = bool(COUNT.search(qs)) and bool(agg_pos) and not numeric_field and (noun_after or not clear_row)
        if count_q or LIST.search(qs):   # câu đếm / liệt kê: phép tính trên cả bảng trước (lỗi b17, b18 ngày 18/10)
            agg = self._aggregate_best(q, qt, agg_pos)
            if agg:
                return agg
            if count_q:
                return {"kind": "decline", "reason": "câu đếm nhưng không dựng được phép đếm chắc chắn"}
        # 1) một dòng rõ ràng (+ trường được hỏi)
        if best and best[0][0] >= ACCEPT:
            (cov, tcov, _, i), ranks, t, field, neg, fpos = best
            tie = [x for x in ranks if x[0] >= cov - 1e-9]
            listing = LIST.search(qs) and (cov < 1 or len(tie) > 1)
            if not (field and t["fields"][field]["type"] == "flag") and not listing:
                if not self.on(t, "field"):
                    return {"kind": "decline", "reason": f"bảng «{t['name']}»: loại câu tra trường đang tắt (tự kiểm chưa đạt)"}
                if self._leftover(q, qt, t, i, fpos, agg_pos, field):
                    return {"kind": "decline", "reason": "câu còn chữ không có trong dữ liệu (vd. hỏi điều dữ liệu không ghi)"}
                if not field and not state.get("pending") and not any(self._named(t, x[3], q, x[2]) for x in tie):
                    return {"kind": "decline", "reason": "không hỏi trường nào và không gọi rõ tên dòng nào: không trả nguyên thẻ"}
                if len(tie) > 1 and not any(x[1] >= 1.0 for x in tie):
                    rows = [t["rows"][x[3]] for x in tie][:8]
                    state["pending"] = {"table": t["key"], "field": field}
                    noun = t.get("entity_noun") or "mục"
                    return {"kind": "ask", "route": "ask", "table": t["key"], "content": f"Có {len(tie)} {noun} khớp. Bạn hỏi về {noun} nào?",
                            "choices": [r["title"] for r in rows], "sources": []}
                if len(tie) > 1:
                    i = next(x[3] for x in tie if x[1] >= 1.0)
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
        agg = self._aggregate_best(q, qt, agg_pos)
        if agg:
            return agg
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
        for grp in _cap_words(text) if self.refuse else []:
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
                        "content": f"**{label[:1].upper() + label[1:]}** của {row['title']}: {show(v, m['type'], field)}", "sources": src}
            return {"kind": "answer", "route": "field-empty", "table": t["key"], "field": field,
                    "content": f"Dữ liệu không ghi {label} của {row['title']}.", "sources": src}
        shown = {k: m for k, m in t["fields"].items() if m["type"] != "empty"}
        card = "\n".join(f"- **{m['label']}**: {show(row['fields'][k], m['type'], k)[:300]}" for k, m in shown.items() if row["fields"].get(k))
        miss = [m["label"] for k, m in shown.items() if not row["fields"].get(k)]
        tail = f"\n\n_Dữ liệu không ghi: {', '.join(miss)}._" if miss else ""
        return {"kind": "answer", "route": "card", "table": t["key"], "content": f"**{row['title']}**\n{card}{tail}", "sources": src}

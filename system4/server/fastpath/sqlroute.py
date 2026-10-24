"""Lộ trình SQL của đường nhanh (24/10/2026): câu ĐẾM / LIỆT KÊ / LỚN NHẤT – NHỎ NHẤT / TỔNG / SO SÁNH SỐ trên bảng người dùng tải lên.

"Biên dịch lúc nạp" dựng cho mỗi bảng một bảng SQLite PHẲNG có KIỂU (theo kiểu cột compile.py đã suy): số đọc theo đúng cách viết của cột
("1.404.587", "6.700,39", "4.4"), cột chữ có thêm bản bỏ dấu để lọc, cột chữ chứa năm ("11/1979", "Côn Đảo (1945)") có thêm cột năm.
Lúc hỏi, model 4B viết MỘT câu SELECT trên đúng bảng đó (ADR-09 / server/listsql.py của System 3: không JOIN, model không viết câu trả lời);
code chạy trong hộp cát (bản sao trong bộ nhớ, query_only, authorizer chỉ cho đọc bảng này, LIMIT, cắt truy vấn dài) và viết câu trả lời
từ kết quả. Sai cú pháp -> model sửa một lần; hỏng nữa -> None (engine lùi về phép tính bằng code / đường cũ).
Bài tự kiểm (selftest.py, route "sql") bật / tắt lộ trình này theo từng bảng.
"""
from __future__ import annotations

import re
import sqlite3
import threading

from ..ground import fold

MAX_ROWS, SHOW = 200, 40
SCHEMA = {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}
_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
YEARISH = re.compile(r"(?<!\d)(1[0-9]\d\d|20\d\d)(?!\d)")
# câu cần phép tính trên nhiều dòng (chữ đã bỏ dấu)
WANTS = re.compile(r"\b(bao nhieu|may|so luong|tong so|dem|liet ke|tat ca|danh sach|nhung|ke ten|tong|trung binh|cong lai|nhat|"
                   r"(?:tren|duoi|hon|lon hon|nho hon|it hon|nhieu hon|cao hon|thap hon|tu) [\d.,]+|truoc nam|sau nam|tro len|tro xuong)\b")
SUPER = re.compile(r"\bnhat\b")


def _ident(label: str, used: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", fold(label)).strip("_")[:40] or "cot"
    if base[0].isdigit():
        base = "c_" + base
    name, k = base, 2
    while name in used or name in ("ten", "ten_kd", "bang"):
        name, k = f"{base}_{k}", k + 1
    used.add(name)
    return name


def number_style(values: list[str]) -> str:
    """Cách viết số của một cột: 'vi' (chấm hàng nghìn, phẩy thập phân), 'dot' (chấm thập phân), 'comma' (phẩy thập phân không có hàng nghìn)."""
    vs = [v.strip() for v in values if v and v.strip()]
    if any(re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", v) for v in vs):
        return "vi"
    if any(re.fullmatch(r"-?\d+,\d+", v) for v in vs) and not any(re.fullmatch(r"-?\d+\.\d+", v) for v in vs):
        return "comma"
    return "dot"


def to_number(v: str, style: str):
    t = re.sub(r"\s*(%|đ|vnd|vnđ|đồng|dong)$", "", str(v or "").strip(), flags=re.I)
    if not t:
        return None
    try:
        if style == "vi" and re.fullmatch(r"-?\d{1,3}(\.\d{3})*(,\d+)?|-?\d+(,\d+)?", t):
            x = float(t.replace(".", "").replace(",", "."))
        elif style == "comma" and re.fullmatch(r"-?\d+(,\d+)?", t):
            x = float(t.replace(",", "."))
        elif re.fullmatch(r"-?\d+(\.\d+)?", t):
            x = float(t)
        elif re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t):      # 1,234,567.5
            x = float(t.replace(",", ""))
        else:
            return None
    except ValueError:
        return None
    return int(x) if x.is_integer() else x


class Box:
    """Bảng SQLite phẳng của MỘT bảng đã biên dịch + mô tả cột cho model."""

    def __init__(self, t: dict, compiled: bool = True):
        self.t = t
        self.cols: list[dict] = []          # {sql, label, kind (num|text|year|flag), field, values (enum)}
        used: set = set()
        rows = t["rows"]
        for f, m in t["fields"].items():
            if m["type"] == "empty":
                continue
            vals = [str(r["fields"].get(f) or "") for r in rows]
            label = m.get("label") or f
            if not compiled:          # mốc "text-to-SQL KHÔNG qua bước biên dịch": mọi cột là chữ, tên cột nguyên văn, không giá trị mẫu
                self.cols.append({"sql": _ident(f, used), "label": f, "kind": "text", "field": f, "values": []})
                continue
            if m["type"] == "number":
                style = number_style(vals)
                nums = [to_number(v, style) for v in vals if v]
                ints = [x for x in nums if isinstance(x, int)]
                # cột năm mà vài ô ghi "tháng/năm" ("12/1994" giữa các ô "2012"): đọc năm của mọi ô, không để ô "12/1994" thành rỗng
                if nums and len(ints) >= 0.8 * len(nums) and all(1000 <= x <= 2100 for x in ints) and any(x is None for x in nums):
                    self.cols.append({"sql": _ident(label, used), "label": label, "kind": "year", "field": f})
                else:
                    self.cols.append({"sql": _ident(label, used), "label": label, "kind": "num", "field": f, "style": style})
            elif m["type"] == "flag":
                self.cols.append({"sql": _ident(label, used), "label": label, "kind": "flag", "field": f})
            else:
                distinct = sorted({v for v in vals if v})
                self.cols.append({"sql": _ident(label, used), "label": label, "kind": "text", "field": f,
                                  "values": distinct if (m["type"] == "enum" or len(distinct) <= 15) else []})
                yrs = [YEARISH.search(v) for v in vals if v]
                if yrs and sum(bool(y) for y in yrs) >= 0.8 * len(yrs) and not all(re.fullmatch(r"\d{4}", v) for v in vals if v):
                    self.cols.append({"sql": _ident(label + " năm", used), "label": f"năm trong «{label}»", "kind": "year", "field": f})
        if compiled:      # tiêu đề dòng kèm năm trong ngoặc ("Côn Đảo (1945)"): cột năm của tiêu đề
            ty = [YEARISH.search(r["title"]) for r in rows]
            if rows and sum(bool(y) for y in ty) >= 0.8 * len(rows):
                self.cols.append({"sql": _ident("ten nam", used), "label": f"năm trong «{t.get('title_label') or 'tên'}»", "kind": "title_year", "field": None})
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        defs = ["ten TEXT", "ten_kd TEXT"]
        for c in self.cols:
            typ = {"num": "REAL", "flag": "INTEGER", "year": "INTEGER", "title_year": "INTEGER"}.get(c["kind"], "TEXT")
            defs.append(f"{c['sql']} {typ}")
            if c["kind"] == "text":
                defs.append(f"{c['sql']}_kd TEXT")
        self.conn.execute(f"CREATE TABLE bang ({', '.join(defs)})")
        data = []
        for r in rows:
            rec = [r["title"], " ".join(re.findall(r"[a-z0-9]+", fold(r["title"])))]
            for c in self.cols:
                v = str(r["fields"].get(c["field"]) or "") if c["field"] else r["title"]
                if c["kind"] == "num":
                    rec.append(to_number(v, c["style"]))
                elif c["kind"] == "flag":
                    rec.append(1 if v.strip() else 0)
                elif c["kind"] in ("year", "title_year"):
                    y = YEARISH.findall(v)
                    rec.append(int(y[-1]) if y else None)
                else:
                    rec += [v or None, " ".join(re.findall(r"[a-z0-9]+", fold(v))) or None]
            data.append(tuple(rec))
        self.conn.executemany(f"INSERT INTO bang VALUES ({','.join('?' * len(data[0]))})", data) if data else None
        self.conn.commit()
        self.conn.execute("PRAGMA query_only=1")
        self.conn.set_authorizer(self._auth)
        self.lock = threading.Lock()
        self.bysql = {c["sql"]: c for c in self.cols}

    @staticmethod
    def _auth(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if arg1 == "bang" else sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in ("load_extension", "readfile", "writefile", "fts3_tokenizer"):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY

    # ------------------------------------------------------------------ model
    def prompt(self) -> str:
        noun = self.t.get("entity_noun") or "dòng"
        lines = [f"  ten TEXT -- {self.t.get('title_label') or 'tên'} (tên {noun})"]
        for c in self.cols:
            if c["kind"] == "num":
                ex = [str(to_number(str(r['fields'].get(c['field']) or ''), c['style'])) for r in self.t["rows"][:3] if r["fields"].get(c["field"])]
                lines.append(f"  {c['sql']} REAL -- {c['label']} (số; ví dụ {', '.join(ex)})")
            elif c["kind"] == "flag":
                lines.append(f"  {c['sql']} INTEGER -- {c['label']} (1 = có, 0 = không)")
            elif c["kind"] in ("year", "title_year"):
                lines.append(f"  {c['sql']} INTEGER -- {c['label']}")
            elif c["values"]:
                lines.append(f"  {c['sql']} TEXT -- {c['label']} (các giá trị: {' | '.join(v[:40] for v in c['values'][:15])})")
            else:
                ex = [str(r["fields"].get(c["field"]))[:40] for r in self.t["rows"][:2] if r["fields"].get(c["field"])]
                lines.append(f"  {c['sql']} TEXT -- {c['label']} (ví dụ: {' | '.join(ex)})")
        return ("Bạn viết MỘT câu SQLite SELECT trên MỘT bảng để trả lời câu hỏi. Không JOIN, không bảng nào khác.\n"
                f"Bảng bang (mỗi dòng là một {noun}, có {len(self.t['rows'])} dòng):\n" + "\n".join(lines) + "\n"
                "Quy tắc:\n"
                "- Đếm: SELECT COUNT(*) FROM bang WHERE ...\n"
                "- Liệt kê: SELECT ten FROM bang WHERE ... ORDER BY ten\n"
                "- Lớn nhất / nhỏ nhất: SELECT ten, <cột> FROM bang WHERE <cột> IS NOT NULL ORDER BY <cột> DESC (hoặc ASC) LIMIT 1\n"
                "- Tổng / trung bình: SELECT SUM(<cột>) FROM bang WHERE ...  (AVG cho trung bình)\n"
                "- Lọc theo chữ: <cột> LIKE '%chữ%' (chép chữ như trong câu hỏi). Lọc theo giá trị trong danh sách: <cột> = '<giá trị chép đúng>'.\n"
                "- So sánh số dùng cột số (REAL): '> 1000', '< 50'. Năm dùng cột năm.\n"
                "- Chỉ trả JSON {\"sql\": \"...\"}.\n"
                "Ví dụ (bảng khác, chỉ để xem cách viết): 'có mấy cửa hàng ở Hà Nội' -> SELECT COUNT(*) FROM bang WHERE tinh LIKE '%Hà Nội%'; "
                "'cửa hàng nào doanh thu cao nhất' -> SELECT ten, doanh_thu FROM bang WHERE doanh_thu IS NOT NULL ORDER BY doanh_thu DESC LIMIT 1; "
                "'tổng số nhân viên của các cửa hàng loại A' -> SELECT SUM(so_nhan_vien) FROM bang WHERE loai = 'A'")

    def rewrite(self, sql: str, like_mode: str = "word") -> str:
        """Chuẩn hoá câu model viết: lọc chữ trên bản bỏ dấu (model bỏ dấu hay sai, người dùng gõ không dấu); bỏ danh từ chỉ loại dòng ở đầu
        mẫu LIKE ("di tích khảo cổ" -> "khảo cổ": mọi dòng đều là di tích); "= 'giá trị'" không có trong cột -> tìm chứa ("= 'Huế'" khi cột
        ghi "Đại học Huế"). like_mode: "word" khớp nguyên âm tiết ("nhi" không khớp "nhiet"); "substr" khớp chuỗi con (model cắt cụt chữ cuối:
        "thế giớ"); "title" chuyển mọi LIKE sang cột tên. Hai chế độ sau là lần thử lại khi lọc ra 0 dòng. Gọi khi đang giữ self.lock."""
        s = re.sub(r"^```(?:sql)?|```$", "", (sql or "").strip(), flags=re.I).strip()
        s = re.sub(r"[\s;}]+$", "", s)
        noun = " ".join(re.findall(r"[a-z0-9]+", fold(self.t.get("entity_noun") or "")))

        def like(m):
            col, neg, pat = m.group(1), m.group(2) or "", m.group(3)
            tgt = "ten_kd" if col == "ten" or like_mode == "title" else (f"{col}_kd" if col in self.bysql and self.bysql[col]["kind"] == "text" else col)
            core = "%".join(" ".join(re.findall(r"[a-z0-9_]+", fold(p))) for p in pat.strip("%").split("%"))
            if noun and core.startswith(noun + " "):
                core = core[len(noun) + 1:]
            if like_mode != "substr" and pat.startswith("%") and pat.endswith("%") and core and tgt.endswith("_kd"):
                return f"(' ' || {tgt} || ' ') {neg}LIKE '% {core} %'"
            return f"{tgt} {neg}LIKE '{'%' if pat.startswith('%') else ''}{core}{'%' if pat.endswith('%') else ''}'"
        s = re.sub(r"(?i)\b([a-z_][a-z0-9_]*)\s+(NOT\s+)?LIKE\s+'([^']*)'", like, s)

        def eq(m):       # cột chữ = 'giá trị': so không phân biệt hoa thường / dấu
            col, val = m.group(1), m.group(2)
            kd = "ten_kd" if col == "ten" else (f"{col}_kd" if col in self.bysql and self.bysql[col]["kind"] == "text" else None)
            if not kd:
                return m.group(0)
            v = " ".join(re.findall(r"[a-z0-9]+", fold(val)))
            if v and self.conn.execute(f"SELECT 1 FROM bang WHERE {kd} = ? LIMIT 1", (v,)).fetchone() is None:
                return f"{kd} LIKE '%{v}%'"
            return f"{kd} = '{v}'"
        return re.sub(r"(?i)\b([a-z_][a-z0-9_]*)\s*=\s*'([^']*)'", eq, s)

    def run(self, sql: str, max_steps: int = 2_000_000, like_mode: str = "word") -> tuple[list[str], list[tuple]]:
        steps = [0]

        def tick():
            steps[0] += 1
            return 1 if steps[0] * 1000 > max_steps else 0
        with self.lock:
            s = self.rewrite(sql, like_mode)
            if not re.match(r"(?is)^(select|with)\b", s):
                raise ValueError("chỉ được dùng SELECT")
            if ";" in s:
                raise ValueError("chỉ được một câu lệnh")
            self.conn.set_progress_handler(tick, 1000)
            try:
                cur = self.conn.execute(f"SELECT * FROM ({s}) LIMIT {MAX_ROWS}")
                return [d[0] for d in cur.description], cur.fetchall()
            finally:
                self.conn.set_progress_handler(None, 0)

    # ------------------------------------------------------------------ trả lời bằng code
    def render(self, sql: str, names: list[str], rows: list[tuple], question: str) -> dict | None:
        noun = self.t.get("entity_noun") or "mục"
        su = sql.upper()
        fq = fold(question)
        if not rows:
            return {"kind": "list", "count": 0, "titles": [], "text": f"Không có {noun} nào thỏa điều kiện trong {len(self.t['rows'])} {noun}."}
        if len(rows) == 1 and len(names) == 1 and isinstance(rows[0][0], (int, float)) and re.search(r"\bCOUNT\s*\(", su):
            n = int(rows[0][0])
            return {"kind": "count", "count": n, "titles": [], "text": f"Có **{n}** {noun} thỏa điều kiện (trên tổng {len(self.t['rows'])} {noun})."}
        agg = re.search(r"\b(SUM|AVG|MAX|MIN|TOTAL)\s*\(\s*([a-z0-9_]+)?", su, re.I)
        if len(rows) == 1 and len(names) == 1 and agg and isinstance(rows[0][0], (int, float)):
            col = self.bysql.get((agg.group(2) or "").lower())
            what = {"SUM": "Tổng", "TOTAL": "Tổng", "AVG": "Trung bình", "MAX": "Lớn nhất", "MIN": "Nhỏ nhất"}[agg.group(1).upper()]
            return {"kind": "value", "count": None, "titles": [], "value": rows[0][0],
                    "text": f"{what} {col['label'] if col else ''}: **{fmt(rows[0][0])}**."}
        ti = next((i for i, n in enumerate(names) if n.lower() == "ten"), None)
        if ti is None:
            return None
        titles = list(dict.fromkeys(str(r[ti]) for r in rows if r[ti] is not None))
        others = [(i, n) for i, n in enumerate(names) if i != ti]
        if len(rows) == 1 and others and SUPER.search(fq):
            i, n = others[0]
            col = self.bysql.get(n.lower())
            return {"kind": "row", "count": 1, "titles": titles,
                    "text": f"**{titles[0]}**" + (f" ({col['label'] if col else n}: {fmt(rows[0][i])})" if rows[0][i] is not None else "") + "."}
        more = len(titles) - SHOW
        body = "\n".join(f"- {x}" + (" (" + ", ".join(f"{(self.bysql.get(n.lower()) or {}).get('label', n)}: {fmt(r[i])}" for i, n in others if r[i] is not None) + ")"
                                     if others and len(titles) <= SHOW else "") for x, r in zip(titles[:SHOW], rows[:SHOW]))
        tail = f"\n- … và {more} {noun} khác" if more > 0 else ""
        return {"kind": "list", "count": len(titles), "titles": titles, "text": f"Có **{len(titles)}** {noun}:\n{body}{tail}"}


def fmt(v) -> str:
    if isinstance(v, float) and not v.is_integer():
        s = f"{v:,.2f}".rstrip("0").rstrip(".")
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(v, (int, float)):
        n = int(v)
        return f"{n:,}".replace(",", ".") if abs(n) >= 10000 else str(n)
    return str(v)


def wants(text: str) -> bool:
    return bool(WANTS.search(" " + " ".join(re.findall(r"[a-z0-9.,]+", fold(text or ""))) + " "))


def answer(box: Box, text: str, chat_json) -> dict | None:
    """-> {"text", "sql", "kind", "count", "titles", "tries"} hoặc None."""
    system, user, err = box.prompt(), f"Câu hỏi: {text}", ""
    for attempt in (1, 2):
        try:
            out = chat_json([{"role": "system", "content": system},
                             {"role": "user", "content": user + (f"\nCâu SQL trước bị lỗi: {err}. Viết lại cho đúng." if err else "")}],
                            SCHEMA, timeout=60)
        except Exception:      # noqa: BLE001 - model lỗi / hết giờ: nhường đường khác
            return None
        sql = str((out or {}).get("sql") or "")
        try:
            names, rows = box.run(sql)
        except (ValueError, sqlite3.Error) as e:
            err = f"{type(e).__name__}: {e}"[:200]
            continue
        res = box.render(sql, names, rows, text)
        if res and res.get("count") == 0 and re.search(r"(?i)\bLIKE\b", sql):
            # lọc chữ ra 0 dòng: model cắt cụt chữ cuối -> khớp chuỗi con; chữ nằm trong TÊN dòng ("bệnh viện nhi" -> "Bệnh viện Nhi đồng 1") -> cột tên
            modes = ["substr"] + ([] if re.search(r"(?i)\bten\s+(NOT\s+)?LIKE\b", sql) else ["title"])
            for mode in modes:
                try:
                    n2, r2 = box.run(sql, like_mode=mode)
                except (ValueError, sqlite3.Error):
                    continue
                alt = box.render(sql, n2, r2, text)
                if alt and alt.get("count"):
                    res = alt
                    break
        if res is None:
            err = "kết quả phải có cột ten (liệt kê) hoặc một con số (đếm / tổng)"
            continue
        return {**res, "sql": sql, "tries": attempt}
    return None

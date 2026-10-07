"""Đọc tệp người dùng tải lên và đổi sang CẤU TRÚC ĐỊNH SẴN (NV3, 4A: không cần người dùng xác nhận).

Một bản ghi = {title, fields {tên trường: giá trị}, text (chữ để tìm), source (tệp · trang tính · dòng / trang)}.
- Bảng (CSV, Excel, JSON danh sách, bảng trong Word): code chọn cột tiêu đề, AI kiểm lại, code duyệt.
  Không khớp được -> phương án C: mỗi dòng thành một đoạn chữ "cột: giá trị; …" (kind = rows).
- Văn bản (TXT/MD, đoạn văn Word, PDF): chia theo tiêu đề / đoạn, mỗi phần ~CHUNK_CHARS ký tự (kind = text).
"""
from __future__ import annotations
import csv
import datetime
import io
import json
import re
from pathlib import Path

from . import llm, settings

READER_VERSION = 2   # tăng khi đổi cách đọc tệp: dữ liệu đọc bằng bản cũ được xử lý lại khi khởi động server
csv.field_size_limit(2**31 - 1)   # ô rất dài (mô tả, văn bản dán vào) không làm hỏng việc đọc CSV
SUPPORTED = {".csv", ".tsv", ".xlsx", ".xlsm", ".json", ".txt", ".md", ".docx", ".pdf"}
_TITLE_HINTS = ("tên", "ten", "name", "title", "tiêu đề", "tieu de", "sản phẩm", "san pham", "thủ tục", "thu tuc", "mặt hàng",
                "câu hỏi", "cau hoi", "question", "chủ đề", "chu de", "dịch vụ", "dich vu", "họ tên", "ho ten", "mục", "item")


class IngestError(Exception):
    pass


# ------------------------------------------------------------------ đọc tệp
def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()[:10] if isinstance(v, datetime.datetime) and not (v.hour or v.minute) else v.isoformat()
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return " ".join(str(v).split())


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16") if data[:2] in (b"\xff\xfe", b"\xfe\xff") else ("utf-8-sig", "cp1258", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def read(path: Path) -> list[tuple]:
    """Trả danh sách phần: ("table", tên, rows[list[list[str]]]) hoặc ("text", tiêu đề, chữ, nguồn)."""
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise IngestError(f"Chưa hỗ trợ tệp {ext or 'không có đuôi'}. Hỗ trợ: CSV, Excel (.xlsx), JSON, TXT/MD, Word (.docx), PDF.")
    if ext in (".csv", ".tsv"):
        text = _decode(path.read_bytes())
        try:
            dialect = csv.Sniffer().sniff(text[:20000], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel_tab if ext == ".tsv" else csv.excel
        return [("table", path.stem, [[_cell(c) for c in r] for r in csv.reader(io.StringIO(text), dialect)])]
    if ext in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        out = [("table", ws.title, [[_cell(c) for c in row] for row in ws.iter_rows(values_only=True)]) for ws in wb.worksheets]
        wb.close()
        return out
    if ext == ".json":
        try:
            data = json.loads(_decode(path.read_bytes()))
        except ValueError as e:
            raise IngestError(f"Tệp JSON hỏng: {e}") from None
        if isinstance(data, dict):
            lst = next((v for v in data.values() if isinstance(v, list) and v and isinstance(v[0], dict)), None)
            data = lst if lst is not None else data
        if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
            keys = list(dict.fromkeys(k for x in data for k in x))
            return [("table", path.stem, [keys] + [[_cell(x.get(k)) for k in keys] for x in data])]
        return [("text", path.stem, json.dumps(data, ensure_ascii=False, indent=1), path.name)]
    if ext in (".txt", ".md"):
        return _sections(_decode(path.read_bytes()), path.name, markdown=True)
    if ext == ".docx":
        import docx
        d = docx.Document(str(path))
        out, title, buf = [], path.stem, []
        body = d.element.body
        tables = {t._tbl: t for t in d.tables}
        paras = {p._p: p for p in d.paragraphs}
        for child in body.iterchildren():
            if child in paras:
                p = paras[child]
                if (p.style.name or "").lower().startswith(("heading", "title")) and p.text.strip():
                    if buf:
                        out.append(("text", title, "\n".join(buf), path.name)); buf = []
                    title = p.text.strip()
                elif p.text.strip():
                    buf.append(p.text.strip())
            elif child in tables:
                rows = [[_cell(c.text) for c in r.cells] for r in tables[child].rows]
                if len(rows) >= 2:
                    out.append(("table", f"{path.stem} · bảng {sum(1 for x in out if x[0] == 'table') + 1}", rows))
        if buf:
            out.append(("text", title, "\n".join(buf), path.name))
        return out
    if ext == ".pdf":
        from pypdf import PdfReader
        try:
            reader = PdfReader(str(path))
        except Exception as e:
            raise IngestError(f"Không đọc được PDF: {e}") from None
        out = []
        for i, page in enumerate(reader.pages, 1):
            t = (page.extract_text() or "").strip()
            if t:
                out.append(("text", f"{path.stem} · trang {i}", t, f"{path.name} · trang {i}"))
        if not out:
            raise IngestError("PDF không có chữ (có thể là ảnh quét). Hiện chỉ hỗ trợ PDF có chữ.")
        return out
    raise IngestError("Định dạng không hỗ trợ")


def _sections(text: str, source: str, markdown: bool) -> list[tuple]:
    """Chia văn bản theo tiêu đề Markdown (#) nếu có; không có thì để một phần, việc chia đoạn làm ở bước sau."""
    out, title, buf = [], Path(source).stem, []
    for line in text.splitlines():
        m = re.match(r"^\s{0,3}#{1,6}\s+(.+)$", line) if markdown else None
        if m:
            if "".join(buf).strip():
                out.append(("text", title, "\n".join(buf).strip(), source))
            title, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        out.append(("text", title, "\n".join(buf).strip(), source))
    return out


# --------------------------------------------------------- bảng -> bản ghi
def _numeric(v: str) -> bool:
    return bool(re.fullmatch(r"[\d\s.,%:/\-+đ₫$]*", v or ""))


def _header_index(rows: list[list[str]]) -> int | None:
    """Dòng tiêu đề cột = dòng ĐẦU TIÊN (trong 15 dòng đầu) mà các ô là nhãn chữ ngắn và phủ >= một nửa số cột.
    Dòng tên bảng / ghi chú phía trên (vd. "DANH SÁCH HỌC SINH LỚP ..." chỉ chiếm vài ô) bị bỏ qua.
    Gặp dòng toàn số trước khi thấy tiêu đề -> bảng không có tiêu đề cột."""
    width = max((sum(1 for c in r if c) for r in rows[:30]), default=0)
    fallback = None
    for i, r in enumerate(rows[:15]):
        filled = [c for c in r if c]
        if len(filled) < 2:
            continue
        labels = [c for c in filled if not _numeric(c) and len(c) <= 60]
        if len(labels) < max(2, len(filled) * 0.6):
            return fallback   # dòng dữ liệu (nhiều số) -> dừng
        if len(filled) >= width * 0.5:
            return i
        fallback = i if fallback is None else fallback
    return fallback


def _norm(h: str) -> str:
    return " ".join(_strip(h).lower().split())


def _strip(t: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t or "") if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D")


def _name_pair(headers: list[str]) -> tuple[int, int] | None:
    """Danh sách người kiểu Việt Nam hay tách "Họ và tên" thành 2 cột: họ + tên đệm | tên. Trả (cột họ, cột tên)."""
    for i in range(len(headers) - 1):
        if _norm(headers[i + 1]) == "ten" and _norm(headers[i]).startswith(("ho", "cot")):
            return i, i + 1
    return None


def _clean_table(rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return [], []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    hi = _header_index(rows)
    if hi is None:
        headers, data = [f"Cột {i + 1}" for i in range(width)], rows
    else:
        headers, data = rows[hi], rows[hi + 1:]
        headers = [h or ("Họ và tên đệm" if i + 1 < width and _norm(headers[i + 1]) == "ten" else f"Cột {i + 1}")
                   for i, h in enumerate(headers)]   # cột không nhãn ngay trước cột "Tên" = phần họ và tên đệm
        seen = {}
        for i, h in enumerate(headers):   # tên cột trùng -> thêm số
            if h in seen:
                seen[h] += 1; headers[i] = f"{h} ({seen[h]})"
            else:
                seen[h] = 1
    keep = [i for i in range(width) if sum(1 for r in data if r[i]) > max(0, len(data) * 0.02)]
    return [headers[i] for i in keep], [[r[i] for i in keep] for r in data]


def _title_score(header: str, values: list[str]) -> float:
    vals = [v for v in values if v]
    if not vals or len(vals) < len(values) * 0.6:
        return -1
    if sum(_numeric(v) for v in vals) > len(vals) * 0.5:
        return -1
    avg = sum(len(v) for v in vals) / len(vals)
    spaced = sum(" " in v for v in vals) / len(vals)
    if (spaced < 0.3 and avg > 15) or sum(v.startswith(("http://", "https://")) for v in vals) > len(vals) * 0.3:
        return -1   # mã, chuỗi băm, đường dẫn: duy nhất nhưng không phải tiêu đề
    uniq = len(set(vals)) / len(vals)
    s = uniq * 2 + (1 if 3 <= avg <= 150 else -1)
    if any(h in header.lower() for h in _TITLE_HINTS):
        s += 2
    return s


def _ai_title(headers: list[str], data: list[list[str]], guess: str | None) -> str | None:
    """AI kiểm lại lựa chọn cột tiêu đề (chế độ JSON, ~1 giây). Lỗi/không hợp lệ -> None."""
    sample = "\n".join(" | ".join(r) for r in data[:4])
    out = llm.chat_json([
        {"role": "system", "content": "Bạn chọn cột TIÊU ĐỀ cho một bảng dữ liệu: cột mô tả mỗi dòng là cái gì (tên sản phẩm, tên thủ tục, câu hỏi...). "
                                      "Chỉ chọn một tên cột có trong danh sách. Không có cột nào phù hợp thì để chuỗi rỗng."},
        {"role": "user", "content": f"Các cột: {headers}\nGợi ý của code: {guess or '(không có)'}\nVài dòng mẫu:\n{sample}"}],
        {"type": "object", "properties": {"title_column": {"type": "string"}}, "required": ["title_column"]}, timeout=30)
    t = str(out.get("title_column", "")).strip()
    return t if t in headers else None


def table_records(name: str, rows: list[list[str]], filename: str, use_ai: bool = True) -> tuple[list[dict], dict]:
    headers, data = _clean_table(rows)
    if not data:
        return [], {"kind": "empty"}
    if len(headers) == 1:   # một cột: là ghi chú/văn bản (câu dài) thì coi như văn bản
        vals = [headers[0]] + [r[0] for r in data]
        if sum(len(v) for v in vals) / len(vals) > 40 or headers[0].startswith("Cột"):
            recs = text_records(name, "\n\n".join(vals), f"{filename} · {name}")
            return recs, {"kind": "text", "title": name, "chunks": len(recs)}
    scores = {h: _title_score(h, [r[i] for r in data[:500]]) for i, h in enumerate(headers)}
    guess = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else None
    title = (_ai_title(headers, data, guess) if use_ai else None) or guess
    if title and scores.get(title, -1) < 0:   # AI chọn cột không dùng được (trống / toàn số): giữ lựa chọn của code
        title = guess
    recs = []
    pair = _name_pair(headers)
    if title and pair and headers.index(title) in pair:   # tiêu đề = họ tên đầy đủ (ghép 2 cột)
        title_label = f"{headers[pair[0]]} + {headers[pair[1]]}"
    else:
        pair, title_label = None, title
    if title:
        ti = headers.index(title)
        for n, r in enumerate(data, 1):
            fields = {h: v for h, v in zip(headers, r) if v and h != title}
            t = (" ".join(x for x in (r[pair[0]], r[pair[1]]) if x) if pair else r[ti]) or f"Dòng {n}"
            if pair:
                fields = {h: v for h, v in zip(headers, r) if v}
            recs.append({"title": t[:300], "fields": fields,
                         "text": t + "\n" + "\n".join(f"{k}: {v}" for k, v in fields.items()),
                         "source": f"{filename} · {name} · dòng {n}"})
        return recs, {"kind": "table", "title_column": title_label, "fields": [h for h in headers if h != title], "sheet": name}
    for n, r in enumerate(data, 1):   # phương án C: không có cột tiêu đề dùng được
        fields = {h: v for h, v in zip(headers, r) if v}
        recs.append({"title": f"{name} · dòng {n}", "fields": fields,
                     "text": "; ".join(f"{k}: {v}" for k, v in fields.items()), "source": f"{filename} · {name} · dòng {n}"})
    return recs, {"kind": "rows", "sheet": name, "fields": headers}


def text_records(title: str, text: str, source: str) -> list[dict]:
    """Chia văn bản thành đoạn ~CHUNK_CHARS ký tự theo đoạn văn, gối đầu một đoạn để không mất ý ở chỗ cắt."""
    size = settings.get("CHUNK_CHARS")
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=[-*•]\s)", text) if p.strip()]
    pieces, buf = [], []
    for p in paras:
        while len(p) > size * 1.5:   # đoạn quá dài: cắt theo câu
            cut = p.rfind(". ", 0, size)
            cut = cut + 1 if cut > size * 0.5 else size
            paras_head, p = p[:cut].strip(), p[cut:].strip()
            if buf:
                pieces.append("\n".join(buf)); buf = []
            pieces.append(paras_head)
        if buf and sum(len(x) for x in buf) + len(p) > size:
            pieces.append("\n".join(buf))
            buf = [buf[-1]] if len(buf[-1]) < size * 0.4 else []
        buf.append(p)
    if buf:
        pieces.append("\n".join(buf))
    multi = len(pieces) > 1
    return [{"title": f"{title} (phần {i})" if multi else title, "fields": {}, "text": t, "source": source}
            for i, t in enumerate(pieces, 1)]


def to_records(path: Path, filename: str, use_ai: bool = True) -> tuple[list[dict], dict]:
    """Tệp -> (bản ghi theo cấu trúc định sẵn, mô tả cách đã khớp)."""
    recs, maps = [], []
    for part in read(path):
        if part[0] == "table":
            r, m = table_records(part[1], part[2], filename, use_ai)
            if r:
                recs += r; maps.append(m if m["kind"] != "text" else {"kind": "text", "title": m["title"], "chunks": m["chunks"]})
        else:
            r = text_records(part[1], part[2], part[3])
            if r:
                recs += r; maps.append({"kind": "text", "title": part[1], "chunks": len(r)})
    if not recs:
        raise IngestError("Không tìm thấy nội dung nào trong tệp.")
    kinds = {m["kind"] for m in maps}
    kind = "table" if kinds == {"table"} else ("text" if kinds == {"text"} else ("rows" if kinds == {"rows"} else "mixed"))
    return recs, {"kind": kind, "parts": maps, "reader": READER_VERSION}


def describe(mapping: dict, n: int) -> str:
    """Câu mô tả cho người dùng: đã khớp cấu trúc thế nào."""
    parts = mapping.get("parts", [])
    tables = [m for m in parts if m["kind"] == "table"]
    rows = [m for m in parts if m["kind"] == "rows"]
    texts = [m for m in parts if m["kind"] == "text"]
    out = []
    if tables:
        out.append("Bảng: cột tiêu đề " + ", ".join(f"\"{m['title_column']}\"" for m in tables[:3])
                   + f" ({sum(len(m['fields']) for m in tables)} trường)")
    if rows:
        out.append(f"{len(rows)} bảng không khớp được cột tiêu đề, lưu dạng dòng chữ")
    if texts:
        out.append(f"Văn bản: {sum(m['chunks'] for m in texts)} đoạn")
    return "; ".join(out) + f" · {n} bản ghi"

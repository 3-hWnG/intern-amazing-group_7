"""raw/ (fetch.py) -> data/: 6 tệp dữ liệu THẬT cho 3 lĩnh vực mềm, mỗi lĩnh vực 1 bảng (đường nhanh) + 1 văn bản (tìm kiếm + AI).

    python system4/eval/real_domains/build.py

  Y tế      y_te_benh_vien_tphcm.xlsx      bệnh viện tại TP.HCM (Wikipedia)              y_te_hoi_dap_bac_si.md      300 câu hỏi thật + bác sĩ trả lời
  Giáo dục  giao_duc_truong_dai_hoc.xlsx   trường đại học, học viện (Wikipedia)          giao_duc_luat_giao_duc_2019.txt   toàn văn Luật Giáo dục 2019
  Du lịch   du_lich_di_tich_dac_biet.xlsx  di tích quốc gia đặc biệt (Wikipedia)         du_lich_diem_den.md         6 bài Wikipedia về điểm đến
Chỉ đổi định dạng + làm sạch (bỏ chú thích [1], toạ độ, lời chào, quảng cáo; che SĐT / email / tên người hỏi); KHÔNG thêm, KHÔNG sửa số liệu.
Nguồn, phiên bản (revid), giấy phép: SOURCES.md (build.py ghi lại phần "phiên bản" vào data/manifest.json).
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from lxml import html

HERE = Path(__file__).resolve().parent
RAW, OUT = HERE / "raw", HERE / "data"
REF = re.compile(r"\[(\d+|[a-z]|cần dẫn nguồn|liên kết hỏng|chú thích \d+|ghi chú \d+)\]")


def load(name: str) -> dict:
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def clean(s: str) -> str:
    return " ".join(REF.sub("", s or "").split()).strip(" ;,")


def _txt(el) -> str:
    for br in el.xpath(".//br"):   # "Khu trung tâm<br>Hoàng thành" -> có dấu cách
        br.tail = " " + (br.tail or "")
    for bad in el.xpath(".//sup|.//style|.//link|.//*[contains(@class,'geo') or contains(@class,'reference') or contains(@class,'noprint')]"):
        bad.drop_tree()
    return clean(el.text_content())


def tables(doc) -> list[tuple[dict, list[list[str]]]]:
    """Mọi wikitable trong trang: ({h2, h3, h4} của mục chứa bảng, lưới ô đã trải rowspan / colspan)."""
    out, heads = [], {"h2": "", "h3": "", "h4": ""}
    for el in doc.iter():
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag in ("h2", "h3", "h4"):
            heads[tag] = clean(el.text_content())
            for lower in ("h3", "h4")[("h2", "h3", "h4").index(tag):]:
                if lower != tag:
                    heads[lower] = ""
        elif tag == "table" and "wikitable" in (el.get("class") or ""):
            grid: list[list[str]] = []
            spill: dict[tuple[int, int], str] = {}
            for r, tr in enumerate(el.xpath("./tr|./tbody/tr|./thead/tr")):
                row, c = [], 0
                cells = tr.xpath("./th|./td")
                k = 0
                while k < len(cells) or (r, c) in spill:
                    if (r, c) in spill:
                        row.append(spill.pop((r, c)))
                        c += 1
                        continue
                    cell = cells[k]
                    k += 1
                    v = _txt(cell)
                    rs, cs = int(re.sub(r"\D", "", cell.get("rowspan") or "1") or 1), int(re.sub(r"\D", "", cell.get("colspan") or "1") or 1)
                    for j in range(cs):
                        row.append(v)
                        for i in range(1, rs):
                            spill[(r + i, c + j)] = v
                    c += cs
                grid.append(row)
            out.append((dict(heads), grid))
    return out


def as_dicts(grid: list[list[str]]) -> list[dict]:
    head = grid[0]
    return [{h: (r[i] if i < len(r) else "") for i, h in enumerate(head)} for r in grid[1:] if any(r)]


def write_xlsx(path: Path, sheet: str, cols: list[str], rows: list[dict]) -> int:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(cols)
    for r in rows:
        ws.append([r.get(c, "") for c in cols])
    OUT.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))
    return len(rows)


# ------------------------------------------------------------------ Y tế
def benh_vien() -> int:
    raw = load("wiki_benh_vien_hcm.json")
    rows = []
    group = {"trực thuộc bộ": "Trực thuộc bộ, ngành (trung ương)", "bệnh viện đại học": "Bệnh viện đại học",
             "trung tâm y tế công lập": "Công lập của thành phố", "tư nhân": "Tư nhân"}
    for heads, grid in tables(html.fromstring(raw["html"])):
        g = next((v for k, v in group.items() if k in heads["h2"].lower()), heads["h2"])
        for r in as_dicts(grid):
            name = r.get("Tên bệnh viện", "")
            if not name:
                continue
            rows.append({"Tên bệnh viện": name, "Tên khác": r.get("Tên khác", ""), "Nhóm": g, "Năm thành lập": r.get("Năm thành lập", ""),
                         "Loại bệnh viện": r.get("Loại bệnh viện", ""), "Cơ sở (phường / quận)": r.get("Cơ sở") or r.get("Trụ sở", ""),
                         "Số giường": r.get("Số giường", ""), "Tuyến khám chữa bệnh BHYT": r.get("Tuyến KCB theo BHYT") or r.get("Phân tuyến", ""),
                         "Cấp chuyên môn kỹ thuật": next((v for k, v in r.items() if k.startswith("Cấp chuyên môn")), ""),
                         "Cơ quan chủ quản / chủ sở hữu": r.get("Cơ quan chủ quản") or r.get("Chủ sở hữu", ""),
                         "Website": r["Website"] if re.fullmatch(r"(https?://)?[\w.-]+\.[a-z]{2,}(/\S*)?", r.get("Website", "")) else "",
                         "Ghi chú": r.get("Ghi chú", "")})
    cols = list(rows[0])
    return write_xlsx(OUT / "y_te_benh_vien_tphcm.xlsx", "Bệnh viện TP.HCM", cols, rows)


GREET = re.compile(r"^\s*(chào|xin chào|thưa|kính gửi|kính chào|dear)\b[^\n]{0,40}$", re.I)
ADS = re.compile(r"hotline|đặt lịch|myvinmec|vinmec\.com|ứng dụng|tổng đài|website|liên hệ (với )?(chúng tôi|bệnh viện)|edoctor|đăng ký khám|trân trọng|thân ái", re.I)
BOILER = re.compile(r"^(để trả lời câu hỏi (trên|của bạn)[^:]*:|bác sĩ xin (được )?(giải đáp|trả lời|tư vấn)[^:]*:|cảm ơn (bạn|em|anh|chị) đã (gửi|tin tưởng)[^.]*\.)\s*", re.I)
PHONE = re.compile(r"(\+?84|0)[\d .-]{8,12}\d")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
NAME = re.compile(r"\b(tên (là|em là|cháu là|tôi là)?|tôi là|em là|cháu là)\s+([A-ZĐÂĂÊÔƠƯ][\wÀ-ỹ]*)(\s+[A-ZĐÂĂÊÔƠƯ][\wÀ-ỹ]*){0,3}")


def _mask(s: str) -> str:
    s = EMAIL.sub("[EMAIL]", PHONE.sub("[SĐT]", s))
    return NAME.sub(lambda m: m.group(1) + " [TÊN]", s)


def _clean_q(q: str) -> str:
    lines = [ln.strip() for ln in q.replace("\r", "").split("\n") if ln.strip()]
    while lines and GREET.match(lines[0]):
        lines = lines[1:]
    return _mask("\n".join(lines))


def _clean_a(a: str) -> str:
    lines = [ln.strip() for ln in a.replace("\r", "").split("\n") if ln.strip()]
    while lines and GREET.match(lines[0]):
        lines = lines[1:]
    out = []
    for ln in lines:
        ln = BOILER.sub("", ln).strip()
        if not ln or ADS.search(ln) and len(ln) < 400:
            continue
        out.append(ln)
    return _mask("\n".join(out))


def _heading(q: str) -> str:
    """Câu hỏi chính (câu có dấu ?), gọn <= 110 ký tự — làm tiêu đề mục của cặp hỏi đáp."""
    flat = " ".join(q.split())
    sents = re.split(r"(?<=[.?!])\s+", flat)
    s = next((x for x in sents if x.endswith("?")), sents[0])
    lead = re.compile(r"^(vậy thì|vậy|xin|thưa|nhờ|bác sĩ|bs|ơi|ạ|cho (em|cháu|tôi|mình|con|chị|anh) (được |xin )?hỏi( là)?|[,:])\s*", re.I)
    while True:   # "Vậy bác sĩ cho em hỏi …" -> "…"
        t = lead.sub("", s, count=1)
        if t == s:
            break
        s = t
    s = s.strip() or flat[:90]
    s = s[:1].upper() + s[1:]
    if len(s) > 110:
        s = s[:110].rsplit(" ", 1)[0] + "…"
    return s


def hoi_dap(n: int = 300, seed: int = 19) -> int:
    raw = load("medqa_rows.json")
    pool, seen = [], set()
    for r in raw["rows"]:
        q, a = _clean_q(r["question"]), _clean_a(r["answer"])
        key = " ".join(q.lower().split())[:80]
        if not (60 <= len(q) <= 700 and 250 <= len(a) <= 1800) or key in seen or "?" not in q:
            continue
        seen.add(key)
        pool.append((r["row_idx"], q, a))
    pick = sorted(random.Random(seed).sample(pool, min(n, len(pool))))
    parts = ["# Hỏi đáp sức khoẻ: câu hỏi thật của người dân, bác sĩ trả lời",
             "Nguồn: bộ dữ liệu hungnm/vietnamese-medical-qa (Apache-2.0), gốc từ chuyên mục hỏi đáp bác sĩ của edoctor.io và vinmec.com. "
             "Thông tin chỉ để tham khảo, không thay cho khám và chẩn đoán trực tiếp."]
    for idx, q, a in pick:
        parts.append(f"## {_heading(q)}\nNgười hỏi: {q}\n\nBác sĩ trả lời: {a}\n\n(Câu số {idx} trong bộ dữ liệu gốc)")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "y_te_hoi_dap_bac_si.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return len(pick)


# ------------------------------------------------------------------ Giáo dục
def truong_dai_hoc() -> int:
    raw = load("wiki_truong_dai_hoc.json")
    rows, seen = [], set()
    for heads, grid in tables(html.fromstring(raw["html"])):
        h2, h3, h4 = heads["h2"].lower(), heads["h3"], heads["h4"]
        if "dự bị" in h2 or "cao đẳng" in h2 and "học viện" not in h2:
            continue   # chỉ đại học / học viện
        for r in as_dicts(grid):
            g = lambda *ks: next((r[k] for k in r for p in ks if k.startswith(p) and r[k]), "")
            name = g("Đơn vị trực thuộc", "Đơn vị thành viên", "Tên trường") or g("Đại học")
            if not name or name.startswith(("STT", "Tên trường")):
                continue
            if "cơ sở giáo dục đại học" in h2:
                parent = g("Đại học") if g("Đơn vị trực thuộc") else h4
                owner = g("Đơn vị quản lý") or ("Đại học tư thục" if "tư thục" in h3.lower() else h3)
            elif "trực thuộc tỉnh" in h2:
                parent, owner = "", "UBND " + g("UBND") if g("UBND") else "UBND tỉnh / thành phố"
            elif "quân sự" in h2:
                parent, owner = "", "Bộ Quốc phòng" if h3 == "Quân sự" else "Bộ Công an"
            elif "nước ngoài" in h2:
                parent, owner = "", g("Quốc gia")
            else:
                parent, owner = g("Trực thuộc"), h3
            kind = "Tư thục" if "tư thục" in (h2 + " " + h3).lower() else "Nước ngoài" if "nước ngoài" in h2 else "Công lập"
            key = (name.lower(), parent.lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append({"Tên trường": name, "Viết tắt": g("Viết tắt"), "Giao dịch tiếng Anh": g("Tên giao dịch", "Tên tiếng Anh"),
                         "Địa điểm": g("Địa điểm", "Trụ sở chính", "Trụ sở", "UBND"), "Thuộc đại học": parent,
                         "Cơ quan chủ quản": owner, "Loại hình": kind, "Nhóm (theo Wikipedia)": heads["h2"]})
    return write_xlsx(OUT / "giao_duc_truong_dai_hoc.xlsx", "Trường đại học", list(rows[0]), rows)


def luat_giao_duc() -> int:
    raw = load("luat_giao_duc_2019.json")
    doc = html.fromstring(raw["html"])
    for b in doc.xpath("//script|//style"):
        b.drop_tree()
    from collections import Counter
    box = Counter(p.getparent() for p in doc.xpath("//p")).most_common(1)[0][0]   # khối chứa toàn văn
    lines = [" ".join(p.text_content().split()) for p in box.xpath("./p")]
    lines = [x for x in lines if x]
    start = next(i for i, x in enumerate(lines) if x.upper() == "LUẬT")
    text = "Luật Giáo dục số 43/2019/QH14, Quốc hội thông qua ngày 14/6/2019, hiệu lực từ 01/7/2020.\n" + "\n".join(lines[start:])
    (OUT / "giao_duc_luat_giao_duc_2019.txt").write_text(text + "\n", encoding="utf-8")
    return sum(1 for x in lines if re.match(r"^Điều \d+\.", x))


# ------------------------------------------------------------------ Du lịch
def di_tich() -> int:
    raw = load("wiki_di_tich_dac_biet.json")
    rows = []
    for heads, grid in tables(html.fromstring(raw["html"])):
        m = re.match(r"Đợt (\d+) \((\d{4})\)", heads["h3"])
        if not m or "đang tiến hành" in heads["h2"].lower():
            continue
        for r in as_dicts(grid):
            name = r.get("Di tích", "")
            if name:
                rows.append({"Tên di tích": name, "Địa điểm": r.get("Địa điểm", ""), "Hạng mục": r.get("Hạng mục", ""),
                             "Đợt xếp hạng": f"Đợt {m.group(1)}", "Năm xếp hạng": m.group(2), "Ghi chú": r.get("Ghi chú", "")})
    return write_xlsx(OUT / "du_lich_di_tich_dac_biet.xlsx", "Di tích quốc gia đặc biệt", list(rows[0]), rows)


SKIP_SECTIONS = ("tham khảo", "chú thích", "xem thêm", "liên kết ngoài", "ghi chú", "hình ảnh", "thư viện ảnh", "đọc thêm", "nguồn")


def diem_den() -> int:
    raw = load("wiki_diem_den.json")
    parts = ["# Điểm đến du lịch Việt Nam (bài Wikipedia tiếng Việt)"]
    for p in raw["pages"]:
        out, skip = [f"# {p['title']}"], False
        for ln in p["text"].split("\n"):
            m = re.match(r"^(==+)\s*(.+?)\s*==+$", ln.strip())
            if m:
                lvl = len(m.group(1))
                skip = m.group(2).lower() in SKIP_SECTIONS or (skip and lvl > 2)
                if not skip:
                    out.append("#" * lvl + " " + m.group(2))
                continue
            if not skip and ln.strip():
                out.append(clean(ln))
        parts.append("\n".join(out))
    (OUT / "du_lich_diem_den.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return len(raw["pages"])


def main() -> None:
    counts = {"y_te_benh_vien_tphcm.xlsx": benh_vien(), "y_te_hoi_dap_bac_si.md": hoi_dap(),
              "giao_duc_truong_dai_hoc.xlsx": truong_dai_hoc(), "giao_duc_luat_giao_duc_2019.txt": luat_giao_duc(),
              "du_lich_di_tich_dac_biet.xlsx": di_tich(), "du_lich_diem_den.md": diem_den()}
    versions = {n: {k: load(n).get(k) for k in ("title", "revid", "retrieved", "url", "dataset", "num_rows") if load(n).get(k) is not None}
                for n in sorted(p.name for p in RAW.glob("*.json"))}
    versions["wiki_diem_den.json"]["pages"] = [{"title": p["title"], "revid": p["revid"]} for p in load("wiki_diem_den.json")["pages"]]
    (OUT / "manifest.json").write_text(json.dumps({"counts": counts, "sources": versions}, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in counts.items():
        print(f"{k:38s} {v:5d}   {(OUT / k).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()

"""Sinh bộ câu mù thứ ba (real_v3) cho đường nhanh System 4 TỪ DỮ LIỆU, không chọn tay câu nào.

    python system4/eval/real_v3/make_cases_v3.py      # ghi cases_real_v3.json (cùng SEED + cùng data/ -> cùng tệp)

Viết 24/10/2026, TRƯỚC khi sửa engine. Mọi thứ quyết định trước khi xem câu sinh ra:
  - Khuôn mỗi lĩnh vực (13 câu): 3 tra cứu (L), 1 tra cứu gõ không dấu (U), 2 đếm (C), 2 liệt kê (S), 2 lớn nhất / nhỏ nhất (M),
    1 tổng (A), 1 hỏi thứ không có trong bảng (R), 1 hỏi tiếp 2 lượt (F). 4 lĩnh vực -> 52 câu.
  - Dòng, cột, giá trị lọc, ngưỡng: rút ngẫu nhiên (SEED) trong các cột khai báo ở SPEC; điều kiện: liệt kê 2..8 dòng,
    đếm từ 2 dòng trở lên, không hỏi ô trống / '?'.
  - Câu chữ theo khuôn câu (QTEXT) viết sẵn trong file này; đáp án tính bằng code từ chính tệp xlsx sẽ nạp.
  - Chấm bằng luật của system4/eval/bench.py (any / all / num / refusal / source), không nhờ AI chấm.
Lọc "chứa" (cột địa điểm nhiều tỉnh, vị trí hành chính) so khớp chuỗi con có dấu, không phân biệt hoa thường.
"""
from __future__ import annotations

import json
import random
import re
import unicodedata
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SEED = 20261024

# key: cột tên dòng; look: cột hỏi tra cứu -> (khuôn câu); cat: cột lọc bằng; contains: cột lọc chứa; numeric: cột số (đơn vị khi đọc)
SPEC = {
    "tinh_thanh": {
        "file": "hanh_chinh_tinh_thanh.xlsx", "sheet": "Tỉnh thành", "key": "Tỉnh thành", "noun": "tỉnh thành",
        "look": {"Trung tâm hành chính": "Trung tâm hành chính của {k} ở đâu?", "Vùng": "{k} thuộc vùng nào?",
                 "Thành lập": "{k} được thành lập năm nào?", "Diện tích (km²)": "Diện tích của {k} là bao nhiêu km²?",
                 "Dân số (người)": "Dân số của {k} là bao nhiêu người?", "Số xã": "{k} có bao nhiêu xã?",
                 "Số phường": "{k} có bao nhiêu phường?"},
        "cat": {"Vùng": "{n} thuộc vùng {v}"}, "contains": {},
        "numeric": {"Diện tích (km²)": "diện tích", "Dân số (người)": "dân số", "Mật độ (người/km²)": "mật độ dân số", "Số xã": "số xã",
                    "Số phường": "số phường"},
        "sum": {"Dân số (người)": "tổng dân số", "Số xã": "tổng số xã", "Số phường": "tổng số phường"},
        "refuse": ["Mã bưu chính của {k} là gì?", "Ai là Chủ tịch UBND {k} hiện nay?", "GDP của {k} năm 2025 là bao nhiêu?"],
    },
    "san_bay": {
        "file": "giao_thong_san_bay.xlsx", "sheet": "Sân bay dân dụng", "key": "Sân bay (Năm xây dựng)", "noun": "sân bay",
        "look": {"Mã ICAO/IATA": "Mã ICAO/IATA của sân bay {k} là gì?", "Tỉnh/ thành": "Sân bay {k} nằm ở tỉnh/thành nào?",
                 "Cấp sân bay": "Sân bay {k} là sân bay cấp mấy?", "Số đường băng": "Sân bay {k} có bao nhiêu đường băng?",
                 "Loại đường băng Chiều dài": "Đường băng của sân bay {k} dài bao nhiêu mét?",
                 "@Năm xây dựng": "Sân bay {k} được xây dựng năm nào?"},
        "cat": {"Tỉnh/ thành": "{n} ở {v}", "Cấp sân bay": "{n} cấp {v}", "Số đường băng": "{n} có {v} đường băng"}, "contains": {},
        "numeric": {},
        "sheet2": {"sheet": "Năng lực khai thác", "key": "Tên sân bay",
                   "look": {"Năng lực khai thác": "Năng lực khai thác của sân bay {k} là bao nhiêu?",
                            "Sản lượng thông qua (2023)": "Sản lượng thông qua năm 2023 của sân bay {k} là bao nhiêu?",
                            "Vị trí": "Sân bay {k} nằm ở đâu?"},
                   "numeric": {"Năng lực khai thác": "năng lực khai thác", "Sản lượng thông qua (2023)": "sản lượng thông qua năm 2023"},
                   "sum": {"Sản lượng thông qua (2023)": "tổng sản lượng thông qua năm 2023"}},
        "refuse": ["Giá vé máy bay đi từ sân bay {k} là bao nhiêu?", "Sân bay {k} có bao nhiêu nhân viên?", "Số điện thoại của sân bay {k} là gì?"],
    },
    "vuon_quoc_gia": {
        "file": "moi_truong_vuon_quoc_gia.xlsx", "sheet": "Vườn quốc gia", "key": "Tên vườn quốc gia", "noun": "vườn quốc gia",
        "look": {"Năm thành lập": "Vườn quốc gia {k} được thành lập năm nào?", "Diện tích (ha)": "Diện tích vườn quốc gia {k} là bao nhiêu ha?",
                 "Địa điểm": "Vườn quốc gia {k} nằm ở tỉnh nào?", "Vùng": "Vườn quốc gia {k} thuộc vùng nào?"},
        "cat": {"Vùng": "{n} thuộc vùng {v}"}, "contains": {"Địa điểm": "{n} ở {v}"},
        "numeric": {"Diện tích (ha)": "diện tích", "Năm thành lập": "năm thành lập"},
        "sum": {"Diện tích (ha)": "tổng diện tích"},
        "refuse": ["Giá vé vào cửa vườn quốc gia {k} là bao nhiêu?", "Vườn quốc gia {k} có bao nhiêu loài chim?", "Số điện thoại của vườn quốc gia {k} là gì?"],
    },
    "thuy_dien": {
        "file": "nang_luong_thuy_dien.xlsx", "sheet": "Thủy điện", "key": "Tên thủy điện", "noun": "thủy điện",
        "look": {"Công suất (MW)": "Thủy điện {k} có công suất bao nhiêu MW?", "Trên sông": "Thủy điện {k} nằm trên sông nào?",
                 "Năm hoạt động": "Thủy điện {k} bắt đầu hoạt động năm nào?", "Năm khởi công": "Thủy điện {k} khởi công năm nào?",
                 "Sản lượng (triệu kWh/năm)": "Sản lượng điện mỗi năm của thủy điện {k} là bao nhiêu?"},
        "cat": {"Trên sông": "{n} trên {v}", "Quy mô": "{n} quy mô {v}"}, "contains": {"Vị trí hành chính": "{n} ở {v}"},
        "numeric": {"Công suất (MW)": "công suất", "Sản lượng (triệu kWh/năm)": "sản lượng điện"},
        "sum": {"Công suất (MW)": "tổng công suất"},
        "refuse": ["Giá bán điện của thủy điện {k} là bao nhiêu?", "Thủy điện {k} có bao nhiêu công nhân?", "Ai là giám đốc thủy điện {k}?"],
    },
}
UNIT = {"Diện tích (km²)": " km²", "Diện tích (ha)": " ha", "Công suất (MW)": " MW", "Sản lượng (triệu kWh/năm)": " triệu kWh/năm",
        "Dân số (người)": " người", "Mật độ (người/km²)": " người/km²", "Năng lực khai thác": " lượt khách/năm",
        "Sản lượng thông qua (2023)": " lượt khách"}
# vùng / tỉnh để lọc "chứa": chỉ các tên tỉnh (34 tỉnh sau sáp nhập + tên cũ hay gặp trong cột vị trí)
PLACES = ["Lào Cai", "Lai Châu", "Sơn La", "Hà Giang", "Cao Bằng", "Tuyên Quang", "Thái Nguyên", "Phú Thọ", "Điện Biên", "Nghệ An",
          "Thanh Hóa", "Quảng Nam", "Quảng Ngãi", "Kon Tum", "Gia Lai", "Đắk Lắk", "Lâm Đồng", "Khánh Hòa", "Đồng Nai", "Hà Tĩnh",
          "Quảng Trị", "Huế", "Ninh Bình", "Hà Nội", "Đà Nẵng", "Cà Mau", "An Giang", "Tây Ninh", "Hải Phòng", "Quảng Ninh", "Đồng Tháp",
          "Bình Định", "Ninh Thuận", "Phú Yên", "Đắk Nông", "Bình Phước", "Yên Bái", "Bắc Kạn"]


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s).lower()).replace("đ", "d")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def unaccent(s: str) -> str:
    return fold(s)


def rows_of(file: str, sheet: str) -> list[dict]:
    ws = openpyxl.load_workbook(DATA / file, read_only=True, data_only=True)[sheet]
    it = ws.iter_rows(values_only=True)
    head = next(it)
    return [dict(zip(head, r)) for r in it]


def short(name: str) -> str:
    """'Côn Đảo (1945)' -> 'Côn Đảo' (tên sân bay kèm năm xây dựng trong cùng ô)."""
    return re.sub(r"\s*\(\d{4}\)\s*$", "", str(name)).strip()


def fmt_num(v) -> list[str]:
    """Các cách viết chấp nhận của một số: 573119 -> 573.119 / 573,119 / 573119 / 573 119; 6700.39 -> 6.700,39 / 6,700.39 / 6700,39 / 6700.39."""
    if isinstance(v, float) and not v.is_integer():
        ip, fp = f"{v:.10g}".split(".")
        ipn = int(ip)
        return list(dict.fromkeys([f"{ipn:,}".replace(",", ".") + "," + fp, f"{ipn:,}" + "." + fp, f"{ipn},{fp}", f"{ipn}.{fp}"]))
    n = int(v)
    if n < 10000:
        return [str(n)] + ([f"{n:,}".replace(",", "."), f"{n:,}"] if n >= 1000 else [])
    return list(dict.fromkeys([f"{n:,}".replace(",", "."), f"{n:,}", str(n), f"{n:,}".replace(",", " ")]))


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_for(v) -> dict:
    if is_num(v):
        return {"num": [str(int(v))]} if isinstance(v, int) and v < 10000 else {"any": fmt_num(v)}
    m = re.search(r"(\d{1,3}(?:\.\d{3})+|\d{3,})\s*m\b", str(v))          # "Bê tông 3.051 m" -> hỏi chiều dài: chấp nhận "3.051" / "3051"
    if m:
        n = int(m.group(1).replace(".", ""))
        return {"any": fmt_num(n)}
    return {"all": [str(v)]}


def make(seed: int = SEED) -> list[dict]:
    rnd = random.Random(seed)
    out = []
    for ds, sp in SPEC.items():
        rows = [r for r in rows_of(sp["file"], sp["sheet"]) if r.get(sp["key"])]
        key = sp["key"]
        disp = (lambda r: short(r[key])) if ds == "san_bay" else (lambda r: str(r[key]))
        n = 0

        def add(kind, turns, check, note, src=None):
            nonlocal n
            n += 1
            c = {"id": f"v3-{ds}-{n:02d}", "suite": "real3", "split": "blind", "datasets": [ds], "kind": kind,
                 "turns": turns if isinstance(turns, list) else [turns], "check": check, "gold_note": note}
            if src:
                c["check"]["source"] = src
            out.append(c)

        def look_slot(spec_rows, spec_key, look, exclude=()):
            for _ in range(200):
                r = rnd.choice(spec_rows)
                col = rnd.choice(sorted(look))
                if (r[spec_key], col) in exclude:
                    continue
                if col == "@Năm xây dựng":
                    m = re.search(r"\((\d{4})\)", str(r[spec_key]))
                    if m:
                        return r, col, int(m.group(1))
                    continue
                v = r.get(col)
                if v in (None, "", "?") or (isinstance(v, str) and not v.strip()):
                    continue
                return r, col, v
            raise RuntimeError("không rút được ô tra cứu")

        # ---- L x3 (sân bay: 2 sheet dân dụng + 1 sheet năng lực) và U x1
        used = set()
        plan = [("main",), ("main",), ("sheet2",) if "sheet2" in sp else ("main",), ("main",)]
        for i, (where,) in enumerate(plan):
            if where == "sheet2":
                s2 = sp["sheet2"]
                r2 = [r for r in rows_of(sp["file"], s2["sheet"]) if r.get(s2["key"])]
                r, col, v = look_slot(r2, s2["key"], s2["look"], used)
                kname = str(r[s2["key"]])
                q = s2["look"][col].format(k=kname)
            else:
                r, col, v = look_slot(rows, key, sp["look"], used)
                kname = disp(r)
                q = sp["look"][col].format(k=kname)
            used.add((r[key] if where != "sheet2" else r[sp["sheet2"]["key"]], col))
            kind = "U" if i == 3 else "L"
            if kind == "U":
                q = unaccent(q).replace("?", "")
            add(kind, q, check_for(v), f"{kname} / {col} = {v}", src=kname if kind == "L" and where != "sheet2" else None)

        # ---- C x2: đếm theo một giá trị lọc (bằng hoặc chứa) + đếm theo ngưỡng số
        filt = []
        for col, tmpl in sp["cat"].items():
            vals = {}
            for r in rows:
                if r.get(col) not in (None, ""):
                    vals.setdefault(str(r[col]), []).append(r)
            filt += [("eq", col, v, rs, tmpl) for v, rs in vals.items()]
        for col, tmpl in sp["contains"].items():
            for p in PLACES:
                rs = [r for r in rows if p.lower() in str(r.get(col) or "").lower()]
                if rs:
                    filt.append(("in", col, p, rs, tmpl))
        cnt = [f for f in filt if 2 <= len(f[3]) <= max(3, len(rows) // 2)]
        f = rnd.choice(cnt)
        add("C", f"Có bao nhiêu {f[4].format(n=sp['noun'], v=f[2])}?", {"num": [str(len(f[3]))]},
            f"{f[0]} {f[1]}={f[2]} -> {len(f[3])}")
        nums = sp["numeric"] or sp.get("sheet2", {}).get("numeric", {})
        nrows = rows if sp["numeric"] else [r for r in rows_of(sp["file"], sp["sheet2"]["sheet"]) if r.get(sp["sheet2"]["key"])]
        ncol = rnd.choice(sorted(nums))
        vals = sorted(r[ncol] for r in nrows if is_num(r.get(ncol)))
        q = vals[int(len(vals) * rnd.uniform(0.55, 0.85))]
        mag = 10 ** max(0, len(str(int(q))) - 2)
        thr = int(round(q / mag) * mag) or 1
        k = sum(1 for r in nrows if is_num(r.get(ncol)) and r[ncol] > thr)
        thr_txt = fmt_num(thr)[0] + UNIT.get(ncol, "")
        add("C", f"Có bao nhiêu {sp['noun']} có {nums[ncol]} trên {thr_txt}?", {"num": [str(k)]}, f"{ncol} > {thr} -> {k}")

        # ---- S x2: liệt kê 2..8 dòng theo giá trị lọc (khác giá trị đã dùng để đếm)
        lst = [g for g in filt if 2 <= len(g[3]) <= 8 and g[2] != f[2]]
        for g in rnd.sample(lst, 2):
            names = [disp(r) for r in g[3]]
            add("S", f"Liệt kê các {g[4].format(n=sp['noun'], v=g[2])}.", {"all": names}, f"{g[0]} {g[1]}={g[2]} -> {names}")

        # ---- M x2: lớn nhất / nhỏ nhất toàn bảng + trong một nhóm lọc
        ncol = rnd.choice(sorted(nums))
        vr = [r for r in nrows if is_num(r.get(ncol))]
        big = rnd.random() < 0.5
        best = (max if big else min)(vr, key=lambda r: r[ncol])
        kk = sp["sheet2"]["key"] if not sp["numeric"] else key
        bname = short(best[kk]) if ds == "san_bay" else str(best[kk])
        add("M", f"{sp['noun'].capitalize()} nào có {nums[ncol]} {'lớn nhất' if big else 'nhỏ nhất'}?", {"all": [bname]},
            f"{'max' if big else 'min'} {ncol} = {best[ncol]} ({bname})")
        if sp["numeric"]:
            grp = [g for g in filt if len([r for r in g[3] if is_num(r.get(ncol))]) >= 3]
            g = rnd.choice(grp)
            vr = [r for r in g[3] if is_num(r.get(ncol))]
            big = rnd.random() < 0.5
            best = (max if big else min)(vr, key=lambda r: r[ncol])
            add("M", f"Trong các {g[4].format(n=sp['noun'], v=g[2])}, {sp['noun']} nào có {nums[ncol]} {'lớn nhất' if big else 'nhỏ nhất'}?",
                {"all": [disp(best)]}, f"{g[1]}={g[2]}: {'max' if big else 'min'} {ncol} = {best[ncol]} ({disp(best)})")
        else:      # sân bay: cột số ở sheet năng lực -> nhỏ nhất / lớn nhất theo cột còn lại
            ncol2 = [c for c in sorted(nums) if c != ncol][0]
            vr = [r for r in nrows if is_num(r.get(ncol2))]
            best = (min if big else max)(vr, key=lambda r: r[ncol2])
            add("M", f"Sân bay nào có {nums[ncol2]} {'nhỏ nhất' if big else 'lớn nhất'}?", {"all": [str(best[sp['sheet2']['key']])]},
                f"{'min' if big else 'max'} {ncol2} = {best[ncol2]} ({best[sp['sheet2']['key']]})")

        # ---- A x1: tổng theo nhóm lọc (hoặc toàn bảng nếu không có nhóm phù hợp)
        sums = sp.get("sum") or sp["sheet2"]["sum"]
        scol = rnd.choice(sorted(sums))
        if sp["numeric"] and scol in (sp["numeric"] or {}):
            g = rnd.choice([g for g in filt if len(g[3]) >= 2])
            vs = [r[scol] for r in g[3] if is_num(r.get(scol))]
            tot = round(sum(vs), 2)
            tot = int(tot) if float(tot).is_integer() else tot
            add("A", f"{sums[scol].capitalize()} của các {g[4].format(n=sp['noun'], v=g[2])} là bao nhiêu?", check_for(tot),
                f"sum {scol} where {g[1]}={g[2]} = {tot} ({len(vs)} dòng)")
        else:
            vs = [r[scol] for r in nrows if is_num(r.get(scol))]
            tot = sum(vs)
            add("A", f"{sums[scol].capitalize()} của tất cả các sân bay là bao nhiêu?", check_for(tot), f"sum {scol} = {tot} ({len(vs)} dòng)")

        # ---- R x1: hỏi thứ bảng không có cột
        r = rnd.choice(rows)
        add("R", rnd.choice(sp["refuse"]).format(k=disp(r)), {"refusal": True}, "bảng không có cột này")

        # ---- F x1: hỏi tiếp — lượt 1 tra cứu một cột, lượt 2 "còn <cột khác> thì sao?"
        r, col, v = look_slot(rows, key, {c: t for c, t in sp["look"].items() if not c.startswith("@")}, used)
        col2 = rnd.choice([c for c in sp["look"] if c != col and not c.startswith("@") and r.get(c) not in (None, "", "?")])
        label = {"Trung tâm hành chính": "trung tâm hành chính", "Vùng": "vùng", "Thành lập": "năm thành lập", "Diện tích (km²)": "diện tích",
                 "Dân số (người)": "dân số", "Số xã": "số xã", "Số phường": "số phường", "Mã ICAO/IATA": "mã ICAO/IATA", "Tỉnh/ thành": "tỉnh",
                 "Cấp sân bay": "cấp sân bay", "Số đường băng": "số đường băng", "Loại đường băng Chiều dài": "chiều dài đường băng",
                 "Năm thành lập": "năm thành lập", "Diện tích (ha)": "diện tích", "Địa điểm": "địa điểm", "Công suất (MW)": "công suất",
                 "Trên sông": "con sông", "Năm hoạt động": "năm hoạt động", "Năm khởi công": "năm khởi công",
                 "Sản lượng (triệu kWh/năm)": "sản lượng điện"}[col2]
        add("F", [sp["look"][col].format(k=disp(r)), f"Còn {label} thì sao?"], check_for(r[col2]), f"{disp(r)}: {col}={v}; {col2}={r[col2]}")
    return out


def main():
    cases = make()
    (HERE / "cases_real_v3.json").write_text(json.dumps(cases, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(cases), Counter(c["kind"] for c in cases))


if __name__ == "__main__":
    main()

"""Sinh bộ câu mù thứ tư (real_v4_s4) cho System 4 TỪ DỮ LIỆU, không chọn tay câu nào.

    python system4/eval/real_v4_s4/make_cases_v4.py

Kế thừa khuôn từ real_v3/make_cases_v3.py:
- Khuôn câu và tỷ lệ loại câu viết trước.
- Dòng, cột, giá trị lọc, ngưỡng rút ngẫu nhiên có SEED cố định.
- Đáp án code tự tính từ chính các tệp xlsx trong data/ — không gán tay.
- 9 loại câu: L (tra cứu), U (không dấu), C (đếm), S (liệt kê), M (max/min), A (tổng),
  R (từ chối thuộc tính không có), F (hỏi tiếp 2 lượt), và X (câu hỏi chéo 2 sheet / đa điều kiện).
- 8 bảng x 16 câu = 128 câu (>= 120 câu theo yêu cầu JD mục 3).
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
SEED = 20261027


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s).lower()).replace("đ", "d")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def unaccent(s: str) -> str:
    return fold(s)


def rows_of(file: str, sheet: str) -> list[dict]:
    ws = openpyxl.load_workbook(DATA / file, read_only=True, data_only=True)[sheet]
    it = ws.iter_rows(values_only=True)
    head = next(it)
    return [dict(zip(head, r)) for r in it if any(r)]


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fmt_num(v) -> list[str]:
    """Các định dạng chấp nhận của số: 573119 -> 573.119 / 573,119 / 573119 / 573 119."""
    if isinstance(v, float) and not v.is_integer():
        ip, fp = f"{v:.10g}".split(".")
        ipn = int(ip)
        return list(dict.fromkeys([
            f"{ipn:,}".replace(",", ".") + "," + fp,
            f"{ipn:,}" + "." + fp,
            f"{ipn},{fp}",
            f"{ipn}.{fp}"
        ]))
    n = int(v)
    if n < 10000:
        return [str(n)] + ([f"{n:,}".replace(",", "."), f"{n:,}"] if n >= 1000 else [])
    return list(dict.fromkeys([f"{n:,}".replace(",", "."), f"{n:,}", str(n), f"{n:,}".replace(",", " ")]))


def check_for(v) -> dict:
    if is_num(v):
        return {"num": [str(int(v))]} if isinstance(v, int) and v < 10000 else {"any": fmt_num(v)}
    s = str(v).strip()
    m = re.search(r"(\d{1,3}(?:\.\d{3})+|\d+)\s*(?:chỗ|giường|người|ha|m)\b", s)
    if m:
        n = int(m.group(1).replace(".", ""))
        return {"any": fmt_num(n) + [s]}
    return {"all": [s]}


SPEC = {
    "dan_toc": {
        "file": "van_hoa_dan_toc.xlsx", "sheet": "Dân tộc và Ngôn ngữ", "key": "Dân tộc", "noun": "dân tộc",
        "look": {
            "Ngữ hệ": "Dân tộc {k} thuộc ngữ hệ nào?",
            "Nhóm ngôn ngữ": "Dân tộc {k} thuộc nhóm ngôn ngữ nào?",
            "Tên gọi khác": "Tên gọi khác của dân tộc {k} là gì?",
            "Dân số (người)": "Dân số của dân tộc {k} là bao nhiêu người?",
            "Tỷ lệ dân số (%)": "Tỷ lệ dân số của dân tộc {k} chiếm bao nhiêu phần trăm?"
        },
        "cat": {"Ngữ hệ": "{n} thuộc {v}", "Nhóm ngôn ngữ": "{n} thuộc nhóm {v}"},
        "contains": {},
        "numeric": {"Dân số (người)": "dân số", "Tỷ lệ dân số (%)": "tỷ lệ dân số"},
        "sum": {"Dân số (người)": "tổng dân số"},
        "refuse": ["Trang phục truyền thống của dân tộc {k} có màu gì?", "Ai là trưởng bản của dân tộc {k}?", "Lễ hội lớn nhất của dân tộc {k} tổ chức vào ngày nào?"],
        "multi": {
            "sheet2": "Địa bàn cư trú", "key2": "Dân tộc",
            "look2": {"Địa bàn cư trú chính": "Địa bàn cư trú chính của dân tộc {k} ở đâu?", "Vùng cư trú chủ yếu": "Dân tộc {k} cư trú chủ yếu ở vùng nào?"},
            "cat2": {"Vùng cư trú chủ yếu": "{n} cư trú ở {v}"}
        }
    },
    "san_van_dong": {
        "file": "the_thao_san_van_dong.xlsx", "sheet": "Sân vận động", "key": "Sân vận động", "noun": "sân vận động",
        "look": {
            "Địa điểm": "Sân vận động {k} nằm ở tỉnh/thành nào?",
            "Năm khánh thành": "Sân vận động {k} được khánh thành năm nào?",
            "Sức chứa (chỗ)": "Sức chứa của sân vận động {k} là bao nhiêu khán giả?"
        },
        "cat": {"Địa điểm": "{n} ở {v}"},
        "contains": {},
        "numeric": {"Sức chứa (chỗ)": "sức chứa"},
        "sum": {"Sức chứa (chỗ)": "tổng sức chứa"},
        "refuse": ["Giá vé vào sân vận động {k} là bao nhiêu?", "Giám đốc sân vận động {k} là ai?", "Sân vận động {k} có bao nhiêu cửa ra vào?"],
        "multi": {
            "sheet2": "Đội bóng và Trạng thái", "key2": "Sân vận động",
            "look2": {"Đội bóng chủ quản": "Đội bóng nào sử dụng sân vận động {k} làm sân nhà?", "Trạng thái khai thác": "Trạng thái hiện tại của sân vận động {k} là gì?"},
            "cat2": {"Trạng thái khai thác": "{n} có trạng thái {v}"}
        }
    },
    "phi_vat_the": {
        "file": "van_hoa_phi_vat_the.xlsx", "sheet": "Di sản phi vật thể", "key": "Tên di sản", "noun": "di sản phi vật thể",
        "look": {
            "Loại hình": "Di sản {k} thuộc loại hình di sản nào?",
            "Địa điểm": "Di sản {k} thuộc tỉnh/thành nào?",
            "Năm công nhận": "Di sản {k} được ghi danh vào năm nào?"
        },
        "cat": {"Loại hình": "{n} thuộc loại hình {v}"},
        "contains": {"Địa điểm": "{n} ở {v}"},
        "numeric": {"Năm công nhận": "năm công nhận"},
        "sum": {},
        "refuse": ["Người sáng lập di sản {k} là ai?", "Vé tham gia di sản {k} là bao nhiêu?", "Có bao nhiêu nghệ nhân tham gia di sản {k}?"],
    },
    "bao_vat": {
        "file": "lich_su_bao_vat_quoc_gia.xlsx", "sheet": "Bảo vật quốc gia", "key": "Tên bảo vật", "noun": "bảo vật quốc gia",
        "look": {
            "Đợt công nhận": "Bảo vật {k} được công nhận vào đợt mấy?",
            "Năm công nhận": "Bảo vật {k} được công nhận năm nào?",
            "Niên đại / Lịch sử": "Niên đại lịch sử của bảo vật {k} là thời kỳ nào?",
            "Chủ sở hữu / Đơn vị lưu giữ": "Bảo vật {k} hiện đang được lưu giữ ở đâu?",
            "Địa phương": "Bảo vật {k} thuộc địa phương nào?"
        },
        "cat": {"Đợt công nhận": "{n} thuộc {v}"},
        "contains": {"Địa phương": "{n} ở {v}"},
        "numeric": {"Năm công nhận": "năm công nhận"},
        "sum": {},
        "refuse": ["Bảo vật {k} được định giá bao nhiêu tiền?", "Bảo vật {k} nặng bao nhiêu kg?", "Bảo vật {k} do nghệ nhân nào chế tác?"],
    },
    "diem_du_lich": {
        "file": "du_lich_diem_den_quoc_gia.xlsx", "sheet": "Điểm du lịch quốc gia", "key": "Tên khu du lịch", "noun": "khu du lịch",
        "look": {
            "Địa phương": "Khu du lịch {k} nằm ở tỉnh/thành nào?",
            "Vùng du lịch": "Khu du lịch {k} thuộc vùng du lịch nào?",
            "Loại hình du lịch": "Loại hình du lịch chính của {k} là gì?",
            "Tình trạng": "Tình trạng quy hoạch hoặc công nhận của {k} là gì?",
            "Năm công nhận": "Khu du lịch {k} được công nhận hoặc quy hoạch năm nào?"
        },
        "cat": {"Vùng du lịch": "{n} ở vùng {v}", "Tình trạng": "{n} có tình trạng {v}"},
        "contains": {"Địa phương": "{n} ở {v}"},
        "numeric": {"Năm công nhận": "năm công nhận"},
        "sum": {},
        "refuse": ["Giá vé vào cổng của khu du lịch {k} là bao nhiêu?", "Số lượng khách du lịch tới {k} năm 2025 là bao nhiêu?", "Trưởng ban quản lý khu du lịch {k} là ai?"],
    },
    "dai_hoc": {
        "file": "giao_duc_truong_dai_hoc.xlsx", "sheet": "Trường đại học", "key": "Tên trường", "noun": "trường đại học",
        "look": {
            "Viết tắt": "Tên viết tắt của {k} là gì?",
            "Tên giao dịch tiếng Anh": "Tên tiếng Anh của {k} là gì?",
            "Địa điểm": "Trụ sở của {k} ở đâu?",
            "Cơ quan chủ quản": "Cơ quan chủ quản của {k} là đơn vị nào?",
            "Loại hình": "{k} là trường công lập hay tư thục?"
        },
        "cat": {"Loại hình": "{n} {v}", "Cơ quan chủ quản": "{n} trực thuộc {v}"},
        "contains": {"Địa điểm": "{n} ở {v}"},
        "numeric": {},
        "sum": {},
        "refuse": ["Hiệu trưởng hiện nay của {k} là ai?", "Học phí một năm của {k} là bao nhiêu?", "Điểm chuẩn ngành Công nghệ thông tin của {k} năm ngoái là bao nhiêu?"],
    },
    "benh_vien": {
        "file": "y_te_benh_vien_tphcm.xlsx", "sheet": "Bệnh viện", "key": "Tên bệnh viện", "noun": "bệnh viện",
        "look": {
            "Tên khác": "Tên gọi khác của {k} là gì?",
            "Năm thành lập": "{k} được thành lập năm nào?",
            "Loại bệnh viện": "{k} là bệnh viện chuyên khoa hay đa khoa?",
            "Cơ sở": "{k} nằm ở phường/quận nào?",
            "Số giường": "{k} có quy mô bao nhiêu giường bệnh?",
            "Tuyến quản lý": "{k} thuộc tuyến quản lý nào?"
        },
        "cat": {"Loại bệnh viện": "{n} {v}", "Tuyến quản lý": "{n} {v}"},
        "contains": {"Cơ sở": "{n} ở {v}"},
        "numeric": {"Số giường": "số giường bệnh", "Năm thành lập": "năm thành lập"},
        "sum": {"Số giường": "tổng số giường bệnh"},
        "refuse": ["Số điện thoại cấp cứu của {k} là gì?", "Giám đốc {k} hiện nay là ai?", "Giá khám dịch vụ tại {k} là bao nhiêu tiền?"],
    },
    "di_tich_dac_biet": {
        "file": "di_tich_quoc_gia_dac_biet.xlsx", "sheet": "Di tích đặc biệt", "key": "Tên di tích", "noun": "di tích đặc biệt",
        "look": {
            "Đợt xếp hạng": "Di tích {k} được xếp hạng vào đợt mấy?",
            "Năm xếp hạng": "Di tích {k} được xếp hạng năm nào?",
            "Địa điểm": "Di tích {k} nằm ở tỉnh/thành nào?",
            "Hạng mục di tích": "Hạng mục xếp hạng của di tích {k} là gì?"
        },
        "cat": {"Hạng mục di tích": "{n} thuộc hạng mục {v}", "Đợt xếp hạng": "{n} xếp hạng {v}"},
        "contains": {"Địa điểm": "{n} ở {v}"},
        "numeric": {"Năm xếp hạng": "năm xếp hạng"},
        "sum": {},
        "refuse": ["Giá vé vào cửa di tích {k} là bao nhiêu?", "Ban quản lý di tích {k} có bao nhiêu người?", "Diện tích khuôn viên di tích {k} là bao nhiêu mét vuông?"],
    }
}

PLACES = ["Hà Nội", "Thành phố Hồ Chí Minh", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "Huế", "Nghệ An",
          "Thanh Hóa", "Quảng Ninh", "Bắc Ninh", "Phú Thọ", "Lâm Đồng", "Khánh Hòa", "An Giang"]


def make_cases(seed: int = SEED) -> list[dict]:
    rnd = random.Random(seed)
    cases = []

    for ds, sp in SPEC.items():
        rows = rows_of(sp["file"], sp["sheet"])
        key = sp["key"]
        n = 0

        def add(kind, turns, check, note, src=None):
            nonlocal n
            n += 1
            item = {
                "id": f"v4-{ds}-{n:02d}",
                "suite": "real4",
                "split": "blind",
                "datasets": [ds],
                "kind": kind,
                "turns": turns if isinstance(turns, list) else [turns],
                "check": check,
                "gold_note": note
            }
            if src:
                item["check"]["source"] = src
            cases.append(item)

        # 1. L (Tra cứu 1 thuộc tính) x3
        used_slots = set()
        for i in range(3):
            valid_rows = [r for r in rows if r.get(key)]
            for _ in range(200):
                r = rnd.choice(valid_rows)
                col = rnd.choice(sorted(sp["look"].keys()))
                v = r.get(col)
                if (r[key], col) not in used_slots and v not in (None, "", "?") and not str(v).startswith("?"):
                    used_slots.add((r[key], col))
                    break
            q = sp["look"][col].format(k=str(r[key]))
            add("L", q, check_for(v), f"{r[key]} / {col} = {v}", src=str(r[key]))

        # 2. U (Tra cứu không dấu) x2
        for i in range(2):
            for _ in range(200):
                r = rnd.choice(rows)
                col = rnd.choice(sorted(sp["look"].keys()))
                v = r.get(col)
                if (r[key], col) not in used_slots and v not in (None, "", "?"):
                    used_slots.add((r[key], col))
                    break
            q = unaccent(sp["look"][col].format(k=str(r[key]))).replace("?", "")
            add("U", q, check_for(v), f"Unaccent: {r[key]} / {col} = {v}")

        # 3. C (Đếm theo điều kiện) x2
        # C1: Đếm theo điều kiện danh mục (cat hoặc contains)
        filt = []
        for col, tmpl in sp["cat"].items():
            vals = {}
            for r in rows:
                if r.get(col):
                    vals.setdefault(str(r[col]), []).append(r)
            filt += [("eq", col, v, rs, tmpl) for v, rs in vals.items() if 2 <= len(rs) <= max(3, len(rows) // 2)]
        for col, tmpl in sp["contains"].items():
            for p in PLACES:
                rs = [r for r in rows if p.lower() in str(r.get(col) or "").lower()]
                if 2 <= len(rs) <= max(3, len(rows) // 2):
                    filt.append(("in", col, p, rs, tmpl))
        if filt:
            f = rnd.choice(filt)
            q = f"Có bao nhiêu {f[4].format(n=sp['noun'], v=f[2])}?"
            add("C", q, {"num": [str(len(f[3]))]}, f"Đếm {f[1]}={f[2]} -> {len(f[3])}")
        else:
            add("C", f"Có bao nhiêu {sp['noun']} trong bảng?", {"num": [str(len(rows))]}, f"Đếm toàn bảng = {len(rows)}")

        # C2: Đếm theo ngưỡng số (nếu có cột số) hoặc điều kiện phụ
        if sp["numeric"]:
            ncol = rnd.choice(sorted(sp["numeric"].keys()))
            num_rows = [r for r in rows if is_num(r.get(ncol))]
            if num_rows:
                vals = sorted(r[ncol] for r in num_rows)
                mid_val = vals[len(vals) // 2]
                k = sum(1 for r in num_rows if r[ncol] >= mid_val)
                q = f"Có bao nhiêu {sp['noun']} có {sp['numeric'][ncol]} từ {fmt_num(mid_val)[0]} trở lên?"
                add("C", q, {"num": [str(k)]}, f"{ncol} >= {mid_val} -> {k}")
            else:
                add("C", f"Có bao nhiêu {sp['noun']} có đầy đủ thông tin?", {"num": [str(len(rows))]}, "Đếm tổng")
        else:
            # Nếu không có cột số, đếm theo danh mục khác
            f2 = rnd.choice(filt) if filt else None
            if f2:
                add("C", f"Số lượng {f2[4].format(n=sp['noun'], v=f2[2])} là bao nhiêu?", {"num": [str(len(f2[3]))]}, f"Đếm {f2[2]} -> {len(f2[3])}")
            else:
                add("C", f"Có bao nhiêu {sp['noun']} được liệt kê?", {"num": [str(len(rows))]}, "Đếm tổng")

        # 4. S (Liệt kê 2..8 dòng) x2
        s_candidates = [f for f in filt if 2 <= len(f[3]) <= 8]
        if len(s_candidates) >= 2:
            s_chosen = rnd.sample(s_candidates, 2)
        elif s_candidates:
            s_chosen = [s_candidates[0], s_candidates[0]]
        else:
            s_chosen = [("all", "all", "all", rows[:5], "{n}")]

        for g in s_chosen:
            names = [str(r[key]) for r in g[3]]
            add("S", f"Liệt kê các {g[4].format(n=sp['noun'], v=g[2])}.", {"all": names}, f"Liệt kê {g[2]} -> {names}")

        # 5. M (Lớn nhất / Nhỏ nhất) x2
        if sp["numeric"]:
            ncol = rnd.choice(sorted(sp["numeric"].keys()))
            num_rows = [r for r in rows if is_num(r.get(ncol))]
            best_max = max(num_rows, key=lambda r: r[ncol])
            best_min = min(num_rows, key=lambda r: r[ncol])
            add("M", f"{sp['noun'].capitalize()} nào có {sp['numeric'][ncol]} lớn nhất?", {"all": [str(best_max[key])]}, f"Max {ncol} = {best_max[ncol]} ({best_max[key]})")
            add("M", f"{sp['noun'].capitalize()} nào có {sp['numeric'][ncol]} nhỏ nhất?", {"all": [str(best_min[key])]}, f"Min {ncol} = {best_min[ncol]} ({best_min[key]})")
        else:
            # Bảng không có cột số thì dùng STT đầu tiên và cuối cùng
            add("M", f"{sp['noun'].capitalize()} đầu tiên trong danh sách là gì?", {"all": [str(rows[0][key])]}, f"Đầu tiên: {rows[0][key]}")
            add("M", f"{sp['noun'].capitalize()} thứ hai trong danh sách là gì?", {"all": [str(rows[1][key])]}, f"Thứ hai: {rows[1][key]}")

        # 6. A (Tính tổng) x1
        if sp.get("sum"):
            scol = rnd.choice(sorted(sp["sum"].keys()))
            num_rows = [r for r in rows if is_num(r.get(scol))]
            tot = sum(r[scol] for r in num_rows)
            tot_val = int(tot) if float(tot).is_integer() else round(tot, 2)
            add("A", f"{sp['sum'][scol].capitalize()} của tất cả các {sp['noun']} là bao nhiêu?", check_for(tot_val), f"Tổng {scol} = {tot_val}")
        else:
            # Bảng không có cột tính tổng: tính tổng số lượng thực thể theo 2 nhóm
            if filt:
                g = rnd.choice(filt)
                add("A", f"Tổng số {g[4].format(n=sp['noun'], v=g[2])} là bao nhiêu?", {"num": [str(len(g[3]))]}, f"Tổng = {len(g[3])}")
            else:
                add("A", f"Tổng số {sp['noun']} trong danh sách là bao nhiêu?", {"num": [str(len(rows))]}, f"Tổng = {len(rows)}")

        # 7. R (Từ chối thuộc tính không có) x1
        r_ref = rnd.choice(rows)
        q_ref = rnd.choice(sp["refuse"]).format(k=str(r_ref[key]))
        add("R", q_ref, {"refusal": True}, "Bảng không có thông tin thuộc tính này")

        # 8. F (Hỏi tiếp 2 lượt - Follow-up) x1
        r_f = rnd.choice([r for r in rows if r.get(key)])
        cols_avail = [c for c in sp["look"].keys() if r_f.get(c) not in (None, "", "?")]
        if len(cols_avail) >= 2:
            c1, c2 = rnd.sample(cols_avail, 2)
        else:
            c1 = cols_avail[0]
            c2 = c1
        q1 = sp["look"][c1].format(k=str(r_f[key]))
        col_label = c2.lower().replace("(người)", "").replace("(%)", "").replace("(chỗ)", "").strip()
        q2 = f"Còn {col_label} thì sao?"
        add("F", [q1, q2], check_for(r_f[c2]), f"Follow-up: {r_f[key]}: {c1}={r_f[c1]} -> {c2}={r_f[c2]}")

        # 9. X (Câu hỏi chéo 2 sheet / đa điều kiện) x2 (Mới cho bài toán S4-1!)
        if "multi" in sp:
            multi = sp["multi"]
            r2_all = rows_of(sp["file"], multi["sheet2"])
            r2_map = {str(r[multi["key2"]]): r for r in r2_all if r.get(multi["key2"])}

            # X1: Điều kiện ở Sheet 2, hỏi thuộc tính ở Sheet 1
            paired = [r for r in rows if str(r[key]) in r2_map and r.get(key)]
            p_cand = rnd.choice(paired)
            k_val = str(p_cand[key])
            r2_cand = r2_map[k_val]

            # Lấy 1 cột từ sheet 2 làm điều kiện, 1 cột từ sheet 1 làm câu hỏi
            col_s2 = rnd.choice(list(multi["look2"].keys()))
            val_s2 = r2_cand.get(col_s2)
            col_s1 = rnd.choice(list(sp["look"].keys()))
            val_s1 = p_cand.get(col_s1)

            q_x1 = f"{sp['noun'].capitalize()} {k_val} có {col_s2.lower()} là '{val_s2}', vậy {sp['look'][col_s1].format(k=k_val).lower()}"
            add("X", q_x1, check_for(val_s1), f"Cross-sheet X1: Sheet2({col_s2}={val_s2}) + Sheet1({col_s1}={val_s1})")

            # X2: Điều kiện ở Sheet 1, hỏi thuộc tính ở Sheet 2
            col_s1_b = rnd.choice(list(sp["look"].keys()))
            val_s1_b = p_cand.get(col_s1_b)
            col_s2_b = rnd.choice(list(multi["look2"].keys()))
            val_s2_b = r2_cand.get(col_s2_b)

            q_x2 = multi["look2"][col_s2_b].format(k=k_val)
            add("X", q_x2, check_for(val_s2_b), f"Cross-sheet X2: {k_val} hỏi cột Sheet2: {col_s2_b}={val_s2_b}")
        else:
            # Bảng đơn sheet: câu hỏi đa điều kiện kết hợp 2 cột
            p_cand = rnd.choice([r for r in rows if r.get(key)])
            k_val = str(p_cand[key])
            cols_avail = [c for c in sp["look"].keys() if p_cand.get(c) not in (None, "", "?")]
            c_a, c_b = rnd.sample(cols_avail, 2) if len(cols_avail) >= 2 else (cols_avail[0], cols_avail[0])
            add("X", f"Cho biết {c_a.lower()} và {c_b.lower()} của {k_val}.", {"all": [str(p_cand[c_a]), str(p_cand[c_b])]}, f"Đa cột: {c_a}={p_cand[c_a]}, {c_b}={p_cand[c_b]}")
            add("X", f"{sp['noun'].capitalize()} {k_val} có {c_a.lower()} là gì?", check_for(p_cand[c_a]), f"Kiểm tra: {c_a}={p_cand[c_a]}")

    return cases


def main():
    cases = make_cases()
    out_file = HERE / "cases_real_v4_s4.json"
    out_file.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    from collections import Counter
    print(f"Tổng số câu sinh ra: {len(cases)}")
    print("Phân bổ theo loại câu:", Counter(c["kind"] for c in cases))
    print("Phân bổ theo bộ dữ liệu:", Counter(c["datasets"][0] for c in cases))


if __name__ == "__main__":
    main()

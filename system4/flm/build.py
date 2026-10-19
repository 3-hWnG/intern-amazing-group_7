"""Dữ liệu thô FLM (scrape.collect) -> tệp Excel nhiều sheet, nạp như một bộ dữ liệu bình thường (ingest + đường nhanh).

Mỗi sheet là một bảng, cột tiếng Việt (đường nhanh dựa vào tên cột để hiểu cách hỏi); bảng con nối bảng cha qua cột khoá
"Mã môn" / "Mã chương trình" (fastpath/compile.py nhận bảng con theo cột khoá):
  Chương trình        mỗi khung chương trình (ngành, khoá mới nhất)
  PLO                 chuẩn đầu ra của chương trình           (khoá: Mã chương trình)
  Khung chương trình  môn × chương trình: học kỳ, tín chỉ      (khoá: Mã chương trình, Mã môn)
  Môn học             mỗi môn một dòng, từ đề cương đang dùng
  CLO                 chuẩn đầu ra của môn                    (khoá: Mã môn)
  Đánh giá            các đầu điểm của môn: trọng số, thời lượng… (khoá: Mã môn)
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .scrape import BASE

MAX_CELL = 30000   # Excel tối đa 32767 ký tự một ô


def _major(name: str) -> str:
    """"… Software Engineering Major (Chương trình cử nhân ngành CNTT, chuyên ngành Kỹ thuật phần mềm)" -> "Kỹ thuật phần mềm"."""
    m = re.search(r"chuyên ngành\s+([^)]+)\)", name, re.I)
    return m.group(1).strip() if m else name


def _split_name(name: str) -> tuple[str, str]:
    """FLM ghi "English_Tiếng Việt" hoặc "Tiếng Việt_English": trả (tên đầy đủ, phần tiếng Anh nếu tách được)."""
    parts = [p.strip() for p in name.split("_") if p.strip()]
    return name.replace("_", " – ") if len(parts) == 2 else name, parts[0] if len(parts) == 2 and parts[0].isascii() else \
        (parts[1] if len(parts) == 2 and parts[1].isascii() else "")


def digest(raw: dict) -> str:
    """Băm dữ liệu (bỏ số request) để biết lần đồng bộ này có ĐỔI so với bản trước không."""
    keep = {k: raw[k] for k in ("programs", "curricula", "syllabi") if k in raw}
    return hashlib.sha1(json.dumps(keep, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def _none(v: str) -> str:
    return "" if (v or "").strip().lower() in ("none", "n/a", "không", "khong") else v


def _material(m: dict) -> str:
    """Một dòng tài liệu: tên — tác giả — NXB (năm) [chính] · bản cứng / online · link. Chỉ LINK, không tải tệp (leader 19/10)."""
    bits = [m.get("Material Description", ""), m.get("Author", ""), m.get("Publisher", "")]
    s = " — ".join(b for b in bits if b and b.upper() != "N/A")
    if m.get("Published Date"):
        s += f" ({m['Published Date']})"
    tags = [t for t, k in (("tài liệu chính", "Is Main Material"), ("bản cứng", "Is Hard Copy"), ("online", "Is Online")) if m.get(k) == "True"]
    if m.get("ISBN") and m["ISBN"].upper() != "N/A":
        tags.append("ISBN " + m["ISBN"])
    links = [x for x in [m.get("Note", "")] + m.get("_links", []) if x.startswith("http")]
    return s + (f" [{', '.join(tags)}]" if tags else "") + (" · " + " ".join(dict.fromkeys(links)) if links else "")


def sheets(raw: dict) -> dict[str, list[list]]:
    """Chế độ khách: 6 sheet. Chế độ ĐĂNG NHẬP (raw["mode"] == "full", mọi ngành): CLO và tài liệu gộp vào cột của "Môn học" (bớt hàng chục
    nghìn dòng), có thêm môn của combo / tự chọn; lịch từng buổi + câu hỏi thảo luận ở tệp văn bản riêng (schedule_md)."""
    full = raw.get("mode") == "full"
    cur_rows = [["Tên chuyên ngành", "Mã chương trình", "Mã ngành", "Chuyên ngành", "Tên chương trình", "Tổng số tín chỉ", "Số môn trong khung",
                 "Quyết định ban hành", "Link FLM"]]
    # bảng con: cột "Tên …" duy nhất đứng đầu để ingest chọn đúng cột tiêu đề (ingest._title_score: duy nhất + có chữ "tên")
    plo_rows = [["Tên PLO", "Mã chương trình", "Chuyên ngành", "Chuẩn đầu ra (PLO)", "Nội dung PLO"]]
    frame = [["Tên môn trong khung", "Mã chương trình", "Chuyên ngành", "Mã môn", "Tên môn", "Học kỳ", "Số tín chỉ", "Môn tiên quyết (theo khung)",
              "Thuộc nhóm (combo / tự chọn)"]]
    where: dict[str, list[str]] = {}
    frame_of: dict[str, dict] = {}
    for c in raw["curricula"]:
        major = _major(c.get("name") or c["info"].get("Name", ""))
        cur_rows.append([f"Chuyên ngành {major} ({c['code']})", c["code"], c.get("program") or "", major, c.get("name") or c["info"].get("Name", ""),
                         c.get("credits", ""), len(c["subjects"]), c.get("decision", ""), f"{BASE}/gui/role/guest/CurriculumDetails?curid={c['curid']}"])
        for p in c["plo"]:
            plo_rows.append([f"{p['name']} · {major}", c["code"], major, p["name"], p["description"]])
        seen = set()
        for s in c["subjects"]:
            frame.append([f"{s['code']} · {major}", c["code"], major, s["code"], _split_name(s["name"])[0], s["semester"], s["credits"],
                          _none(s["prerequisite"]), ""])
            where.setdefault(s["code"], []).append(f"{major} (kỳ {s['semester']})")
            frame_of.setdefault(s["code"], s)
            seen.add(s["code"])
        for g in c.get("groups") or []:   # môn trong combo / tự chọn (chỉ chế độ đăng nhập)
            label = ("Combo " if g["kind"] == "combo" else "Tự chọn ") + g["name"]
            for s in g["subjects"]:
                if s["code"] in seen:
                    continue
                seen.add(s["code"])
                frame.append([f"{s['code']} · {major}", c["code"], major, s["code"], _split_name(s["name"])[0], s["semester"], "", "", label])
                where.setdefault(s["code"], []).append(f"{major} ({label[:40]}{', kỳ ' + s['semester'] if s['semester'] else ''})")
                frame_of.setdefault(s["code"], {**s, "credits": "", "prerequisite": ""})
    # tiêu đề có cả mã: đường nhanh tìm thực thể theo cột tiêu đề -> "MAC103 bao nhiêu tín chỉ" khớp; hai môn trùng tên vẫn phân biệt
    head = ["Tên môn (kèm mã)", "Mã môn", "Tên môn", "Tên tiếng Anh", "Số tín chỉ", "Môn tiên quyết", "Thuộc chuyên ngành (học kỳ)", "Đề cương trên FLM",
            "Phương pháp dạy học", "Thời lượng học", "Thang điểm", "Điểm trung bình tối thiểu để qua môn", "Nhiệm vụ của sinh viên", "Công cụ",
            "Mô tả môn học", "Quyết định ban hành đề cương", "Ngày duyệt đề cương", "Link đề cương"]
    if full:
        head += ["Chuẩn đầu ra (CLO)", "Tài liệu", "Số buổi học"]
    subj = [head]
    clo = [["Tên CLO", "Mã môn", "Chuẩn đầu ra (CLO)", "Nội dung CLO"]]
    ass = [["Tên đầu điểm", "Mã môn", "Đầu điểm", "Hình thức", "Phần", "Trọng số", "Điều kiện hoàn thành", "Thời lượng", "CLO đánh giá", "Dạng câu hỏi",
            "Số câu hỏi", "Kiến thức và kỹ năng", "Hướng dẫn chấm", "Ghi chú"]]
    missing = "không có đề cương đang dùng trên FLM" if full else "chưa có đề cương công khai (chế độ khách)"
    for code, fs in frame_of.items():   # mọi môn trong khung; môn chưa có đề cương vẫn có tên / tín chỉ / kỳ từ khung
        syl = raw["syllabi"].get(code)
        if not syl:
            name, en = _split_name(fs["name"])
            subj.append([f"{code} · {name}", code, name, en, fs.get("credits", ""), _none(fs.get("prerequisite", "")), "; ".join(where.get(code, [])),
                         missing] + [""] * (len(head) - 8))
            continue
        i = syl["info"]
        name, en = _split_name(fs["name"] or i.get("Syllabus Name", code))
        row = [f"{code} · {name}", code, name, i.get("Course Name English") or en, i.get("NoCredit", "") or fs.get("credits", ""),
               _none(i.get("Pre-Requisite", "")), "; ".join(where.get(code, [])), "có", i.get("Learning-Teaching Method", ""),
               i.get("Time Allocation", ""), i.get("Scoring Scale", ""), i.get("MinAvgMarkToPass", ""), i.get("StudentTasks", ""), i.get("Tools", ""),
               i.get("Description", ""), i.get("DecisionNo MM/dd/yyyy", ""), i.get("ApprovedDate", ""),
               f"{BASE}/gui/role/guest/SyllabusDetails?sylID={syl['sylID']}"]
        if full:
            row += ["\n".join(f"{x['name']}: {x['details']}" for x in syl["clo"]), "\n".join(_material(m) for m in syl.get("materials") or []),
                    len(syl.get("schedule") or []) or ""]
        else:
            for x in syl["clo"]:
                clo.append([f"{code} · {x['name']}", code, x["name"], x["details"]])
        subj.append(row)
        for a in syl["assessment"]:
            ass.append([f"{code} · {a.get('Category', '')}" + (f" (phần {a['Part']})" if a.get("Part") else ""), code, a.get("Category", ""),
                        a.get("Type", ""), a.get("Part", ""), a.get("Weight", ""), a.get("Completion Criteria", ""), a.get("Duration", ""),
                        a.get("CLO", ""), a.get("Question Type", ""), a.get("No Question", ""), a.get("Knowledge and Skill", ""),
                        a.get("Grading Guide", ""), a.get("Note", "")])
    out = {"Chương trình": cur_rows, "PLO": plo_rows, "Khung chương trình": frame, "Môn học": subj}
    if not full:
        out["CLO"] = clo
    out["Đánh giá"] = ass
    return out


def schedule_md(raw: dict) -> str:
    """Chế độ đăng nhập: lịch từng buổi + câu hỏi thảo luận của mọi môn, mỗi môn một mục "#" (bộ chia văn bản chia theo mục).
    Link slide / tài liệu của buổi chỉ ghi LINK (không tải tệp)."""
    names = {}
    for c in raw["curricula"]:
        for s in list(c["subjects"]) + [x for g in c.get("groups") or [] for x in g["subjects"]]:
            names.setdefault(s["code"], _split_name(s["name"])[0])
    parts = ["# Lịch học và câu hỏi thảo luận (flm.fpt.edu.vn, chế độ đăng nhập)"]
    for code in sorted(raw["syllabi"]):
        syl = raw["syllabi"][code]
        sch, qs = syl.get("schedule") or [], syl.get("questions") or []
        if not sch and not qs:
            continue
        title = f"{code} · {names.get(code) or syl['info'].get('Syllabus Name', '')}"
        if sch:
            lines = [f"# {title}: lịch {len(sch)} buổi học"]
            for x in sch:
                bits = [f"Buổi {x.get('Session', '')}: {x.get('Topic', '')}"]
                for lab, k in (("hình thức", "Learning-Teaching Type"), ("CLO", "LO"), ("tài liệu", "Student Materials"), ("tải về", "S-Download"),
                               ("nhiệm vụ của sinh viên", "Student's Tasks")):
                    if x.get(k):
                        bits.append(f"{lab}: {x[k]}")
                links = [u for u in x.get("_links") or [] if u.startswith("http")]
                if links:
                    bits.append("link: " + " ".join(dict.fromkeys(links)))
                lines.append(" · ".join(bits))
            parts.append("\n".join(lines))
        if qs:
            parts.append("\n".join([f"# {title}: câu hỏi thảo luận"] +
                                   [f"{q.get('Name', '')} (buổi {q.get('Session No', '')}): {q.get('Details', '')}" for q in qs]))
    return "\n\n".join(parts) + "\n"


def write_xlsx(raw: dict, path: Path) -> dict:
    """Ghi workbook; trả số dòng mỗi sheet."""
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    counts = {}
    for name, rows in sheets(raw).items():
        ws = wb.create_sheet(name)
        for r in rows:
            ws.append([v[:MAX_CELL] if isinstance(v, str) else v for v in r])
        counts[name] = len(rows) - 1
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))
    return counts

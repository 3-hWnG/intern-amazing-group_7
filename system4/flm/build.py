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


def sheets(raw: dict) -> dict[str, list[list]]:
    cur_rows = [["Tên chuyên ngành", "Mã chương trình", "Chuyên ngành", "Tên chương trình", "Tổng số tín chỉ", "Số môn trong khung", "Quyết định ban hành", "Link FLM"]]
    # bảng con: cột "Tên …" duy nhất đứng đầu để ingest chọn đúng cột tiêu đề (ingest._title_score: duy nhất + có chữ "tên")
    plo_rows = [["Tên PLO", "Mã chương trình", "Chuyên ngành", "Chuẩn đầu ra (PLO)", "Nội dung PLO"]]
    frame = [["Tên môn trong khung", "Mã chương trình", "Chuyên ngành", "Mã môn", "Tên môn", "Học kỳ", "Số tín chỉ", "Môn tiên quyết (theo khung)"]]
    where: dict[str, list[str]] = {}
    for c in raw["curricula"]:
        major = _major(c.get("name") or c["info"].get("Name", ""))
        cur_rows.append([f"Chuyên ngành {major} ({c['code']})", c["code"], major, c.get("name") or c["info"].get("Name", ""), c.get("credits", ""), len(c["subjects"]),
                         c.get("decision", ""), f"{BASE}/gui/role/guest/CurriculumDetails?curid={c['curid']}"])
        for p in c["plo"]:
            plo_rows.append([f"{p['name']} · {major}", c["code"], major, p["name"], p["description"]])
        for s in c["subjects"]:
            frame.append([f"{s['code']} · {major}", c["code"], major, s["code"], _split_name(s["name"])[0], s["semester"], s["credits"],
                          "" if s["prerequisite"].lower() in ("none", "n/a", "không") else s["prerequisite"]])
            where.setdefault(s["code"], []).append(f"{major} (kỳ {s['semester']})")
    frame_of: dict[str, dict] = {}
    for c in raw["curricula"]:
        for s in c["subjects"]:
            frame_of.setdefault(s["code"], s)
    # tiêu đề có cả mã: đường nhanh tìm thực thể theo cột tiêu đề -> "MAC103 bao nhiêu tín chỉ" khớp; hai môn trùng tên vẫn phân biệt
    subj = [["Tên môn (kèm mã)", "Mã môn", "Tên môn", "Tên tiếng Anh", "Số tín chỉ", "Môn tiên quyết", "Thuộc chuyên ngành (học kỳ)", "Đề cương trên FLM", "Phương pháp dạy học",
             "Thời lượng học", "Thang điểm", "Điểm trung bình tối thiểu để qua môn", "Nhiệm vụ của sinh viên", "Công cụ", "Mô tả môn học",
             "Quyết định ban hành đề cương", "Ngày duyệt đề cương", "Link đề cương"]]
    clo = [["Tên CLO", "Mã môn", "Chuẩn đầu ra (CLO)", "Nội dung CLO"]]
    ass = [["Tên đầu điểm", "Mã môn", "Đầu điểm", "Hình thức", "Phần", "Trọng số", "Điều kiện hoàn thành", "Thời lượng", "CLO đánh giá", "Dạng câu hỏi",
            "Số câu hỏi", "Kiến thức và kỹ năng", "Hướng dẫn chấm", "Ghi chú"]]
    for code, fs in frame_of.items():   # mọi môn trong khung; môn chưa có đề cương công khai vẫn có tên / tín chỉ / kỳ từ khung
        syl = raw["syllabi"].get(code)
        if not syl:
            full, en = _split_name(fs["name"])
            pre = fs["prerequisite"]
            subj.append([f"{code} · {full}", code, full, en, fs["credits"], "" if pre.lower() in ("none", "n/a", "không") else pre, "; ".join(where.get(code, [])),
                         "chưa có đề cương công khai (chế độ khách)"] + [""] * (len(subj[0]) - 8))
            continue
        i = syl["info"]
        full, en = _split_name(fs["name"] or i.get("Syllabus Name", code))
        pre = i.get("Pre-Requisite", "")
        subj.append([f"{code} · {full}", code, full, i.get("Course Name English") or en, i.get("NoCredit", ""), "" if pre.lower() in ("none", "n/a", "không") else pre,
                     "; ".join(where.get(code, [])), "có", i.get("Learning-Teaching Method", ""), i.get("Time Allocation", ""), i.get("Scoring Scale", ""),
                     i.get("MinAvgMarkToPass", ""), i.get("StudentTasks", ""), i.get("Tools", ""), i.get("Description", ""),
                     i.get("DecisionNo MM/dd/yyyy", ""), i.get("ApprovedDate", ""), f"{BASE}/gui/role/guest/SyllabusDetails?sylID={syl['sylID']}"])
        for x in syl["clo"]:
            clo.append([f"{code} · {x['name']}", code, x["name"], x["details"]])
        for a in syl["assessment"]:
            ass.append([f"{code} · {a.get('Category', '')}" + (f" (phần {a['Part']})" if a.get("Part") else ""), code, a.get("Category", ""), a.get("Type", ""), a.get("Part", ""), a.get("Weight", ""), a.get("Completion Criteria", ""),
                        a.get("Duration", ""), a.get("CLO", ""), a.get("Question Type", ""), a.get("No Question", ""),
                        a.get("Knowledge and Skill", ""), a.get("Grading Guide", ""), a.get("Note", "")])
    return {"Chương trình": cur_rows, "PLO": plo_rows, "Khung chương trình": frame, "Môn học": subj, "CLO": clo, "Đánh giá": ass}


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

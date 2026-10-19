"""Đọc trang khách của FLM (flm.fpt.edu.vn, FPT University) thành dữ liệu thô — chỉ GET, ≤ 1 request/giây.

Trang dùng (chế độ khách, không đăng nhập):
  /gui/role/guest/ListCurriculum?educationLevel=fptu&searchOn=Code&keyword=<tiền tố>   danh sách khung chương trình
  /gui/role/guest/CurriculumDetails?curid=<id>        thông tin + PLO (gvPLO) + các môn (gvSubs: mã, tên, kỳ, tín chỉ, tiên quyết)
  /gui/role/guest/Syllabuses?subCode=<mã>&curriculumID=<id>   các phiên bản đề cương của môn -> SyllabusDetails?sylID=
  /gui/role/guest/SyllabusDetails?sylID=<id>           thông tin môn (bảng table-detail), CLO (gvLO), đánh giá (gvAssessment)
Khách KHÔNG xem được tài liệu (gvMaterial) và lịch buổi học (gvSchedule) — cần đăng nhập, leader không cho dùng tài khoản.
Chọn khung: mỗi tiền tố ngành (FLM_PROGRAMS, vd. BIT_SE, BIT_AI) lấy khung MỚI NHẤT (curid lớn nhất), bỏ bản _FNO.
"""
from __future__ import annotations

import re
import time
from typing import Callable
from urllib.parse import quote

from lxml import html as LH

BASE = "https://flm.fpt.edu.vn"
LIST = "/gui/role/guest/ListCurriculum?educationLevel=fptu&searchOn=Code&keyword="
DELAY = 1.0   # giây giữa hai request (lịch sự với máy chủ của trường)


class FlmError(Exception):
    pass


def _t(el) -> str:
    return " ".join(el.text_content().split()) if el is not None else ""


def _doc(text: str):
    doc = LH.fromstring(text)
    for bad in doc.xpath("//script|//style"):
        bad.drop_tree()
    return doc


def captcha_page(text: str, url: str = "") -> bool:
    return "guest-captcha" in url or 'class="g-recaptcha"' in text or "/gui/guest-captcha/continue" in text


def _rows(table) -> tuple[list[str], list[list]]:
    rows = table.xpath(".//tr")
    if not rows:
        return [], []
    head = [_t(c) for c in rows[0].xpath("./th|./td")]
    return head, [r.xpath("./td") for r in rows[1:]]


def parse_list(text: str) -> list[dict]:
    """Danh sách khung chương trình: [{code, name, decision, credits, curid}]."""
    out = []
    for t in _doc(text).xpath("//table"):
        head, rows = _rows(t)
        if "CurriculumCode" not in head:
            continue
        ix = {h: i for i, h in enumerate(head)}
        for cells in rows:
            link = next((a for a in cells[ix["CurriculumCode"]].xpath(".//a/@href") if "curid=" in a), None) \
                or next((a for c in cells for a in c.xpath(".//a/@href") if "curid=" in a), None)
            if not link:
                continue
            out.append({"code": _t(cells[ix["CurriculumCode"]]), "name": _t(cells[ix.get("Curriculum Name", 2)]),
                        "decision": _t(cells[ix.get("DecisionNo MM/dd/yyyy", 4)]) if len(cells) > 4 else "",
                        "credits": _t(cells[ix.get("Total Credit", 5)]) if len(cells) > 5 else "",
                        "curid": int(re.search(r"curid=(\d+)", link).group(1))})
    return out


def newest(items: list[dict], prefix: str) -> dict | None:
    """Khung mới nhất của một ngành: mã bắt đầu bằng tiền tố (BIT_SE khớp BIT_SE_K21C và BIT_SE-2026_K22B), bỏ bản _FNO."""
    p = prefix.upper()
    ok = [x for x in items if re.match(re.escape(p) + r"($|[-_ ])", x["code"].upper()) and "FNO" not in x["code"].upper()]
    return max(ok, key=lambda x: x["curid"]) if ok else None


def _detail_table(doc) -> dict:
    out = {}
    for t in doc.xpath("//table[contains(@class,'table-detail') or @id='table-detail']")[:1]:
        for r in t.xpath(".//tr"):
            c = r.xpath("./td|./th")
            if len(c) >= 2 and _t(c[0]).endswith(":"):
                out[_t(c[0])[:-1].strip()] = "\n".join(x.strip() for x in c[1].itertext() if x.strip())
    return out


def parse_curriculum(text: str) -> dict:
    doc = _doc(text)
    info = _detail_table(doc)
    plo, subjects = [], []
    for t in doc.xpath("//table[@id='gvPLO']"):
        for cells in _rows(t)[1]:
            if len(cells) >= 3:
                plo.append({"name": _t(cells[1]), "description": _t(cells[2])})
    for t in doc.xpath("//table[@id='gvSubs']"):
        head, rows = _rows(t)
        ix = {h: i for i, h in enumerate(head)}
        for cells in rows:
            if len(cells) < len(head):
                continue
            link = next(iter(cells[ix["Subject Code"]].xpath(".//a/@href") + [a for c in cells for a in c.xpath(".//a/@href")]), "")
            subjects.append({"code": _t(cells[ix["Subject Code"]]), "name": _t(cells[ix["Subject Name"]]),
                             "semester": _t(cells[ix["Semester"]]), "credits": _t(cells[ix["NoCredit"]]),
                             "prerequisite": _t(cells[ix["PreRequisite"]]), "link": link})
    return {"info": info, "plo": plo, "subjects": subjects}


def parse_syllabuses(text: str) -> list[dict]:
    """Các phiên bản đề cương của một môn; đề cương đang dùng (IsActive + IsApproved) đứng trước."""
    out = []
    for t in _doc(text).xpath("//table"):
        head, rows = _rows(t)
        if "Syllabus Name" not in head:
            continue
        ix = {h: i for i, h in enumerate(head)}
        for cells in rows:
            link = next((a for c in cells for a in c.xpath(".//a/@href") if "sylID=" in a), None)
            if not link:
                continue
            flag = lambda k: bool(cells[ix[k]].xpath(".//input[@checked]")) if k in ix else False
            out.append({"sylID": int(re.search(r"sylID=(\d+)", link).group(1)), "name": _t(cells[ix["Syllabus Name"]]),
                        "active": flag("IsActive"), "approved": flag("IsApproved"),
                        "decision": _t(cells[ix["DecisionNo"]]) if "DecisionNo" in ix else ""})
    return sorted(out, key=lambda x: (not (x["active"] and x["approved"]), not x["active"], -x["sylID"]))


def parse_syllabus(text: str) -> dict:
    doc = _doc(text)
    info = _detail_table(doc)
    clo, assess = [], []
    for t in doc.xpath("//table[@id='gvLO']"):
        for cells in _rows(t)[1]:
            if len(cells) >= 3:
                clo.append({"name": _t(cells[1]), "details": _t(cells[2])})
    for t in doc.xpath("//table[@id='gvAssessment']"):
        head, rows = _rows(t)
        for cells in rows:
            if len(cells) == len(head):
                assess.append({h: _t(c) for h, c in zip(head, cells) if h != "No."})
    return {"info": info, "clo": clo, "assessment": assess}


def collect(get: Callable[[str], tuple[int, str, str]], programs: list[str], step: Callable[[str], None] = lambda s: None,
            delay: float | None = None) -> dict:
    """get(path) -> (mã HTTP, url cuối, html). Trả dữ liệu thô của khung mới nhất mỗi ngành + đề cương từng môn (mỗi môn một lần)."""
    delay = DELAY if delay is None else delay
    last = [0.0]
    n_req = [0]

    def fetch(path: str) -> str:
        wait = delay - (time.time() - last[0])
        if wait > 0:
            time.sleep(wait)
        st, url, text = get(path)
        last[0] = time.time()
        n_req[0] += 1
        if captcha_page(text, url):
            raise FlmError("FLM đòi giải captcha lại (phiên khách hết hạn). Bấm Đồng bộ lại và tích captcha trong cửa sổ Chrome.")
        if st != 200:
            raise FlmError(f"{path}: HTTP {st}")
        return text

    curricula, syllabi = [], {}
    for prefix in programs:
        step(f"Tìm khung chương trình mới nhất của {prefix}…")
        cur = newest(parse_list(fetch(LIST + quote(prefix))), prefix)
        if not cur:
            raise FlmError(f"Không thấy khung chương trình nào có mã bắt đầu bằng {prefix}")
        step(f"Đọc khung {cur['code']}…")
        cur.update(parse_curriculum(fetch(f"/gui/role/guest/CurriculumDetails?curid={cur['curid']}")))
        curricula.append(cur)
    todo = {}
    for cur in curricula:
        for s in cur["subjects"]:
            todo.setdefault(s["code"], (s, cur["curid"]))
    for i, (code, (s, curid)) in enumerate(todo.items(), 1):
        step(f"Đề cương môn {i}/{len(todo)}: {code}…")
        path = s["link"] or f"/gui/role/guest/Syllabuses?subCode={quote(code)}&curriculumID={curid}"
        vers = parse_syllabuses(fetch(path))
        if not vers:   # môn tự chọn / nhóm môn (SE_GRA_ELE…) không có đề cương riêng
            continue
        syl = parse_syllabus(fetch(f"/gui/role/guest/SyllabusDetails?sylID={vers[0]['sylID']}"))
        syl["sylID"] = vers[0]["sylID"]
        syllabi[code] = syl
    return {"programs": programs, "curricula": curricula, "syllabi": syllabi, "requests": n_req[0]}

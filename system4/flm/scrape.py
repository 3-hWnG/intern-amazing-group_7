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
            dec = next((k for k in ix if k.startswith("DecisionNo")), None)
            out.append({"sylID": int(re.search(r"sylID=(\d+)", link).group(1)), "name": _t(cells[ix["Syllabus Name"]]),
                        "code": _t(cells[ix["Subject Code"]]) if "Subject Code" in ix else "",
                        "active": flag("IsActive"), "approved": flag("IsApproved"), "decision": _t(cells[ix[dec]]) if dec else ""})
    return sorted(out, key=lambda x: (not (x["active"] and x["approved"]), not x["active"], -x["sylID"]))


def _table_dicts(doc, tid: str, skip=("No.",), links: bool = False) -> list[dict]:
    out = []
    for t in doc.xpath(f"//table[@id='{tid}']"):
        head, rows = _rows(t)
        for cells in rows:
            if len(cells) != len(head):
                continue
            d = {h: _t(c) for h, c in zip(head, cells) if h not in skip}
            if links:   # chỉ lấy LINK (leader 19/10: không tải tệp đính kèm)
                hrefs = [a for c in cells for a in c.xpath(".//a/@href") if a and not a.startswith(("#", "javascript"))]
                d["_links"] = [BASE + a if a.startswith("/") else a for a in hrefs]
            out.append(d)
    return out


def parse_syllabus(text: str) -> dict:
    """Thông tin môn, CLO, đánh giá; khi ĐĂNG NHẬP có thêm tài liệu (gvMaterial), lịch từng buổi (gvSchedule), câu hỏi thảo luận (gvCQ)."""
    doc = _doc(text)
    info = _detail_table(doc)
    clo = [{"name": _t(c[1]), "details": _t(c[2])} for t in doc.xpath("//table[@id='gvLO']") for c in _rows(t)[1] if len(c) >= 3]
    return {"info": info, "clo": clo, "assessment": _table_dicts(doc, "gvAssessment"),
            "materials": _table_dicts(doc, "gvMaterial", links=True), "schedule": _table_dicts(doc, "gvSchedule", skip=(), links=True),
            "questions": _table_dicts(doc, "gvCQ")}


# ---------------------------------------------------------------- chế độ ĐĂNG NHẬP: mọi ngành, mọi môn
STUDENT = "/gui/role/student"
LIST_ALL = STUDENT + "/ListCurriculum?searchOn=Code&keyword=_"   # "_" khớp mọi mã khung (510 khung lúc 19/10/2026)


def program_key(code: str) -> str:
    """Mã khung -> mã ngành: "BIT_SE-2026_K22D_23A" / "BIT_SE_K21C" -> "BIT_SE"; "BBA_HM_K22C" -> "BBA_HM"; "PEN_A2" -> "PEN_A2"."""
    c = code.upper().replace(" ", "")
    return re.split(r"[-_]?(?:20\d\d[-_])?K\d|[-_]TỪ|\(|,", c)[0].rstrip("-_")


def newest_per_program(items: list[dict]) -> list[dict]:
    best: dict[str, dict] = {}
    for x in items:
        if "FNO" in x["code"].upper():
            continue
        k = program_key(x["code"])
        if k not in best or x["curid"] > best[k]["curid"]:
            best[k] = {**x, "program": k}
    return sorted(best.values(), key=lambda x: x["program"])


def parse_group_list(text: str, kind: str) -> list[int]:
    """Trang Combo / Elective của một khung -> id các nhóm (link /Compo/Detail/<id> hoặc /Elective/Detail/<id>)."""
    path = "/Compo/Detail/" if kind == "combo" else "/Elective/Detail/"
    return sorted({int(m) for m in re.findall(re.escape(path) + r"(\d+)", text)})


def parse_group(text: str) -> dict:
    """Chi tiết một combo / elective: tên + các môn (mã, tên, kỳ)."""
    doc = _doc(text)
    names, subs = {}, []
    for t in doc.xpath("//table"):
        head, rows = _rows(t)
        if "Subject Code" in head:
            ix = {h: i for i, h in enumerate(head)}
            for c in rows:
                if len(c) > ix["Subject Code"] and _t(c[ix["Subject Code"]]):
                    get = lambda k: _t(c[ix[k]]) if k in ix and len(c) > ix[k] else ""
                    subs.append({"code": get("Subject Code"), "name": get("Subject Name"), "semester": get("Semester")})
        else:
            for r in t.xpath(".//tr"):
                c = r.xpath("./td|./th")
                if len(c) >= 2:
                    names[_t(c[0]).rstrip(":").strip()] = _t(c[1])
    return {"name": names.get("Combo Name") or names.get("Elective Subject") or names.get("Name", ""), "subjects": subs}


class SylCache:
    """Bộ đệm của chế độ đăng nhập (runtime/flm/cache/full): mỗi khoá một tệp JSON đã PHÂN TÍCH (không lưu HTML). Lần đồng bộ bị ngắt
    (phiên hết hạn, mất mạng) chạy lại thì đi tiếp nhanh. Đề cương (syl_<id>) giữ 7 ngày; trang khung / combo / chỉ mục giữ 1 ngày."""

    def __init__(self, folder, ttl_days: float = 7):
        self.dir, self.ttl = folder, ttl_days
        if folder:
            folder.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str):
        return self.dir / (re.sub(r"[^\w.-]", "_", key) + ".json") if self.dir else None

    def load(self, key: str, ttl_days: float | None = None):
        p = self._path(key)
        if not p or not p.exists() or time.time() - p.stat().st_mtime > (self.ttl if ttl_days is None else ttl_days) * 86400:
            return None
        try:
            import json
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def store(self, key: str, data) -> None:
        p = self._path(key)
        if p:
            import json
            p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def get(self, syl_id: int) -> dict | None:
        return self.load(f"syl_{syl_id}")

    def put(self, syl_id: int, data: dict) -> None:
        self.store(f"syl_{syl_id}", data)


class SkipPage(Exception):
    """Trang bị chuyển về Login nhưng phiên vẫn còn: tài khoản không có quyền xem riêng trang này -> bỏ qua trang, đi tiếp."""


def collect_full(get: Callable[[str], tuple[int, str, str]], step: Callable[[str], None] = lambda s: None,
                 delay: float | None = None, cache: SylCache | None = None) -> dict:
    """ĐÃ ĐĂNG NHẬP: khung mới nhất của MỌI ngành (66 ngành lúc 19/10/2026) + combo / tự chọn + đề cương đầy đủ của mọi môn
    (thêm tài liệu, lịch từng buổi, câu hỏi thảo luận). ~1 + 66×(3 + số combo/tự chọn) + 26 + số môn request.
    Trang bị chuyển về Login: kiểm lại phiên bằng trang chủ — còn phiên thì BỎ QUA trang đó (ghi vào "skipped"), mất phiên thì dừng."""
    delay = DELAY if delay is None else delay
    cache = cache or SylCache(None)
    last, n_req, hits = [0.0], [0], [0]
    skipped: list[str] = []
    t0 = time.time()

    def raw_get(path: str) -> tuple[int, str, str]:
        wait = delay - (time.time() - last[0])
        if wait > 0:
            time.sleep(wait)
        out = get(path)
        last[0] = time.time()
        n_req[0] += 1
        return out

    bad = set(cache.load("bad_pages", 30) or [])   # trang làm FLM ĐĂNG XUẤT (thấy 19/10: khung LLB_LA_K22A, curid 2915) -> lần sau bỏ qua

    def fetch(path: str) -> str:
        if path in bad:
            skipped.append(path)
            raise SkipPage(path)
        st, url, text = raw_get(path)
        if "/Login" in url or "/SignIn" in url or captcha_page(text, url):
            _, hurl, home = raw_get("/Home")
            if "lbtnSignOut" in home and "/Login" not in hurl:
                skipped.append(path)
                raise SkipPage(path)
            bad.add(path)   # mất phiên đúng ở trang này: ghi lại để lần chạy sau bỏ qua (FLM hết phiên thật thì chỉ phí một trang)
            cache.store("bad_pages", sorted(bad))
            raise FlmError(f"Phiên đăng nhập FLM đã hết hạn (ở {path}). Bấm Đồng bộ đầy đủ lại và đăng nhập trong cửa sổ Chrome "
                           "(phần đã tải được giữ trong bộ đệm, lần sau đi tiếp nhanh và bỏ qua trang này).")
        if st != 200:
            raise FlmError(f"{path}: HTTP {st}")
        return text

    def cached(key: str, path: str, parse, ttl_days: float = 1):
        v = cache.load(key, ttl_days)
        if v is not None:
            hits[0] += 1
            return v
        v = parse(fetch(path))
        cache.store(key, v)
        return v

    step("Danh sách mọi khung chương trình…")
    curricula = newest_per_program(cached("list_all", LIST_ALL, parse_list))
    if not curricula:
        raise FlmError("Không đọc được danh sách khung chương trình (tài khoản không có quyền xem, hoặc FLM đổi giao diện)")
    groups: dict[str, dict] = {}
    kept = []
    for i, cur in enumerate(curricula, 1):
        step(f"Khung {i}/{len(curricula)}: {cur['code']}…")
        c = cur["curid"]
        try:
            cur.update(cached(f"cur_{c}", f"{STUDENT}/CurriculumDetails?curid={c}", parse_curriculum))
        except SkipPage:
            continue
        cur["groups"] = []
        for kind, lst, det in (("combo", "/Compo/ViewComBo?cur_id={c}", "/Compo/Detail/{g}?curriculumID={c}"),
                               ("elective", "/Elective/ViewElective?cur_id={c}", "/Elective/Detail/{g}?curriculumID={c}")):
            try:
                ids = cached(f"{kind}s_{c}", lst.format(c=c), lambda t, k=kind: parse_group_list(t, k))
            except SkipPage:
                continue
            for gid in ids:
                key = f"{kind}_{gid}"   # combo / tự chọn dùng chung giữa nhiều khung: đọc một lần
                if key not in groups:
                    try:
                        groups[key] = cached(key, det.format(g=gid, c=c), parse_group)
                    except SkipPage:
                        continue
                cur["groups"].append({"kind": kind, "id": gid, **groups[key]})
        kept.append(cur)
    index: dict[str, dict] = {}
    for k, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 1):   # mọi mã môn có chữ cái: 26 trang tìm kiếm = chỉ mục mọi đề cương đang dùng
        step(f"Chỉ mục đề cương {k}/26…")
        try:
            rows = cached(f"index_{ch}", f"{STUDENT}/SyllabusManagement?searchOn=Code&keyword={ch}", parse_syllabuses)
        except SkipPage:
            continue
        for s in rows:
            old = index.get(s["code"])
            if s["code"] and (old is None or (s["active"] and s["approved"], s["sylID"]) > (old["active"] and old["approved"], old["sylID"])):
                index[s["code"]] = s
    codes = sorted({s["code"] for c in kept for s in c["subjects"]} | {s["code"] for g in groups.values() for s in g["subjects"]})
    syllabi = {}
    todo = [c for c in codes if c in index]
    for i, code in enumerate(todo, 1):
        sid = index[code]["sylID"]
        syl = cache.get(sid)
        if syl is None:
            left = (len(todo) - i) * delay
            step(f"Đề cương {i}/{len(todo)}: {code}… (còn khoảng {int(left // 60)} phút)")
            try:
                syl = parse_syllabus(fetch(f"{STUDENT}/SyllabusDetails?sylID={sid}"))
            except SkipPage:
                continue
            cache.put(sid, syl)
        else:
            hits[0] += 1
        syllabi[code] = {**syl, "sylID": sid}
    return {"mode": "full", "programs": [c["program"] for c in kept], "curricula": kept, "syllabi": syllabi,
            "requests": n_req[0], "cached": hits[0], "skipped": skipped, "subjects": len(codes), "seconds": int(time.time() - t0)}


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

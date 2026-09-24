"""CỬA DUY NHẤT mà Hệ thống 2 (Backend) dùng để đọc CSDL thủ tục.

`search.py` đã lo phần khớp chữ (FTS5 ba tầng + `confident`). Tệp này lo phần
CÒN LẠI mà kiến trúc mới cần, và KHÔNG có ở tầng dưới:

    axes()            các trục MCQ có thật trong dữ liệu -> hỏi lại cho đúng
    derive_steps()    "checklist việc cần làm" (tick được) từ `Bước 1: … Bước 2: …`
    clean_fees()      gộp các dòng lệ phí rỗng/trùng của cổng
    build_record()    một bản ghi ĐÃ SẠCH, đủ để dựng bảng mà không cần SQL nữa

NGUYÊN TẮC: Backend KHÔNG viết câu SQL nào. Đổi schema thì chỉ sửa tệp này.

⚠️ GIỚI HẠN DỮ LIỆU THẬT (CSDL cấp Xã/Phường, 1.350 thủ tục — đừng hứa hơn thế):
  · `province` = tỉnh CÔNG BỐ bản đó (614 bản của UBND tỉnh, mã H…); NULL = bản
    của bộ/ngành (736). Là tỉnh công bố, KHÔNG phải "chỉ áp dụng ở" — nói đúng vậy.
  · `receiving_address` rỗng ở 842/1.350 ⇒ ô "địa điểm nộp" thường trống.
  · 476/2.029 `procedure_steps` có `name`; phần còn lại là một khối văn bản
    ⇒ các bước phải TÁCH LÚC ĐỌC, không có sẵn thành dòng.
Mọi chỗ thiếu đều đi kèm cờ `status_*` để tầng trên nói thật, không đoán.
"""

from __future__ import annotations

import json
import re
import sqlite3

from Database.pipeline import search as _search
from Database.pipeline.import_db import connect as _connect
from Database.pipeline.paths import STAGING_DIR

# ─────────────────────────────────────────────────────────────────── kết nối ──

def connect(db_path=None) -> sqlite3.Connection:
    """Kết nối CSDL thủ tục (chỉ đọc về mặt nghiệp vụ)."""
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ───────────────────────────────────────────────────────────────── tìm kiếm ──

def _tokens(text: str) -> set[str]:
    from Database.pipeline.textutil import fold
    return {t for t in re.split(r"[^0-9a-z]+", fold(text or "")) if t}


def refine(hits: list[dict], query: str) -> list[dict]:
    """Siết lại `term_overlap` / `confident` rồi xếp lại thứ tự.

    ⚠️ VÌ SAO KHÔNG DÙNG THẲNG SỐ CỦA `search.py` (đo thật, đừng bỏ bước này):
    `search._overlap()` so khớp bằng CHUỖI CON (`t in hay`), nên âm tiết ngắn
    lọt vào trong âm tiết dài:

        hỏi "đăng ký thường trú"
          "(Hà Nội) Đăng ký, cấp Giấy chứng nhận đối với TRƯỜNG hợp…"
           -> "tru" khớp nhờ nằm trong "truong"  -> overlap 0.75 -> confident ✅SAI

    Một kết quả SAI mà `confident=True` thì còn nguy hơn không tìm thấy: nó đi
    thẳng ra bảng, bỏ qua cả vòng hỏi lại lẫn lối thoát "không cái nào đúng".
    Ở đây so khớp theo TỪNG ÂM TIẾT trọn vẹn nên "tru" ≠ "truong".

    Xếp lại theo (tầng, độ khớp giảm dần, điểm bm25): `search.py` xếp thuần
    bm25 nên bản khớp đủ 4/4 âm tiết có thể bị đẩy xuống dưới bản khớp 3/4.
    """
    terms = [t for t in _tokens(query)]
    for h in hits:
        hay = _tokens(f"{h.get('name', '')} {h.get('domain', '')}")
        ov = sum(1 for t in terms if t in hay) / len(terms) if terms else 0.0
        h["term_overlap"] = round(ov, 2)
        h["confident"] = bool(h.get("match_tier") == 1 and ov >= 0.75)
        # Phủ phía TÊN (xem search.name_coverage): tie-break khi term_overlap
        # bằng nhau — "làm giấy khai sinh cho con" từng xếp "Khai thuế … xăng
        # SINH học" lên trên "Đăng ký khai sinh" vì cả hai cùng 0.67, chốt bằng bm25.
        h["name_hits"], cov = _search.name_coverage(terms, h.get("name", ""))
        h["name_cov"] = round(cov, 2)
    return sorted(hits, key=lambda h: (h["match_tier"], -h["term_overlap"], -h["name_cov"],
                                       h["score"]))


def _name_covered(h: dict) -> bool:
    return (h.get("name_hits", 0) >= _search.NAME_MIN_TERMS
            and h.get("name_cov", 0) >= _search.NAME_COVER)


def search(conn: sqlite3.Connection, query: str, limit: int = 8) -> list[dict]:
    """Trả về ứng viên kèm `confident` / `match_tier` / `term_overlap`."""
    return refine(_search.search(conn, query, limit * 3), query)[:limit]


def search_in_domain(conn: sqlite3.Connection, query: str, domain: str,
                     limit: int = 8) -> list[dict]:
    """Như `search`, nhưng lĩnh vực LLM chọn được dùng để XẾP HẠNG, KHÔNG để LỌC.

    ⚠️ ĐÂY LÀ BÀI HỌC ĐO ĐƯỢC, ĐỪNG ĐỔI NGƯỢC LẠI.
    Bản đầu lọc cứng theo `domain`. Thử với mô hình thật (Qwen2.5 1.5B):

        "t muốn dk kết hôn"
          -> primary_keyword = "đăng ký kết hôn"   ✅ ĐÚNG
             domain          = "Đất đai"           ❌ SAI

    Từ khoá chuẩn, nhưng lọc cứng theo lĩnh vực sai thì mọi thủ tục Hộ tịch bị
    vứt hết, còn lại toàn "đăng ký biến động quyền sử dụng đất". Chọn đúng 1
    trong 103 lĩnh vực là việc quá sức mô hình 1.5B, trong khi rút từ khoá thì
    nó làm tốt. Nên: cho lĩnh vực cộng điểm, không cho nó quyền loại bỏ.

    Thứ tự xếp: `match_tier` trước (độ khớp CHỮ, đáng tin), rồi mới tới lĩnh
    vực khớp hay không. Nhờ vậy một kết quả khớp tên ở tầng 1 dù "sai lĩnh vực"
    vẫn đứng trên kết quả tầng 3 "đúng lĩnh vực".
    """
    hits = refine(_search.search(conn, query, limit * 3), query)
    if domain:
        # Lĩnh vực chỉ là tiêu chí phụ, xếp SAU tầng khớp và độ khớp tên.
        hits = sorted(hits, key=lambda h: (h["match_tier"], -h["term_overlap"], -h["name_cov"],
                                           0 if h.get("domain") == domain else 1,
                                           h["score"]))
    return hits[:limit]


# ─────────────────────────────────────────── tra THẲNG bằng từ khoá (không LLM) ──
# Nhóm chốt (2026-09-24): tra bằng từ khoá là đường CHÍNH. LLM 1 chỉ được gọi
# khi từ khoá KHÔNG khớp được gì chắc chắn — tức câu hỏi mơ hồ/gõ sai ("đkj").
# Sai sót còn lại đã có MCQ "thủ tục chính → dạng cụ thể" hứng.

# Viết tắt hay gặp -> dạng đầy đủ (đã bỏ dấu). Chỉ những cái KHÔNG mơ hồ.
_ABBREV = {
    "dk": "dang ky", "dky": "dang ky", "gks": "giay khai sinh",
    "cccd": "can cuoc", "cmnd": "chung minh nhan dan", "gplx": "giay phep lai xe",
    "gpxd": "giay phep xay dung", "gcn": "giay chung nhan", "qsdd": "quyen su dung dat",
    "hkd": "ho kinh doanh", "bhxh": "bao hiem xa hoi", "bhyt": "bao hiem y te",
    "xd": "xay dung", "tthc": "",
}
# Lời đệm bỏ được khi tra từ khoá. CHỈ những âm tiết KHÔNG trùng chữ nghiệp vụ
# sau khi bỏ dấu — đừng gộp `_FILLER` vào đây: "hoi" vừa là "hỏi" vừa là "hồi"
# (thu hồi) và "hội"; "ban" là "bạn"/"bản sao"/"bán lẻ"; "tu" là "tư pháp".
# Bỏ nhầm những chữ đó là "thu hồi đất" thành "thu đất".
_QUERY_FILLER = set("toi minh muon t tao ko k hok dc duoc giup dum xin oi nhe nhi vay gi".split())
# Cách người dân gọi -> chữ trong TÊN thủ tục (`_SYNONYMS`, áp trước) và cụm bỏ
# nguyên cụm (`_DROP_PHRASES`; bỏ từng âm tiết sẽ hại "thu hồi", "bảo hiểm"…).
# Dữ liệu, không phải logic: sửa ở `staging/synonyms.json` (luật thêm ghi trong file).
_VOCAB = json.loads((STAGING_DIR / "synonyms.json").read_text(encoding="utf-8"))
_SYNONYMS: dict[str, str] = _VOCAB["synonyms"]
_DROP_PHRASES: tuple[str, ...] = tuple(_VOCAB["drop_phrases"])
# Chữ đứng sau "lam" trong tên thủ tục (đo cả kho 24/09): lâm nghiệp, làm việc, …
_LAM_NEXT = set("cong viec nhiem nghiep sinh thay con nghia dich chuyen tu dai chu nong"
                " lam do thu hoa thuy cho".split())

# Tỉnh/thành người dân hay nhắc (63 tên trước sáp nhập + tên gọi tắt). Nhắc tên
# tỉnh là NGỮ CẢNH để xếp bản của tỉnh đó lên trước, KHÔNG phải từ khoá tra —
# để nguyên trong câu thì tầng AND của FTS trượt hết bản toàn quốc.
_PROVINCE_NAMES = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bà Rịa Vũng Tàu", "Bạc Liêu", "Bắc Giang",
    "Bắc Kạn", "Bắc Ninh", "Bến Tre", "Bình Dương", "Bình Định", "Bình Phước",
    "Bình Thuận", "Cà Mau", "Cao Bằng", "Cần Thơ", "Đà Nẵng", "Đắk Lắk", "Đắk Nông",
    "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Giang", "Hà Nam", "Hà Nội",
    "Hà Tĩnh", "Hải Dương", "Hải Phòng", "Hậu Giang", "Hòa Bình", "Hưng Yên",
    "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", "Lâm Đồng", "Lạng Sơn",
    "Lào Cai", "Long An", "Nam Định", "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ",
    "Phú Yên", "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị",
    "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa",
    "Thừa Thiên Huế", "Huế", "Tiền Giang", "Hồ Chí Minh", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
]
# Cách gọi khác -> tên đúng như cột `province` trong CSDL.
_PROVINCE_ALIASES = {
    "tphcm": "Hồ Chí Minh", "hcm": "Hồ Chí Minh", "sai gon": "Hồ Chí Minh",
    "sg": "Hồ Chí Minh", "thanh pho ho chi minh": "Hồ Chí Minh",
    "thua thien hue": "Huế", "ba ria vung tau": "Bà Rịa - Vũng Tàu",
}


def _fold(text: str) -> str:
    from Database.pipeline.textutil import fold
    return re.sub(r"[^0-9a-z]+", " ", fold(text or "")).strip()


def _province_patterns() -> list[tuple[str, str]]:
    pats = {_fold(p): p for p in _PROVINCE_NAMES}
    pats.update(_PROVINCE_ALIASES)
    # Dài trước: "thai binh" phải thắng "binh".
    return sorted(pats.items(), key=lambda kv: -len(kv[0]))


_PROVINCE_PATTERNS = _province_patterns()


def parse_query(question: str) -> dict:
    """Câu hỏi -> {"keyword": chuỗi tra FTS, "provinces": [tỉnh được nhắc]}.

    Tất định, không LLM: bỏ tên tỉnh (giữ lại làm ngữ cảnh), bung viết tắt,
    bỏ lời đệm. "t người bình định muốn dk kết hôn"
        -> {"keyword": "nguoi dang ky ket hon", "provinces": ["Bình Định"]}
    """
    text = f" {_fold(question)} "
    provinces: list[str] = []
    for pat, name in _PROVINCE_PATTERNS:
        if f" {pat} " in text:
            text = text.replace(f" {pat} ", " ")
            if name not in provinces:
                provinces.append(name)
    for ph, to in _SYNONYMS.items():
        text = text.replace(f" {ph} ", f" {to} ")
    for ph in _DROP_PHRASES:
        text = text.replace(f" {ph} ", " ")

    words: list[str] = []
    for t in text.split():
        t = _ABBREV.get(t, t)
        words.extend(t.split())
    words = [w for w in words if w not in _QUERY_FILLER]
    # "làm …" đầu câu là lời nói, không phải tên: "làm giấy chứng tử" -> "lam khai tu"
    # từng ra thẳng "Khai thuế …". Giữ khi ghép thành chữ có trong tên thủ tục.
    if len(words) > 2 and words[0] == "lam" and words[1] not in _LAM_NEXT:
        words = words[1:]
    return {"keyword": " ".join(words), "provinces": provinces}


# Từ khoá khớp ≥ 75% số âm tiết trong TÊN một thủ tục = đủ để đưa ra MCQ, khỏi
# gọi LLM. (Không đòi tầng 1: "người … đăng ký kết hôn" có chữ "người" không
# nằm trong tên nhưng 4/5 âm tiết vẫn trúng "Thủ tục đăng ký kết hôn".)
STRONG_OVERLAP = 0.75


def is_strong(hits: list[dict]) -> bool:
    return any(h.get("term_overlap", 0) >= STRONG_OVERLAP for h in hits)


# Câu chỉ gồm những từ này là chào hỏi/xã giao, dù tình cờ khớp tên thủ tục nào
# đó ("bạn tên gì" -> "bản" + "tên" có trong "Cấp bản sao… đổi tên…").
_CHITCHAT = set(
    "chao xin hello hi alo cam on ban ten la ai khoe khong ok oke vang da tam biet bye"
    " thanks thank you tro ly may co the lam duoc gi giup nhe a oi nha".split())


# Cụm xã giao chứa chữ trùng tên thủ tục: "mình cần HỖ TRỢ" khớp "HỖ TRỢ chi phí
# hoả táng…" (bắt được ở bản chạy thật). Bỏ nguyên cụm trước khi xét.
_CHAT_PHRASES = ("can ho tro", "ho tro minh", "ho tro toi", "ho tro em", "ho tro voi",
                 "giup do", "can giup", "giup minh", "giup toi", "tu van")


def _without_chat_phrases(question: str) -> str:
    text = f" {_fold(question)} "
    for ph in _CHAT_PHRASES:
        text = text.replace(f" {ph} ", " ")
    return text.strip()


def is_chitchat(question: str) -> bool:
    """Chỉ chào hỏi / cảm ơn / xã giao — không có từ nghiệp vụ nào."""
    words = parse_query(_without_chat_phrases(question))["keyword"].split()
    return all(w in _CHITCHAT for w in words)


# Bộ nhận diện chỉ GỢI Ý (bỏ sót thì người dân không biết có nút 🎯; gợi ý thừa
# chỉ tốn một dòng chữ) -> nới hơn ngưỡng tra thật. "làm giấy khai sinh cho con"
# chỉ khớp 3/5 âm tiết với "… Giấy khai sinh" vì "làm/cho/con" không bỏ được
# ("lâm nghiệp", "cho thuê", "cha, mẹ, con").
DETECT_OVERLAP = 0.6
DETECT_MIN_TERMS = 2


def looks_like_procedure(conn: sqlite3.Connection, question: str) -> dict | None:
    """Bộ nhận diện SONG SONG của Proposal: câu này có vẻ đang hỏi thủ tục không?

    Nhóm chốt: dùng LUẬT THEO CSDL, không dùng LLM — cùng lý do với bộ gác
    `newProcedure` (PHASE2 §4.6: Qwen 1.5B phân biệt 0%), và chạy trên MỌI tin
    nhắn thường nên phải nhanh. Luật: sau khi bỏ lời đệm, từ khoá khớp
    ≥ `DETECT_OVERLAP` và ít nhất `DETECT_MIN_TERMS` âm tiết vào tên một thủ tục.
    Trả {"proc_id", "label"} của ứng viên đầu (chỉ để ghi vết), None nếu không.
    """
    q = parse_query(_without_chat_phrases(question))
    words = q["keyword"].split()
    if not words or all(w in _CHITCHAT for w in words):
        return None
    need = min(DETECT_MIN_TERMS, len(set(words)))
    hits = [h for h in search(conn, q["keyword"], 10)
            if (h.get("term_overlap", 0) >= DETECT_OVERLAP
                and round(h["term_overlap"] * len(set(words))) >= need)
            or _name_covered(h)]
    if not hits:
        return None
    idx = family_index(conn)
    head = idx["head_of"].get(hits[0]["proc_id"], "")
    return {"proc_id": hits[0]["proc_id"], "label": idx["label"].get(head, hits[0]["name"])}


# ─────────────────────────────── nhóm "THỦ TỤC CHÍNH" -> các "dạng cụ thể" ──
# Nhóm chốt: xếp hạng không cần hoàn hảo, vì đã được hỏi MCQ — nên hỏi người
# dân chọn THỦ TỤC CHÍNH trước, rồi mới chọn DẠNG cụ thể của nó:
#
#   "khai sinh" -> MCQ 1: [Đăng ký khai sinh] [Khai thuế tiêu thụ đặc biệt…] …
#               -> MCQ 2: [Thủ tục đăng ký khai sinh] [… lưu động]
#                         [… kết hợp nhận cha, mẹ, con] [… có yếu tố nước ngoài] …
#
# MCQ 2 lấy TOÀN BỘ thành viên của nhóm trong CSDL, không chỉ những cái FTS moi
# ra — nhờ vậy bản gốc "Thủ tục đăng ký khai sinh" có mặt kể cả khi xếp hạng
# đẩy nó ra khỏi top (đo thật: nó không lọt top 5 cho câu "khai sinh").
#
# "Thủ tục chính" của một tên = tên NGẮN NHẤT trong kho là tiền tố của nó (tính
# theo từ, đã bỏ "Thủ tục", tiền tố tỉnh "Quảng Ninh - ", đuôi "(Cấp xã)").
# Bản địa phương trùng tên với bản của bộ => rơi vào cùng một nhóm.

AXIS_FAMILY = "family"
_MIN_HEAD_WORDS = 3          # "Đăng ký" trơn không được làm thủ tục chính
# Tiền tố tỉnh của bản địa phương: "Quảng Ninh - …" hoặc "(Hà Nội) …".
#   "Thái Nguyên (cấp xã) - …" cũng có. Chỉ áp cho bản CÓ `province`.
_PREFIX_RE = re.compile(r"^(?:\([^)]{2,30}\)\s*|[^-–]{2,40}?\s[-–]\s)")
_TRAIL_RE = re.compile(r"\s*\((?:cap|thuoc tham quyen)[^)]*\)\s*$")

_family_cache: dict = {}


def _base(name: str, province: str | None) -> str:
    raw = (name or "").strip()
    if province and _PREFIX_RE.match(raw):
        raw = _PREFIX_RE.sub("", raw, count=1)
    b = _fold(raw)
    b = re.sub(r"^thu tuc\s+", "", b)
    return _TRAIL_RE.sub("", b).strip()


def _display(name: str, province: str | None) -> str:
    """Tên hiển thị của thủ tục chính: bỏ tiền tố tỉnh và chữ "Thủ tục" đầu câu."""
    raw = (name or "").strip()
    if province and _PREFIX_RE.match(raw):
        raw = _PREFIX_RE.sub("", raw, count=1)
    raw = re.sub(r"^(?:Thủ tục|thủ tục)\s*:?\s*", "", raw).strip()
    return raw[:1].upper() + raw[1:]


def family_index(conn: sqlite3.Connection) -> dict:
    """{head_of: {proc_id: head}, members: {head: [proc_id]}, info: {proc_id: {...}},
        label: {head: tên hiển thị}}. Tính một lần, dựng lại khi CSDL đổi."""
    stamp = conn.execute("SELECT COUNT(*), MAX(row_id) FROM procedures"
                         " WHERE status='active'").fetchone()
    stamp = tuple(stamp)
    if _family_cache.get("stamp") == stamp:
        return _family_cache["index"]

    info = {r["proc_id"]: dict(r) for r in conn.execute(
        "SELECT proc_id, name, domain, province, department_promulgate, agency_levels,"
        "       executing_agency FROM procedures WHERE status='active'")}
    base = {pid: _base(r["name"], r["province"]) for pid, r in info.items()}

    # Ứng viên làm "đầu nhóm" gom theo 3 từ đầu -> khỏi so O(n²) cả kho.
    by_lead: dict[str, list[str]] = {}
    for b in set(base.values()):
        if len(b.split()) >= _MIN_HEAD_WORDS:
            by_lead.setdefault(" ".join(b.split()[:_MIN_HEAD_WORDS]), []).append(b)
    for lst in by_lead.values():
        lst.sort(key=len)

    head_of: dict[str, str] = {}
    for pid, b in base.items():
        head = b
        for cand in by_lead.get(" ".join(b.split()[:_MIN_HEAD_WORDS]), []):
            if b == cand or b.startswith(cand + " "):
                head = cand
                break
        head_of[pid] = head

    members: dict[str, list[str]] = {}
    for pid, h in head_of.items():
        members.setdefault(h, []).append(pid)

    label: dict[str, str] = {}
    for h, pids in members.items():
        # Tên đẹp nhất: thành viên có base == head, ưu tiên bản của bộ (không tỉnh).
        exact = [p for p in pids if base[p] == h] or pids
        exact.sort(key=lambda p: (info[p]["province"] is not None, len(info[p]["name"])))
        label[h] = _display(info[exact[0]]["name"], info[exact[0]]["province"])

    index = {"head_of": head_of, "members": members, "info": info, "label": label}
    _family_cache.update(stamp=stamp, index=index)
    return index


# Lĩnh vực mà cổng gắn cấp Xã/Phường nhưng hồ sơ do NGÀNH DỌC giải quyết, không
# phải UBND phường. Nhóm chốt: giữ lại, nhưng nói rõ ở mọi chỗ người dân nhìn thấy.
VERTICAL_DOMAINS = {"Thuế": "cơ quan Thuế", "Hải quan": "cơ quan Hải quan"}


def vertical_agency(domain: str) -> str:
    """"cơ quan Thuế" nếu thủ tục thuộc lĩnh vực ngành dọc, "" nếu không."""
    for part in (domain or "").split(";"):
        if part.strip() in VERTICAL_DOMAINS:
            return VERTICAL_DOMAINS[part.strip()]
    return ""


def publisher_tag(info: dict) -> str:
    """Nhãn ngắn cho MCQ: ai công bố bản này."""
    if info.get("province"):
        return f"Bản do {info.get('department_promulgate') or 'UBND ' + info['province']} công bố"
    return "Bản chung toàn quốc"


def _province_rank(info: dict, preferred: list[str]) -> int:
    """0 = đúng tỉnh người dân nhắc · 1 = bản toàn quốc · 2 = tỉnh khác."""
    p = info.get("province")
    if p and _fold(p) in {_fold(x) for x in preferred}:
        return 0
    return 1 if not p else 2


def axes_for_families(conn: sqlite3.Connection, hits: list[dict],
                      low_confidence: bool = False,
                      provinces: list[str] | None = None) -> list[dict]:
    """MCQ 1 — "thủ tục chính". Rỗng nếu chỉ có một nhóm hoặc nhóm đầu thắng rõ
    (và đang chắc chắn) — xem `_clear_winner`.

    `low_confidence=True` (từ khoá lẫn LLM 1 đều không khớp chắc) -> thêm lựa
    chọn "không có cái nào đúng" để người dùng thoát ra nhánh xin lỗi.
    VÌ SAO PHẢI CÓ LỐI THOÁT ĐÓ (đo thật, không đoán):
        "thẻ căn cước cho trẻ em"   -> tier 3, overlap 0.67   ← câu hỏi THẬT
        "đăng ký bay lên sao Hỏa"   -> tier 3, overlap 0.67   ← câu hỏi RÁC
    Không ngưỡng nào tách nổi hai câu này, nên cứ hiện thứ tìm được RỒI ĐỂ
    NGƯỜI DÙNG nói "không phải cái này". Thà tốn một cú bấm còn hơn trả nhầm.
    """
    idx = family_index(conn)
    heads: list[str] = []
    for h in hits:
        head = idx["head_of"].get(h["proc_id"])
        if head and head not in heads:
            heads.append(head)
    if not heads or (len(heads) == 1 and not low_confidence):
        return []
    if not low_confidence and _clear_winner(hits, idx):
        return []

    # Nhóm CHỈ có bản của tỉnh khác (không có bản toàn quốc, không có bản của
    # tỉnh người dân nhắc) xuống cuối — giữ thứ tự FTS trong cùng hạng. Nhưng
    # chỉ trong cùng TẦNG khớp: "thiết bị giám sát hành trình tàu cá" khớp đủ
    # 100% ở tầng 1 chỉ có bản tỉnh, từng bị rác tầng 3 toàn quốc đẩy khỏi top.
    preferred = provinces or []
    tier = {}
    for h in hits:
        tier.setdefault(idx["head_of"].get(h["proc_id"]), h.get("match_tier", 3))
    heads.sort(key=lambda h: (tier.get(h, 3) > 1,
                              min(_province_rank(idx["info"][p], preferred)
                                  for p in idx["members"][h])))

    options = []
    for head in heads[:6]:
        pids = idx["members"][head]
        first = idx["info"][pids[0]]
        bits = [first.get("domain") or ""]
        if len(pids) > 1:
            bits.append(f"{len(pids)} dạng cụ thể")
        elif first.get("province"):
            bits.append(f"bản của {first['province']}")
        va = vertical_agency(first.get("domain", ""))
        if va:
            bits.append(f"do {va} giải quyết")
        options.append({"value": head, "label": idx["label"][head],
                        "hint": " · ".join(b for b in bits if b)})

    question = "Bạn cần làm thủ tục nào?"
    if low_confidence:
        question = "Mình không chắc lắm — có phải bạn cần một trong những thủ tục này không?"
        options.append({"value": NONE_OF_THESE, "label": "Không có thủ tục nào đúng ý tôi",
                        "hint": "Mình sẽ nói rõ vì sao chưa tìm được"})
    return [{"axis": AXIS_FAMILY, "question": question,
             "memorable": False, "options": options}]


def _clear_winner(hits: list[dict], idx: dict) -> bool:
    """Nhóm đầu thắng rõ -> khỏi hỏi MCQ 1. Thắng rõ = khớp tầng 1 và
    (a) không nhóm nào khác khớp tầng 1 ("trích lục khai sinh"), hoặc
    (b) câu hỏi phủ HẾT tên nhóm đầu mà không phủ hết tên nhóm nào khác
        ("đăng ký kết hôn" thắng "Đăng ký lại kết hôn")."""
    best: dict[str, dict] = {}
    for h in hits:
        best.setdefault(idx["head_of"].get(h["proc_id"], ""), h)
    top, *rest = best.values()

    def strong(h: dict) -> bool:
        return h.get("match_tier") == 1 and h.get("term_overlap", 0) >= STRONG_OVERLAP

    if not strong(top):
        return False
    rivals = [h for h in rest if strong(h)]
    return not rivals or (top.get("name_cov", 0) >= 1
                          and all(h.get("name_cov", 0) < 1 for h in rivals))


def family_of(conn: sqlite3.Connection, proc_id: str) -> str:
    return family_index(conn)["head_of"].get(proc_id, "")


def axis_for_variants(conn: sqlite3.Connection, head: str,
                      provinces: list[str] | None = None,
                      limit: int = 8) -> dict | None:
    """MCQ 2 — "dạng cụ thể" trong một thủ tục chính. None nếu chỉ có một dạng.

    Xếp: bản của tỉnh người dân nhắc -> bản toàn quốc -> bản tỉnh khác;
    trong cùng hạng thì tên ngắn (bản gốc) đứng trước.
    """
    idx = family_index(conn)
    pids = list(idx["members"].get(head, []))
    if len(pids) < 2:
        return None
    preferred = provinces or []
    pids.sort(key=lambda p: (_province_rank(idx["info"][p], preferred),
                             len(idx["info"][p]["name"])))
    options, used = [], set()
    for p in pids[:limit]:
        inf = idx["info"][p]
        label = _display(inf["name"], inf["province"])
        # Nút MCQ gửi về đúng NHÃN, nên hai nhãn trùng nhau (bản bộ + bản tỉnh
        # cùng tên) sẽ luôn trỏ vào cái đầu. Gắn tên tỉnh cho khác nhau.
        if label in used:
            label = f"{label} ({inf['province'] or 'toàn quốc'})"
        k = 2
        while label in used:
            label, k = f"{label} #{k}", k + 1
        used.add(label)
        options.append({"value": p, "label": label, "hint": publisher_tag(inf)})
    return {"axis": AXIS_PROCEDURE,
            "question": f"“{idx['label'][head]}” có {len(pids)} dạng — bạn cần dạng nào?",
            "memorable": False, "options": options}


def only_member(conn: sqlite3.Connection, head: str) -> str:
    pids = family_index(conn)["members"].get(head, [])
    return pids[0] if len(pids) == 1 else ""


# ────────────────────────────────────────────────── làm sạch từng mảnh dữ liệu ──

# Cổng nhồi hết các bước vào MỘT ô văn bản, và dùng ba kiểu đánh dấu khác nhau.
# Đo trên 1.407 thủ tục: chỉ ~43% dùng "Bước N", số còn lại dùng "a) b)" hoặc
# gạch đầu dòng. Thử lần lượt, kiểu nào tách được thì dừng.
_STEP_SPLIT = re.compile(r"(?=\bB[ưu]ớc\s*\d+\s*[:.\-])", re.IGNORECASE)
_STEP_LABEL = re.compile(r"^\s*(B[ưu]ớc\s*\d+)\s*[:.\-]\s*", re.IGNORECASE)
# "a) Nộp hồ sơ TTHC: … b) Giải quyết TTHC: …"
_ALPHA_SPLIT = re.compile(r"(?=(?:^|\s)[a-zđ]\)\s*[A-ZĐÀ-Ỹ])")
_ALPHA_LABEL = re.compile(r"^\s*([a-zđ]\))\s*")
# "- Nếu lựa chọn hình thức… - Nếu lựa chọn hình thức…"
# Bắt buộc có chữ HOA ngay sau để không cắt nhầm dấu gạch nối giữa câu
# ("Bộ Tư pháp - Cục Hộ tịch" phải giữ nguyên).
_DASH_SPLIT = re.compile(r"(?:^|\s)[-+•]\s+(?=[A-ZĐÀ-Ỹ])")

_CUTS = ((_STEP_SPLIT, _STEP_LABEL), (_ALPHA_SPLIT, _ALPHA_LABEL), (_DASH_SPLIT, None))


def _split_steps(text: str) -> list[tuple[str, str]]:
    """-> [(nhãn, nội dung)]. Trả về một phần tử nếu không tách được."""
    text = (text or "").strip()
    if not text:
        return []
    for splitter, labeller in _CUTS:
        parts = [p.strip(" .;\n\t") for p in splitter.split(text) if p and p.strip()]
        parts = [p for p in parts if len(p) > 1]
        if len(parts) < 2:
            continue
        out = []
        for p in parts:
            m = labeller.match(p) if labeller else None
            out.append((m.group(1).strip(), p[m.end():].strip()) if m else ("", p))
        return [(lab, body) for lab, body in out if body]
    return [("", text)]


def derive_steps(record: dict) -> list[dict]:
    """"Checklist những việc cần làm" — mỗi phần tử là MỘT ô tick được.

    Ba nguồn, xét theo thứ tự tin cậy giảm dần:
      1. `procedure_steps` có `name`  -> dùng thẳng, đã là từng bước riêng.
      2. `procedure_steps` không tên  -> tách khối mô tả theo "Bước N:".
      3. không có bước nào            -> tách `description` của thủ tục.
    """
    out: list[dict] = []

    named = [s for s in record.get("steps", []) if (s.get("name") or "").strip()]
    if named:
        for s in named:
            out.append({"label": (s.get("name") or "").strip(),
                        "detail": (s.get("description") or "").strip()})
        return out

    blob = "\n".join((s.get("description") or "") for s in record.get("steps", []))
    if not blob.strip():
        blob = record.get("description", "") or ""

    return [{"label": label, "detail": detail} for label, detail in _split_steps(blob)]


def clean_fees(record: dict) -> list[dict]:
    """Gộp lệ phí trùng và bỏ dòng rỗng.

    Cổng hay trả 3 dòng `{fee_type: FEE, amount_value: 0.0, amount_text: ''}`
    giống hệt nhau cho cùng một thủ tục. Hiện cả ba là nhiễu, không phải dữ liệu.
    """
    seen: set[tuple] = set()
    out: list[dict] = []
    for f in record.get("fees", []):
        text = (f.get("amount_text") or "").strip()
        value = f.get("amount_value")
        key = (f.get("fee_type") or "", value, text, (f.get("submission_method") or ""))
        if key in seen:
            continue
        seen.add(key)
        # Không số, không chữ -> không mang thông tin gì.
        if not text and (value is None or value == 0):
            continue
        out.append({"fee_type": f.get("fee_type") or "",
                    "amount_value": value,
                    "amount_text": text,
                    "submission_method": (f.get("submission_method") or "").strip()})

    # Mọi dòng đều 0 đồng và KHÔNG ghi chú -> KHÔNG được suy ra "miễn phí".
    # Nhóm chốt (2026-09-24): nói thẳng là CHƯA CÓ THÔNG TIN. Trả rỗng; tầng
    # bảng thấy `fees` gốc có dòng mà bản sạch rỗng thì hiện câu `FEES_UNCLEAR`.
    return out


def clean_files(record: dict) -> list[dict]:
    """Chỉ giữ tệp TẢI ĐƯỢC. `file_available=0` = có tên nhưng cổng trả 0 byte."""
    return [{"file_id": f.get("file_id") or "",
             "name": f.get("file_name") or "",
             "description": (f.get("belongs_to") or "").strip(),
             "local_path": f.get("local_path") or ""}
            for f in record.get("files", []) if f.get("file_available")]


# ───────────────────────────────────────────────────────────── các trục MCQ ──
# CHỈ sinh trục khi dữ liệu THẬT SỰ phân nhánh. Hỏi lại một câu chỉ có một đáp
# án là bắt người dân bấm thừa.

AXIS_PROCEDURE = "procedure"        # thủ tục nào trong các ứng viên
AXIS_CASE = "case"                  # trường hợp nào (executionCase)
AXIS_SUBJECT = "subject"            # bạn là ai
AXIS_LEVEL = "agency_level"         # nộp ở cấp nào

# Trục MÔ TẢ NGƯỜI DÙNG -> nhớ được cho lần sau.
# Trục MÔ TẢ CÂU HỎI (thủ tục nào, trường hợp nào) -> KHÔNG BAO GIỜ nhớ:
# nhớ "lần trước bạn chọn Đăng ký kết hôn" rồi áp cho câu hỏi khác là trả lời sai.
MEMORABLE_AXES = (AXIS_SUBJECT, AXIS_LEVEL)

AXIS_QUESTION = {
    AXIS_PROCEDURE: "Bạn cần thủ tục nào trong số này?",
    AXIS_CASE: "Bạn thuộc trường hợp nào?",
    AXIS_SUBJECT: "Bạn thực hiện thủ tục với tư cách nào?",
    AXIS_LEVEL: "Bạn nộp hồ sơ ở cấp nào?",
}


# ⚠️ `procedure_cases.case_name` KHÔNG phải lúc nào cũng là một "trường hợp".
# Đo trên 939 case có tên: cổng trộn hai thứ khác hẳn nhau vào cùng một chỗ —
#   (a) NHÁNH THẬT      "(1) Đối với công trình theo tuyến", "Trường hợp ủy quyền…"
#   (b) TIÊU ĐỀ MỤC     "* Giấy tờ phải nộp:", "* Giấy tờ phải xuất trình:", "* Lưu ý:"
# Loại (b) chiếm ~20%. Đem nó ra hỏi "Bạn thuộc trường hợp nào? → * Giấy tờ phải
# nộp:" là hỏi vô nghĩa, và lọc hồ sơ theo nó thì giấu mất nửa số giấy tờ.
# Chỉ nhận loại (a); gặp loại (b) thì KHÔNG hỏi và hiện TOÀN BỘ thành phần hồ sơ.
_HEADER_PHRASES = {
    "giay to phai nop", "giay to phai xuat trinh", "giay to can xuat trinh",
    "giay to khac", "thanh phan ho so", "ho so gom", "ho so bao gom",
    "luu y", "ghi chu", "so luong ho so", "cach thuc thuc hien",
}
_MARKER = re.compile(r"^[\s*\-+•()\d.]+")


def _is_real_case(name: str) -> bool:
    """Tên này là một NHÁNH người dùng chọn được, hay chỉ là tiêu đề mục?"""
    from Database.pipeline.textutil import fold
    body = _MARKER.sub("", (name or "").strip())
    key = fold(body).strip(" :.-").strip()
    if not key or len(key) < 3:
        return False
    return key not in _HEADER_PHRASES


def cases_for(conn: sqlite3.Connection, row_id: int,
              real_only: bool = False) -> list[dict]:
    """`real_only=True` -> chỉ các nhánh hỏi được (xem `_is_real_case`)."""
    rows = [dict(r) for r in conn.execute(
        "SELECT ordinal, case_name, n_components FROM procedure_cases"
        " WHERE row_id = ? AND TRIM(case_name) <> '' ORDER BY ordinal", (row_id,))]
    if real_only:
        rows = [r for r in rows if _is_real_case(r["case_name"])]
    return rows


def subjects_for(conn: sqlite3.Connection, row_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT TRIM(subject_name) AS s FROM procedure_subjects"
        " WHERE row_id = ? AND TRIM(subject_name) <> '' ORDER BY s", (row_id,))
    return [r["s"] for r in rows]


def levels_for(record: dict) -> list[str]:
    raw = (record.get("agency_levels") or "").split(",")
    return [lv.strip() for lv in raw if lv.strip()]


# Giá trị của lựa chọn "không có cái nào đúng ý tôi".
NONE_OF_THESE = "__none__"


def axes_for_record(conn: sqlite3.Connection, record: dict) -> list[dict]:
    """Các trục còn phân nhánh BÊN TRONG một thủ tục đã chốt."""
    axes: list[dict] = []
    row_id = record["row_id"]

    cases = cases_for(conn, row_id, real_only=True)
    if len(cases) > 1:
        axes.append({
            "axis": AXIS_CASE, "question": AXIS_QUESTION[AXIS_CASE],
            "memorable": False,      # trường hợp gắn với THỦ TỤC, không với người
            "options": [{"value": str(c["ordinal"]),
                         # Bỏ "*", "-", "(1)" ở đầu: đó là ký hiệu trình bày của
                         # cổng, người dân đọc lên thấy rối chứ không thêm nghĩa.
                         "label": _MARKER.sub("", c["case_name"]).strip(" :") or c["case_name"],
                         "hint": f"{c['n_components']} giấy tờ" if c["n_components"] else ""}
                        for c in cases[:6]]})

    subjects = subjects_for(conn, row_id)
    if len(subjects) > 1:
        axes.append({
            "axis": AXIS_SUBJECT, "question": AXIS_QUESTION[AXIS_SUBJECT],
            "memorable": True,
            "options": [{"value": s, "label": s, "hint": ""} for s in subjects[:6]]})

    # KHÔNG hỏi trục "nộp cấp nào" nữa: CSDL giờ chỉ gồm thủ tục cấp Xã/Phường
    # (level=COMMUNE), và đáp án của trục này không đổi được ô nào trong bảng —
    # hỏi là bắt người dân bấm thừa. Cấp nộp vẫn hiện trong bảng (`scope`).
    return axes


# ─────────────────────────────────────────────────────── bản ghi đã làm sạch ──

def build_record(conn: sqlite3.Connection, proc_id: str,
                 case_ordinal: int | None = None) -> dict | None:
    """Bản ghi ĐẦY ĐỦ + ĐÃ SẠCH cho một thủ tục. None nếu không có bản active.

    `case_ordinal` là đáp án MCQ trục "trường hợp": lọc thành phần hồ sơ đúng
    nhánh người dùng chọn. `checklist_items.case_ordinal` đã mang sẵn trục này
    từ Phase 1, nên lọc ở đây không mất mát gì.
    """
    rec = _search.find_by_primary_key(conn, proc_id)
    if rec is None:
        return None

    rec["cases"] = cases_for(conn, rec["row_id"])
    rec["subjects"] = subjects_for(conn, rec["row_id"])
    rec["levels"] = levels_for(rec)
    rec["online_services"] = [dict(r) for r in conn.execute(
        "SELECT service_code, service_name, processing_qty, processing_unit"
        "  FROM online_services WHERE row_id = ? ORDER BY id", (rec["row_id"],))]

    components = rec.get("checklist", [])
    if case_ordinal is not None:
        picked = [c for c in components if c.get("case_ordinal") == case_ordinal]
        # -1 = giấy tờ dùng chung cho mọi trường hợp, luôn phải nộp.
        shared = [c for c in components if c.get("case_ordinal") == -1]
        if picked:
            components = shared + picked
    rec["components"] = components

    rec["fees_clean"] = clean_fees(rec)
    rec["files_clean"] = clean_files(rec)
    rec["steps_clean"] = derive_steps(rec)
    return rec


# ────────────────────────────────────────── gác phạm vi (`newProcedure`) ──
# Người dân đang xem bảng của MỘT thủ tục mà hỏi sang thủ tục KHÁC thì phải mời
# họ mở ô chat mới, kẻo mô hình trộn giấy tờ của hai thủ tục.
#
# ⚠️ ĐÃ THỬ HỎI LLM — BỎ, VÌ ĐO ĐƯỢC LÀ VÔ DỤNG.
# Qwen2.5 1.5B trả `is_new_procedure=true` cho **9/9** câu thử, kể cả "lệ phí
# bao nhiêu tiền?" và "cảm ơn bạn" ⇒ 0% phân biệt, và nếu dùng thì mọi câu hỏi
# tiếp đều bị đá sang ô chat mới, LLM 2 không bao giờ chạy.
#
# Thay bằng luật dựa trên DỮ LIỆU, không cần mô hình: "câu hỏi này có khớp CHẮC
# CHẮN vào một thủ tục KHÁC trong kho không?". Đo trên bộ thử: hỏi tiếp 8/8
# đúng, thủ tục mới 4/4 đúng. Nhanh hơn, xác định được, và gỡ lỗi được.

# Từ đệm không mang nghĩa tra cứu — bỏ đi thì độ khớp mới phản ánh đúng ý hỏi.
_FILLER = set(
    "toi minh muon the con lam thi sao cach can co khong gi bao nhieu nay a xin"
    " cho hoi vay ban oi nhi la duoc va voi ve mat nua het hay tu o".split())

# Từ chỉ MỘT Ô TRONG BẢNG, không phải tên thủ tục. Câu hỏi chỉ gồm toàn những
# từ này (vd "lệ phí", "phí là bao nhiêu") luôn là hỏi tiếp về thủ tục đang xem
# — dù trong kho có thủ tục nào đó tình cờ mang chữ "lệ phí" trong tên.
_ATTRIBUTE_WORDS = set(
    "le phi mien chi tien gia giay to ho so thanh phan hinh thuc nop thoi gian lau"
    " dia diem diem noi dau mau don bieu mau tep file tai lieu truc tuyen online"
    " website link buoc quy trinh dieu kien ket qua co quan lien he han"
    " cam on chao tam biet ro them nhu nao mang theo chuan bi".split())


# Bản CÓ DẤU của `_FILLER`. So trên chữ bỏ dấu thì xoá nhầm chữ nghiệp vụ: "cần"
# = "căn" (căn cước), "thế" = "thẻ", "mất" = "mặt", "bạn" = "bản" — "làm lại
# căn cước bị mất" từng chỉ còn "lai cuoc bi" (chạy thử thật 24/09). Chữ có dấu
# so với danh sách này; chữ gõ KHÔNG dấu thì vẫn so `_FILLER` như cũ.
_FILLER_ACCENTED = set(
    "tôi mình muốn thế còn làm thì sao cách cần có không gì bao nhiêu này à ạ xin"
    " cho hỏi vậy bạn ơi nhỉ là được và với về mất nữa hết hay từ ở".split())


# Chữ đệm gõ không dấu trùng với chữ nghiệp vụ: cần/căn, thế/thẻ, mất/mặt, bạn/bản.
_AMBIGUOUS_BARE = {"can", "the", "mat", "ban"}
_bigram_cache: dict = {}


def _name_bigrams(conn: sqlite3.Connection) -> set[str]:
    """Mọi cặp hai âm tiết liền nhau (bỏ dấu) trong tên thủ tục đang hiệu lực."""
    stamp = tuple(conn.execute("SELECT COUNT(*), MAX(row_id) FROM procedures"
                               " WHERE status='active'").fetchone())
    if _bigram_cache.get("stamp") != stamp:
        grams = set()
        for (name,) in conn.execute("SELECT name FROM procedures WHERE status='active'"):
            toks = _fold(name).split()
            grams.update(f"{a} {b}" for a, b in zip(toks, toks[1:]))
        _bigram_cache.update(stamp=stamp, grams=grams)
    return _bigram_cache["grams"]


def _content_terms(text: str, conn: sqlite3.Connection | None = None) -> list[str]:
    import unicodedata

    from Database.pipeline.textutil import fold
    words = []
    for w in re.findall(r"\w+", unicodedata.normalize("NFC", (text or "").lower())):
        f = re.sub(r"[^0-9a-z]+", "", fold(w))
        if f:
            is_filler = (w in _FILLER_ACCENTED) if w != f else (f in _FILLER)
            words.append((f, is_filler, w == f))
    # Gõ KHÔNG dấu: "can" là "cần" hay "căn"? Giữ lại nếu nó ghép với chữ nghiệp vụ
    # liền kề thành một cặp CÓ trong tên thủ tục ("can cuoc", "the bao hiem").
    grams = _name_bigrams(conn) if conn is not None else set()
    out = []
    for i, (f, filler, bare) in enumerate(words):
        if filler and bare and grams and f in _AMBIGUOUS_BARE:
            pairs = []
            if i > 0 and not words[i - 1][1]:
                pairs.append(f"{words[i - 1][0]} {f}")
            if i + 1 < len(words) and not words[i + 1][1]:
                pairs.append(f"{f} {words[i + 1][0]}")
            filler = not any(p in grams for p in pairs)
        if not filler:
            out.append(f)
    return out


def is_other_procedure(conn: sqlite3.Connection, question: str,
                       current_proc_id: str) -> bool:
    """Câu hỏi này đã chuyển sang một thủ tục KHÁC chưa? Không dùng LLM."""
    terms = _content_terms(question, conn)
    if not terms:
        return False
    # Toàn từ chỉ ô trong bảng -> chắc chắn là hỏi tiếp, khỏi tra.
    if all(t in _ATTRIBUTE_WORDS for t in terms):
        return False

    hits = search(conn, " ".join(terms), 3)
    if not hits:
        return False
    top = hits[0]
    # Tên thủ tục khác được câu hỏi phủ đủ cũng tính: bộ gác chỉ GẮN cảnh báo,
    # không chặn, nên thừa một dòng rẻ hơn bỏ sót ("à còn làm lại căn cước bị
    # mất thì sao" từng không có cảnh báo, LLM 2 trả lời lan man theo bảng cũ).
    return bool((top["confident"] or _name_covered(top)) and top["proc_id"] != current_proc_id)


def count_active(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM procedures WHERE status = 'active'").fetchone()[0]


def is_expired(conn: sqlite3.Connection, proc_id: str) -> dict | None:
    """Thủ tục đã biến mất khỏi danh mục cổng? Trả về bản tombstone nếu có.

    Cổng KHÔNG công bố ngày hết hiệu lực, nên `expired_at` chỉ là ngày MÌNH
    phát hiện nó biến mất — tầng trên phải nói đúng như vậy với người dùng.
    """
    row = conn.execute(
        "SELECT proc_id, name, expired_at, expiry_note FROM procedures"
        " WHERE proc_id = ? AND status = 'expired' ORDER BY row_id DESC LIMIT 1",
        (proc_id,)).fetchone()
    return dict(row) if row else None

"""CỬA DUY NHẤT mà Hệ thống 2 (Backend) dùng để đọc CSDL thủ tục.

`search.py` đã lo phần khớp chữ (FTS5 ba tầng + `confident`). Tệp này lo phần
CÒN LẠI mà kiến trúc mới cần, và KHÔNG có ở tầng dưới:

    axes()            các trục MCQ có thật trong dữ liệu -> hỏi lại cho đúng
    derive_steps()    "checklist việc cần làm" (tick được) từ `Bước 1: … Bước 2: …`
    clean_fees()      gộp các dòng lệ phí rỗng/trùng của cổng
    build_record()    một bản ghi ĐÃ SẠCH, đủ để dựng bảng mà không cần SQL nữa

NGUYÊN TẮC: Backend KHÔNG viết câu SQL nào. Đổi schema thì chỉ sửa tệp này.

⚠️ GIỚI HẠN DỮ LIỆU THẬT (đo trên 1.407 thủ tục đang có — đừng hứa hơn thế):
  · `province` NULL ở 100% bản ghi ⇒ KHÔNG lọc được theo tỉnh. Trục địa phương
    dùng được duy nhất là `agency_levels` (Tỉnh / Xã-Phường / Bộ / Ngành dọc).
  · `receiving_address` rỗng ở 1.055/1.407 ⇒ ô "địa điểm nộp" thường trống.
  · 476/2.029 `procedure_steps` có `name`; phần còn lại là một khối văn bản
    ⇒ các bước phải TÁCH LÚC ĐỌC, không có sẵn thành dòng.
Mọi chỗ thiếu đều đi kèm cờ `status_*` để tầng trên nói thật, không đoán.
"""

from __future__ import annotations

import re
import sqlite3

from Database.pipeline import search as _search
from Database.pipeline.import_db import connect as _connect

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
    return sorted(hits, key=lambda h: (h["match_tier"], -h["term_overlap"], h["score"]))


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
        hits = sorted(hits, key=lambda h: (h["match_tier"], -h["term_overlap"],
                                           0 if h.get("domain") == domain else 1,
                                           h["score"]))
    return hits[:limit]


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

    # Mọi dòng đều 0 đồng và không ghi chú -> thủ tục MIỄN PHÍ, nói rõ ra.
    if not out and record.get("fees"):
        out = [{"fee_type": "FEE", "amount_value": 0.0,
                "amount_text": "Không quy định mức phí (0 đồng)",
                "submission_method": ""}]
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


def axes_for_candidates(hits: list[dict], low_confidence: bool = False) -> list[dict]:
    """Trục "thủ tục nào" — chỉ khi còn nhiều ứng viên khác nhau.

    `low_confidence=True` khi KHÔNG ứng viên nào đạt `confident`. Lúc đó thêm
    lựa chọn "không có cái nào đúng" để người dùng thoát ra nhánh xin lỗi.

    VÌ SAO PHẢI CÓ LỐI THOÁT ĐÓ (đo thật, không đoán):
        "thẻ căn cước cho trẻ em"   -> tier 3, overlap 0.67   ← câu hỏi THẬT
        "đăng ký bay lên sao Hỏa"   -> tier 3, overlap 0.67   ← câu hỏi RÁC
    Hai câu giống hệt nhau về mọi chỉ số máy đo được. Không ngưỡng nào tách nổi
    chúng, nên đừng giả vờ tách được: cứ hiện thứ tìm được RỒI ĐỂ NGƯỜI DÙNG
    nói "không phải cái này". Thà tốn một cú bấm còn hơn trả nhầm thủ tục.
    """
    options, seen = [], set()
    for h in hits:
        if h["proc_id"] in seen:
            continue
        seen.add(h["proc_id"])
        # Có 9 tên trùng nhau trong kho -> kèm lĩnh vực cho phân biệt được.
        options.append({"value": h["proc_id"],
                        "label": h["name"],
                        "hint": h.get("domain") or ""})

    if len(options) < 2 and not low_confidence:
        return []
    if not options:
        return []

    options = options[:6]
    question = AXIS_QUESTION[AXIS_PROCEDURE]
    if low_confidence:
        question = ("Mình không chắc lắm — có phải bạn cần một trong những thủ tục này không?")
        options = options + [{"value": NONE_OF_THESE,
                              "label": "Không có thủ tục nào đúng ý tôi",
                              "hint": "Mình sẽ nói rõ vì sao chưa tìm được"}]

    return [{"axis": AXIS_PROCEDURE, "question": question,
             "memorable": False, "options": options}]


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

    levels = levels_for(record)
    if len(levels) > 1:
        axes.append({
            "axis": AXIS_LEVEL, "question": AXIS_QUESTION[AXIS_LEVEL],
            "memorable": True,
            "options": [{"value": lv, "label": lv, "hint": ""} for lv in levels[:6]]})

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
    "le phi chi tien gia giay to ho so thanh phan hinh thuc nop thoi gian lau"
    " dia diem diem noi dau mau don bieu mau tep file tai lieu truc tuyen online"
    " website link buoc quy trinh dieu kien ket qua co quan lien he han"
    " cam on chao tam biet ro them nhu nao".split())


def _content_terms(text: str) -> list[str]:
    from Database.pipeline.textutil import fold
    return [t for t in re.split(r"[^0-9a-z]+", fold(text or "")) if t and t not in _FILLER]


def is_other_procedure(conn: sqlite3.Connection, question: str,
                       current_proc_id: str) -> bool:
    """Câu hỏi này đã chuyển sang một thủ tục KHÁC chưa? Không dùng LLM."""
    terms = _content_terms(question)
    if not terms:
        return False
    # Toàn từ chỉ ô trong bảng -> chắc chắn là hỏi tiếp, khỏi tra.
    if all(t in _ATTRIBUTE_WORDS for t in terms):
        return False

    hits = search(conn, " ".join(terms), 3)
    if not hits:
        return False
    top = hits[0]
    return bool(top["confident"] and top["proc_id"] != current_proc_id)


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

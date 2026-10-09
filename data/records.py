"""Dựng bản ghi sạch + nhóm thủ tục (copy-rồi-sửa từ retrieval.py của V10.6).

Đã BỎ: toàn bộ trục MCQ (axes_*, AXIS_*), looks_like_procedure, is_other_procedure.
Giữ nguyên các bài học về dữ liệu cổng (giới hạn `status_*`, "không suy ra miễn phí",
`procedure_cases` lẫn tiêu đề mục...).

⚠️ GIỚI HẠN DỮ LIỆU THẬT (1.350 thủ tục cấp Xã/Phường):
  · `province` = tỉnh CÔNG BỐ bản đó (614 bản mã H…); NULL = bản của bộ/ngành (736).
  · `receiving_address` rỗng ở 842/1.350.
  · `procedure_steps`: phần lớn là một khối văn bản -> các bước phải TÁCH LÚC ĐỌC.
Mọi chỗ thiếu đều có cờ `status_*` để tầng trên nói thật, không đoán.
"""

from __future__ import annotations

import re
import sqlite3

from . import search as _search
from .textutil import fold

def _fold(text: str) -> str:
    return re.sub(r"[^0-9a-z]+", " ", fold(text or "")).strip()


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

_MIN_HEAD_WORDS = 3          # "Đăng ký" trơn không được làm thủ tục chính
# Tiền tố tỉnh của bản địa phương: "Quảng Ninh - …" hoặc "(Hà Nội) …".
#   "Thái Nguyên (cấp xã) - …" cũng có. Chỉ áp cho bản CÓ `province`.
_PREFIX_RE = re.compile(r"^(?:\([^)]{2,30}\)\s*|[^-–]{2,40}?\s[-–]\s)")
_TRAIL_RE = re.compile(r"\s*\((?:cap|thuoc tham quyen)[^)]*\)\s*$")

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
        label: {head: tên hiển thị}}. Chỉ gọi lúc build; runtime đọc bảng `families`."""
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

    return {"head_of": head_of, "members": members, "info": info, "label": label}


# Lĩnh vực mà cổng gắn cấp Xã/Phường nhưng hồ sơ do NGÀNH DỌC giải quyết, không
# phải UBND phường. Nhóm chốt: giữ lại, nhưng nói rõ ở mọi chỗ người dân nhìn thấy.
VERTICAL_DOMAINS = {"Thuế": "cơ quan Thuế", "Hải quan": "cơ quan Hải quan"}


def vertical_agency(domain: str) -> str:
    """"cơ quan Thuế" nếu thủ tục thuộc lĩnh vực ngành dọc, "" nếu không."""
    for part in (domain or "").split(";"):
        if part.strip() in VERTICAL_DOMAINS:
            return VERTICAL_DOMAINS[part.strip()]
    return ""




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


def build_record(conn: sqlite3.Connection, proc_id: str,
                 case_ordinal: int | None = None) -> dict | None:
    """Bản ghi ĐẦY ĐỦ + ĐÃ SẠCH cho một thủ tục. None nếu không có bản active.

    `case_ordinal` (tuỳ chọn) lọc theo nhánh "trường hợp": lọc thành phần hồ sơ đúng
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

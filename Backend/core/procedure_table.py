"""Bản ghi CSDL -> BẢNG hiển thị. KHÔNG có LLM trong tệp này.

Đây là chỗ Proposal gọi là "UI Formatting Engine (Zero LLM Hallucination Risk)":
mọi con số, mọi loại giấy tờ, mọi mức phí đi THẲNG từ cột CSDL ra giao diện.
Mô hình ngôn ngữ không được chạm vào — nó chỉ xuất hiện ở LLM 1 (hiểu câu hỏi)
và LLM 2 (trả lời hỏi thêm), cả hai đều nằm NGOÀI hàm này.

NÓI THẬT VỀ CHỖ THIẾU. Mỗi ô mang theo cờ `status` lấy từ cột `status_*` của
Phase 1:
    present           cổng có công bố    -> hiện dữ liệu
    absent_confirmed  cổng KHÔNG công bố -> hiện câu giải thích, KHÔNG để trống
    unknown           chưa cào được      -> nói rõ là chưa rõ
Ô trống không kèm lý do sẽ bị người dân hiểu là "thủ tục này miễn phí" hoặc
"không cần giấy tờ gì" — sai nguy hiểm hơn là thiếu.
"""

from __future__ import annotations

import re

from Database.pipeline import retrieval as R

# Câu giải thích khi cổng không công bố — theo TỪNG ô, vì lý do mỗi ô mỗi khác.
# Nhóm chốt (2026-09-24): mở đầu bằng "Chưa có thông tin" và KHÔNG suy ra điều
# ngược lại ("miễn phí", "không cần giấy tờ", "không có bản trực tuyến"). Cổng
# không ghi ≠ không có — mình chỉ biết là mình chưa biết.
ABSENT_TEXT = {
    "fees": "Chưa có thông tin về lệ phí: Cổng Dịch vụ công không công bố mức phí cho thủ tục này. "
            "Điều này KHÔNG có nghĩa là miễn phí — bạn hỏi cơ quan tiếp nhận trước khi đi nộp.",
    "files": "Chưa có thông tin về biểu mẫu: Cổng Dịch vụ công không đính kèm biểu mẫu nào cho thủ tục này.",
    "address": "Chưa có thông tin về địa điểm tiếp nhận: Cổng Dịch vụ công không công bố địa chỉ cụ thể. "
               "Thông thường bạn nộp tại bộ phận Một cửa của cơ quan có thẩm quyền nêu ở phần Cơ quan thực hiện.",
    "online": "Chưa có thông tin về nộp trực tuyến: Cổng Dịch vụ công chưa mở dịch vụ nộp online cho thủ tục này.",
    "processing_time": "Chưa có thông tin về thời gian giải quyết: Cổng Dịch vụ công không công bố.",
    "checklist": "Chưa có thông tin về thành phần hồ sơ: Cổng Dịch vụ công không liệt kê. "
                 "Điều này KHÔNG có nghĩa là không cần giấy tờ.",
    "legal": "Chưa có thông tin về căn cứ pháp lý: Cổng Dịch vụ công không nêu.",
    "description": "Chưa có thông tin về trình tự thực hiện: Cổng Dịch vụ công không có phần mô tả.",
}

# Cổng có dòng lệ phí nhưng mọi dòng đều 0 đồng và KHÔNG ghi chú gì.
FEES_UNCLEAR_TEXT = ("Chưa có thông tin về lệ phí: Cổng Dịch vụ công ghi 0 đồng nhưng không kèm "
                     "giải thích, nên mình KHÔNG chắc thủ tục này miễn phí — bạn hỏi cơ quan "
                     "tiếp nhận trước khi đi nộp.")

UNKNOWN_TEXT = "Chưa tra được thông tin này (dữ liệu cào về chưa đầy đủ)."


def _cell(value, status: str, key: str) -> dict:
    """Một ô của bảng: giá trị + trạng thái + lý do nếu trống."""
    has = bool(value)
    if has:
        return {"value": value, "status": "present", "note": ""}
    if status == "absent_confirmed":
        return {"value": None, "status": "absent", "note": ABSENT_TEXT.get(key, "")}
    return {"value": None, "status": "unknown", "note": UNKNOWN_TEXT}


# Phase 1 gộp thời gian từ hai nguồn (executionMethods + cases[]) nên hay ra
# chuỗi kiểu "1; 1 ngày làm việc" hoặc "7; 12 ngày làm việc": vế đầu bị rụng
# đơn vị. Mượn đơn vị của vế có đơn vị rồi khử trùng lặp.
_BARE_NUMBER = re.compile(r"^\d+([.,]\d+)?$")
_UNIT_AFTER_NUMBER = re.compile(r"^\d+([.,]\d+)?\s+(.+)$")


# Cổng ghi `processingTimeUnit: "OTHER"` cho 86 thủ tục -> chỉ có con số, không
# có đơn vị. Để trần "3" thì người đọc (và LLM 2) tự điền "3 ngày" — đó là bịa.
NO_UNIT_NOTE = "(Cổng Dịch vụ công không ghi đơn vị — không rõ là ngày hay giờ)"


def _clean_time(text: str) -> str:
    parts = [p.strip(" .") for p in (text or "").split(";") if p.strip(" .")]
    if not parts:
        return ""

    unit = ""
    for p in parts:
        m = _UNIT_AFTER_NUMBER.match(p)
        if m:
            unit = m.group(2).strip()
            break

    out: list[str] = []
    for p in parts:
        if _BARE_NUMBER.match(p) and unit:
            p = f"{p} {unit}"
        if p not in out:
            out.append(p)
    joined = " hoặc ".join(out)
    if not unit and all(_BARE_NUMBER.match(p) for p in out):
        joined = f"{joined} {NO_UNIT_NOTE}"
    return joined


def _fee_line(fee: dict) -> str:
    """Một dòng lệ phí đọc được bằng mắt."""
    text = (fee.get("amount_text") or "").strip()
    value = fee.get("amount_value")
    if value is not None and value > 0:
        amount = f"{value:,.0f}".replace(",", ".") + " đồng"
        line = f"{amount} — {text}" if text else amount
    elif text:
        line = text
    else:
        line = "0 đồng"
    method = (fee.get("submission_method") or "").strip()
    return f"{line} ({method})" if method else line


def _component_line(c: dict) -> dict:
    """Một dòng THÀNH PHẦN HỒ SƠ (giấy tờ phải nộp) — tick được."""
    bits = []
    if c.get("original_qty"):
        bits.append(f"{c['original_qty']} bản chính")
    if c.get("copy_qty"):
        bits.append(f"{c['copy_qty']} bản sao")
    return {
        "name": (c.get("name") or "").strip(),
        "quantity": " · ".join(bits),
        "required": bool(c.get("required")),
        "case_name": (c.get("case_name") or "").strip(),
        "has_form": bool(c.get("has_electronic_form")),
    }


def _scope(record: dict) -> dict:
    """Phạm vi áp dụng: ai công bố · cấp nào giải quyết · ngành dọc."""
    levels = record.get("levels", [])
    province = record.get("province") or ""
    vertical = R.vertical_agency(record.get("domain", ""))
    notes = []
    if province:
        notes.append(f"Bản này do {record.get('department_promulgate') or 'UBND ' + province} "
                     f"công bố — nơi nộp, lệ phí và giấy tờ có thể chỉ đúng tại {province}.")
    else:
        notes.append("Bản chung của bộ/ngành, áp dụng toàn quốc. Một số tỉnh/thành có thể "
                     "có hướng dẫn riêng về nơi nộp và lệ phí.")
    if vertical:
        # Nhóm chốt: GIỮ thủ tục Thuế/Hải quan nhưng nói rõ không nộp ở phường.
        agency = (record.get("executing_agency") or "").strip()
        notes.append(f"Cổng xếp thủ tục này ở cấp Xã/Phường, nhưng hồ sơ do {vertical} giải quyết"
                     + (f" ({agency[:160]})" if agency else "")
                     + " — KHÔNG nộp tại UBND phường/xã.")
    elif "Xã/Phường" in levels:
        notes.append("Thủ tục thuộc thẩm quyền UBND cấp Xã/Phường.")
    else:
        notes.append("Thủ tục này giải quyết ở cấp Tỉnh/Thành phố, không phải cấp Xã/Phường.")
    return {
        "province": province,
        "nationwide": not province,
        "published_by": record.get("department_promulgate") or "",
        "vertical": vertical,
        "agency_levels": levels,
        "subjects": record.get("subjects", []),
        "note": " ".join(notes),
    }


def build(record: dict, *, expired: dict | None = None,
          picked: dict | None = None, memory_used: list | None = None) -> dict:
    """Bản ghi đã sạch (`retrieval.build_record`) -> bảng cho giao diện."""
    picked = picked or {}

    fees = record.get("fees_clean", [])
    files = record.get("files_clean", [])
    steps = record.get("steps_clean", [])
    components = record.get("components", [])
    legal = record.get("legal_basis", [])

    methods = [m for m in (record.get("methods") or [])
               if (m.get("submission_method") or "").strip()]
    submission = sorted({(m.get("submission_method") or "").strip() for m in methods})

    table = {
        "proc_id": record.get("proc_id", ""),
        "name": record.get("name", ""),
        "domain": record.get("domain", ""),

        # ── Giải thích thủ tục ──────────────────────────────────────────
        "explanation": _cell((record.get("description") or "").strip(),
                             record.get("status_description", "unknown"), "description"),
        "requirements": (record.get("requirements") or "").strip(),
        "results": (record.get("results") or "").strip(),

        # ── Thành phần hồ sơ (GIẤY TỜ phải nộp) ─────────────────────────
        "components": _cell([_component_line(c) for c in components],
                            record.get("status_checklist", "unknown"), "checklist"),

        # ── Hình thức nộp ───────────────────────────────────────────────
        "submission_methods": submission,

        # ── Chi phí ─────────────────────────────────────────────────────
        "fees": (_cell([_fee_line(f) for f in fees],
                       record.get("status_fees", "unknown"), "fees")
                 if fees or not record.get("fees") else
                 {"value": None, "status": "absent", "note": FEES_UNCLEAR_TEXT}),

        # ── Thời gian giải quyết ────────────────────────────────────────
        "processing_time": _cell(_clean_time(record.get("processing_time_text") or ""),
                                 record.get("status_processing_time", "unknown"),
                                 "processing_time"),

        # ── Địa điểm tiếp nhận trực tiếp ────────────────────────────────
        "address": _cell((record.get("receiving_address") or "").strip(),
                         record.get("status_address", "unknown"), "address"),
        "executing_agency": (record.get("executing_agency") or "").strip(),
        "coordinating_agency": (record.get("coordinating_agency") or "").strip(),

        # ── Checklist NHỮNG VIỆC CẦN LÀM (ô tick được) ──────────────────
        "steps": steps,

        # ── Tài liệu liên quan (bấm để tải) ─────────────────────────────
        "files": _cell([{**f, "url": f"/api/procedures/{record['proc_id']}/files/{f['file_id']}"}
                        for f in files],
                       record.get("status_files", "unknown"), "files"),

        # ── Link tới web đăng ký online ─────────────────────────────────
        "online": _cell({"url": (record.get("online_url") or "").strip(),
                         "portal_url": (record.get("portal_url") or "").strip(),
                         "services": record.get("online_services", [])}
                        if record.get("has_online_submission") else None,
                        record.get("status_online", "unknown"), "online"),

        # ── Thông tin meta (luật từ ngày nào, ai ban hành) ──────────────
        "meta": {
            "decision_number": (record.get("decision_number") or "").strip(),
            "decision_date": (record.get("decision_date") or "").strip(),
            "issuing_agency": (record.get("issuing_agency") or "").strip(),
            "department": (record.get("department_promulgate") or "").strip(),
            "publication_date": (record.get("publication_date") or "").strip(),
            "source_updated_at": (record.get("source_updated_at") or "").strip(),
            "scraped_at": (record.get("scraped_at") or "").strip(),
            "portal_url": (record.get("portal_url") or "").strip(),
            "legal_basis": [{"code": l.get("doc_code", ""), "name": l.get("doc_name", ""),
                             "year": l.get("doc_year", "")} for l in legal],
            # Cổng KHÔNG công bố ngày hết hiệu lực. Nói thẳng, đừng để giao diện
            # tự bịa ra một ô "còn hiệu lực đến ngày…" không có thật.
            "expiry_known": False,
            "expiry_note": ("Cổng Dịch vụ công không công bố ngày hết hiệu lực của thủ tục. "
                            "Ngày quyết định ở trên là mốc mới nhất mình có."),
        },

        # ── Phạm vi áp dụng ─────────────────────────────────────────────
        # `province` = tỉnh CÔNG BỐ bản này (mã H…), NULL = bản của bộ/ngành.
        # Ghi đúng ai công bố, cấp nào giải quyết, và ngành dọc nếu có — đừng để
        # người dân tưởng đã lọc theo tỉnh/phường của họ.
        "scope": _scope(record),

        # ── Dấu vết MCQ: người dùng đã chọn gì, trí nhớ đã đỡ được gì ───
        "picked": picked,
        "memory_used": memory_used or [],
        "cases": record.get("cases", []),

        # ── Cảnh báo hết hạn (nếu có) ───────────────────────────────────
        "expired": bool(expired),
        "expired_at": (expired or {}).get("expired_at", ""),
    }
    return table


# ---------------------------------------------------------------------------
# Bảng -> VĂN BẢN, để nhét vào prompt của LLM 2.
# ---------------------------------------------------------------------------
def to_text(table: dict, max_items: int = 12, only: list[str] | None = None) -> str:
    """Rút gọn bảng thành văn bản cho LLM 2 đọc. Giữ nguyên con số, không diễn giải.

    `only` = chỉ đưa các mục này (khoá của `SECTION_CUES`); None = cả bảng.
    """
    L: list[str] = [f"TÊN THỦ TỤC: {table['name']}",
                    f"MÃ THỦ TỤC: {table['proc_id']}",
                    f"LĨNH VỰC: {table['domain']}"]

    def cell(label: str, key: str, fmt=None) -> None:
        c = table.get(key) or {}
        if c.get("status") == "present":
            v = c["value"]
            L.append(f"{label}: {fmt(v) if fmt else v}")
        else:
            L.append(f"{label}: CHƯA CÓ THÔNG TIN. {c.get('note', '')}")

    want = (lambda k: True) if not only else (lambda k: k in only)

    if want("explanation"):
        cell("GIẢI THÍCH THỦ TỤC", "explanation")
    if want("processing_time"):
        cell("THỜI GIAN GIẢI QUYẾT", "processing_time")
    if want("fees"):
        cell("CHI PHÍ", "fees", lambda v: "; ".join(v[:max_items]))
    if want("address"):
        cell("ĐỊA ĐIỂM TIẾP NHẬN TRỰC TIẾP", "address")

    if want("agency") and table.get("executing_agency"):
        L.append(f"CƠ QUAN THỰC HIỆN: {table['executing_agency']}")
    if want("methods") and table.get("submission_methods"):
        L.append(f"HÌNH THỨC NỘP: {', '.join(table['submission_methods'])}")

    comp = table.get("components") or {}
    if want("components"):
        if comp.get("status") == "present":
            L.append("THÀNH PHẦN HỒ SƠ:")
            for c in comp["value"][:max_items]:
                qty = f" ({c['quantity']})" if c["quantity"] else ""
                L.append(f"  - {c['name']}{qty}")
        else:
            L.append(f"THÀNH PHẦN HỒ SƠ: CHƯA CÓ THÔNG TIN. {comp.get('note', '')}")

    if want("steps") and table.get("steps"):
        L.append("CÁC VIỆC CẦN LÀM:")
        for s in table["steps"][:max_items]:
            L.append(f"  - {(s['label'] + ': ') if s['label'] else ''}{s['detail'][:300]}")

    files = table.get("files") or {}
    if want("files"):
        if files.get("status") == "present":
            L.append("BIỂU MẪU ĐÍNH KÈM: " + ", ".join(f["name"] for f in files["value"][:max_items]))
        else:
            L.append(f"BIỂU MẪU ĐÍNH KÈM: CHƯA CÓ THÔNG TIN. {files.get('note', '')}")

    online = table.get("online") or {}
    if want("online"):
        if online.get("status") == "present" and online["value"].get("url"):
            L.append(f"NỘP TRỰC TUYẾN TẠI: {online['value']['url']}")
        else:
            L.append(f"NỘP TRỰC TUYẾN: CHƯA CÓ THÔNG TIN. {online.get('note', '')}")

    meta = table.get("meta", {})
    if want("meta"):
        L.append(f"CĂN CỨ: Quyết định {meta.get('decision_number', '')} "
                 f"ngày {meta.get('decision_date', '')} — {meta.get('issuing_agency', '')}")
        if meta.get("legal_basis"):
            L.append("VĂN BẢN PHÁP LÝ: " + "; ".join(
                f"{l['code']} {l['name']}"[:120] for l in meta["legal_basis"][:5]))
    if want("scope"):
        L.append(f"PHẠM VI: {table['scope']['note']}")
    if table.get("expired"):
        L.append("CẢNH BÁO: thủ tục này không còn trong danh mục cổng.")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Câu hỏi tiếp -> MỤC nào của bảng. Dùng cho hai việc:
#   1. câu hỏi chỉ về MỘT ô (lệ phí, thời gian…) -> CODE trích nguyên ô, không LLM
#   2. câu khác -> LLM 2 chỉ được đọc các mục liên quan, không phải cả bảng
# Mô hình 1.5B đọc cả bảng thì hay kể lan man và trộn mục nọ sang mục kia (đo
# được: "tóm tắt phần giải thích" -> kể cả giấy tờ, lệ phí, rồi bịa "sổ hộ khẩu,
# hoá đơn VAT"). Cụm từ khoá so trên chữ ĐÃ BỎ DẤU, có khoảng trắng hai đầu.
# ---------------------------------------------------------------------------
SECTION_CUES = {
    "fees": ("le phi", "chi phi", "phi ", "bao nhieu tien", "mat tien", "ton tien",
             "mien phi", "tien le phi", "gia bao nhieu", "tra tien", "dong tien"),
    "processing_time": ("thoi gian", "bao lau", "may ngay", "bao nhieu ngay", "mat bao lau",
                        "khi nao co", "bao gio co", "thoi han"),
    "components": ("giay to", "ho so", "thanh phan", "mang theo", "chuan bi", "can nop gi",
                   "nop nhung gi", "can nhung gi", "ban sao", "ban chinh"),
    "address": ("o dau", "dia diem", "dia chi", "noi nop", "nop tai", "cho nao"),
    "online": ("online", "truc tuyen", "qua mang", "link", "website", "trang web",
               "tren mang", "dich vu cong"),
    "methods": ("hinh thuc nop", "cach nop", "buu chinh", "buu dien", "nop truc tiep"),
    "files": ("bieu mau", "mau don", "to khai", "tai mau", "file", "tai ve"),
    "agency": ("co quan", "ai giai quyet", "ai cap", "ubnd", "uy ban"),
    "explanation": ("giai thich", "trinh tu", "quy trinh", "the nao", "lam sao", "cach lam",
                    "thu tuc nay la gi", "la gi"),
    "steps": ("cac buoc", "buoc nao", "viec can lam", "lam gi truoc", "checklist"),
    "meta": ("can cu", "luat nao", "nghi dinh", "thong tu", "van ban", "quyet dinh",
             "hieu luc", "het han"),
}
# Có những cụm này thì người dân cần DIỄN GIẢI, không phải trích ô -> để LLM 2.
_NEEDS_LLM = ("tom tat", "giai thich", "tai sao", "vi sao", "khac gi", "so sanh",
              "nghia la", "hieu the nao", "vi du")
# Câu hỏi CÓ ĐIỀU KIỆN về một ô ("nếu tôi thuộc hộ nghèo thì có phải nộp lệ phí
# không?"). Đo trên Qwen 1.5B: ô lệ phí ghi rõ "Miễn lệ phí cho … hộ nghèo" mà
# 6/6 lần mô hình vẫn trả "Chưa có thông tin" -> trích NGUYÊN VĂN ô đó và để
# người dân tự đối chiếu, chắc hơn để mô hình suy luận.
_CONDITIONAL = ("neu", "truong hop", "thi sao", "co phai", "con", "doi voi", "rieng")
# Mục trả được bằng CODE (trích nguyên ô). "explanation"/"steps"/"meta" là văn
# bản dài — người dân hỏi về chúng thường là muốn tóm tắt, để LLM 2 lo.
_QUOTABLE = ("fees", "processing_time", "components", "address", "online",
             "methods", "files", "agency")


def sections_for(question: str) -> list[str]:
    from Database.pipeline.textutil import fold
    q = f" {re.sub(r'[^0-9a-z]+', ' ', fold(question or ''))} "
    return [k for k, cues in SECTION_CUES.items()
            if any(f" {c.strip()} " in q for c in cues)]


# "Chắc không?" — người dân hỏi lại độ tin cậy, không hỏi một mục nào. Đưa
# cho LLM 2 thì mô hình 1.5B lẫn vai ("việc BẠN cung cấp thông tin là chính
# xác…") -> trả lời CỐ ĐỊNH, nói đúng nguồn gốc dữ liệu.
_CONFIRM = ("chac khong", "co chac", "chac chan khong", "that khong", "co that",
            "dung khong", "chinh xac khong", "tin duoc khong", "chuan khong")


def confirm_answer(table: dict, question: str) -> str | None:
    from Database.pipeline.textutil import fold
    q = f" {re.sub(r'[^0-9a-z]+', ' ', fold(question or ''))} "
    if len(q.split()) > 8 or not any(f" {c} " in q for c in _CONFIRM):
        return None
    meta = table.get("meta", {})
    bits = []
    if meta.get("source_updated_at"):
        bits.append(f"cổng cập nhật ngày {meta['source_updated_at']}")
    if meta.get("scraped_at"):
        bits.append(f"mình lấy về ngày {meta['scraped_at'][:10]}")
    when = f" ({', '.join(bits)})" if bits else ""
    return ("Thông tin trong bảng được **trích nguyên văn từ Cổng Dịch vụ công quốc gia** "
            f"(dichvucong.gov.vn){when}, mình không tự thêm gì. Riêng những ô ghi "
            "“Chưa có thông tin” là cổng không công bố.\n\n"
            "Nếu cần chắc chắn trước khi đi nộp, bạn đối chiếu bằng nút **🌐 Web search** "
            "hoặc gọi hỏi cơ quan tiếp nhận.")


# "còn người khuyết tật thì sao?" — X trong "còn X thì sao" có NẰM NGUYÊN VĂN
# trong bảng đang xem không? Có -> đang hỏi tiếp về thủ tục này (ô lệ phí ghi
# "Miễn lệ phí cho … người khuyết tật"), dù trong kho có thủ tục khác mang chữ
# "người khuyết tật" và bộ gác `newProcedure` sẽ tưởng là thủ tục mới.
# "còn làm hộ chiếu thì sao?" -> "lam ho chieu" không có trong bảng -> để bộ gác xét.
_FOLLOW_ON = re.compile(r"(?:^| )con (?:doi voi |voi |neu la |truong hop )?(.+?) thi "
                        r"(?:sao|the nao|nhu the nao|nhu nao)(?: |$)")


# Yêu cầu VIẾT LẠI câu trả lời trước, không phải câu hỏi mới. Bỏ dấu thì "ngắn
# hơn" = "ngan hon" khớp trọn "ngân … hơn" trong tên thủ tục thuế -> bộ gác
# `newProcedure` báo nhầm (bắt được ở bản chạy thật) -> nhận diện riêng.
_REWRITE = ("ngan hon", "ngan gon", "ngan lai", "tom tat lai", "rut gon", "chi tiet hon",
            "ky hon", "ro hon", "de hieu hon", "noi lai", "viet lai", "giai thich lai",
            "don gian hon", "dai hon", "cu the hon")


def is_rewrite(question: str) -> bool:
    from Database.pipeline.textutil import fold
    q = f" {re.sub(r'[^0-9a-z]+', ' ', fold(question or ''))} "
    return len(q.split()) <= 8 and any(f" {c} " in q for c in _REWRITE)


def refers_to_table(table: dict, question: str) -> bool:
    from Database.pipeline.textutil import fold
    q = re.sub(r"[^0-9a-z]+", " ", fold(question or "")).strip()
    m = _FOLLOW_ON.search(q)
    if not m or len(m.group(1)) < 3:
        return False
    hay = re.sub(r"[^0-9a-z]+", " ", fold(to_text(table, max_items=200)))
    return f" {m.group(1)} " in f" {hay} "


# Cụm (đã bỏ dấu) hỏi thứ KHÔNG BAO GIỜ có trong bảng của cổng.
_OUT_OF_TABLE = ("thu 7", "thu bay", "chu nhat", "cuoi tuan", "gio lam viec", "may gio",
                 "mo cua", "so dien thoai", "sdt", "hotline", "can bo", "nguoi phu trach")


def field_answer(table: dict, question: str, previous: str = "") -> str | None:
    """Câu hỏi chỉ về MỘT ô -> câu trả lời trích NGUYÊN VĂN ô đó. None nếu không phải.

    Không có LLM: đây là loại câu hỏi hay gặp nhất sau khi có bảng, và cũng là
    chỗ LLM 2 hay sai nhất (thêm "ngày" vào một con số không có đơn vị, nói
    "bảng không nêu" khi bảng có nêu).
    """
    from Database.pipeline.textutil import fold
    q = f" {re.sub(r'[^0-9a-z]+', ' ', fold(question or ''))} "
    # Lịch làm việc / liên hệ / cán bộ: bảng (cổng) KHÔNG có -> nói thẳng bằng
    # code. Không để LLM 2 đoán ("Thứ 7 phường không làm việc" — V10.2.1, 1.5B).
    if any(f" {c} " in q for c in _OUT_OF_TABLE):
        return ("Bảng thông tin của cổng **không có** lịch làm việc, số điện thoại hay tên "
                "cán bộ phụ trách. Bạn gọi hỏi trực tiếp cơ quan tiếp nhận (xem mục **Cơ quan "
                "thực hiện** trong bảng) hoặc dùng nút **🌐 Web search**.")
    secs = sections_for(question)
    # "còn người khuyết tật thì sao?" không nhắc mục nào -> mượn mục của câu trước.
    # CHỈ khi câu có dạng nối tiếp/điều kiện: mượn cho mọi câu ngắn thì "thứ 7
    # phường có làm việc không" bị trả ô THỜI GIAN của câu trước (chạy thử 24/09).
    if (not secs and previous and len(q.split()) <= 8
            and (_FOLLOW_ON.search(q.strip()) or any(f" {c} " in q for c in _CONDITIONAL))):
        secs = sections_for(previous)
    if len(secs) != 1 or secs[0] not in _QUOTABLE:
        return None
    if any(f" {c} " in q for c in _NEEDS_LLM) or len(q.split()) > 18:
        return None
    answer = _quote(table, secs[0])
    if any(f" {c} " in q for c in _CONDITIONAL):
        answer = ("Bảng ghi **nguyên văn** như sau — bạn đối chiếu với trường hợp của mình:\n\n"
                  + answer)
    return answer


def _quote(table: dict, key: str) -> str:
    name = table.get("name", "thủ tục này")

    def absent(cell: dict) -> str:
        return cell.get("note") or UNKNOWN_TEXT

    if key in ("fees", "processing_time", "address"):
        cell = table.get(key) or {}
        label = {"fees": "Lệ phí", "processing_time": "Thời gian giải quyết",
                 "address": "Địa điểm tiếp nhận trực tiếp"}[key]
        if cell.get("status") != "present":
            return absent(cell)
        v = cell["value"]
        if isinstance(v, list):
            body = "\n".join(f"- {x}" for x in v)
            return f"**{label}** của {name} theo Cổng Dịch vụ công:\n{body}"
        return f"**{label}** của {name} theo Cổng Dịch vụ công: {v}"

    if key == "components":
        cell = table.get("components") or {}
        if cell.get("status") != "present":
            return absent(cell)
        items = cell["value"]
        # Chat chỉ điểm qua; danh sách ĐẦY ĐỦ (tick được) đã nằm trong bảng.
        # Cổng tự đánh dấu "- ", "+ " ở đầu dòng -> bỏ để khỏi ra "- - …".
        shown = 8
        lines = []
        for c in items[:shown]:
            doc = re.sub(r"^[\s\-+*•]+", "", c["name"])
            doc = doc if len(doc) <= 180 else doc[:180].rsplit(" ", 1)[0] + "…"
            lines.append(f"- {doc}" + (f" ({c['quantity']})" if c.get("quantity") else ""))
        more = (f"\n… và {len(items) - shown} mục nữa — xem đủ ở phần **Thành phần hồ sơ** trong bảng."
                if len(items) > shown else "")
        return (f"**Thành phần hồ sơ** của {name} theo Cổng Dịch vụ công "
                f"({len(items)} mục, tick được trong bảng ở trên):\n" + "\n".join(lines) + more)

    if key == "online":
        cell = table.get("online") or {}
        if cell.get("status") == "present" and cell["value"].get("url"):
            return (f"Có — bạn nộp **trực tuyến** tại: {cell['value']['url']} "
                    "(nút “Mở trang nộp hồ sơ trực tuyến” trong bảng).")
        return absent(cell)

    if key == "methods":
        m = table.get("submission_methods") or []
        return (f"**Hình thức nộp** theo Cổng Dịch vụ công: {', '.join(m)}." if m
                else "Chưa có thông tin về hình thức nộp: Cổng Dịch vụ công không công bố.")

    if key == "files":
        cell = table.get("files") or {}
        if cell.get("status") != "present":
            return absent(cell)
        names = "\n".join(f"- {f['name']}" for f in cell["value"])
        return f"**Biểu mẫu** tải được (bấm trong phần Tài liệu liên quan của bảng):\n{names}"

    agency = table.get("executing_agency") or ""
    return (f"**Cơ quan thực hiện** theo Cổng Dịch vụ công: {agency}" if agency
            else "Chưa có thông tin về cơ quan thực hiện: Cổng Dịch vụ công không công bố.")


def summary_line(table: dict) -> str:
    """Một dòng mở đầu để lưu vào lịch sử chat — KHÔNG lặp lại cả bảng."""
    name = table["name"]
    bits = [f"**{name}**", f"(mã {table['proc_id']}, lĩnh vực {table['domain']})"]
    pt = table.get("processing_time") or {}
    if pt.get("status") == "present":
        bits.append(f"· thời gian giải quyết: {pt['value']}")
    return "Đây là thông tin thủ tục " + " ".join(bits) + "."


def axes_still_open(conn, record: dict, picked: dict) -> list[dict]:
    """Các trục MCQ CHƯA được chốt — tầng trên dùng để quyết định có hỏi nữa không."""
    return [a for a in R.axes_for_record(conn, record) if a["axis"] not in picked]

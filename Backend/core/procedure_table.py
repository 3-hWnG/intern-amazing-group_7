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
ABSENT_TEXT = {
    "fees": "Cổng Dịch vụ công không công bố mức phí cho thủ tục này. "
            "Bạn hỏi trực tiếp cơ quan tiếp nhận để biết chính xác.",
    "files": "Thủ tục này không có biểu mẫu đính kèm trên Cổng Dịch vụ công.",
    "address": "Cổng Dịch vụ công không công bố địa điểm tiếp nhận cụ thể. "
               "Thông thường bạn nộp tại bộ phận Một cửa của cơ quan có thẩm quyền nêu ở phần Cơ quan thực hiện.",
    "online": "Thủ tục này chưa có dịch vụ công trực tuyến — bạn nộp hồ sơ trực tiếp hoặc qua bưu chính.",
    "processing_time": "Cổng Dịch vụ công không công bố thời gian giải quyết cho thủ tục này.",
    "checklist": "Cổng Dịch vụ công không liệt kê thành phần hồ sơ cho thủ tục này.",
    "legal": "Cổng Dịch vụ công không nêu căn cứ pháp lý cho thủ tục này.",
    "description": "Cổng Dịch vụ công không có phần mô tả trình tự thực hiện.",
}

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


def _clean_time(text: str) -> str:
    parts = [p.strip(" .") for p in (text or "").split(";") if p.strip(" .")]
    if len(parts) < 2:
        return (text or "").strip()

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
    return " hoặc ".join(out)


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
        "fees": _cell([_fee_line(f) for f in fees],
                      record.get("status_fees", "unknown"), "fees"),

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
        # `province` NULL ở 100% bản ghi -> không có bản địa phương hoá nào.
        # Phải nói rõ là bản TOÀN QUỐC, đừng để người dân tưởng đã lọc theo tỉnh.
        "scope": {
            "province": record.get("province") or "",
            "nationwide": not record.get("province"),
            "agency_levels": record.get("levels", []),
            "subjects": record.get("subjects", []),
            "note": ("Đây là thủ tục cấp trung ương, áp dụng chung toàn quốc. "
                     "Một số tỉnh/thành có thể có hướng dẫn riêng về nơi nộp và lệ phí."),
        },

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
def to_text(table: dict, max_items: int = 12) -> str:
    """Rút gọn bảng thành văn bản cho LLM 2 đọc. Giữ nguyên con số, không diễn giải."""
    L: list[str] = [f"TÊN THỦ TỤC: {table['name']}",
                    f"MÃ THỦ TỤC: {table['proc_id']}",
                    f"LĨNH VỰC: {table['domain']}"]

    def cell(label: str, key: str, fmt=None) -> None:
        c = table.get(key) or {}
        if c.get("status") == "present":
            v = c["value"]
            L.append(f"{label}: {fmt(v) if fmt else v}")
        else:
            L.append(f"{label}: (không có dữ liệu) {c.get('note', '')}")

    cell("GIẢI THÍCH THỦ TỤC", "explanation")
    cell("THỜI GIAN GIẢI QUYẾT", "processing_time")
    cell("CHI PHÍ", "fees", lambda v: "; ".join(v[:max_items]))
    cell("ĐỊA ĐIỂM TIẾP NHẬN TRỰC TIẾP", "address")

    if table.get("executing_agency"):
        L.append(f"CƠ QUAN THỰC HIỆN: {table['executing_agency']}")
    if table.get("submission_methods"):
        L.append(f"HÌNH THỨC NỘP: {', '.join(table['submission_methods'])}")

    comp = table.get("components") or {}
    if comp.get("status") == "present":
        L.append("THÀNH PHẦN HỒ SƠ:")
        for c in comp["value"][:max_items]:
            qty = f" ({c['quantity']})" if c["quantity"] else ""
            L.append(f"  - {c['name']}{qty}")
    else:
        L.append(f"THÀNH PHẦN HỒ SƠ: (không có dữ liệu) {comp.get('note', '')}")

    if table.get("steps"):
        L.append("CÁC VIỆC CẦN LÀM:")
        for s in table["steps"][:max_items]:
            L.append(f"  - {(s['label'] + ': ') if s['label'] else ''}{s['detail'][:300]}")

    files = table.get("files") or {}
    if files.get("status") == "present":
        L.append("BIỂU MẪU ĐÍNH KÈM: " + ", ".join(f["name"] for f in files["value"][:max_items]))

    online = table.get("online") or {}
    if online.get("status") == "present" and online["value"].get("url"):
        L.append(f"NỘP TRỰC TUYẾN TẠI: {online['value']['url']}")
    else:
        L.append(f"NỘP TRỰC TUYẾN: không có. {online.get('note', '')}")

    meta = table.get("meta", {})
    L.append(f"CĂN CỨ: Quyết định {meta.get('decision_number', '')} "
             f"ngày {meta.get('decision_date', '')} — {meta.get('issuing_agency', '')}")
    if meta.get("legal_basis"):
        L.append("VĂN BẢN PHÁP LÝ: " + "; ".join(
            f"{l['code']} {l['name']}"[:120] for l in meta["legal_basis"][:5]))
    L.append(f"PHẠM VI: {table['scope']['note']}")
    if table.get("expired"):
        L.append("CẢNH BÁO: thủ tục này không còn trong danh mục cổng.")
    return "\n".join(L)


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

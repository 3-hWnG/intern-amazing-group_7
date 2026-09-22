"""BƯỚC ③ — biến JSON thô của cổng thành schema đích.

⚡ THUẦN HÀM · KHÔNG CHẠM MẠNG · KHÔNG CHẠM DB · KHÔNG GỌI LLM.
Chạy lại mất vài giây, nên đổi schema thoải mái mà không phải cào lại.

Luật bất di bất dịch:
  ⛔ KHÔNG hardcode theo tên thủ tục ("nếu là kết hôn thì phí là...").
  ⛔ KHÔNG tự chế phí / thời hạn. Nguồn ghi "Theo quy định" thì lưu y hệt.
  ⛔ KHÔNG regex mong manh — dữ liệu là JSON, đọc bằng key.

BA TRẠNG THÁI (xem PHASE1_PLAN.md §2): mỗi ô dữ liệu phải phân biệt được
    present          — có dữ liệu
    absent_confirmed — đã cào, nguồn KHÔNG công bố
    unknown          — chưa cào / cào lỗi
Gộp 2 cái cuối thành "không có" là đang khẳng định điều mình không biết.
Riêng PHÍ: absent_confirmed KHÔNG có nghĩa là miễn phí.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re

from Database.pipeline.paths import RAW_DIR, safe_name, stored_filename
from Database.pipeline.textutil import clean, fold

PRESENT = "present"
ABSENT = "absent_confirmed"
UNKNOWN = "unknown"

# Đơn vị thời gian cổng dùng trong processingTimeUnit / processingDay.type
_TIME_UNITS = {
    "DAY": "ngày", "WORKING_DAY": "ngày làm việc", "HOUR": "giờ",
    "MONTH": "tháng", "YEAR": "năm", "MINUTE": "phút", "OTHER": "",
}

_SUBMISSION = {
    "ONLINE": "Trực tuyến", "DIRECT": "Trực tiếp",
    "POSTAL": "Bưu chính", "OTHER": "Khác",
}

# Đường dẫn công khai trên Cổng DVCQG. Lấy từ bảng route của SPA (react-router):
#     "/dich-vu-cong-truc-tuyen/:code"
#     "/dich-vu-cong-truc-tuyen/:code/nop-ho-so"
# Tham số là MÃ TTHC (proc_id), không phải uuid. Đã kiểm chứng trả về HTTP 200.
_PORTAL = "https://dichvucong.gov.vn/dich-vu-cong-truc-tuyen/{code}"
_PORTAL_SUBMIT = _PORTAL + "/nop-ho-so"


def _epoch_ms_to_date(value) -> str:
    """1564592400000 → '2019-08-01'. Trả '' nếu không hợp lệ."""
    if not isinstance(value, (int, float)) or value <= 0:
        return ""
    try:
        return _dt.datetime.fromtimestamp(value / 1000, _dt.timezone.utc).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return ""


def _status(items) -> str:
    return PRESENT if items else ABSENT


def _num(value) -> float:
    """Ép về số. Nguồn trả processingTime lẫn lộn int / float / CHUỖI.

    Đo thật trên 221 thủ tục: 720 int, 100 str, 1 float. So sánh thẳng sẽ nổ
    TypeError, nên mọi chỗ đụng tới con số đều phải đi qua đây.
    """
    if isinstance(value, bool) or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------- các mảnh --
def _map_fees(raw: dict) -> list[dict]:
    """Phí. `value` có khi là SỐ, có khi None + nội dung nằm ở `description`.

    Nên bảng phải có CẢ HAI cột. Không được tự suy ra số từ chữ.
    """
    out = []
    for method in raw.get("executionMethods") or []:
        submission = method.get("submissionMethod") or ""
        for fee in method.get("fees") or []:
            out.append({
                "fee_type": clean(fee.get("type")),
                "amount_value": fee.get("value") if isinstance(fee.get("value"), (int, float)) else None,
                "amount_text": clean(fee.get("description")),
                "currency_id": clean(fee.get("currencyId")),
                "submission_method": _SUBMISSION.get(submission, submission),
            })
    for fee in raw.get("fees") or []:          # một số thủ tục để phí ở gốc
        out.append({
            "fee_type": clean(fee.get("type")),
            "amount_value": fee.get("value") if isinstance(fee.get("value"), (int, float)) else None,
            "amount_text": clean(fee.get("description")),
            "currency_id": clean(fee.get("currencyId")),
            "submission_method": "",
        })
    return out


def _map_checklist(raw: dict) -> list[dict]:
    """Hồ sơ cần nộp. Giữ cả tên 'trường hợp' để UI nhóm cho đúng."""
    out = []
    groups = [(i, clean(ec.get("name")), ec.get("profileComponents") or [])
              for i, ec in enumerate(raw.get("executionCases") or [])]
    if raw.get("profileComponents"):
        groups.append((-1, "", raw["profileComponents"]))

    for case_ordinal, case_name, components in groups:
        for pc in components:
            out.append({
                "case_ordinal": case_ordinal,
                "case_name": case_name,
                "name": clean(pc.get("name")),
                "code": clean(pc.get("code")),
                "required": bool(pc.get("required")),
                "original_qty": pc.get("originalQty") or 0,
                "copy_qty": pc.get("copyQty") or 0,
                "has_electronic_form": bool(pc.get("hasElectronicForm")),
                "is_processing_result": bool(pc.get("isProcessingResult")),
                "n_attachments": len(pc.get("attachments") or []),
            })
    return out


def _map_files(raw: dict, proc_id: str) -> list[dict]:
    """Tệp đính kèm. KHÔNG có URL công khai — chỉ có fileId để POST tải về."""
    out = []
    groups = [pc for ec in raw.get("executionCases") or []
              for pc in ec.get("profileComponents") or []]
    groups += raw.get("profileComponents") or []
    for pc in groups:
        for att in pc.get("attachments") or []:
            if not isinstance(att, dict) or not att.get("id"):
                continue
            file_name = clean(att.get("fileName"))
            # Tên trên đĩa do paths.stored_filename() quyết định — PHẢI gọi đúng
            # hàm mà fetch_details dùng, nếu không đường dẫn sẽ trỏ sai chỗ.
            stored = stored_filename(file_name or att["id"])
            rel = f"files/{safe_name(proc_id)}/{stored}" if stored else ""
            # Có metadata KHÔNG có nghĩa là tải được. Đo thật: 1 tệp cổng trả về
            # 0 byte. Nếu không đánh dấu, UI sẽ hiện nút tải rồi 404.
            # Đọc đĩa cục bộ, KHÔNG phải gọi mạng — bước ③ vẫn offline.
            available = bool(rel) and (RAW_DIR / rel).exists() and (RAW_DIR / rel).stat().st_size > 0
            out.append({
                "file_id": att["id"],
                "file_name": file_name,
                "bucket_name": clean(att.get("bucketName")),
                "remote_path": clean(att.get("filePath")),
                # đường dẫn tương đối tới tệp ETL đã tải về
                "local_path": rel,
                "file_available": int(available),
                "belongs_to": clean(pc.get("name"))[:200],
            })
    return out


def _map_steps(raw: dict) -> list[dict]:
    out = []
    for i, step in enumerate(raw.get("executionSteps") or []):
        out.append({"ordinal": i, "name": clean(step.get("name")),
                    "description": clean(step.get("description"))})
    return out


def _map_methods(raw: dict) -> list[dict]:
    """Cách nộp + thời hạn giải quyết."""
    out = []
    for m in raw.get("executionMethods") or []:
        qty = _num(m.get("processingTime"))
        unit = _TIME_UNITS.get(m.get("processingTimeUnit") or "", "")
        out.append({
            "submission_method": _SUBMISSION.get(m.get("submissionMethod") or "",
                                                 m.get("submissionMethod") or ""),
            "processing_time_qty": qty,
            "processing_time_unit": unit,
            "processing_time_text": _fmt_time(qty, unit),
            "description": clean(m.get("description")),
        })
    return out


def _fmt_time(qty: float, unit: str) -> str:
    """'15 ngày làm việc'. Bỏ .0 thừa. Rỗng nếu không có số."""
    if qty <= 0:
        return ""
    n = int(qty) if float(qty).is_integer() else qty
    return f"{n} {unit}".strip()


def _map_online_services(raw: dict) -> list[dict]:
    """cases[] của cổng — dịch vụ công trực tuyến, MỖI CÁI CÓ MÃ RIÊNG.

    Trước đây bị bỏ hoàn toàn; đây là nguồn thời hạn giải quyết thứ hai
    (75/221 thủ tục chỉ có thời hạn ở đây).
    """
    out = []
    for case in raw.get("cases") or []:
        day = case.get("processingDay") or {}
        qty = _num(day.get("qty"))
        out.append({
            "service_code": clean(case.get("code")),
            "service_name": clean(case.get("name")),
            "processing_qty": qty,
            "processing_unit": _TIME_UNITS.get(day.get("type") or "", ""),
            "processing_text": _fmt_time(qty, _TIME_UNITS.get(day.get("type") or "", "")),
        })
    return out


def _map_cases(raw: dict) -> list[dict]:
    """executionCases[] — TRỤC MCQ 'bạn thuộc trường hợp nào?'.

    Giữ nguyên câu đầy đủ theo yêu cầu của nhóm, không rút gọn.
    """
    return [{
        "ordinal": i,
        "case_name": clean(ec.get("name")),
        "n_components": len(ec.get("profileComponents") or []),
    } for i, ec in enumerate(raw.get("executionCases") or [])]


def _map_subjects(raw: dict) -> list[dict]:
    """subjectTypesDetails — TRỤC MCQ 'bạn là ai?'."""
    return [{"subject_name": clean(s.get("name")), "subject_code": clean(s.get("code"))}
            for s in raw.get("subjectTypesDetails") or [] if s.get("name")]


def _map_legal(raw: dict) -> list[dict]:
    out = []
    for x in raw.get("legalBasisesDetails") or []:
        code = clean(x.get("code"))
        m = re.search(r"/(\d{4})/", code) or re.search(r"(19|20)(\d{2})", code)
        out.append({"doc_code": code, "doc_name": clean(x.get("name")),
                    "doc_year": m.group(1) if m and len(m.group(1)) == 4 else ""})
    return out


def _map_meta(raw: dict) -> dict:
    prop = raw.get("procedureProposal") or {}
    issuing = (prop.get("issuingAgency") or {}).get("name")
    return {
        "decision_number": clean(prop.get("decisionNumber") or prop.get("proposalNumber")),
        "decision_date": _epoch_ms_to_date(prop.get("decisionDate")),
        "publication_date": _epoch_ms_to_date(prop.get("publicationDate")),
        "issuing_agency": clean(issuing),
        "source_updated_at": _epoch_ms_to_date(raw.get("updatedAt")),
        "source_created_at": _epoch_ms_to_date(raw.get("createdAt")),
    }


def _agency_levels(raw: dict) -> str:
    levels = [label for key, label in (
        ("isWard", "Xã/Phường"), ("isProvince", "Tỉnh"), ("isMinistry", "Bộ"),
        ("isOtherAgency", "Cơ quan khác"), ("isVertical", "Ngành dọc"),
    ) if raw.get(key)]
    return ", ".join(levels)


# ------------------------------------------------------------------- chính --
def normalize(raw: dict) -> dict:
    """JSON thô → một bản ghi đúng schema đích. Tất định: cùng input → cùng output."""
    proc_id = clean(raw.get("code")) or clean(raw.get("codeNotation")) or clean(raw.get("id"))
    name = clean(raw.get("name"))
    domains = [clean(c.get("name")) for c in raw.get("categoriesDetails") or [] if c.get("name")]

    steps = _map_steps(raw)
    fees = _map_fees(raw)
    checklist = _map_checklist(raw)
    files = _map_files(raw, proc_id)
    legal = _map_legal(raw)
    methods = _map_methods(raw)
    meta = _map_meta(raw)
    cases = _map_cases(raw)
    subjects = _map_subjects(raw)
    services = _map_online_services(raw)

    # Thời hạn giải quyết gộp từ HAI nguồn. executionMethods phủ 188/221,
    # cases[] phủ thêm 75 — gộp lại được 217/221 (98%).
    times = [m["processing_time_text"] for m in methods if m["processing_time_text"]]
    times += [s["processing_text"] for s in services if s["processing_text"]]
    seen_t, uniq_t = set(), []
    for t in times:
        if t not in seen_t:
            seen_t.add(t)
            uniq_t.append(t)
    processing_time_text = "; ".join(uniq_t)

    receiving = clean(raw.get("dossierReceivingAddresses"))

    description = "\n\n".join(s["description"] for s in steps if s["description"])
    executing = clean(raw.get("executingAgencies")) or ", ".join(
        clean(d.get("name")) for d in raw.get("departmentsExecuting") or [])

    # "Làm thủ tục này ở đâu trên mạng" — mục người dùng cần nhất sau checklist.
    # Cổng chỉ bật nút nộp hồ sơ khi `cases[]` có phần tử (đúng logic SPA đang dùng),
    # và phải có ít nhất một cách nộp trực tuyến.
    has_online = bool(raw.get("cases")) and any(
        m.get("submissionMethod") == "ONLINE" for m in raw.get("executionMethods") or [])
    portal_url = _PORTAL.format(code=proc_id) if proc_id else ""
    online_url = _PORTAL_SUBMIT.format(code=proc_id) if (proc_id and has_online) else ""

    record = {
        "proc_id": proc_id,
        "source_id": clean(raw.get("id")),
        "name": name,
        "domain": "; ".join(domains),
        "description": description,
        "requirements": clean(raw.get("requirementsAndConditions")),
        "results": "; ".join(clean(r.get("name")) for r in raw.get("resultsDetails") or []),
        "executing_agency": executing,
        "department_promulgate": clean(raw.get("departmentPromulgateName")),
        "department_code": clean(raw.get("departmentPromulgateCode")),
        "agency_levels": _agency_levels(raw),
        "subject_types": "; ".join(clean(s.get("name")) for s in raw.get("subjectTypesDetails") or []),
        "keywords": clean(raw.get("keywords")),
        "state": clean(raw.get("state")),

        "province": None,              # xem PHASE1_PLAN.md §13 — chưa chứng minh được
        "receiving_address": receiving,
        "coordinating_agency": clean(raw.get("coordinatingAgencies")),
        "processing_time_text": processing_time_text,

        "portal_url": portal_url,      # trang mô tả thủ tục trên Cổng DVCQG
        "online_url": online_url,      # trang NỘP HỒ SƠ trực tuyến ('' = không có)
        "has_online_submission": int(has_online),

        "fees": fees,
        "checklist": checklist,
        "files": files,
        "steps": steps,
        "methods": methods,
        "legal_basis": legal,
        "cases": cases,
        "subjects": subjects,
        "online_services": services,
        **meta,

        # BA TRẠNG THÁI — UI đọc mấy cờ này để không bao giờ khẳng định bừa.
        "status_fees": _status(fees),
        "status_files": _status([f for f in files if f["file_available"]]),
        "status_checklist": _status(checklist),
        "status_description": _status(description),
        "status_legal": _status(legal),
        "status_meta": PRESENT if meta["decision_date"] else ABSENT,
        "status_online": PRESENT if online_url else ABSENT,
        "status_address": _status(receiving),
        "status_processing_time": _status(processing_time_text),
    }

    # Chuỗi dùng để tra cứu: đã bỏ dấu + xử lý đ/Đ (xem textutil.py).
    record["search_text"] = fold(" ".join(filter(None, [
        name, record["domain"], record["keywords"], proc_id, record["executing_agency"],
        " ".join(s["subject_name"] for s in subjects),
    ])))
    record["content_hash"] = content_hash(record)
    return record


def content_hash(record: dict) -> str:
    """SHA-256 của bản ghi, BỎ QUA các trường hay đổi vặt.

    Nếu tính cả `search_text`/`content_hash` thì hash tự tham chiếu chính nó.
    """
    payload = {k: v for k, v in record.items()
               if k not in ("content_hash", "search_text", "scraped_at")}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------- CLI --
def main(argv: list[str] | None = None) -> int:
    import argparse
    import logging

    from Database.pipeline import paths

    ap = argparse.ArgumentParser(description="Bước ③: chuẩn hoá raw → staging")
    ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("pipeline.normalize")
    paths.ensure_dirs()

    src = sorted(paths.RAW_DETAILS_DIR.glob("*.json"))
    if not src:
        log.error("không có dữ liệu thô trong %s — chạy fetch_details trước",
                  paths.RAW_DETAILS_DIR)
        return 1

    records, bad = [], 0
    for path in src:
        try:
            records.append(normalize(json.loads(path.read_text(encoding="utf-8"))))
        except Exception as exc:
            bad += 1
            log.error("hỏng %s: %s", path.name, exc)

    with paths.STAGING_PATH.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    log.info("chuẩn hoá %d bản ghi (%d lỗi) → %s", len(records), bad, paths.STAGING_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

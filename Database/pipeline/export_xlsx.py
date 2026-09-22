"""Xuất DB ra XLSX nhiều sheet để người đọc bằng mắt.

Đây là bản ĐỂ ĐỌC, không phải định dạng trao đổi dữ liệu — nguồn thật vẫn là
staging/procedures.jsonl + procedures.db. Excel không chịu nổi ô 15.000 ký tự nên
mô tả dài bị cắt bớt (có đánh dấu "…"), cột `description_full_len` cho biết độ dài thật.

Chạy:  python -m Database.pipeline.export_xlsx
       python -m Database.pipeline.export_xlsx --limit 50 --out mau.xlsx
"""

from __future__ import annotations

import argparse
import logging

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from Database.pipeline import paths
from Database.pipeline.import_db import load_staging

log = logging.getLogger("pipeline.xlsx")

MAX_CELL = 2000          # Excel chịu 32.767 nhưng dài thế thì không ai đọc
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
HEAD_FONT = Font(color="FFFFFF", bold=True)
WARN_FILL = PatternFill("solid", fgColor="FFF2CC")


def _cut(value, limit: int = MAX_CELL):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return value
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _sheet(wb: Workbook, title: str, headers: list[str], rows: list[list],
           widths: list[int] | None = None, note: str = "") -> None:
    ws = wb.create_sheet(title[:31])
    start = 1
    if note:
        ws.cell(row=1, column=1, value=note).font = Font(italic=True, color="7F7F7F")
        start = 2

    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=start, column=c, value=h)
        cell.fill, cell.font = HEAD_FILL, HEAD_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)

    for r, row in enumerate(rows, start + 1):
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=_cut(v))
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    for i, w in enumerate(widths or [18] * len(headers), 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=start + 1, column=1)
    ws.auto_filter.ref = (f"A{start}:{get_column_letter(len(headers))}"
                          f"{start + len(rows)}")


def build(records: list[dict], out_path) -> None:
    wb = Workbook()
    wb.remove(wb.active)

    # ── README ────────────────────────────────────────────────────────────
    ws = wb.create_sheet("README")
    lines = [
        ("CSDL THỦ TỤC HÀNH CHÍNH — mẫu xuất từ Phase 1", True),
        ("", False),
        (f"Số thủ tục trong tệp này: {len(records)}", False),
        ("Nguồn: API JSON công khai của Cổng DVCQG (dichvucong.gov.vn/api/v1)", False),
        ("Sinh tự động bằng: python -m Database.pipeline.export_xlsx", False),
        ("", False),
        ("CÁCH ĐỌC — 3 TRẠNG THÁI của mỗi ô:", True),
        ("   present          = cổng CÓ công bố dữ liệu này", False),
        ("   absent_confirmed = đã cào, cổng KHÔNG công bố", False),
        ("   unknown          = chưa cào / cào lỗi", False),
        ("", False),
        ("⚠️ QUAN TRỌNG: status_fees = absent_confirmed KHÔNG có nghĩa là MIỄN PHÍ.", True),
        ("   Nó chỉ có nghĩa là cổng không công bố mức phí. Giao diện tuyệt đối", False),
        ("   không được tự suy ra 'Miễn phí' — người dân sẽ đi làm thủ tục mà không mang tiền.", False),
        ("", False),
        ("⚠️ decision_date KHÔNG phải ngày ban hành luật.", True),
        ("   Đó là ngày quyết định công bố thủ tục lên cổng (tất cả đều 2026).", False),
        ("   Muốn biết 'luật từ ngày nào' phải xem sheet 'Căn cứ pháp lý'.", False),
        ("", False),
        ("Các sheet:", True),
        ("⚠️ province = (toàn quốc) ở mọi dòng.", True),
        ("   Cổng KHÔNG có trường tỉnh/thành trong dữ liệu chi tiết. Để trống thay vì", False),
        ("   đoán bừa. Cột vẫn có sẵn để điền nếu sau này chứng minh được bản địa phương hoá.", False),
        ("", False),
        ("⚠️ Không có NGÀY HẾT HẠN trong nguồn.", True),
        ("   Đã dò toàn bộ payload: không có trường expiry/effective/valid nào.", False),
        ("   Thủ tục biến mất khỏi danh mục mới bị đánh status='expired', và ghi rõ", False),
        ("   đó là NGÀY PHÁT HIỆN, không phải ngày luật hết hiệu lực.", False),
        ("", False),
        ("   Thủ tục          — mỗi dòng một thủ tục (bảng chính)", False),
        ("   MCQ              — các lựa chọn hỏi làm rõ trước khi truy xuất", False),
        ("   Checklist        — hồ sơ cần nộp, mỗi dòng một loại giấy tờ", False),
        ("   Phí              — amount_value là SỐ, amount_text là CHỮ; có thể chỉ có một trong hai", False),
        ("   Tệp đính kèm     — biểu mẫu tải được; local_path là tệp đã tải về máy", False),
        ("   Căn cứ pháp lý   — luật/thông tư/nghị định làm căn cứ", False),
        ("   Cách nộp         — trực tuyến/trực tiếp + thời hạn giải quyết", False),
        ("   Độ phủ           — bao nhiêu % thủ tục có từng trường", False),
    ]
    for i, (text, bold) in enumerate(lines, 1):
        c = ws.cell(row=i, column=1, value=text)
        if bold:
            c.font = Font(bold=True)
    ws.column_dimensions["A"].width = 110

    # ── Thủ tục ───────────────────────────────────────────────────────────
    headers = ["proc_id", "province", "name", "domain", "department_promulgate",
               "agency_levels", "subject_types", "executing_agency",
               "receiving_address", "processing_time_text", "n_cases",
               "portal_url", "online_url",
               "has_online_submission", "n_checklist", "n_fees", "n_files", "n_legal",
               "status_fees", "status_files", "status_online", "status_meta",
               "decision_date", "decision_number", "issuing_agency",
               "source_updated_at", "requirements", "results", "description",
               "description_len", "content_hash"]
    rows = []
    for r in sorted(records, key=lambda x: x["proc_id"]):
        rows.append([
            r["proc_id"], r.get("province") or "(toàn quốc)", r["name"], r["domain"],
            r["department_promulgate"], r["agency_levels"], r["subject_types"],
            r["executing_agency"], r.get("receiving_address", ""),
            r.get("processing_time_text", ""), len(r.get("cases") or []),
            r.get("portal_url", ""), r.get("online_url", ""),
            "CÓ" if r.get("has_online_submission") else "KHÔNG",
            len(r["checklist"]), len(r["fees"]), len(r["files"]), len(r["legal_basis"]),
            r["status_fees"], r["status_files"], r.get("status_online", ""),
            r["status_meta"], r["decision_date"], r["decision_number"],
            r["issuing_agency"], r["source_updated_at"],
            r["requirements"], r["results"], r["description"],
            len(r["description"]), r["content_hash"][:16],
        ])
    _sheet(wb, "Thủ tục", headers, rows,
           widths=[13, 14, 46, 26, 22, 16, 22, 30, 40, 20, 8, 46, 46, 10, 11, 9, 9, 9,
                   17, 17, 17, 15, 13, 16, 20, 15, 40, 34, 70, 13, 18])

    # ── MCQ ──────────────────────────────────────────────────────────────
    rows = [[r["proc_id"], r["name"][:70], "Trường hợp", c["ordinal"] + 1,
             c["case_name"], c["n_components"]]
            for r in sorted(records, key=lambda x: x["proc_id"])
            for c in (r.get("cases") or []) if len(r.get("cases") or []) > 1]
    rows += [[r["proc_id"], r["name"][:70], "Đối tượng", i + 1,
              s2["subject_name"], ""]
             for r in sorted(records, key=lambda x: x["proc_id"])
             for i, s2 in enumerate(r.get("subjects") or [])
             if len(r.get("subjects") or []) > 1]
    _sheet(wb, "MCQ", ["proc_id", "tên thủ tục", "trục hỏi", "#", "lựa chọn",
                       "số giấy tờ"], rows, widths=[13, 40, 12, 5, 92, 10],
           note="Các lựa chọn để hỏi làm rõ TRƯỚC khi truy xuất thật. "
                "Giữ nguyên câu đầy đủ theo quyết định của nhóm.")

    # ── Checklist ─────────────────────────────────────────────────────────
    rows = [[r["proc_id"], r["name"][:70], i, it["case_name"], it["name"],
             len(it["name"]), "CÓ" if it["required"] else "—",
             it["original_qty"], it["copy_qty"],
             "CÓ" if it["has_electronic_form"] else "—", it["n_attachments"]]
            for r in sorted(records, key=lambda x: x["proc_id"])
            for i, it in enumerate(r["checklist"], 1)]
    _sheet(wb, "Checklist",
           ["proc_id", "tên thủ tục", "#", "trường hợp", "giấy tờ cần nộp",
            "độ dài", "bắt buộc", "bản chính", "bản sao", "có mẫu điện tử", "số tệp"],
           rows, widths=[13, 40, 5, 26, 85, 8, 9, 10, 9, 14, 8],
           note="⚠️ Cột 'bắt buộc' toàn '—': nguồn không ai điền cờ này, ĐỪNG hiển thị lên UI. "
                "Dòng nào 'độ dài' > 300 là gộp nhiều giấy tờ, cần tách khi render checkbox.")

    # ── Phí ───────────────────────────────────────────────────────────────
    rows = [[r["proc_id"], r["name"][:70], f["fee_type"], f["amount_value"],
             f["amount_text"], f["submission_method"]]
            for r in sorted(records, key=lambda x: x["proc_id"]) for f in r["fees"]]
    no_fee = [[r["proc_id"], r["name"][:70], "(cổng KHÔNG công bố phí)", None,
               "KHÔNG có nghĩa là miễn phí", ""]
              for r in sorted(records, key=lambda x: x["proc_id"]) if not r["fees"]]
    _sheet(wb, "Phí", ["proc_id", "tên thủ tục", "loại", "số tiền", "mô tả mức phí",
                       "áp dụng cho cách nộp"], rows + no_fee,
           widths=[13, 46, 12, 14, 70, 20],
           note="Số tiền trống + mô tả trống = cổng không công bố. TUYỆT ĐỐI không ghi 'Miễn phí'.")

    # ── Tệp đính kèm ──────────────────────────────────────────────────────
    rows = [[r["proc_id"], r["name"][:70], f["file_name"],
             "CÓ" if f.get("file_available") else "KHÔNG (cổng trả 0 byte)",
             f["local_path"], f["belongs_to"], f["file_id"]]
            for r in sorted(records, key=lambda x: x["proc_id"]) for f in r["files"]]
    _sheet(wb, "Tệp đính kèm",
           ["proc_id", "tên thủ tục", "tên tệp", "tải được?",
            "đường dẫn đã tải về", "thuộc mục hồ sơ", "file_id (để tải lại)"],
           rows, widths=[13, 36, 50, 22, 50, 36, 38],
           note="Tệp KHÔNG có URL công khai. Muốn tải phải POST "
                "/api/v1/submitting/preview-attachment với {fileId}. "
                "Đường dẫn là tương đối so với Database/raw/.")

    # ── Căn cứ pháp lý ────────────────────────────────────────────────────
    rows = [[r["proc_id"], r["name"][:70], lb["doc_code"], lb["doc_name"]]
            for r in sorted(records, key=lambda x: x["proc_id"]) for lb in r["legal_basis"]]
    _sheet(wb, "Căn cứ pháp lý", ["proc_id", "tên thủ tục", "số hiệu văn bản", "tên văn bản"],
           rows, widths=[13, 46, 22, 80],
           note="ĐÂY mới là 'luật từ ngày nào' cho ô Thông tin meta — không phải decision_date.")

    # ── Cách nộp ──────────────────────────────────────────────────────────
    rows = [[r["proc_id"], r["name"][:70], m["submission_method"],
             m["processing_time_text"], m["description"]]
            for r in sorted(records, key=lambda x: x["proc_id"]) for m in r["methods"]]
    _sheet(wb, "Cách nộp", ["proc_id", "tên thủ tục", "cách nộp", "thời hạn", "mô tả"],
           rows, widths=[13, 46, 14, 16, 90])

    # ── Độ phủ ────────────────────────────────────────────────────────────
    n = len(records)
    fields = [
        ("description (các bước)", lambda r: r["description"]),
        ("checklist (hồ sơ cần nộp)", lambda r: r["checklist"]),
        ("methods (cách nộp)", lambda r: r["methods"]),
        ("results (kết quả)", lambda r: r["results"]),
        ("domain (lĩnh vực)", lambda r: r["domain"]),
        ("decision_date", lambda r: r["decision_date"]),
        ("legal_basis (căn cứ pháp lý)", lambda r: r["legal_basis"]),
        ("requirements (yêu cầu/điều kiện)", lambda r: r["requirements"]),
        ("executing_agency", lambda r: r["executing_agency"]),
        ("files (biểu mẫu)", lambda r: r["files"]),
        ("online_url (nộp trực tuyến)", lambda r: r.get("online_url")),
        ("fees (phí)", lambda r: r["fees"]),
        ("receiving_address (địa điểm nộp)", lambda r: r.get("receiving_address")),
        ("processing_time_text (thời hạn)", lambda r: r.get("processing_time_text")),
        ("cases (trục MCQ trường hợp)", lambda r: r.get("cases")),
        ("subjects (trục MCQ đối tượng)", lambda r: r.get("subjects")),
        ("keywords", lambda r: r["keywords"]),
    ]
    rows = []
    for label, get in fields:
        have = sum(1 for r in records if get(r))
        rows.append([label, have, n - have, round(100 * have / n, 1) if n else 0])
    _sheet(wb, "Độ phủ", ["trường", "có dữ liệu", "trống", "% có"], rows,
           widths=[38, 13, 10, 10],
           note=f"Đo trên {n} thủ tục. Độ phủ phụ thuộc NẶNG vào bộ ngành "
                "(vd: files 8% ở Bộ Công an nhưng 64% ở mẫu trộn) — đừng suy rộng.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Xuất XLSX để đọc bằng mắt")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    records = load_staging()
    if not records:
        log.error("chưa có staging/procedures.jsonl")
        return 1
    if args.limit:
        records = records[:args.limit]

    out = paths.DATABASE_DIR / (args.out or "MAU_THU_TUC.xlsx")
    build(records, out)
    log.info("đã xuất %d thủ tục → %s (%.0f KB)",
             len(records), out, out.stat().st_size / 1024)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Xuất một DB thủ tục (kiểu System 3) ra một tệp Excel. Độc lập với server: chỉ cần sqlite3 + openpyxl, riêng đầu vào
.jsonl thì dựng DB tạm bằng chính system3.data.build.

Dùng trên web: Quản trị → Dữ liệu Strict → "Xuất Excel" (bản đang dùng) hoặc nút "Xuất Excel" ở từng phiên bản đã lưu.
Dùng độc lập (ở thư mục gốc repo):
    python run_server.py -m system3.system4.server.procs_xlsx data/runtime/system3.db
    python run_server.py -m system3.system4.server.procs_xlsx system4/runtime/procs/versions/2.jsonl -o v2.xlsx
    python run_server.py -m system3.system4.server.procs_xlsx system4/runtime/scrape/staging/procedures.jsonl
Đầu vào: .db / .sqlite (DB đã dựng) hoặc .jsonl (snapshot, phiên bản đã lưu, kết quả cào).

Mục đích: trích dẫn được dữ liệu và cách các bảng nối với nhau.
- Sheet "Procedures": mỗi thủ tục một dòng, row_id (khoá) + proc_id (mã thủ tục nhà nước) + portal_url (bấm để đối chiếu
  dichvucong.gov.vn), cột công thức đếm số dòng con ở từng sheet.
- 9 sheet con nối bằng row_id (giấy tờ, lệ phí, căn cứ pháp lý, …): giữ đúng row_id như trong DB, proc_id + tên thủ tục
  lấy bằng công thức INDEX/MATCH để thấy liên kết.
- 5 sheet System 3 tự dựng nối bằng proc_id (fees_clean, field_chunks, condition_index, families, team_fee_overlay).
- README: bảng liên kết, số dòng, số dòng không khớp thủ tục nào (phải là 0), kiểm nguồn; "Versions": phiên bản dữ liệu.
Không xuất: procedures.search_text (bản bỏ dấu để tìm), các bảng chỉ mục FTS5, import_log.
Công thức không có giá trị lưu sẵn: Excel tính khi mở (fullCalcOnLoad); tệp tải về mở ở Protected View thì bấm "Enable Editing".
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ARIAL = "Arial"
F_BODY = Font(name=ARIAL, size=10)
F_BOLD = Font(name=ARIAL, size=10, bold=True)
F_HEAD = Font(name=ARIAL, size=10, bold=True, color="FFFFFF")
F_LINK = Font(name=ARIAL, size=10, color="0563C1", underline="single")
F_FORM = Font(name=ARIAL, size=10, color="000000")
F_XSHEET = Font(name=ARIAL, size=10, color="008000")      # giá trị lấy từ sheet khác
F_H2 = Font(name=ARIAL, size=12, bold=True, color="1F3A68")
FILL_HEAD = PatternFill("solid", fgColor="1F3A68")
FILL_KEY = PatternFill("solid", fgColor="7A4E00")          # cột khoá / khoá ngoại
FILL_LOOK = PatternFill("solid", fgColor="2E7D52")         # tra qua khoá
FILL_CNT = PatternFill("solid", fgColor="5C54A8")          # đếm dòng con
THIN = Side(style="thin", color="C8CDD5")
MAXLEN = 32000                                             # Excel giới hạn 32.767 ký tự mỗi ô

# (tên sheet, bảng, cột xuất sau id + row_id, ý nghĩa)
CHILD = [
    ("Documents", "checklist_items", ["ordinal", "case_ordinal", "case_name", "name", "code", "required", "original_qty",
                                      "copy_qty", "has_electronic_form", "n_attachments"],
     "Required documents (thành phần hồ sơ), grouped by case"),
    ("Fees", "procedure_fees", ["fee_type", "amount_value", "amount_text", "currency_id", "submission_method"],
     "Fees exactly as published on the portal (lệ phí / phí)"),
    ("Legal basis", "legal_basis", ["doc_code", "doc_name", "doc_year"], "Legal documents the procedure is based on (căn cứ pháp lý)"),
    ("Steps", "procedure_steps", ["ordinal", "name", "description"], "Steps to carry out the procedure (trình tự thực hiện)"),
    ("Processing", "procedure_methods", ["submission_method", "processing_time_qty", "processing_time_unit",
                                         "processing_time_text", "description"],
     "Submission methods and processing time (cách thức, thời hạn)"),
    ("Cases", "procedure_cases", ["ordinal", "case_name", "n_components"], "Named cases / situations (trường hợp)"),
    ("Subjects", "procedure_subjects", ["subject_name", "subject_code"], "Who may carry out the procedure (đối tượng thực hiện)"),
    ("Online services", "online_services", ["service_code", "service_name", "processing_qty", "processing_unit"],
     "Online public-service entries (dịch vụ công trực tuyến)"),
    ("Attachments", "procedure_files", ["file_id", "file_name", "bucket_name", "remote_path", "file_available", "belongs_to"],
     "Form/attachment metadata on the portal (files not downloaded)"),
]
DERIVED = [
    ("Fees (clean)", "fees_clean", ["kind", "amount_value", "amount_text", "fee_type", "submission_method", "currency", "amount_vnd", "amount_ok"],
     "Fees normalised by data/build.py: kind = numeric / text_only / none; currency VND/USD/'' (unknown); amount_vnd = amount fixed against the text (\"20.000\" read as 20); amount_ok = 0 means only the portal text is shown"),
    ("Field chunks", "field_chunks", ["field", "case_ordinal", "text", "status"],
     "The 12 answer fields per procedure the bot quotes from, with present / absent_confirmed / unknown status"),
    ("Conditions", "condition_index", ["type", "text", "source"], "Who / situation / status / place conditions extracted for matching"),
    ("Families", "families", ["head", "label", "n_members", "default_variant"], "Groups of variant procedures and the default variant"),
    ("Team fee overlay", "team_fee_overlay", ["amount_text", "team_id"], "Fees filled from the team corpus ONLY when the portal has none"),
]
P_FIRST = ["row_id", "proc_id", "name", "portal_url"]
WIDE = {"name", "description", "amount_text", "case_name", "doc_name", "processing_time_text", "service_name", "file_name"}


REPO = Path(__file__).resolve().parents[2]   # thư mục gốc repo (có run_server.py)


def filename(version: int | None) -> str:
    return f"du_lieu_strict_v{version or 0}_{datetime.date.today().isoformat()}.xlsx"


def db_from_jsonl(src: Path, out: Path, timeout: int = 1800) -> int:
    """Dựng DB thủ tục từ một procedures.jsonl bằng chính system3.data.build (không sửa), ra tệp `out`; trả số thủ tục.
    Chạy tiến trình con qua run_server.register_package nên không phụ thuộc tên thư mục / PYTHONPATH."""
    out.unlink(missing_ok=True)
    code = ("import sys, pathlib; root = pathlib.Path(sys.argv[2]); sys.path.insert(0, str(root)); "
            "import run_server; run_server.register_package(root); "
            "import system3.data.load as L, system3.data.build as B; p = pathlib.Path(sys.argv[1]); "
            "B.load_snapshot = lambda path=None: L.load_snapshot(p); raise SystemExit(B.main())")
    env = dict(os.environ, S3_DATA_DB=str(out), PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", code, str(src), str(REPO)], env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0 or not out.is_file():
        raise RuntimeError("Dựng DB từ " + src.name + " thất bại: " + (r.stderr or r.stdout)[-800:])
    c = sqlite3.connect(str(out))
    try:
        return c.execute("SELECT COUNT(*) FROM procedures").fetchone()[0]
    finally:
        c.close()


def build(db_path: Path, out: Path, versions: list[dict] | None = None, version: int | None = None,
          active: int | None = None, source: str = "") -> dict:
    """Ghi tệp .xlsx từ DB thủ tục. versions/version/active: phiên bản (tuỳ chọn, cho sheet Versions); source: dòng
    "xuất từ đâu" ghi ở README. Trả {"procedures": n, "truncated": [...]}."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return _build(con, out, versions or [], version, active, source or str(db_path))
    finally:
        con.close()


def _build(con, out: Path, versions: list[dict], version: int | None, active: int | None, source: str) -> dict:
    truncated: list[str] = []

    def clean(v, where):
        if isinstance(v, str):
            v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", v)   # ký tự điều khiển làm hỏng tệp xlsx
            if len(v) > MAXLEN:
                truncated.append(where)
                v = v[:MAXLEN] + " …[cut: cell limit]"
        return v

    def header(ws, cols, fills, notes):
        for i, name in enumerate(cols, 1):
            c = ws.cell(row=1, column=i, value=name)
            c.font, c.fill = F_HEAD, fills.get(name, FILL_HEAD)
            c.alignment = Alignment(vertical="center", wrap_text=True)
            if name in notes:
                c.comment = Comment(notes[name], "export")
        ws.freeze_panes = "D2" if ws.title == "Procedures" else "A2"
        ws.row_dimensions[1].height = 30

    def widths(ws, spec):
        for i, w in enumerate(spec, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    def count(tbl):
        return con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]

    n_proc = count("procedures")
    p_last = n_proc + 1
    wb = Workbook()
    readme = wb.active
    readme.title = "README"

    # ---- Procedures
    p_rest = [r[1] for r in con.execute("PRAGMA table_info(procedures)") if r[1] not in P_FIRST + ["search_text"]]
    cnt_cols = [f"# {t}" for t, *_ in CHILD]
    p_cols = P_FIRST + cnt_cols + p_rest
    child_last = {t: count(tbl) + 1 for t, tbl, *_ in CHILD}
    ws = wb.create_sheet("Procedures")
    notes = {"row_id": "Technical primary key. Every child sheet stores this number in its row_id column.",
             "proc_id": "Official procedure code on dichvucong.gov.vn (mã thủ tục). Derived sheets link by this code.",
             "portal_url": "Official page of this procedure on the National Public Service Portal. Click to verify."}
    notes.update({f"# {t}": f"Formula: number of rows on sheet '{t}' whose row_id equals this procedure's row_id." for t, *_ in CHILD})
    header(ws, p_cols, {"row_id": FILL_KEY, "proc_id": FILL_KEY, **{c: FILL_CNT for c in cnt_cols}}, notes)
    for r_i, rec in enumerate(con.execute(f"SELECT {', '.join(P_FIRST + p_rest)} FROM procedures ORDER BY row_id"), 2):
        rec = dict(rec)
        for c_i, col in enumerate(p_cols, 1):
            cell = ws.cell(row=r_i, column=c_i)
            if col in cnt_cols:
                t = col[2:]
                cell.value, cell.font = f"=COUNTIF('{t}'!$B$2:$B${child_last[t]},$A{r_i})", F_FORM
                continue
            cell.value = clean(rec[col], f"Procedures!{col} row_id={rec['row_id']}")
            cell.font = F_BODY
            if col == "portal_url" and cell.value:
                cell.hyperlink, cell.font = cell.value, F_LINK
    widths(ws, [8, 10, 60, 48] + [11] * len(cnt_cols) + [16] * len(p_rest))
    ws.auto_filter.ref = f"A1:{get_column_letter(len(p_cols))}{p_last}"

    look_pid = "=INDEX(Procedures!$B$2:$B${last},MATCH($B{r},Procedures!$A$2:$A${last},0))"
    look_name_row = "=INDEX(Procedures!$C$2:$C${last},MATCH($B{r},Procedures!$A$2:$A${last},0))"
    look_name_pid = "=IFERROR(INDEX(Procedures!$C$2:$C${last},MATCH($A{r},Procedures!$B$2:$B${last},0)),\"(not in Procedures)\")"

    # ---- sheet con, nối bằng row_id
    for title, tbl, cols, _ in CHILD:
        ws = wb.create_sheet(title)
        all_cols = ["id", "row_id", "proc_id (via row_id)", "procedure name (via row_id)"] + cols
        header(ws, all_cols, {"row_id": FILL_KEY, "proc_id (via row_id)": FILL_LOOK, "procedure name (via row_id)": FILL_LOOK},
               {"row_id": "Foreign key → Procedures.row_id (stored in the database).",
                "proc_id (via row_id)": "Formula: looks up Procedures.proc_id using this row's row_id (not stored in this table).",
                "procedure name (via row_id)": "Formula: looks up Procedures.name using this row's row_id."})
        for r_i, rec in enumerate(con.execute(f"SELECT id, row_id, {', '.join(cols)} FROM {tbl} ORDER BY row_id, id"), 2):
            rec = dict(rec)
            ws.cell(row=r_i, column=1, value=rec["id"]).font = F_BODY
            ws.cell(row=r_i, column=2, value=rec["row_id"]).font = F_BODY
            ws.cell(row=r_i, column=3, value=look_pid.format(last=p_last, r=r_i)).font = F_XSHEET
            ws.cell(row=r_i, column=4, value=look_name_row.format(last=p_last, r=r_i)).font = F_XSHEET
            for c_i, col in enumerate(cols, 5):
                ws.cell(row=r_i, column=c_i, value=clean(rec[col], f"{title}!{col} id={rec['id']}")).font = F_BODY
        widths(ws, [8, 8, 11, 45] + [40 if c in WIDE else 14 for c in cols])
        ws.auto_filter.ref = f"A1:{get_column_letter(len(all_cols))}{max(ws.max_row, 2)}"

    # ---- sheet System 3 tự dựng, nối bằng proc_id
    for title, tbl, cols, _ in DERIVED:
        have = {r[1] for r in con.execute(f"PRAGMA table_info({tbl})")}
        cols = [c for c in cols if c in have]      # DB dựng trước G1.1 chưa có currency/amount_vnd/amount_ok
        ws = wb.create_sheet(title)
        all_cols = ["proc_id", "procedure name (via proc_id)"] + cols
        header(ws, all_cols, {"proc_id": FILL_KEY, "procedure name (via proc_id)": FILL_LOOK},
               {"proc_id": "Links to Procedures.proc_id (official code).",
                "procedure name (via proc_id)": "Formula: looks up Procedures.name using this row's proc_id."})
        for r_i, rec in enumerate(con.execute(f"SELECT proc_id, {', '.join(cols)} FROM {tbl} ORDER BY proc_id"), 2):
            rec = dict(rec)
            ws.cell(row=r_i, column=1, value=rec["proc_id"]).font = F_BODY
            ws.cell(row=r_i, column=2, value=look_name_pid.format(last=p_last, r=r_i)).font = F_XSHEET
            for c_i, col in enumerate(cols, 3):
                ws.cell(row=r_i, column=c_i, value=clean(rec[col], f"{title}!{col} proc_id={rec['proc_id']}")).font = F_BODY
        widths(ws, [11, 45] + [60 if c in ("text", "amount_text", "head", "label") else 14 for c in cols])
        ws.auto_filter.ref = f"A1:{get_column_letter(len(all_cols))}{max(ws.max_row, 2)}"

    # ---- Synonyms (không nối)
    ws = wb.create_sheet("Synonyms")
    header(ws, ["raw_term", "canonical_keyword"], {}, {})
    for r_i, rec in enumerate(con.execute("SELECT raw_term, canonical_keyword FROM synonyms ORDER BY raw_term"), 2):
        ws.cell(row=r_i, column=1, value=rec[0]).font = F_BODY
        ws.cell(row=r_i, column=2, value=rec[1]).font = F_BODY
    widths(ws, [16, 30])

    # ---- Versions (nguồn gốc, từ system4.db; xuất từ tệp ngoài web thì không có)
    if versions:
        ws = wb.create_sheet("Versions")
        vcols = ["id", "label", "source", "parent_id", "n_records", "note", "created_at"]
        header(ws, vcols + ["in this file", "used by Strict now"], {}, {})
        for r_i, v in enumerate(sorted(versions, key=lambda x: x["id"]), 2):
            for c_i, col in enumerate(vcols, 1):
                ws.cell(row=r_i, column=c_i, value=v.get(col)).font = F_BODY
            ws.cell(row=r_i, column=len(vcols) + 1, value="yes" if v["id"] == version else "").font = F_BOLD
            ws.cell(row=r_i, column=len(vcols) + 2, value="yes" if v["id"] == active else "").font = F_BOLD
        widths(ws, [6, 26, 12, 10, 12, 50, 22, 12, 16])

    # ---- README
    ws = readme
    row = 1

    def put(text, font=F_BODY):
        nonlocal row
        ws.cell(row=row, column=1, value=text).font = font
        row += 1

    built = con.execute("SELECT MAX(scraped_at) FROM procedures").fetchone()[0]
    upd = con.execute("SELECT MIN(source_updated_at), MAX(source_updated_at) FROM procedures").fetchone()
    ver = next((v for v in versions if v["id"] == version), None)
    put("Procedure database: full export", Font(name=ARIAL, size=16, bold=True, color="1F3A68"))
    put(f"Exported {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} from {source}.")
    if ver:
        put(f"Data version: {version} ({ver['label']}, {ver['n_records']} procedures) — "
            + ("the version Strict mode uses now." if version == active else f"NOT the version Strict mode uses now ({active}).")
            + " See sheet 'Versions'.")
    put(f"{n_proc} procedures. Records built {built}; portal last-updated dates {upd[0]} to {upd[1]}.")
    put("Source: National Public Service Portal API, https://dichvucong.gov.vn/api/v1 (scraper: system4/scraper/).")
    put("Numbers below are formulas: if they look empty, click 'Enable Editing' (Excel calculates them then).")
    row += 1
    put("How the tables link", F_H2)
    heads = ["Sheet", "Database table", "Link column", "Links to", "Rows", "Rows matched to a procedure", "Unmatched rows", "Contents"]
    hr = row
    for i, h in enumerate(heads, 1):
        c = ws.cell(row=row, column=i, value=h)
        c.font, c.fill = F_HEAD, FILL_HEAD
    row += 1
    first = row

    def link_row(sheet, tbl, link, to, rows_f, match_f, meaning):
        nonlocal row
        vals = [sheet, tbl, link, to, rows_f, match_f, f"=E{row}-F{row}" if match_f else None, meaning]
        for i, v in enumerate(vals, 1):
            ws.cell(row=row, column=i, value=v).font = F_BOLD if i == 1 else (F_FORM if isinstance(v, str) and v.startswith("=") else F_BODY)
        row += 1

    link_row("Procedures", "procedures", "row_id (key), proc_id (official code)", "—",
             "=COUNTA(Procedures!$A$2:$A$100000)", None,
             "One row per procedure: name, agency, legal decision, portal link, status flags")
    for title, tbl, _, meaning in CHILD:
        last = child_last[title]
        link_row(title, tbl, "row_id", "Procedures.row_id", f"=COUNTA('{title}'!$A$2:$A$100000)",
                 f"=SUMPRODUCT(--ISNUMBER(MATCH('{title}'!$B$2:$B${last},Procedures!$A$2:$A${p_last},0)))", meaning)
    for title, tbl, _, meaning in DERIVED:
        last = count(tbl) + 1
        link_row(title, tbl, "proc_id", "Procedures.proc_id", f"=COUNTA('{title}'!$A$2:$A$100000)",
                 f"=SUMPRODUCT(--ISNUMBER(MATCH('{title}'!$A$2:$A${last},Procedures!$B$2:$B${p_last},0)))", meaning)
    link_row("Synonyms", "synonyms", "—", "(none: abbreviation list)", "=COUNTA(Synonyms!$A$2:$A$1000)", None,
             "Abbreviations the search understands (dk → đăng ký, cccd → căn cước…)")
    for r in range(hr, row):
        for c in range(1, 9):
            ws.cell(row=r, column=c).border = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
    row += 1
    put("Provenance checks (formulas over the Procedures sheet)", F_H2)
    checks = [
        ("Procedures", "=COUNTA(Procedures!$A$2:$A$100000)"),
        ("…with a dichvucong.gov.vn portal link", f"=COUNTIF(Procedures!$D$2:$D${p_last},\"https://dichvucong.gov.vn/*\")"),
        ("…with a non-empty official code (proc_id)", f"=COUNTIF(Procedures!$B$2:$B${p_last},\"?*\")"),
        ("…with at least one required document", f"=COUNTIF(Procedures!$E$2:$E${p_last},\">0\")"),
        ("…with at least one legal-basis document", f"=COUNTIF(Procedures!$G$2:$G${p_last},\">0\")"),
        ("Total unmatched child rows (should be 0)", f"=SUM(G{first + 1}:G{first + len(CHILD) + len(DERIVED)})"),
    ]
    for label, f in checks:
        ws.cell(row=row, column=1, value=label).font = F_BODY
        ws.cell(row=row, column=5, value=f).font = F_FORM
        row += 1
    row += 1
    put("How to read / cite", F_H2)
    for t in ["Brown header = key column stored in the database (row_id / proc_id).",
              "Green header + green text = looked up by formula through the key (shows the link live; not stored in that table).",
              "Purple header on 'Procedures' = formula counting the linked rows on each child sheet.",
              "Example: find a proc_id on 'Procedures' (its portal_url opens the official page); its rows on 'Documents', 'Fees', "
              "'Legal basis'… carry the same row_id.",
              "Not exported: procedures.search_text (accent-folded search copy of the text), the FTS5 search-index tables, "
              "and import_log."]:
        put("• " + t)
    if truncated:
        put(f"• {len(truncated)} cell(s) longer than Excel's 32,767-character limit were cut and end with "
            f"'…[cut: cell limit]': " + "; ".join(truncated[:10]))
    widths(ws, [30, 20, 30, 20, 10, 16, 12, 70])

    wb.calculation.fullCalcOnLoad = True
    wb.save(out)
    return {"procedures": n_proc, "truncated": truncated}


def export_file(src: Path, out: Path, versions: list[dict] | None = None, version: int | None = None,
                active: int | None = None, source: str = "") -> dict:
    """Xuất từ một tệp bất kỳ: .db/.sqlite đọc thẳng (qua bản chụp, không giữ DB đang dùng), .jsonl dựng DB tạm trước."""
    tmp = Path(tempfile.mkdtemp(prefix="procs_xlsx_"))
    try:
        snap = tmp / "procs.db"
        if src.suffix.lower() == ".jsonl":
            db_from_jsonl(src, snap)
        else:
            a = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
            b = sqlite3.connect(snap)
            try:
                a.backup(b)
            finally:
                a.close()
                b.close()
        return build(snap, out, versions, version, active, source or str(src))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Xuất DB thủ tục (.db) hoặc procedures.jsonl (snapshot / phiên bản / cào) ra .xlsx")
    ap.add_argument("src", type=Path, help=".db / .sqlite hoặc .jsonl")
    ap.add_argument("-o", "--out", type=Path, help="tệp .xlsx ra (mặc định: cùng tên, cạnh tệp nguồn)")
    a = ap.parse_args(argv)
    if not a.src.is_file():
        ap.error(f"không thấy tệp {a.src}")
    out = a.out or a.src.with_suffix(".xlsx")
    res = export_file(a.src.resolve(), out)
    print(f"{res['procedures']} thủ tục -> {out}" + (f" ({len(res['truncated'])} ô bị cắt vì quá dài)" if res["truncated"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

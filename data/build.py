"""Dựng system3/data/runtime/system3.db từ snapshot.  Chạy: python -m system3.data.build"""
from __future__ import annotations

import re
import sys

from . import DB_PATH, records as R
from .load import connect_new, import_records, load_snapshot
from .textutil import fold
from . import team_overlay

EXTRA_SCHEMA = """
CREATE TABLE fees_clean (
    proc_id TEXT NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('numeric','text_only','none')),
    amount_value REAL, amount_text TEXT NOT NULL DEFAULT '',
    fee_type TEXT NOT NULL DEFAULT '', submission_method TEXT NOT NULL DEFAULT '');
CREATE INDEX idx_fc_proc ON fees_clean(proc_id);
CREATE TABLE field_chunks (
    proc_id TEXT NOT NULL, field TEXT NOT NULL, case_ordinal INTEGER NOT NULL DEFAULT -1,
    text TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('present','absent_confirmed','unknown')));
CREATE INDEX idx_chunk_proc ON field_chunks(proc_id, field);
CREATE TABLE condition_index (
    proc_id TEXT NOT NULL, type TEXT NOT NULL CHECK (type IN ('who','situation','status','place')),
    text TEXT NOT NULL, source TEXT NOT NULL CHECK (source IN ('case','subject','variant_name')));
CREATE INDEX idx_cond_proc ON condition_index(proc_id);
CREATE TABLE families (
    proc_id TEXT PRIMARY KEY, head TEXT NOT NULL, label TEXT NOT NULL,
    n_members INTEGER NOT NULL, default_variant INTEGER NOT NULL);
CREATE INDEX idx_fam_head ON families(head);
CREATE TABLE synonyms (raw_term TEXT PRIMARY KEY, canonical_keyword TEXT NOT NULL);
"""

# Chỉ những viết tắt KHÔNG mơ hồ (lấy từ _ABBREV của V10.6, đã dùng thật).
SEED_SYNONYMS = {
    "dk": "đăng ký", "dky": "đăng ký", "gks": "giấy khai sinh", "cccd": "căn cước",
    "cmnd": "chứng minh nhân dân", "gplx": "giấy phép lái xe",
    "gpxd": "giấy phép xây dựng", "gcn": "giấy chứng nhận",
    "qsdd": "quyền sử dụng đất", "hkd": "hộ kinh doanh",
    "bhxh": "bảo hiểm xã hội", "bhyt": "bảo hiểm y tế",
}

# field -> cột status_* tương ứng (agency không có cột riêng: dùng status_meta).
FIELD_STATUS = {
    "components": "status_checklist", "fees": "status_fees",
    "processing_time": "status_processing_time", "address": "status_address",
    "online": "status_online", "methods": "status_processing_time",
    "files": "status_files", "agency": "status_meta", "steps": "status_description",
    "explanation": "status_description", "meta": "status_meta", "legal_basis": "status_legal",
}

_STATUS_RE = re.compile(r"ho ngheo|can ngheo|khuyet tat|nguoi co cong|thuong binh|liet si|"
                        r"bao tro|doi tuong chinh sach|mo coi|cao tuoi|nguoi gia")
_PLACE_RE = re.compile(r"nuoc ngoai|bien gioi|hai dao|vung |khu vuc|noi cu tru|noi sinh")
_WHO_RE = re.compile(r"^\W*(?:cong dan|nguoi|cha|me|tre em|vo|chong|con|to chuc|doanh nghiep)\b")


def _ctype(text: str) -> str:
    f = fold(text)
    if _STATUS_RE.search(f):
        return "status"
    if _PLACE_RE.search(f):
        return "place"
    if _WHO_RE.search(f):
        return "who"
    return "situation"


def _fee_kind(f: dict) -> str:
    v = f.get("amount_value")
    if v is not None and v > 0:
        return "numeric"
    return "text_only" if (f.get("amount_text") or "").strip() else "none"


def _fee_line(f: dict) -> str:
    amt = f"{f['amount_value']:,.0f} đồng".replace(",", ".") if f["amount_value"] else ""
    return " - ".join(x for x in (f["fee_type"], amt, f["amount_text"],
                                  f["submission_method"]) if x)


def build_fees_and_chunks(conn):
    for (pid,) in conn.execute("SELECT proc_id FROM procedures").fetchall():
        rec = R.build_record(conn, pid)

        # ── fees_clean ──
        if not rec["fees_clean"]:
            # Có dòng rỗng/0 hoặc không có dòng: kind=none. KHÔNG suy ra miễn phí.
            conn.execute("INSERT INTO fees_clean (proc_id, kind) VALUES (?, 'none')", (pid,))
        for f in rec["fees_clean"]:
            conn.execute("INSERT INTO fees_clean VALUES (?,?,?,?,?,?)",
                         (pid, _fee_kind(f), f["amount_value"], f["amount_text"],
                          f["fee_type"], f["submission_method"]))

        # ── field_chunks ──
        st = {k: rec[v] or "unknown" for k, v in FIELD_STATUS.items()}
        chunks: dict[str, list[tuple[int, str]]] = {}

        by_case: dict[int, list[str]] = {}
        for c in rec["components"]:
            q = (f" (bản chính {c['original_qty']}, bản sao {c['copy_qty']})"
                 if c["original_qty"] or c["copy_qty"] else "")
            by_case.setdefault(c["case_ordinal"], []).append(f"- {c['name']}{q}")
        names = {c["ordinal"]: c["case_name"] for c in rec["cases"]}
        chunks["components"] = [
            (k, (names.get(k, "") + "\n" if names.get(k) else "") + "\n".join(lines))
            for k, lines in sorted(by_case.items())]

        j = "\n".join
        chunks["fees"] = [(-1, j(_fee_line(f) for f in rec["fees_clean"]))]
        chunks["processing_time"] = [(-1, rec["processing_time_text"])]
        chunks["address"] = [(-1, rec["receiving_address"])]
        chunks["online"] = [(-1, j(x for x in [rec["online_url"]] + [
            f"{s['service_code']} {s['service_name']}".strip()
            for s in rec["online_services"]] if x))]
        chunks["methods"] = [(-1, j(" - ".join(x for x in (
            m["submission_method"], m["processing_time_text"], m["description"]) if x)
            for m in rec["methods"]))]
        chunks["files"] = [(-1, j(f["name"] for f in rec["files_clean"]))]
        chunks["agency"] = [(-1, j(x for x in (
            rec["executing_agency"], rec["coordinating_agency"]) if x))]
        chunks["steps"] = [(-1, j(f"{s['label']} {s['detail']}".strip()
                                  for s in rec["steps_clean"]))]
        chunks["explanation"] = [(-1, j(x for x in (
            rec["description"], rec["requirements"], rec["results"]) if x))]
        chunks["meta"] = [(-1, j(x for x in (
            f"Quyết định: {rec['decision_number']}" if rec["decision_number"] else "",
            f"Ngày: {rec['decision_date']}" if rec["decision_date"] else "",
            f"Cơ quan ban hành: {rec['issuing_agency']}" if rec["issuing_agency"] else "",
            f"Cổng: {rec['portal_url']}" if rec["portal_url"] else "") if x))]
        chunks["legal_basis"] = [(-1, j(f"{l['doc_code']} {l['doc_name']}".strip()
                                        for l in rec["legal_basis"]))]

        for field in FIELD_STATUS:
            items = [(k, t.strip()) for k, t in chunks.get(field, []) if t and t.strip()]
            status = st[field]
            if not items:
                items = [(-1, "")]
                # Cổng khai báo "present" nhưng nội dung rỗng (vd phí rỗng/0) => unknown.
                if status == "present":
                    status = "unknown"
            for k, t in items:
                conn.execute("INSERT INTO field_chunks VALUES (?,?,?,?,?)",
                             (pid, field, k, t, status))


def build_conditions_families(conn):
    idx = R.family_index(conn)
    info, members = idx["info"], idx["members"]
    for head, pids in members.items():
        # Mặc định = bản tên ngắn nhất, ưu tiên bản không thuộc tỉnh.
        pids = sorted(pids, key=lambda p: (info[p]["province"] is not None,
                                           len(info[p]["name"])))
        for i, p in enumerate(pids):
            conn.execute("INSERT INTO families VALUES (?,?,?,?,?)",
                         (p, head, idx["label"][head], len(pids), int(i == 0)))

    seen = set()

    def add(pid, typ, text, src):
        text = " ".join(text.split()).strip(" :;.*-")
        if text and (pid, text, src) not in seen:
            seen.add((pid, text, src))
            conn.execute("INSERT INTO condition_index VALUES (?,?,?,?)", (pid, typ, text, src))

    for row in conn.execute("SELECT row_id, proc_id, name, province FROM procedures").fetchall():
        pid = row["proc_id"]
        for c in R.cases_for(conn, row["row_id"], real_only=True):
            t = R._MARKER.sub("", c["case_name"]).strip(" :") or c["case_name"]
            add(pid, _ctype(t), t, "case")
        for s in R.subjects_for(conn, row["row_id"]):
            add(pid, "who", s, "subject")
        head = idx["head_of"][pid]
        if len(members[head]) > 1 and R._base(row["name"], row["province"]) != head:
            # Phần khác biệt so với thủ tục chính: bỏ tiền tố tỉnh/"Thủ tục", cắt các từ của head.
            disp = R._display(row["name"], row["province"])
            toks = [t for t in disp.split() if re.search(r"\w", t)]
            diff = " ".join(toks[len(head.split()):])
            add(pid, _ctype(diff), diff, "variant_name")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    conn = connect_new()
    conn.executescript(EXTRA_SCHEMA)
    n = import_records(conn, load_snapshot())
    conn.executemany("INSERT INTO synonyms VALUES (?,?)", SEED_SYNONYMS.items())
    build_fees_and_chunks(conn)
    build_conditions_families(conn)
    print(f"team_fee_overlay {team_overlay.build(conn)}")
    conn.commit()
    for t in ("procedures", "fees_clean", "field_chunks", "condition_index", "families",
              "synonyms"):
        print(f"{t:16s}{conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
    conn.close()
    print(f"nạp {n} thủ tục -> {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

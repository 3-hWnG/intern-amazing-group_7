"""Xuất TỪ ĐIỂN KHOÁ cho LLM 1 (router) — `staging/vocabulary.json`.

VÌ SAO CẦN:
Kiến trúc mới cho LLM 1 tối đa 3 lần sinh lại keyword rồi mới xin lỗi. Với một
mô hình 1.5B, sinh tự do 3 lần = 3 cơ hội bịa ra thứ không có trong DB.
Ép nó CHỌN trong một danh sách có sẵn thì bài toán đổi từ "sinh" thành "phân
loại" — dễ hơn hẳn với mô hình nhỏ, và không bao giờ trỏ vào thứ DB không có.

Tệp gồm:
    domains[]    — TÊN THẬT lĩnh vực của cổng (không phải nhóm nội bộ của nhóm)
    procedures[] — mã + tên + dạng đã bỏ dấu, để khớp không dấu
    subjects[]   — đối tượng thực hiện (trục MCQ "bạn là ai")
    agency_levels[]
    confusables[] — các cặp tên gần giống nhau, để LLM/УI cảnh giác

Chạy:  python -m Database.pipeline.vocabulary
"""

from __future__ import annotations

import argparse
import collections
import difflib
import json
import logging

from Database.pipeline import paths
from Database.pipeline.import_db import connect
from Database.pipeline.textutil import fold

log = logging.getLogger("pipeline.vocab")

VOCAB_PATH = paths.STAGING_DIR / "vocabulary.json"


def build(conn) -> dict:
    rows = conn.execute(
        "SELECT proc_id, name, domain, agency_levels FROM procedures"
        " WHERE status='active' ORDER BY proc_id").fetchall()

    domains = collections.Counter(r["domain"] for r in rows if r["domain"])
    levels = collections.Counter(
        lv.strip() for r in rows for lv in (r["agency_levels"] or "").split(",")
        if lv.strip())
    subjects = collections.Counter(
        r["subject_name"] for r in conn.execute(
            "SELECT s.subject_name FROM procedure_subjects s"
            " JOIN procedures p ON p.row_id=s.row_id WHERE p.status='active'")
        if r["subject_name"])

    procedures = [{"proc_id": r["proc_id"], "name": r["name"],
                   "name_folded": fold(r["name"]), "domain": r["domain"]}
                  for r in rows]

    # Cặp tên dễ nhầm: gần giống nhau nhưng KHÁC mã. Đây chính là "bảng hỗ trợ
    # các từ dễ giống nhau" trong slide — sinh tự động thay vì gõ tay.
    confusables = []
    by_domain: dict[str, list[dict]] = collections.defaultdict(list)
    for p in procedures:
        by_domain[p["domain"]].append(p)
    for group in by_domain.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                ratio = difflib.SequenceMatcher(
                    None, a["name_folded"], b["name_folded"]).ratio()
                if ratio >= 0.86:
                    confusables.append({
                        "a": a["proc_id"], "b": b["proc_id"],
                        "a_name": a["name"], "b_name": b["name"],
                        "similarity": round(ratio, 3)})
    confusables.sort(key=lambda x: -x["similarity"])

    return {
        "generated_from": "Database/runtime/procedures.db (status='active')",
        "n_procedures": len(procedures),
        "usage": "LLM 1 chỉ được chọn keyword TRONG các danh sách dưới đây, "
                 "không được tự sinh chuỗi mới.",
        "domains": [{"name": k, "n": v} for k, v in domains.most_common()],
        "subjects": [{"name": k, "n": v} for k, v in subjects.most_common()],
        "agency_levels": [{"name": k, "n": v} for k, v in levels.most_common()],
        "procedures": procedures,
        "confusables": confusables[:500],
    }


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Xuất từ điển khoá cho LLM router").parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    conn = connect()
    try:
        vocab = build(conn)
    finally:
        conn.close()

    VOCAB_PATH.parent.mkdir(parents=True, exist_ok=True)
    VOCAB_PATH.write_text(json.dumps(vocab, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    log.info("từ điển: %d thủ tục · %d lĩnh vực · %d đối tượng · %d cặp dễ nhầm → %s",
             vocab["n_procedures"], len(vocab["domains"]), len(vocab["subjects"]),
             len(vocab["confusables"]), VOCAB_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Tra cứu thủ tục — đây là cửa mà System 2 (MCP) sẽ gọi ở Phase 2.

VÌ SAO KHÔNG DÙNG `MATCH 'can cuoc'` TRẦN:
FTS5 mặc định AND các từ qua MỌI cột đã đánh index, kể cả `description_folded`
(mô tả dài tới 12.000 ký tự). Kết quả: gõ "hồ chiếu" lại ra "Đăng ký xe" chỉ vì
trong mô tả có chữ "hồ sơ" và "đối chiếu". Đo thật: 4/4 truy vấn ra kết quả rác.

Cách chữa, ba tầng (nới lỏng dần, tầng trên luôn được xếp trước):
  Tầng 1 — AND, chỉ khớp trên `search_text` + `name_folded` (tên, lĩnh vực, mã,
           cơ quan). Chính xác cao. Khớp ở TÊN được cộng điểm gấp đôi vì trúng
           cả hai cột — nhờ vậy "căn cước" ra đúng thẻ căn cước, không ra thủ tục
           chỉ tình cờ cùng lĩnh vực.
  Tầng 2 — AND, mở rộng sang mô tả (bm25 hạ trọng số mô tả xuống còn 1/10).
  Tầng 3 — OR, cho câu hỏi dài kiểu "thẻ căn cước cho trẻ em": thiếu một từ vẫn
           phải ra kết quả, chứ không trả về rỗng.

⚠️ NGƯỠNG LIÊN QUAN (quan trọng với kiến trúc mới):
Tầng 3 là OR nên nó gần như LUÔN trả về thứ gì đó — hỏi "hộ chiếu phổ thông"
trong kho không có hộ chiếu thì nó vẫn moi ra "Tách thửa đất" chỉ vì trùng chữ
"thông"/"phổ". Kiến trúc mới có nhánh "không tìm thấy primary key → LLM sinh
lại → quá 3 lượt thì xin lỗi"; nhánh đó KHÔNG BAO GIỜ chạy nếu search luôn trả
về kết quả. Nên kết quả tầng 3 phải khớp ít nhất MỘT NỬA số từ mới được nhận,
và mỗi kết quả mang theo `match_tier`, `term_overlap`, `confident`.

Nói thẳng giới hạn: khớp theo CHỮ không thể biết "thuế thu nhập cá nhân" khác
"thuê nhà ở xã hội" về NGHĨA. Việc đó là của LLM 1 + `vocabulary.json`. Nhiệm vụ
của tầng DB chỉ là **báo đúng độ chắc chắn**, không giả vờ chắc khi không chắc.

Mọi truy vấn đều phải đi qua textutil.fold() — cùng hàm lúc nạp index (đ/Đ).
"""

from __future__ import annotations

import re
import sqlite3

from Database.pipeline.textutil import fold

# Giữ chữ/số/khoảng trắng. Bỏ hết ký tự đặc biệt của cú pháp FTS5 (", *, :, -, (...)
_SAFE = re.compile(r"[^0-9a-z\s]+")

# Trọng số bm25 theo THỨ TỰ CỘT của procedures_fts:
#   proc_id, row_id, search_text, name_folded, description_folded
# bm25 trả về điểm ÂM, càng âm càng khớp → ORDER BY tăng dần.
_WEIGHTS = "0.0, 0.0, 8.0, 10.0, 1.0"

# Tỉ lệ từ khoá tối thiểu phải nằm trong TÊN/LĨNH VỰC (áp cho tầng 2 và 3).
MIN_OVERLAP = 0.6


def _terms(query: str) -> list[str]:
    return [t for t in _SAFE.sub(" ", fold(query)).split() if t]


def _match_expr(terms: list[str], columns: str | None = None, op: str = "AND") -> str:
    """Ghép biểu thức FTS5. `columns` != None thì chỉ khớp trong các cột đó."""
    body = f" {op} ".join(f'"{t}"' for t in terms)
    return f"{{{columns}}} : ({body})" if columns else body


def _overlap(terms: list[str], row: sqlite3.Row) -> float:
    """Tỉ lệ từ khoá thật sự xuất hiện trong tên + lĩnh vực của thủ tục."""
    hay = fold(f"{row['name']} {row['domain']}")
    return sum(1 for t in terms if t in hay) / len(terms) if terms else 0.0


# Tiền tố chung của tên thủ tục, không mang nghĩa phân biệt.
_NAME_PREFIX = {"thu", "tuc"}
# Câu hỏi DÀI kiểu người thật ("à còn làm lại căn cước bị mất thì sao", "vợ em
# mới sinh bé hôm qua… làm giấy khai sinh…") có nhiều từ không nằm trong tên
# nào -> `_overlap` (chia cho số từ CÂU HỎI) luôn < 0.6 và cả tầng 3 bị loại
# (bắt được khi chạy thử thật 24/09). Đo thêm phía TÊN: tên được câu hỏi phủ
# ≥ NAME_COVER và khớp ≥ NAME_MIN_TERMS âm tiết trọn thì cũng nhận.
NAME_COVER = 0.5
NAME_MIN_TERMS = 2


def name_coverage(terms, name: str) -> tuple[int, float]:
    """(số âm tiết của TÊN khớp trọn với câu hỏi, tỉ lệ phủ tên) — bỏ "thủ tục"."""
    toks = {t for t in re.split(r"[^0-9a-z]+", fold(name or "")) if t}
    core = (toks - _NAME_PREFIX) or toks
    hit = len(core & set(terms))
    return hit, (hit / len(core) if core else 0.0)


def name_covered(terms, name: str) -> bool:
    hit, cov = name_coverage(terms, name)
    return hit >= NAME_MIN_TERMS and cov >= NAME_COVER


def _run(conn: sqlite3.Connection, expr: str, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        f"""SELECT p.proc_id, p.name, p.domain, p.department_promulgate,
                   p.status_fees, p.status_files, p.decision_date,
                   bm25(procedures_fts, {_WEIGHTS}) AS score
              FROM procedures_fts f
              JOIN procedures p ON p.row_id = f.row_id
             WHERE procedures_fts MATCH ? AND p.status = 'active'
          ORDER BY score
             LIMIT ?""", (expr, limit)).fetchall()


def search(conn: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]:
    """Tìm thủ tục theo câu chữ tự do, không cần gõ dấu.

    >>> search(conn, "dang ky cu tru")      # doctest: +SKIP
    """
    terms = _terms(query)
    if not terms:
        return []

    NAMEY = "search_text name_folded"
    tiers = [
        _match_expr(terms, NAMEY),                    # ① AND trên tên/lĩnh vực
        _match_expr(terms),                           # ② AND, có cả mô tả
    ]
    if len(terms) > 1:
        tiers.append(_match_expr(terms, NAMEY, "OR"))  # ③ OR, cứu câu hỏi dài

    rows: list[dict] = []
    seen: set[str] = set()
    for tier_no, expr in enumerate(tiers, 1):
        if len(rows) >= limit:
            break
        for r in _run(conn, expr, limit):
            if r["proc_id"] in seen:
                continue
            ov = _overlap(terms, r)
            # Tầng 2 khớp cả trong MÔ TẢ dài 15.000 ký tự, tầng 3 lại là OR —
            # cả hai đều dễ moi ra thứ chẳng liên quan. Bắt phải có đủ số từ
            # nằm trong TÊN/LĨNH VỰC mới được nhận.
            if tier_no >= 2 and ov < MIN_OVERLAP and not name_covered(terms, r["name"]):
                continue
            seen.add(r["proc_id"])
            hit = dict(r)
            hit["match_tier"] = tier_no
            hit["term_overlap"] = round(ov, 2)
            # `confident` = đủ chắc để trả thẳng bảng cho người dùng.
            # Không chắc → tầng trên NÊN hỏi MCQ hoặc đi nhánh "không tìm thấy".
            hit["confident"] = bool(tier_no == 1 and ov >= 0.75)
            rows.append(hit)
    return rows[:limit]


def find_by_primary_key(conn: sqlite3.Connection, proc_id: str) -> dict | None:
    """Lấy nguyên một thủ tục theo mã TTHC — đường đi CHÍNH của System 2.

    Trả về đủ cả bảng con để UI dựng thẳng, không cần LLM đụng vào.
    """
    proc = conn.execute(
        "SELECT * FROM procedures WHERE proc_id = ? AND status = 'active'",
        (proc_id,)).fetchone()
    if proc is None:
        return None

    out = dict(proc)
    row_id = proc["row_id"]
    for key, table, order in (
        ("fees", "procedure_fees", "id"),
        ("checklist", "checklist_items", "ordinal"),
        ("files", "procedure_files", "id"),
        ("steps", "procedure_steps", "ordinal"),
        ("methods", "procedure_methods", "id"),
        ("legal_basis", "legal_basis", "id"),
    ):
        out[key] = [dict(r) for r in conn.execute(
            f"SELECT * FROM {table} WHERE row_id = ? ORDER BY {order}", (row_id,))]
    return out


# --------------------------------------------------------------------- CLI --
def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    from Database.pipeline.import_db import connect

    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Thử tra cứu")
    ap.add_argument("query", nargs="+")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args(argv)

    conn = connect()
    try:
        for hit in search(conn, " ".join(args.query), args.limit):
            print(f"  {hit['score']:7.2f}  {hit['proc_id']:12s} {hit['name'][:70]}")
            print(f"           lĩnh vực: {hit['domain'][:60]}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

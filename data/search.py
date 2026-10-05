"""Tra cứu thủ tục (FTS5 ba tầng) — copy từ search.py của repo V10.6.

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
"thông"/"phổ". Nhánh "không tìm thấy primary key → LLM sinh
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

from .textutil import fold

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
            if tier_no >= 2 and ov < MIN_OVERLAP:
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


# ───────────────────────────── refine / parse_query (copy từ retrieval.py) ──

def _tokens(text: str) -> set[str]:
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


def search_ranked(conn: sqlite3.Connection, query: str, limit: int = 8) -> list[dict]:
    """Ứng viên kèm `confident` / `match_tier` / `term_overlap`, đã xếp lại."""
    return refine(search(conn, query, limit * 3), query)[:limit]



# ── Tra THẲNG bằng từ khoá (không LLM) — copy từ retrieval.py ──
# Viết tắt (dk, cccd, bhyt...) KHÔNG còn nằm cứng trong code: đọc từ bảng
# `synonyms(raw_term, canonical_keyword)` của chính DB system3.

# Lời đệm bỏ được khi tra từ khoá. CHỈ những âm tiết KHÔNG trùng chữ nghiệp vụ
# sau khi bỏ dấu — đừng gộp `_FILLER` vào đây: "hoi" vừa là "hỏi" vừa là "hồi"
# (thu hồi) và "hội"; "ban" là "bạn"/"bản sao"/"bán lẻ"; "tu" là "tư pháp".
# Bỏ nhầm những chữ đó là "thu hồi đất" thành "thu đất".
_QUERY_FILLER = set("toi minh muon t tao ko k hok dc duoc giup dum xin oi nhe nhi vay gi".split())
# Cụm bỏ nguyên cụm (bỏ từng âm tiết sẽ hại "thu hồi", "bảo hiểm", "thẻ"…).
_DROP_PHRASES = ("ho so thu tuc", "thu tuc", "cho minh hoi", "cho toi hoi", "cho hoi",
                 "vui long", "lam on", "bao nhieu", "nhu the nao", "the nao", "nhu nao",
                 "o dau", "bao lau", "can gi", "can nhung gi", "phai lam sao", "lam sao")

# Tỉnh/thành người dân hay nhắc (63 tên trước sáp nhập + tên gọi tắt). Nhắc tên
# tỉnh là NGỮ CẢNH để xếp bản của tỉnh đó lên trước, KHÔNG phải từ khoá tra —
# để nguyên trong câu thì tầng AND của FTS trượt hết bản toàn quốc.
_PROVINCE_NAMES = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bà Rịa Vũng Tàu", "Bạc Liêu", "Bắc Giang",
    "Bắc Kạn", "Bắc Ninh", "Bến Tre", "Bình Dương", "Bình Định", "Bình Phước",
    "Bình Thuận", "Cà Mau", "Cao Bằng", "Cần Thơ", "Đà Nẵng", "Đắk Lắk", "Đắk Nông",
    "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Giang", "Hà Nam", "Hà Nội",
    "Hà Tĩnh", "Hải Dương", "Hải Phòng", "Hậu Giang", "Hòa Bình", "Hưng Yên",
    "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", "Lâm Đồng", "Lạng Sơn",
    "Lào Cai", "Long An", "Nam Định", "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ",
    "Phú Yên", "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị",
    "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa",
    "Thừa Thiên Huế", "Huế", "Tiền Giang", "Hồ Chí Minh", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
]
# Cách gọi khác -> tên đúng như cột `province` trong CSDL.
_PROVINCE_ALIASES = {
    "tphcm": "Hồ Chí Minh", "hcm": "Hồ Chí Minh", "sai gon": "Hồ Chí Minh",
    "sg": "Hồ Chí Minh", "thanh pho ho chi minh": "Hồ Chí Minh",
    "thua thien hue": "Huế", "ba ria vung tau": "Bà Rịa - Vũng Tàu",
}


def _fold(text: str) -> str:
    return re.sub(r"[^0-9a-z]+", " ", fold(text or "")).strip()


def _province_patterns() -> list[tuple[str, str]]:
    pats = {_fold(p): p for p in _PROVINCE_NAMES}
    pats.update(_PROVINCE_ALIASES)
    # Dài trước: "thai binh" phải thắng "binh".
    return sorted(pats.items(), key=lambda kv: -len(kv[0]))


_PROVINCE_PATTERNS = _province_patterns()


def synonyms_map(conn: sqlite3.Connection) -> dict[str, str]:
    return {r[0]: r[1] for r in conn.execute(
        "SELECT raw_term, canonical_keyword FROM synonyms")}


def parse_query(conn: sqlite3.Connection, question: str) -> dict:
    """Câu hỏi -> {"keyword": chuỗi tra FTS, "provinces": [tỉnh được nhắc]}.

    Tất định, không LLM: bỏ tên tỉnh (giữ lại làm ngữ cảnh), bung từ đồng nghĩa/
    viết tắt từ bảng `synonyms`, bỏ lời đệm.
    "t người bình định muốn dk kết hôn"
        -> {"keyword": "nguoi dang ky ket hon", "provinces": ["Bình Định"]}
    """
    text = f" {_fold(question)} "
    provinces: list[str] = []
    for pat, name in _PROVINCE_PATTERNS:
        if f" {pat} " in text:
            text = text.replace(f" {pat} ", " ")
            if name not in provinces:
                provinces.append(name)
    for ph in _DROP_PHRASES:
        text = text.replace(f" {ph} ", " ")

    for raw_term, canonical in sorted(synonyms_map(conn).items(), key=lambda kv: -len(kv[0])):
        if f" {_fold(raw_term)} " in text:
            text = text.replace(f" {_fold(raw_term)} ", f" {_fold(canonical)} ")

    words = [w for w in text.split() if w not in _QUERY_FILLER]
    return {"keyword": " ".join(words), "provinces": provinces}

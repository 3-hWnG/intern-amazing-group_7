"""
service.py — System 2: query CSDL (FTS5 + bm25 + province fallback) và
đóng gói UI Table Card HTML. Theo đúng đặc tả mục 4-5, ARCHITECTURE_SYSTEM2.md.

Cách dùng nhanh (tự test bằng dữ liệu thật đã nạp):
    python service.py --demo "đăng ký kết hôn"
    python service.py --demo "cấp lại thẻ căn cước" --province "Hà Nội"

Dùng như thư viện:
    from service import resolve_query, render_card
    result = resolve_query(conn, primary_keyword, province, facet)
    html = render_card(result["primary"], facet=facet, suggestion=result["suggestion"])

LƯU Ý QUAN TRỌNG — bm25() của SQLite FTS5 trả về SỐ ÂM, CÀNG ÂM CÀNG KHỚP TỐT.
`ORDER BY bm25(...)` KHÔNG được thêm DESC — thêm DESC là đảo ngược kết quả,
không có lỗi runtime nào báo, chỉ âm thầm ra sai. Có test hồi quy cho đúng
lỗi này ở test_extractor.py (dùng DB thật) và calibrate.py (batch 56 câu) —
không có tự-test riêng trong chính file này.
"""

from __future__ import annotations

import argparse
import html as html_lib
import re
import sqlite3
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "db" / "procedures.db"

# Trọng số cột khi tính bm25 — ưu tiên khớp ở TÊN thủ tục hơn nhiều so với
# khớp tình cờ trong mô tả/cơ quan (tránh 1 từ lẻ trong description kéo nhầm
# thủ tục không liên quan lên đầu). Thứ tự trọng số PHẢI khớp thứ tự cột
# trong CREATE VIRTUAL TABLE procedures_fts (bỏ qua cột UNINDEXED):
#   name, normalized_name, description, authority
BM25_WEIGHTS = (10.0, 10.0, 1.0, 1.0)

# Ngưỡng khởi điểm để coi 2 THỦ TỤC KHÁC NHAU (khác proc_code) là "gần điểm,
# có thể nhầm" -> hiện thanh gợi ý. CHƯA hiệu chỉnh bằng dữ liệu thật — mỗi
# lần resolve_query() chạy đều in ra gap_ratio thật, thu thập vài chục case
# rồi tinh lại con số này (xem docstring _log_gap()).
AMBIGUOUS_GAP_RATIO = 0.20

# Ngưỡng tối thiểu tỷ lệ token câu hỏi phải xuất hiện trong TÊN thủ tục top-1
# để coi kết quả là "chắc chắn" (confident). KHÔNG có ngưỡng này thì hệ thống
# sẽ luôn trả về 1 thủ tục nào đó (nhờ AND->OR fallback) dù câu hỏi hoàn toàn
# không liên quan tới 70 thủ tục hiện có — ví dụ thật khi test: "xin visa du
# học nhật bản 2030" (không có trong DB) vẫn ra thẳng thẻ "Thủ tục xét, cấp
# học bổng chính sách" với vẻ chắc chắn như bình thường, KHÔNG có ambiguous
# gap báo hiệu gì (vì chỉ có 1 hướng khớp yếu, không phải 2 hướng gần điểm).
# Đây là rủi ro "0% ảo giác ở khâu hiển thị" nhưng hiển thị NHẦM thủ tục —
# khác nguồn gốc lỗi so với LLM bịa, nhưng hậu quả với người dùng thì giống
# nhau. Ngưỡng 0.5 là khởi điểm, cần hiệu chỉnh bằng test thật giống 2 ngưỡng
# trên (xem debug['name_coverage'] in ra mỗi lần chạy).
MIN_NAME_COVERAGE = 0.5

# ponytail: Ngưỡng F1 token 2 chiều để loại biến thể thừa chữ hoặc thủ tục ngoài phạm vi (như ly hôn)
MIN_F1_SCORE = 0.4

FACET_LABELS = {
    "tong_quan": "Tổng quan", "le_phi": "Lệ phí", "ho_so": "Hồ sơ",
    "thoi_gian": "Thời gian giải quyết", "noi_nop": "Nơi nộp",
}


# ---------------------------------------------------------------------------
# Kết nối DB
# ---------------------------------------------------------------------------

def connect(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Truy vấn FTS5 + bm25 + gom nhóm theo proc_code + province fallback
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[^\W\d_]+|\d+", re.UNICODE)


def _fts_tokens(text: str) -> list[str]:
    """BẮT BUỘC chuẩn hoá NFC trước khi tách token. Dữ liệu cũ (data cào từ
    Excel/Google Form) có một số ô lưu tiếng Việt ở dạng Unicode NFD (chữ cái
    gốc + dấu tổ hợp tách rời, vd 'Á' = 'A' + dấu sắc riêng), lúc đó regex
    token hoá SAI hoàn toàn — bắt được thật khi chạy calibrate.py trên bộ 56
    câu: "XÁC NHẬN VỊ TRÍ NHÀ - ĐẤT" (NFD) bị tách thành ['XA','C','NHÂ','N',
    'VI','TRI','NHA','ĐÂ','T'] thay vì 6 từ đúng, khiến name_coverage tính sai
    (báo 0.50 thay vì 1.0 thật). Không normalize thì lỗi này âm thầm ảnh
    hưởng CẢ truy vấn FTS5 (_fts_query) lẫn phép đo confident — nguy hiểm hơn
    một lỗi có traceback vì không crash, chỉ ra kết quả sai."""
    text = unicodedata.normalize("NFC", text or "")
    return _TOKEN_RE.findall(text)


def _fts_query(text: str, mode: str = "AND") -> str | None:
    """Bọc từng token trong dấu ngoặc kép -> tránh ký tự vận hành FTS5
    (":", "*", "-", "(", ")"...) trong câu hỏi người dùng làm vỡ cú pháp MATCH.
    mode='AND': mặc định FTS5 (cách nhau bởi khoảng trắng = AND).
    mode='OR': nối bằng OR — dùng khi AND ra 0 kết quả (câu hỏi có từ thừa)."""
    tokens = _fts_tokens(text)
    if not tokens:
        return None
    quoted = [f'"{t}"' for t in tokens]
    return (" OR " if mode == "OR" else " ").join(quoted)


def search_candidates(conn: sqlite3.Connection, keyword: str, limit: int = 20) -> list[sqlite3.Row]:
    """Trả về các dòng procedures đang active khớp `keyword`, xếp bm25 ASC
    (điểm càng âm/càng nhỏ càng khớp tốt — xem cảnh báo đầu file)."""
    w = BM25_WEIGHTS
    sql = f"""
        SELECT p.*, bm25(procedures_fts, {w[0]}, {w[1]}, {w[2]}, {w[3]}) AS score
        FROM procedures_fts
        JOIN procedures p ON p.id = procedures_fts.procedure_id
        WHERE procedures_fts MATCH ? AND p.status = 'active'
        ORDER BY score ASC
        LIMIT ?
    """
    for mode in ("AND", "OR"):
        q = _fts_query(keyword, mode)
        if not q:
            return []
        rows = conn.execute(sql, (q, limit)).fetchall()
        if rows:
            return rows
        # AND ra rỗng (câu hỏi có từ thừa/lệch) -> thử lại với OR trước khi bỏ cuộc
    return []


def _name_metrics(keyword: str, name: str) -> tuple[float, float, float]:
    """Trả về (cov_forward, cov_backward, f1).
    - cov_forward: tỷ lệ token keyword có trong name.
    - cov_backward: tỷ lệ token name có trong keyword (phạt biến thể dài thừa chữ).
    - f1: trung bình điều hòa, đo độ khớp sát 2 chiều."""
    from importer import fold
    q_tokens = {fold(t) for t in _fts_tokens(keyword)}
    q_tokens.discard("")
    if not q_tokens:
        return 0.0, 0.0, 0.0
    name_tokens = {fold(t) for t in _fts_tokens(name)}
    # ponytail: bỏ qua tiền tố hành chính phổ thông 'thu', 'tuc' để không phạt tên chuẩn
    name_core = {t for t in name_tokens if t not in ("thu", "tuc")} or name_tokens
    inter = q_tokens & name_core
    cov_fwd = len(inter) / len(q_tokens)
    cov_bwd = len(inter) / len(name_core)
    f1 = (2 * cov_fwd * cov_bwd) / (cov_fwd + cov_bwd) if (cov_fwd + cov_bwd) > 0 else 0.0
    return cov_fwd, cov_bwd, f1


def _group_by_proc_code(rows: list[sqlite3.Row], keyword: str | None = None) -> list[tuple[str, dict]]:
    """Gom các dòng cùng proc_code (khác nhau ở province) vào 1 nhóm — đây
    là các BIẾN THỂ của CÙNG 1 thủ tục, không phải 2 thủ tục khác nhau, nên
    không được đưa vào so sánh 'ambiguous suggestion' ở dưới."""
    groups: dict[str, dict] = {}
    for r in rows:
        pc = r["proc_code"]
        g = groups.setdefault(pc, {"best_score": r["score"], "rows": [], "name": r["name"]})
        g["rows"].append(r)
        g["best_score"] = min(g["best_score"], r["score"])

    # ponytail: rerank ưu tiên F1 token của tên (tránh biến thể lưu động/nước ngoài đè bản chuẩn), BM25 làm tie-breaker
    if keyword:
        return sorted(
            groups.items(),
            key=lambda kv: (round(_name_metrics(keyword, kv[1]["name"])[2], 3), -kv[1]["best_score"]),
            reverse=True,
        )
    return sorted(groups.items(), key=lambda kv: kv[1]["best_score"])


def _name_coverage(keyword: str, name: str) -> float:
    """Tỷ lệ token của `keyword` (bỏ dấu) xuất hiện trong `name` (bỏ dấu)."""
    return _name_metrics(keyword, name)[0]


def _pick_province_variant(rows: list[sqlite3.Row], province: str | None) -> sqlite3.Row:
    """Trong các biến thể cùng proc_code: ưu tiên đúng `province`, fallback
    bản toàn quốc (province IS NULL) — đúng luật mục 4.2.1 ARCHITECTURE_SYSTEM2."""
    if province:
        for r in rows:
            if r["province"] == province:
                return r
    for r in rows:
        if r["province"] is None:
            return r
    return rows[0]  # phòng hờ: không có bản toàn quốc lẫn không khớp province -> lấy tạm bản đầu


def _log_gap(keyword: str, top_code: str, top_score: float,
             second_code: str, second_score: float, gap_ratio: float) -> None:
    """In ra để thu thập số liệu thật, hiệu chỉnh AMBIGUOUS_GAP_RATIO sau này
    (giống cách nhóm đã hiệu chỉnh cỡ mẫu/ngưỡng cho search_baseline.py)."""
    print(f"[ambiguous-check] '{keyword}' -> #1 {top_code} ({top_score:.3f}) "
          f"vs #2 {second_code} ({second_score:.3f})  gap_ratio={gap_ratio:.1%}"
          f"{'  <- DƯỚI NGƯỠNG, sẽ gợi ý' if gap_ratio < AMBIGUOUS_GAP_RATIO else ''}")


def resolve_query(conn: sqlite3.Connection, keyword: str, province: str | None = None,
                   candidate_limit: int = 20) -> dict:
    """Trả về {"found", "confident", "primary": <dict thủ tục đầy đủ | None>,
    "suggestion": {"proc_code","name","id"} | None, "debug": {...}}.

    "found": FTS5 có khớp được dòng nào không (kể cả khớp yếu qua OR fallback).
    "confident": có nên TIN kết quả đó không (name_coverage >= MIN_NAME_COVERAGE và f1 >= MIN_F1_SCORE).
        found=True nhưng confident=False -> vẫn trả `primary` (để tuỳ tầng gọi
        quyết định hiển thị kèm cảnh báo, hay chuyển thẳng System 1) thay vì
        âm thầm hiện 1 thẻ chắc-như-đúng-rồi cho 1 thủ tục có thể sai hoàn toàn."""
    rows = search_candidates(conn, keyword, limit=candidate_limit)
    if not rows:
        return {"found": False, "confident": False, "primary": None, "suggestion": None,
                "debug": {"keyword": keyword, "candidates": 0}}

    groups = _group_by_proc_code(rows, keyword=keyword)
    top_code, top_group = groups[0]
    primary_row = _pick_province_variant(top_group["rows"], province)
    cov_fwd, cov_bwd, f1 = _name_metrics(keyword, primary_row["name"])
    coverage = cov_fwd
    # ponytail: kết hợp cả forward coverage và F1 2 chiều để chặn biến thể lệch và thủ tục ngoài phạm vi
    confident = (coverage >= MIN_NAME_COVERAGE) and (f1 >= MIN_F1_SCORE)

    suggestion = None
    debug = {"keyword": keyword, "candidates": len(rows), "distinct_procedures": len(groups),
              "top_code": top_code, "top_score": top_group["best_score"],
              "name_coverage": coverage, "f1_score": f1, "confident": confident}

    if len(groups) > 1:
        second_code, second_group = groups[1]
        s1, s2 = top_group["best_score"], second_group["best_score"]
        gap_ratio = abs(s2 - s1) / max(abs(s1), 1e-6)
        _log_gap(keyword, top_code, s1, second_code, s2, gap_ratio)
        debug.update(second_code=second_code, second_score=s2, gap_ratio=gap_ratio)
        if gap_ratio < AMBIGUOUS_GAP_RATIO:
            second_row = _pick_province_variant(second_group["rows"], province)
            # ponytail: chỉ gợi ý khi ứng viên thứ 2 có liên quan thực sự tới từ khóa
            if _name_coverage(keyword, second_row["name"]) >= MIN_NAME_COVERAGE:
                suggestion = {"proc_code": second_code, "name": second_row["name"], "id": second_row["id"]}

    if not confident:
        print(f"[low-confidence] '{keyword}' -> top-1 '{primary_row['name']}' "
              f"chỉ khớp coverage={coverage:.0%} (F1={f1:.2f}) — "
              f"khả năng cao SAI thủ tục, cân nhắc chuyển System 1 thay vì hiện thẻ.")

    return {"found": True, "confident": confident, "primary": load_full(conn, primary_row["id"]),
            "suggestion": suggestion, "debug": debug}


# ---------------------------------------------------------------------------
# Nạp đầy đủ 1 thủ tục (checklist + fees + files)
# ---------------------------------------------------------------------------

def load_full(conn: sqlite3.Connection, procedure_id: int) -> dict:
    p = conn.execute("SELECT * FROM procedures WHERE id = ?", (procedure_id,)).fetchone()
    if p is None:
        raise ValueError(f"procedure_id {procedure_id} không tồn tại")
    checklists = conn.execute(
        "SELECT * FROM procedure_checklists WHERE procedure_id = ? ORDER BY step_order, id",
        (procedure_id,)).fetchall()
    fees = conn.execute(
        "SELECT * FROM procedure_fees WHERE procedure_id = ? ORDER BY id", (procedure_id,)).fetchall()
    files = conn.execute(
        "SELECT * FROM procedure_files WHERE procedure_id = ? ORDER BY id", (procedure_id,)).fetchall()
    return {"procedure": dict(p), "checklists": [dict(c) for c in checklists],
            "fees": [dict(f) for f in fees], "files": [dict(f) for f in files]}


# ---------------------------------------------------------------------------
# Render UI Table Card (mục 6.3 ARCHITECTURE_SYSTEM2.md)
# ---------------------------------------------------------------------------

def _esc(text) -> str:
    return html_lib.escape(str(text)) if text is not None else ""


def _hl(facet: str | None, target: str) -> str:
    return " highlight-facet" if facet == target else ""


def render_card(full: dict, facet: str | None = None, suggestion: dict | None = None) -> str:
    """LƯU Ý (22/09/2026, yêu cầu Leader): KHÔNG tự động cảnh báo hết hiệu lực
    ở đây nữa — ETL (importer/crawler) chịu trách nhiệm cào thủ tục mới + xoá
    thủ tục hết hạn khỏi DB (không còn ở trạng thái 'active'), nên card đã
    render coi như luôn còn hiệu lực. `expiration_date` (nếu có) vẫn hiện ở
    footer metadata để tham khảo, không phải để tự bật banner."""
    p = full["procedure"]
    scope = f'Áp dụng: {"Toàn quốc" if not p.get("province") else p["province"]}'

    suggestion_html = ""
    if suggestion:
        suggestion_html = f"""
  <div class="proc-suggestion">
    💡 Có thể bạn quan tâm:
    <button class="btn-switch-proc" data-proc-id="{_esc(suggestion['id'])}"
            onclick="switchProcedure('{_esc(suggestion['id'])}')">{_esc(suggestion['name'])}</button>
  </div>"""

    fees_html = "".join(
        f'<div class="fee-item"><span class="fee-name">{_esc(f["fee_type"])}:</span> '
        f'<span class="fee-amount">{_esc(f["amount_text"])}</span>'
        + (f' <span class="fee-condition">({_esc(f["condition"])})</span>' if f.get("condition") else "")
        + "</div>"
        for f in full["fees"]
    ) or '<div class="fee-item fee-empty">Chưa có thông tin lệ phí.</div>'

    checklist_html = "".join(
        f'<label class="check-item"><input type="checkbox"> {_esc(c["content"])}'
        + (f' <span class="check-note">({_esc(c["note"])})</span>' if c.get("note") else "")
        + "</label>"
        for c in full["checklists"]
    ) or '<p class="checklist-empty">Chưa có checklist hồ sơ.</p>'

    files_html = "".join(
        f'<a href="{_esc(f["download_url"])}" class="download-link" download>'
        f'📄 {_esc(f["file_name"])}'
        + (f' <small>({_esc(f["file_size"])})</small>' if f.get("file_size") else "")
        + "</a>"
        for f in full["files"]
    ) or '<p class="files-empty">Chưa có biểu mẫu đính kèm.</p>'

    meta_line = " · ".join(
        x for x in [
            f"⚖️ Căn cứ: {_esc(p['meta_source'])}" if p.get("meta_source") else None,
            f"Hiệu lực từ: {_esc(p['effective_date'])}" if p.get("effective_date") else None,
            # Chỉ để tham khảo (metadata) -- KHÔNG tự bật banner cảnh báo, xem
            # docstring render_card(). ETL chịu trách nhiệm xoá thủ tục hết hạn.
            f"Hết hiệu lực: {_esc(p['expiration_date'])}" if p.get("expiration_date") else None,
        ] if x
    )

    # noi_nop = "nộp ở đâu / cơ quan nào / nộp online được không" -> gộp cả 4
    # dòng liên quan (cơ quan, hình thức nộp, địa điểm trực tiếp, link online)
    # dưới 1 nhóm highlight, khớp mô tả FACET_LABELS['noi_nop'].
    noi_nop_class = _hl(facet, "noi_nop").strip()
    receiving_html = (f'<p class="{noi_nop_class}"><strong>Địa điểm nộp trực tiếp:</strong> '
                       f'{_esc(p["receiving_location"])}</p>') if p.get("receiving_location") else ""
    online_html = (f'<p class="{noi_nop_class}"><strong>Nộp trực tuyến:</strong> '
                    f'<a href="{_esc(p["online_url"])}" target="_blank" rel="noopener">'
                    f'🔗 Cổng Dịch vụ công</a></p>') if p.get("online_url") else ""

    return f"""<div class="procedure-card" data-proc-id="{_esc(p['proc_code'])}">
  <div class="proc-header">
    <h3 class="proc-title">📋 {_esc(p['name'])}</h3>
    <span class="proc-badge badge-domain">{_esc(p['domain'])}</span>
    <span class="proc-badge badge-scope">{_esc(scope)}</span>
  </div>
{suggestion_html}
  <div class="proc-section proc-overview">
    <p class="{noi_nop_class}"><strong>Cơ quan giải quyết:</strong> {_esc(p.get('authority') or 'Chưa rõ')}</p>
    <p class="{noi_nop_class}"><strong>Hình thức nộp:</strong> {_esc(p.get('application_method') or 'Chưa rõ')}</p>
{receiving_html}
{online_html}
    <p class="{_hl(facet, 'thoi_gian').strip()}"><strong>Thời hạn:</strong> {_esc(p.get('duration_desc') or 'Chưa rõ')}</p>
    <p>{_esc(p.get('description') or '')}</p>
  </div>

  <div class="proc-section proc-fees{_hl(facet, 'le_phi')}">
    <h4>💰 Lệ phí:</h4>
    {fees_html}
  </div>

  <div class="proc-section proc-checklist{_hl(facet, 'ho_so')}">
    <h4>📑 Checklist hồ sơ cần chuẩn bị:</h4>
    {checklist_html}
  </div>

  <div class="proc-section proc-files">
    <h4>📥 Biểu mẫu đính kèm:</h4>
    {files_html}
  </div>

  <div class="proc-footer">
    <small>{meta_line or 'Chưa có căn cứ pháp lý.'}</small>
    <button class="btn-switch-s1" onclick="triggerWebSearch('{_esc(p['name'])}')">
      🌐 Tra cứu Web trực tiếp (System 1)
    </button>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# CLI demo — chạy trên dữ liệu thật đã nạp
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--demo", help="Câu/từ khóa để test resolve_query() + render_card()")
    ap.add_argument("--province", default=None)
    ap.add_argument("--facet", default="tong_quan", choices=list(FACET_LABELS))
    ap.add_argument("--out", default=None, help="Ghi HTML card ra file để mở xem trực quan")
    args = ap.parse_args()

    if not args.demo:
        ap.print_help()
        return

    conn = connect(args.db)
    result = resolve_query(conn, args.demo, province=args.province)
    print()
    print("debug:", result["debug"])
    if not result["found"]:
        print(f"Không tìm thấy thủ tục nào khớp '{args.demo}'.")
        return
    print("primary proc_code:", result["primary"]["procedure"]["proc_code"],
          "-", result["primary"]["procedure"]["name"],
          "| confident:", result["confident"])
    if result["suggestion"]:
        print("suggestion:", result["suggestion"])
    html_out = render_card(result["primary"], facet=args.facet, suggestion=result["suggestion"])
    if args.out:
        Path(args.out).write_text(html_out, encoding="utf-8")
        print(f"\nĐã ghi HTML card ra {args.out}")
    else:
        print("\n--- HTML card (rút gọn 600 ký tự đầu) ---")
        print(html_out[:600], "...")


if __name__ == "__main__":
    main()

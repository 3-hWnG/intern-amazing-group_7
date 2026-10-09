"""Chạy: python -m system3.data.tests.test_data   (hoặc pytest nếu có). Cần build trước."""
import re
import sys
from pathlib import Path

from system3.data import api

DATA = Path(__file__).resolve().parents[1]
conn = api.connect()
Q = lambda sql, *a: conn.execute(sql, a).fetchall()
STATS = {}


def test_active_count():
    assert Q("SELECT COUNT(*) FROM procedures WHERE status='active'")[0][0] == 1350


def test_fee_kinds():
    # kind theo thủ tục: numeric > text_only > none
    rows = Q("""SELECT proc_id, MAX(CASE kind WHEN 'numeric' THEN 3 WHEN 'text_only' THEN 2 ELSE 1 END) k
                FROM fees_clean GROUP BY proc_id""")
    assert len(rows) == 1350
    c = {1: 0, 2: 0, 3: 0}
    for r in rows:
        c[r["k"]] += 1
    STATS.update(fee_numeric=c[3], fee_text_only=c[2], fee_none=c[1])
    assert sum(c.values()) == 1350 and c[1] > 0


def test_none_never_free():
    # kind=none: chunk 'fees' phải rỗng, status không phải present, và không có chữ 'miễn phí'.
    bad = Q("""SELECT c.proc_id FROM field_chunks c JOIN fees_clean f ON f.proc_id=c.proc_id
               WHERE c.field='fees' AND f.kind='none'
                 AND (c.text<>'' OR c.status='present' OR lower(c.text) LIKE '%miễn phí%')""")
    assert not bad, bad[:3]
    # kind=none không mang số tiền
    assert not Q("SELECT 1 FROM fees_clean WHERE kind='none' AND (amount_value IS NOT NULL OR amount_text<>'')")
    # 'present' rỗng đã được hạ xuống unknown
    assert not Q("SELECT 1 FROM field_chunks WHERE status='present' AND text=''")


def test_team_overlay():
    # overlay chỉ bù thủ tục cổng KHÔNG có lệ phí, không đè dữ liệu cổng; khai sinh có 8.000đ
    assert not Q("SELECT 1 FROM team_fee_overlay o JOIN fees_clean f ON f.proc_id=o.proc_id WHERE f.kind<>'none'")
    assert any("8.000" in r[0] for r in Q("SELECT amount_text FROM team_fee_overlay WHERE proc_id='1.001193'"))
    STATS.update(team_overlay=Q("SELECT COUNT(DISTINCT proc_id) FROM team_fee_overlay")[0][0])


def test_families():
    n = Q("SELECT COUNT(DISTINCT head) FROM families")[0][0]
    multi = Q("SELECT COUNT(DISTINCT head) FROM families WHERE n_members>1")[0][0]
    STATS.update(families=n, multi=multi)
    assert 900 <= n <= 960 and 70 <= multi <= 100, (n, multi)
    # đúng 1 default_variant mỗi nhóm; nhóm 1 thành viên default=1
    assert not Q("SELECT head FROM families GROUP BY head HAVING SUM(default_variant)<>1")
    assert not Q("SELECT 1 FROM families WHERE n_members=1 AND default_variant=0")


def test_chunks_for_checklist():
    miss = Q("""SELECT p.proc_id FROM procedures p WHERE p.status_checklist='present'
                AND NOT EXISTS (SELECT 1 FROM field_chunks c WHERE c.proc_id=p.proc_id
                                AND c.field='components' AND c.text<>'')""")
    # status_checklist='present' nhưng không có dòng nào: báo số, tối đa vài ca
    STATS["checklist_present_but_empty"] = len(miss)
    assert len(miss) < 30, len(miss)
    assert Q("SELECT COUNT(*) FROM field_chunks WHERE field='components' AND text<>''")[0][0] > 1000
    assert {r[0] for r in Q("SELECT DISTINCT field FROM field_chunks")} == {
        "components", "fees", "processing_time", "address", "online", "methods", "files",
        "agency", "steps", "explanation", "meta", "legal_basis"}


def test_conditions_and_synonyms():
    STATS["conditions"] = Q("SELECT COUNT(*) FROM condition_index")[0][0]
    assert {r[0] for r in Q("SELECT DISTINCT source FROM condition_index")} == {"case", "subject", "variant_name"}
    assert not Q("SELECT 1 FROM condition_index WHERE text IN ('Giấy tờ phải nộp','Giấy tờ phải xuất trình','Lưu ý')")
    assert api.parse_query(conn, "t muốn dk kết hôn")["keyword"] == "dang ky ket hon"


def test_search_api():
    hits = api.search(conn, "đăng ký kết hôn", 5)
    assert hits and "kết hôn" in hits[0]["name"].lower()
    hits = api.search(conn, "dk khai sinh", 5)
    assert hits and "khai sinh" in hits[0]["name"].lower()
    pid = hits[0]["proc_id"]
    assert api.get_record(conn, pid)["proc_id"] == pid
    assert api.fields(conn, pid, ["fees", "components"])
    f = api.family_of(conn, pid)
    assert f and api.default_variant(conn, f["head"])
    assert api.variants(conn, f["head"])[0]["default_variant"] == 1
    assert api.is_expired(conn, pid) is None


def test_no_legacy_imports():
    pat = re.compile(r"^\s*(?:from|import)\s+(?:Database|Backend)\b", re.M)
    for f in DATA.glob("*.py"):
        assert not pat.search(f.read_text(encoding="utf-8")), f
    for f in DATA.glob("*.py"):
        assert "AXIS_" not in f.read_text(encoding="utf-8").replace("AXIS_*", "") or f.name == "test_data.py"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
            except Exception as e:
                fails += 1
                print("FAIL", name, repr(e))
    print(STATS)
    raise SystemExit(1 if fails else 0)

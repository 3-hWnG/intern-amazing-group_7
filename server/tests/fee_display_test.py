"""G1.1 (P01/F1): lệ phí in đúng đơn vị. USD không còn thành "đồng"; "20.000" đọc thành 20 được sửa; số không đối chiếu được thì in nguyên văn.
Chạy (trên DB cố định): python run_server.py eval/run_tests.py fee_display     hoặc  python run_server.py server/tests/fee_display_test.py"""
import os, re, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.setdefault("S3_USE_LLM", "0")
import tempfile
os.environ.setdefault("S3_DB_PATH", os.path.join(tempfile.mkdtemp(), "s3.db"))

from system3.data import api, fees as F
from answer import answer
from answer.answerer import _fees_text, procedure_table
from planner import plan as make_plan
from policy import check, pre_check

conn = api.connect()


def ask(q: str) -> str:
    pc = pre_check(q)
    p = make_plan([{"role": "user", "text": pc["text"]}])
    r = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
    a = answer(r, conn=conn, question=pc["text"], llm=None)
    return "\n".join(b["text"] for b in a["blocks"])


# ---- cột mới có trong DB dựng lại
cols = {r[1] for r in conn.execute("PRAGMA table_info(fees_clean)")}
assert {"currency", "amount_vnd", "amount_ok"} <= cols, cols
assert conn.execute("SELECT COUNT(*) FROM fees_clean WHERE currency='USD'").fetchone()[0] >= 2

# ---- chứng thực bản sao (2.000815) và chứng thực chữ ký (2.000884): dòng USD in "10 USD", không còn "10 đồng"
for pid in ("2.000815", "2.000884"):
    txt, st = _fees_text(conn, pid)
    assert st == "present" and "10 USD" in txt and not re.search(r"(?<![\d.])10 đồng", txt), (pid, txt)

for q in ("Lệ phí chứng thực bản sao từ bản chính là bao nhiêu?", "chứng thực chữ ký mất bao nhiêu tiền"):
    out = ask(q)
    assert not re.search(r"(?<![\d.])10 đồng", out), (q, out)
    assert "10 USD" in out or "/bản" in out, (q, out)

# ---- "20.000" đọc thành 20: in 20.000 đồng
r = dict(conn.execute("SELECT * FROM fees_clean WHERE proc_id='1.000014' AND kind='numeric'").fetchone())
assert r["amount_value"] == 20 and r["amount_vnd"] == 20000 and r["amount_ok"] == 1, r
assert F.display(r).startswith("20.000 đồng"), F.display(r)

# ---- "4.000 đ" đọc thành 40 (không phải lỗi hàng nghìn): không in số máy đọc, in nguyên văn chữ
txt, _ = _fees_text(conn, "1.003133")
assert "40 đồng" not in txt and "4.000 đ" in txt, txt

# ---- không còn dòng nào in số < 1.000 "đồng" mà chữ không xác nhận
bad = []
for r in conn.execute("SELECT * FROM fees_clean WHERE kind='numeric'"):
    s = F.display(dict(r))
    m = re.match(r"^(\d{1,3}) đồng", s)
    if m and not re.search(r"(?<![\d.])" + m.group(1) + r"\s*(đ|đồng|vnđ|vnd)", r["amount_text"] or "", re.I):
        bad.append((r["proc_id"], s))
assert not bad, bad[:5]

# ---- bảng đầy đủ dùng cùng cách in
t = procedure_table(conn, "2.000815")
fee_row = next(x for x in t["rows"] if x["field"] == "fees")
assert "10 USD" in fee_row["text"] and not re.search(r"(?<![\d.])10 đồng", fee_row["text"]), fee_row

# ---- field_chunks (dòng phí cho LLM / tìm kiếm) cũng không còn "10 đồng"
ch = conn.execute("SELECT text FROM field_chunks WHERE proc_id='2.000815' AND field='fees'").fetchone()[0]
assert "10 USD" in ch and not re.search(r"(?<![\d.])10 đồng", ch), ch

# ---- chuẩn hoá thuần
assert F.normalize(25, "25.000.000đ", "")["amount_vnd"] == 25000000
assert F.normalize(10, "/bản", "019b3fb2-dee2-76ab-aa53-22d4d903a2bb") == {"currency": "USD", "amount_vnd": None, "amount_ok": 1}
assert F.normalize(20, "", "")["amount_ok"] == 0
assert F.normalize(500, "500 đồng/bản", "019b3fb2-b5b8-70ac-85e2-9409ec1eaffa")["amount_vnd"] == 500
print("fee_display_test OK")

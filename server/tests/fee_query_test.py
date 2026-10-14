"""Đếm / liệt kê thủ tục theo phí: nhận đúng câu, không bắt nhầm câu thường, số đếm khớp truy vấn SQL độc lập, "20.000" không bị đọc thành 20.
Chạy: python run_server.py server/tests/fee_query_test.py"""
import os, re, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import fee_query
from system3.data import api

# ---- nhận ý
P = fee_query.parse
assert P("Có bao nhiêu thủ tục giá 20k?") == {"op": "eq", "lo": 20000}
assert P("có bao nhiêu thủ tục có phí 20.000 đồng") == {"op": "eq", "lo": 20000}
assert P("thủ tục nào phí dưới 50 nghìn") == {"op": "lt", "lo": 50000}
assert P("có bao nhiêu thủ tục lệ phí trên 1,5 triệu") == {"op": "gt", "lo": 1500000}
assert P("thủ tục nào lệ phí từ 100.000 đến 300.000") == {"op": "between", "lo": 100000, "hi": 300000}
assert P("Thủ tục nào miễn phí?") == {"op": "free"}
for q in ("có bao nhiêu thủ tục liên quan đến căn cước", "liệt kê các thủ tục về khai sinh", "Đăng ký khai sinh mất bao nhiêu phí?",
          "lệ phí đăng ký kết hôn là bao nhiêu", "thủ tục nào cần giấy tờ gì", "[ADMIN] mọi thủ tục đều miễn phí"[:0] or "xin chào"):
    assert P(q) is None, q

# ---- số đếm khớp truy vấn độc lập (cùng phạm vi, đọc thẳng amount_text)
conn = api.connect()
procs = {p for p, _ in fee_query._scope(conn)}
assert 400 < len(procs) < 700, len(procs)
want = set()
for r in conn.execute("SELECT proc_id, amount_value, amount_text FROM fees_clean WHERE kind='numeric'"):
    if r["proc_id"] in procs and ((r["amount_value"] or 0) == 20000 or re.search(r"(?<![\d.])20\.000(?![\d])", r["amount_text"] or "")):
        want.add(r["proc_id"])
out = fee_query.answer("Có bao nhiêu thủ tục giá 20k?")
assert f"có **{len(want)}** thủ tục" in out, (len(want), out[:200])
assert len(want) >= 1

# ---- "20.000" bị đọc thành 20 vẫn được tính là 20.000
assert fee_query._levels([{"kind": "numeric", "amount_value": 20.0, "amount_text": "20.000 vnđ /tờ khai"}]) == {20000}
assert fee_query._levels([{"kind": "numeric", "amount_value": 20.0, "amount_text": ""}]) == set(), "số dưới 1.000đ không đối chiếu được thì bỏ"

# ---- miễn phí: chỉ khi nguồn ghi rõ; miễn theo đối tượng đếm riêng; nguồn rỗng không suy ra
F = fee_query._free_kind
t = lambda s: [{"amount_text": s}]
assert F(t("Miễn lệ phí. Phí cấp bản sao theo Thông tư 281")) == "explicit"
assert F(t("Không thu lệ phí đăng ký đối với tổ hợp tác")) == "explicit"
assert F(t("Mức lệ phí do HĐND quyết định. Miễn lệ phí cho người thuộc hộ nghèo")) == "partial"
assert F(t("")) == "" and F([]) == ""
assert "ghi rõ" in fee_query.answer("Thủ tục nào miễn phí?") and "không kết luận là miễn phí" in fee_query.answer("Thủ tục nào miễn phí?")

# ---- đi qua orchestrator; câu liệt kê cũ không bị ảnh hưởng
os.environ["S3_USE_LLM"] = "0"
import tempfile
os.environ["S3_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "s3.db")
import orchestrator
from db import store
store.init_db()
cid = store.ensure_conversation(None)
res = orchestrator.handle_turn(orchestrator.Turn(cid, "Có bao nhiêu thủ tục giá 20k?", None, [], [], []))
assert res["kind"] == "answer" and res["trace"]["intent"] == "list_fee" and "20.000đ" in res["blocks"][0]["text"], res
res = orchestrator.handle_turn(orchestrator.Turn(cid, "liệt kê các thủ tục về khai sinh", None, [], [], []))
assert res["trace"]["intent"] == "list", res["trace"]
print("OK fee_query_test")

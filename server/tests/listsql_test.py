"""G4.2: liệt kê / đếm bằng text-to-SQL (server/listsql.py) — hộp cát + luồng, LLM giả.
Chạy: python run_server.py server/tests/listsql_test.py"""
import json, os, sqlite3, sys, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_NO_WARMUP="1", S3_PLANNER_MODE="rules")

import listsql
from system3.data import api

src = api.connect()
n_scope = src.execute("SELECT COUNT(*) FROM proc_flat WHERE in_scope=1").fetchone()[0]
n_all = src.execute("SELECT COUNT(*) FROM proc_flat").fetchone()[0]
box, domains = listsql.sandbox(src)
assert n_scope > 0 and domains

# ---- hộp cát: chỉ đọc proc_flat (bản sao trong bộ nhớ, chỉ thủ tục trong phạm vi)
assert box.execute("SELECT COUNT(*) FROM proc_flat").fetchone()[0] == n_scope
_, rows = listsql.run_sql(box, "SELECT name FROM proc_flat ORDER BY name;")
assert len(rows) == min(n_scope, listsql.MAX_ROWS), "ép LIMIT 200"
_, rows = listsql.run_sql(box, "WITH h AS (SELECT name FROM proc_flat WHERE domain='Hộ tịch') SELECT COUNT(*) FROM h")
assert rows[0][0] >= 0
# model viết chữ có dấu trong LIKE + lọt '}' cuối câu: code bỏ dấu và làm sạch
kw = src.execute("SELECT name FROM proc_flat WHERE in_scope=1 LIMIT 1").fetchone()[0].split()[-1]
_, a = listsql.run_sql(box, f"SELECT COUNT(*) FROM proc_flat WHERE name LIKE '%{kw.upper()}%'}}")
_, b = listsql.run_sql(box, f"SELECT COUNT(*) FROM proc_flat WHERE name_fold LIKE '%{listsql.fold(kw)}%'")
assert a == b and a[0][0] >= 1, (kw, a, b)
BAD = ["DELETE FROM proc_flat", "DROP TABLE proc_flat", "UPDATE proc_flat SET name='x'", "INSERT INTO proc_flat(name) VALUES ('x')",
       "PRAGMA query_only=0", "ATTACH DATABASE 'x.db' AS x", "SELECT 1; DROP TABLE proc_flat", "SELECT * FROM sqlite_master",
       "SELECT load_extension('evil')", "SELECT name FROM proc_flat WHERE 1=1; DELETE FROM proc_flat",
       "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) SELECT x FROM c",
       "SELECT * FROM procedures", "VACUUM", "SELECT writefile('x', 'y')"]
for sql in BAD:
    try:
        listsql.run_sql(box, sql)
        raise AssertionError(f"phải chặn: {sql}")
    except (listsql.SQLRejected, sqlite3.Error):
        pass
try:   # truy vấn quá nặng: progress_handler huỷ
    listsql.run_sql(box, "SELECT COUNT(*) FROM proc_flat a, proc_flat b, proc_flat c, proc_flat d", max_steps=200_000)
    raise AssertionError("phải huỷ truy vấn quá nặng")
except sqlite3.OperationalError:
    pass
assert box.execute("SELECT COUNT(*) FROM proc_flat").fetchone()[0] == n_scope, "hộp cát không bị đổi"
assert src.execute("SELECT COUNT(*) FROM proc_flat").fetchone()[0] == n_all, "DB thật không bị đổi"

# ---- ý liệt kê
assert listsql.wants("Liệt kê các thủ tục thuộc lĩnh vực Hộ tịch.") and listsql.wants("Có bao nhiêu thủ tục về kết hôn?")
assert listsql.wants("những thủ tục nào nộp trực tuyến được") and not listsql.wants("Đăng ký khai sinh cần giấy tờ gì?")

# ---- luồng với LLM giả
dom = domains[0]
want = [r[0] for r in src.execute("SELECT name FROM proc_flat WHERE in_scope=1 AND domain=? ORDER BY name", (dom,))]
calls = []


def llm_seq(*outs):
    it = iter(outs)

    def f(system, user, **kw):
        calls.append(user)
        assert kw.get("schema") == listsql.SCHEMA and "proc_flat" in system and dom in system
        o = next(it)
        if isinstance(o, Exception):
            raise o
        return o
    return f


r = listsql.answer(f"Liệt kê các thủ tục thuộc lĩnh vực {dom}", llm_seq({"sql": f"SELECT name FROM proc_flat WHERE domain = '{dom}' ORDER BY name"}))
assert r["kind"] == "list" and r["names"] == want and r["tries"] == 1 and f"**{len(want)}**" in r["text"], r
r = listsql.answer("Có bao nhiêu thủ tục về hộ tịch?", llm_seq({"sql": f"SELECT COUNT(*) FROM proc_flat WHERE domain = '{dom}'"}))
assert r["kind"] == "count" and r["count"] == len(want) and f"**{len(want)}**" in r["text"], r
calls.clear()   # câu sai -> sửa lần 2 (lỗi được gửi lại cho LLM)
r = listsql.answer(f"liệt kê thủ tục {dom}", llm_seq({"sql": "SELECT nam FROM proc_flat"}, {"sql": f"SELECT name FROM proc_flat WHERE domain='{dom}'"}))
assert r and r["tries"] == 2 and "lỗi" in calls[-1], (r, calls)
assert listsql.answer("liệt kê thủ tục", llm_seq({"sql": "DELETE FROM proc_flat"}, {"sql": "DROP TABLE proc_flat"})) is None, "tiêm 2 lần -> lùi"
assert listsql.answer("liệt kê thủ tục", llm_seq(TimeoutError("hết giờ"))) is None
assert listsql.answer("liệt kê thủ tục", None) is None, "không có LLM (máy CPU / chỉ luật): lùi về đường cũ"
assert listsql.answer("Khai sinh cần giấy tờ gì", llm_seq()) is None
r = listsql.answer("liệt kê thủ tục có chữ xyzxyz", llm_seq({"sql": "SELECT name FROM proc_flat WHERE name_fold LIKE '%xyzxyz%'"}))
assert r["count"] == 0 and "Không có thủ tục nào" in r["text"]

# ---- qua /chat: LLM giả ở core.llm; câu tiêm trong câu hỏi không làm hỏng gì
os.environ["S3_USE_LLM"] = "1"
from core import llm as core_llm


class Fake:
    def __init__(self, sql):
        self.sql = sql

    def chat(self, **kw):
        return {"message": {"content": json.dumps({"sql": self.sql})}}


from fastapi.testclient import TestClient
import main
with TestClient(main.app) as c:
    core_llm.client = lambda timeout=None: Fake(f"SELECT name FROM proc_flat WHERE domain = '{dom}' ORDER BY name")
    out = c.post("/chat", json={"text": f"Liệt kê các thủ tục thuộc lĩnh vực {dom}"}).json()
    assert out["blocks"][0]["title"] == "Danh sách thủ tục" and want[0] in out["blocks"][0]["text"], out
    core_llm.client = lambda timeout=None: Fake("DELETE FROM proc_flat")
    out = c.post("/chat", json={"text": "Liệt kê thủ tục'); DROP TABLE procedures; --"}).json()
    assert out["blocks"] and out["blocks"][0]["title"] != "Danh sách thủ tục", "SQL bị chặn -> lùi về liệt kê gần đúng"
assert src.execute("SELECT COUNT(*) FROM procedures").fetchone()[0] > 0
print("OK listsql_test")

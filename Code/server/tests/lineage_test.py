"""G2.3 (P08): lineage mã thủ tục. Dựng DB từ bản Gốc đã sửa: một thủ tục bị Cổng cấp mã mới (cùng source_id), một thủ tục
mã mới + source_id mới nhưng cùng tên + tỉnh, một thủ tục biến mất. Kiểm proc_lineage, data_api.canonical, báo cáo dựng,
và hội thoại cũ (conv_state / shown_procedures) được đổi sang mã mới khi nạp.
Chạy: python run_server.py server/tests/lineage_test.py   (dựng DB ~10 s, không cần mạng / LLM)"""
import json, os, sqlite3, sys, tempfile
from pathlib import Path
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.setdefault("S3_USE_LLM", "0")
TMP = Path(tempfile.mkdtemp())
os.environ["S3_DB_PATH"] = str(TMP / "s3.db")

ROOT = Path(HERE).parent
recs = [json.loads(l) for l in (ROOT / "data" / "snapshot" / "procedures.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
by = {r["proc_id"]: r for r in recs}
KH, KS, KT = "1.000894", "1.001193", "1.000656"     # kết hôn, khai sinh, khai tử
# kết hôn: Cổng cấp mã mới, giữ source_id
by[KH] = {**by[KH], "proc_id": "9.900001"}
# khai sinh: mã mới + source_id mới, cùng tên + tỉnh -> ghép theo tên
by[KS] = {**by[KS], "proc_id": "9.900002", "source_id": "00000000-0000-0000-0000-000000000002"}
# khai tử: biến mất
del by[KT]
src = TMP / "v_new.jsonl"
src.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in by.values()), encoding="utf-8")
out = TMP / "v_new.db"

from system3.system4.server import procs_xlsx   # noqa: E402  (dựng bằng chính system3.data.build ở tiến trình con)
n = procs_xlsx.db_from_jsonl(src, out)
assert n == len(recs) - 1
c = sqlite3.connect(out)
lin = {r[0]: (r[1], r[2]) for r in c.execute("SELECT old_id, new_id, method FROM proc_lineage")}
assert lin[KH] == ("9.900001", "source_id"), lin.get(KH)
assert lin[KS] == ("9.900002", "name_province"), lin.get(KS)
assert lin[KT] == (None, "unmatched"), lin.get(KT)
assert len(lin) == 3, lin
rep = json.loads(out.with_name(out.name + ".report.json").read_text(encoding="utf-8"))["lineage"]
assert rep["source_id"] == 1 and rep["name_province"] == 1 and rep["unmatched"] == 1
assert [x["old_id"] for x in rep["unmatched_list"]] == [KT]

# ---- System 3 đọc DB này: mã cũ -> mã mới
os.environ["S3_DATA_DB"] = str(out)
from system3.data import api as data_api   # noqa: E402
conn = data_api.connect(out)
assert data_api.canonical(conn, KH) == "9.900001" and data_api.canonical(conn, "1.000005") == "1.000005"
import orchestrator   # noqa: E402
state = {"topic": KH, "history": [KS, KH], "order": [KS, KH], "fields": ["fees"], "story": [], "loose": False}
st, shown = orchestrator._remap_ids(conn, state, [{"proc_id": KH, "label": "Đăng ký kết hôn", "ordinal": 1}])
assert st["topic"] == "9.900001" and st["history"] == ["9.900002", "9.900001"] and shown[0]["proc_id"] == "9.900001", (st, shown)
print("OK lineage_test")

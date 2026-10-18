"""G4.4: mẫu 20 câu cho hỏi lại tỉnh trên DB đang dùng (bản 3). Câu sinh từ tên thủ tục toàn quốc có bản riêng tỉnh:
  10 câu không nêu tỉnh -> phải ra thẻ hỏi tỉnh; 10 câu nêu một tỉnh có bản riêng -> phải trả lời bằng đúng bản của tỉnh đó.
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> S3_USE_LLM=0 python run_server.py eval/province_sample.py"""
import os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "server"))
os.environ.update(S3_DB_PATH=os.path.join(tempfile.mkdtemp(), "s3.db"), S3_USE_LLM="0", S3_NO_WARMUP="1", S3_PLANNER_MODE="rules", S3_DEV="1")
from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402
from system3.data import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
rng = random.Random(5)
conn = api.connect()
fams = {}
for (p,) in conn.execute("SELECT proc_id FROM proc_flat WHERE in_scope=1"):
    v = api.province_versions(conn, p)
    if len(v) >= 2:
        fams[p] = v
pids = sorted(fams)
rng.shuffle(pids)
FIELDS = ["cần giấy tờ gì?", "lệ phí bao nhiêu?", "mất bao lâu?", "nộp ở đâu?"]
ok_a = ok_b = 0
with TestClient(main.app) as c:
    for i, pid in enumerate(pids[:10]):
        name = conn.execute("SELECT name FROM procedures WHERE proc_id=?", (pid,)).fetchone()[0]
        q = f"{name} {FIELDS[i % 4]}"
        out = c.post("/chat", json={"text": q}).json()
        good = (out.get("clarify") or {}).get("meta", {}).get("kind") == "province"
        ok_a += good
        why = "" if good else f"  -> {out['kind']}: {[b['text'][:60] for b in out['blocks']][:1] or (out.get('clarify') or {}).get('question', '')[:60]}"
        print(("ĐÚNG " if good else "SAI  ") + "không nêu tỉnh: " + q[:80] + why)
    for i, pid in enumerate(pids[:10]):
        name = conn.execute("SELECT name FROM procedures WHERE proc_id=?", (pid,)).fetchone()[0]
        prov = rng.choice(sorted(fams[pid]))
        q = f"Tôi ở {prov}, {name[0].lower() + name[1:]} {FIELDS[(i + 1) % 4]}"
        out = c.post("/chat", json={"text": q}).json()
        ts = out.get("dev", {}).get("trace", {}).get("routed", {}).get("tasks") or []
        got = ts[0]["procedure_id"] if ts else None
        good = not out.get("clarify") and got == fams[pid][prov]
        ok_b += good
        print(("ĐÚNG " if good else "SAI  ") + f"nêu tỉnh {prov}: " + q[:70] + ("" if good else f"  -> {out['kind']} {got} (cần {fams[pid][prov]})"))
print(f"\nkhông nêu tỉnh -> hỏi tỉnh: {ok_a}/10; nêu tỉnh -> đúng bản của tỉnh: {ok_b}/10 (tổng {len(fams)} thủ tục toàn quốc có >= 2 bản riêng tỉnh)")

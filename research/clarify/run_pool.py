"""Chạy bộ luật hiện tại trên research/clarify/pool.jsonl (hoặc tệp khác): hành vi, lý do, top-5 ứng viên (mã, tên, họ).
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> S3_USE_LLM=0 python run_server.py research/clarify/run_pool.py [vào.jsonl] [ra.jsonl]"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "eval"), os.path.join(ROOT, "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from system3.data import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "pool.jsonl")
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "pool_run.jsonl")
conn = api.connect()
names = {r[0]: r[1] for r in conn.execute("SELECT proc_id, name FROM procedures WHERE status='active'")}


def head(p):
    f = api.family_of(conn, p)
    return f["head"] if f else p


t0 = time.time()
with open(dst, "w", encoding="utf-8") as out:
    for i, l in enumerate(open(src, encoding="utf-8")):
        x = json.loads(l)
        pc = pre_check(x["q"])
        p = make_plan([{"role": "user", "text": pc["text"]}])
        r = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
        t = p.tasks[0] if p.tasks else None
        cands = [c for c in dict.fromkeys(([t.procedure_id] if t and t.procedure_id else []) + list((t.candidates if t else []) or [])) if c in names][:5]
        x.update(beh=r.behavior, ntasks=len(p.tasks), routes=[[rt.route, rt.reason] for rt in r.tasks],
                 chosen=[rt.procedure_id for rt in r.tasks if rt.route == "direct"],
                 clarify=[o["label"] for o in (r.clarify or {}).get("options", [])], cands=cands,
                 cand_names=[names[c] for c in cands], heads=[head(c) for c in cands])
        out.write(json.dumps(x, ensure_ascii=False) + "\n")
        if i % 500 == 0:
            print(i, f"{time.time() - t0:.0f}s", flush=True)
print("xong", dst)

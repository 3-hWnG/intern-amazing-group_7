"""Đặc trưng cho các cách hỏi lại (M6: gợi ý thay vì xin lỗi): với mỗi câu (dev golden một lượt, cases_p30, câu thật đã gán nhãn)
chạy bộ luật hiện tại, rồi tìm theo nghĩa (bge-m3 qua Ollama) câu hỏi × tên các thủ tục trong phạm vi.
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> S3_USE_LLM=0 python run_server.py research/clarify/features.py
Ghi research/clarify/features.jsonl. Không dùng bộ mù."""
import json, math, os, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "eval"), os.path.join(ROOT, "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from system3.data import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
conn = api.connect()
procs = [(r[0], r[1]) for r in conn.execute("SELECT proc_id, name FROM proc_flat WHERE in_scope=1 ORDER BY proc_id")]
HOST = os.environ.get("OLLAMA_EMBED_HOST", "http://127.0.0.1:11434")


def embed(texts):
    out = []
    for i in range(0, len(texts), 64):
        req = urllib.request.Request(HOST + "/api/embed", json.dumps({"model": "bge-m3", "input": texts[i:i + 64]}).encode(),
                                     {"Content-Type": "application/json"})
        out += json.load(urllib.request.urlopen(req, timeout=300))["embeddings"]
    return out


def norm(v):
    s = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / s for x in v]


cache = os.path.join(HERE, "cache_names_v3.json")
if os.path.exists(cache):
    E = json.load(open(cache, encoding="utf-8"))
else:
    E = dict(zip([p for p, _ in procs], [norm(v) for v in embed([n for _, n in procs])]))
    json.dump(E, open(cache, "w", encoding="utf-8"))
ids = [p for p, _ in procs]
names = dict(procs)


def head(p):
    f = api.family_of(conn, p)
    return f["head"] if f else p


rows = []
for l in open(os.path.join(ROOT, "eval", "golden", "thu-tuc.jsonl"), encoding="utf-8"):
    c = json.loads(l)
    us = [t for t in c["turns"] if t["role"] == "user"]
    if c["status"] == "dev" and len(c["turns"]) == 1 and not c["expected"].get("list_domain"):
        rows.append({"set": "dev", "q": us[0]["text"], "label": {"answer": "A", "clarify": "C", "apologize": "O"}[c["expected"]["behavior"]]})
for l in open(os.path.join(ROOT, "eval", "cases_p30.jsonl"), encoding="utf-8"):
    c = json.loads(l)
    rows.append({"set": "p30-" + c["split"], "q": c["question"], "label": {"answer": "A", "clarify": "C"}[c["expected"]["behavior"]]})
for l in open(os.path.join(HERE, "real_questions_labeled.jsonl"), encoding="utf-8"):
    x = json.loads(l)
    if x["label"] != "X":
        rows.append({"set": "real-" + x["split"], "q": x["q"], "label": x["label"], "src": x["src"]})

qv = [norm(v) for v in embed([r["q"] for r in rows])]
with open(os.path.join(HERE, "features.jsonl"), "w", encoding="utf-8") as f:
    for r, v in zip(rows, qv):
        pc = pre_check(r["q"])
        p = make_plan([{"role": "user", "text": pc["text"]}])
        res = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
        sims = sorted(((sum(a * b for a, b in zip(v, E[i])), i) for i in ids), reverse=True)[:5]
        r.update(beh=res.behavior, reasons=[t.reason for t in res.tasks], ntasks=len(p.tasks),
                 emb=[[round(s, 4), i, names[i], head(i)] for s, i in sims])
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(rows), "câu")

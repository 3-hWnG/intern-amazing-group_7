"""G4.2: chấm liệt kê / đếm bằng text-to-SQL trên model THẬT (Ollama).
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> python run_server.py eval/run_listsql.py [--split dev|test|all] [--template]
- bộ riêng (eval/cases_listsql.jsonl): liệt kê đúng khi TẬP tên trả về = tập đáp án; đếm đúng khi số bằng đáp án.
  Ca SQL hỏng 2 lần (lùi về đường cũ) tính sai.
- --template: 40 câu "liệt kê lĩnh vực X" của eval/golden/template_thu-tuc.jsonl: % mục đúng lĩnh vực (như run_golden), so với
  đường cũ (orchestrator._list_request, 12% trên bản snapshot).
Ghi eval/results/listsql_<split>.json."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(os.path.dirname(HERE), "server")]
os.environ["S3_USE_LLM"] = "1"
import listsql  # noqa: E402
from orchestrator import _answer_llm, _list_request  # noqa: E402
from system3.data import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
split = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "test"
llm = _answer_llm()
conn = api.connect()
rows = []
for l in open(os.path.join(HERE, "cases_listsql.jsonl"), encoding="utf-8"):
    c = json.loads(l)
    if split != "all" and c["split"] != split:
        continue
    t = time.perf_counter()
    r = listsql.answer(c["question"], llm)
    ms = int((time.perf_counter() - t) * 1000)
    if not r:
        ok = False
    elif "count" in c["gold"] and c["kind"].startswith("count"):
        ok = r["count"] == c["gold"]["count"]
    else:
        ok = r["kind"] == "list" and set(r["names"]) == set(c["gold"]["names"])
    rows.append({**c, "ok": ok, "sql": (r or {}).get("sql"), "tries": (r or {}).get("tries"), "got": (r or {}).get("count"), "ms": ms})
    print(("ĐÚNG" if ok else "SAI ") + f" {c['kind']:<18} {ms:>5} ms  {c['question'][:60]}" + ("" if ok else f"\n      sql: {(r or {}).get('sql')}"), flush=True)
by = {}
for r in rows:
    by.setdefault(r["kind"], []).append(r["ok"])
print(f"\n{split}: {sum(r['ok'] for r in rows)}/{len(rows)} đúng; lùi về đường cũ {sum(1 for r in rows if not r['sql'])}")
for k, v in sorted(by.items()):
    print(f"  {k:<20} {sum(v)}/{len(v)}")
res = {"split": split, "n": len(rows), "ok": sum(r["ok"] for r in rows), "by_kind": {k: [sum(v), len(v)] for k, v in by.items()}, "rows": rows}

if "--template" in sys.argv:
    T = [json.loads(l) for l in open(os.path.join(HERE, "golden", "template_thu-tuc.jsonl"), encoding="utf-8") if l.strip()]
    T = [c for c in T if c["expected"].get("list_domain")]

    def prec(names, d):
        ok = [bool(conn.execute("SELECT 1 FROM procedures WHERE name=? AND domain LIKE ?", (n, f"%{d}%")).fetchone()) for n in names]
        return sum(ok) / len(ok) if ok else 0.0
    new, old, empty = [], [], 0
    for c in T:
        d = c["expected"]["list_domain"]
        r = listsql.answer(c["question"], llm)
        empty += bool(r) and not r["names"]
        new.append(prec(r["names"], d) if r else 0.0)
        txt = _list_request(c["question"]) or ""
        old.append(prec([x.split(". ", 1)[1] for x in txt.splitlines() if x[:1].isdigit() and ". " in x], d))
    print(f"\nbộ khuôn 'list' ({len(T)} câu): đúng lĩnh vực — mới {sum(new) / len(T):.0%}, cũ {sum(old) / len(T):.0%}; "
          f"mới trả danh sách rỗng {empty} câu (lĩnh vực không có thủ tục cấp xã trong bản này)")
    res["template"] = {"new": sum(new) / len(T), "old": sum(old) / len(T), "empty": empty}
out = os.path.join(HERE, "results", f"listsql_{split}.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

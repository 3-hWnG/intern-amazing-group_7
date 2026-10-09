"""Bộ test 10 câu của nhóm (Test_Case_Legal_AI_Assistant_Bang_Test.docx). python run_team.py [-v]  (PYTHONPATH=.. S3_USE_LLM=0)
Chấm tự động theo luật (KHÔNG phải điểm chính thức 4+2+2+2): đúng thủ tục, hành vi, có đủ ý chính, không dư task, không có mục bị cấm, độ dài."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402

rows = []
for c in json.load(open(os.path.join(HERE, "cases_team.json"), encoding="utf-8")):
    h = []
    for q in c["turns"]:
        h.append({"role": "user", "text": q}); out = answer_adapter.adapter(h); h.append({"role": "assistant", "text": out["answer_text"]})
    tops = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
    txt = out["answer_text"]
    proc_ok = (set(c["procs"]) <= set(tops)) if c.get("all_procs") else (not c["procs"] or (bool(tops) and tops[0] in c["procs"]))
    missing = [f for f in c["facts"] if not re.search(f, txt, re.I)]
    extra = max(0, len(tops) - c["max_tasks"]) if c["beh"] == "answer" else (0 if c["beh"] == "clarify" else len(tops))
    bad = [f for f in c.get("forbid", []) if f in txt]
    r = dict(id=c["id"], group=c["group"], beh_ok=out["behavior"] == c["beh"], proc_ok=proc_ok, facts_missing=missing, extra_tasks=extra,
             forbidden=bad, chars=len(txt), tops=tops, note=c.get("note", ""))
    r["pass"] = r["beh_ok"] and proc_ok and not missing and not extra and not bad
    rows.append(r)
    print(f"{r['id']} {'PASS' if r['pass'] else 'FAIL'} beh={'ok' if r['beh_ok'] else out['behavior']} proc={'ok' if proc_ok else tops} "
          f"thiếu={missing} dư_task={extra} cấm={bad} {r['chars']}ký tự {r['note']}")
print(f"PASS {sum(r['pass'] for r in rows)}/{len(rows)}  trung bình {sum(r['chars'] for r in rows)//len(rows)} ký tự")
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump(rows, open(os.path.join(HERE, "results", "team.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

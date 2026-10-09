"""Phase 31: đo "tên đầy đủ họ nhiều dạng thật -> hỏi lại" trên eval/cases_p31.jsonl (dựng bằng build_p31.py). Không LLM, không bộ mù.
Mỗi ca: pre_check -> Planner luật (nhiều lượt nếu có `turns`) -> Policy.check (có hồ sơ nếu có `profile_subject`). Chỉ số theo nửa tune/held/fresh:
  clarify recall = ca kỳ vọng clarify mà hỏi lại; options_ok = thẻ có >= 3 dạng của họ (ca prof-shrink: >= 2);
  over-clarify = ca kỳ vọng answer mà lại hỏi; answer top-1 = ca answer trả đúng thủ tục.
Chạy: python run_server.py eval/run_p31.py [-v] [--name p31] [--split tune|held|fresh|all] [--file cases_p31.jsonl]   (held/fresh chỉ chạy ở cuối đợt chỉnh; không in danh sách lỗi của held/fresh)"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(HERE, "..", "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from system3.data import api  # noqa: E402

conn = api.connect()


def route(c):
    pc = pre_check(c["question"])
    turns = (c.get("turns") or [])[:-1] + [{"role": "user", "text": pc["text"]}]
    p = make_plan(turns, use_llm=False)
    mem = {"subjects": {c["profile_subject"]}, "label": c["profile_subject"]} if c.get("profile_subject") else None
    return check(p, user_text=pc["text"], conn=conn, flags=pc["flags"], memory=mem)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-v", action="store_true"); ap.add_argument("--name", default="p31")
    ap.add_argument("--split", default="tune"); ap.add_argument("--file", default="cases_p31.jsonl")
    a = ap.parse_args()
    cases = [json.loads(l) for l in open(os.path.join(HERE, a.file), encoding="utf-8")]
    rows = []
    for c in cases:
        if a.split != "all" and c["split"] != a.split:
            continue
        r = route(c)
        pids = [t.procedure_id for t in r.tasks if t.route == "direct"]
        opts = [o["proc_id"] for o in (r.clarify or {}).get("options", [])]
        e = c["expected"]
        if e["behavior"] == "clarify":
            need = 2 if c["sub"] == "prof-shrink" else 3
            ok = r.behavior == "clarify"
            top = None
            opt_ok = ok and len(set(opts) & set(e["family"])) >= min(need, len(e["family"]))
        else:
            ok = r.behavior == "answer"
            top = bool(pids) and pids[0] in e["acceptable"]
            opt_ok = None
        rows.append({"id": c["id"], "split": c["split"], "kind": c["kind"], "sub": c["sub"], "q": c["question"], "behavior": r.behavior, "ok": ok, "top1": top, "opt_ok": opt_ok, "pids": pids, "options": opts})
        if a.v and not ok and c["split"] == "tune":
            print("MISS", c["id"], c["question"], "->", r.behavior, [t.procedure_label[:40] for t in r.tasks])
    out = {}
    for sp in ("tune", "held", "fresh"):
        cl = [x for x in rows if x["split"] == sp and x["kind"] == "clarify"]
        an = [x for x in rows if x["split"] == sp and x["kind"] == "answer"]
        if not cl and not an:
            continue
        out[sp] = {"clarify_recall": [sum(x["ok"] for x in cl), len(cl)], "options_ok": [sum(bool(x["opt_ok"]) for x in cl), len(cl)], "over_clarify": [sum(x["behavior"] == "clarify" for x in an), len(an)],
                   "answer_top1": [sum(bool(x["top1"]) for x in an), len(an)]}
        print(sp, "clarify recall %d/%d  (thẻ đủ dạng %d/%d)   over-clarify %d/%d   answer top-1 %d/%d" % (*out[sp]["clarify_recall"], *out[sp]["options_ok"], *out[sp]["over_clarify"], *out[sp]["answer_top1"]))
    sub = {}
    for x in rows:
        s = sub.setdefault((x["split"], x["sub"]), [0, 0]); s[0] += x["ok"]; s[1] += 1
    print("theo nhóm (đúng hành vi):", {f"{k[0]}/{k[1]}": f"{v[0]}/{v[1]}" for k, v in sorted(sub.items())})
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump({"summary": out, "rows": rows}, open(os.path.join(HERE, "results", a.name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

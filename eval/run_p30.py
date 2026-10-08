"""Phase 30: đo "hỏi lại khi mơ hồ" trên eval/cases_p30.jsonl (dựng bằng build_p30.py). Không LLM, không bộ mù.
Mỗi ca: pre_check -> Planner luật -> Policy.check (một lượt, không hồ sơ). Chỉ số theo nửa tune/held:
  clarify recall = ca kỳ vọng clarify mà hệ thống hỏi lại; over-clarify = ca kỳ vọng answer mà hệ thống lại hỏi; answer top-1 = ca answer trả đúng thủ tục.
Chạy: python run_server.py eval/run_p30.py [-v] [--name p30] [--split tune|held|all]   (held và fresh chỉ chạy ở cuối đợt chỉnh)"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(HERE, "..", "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from system3.data import api  # noqa: E402

conn = api.connect()


def route(q):
    pc = pre_check(q)
    p = make_plan([{"role": "user", "text": pc["text"]}], use_llm=False)
    r = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
    return r


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-v", action="store_true"); ap.add_argument("--name", default="p30"); ap.add_argument("--split", default="tune", help="tune (mặc định, dùng khi chỉnh) | held | fresh | all (chỉ chạy ở cuối đợt)")
    a = ap.parse_args()
    cases = [json.loads(l) for l in open(os.path.join(HERE, "cases_p30.jsonl"), encoding="utf-8")]
    res, rows = {}, []
    for c in cases:
        if a.split != "all" and c["split"] != a.split:
            continue
        r = route(c["question"])
        pids = [t.procedure_id for t in r.tasks if t.route == "direct"]
        e = c["expected"]
        if e["behavior"] == "clarify":
            ok = r.behavior == "clarify"
        else:
            ok = r.behavior == "answer"
        top = bool(pids) and pids[0] in e.get("acceptable", [])
        rows.append({"id": c["id"], "split": c["split"], "kind": c["kind"], "sub": c["sub"], "q": c["question"], "behavior": r.behavior, "ok": ok, "top1": top if e["behavior"] == "answer" else None,
                     "pids": pids, "options": [o["proc_id"] for o in (r.clarify or {}).get("options", [])]})
        if a.v and not ok:
            print("MISS", c["id"], c["sub"], c["question"], "->", r.behavior, [t.procedure_label[:40] for t in r.tasks])
    out = {}
    for sp in ("tune", "held", "fresh"):
        cl = [x for x in rows if x["split"] == sp and x["kind"] == "clarify"]
        an = [x for x in rows if x["split"] == sp and x["kind"] == "answer"]
        if not cl and not an:
            continue
        out[sp] = {"clarify_recall": [sum(x["ok"] for x in cl), len(cl)], "over_clarify": [sum(x["behavior"] == "clarify" for x in an), len(an)],
                   "answer_top1": [sum(bool(x["top1"]) for x in an), len(an)]}
        print(sp, "clarify recall %d/%d   over-clarify %d/%d   answer top-1 %d/%d" % (*out[sp]["clarify_recall"], *out[sp]["over_clarify"], *out[sp]["answer_top1"]))
    sub = {}
    for x in rows:
        s = sub.setdefault(x["sub"], [0, 0]); s[0] += x["ok"]; s[1] += 1
    print("theo nhóm (đúng hành vi):", {k: f"{v[0]}/{v[1]}" for k, v in sub.items()})
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump({"summary": out, "rows": rows}, open(os.path.join(HERE, "results", a.name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

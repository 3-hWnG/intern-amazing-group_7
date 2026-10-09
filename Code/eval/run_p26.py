"""Phase 26: đo bộ nhớ người dùng trên eval/cases_p26.jsonl (dựng bằng build_p26.py). Không LLM, không bộ mù.
Mỗi ca chạy pre_check -> Planner (luật) -> Policy.check hai lần: KHÔNG hồ sơ (memory=None = hành vi cũ) và CÓ hồ sơ của ca.
Nhóm: a hồ sơ khớp -> không hỏi lại (pick) hoặc thẻ gọn hơn (shrink); b cùng câu không hồ sơ -> hỏi lại như cũ;
      c hồ sơ sai đối tượng / câu nêu rõ thủ tục -> vẫn đúng thủ tục theo câu; d hồ sơ rỗng -> y hệt cũ (so cả Routed).
Chạy: PYTHONPATH=<ROOT> S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1 python run_p26.py [-v] [--name p26]"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(HERE, "..", "server")]   # Phase 28: không giả định thư mục tên system3
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from system3.data import api  # noqa: E402
import user_memory  # noqa: E402

conn = api.connect()


def route(question, profile):
    pc = pre_check(question)
    mem = user_memory.policy_memory({"user_type": profile.get("user_type", "")}, {"subject": profile["mcq_subject"]} if profile.get("mcq_subject") else {})
    p = make_plan([{"role": "user", "text": pc["text"]}])
    return check(p, user_text=pc["text"], conn=conn, flags=pc["flags"], memory=mem)


def view(r):
    return {"behavior": r.behavior, "pids": [t.procedure_id for t in r.tasks if t.route == "direct"],
            "options": [o["proc_id"] for o in (r.clarify or {}).get("options", [])], "note": (r.memory_note or {}).get("kind", "")}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-v", action="store_true"); ap.add_argument("--name", default="p26")
    a = ap.parse_args()
    cases = [json.loads(l) for l in open(os.path.join(HERE, "cases_p26.jsonl"), encoding="utf-8")]
    rows, bad = [], []
    for c in cases:
        base, got = route(c["question"], {}), route(c["question"], c["profile"])
        b, g, e = view(base), view(got), c["expected"]
        ok = True
        if c["group"] == "a":      # hồ sơ khớp: pick = trả đúng thủ tục không hỏi lại; shrink = thẻ gọn hơn mà vẫn còn thủ tục đúng
            if e["note"] == "pick":
                ok = b["behavior"] == "clarify" and g["behavior"] == "answer" and g["pids"][:1] and g["pids"][0] in e["acceptable"] and g["note"] == "pick"
            else:
                ok = b["behavior"] == "clarify" and g["behavior"] == "clarify" and len(g["options"]) <= len(b["options"]) and bool(set(g["options"]) & set(e["acceptable"])) and g["note"] == "shrink"
        elif c["group"] == "b":    # không hồ sơ: hỏi lại như cũ (đây chính là hành vi cũ)
            ok = g == b and b["behavior"] == "clarify"
        elif c["group"] == "c":    # hồ sơ sai/lạc: đúng thủ tục theo câu, hồ sơ không can thiệp
            ok = g["behavior"] == e["behavior"] and g["note"] == "" and g == b
            if e["behavior"] == "answer":
                ok = ok and bool(g["pids"][:1]) and g["pids"][0] in e["acceptable"]
            elif e["behavior"] == "clarify" and e["acceptable"]:
                ok = ok and bool(set(e["acceptable"]) & set(g["options"]))
        elif c["group"] == "d":    # hồ sơ rỗng: y hệt cũ, so cả Routed
            ok = got.to_dict() == base.to_dict()
        rows.append({"id": c["id"], "group": c["group"], "ok": bool(ok), "base": b, "got": g})
        if not ok:
            bad.append(rows[-1])
        if a.v or not ok:
            print(("PASS " if ok else "FAIL ") + c["id"], c["question"][:70], "| base", b, "| got", g)
    n = lambda g: [r for r in rows if r["group"] == g]
    print("\n| nhóm | ca | đạt |\n|---|---|---|")
    for g, name in [("a", "a hồ sơ khớp, câu mơ hồ"), ("b", "b cùng câu, không hồ sơ"), ("c", "c hồ sơ sai/lạc"), ("d", "d hồ sơ rỗng")]:
        print(f"| {name} | {len(n(g))} | {sum(r['ok'] for r in n(g))} |")
    ca = [r for r in rows if r["group"] == "a"]
    ask_base = sum(r["base"]["behavior"] == "clarify" for r in ca)
    ask_got = sum(r["got"]["behavior"] == "clarify" for r in ca)
    pick = [r for r in ca if r["got"]["note"] == "pick"]
    shr = [r for r in ca if r["got"]["note"] == "shrink"]
    smaller = sum(len(r["got"]["options"]) < len(r["base"]["options"]) for r in shr)
    print(f"\nNhóm a ({len(ca)} ca): hỏi lại không hồ sơ {ask_base}/{len(ca)} -> có hồ sơ {ask_got}/{len(ca)} (bỏ hỏi {ask_base - ask_got}); "
          f"shrink {len(shr)} ca ({smaller} thẻ nhỏ hơn, {len(shr) - smaller} cùng cỡ nhưng đổi sang ứng viên hợp): số nút TB {sum(len(r['base']['options']) for r in shr) / max(1, len(shr)):.1f} -> {sum(len(r['got']['options']) for r in shr) / max(1, len(shr)):.1f}")
    print(f"TỔNG đạt {sum(r['ok'] for r in rows)}/{len(rows)}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump({"rows": rows, "summary": {"n": len(rows), "ok": sum(r["ok"] for r in rows), "a_clarify_base": ask_base, "a_clarify_with_profile": ask_got,
                                         "pick": len(pick), "shrink": len(shr)}}, open(os.path.join(HERE, "results", a.name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()

"""Phase 19: bảng so sánh rules vs hybrid từ results/<tag>.json (run.py), <tag>_ctx.json (run_ctx.py), <tag>_concise.json (run_concise.py).
python p19_compare.py --rules p19_rules --hyb p19_h080,p19_h090,...      Chỉ đọc kết quả DEV + ctx + HOLDOUT cũ (không đụng bộ nghiệm thu)."""
import argparse, json, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
OLD_EXCL = ("p16", "p18", "p19", "p23")


def load(name):
    p = os.path.join(HERE, "results", name + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else None


def rate(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs), len(xs)) if xs else (None, 0)


def pc(r):
    return "-" if r[0] is None else f"{100 * r[0]:.1f}%"


def ok(c):
    return c["top1"] is not False and c["behavior_ok"] and c["fields_ok"] is not False and not c["fab"]


def lat(c):
    l = (c.get("extra") or {}).get("llm") or {}
    return (c["latency_ms"] or 0) + (l.get("ms", 0) if l.get("cached") else 0)      # phát lại từ cache: cộng độ trễ LLM đã đo lúc gọi thật


def pctl(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else 0


def split_sets(d):
    cs = d["cases"]
    dev = [c for c in cs if c["split"] == "dev"]
    old = [c for c in dev if not c["id"].startswith(OLD_EXCL)]
    return {"DEV cũ": old, "DEV (cả p16/p18/p19)": dev, "HOLDOUT cũ": [c for c in cs if c["split"] == "holdout"]}


def row(label, cs):
    t1, b, f, fab = (rate([c[k] for c in cs]) for k in ("top1", "behavior_ok", "fields_ok", "fab"))
    mi = rate([c["top1"] for c in cs if c["category"] == "multi_intent"])
    oos = [c for c in cs if c["category"] == "out_of_scope"]
    L = [lat(c) for c in cs]
    llm = [(c.get("extra") or {}).get("llm") or {} for c in cs]
    called = [l for l in llm if l.get("called")]
    return (f"| {label} | {len(cs)} | {pc(t1)} ({int(round(t1[0] * t1[1])) if t1[0] is not None else 0}/{t1[1]}) | {pc(b)} | {pc(f)} | {pc(fab)} | {pc(mi)} | "
            f"{sum(c['behavior_ok'] for c in oos)}/{len(oos)} | {pctl(L, .5):.0f} | {pctl(L, .95):.0f} | "
            f"{(sum(1 for l in called if l.get('timeout')) / len(called) * 100 if called else 0):.1f}% |")


def ops(r_cs, h_cs):
    """Đề xuất của LLM vs đáp án: đối chiếu từng ca với bản rules cùng id."""
    R = {c["id"]: c for c in r_cs}
    st = dict(prop_cases=0, prop=0, acc_ops=0, acc_cases=0, right=0, wrong=0, same=0, rej_would_help=0)
    for c in h_cs:
        l = (c.get("extra") or {}).get("llm") or {}
        o = l.get("proposals") or []
        if not o:
            continue
        st["prop_cases"] += 1
        st["prop"] += len(o)
        a = [x for x in o if x["accepted"]]
        r = R.get(c["id"])
        if r is None:
            continue
        if not a:
            continue
        st["acc_ops"] += len(a)
        st["acc_cases"] += 1
        a_ok, r_ok = ok(c), ok(r)
        st["right" if a_ok and not r_ok else "wrong" if r_ok and not a_ok else "same"] += 1
    return st


def ctx_row(label, d):
    cs = d["cases"] if d else []
    if not cs:
        return f"| {label} | - |"
    fs = [c["fields_ok"] for c in cs if c["fields_ok"] is not None]
    return f"| {label} | {sum(c['ok'] for c in cs)}/{len(cs)} | {sum(fs)}/{len(fs)} |"


def concise_rows(d):
    out = {}
    for line in (d or {}).get("table_md", "").splitlines():
        p = [x.strip() for x in line.strip("|").split("|")]
        if len(p) >= 3 and p[0] in ("DEV", "ctx", "HOLDOUT cũ"):
            out[p[0]] = (p[2], p[3])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="p19_rules")
    ap.add_argument("--hyb", default="")
    a = ap.parse_args()
    tags = [("rules", a.rules)] + [(t.replace("p19_", ""), t) for t in a.hyb.split(",") if t]
    wrap = lambda x: {"cases": x} if isinstance(x, list) else x
    runs = {lab: (load(t), wrap(load(t + "_ctx")), load(t + "_concise")) for lab, t in tags}
    print("## run.py (answer_adapter)\n")
    print("| cấu hình | n | top-1 | hành vi | fields | bịa số | multi-intent top-1 | OOS hành vi | p50 ms | p95 ms | timeout LLM |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for sp in ("DEV cũ", "DEV (cả p16/p18/p19)", "HOLDOUT cũ"):
        for lab, _ in tags:
            d = runs[lab][0]
            if d:
                print(row(f"{sp} / {lab}", split_sets(d)[sp]))
    print("\n## ctx (lượt cuối) | focus (run_concise)\n")
    print("| cấu hình | ctx top-1 | ctx fields | focus DEV | task thừa DEV | focus ctx | focus HOLDOUT cũ |\n|---|---|---|---|---|---|---|")
    for lab, _ in tags:
        _, c, k = runs[lab]
        cr = concise_rows(k)
        fs = [x["fields_ok"] for x in (c or {"cases": []})["cases"] if x["fields_ok"] is not None]
        print(f"| {lab} | {sum(x['ok'] for x in c['cases'])}/{len(c['cases'])} | {sum(fs)}/{len(fs)} | " + " | ".join(
            (cr.get(k2, ('-', '-'))[0] if i != 1 else cr.get(k2, ('-', '-'))[1]) for i, k2 in enumerate(("DEV", "DEV", "ctx", "HOLDOUT cũ"))) + " |" if c else f"| {lab} | - |")
    print("\n## đề xuất của LLM (so với bản rules cùng ca; ok = top-1 + hành vi + fields + không bịa)\n")
    print("| cấu hình | bộ | ca có đề xuất | đề xuất | đề xuất được nhận | ca được nhận | nhận -> đúng hơn | nhận -> sai đi | nhận -> không đổi |\n|---|---|---|---|---|---|---|---|---|")
    r = runs["rules"][0]
    for lab, _ in tags[1:]:
        h = runs[lab][0]
        if not (h and r):
            continue
        for sp in ("DEV cũ", "DEV (cả p16/p18/p19)"):
            s = ops(split_sets(r)[sp], split_sets(h)[sp])
            print(f"| {lab} | {sp} | {s['prop_cases']} | {s['prop']} | {s['acc_ops']} | {s['acc_cases']} | {s['right']} | {s['wrong']} | {s['same']} |")
        rc, hc = runs["rules"][1], runs[lab][1]
        if rc and hc:
            R = {c["id"]: c for c in rc["cases"]}
            acc = [c for c in hc["cases"] if any(o["accepted"] for o in ((c.get("llm") or {}).get("proposals") or []))]
            print(f"| {lab} | ctx | - | - | - | {len(acc)} | {sum(1 for c in acc if c['ok'] and not R[c['id']]['ok'])} | {sum(1 for c in acc if R[c['id']]['ok'] and not c['ok'])} | - |")


if __name__ == "__main__":
    main()

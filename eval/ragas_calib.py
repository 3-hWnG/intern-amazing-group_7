"""Hiệu chuẩn giám khảo RAGAS-lite (chế độ ít chấm tay, MERGE_PLAN C3b-C3d).
  python eval/ragas_calib.py export --name x [--k 30]   -> results/ragas_calib_x.json: k ca phân tầng theo nguồn, kèm điểm giám khảo, để chấm
  python eval/ragas_calib.py kappa  --name x --ratings results/ragas_calib_llm_x.json [--human results/ragas_calib_human_x.json]
Tệp chấm: {id: {"faithful": 0|1, "rel": 0|1|2}}. faithful = mọi ý của câu trả lời đều có trong ngữ cảnh.
So sánh nhị phân: giám khảo faith >= 0.8 <-> faithful; giám khảo rel >= 0.5 <-> rel >= 1. In Cohen's kappa và các ca bất đồng (để người chấm lại)."""
import argparse, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=("export", "kappa"))
ap.add_argument("--name", required=True)
ap.add_argument("--k", type=int, default=30)
ap.add_argument("--ratings")
ap.add_argument("--human")
a = ap.parse_args()
load = lambda p: json.load(open(p if os.path.isabs(p) or os.path.exists(p) else os.path.join(HERE, p), encoding="utf-8"))


def kappa(x, y):
    n = len(x)
    if not n:
        return None
    po = sum(i == j for i, j in zip(x, y)) / n
    pe = sum((x.count(v) / n) * (y.count(v) / n) for v in set(x) | set(y))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


if a.cmd == "export":
    ds = {c["id"]: c for c in load(os.path.join(R, f"ragas_dataset_{a.name}.json"))["cases"]}
    sc = {r["id"]: r for r in load(os.path.join(R, f"ragas_lite_{a.name}.json"))["rows"]}
    by = {}
    for i in sc:
        by.setdefault(sc[i]["src"], []).append(i)
    rng, pick = random.Random(7), []
    per = max(1, a.k // len(by))
    for src in sorted(by):
        pick += rng.sample(by[src], min(per, len(by[src])))
    rest = [i for i in sc if i not in pick]
    pick += rng.sample(rest, min(a.k - len(pick), len(rest)))
    out = [dict(id=i, src=sc[i]["src"], q=ds[i]["q"], ans=ds[i]["ans"], ctx="\n---\n".join(ds[i]["ctx_chunks"])[:3500],
                judge_faith=sc[i]["faith"], judge_rel=sc[i]["rel"]) for i in pick]
    json.dump(out, open(os.path.join(R, f"ragas_calib_{a.name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ghi results/ragas_calib_{a.name}.json: {len(out)} ca")
else:
    cal = {c["id"]: c for c in load(os.path.join(R, f"ragas_calib_{a.name}.json"))}
    for label, path in (("LLM", a.ratings), ("người", a.human)):
        if not path:
            continue
        rt = load(path)
        ids = [i for i in cal if i in rt and cal[i]["judge_faith"] is not None]
        jf = [int(cal[i]["judge_faith"] >= 0.8) for i in ids]
        rf = [int(rt[i]["faithful"]) for i in ids]
        ids2 = [i for i in cal if i in rt and cal[i]["judge_rel"] is not None]
        jr = [int(cal[i]["judge_rel"] >= 0.5) for i in ids2]
        rr = [int(rt[i]["rel"] >= 1) for i in ids2]
        kf, kr = kappa(jf, rf), kappa(jr, rr)
        print(f"[{label}] faithfulness: n={len(ids)}, đồng ý {sum(x == y for x, y in zip(jf, rf))}/{len(ids)}, kappa={kf if kf is None else round(kf, 2)}")
        print(f"[{label}] relevancy:    n={len(ids2)}, đồng ý {sum(x == y for x, y in zip(jr, rr))}/{len(ids2)}, kappa={kr if kr is None else round(kr, 2)}")
        dis = [i for i, x, y in zip(ids, jf, rf) if x != y] + [i for i, x, y in zip(ids2, jr, rr) if x != y]
        print(f"[{label}] ca bất đồng (cần người chấm lại, tối đa ~15): {sorted(set(dis))}")

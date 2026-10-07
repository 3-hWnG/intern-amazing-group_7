"""Phase 28: so baseline V10.6 chạy lại (results/v106_rerun.json, từ run.py --adapter baseline_adapter:adapter --name v106_rerun --split dev)
với results/baseline.json (185 câu gốc, số lịch sử). In top-1/top-3/hành vi trên 185 id chung và trên DEV cũ 209. Không dùng bộ mù."""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__))
L = lambda n: json.load(open(os.path.join(H, "results", n + ".json"), encoding="utf-8"))
OLD_EXCL = ("p16", "p18", "p19", "p23")


def rate(cs, k):
    xs = [c[k] for c in cs if c[k] is not None]
    return (sum(map(bool, xs)), len(xs))


def pct(t):
    return f"{100 * t[0] / t[1]:.1f}% ({t[0]}/{t[1]})" if t[1] else "-"


def main():
    old, new = L("baseline")["cases"], L("v106_rerun")["cases"]
    nid = {c["id"]: c for c in new}
    common = [c["id"] for c in old if c["id"] in nid]
    o = [c for c in old if c["id"] in nid]
    n = [nid[i] for i in common]
    d209 = [c for c in new if not c["id"].startswith(OLD_EXCL) and c["split"] == "dev"]
    print(f"| tập | n | top-1 | top-3 | hành vi |\n|---|---|---|---|---|")
    worst = 0
    for lab, cs in (("baseline.json (cũ), 185 id chung", o), ("chạy lại, 185 id chung", n), ("chạy lại, DEV cũ 209", d209), ("chạy lại, DEV gộp", [c for c in new if c["split"] == "dev"])):
        print(f"| {lab} | {len(cs)} | {pct(rate(cs, 'top1'))} | {pct(rate(cs, 'top3'))} | {pct(rate(cs, 'behavior_ok'))} |")
    for k in ("top1", "top3", "behavior_ok"):
        a, b = rate(o, k), rate(n, k)
        worst = max(worst, abs(100 * a[0] / a[1] - 100 * b[0] / b[1]))
    diff = [i for i in common if any(bool(next(c for c in o if c["id"] == i)[k]) != bool(nid[i][k]) for k in ("top1", "behavior_ok"))]
    print(f"ca khác kết quả top1/hành vi: {len(diff)}/{len(common)} {diff[:10]}; lệch lớn nhất {worst:.2f} điểm % (ngưỡng 2)")
    return 0 if worst <= 2 else 1


if __name__ == "__main__":
    sys.exit(main())

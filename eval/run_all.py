"""Phase 28: một lệnh dựng DB + chạy mọi gate GPU-free + in bảng số kèm ngưỡng.
    python run_server.py eval/run_all.py [--quick] [--skip-build] [--only tên,tên] [--with-blind]
(chạy ở thư mục gốc system3; thư mục tên gì cũng được, không cần PYTHONPATH). Ép S3_USE_LLM=0 S3_PLANNER_MODE=rules S3_NO_WARMUP=1: không GPU, không Ollama.
--quick bỏ synth + perturb (phần chậm). --with-blind CHỈ cho người điều phối: chạy thêm run_pseudo.py/run_team.py (bộ mù/team), mặc định TẮT;
script này không mở file ca hay kết quả của các bộ đó. Exit 0 = mọi gate đạt."""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL, RES = ROOT / "eval", ROOT / "eval" / "results"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", S3_USE_LLM="0", S3_PLANNER_MODE="rules", S3_NO_WARMUP="1")
OLD_EXCL = re.compile(r"p(16|18|19|23)")
rows, fails = [], []          # rows: (nhóm, số đo, kết quả, ngưỡng, đạt?)


def sh(args, timeout=1800):
    """Chạy `python run_server.py <args>` ở gốc; trả (exit, stdout+stderr)."""
    p = subprocess.run([sys.executable, "run_server.py", *args], cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def J(name):
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def add(group, label, got, thr, ok):
    rows.append((group, label, got, thr, ok))
    if not ok:
        fails.append(f"{group}: {label}")


def pc(a, b):
    return f"{100 * a / b:.1f}% ({a}/{b})" if b else "-"


def step_cmd(group, label, args, thr="exit 0"):
    t0 = time.time()
    code, out = sh(args)
    add(group, label, f"exit {code} ({time.time() - t0:.0f}s)", thr, code == 0)
    if code:
        print(f"--- {label} lỗi, 20 dòng cuối:\n" + "\n".join(out.strip().splitlines()[-20:]), file=sys.stderr)
    return out


def guard(name, fn):
    try:
        fn()
    except Exception as e:      # một bước hỏng (thiếu file kết quả...) không chặn các bước sau
        add(name, "bước không hoàn tất", f"{type(e).__name__}: {str(e)[:80]}", "-", False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="bỏ synth + perturb")
    ap.add_argument("--skip-build", action="store_true", help="không dựng lại DB (dùng DB có sẵn)")
    ap.add_argument("--with-blind", action="store_true", help="CHỈ người điều phối: chạy thêm bộ mù/team (mặc định tắt)")
    ap.add_argument("--only", default="", help="chỉ chạy các nhóm: build,tests,dev,ctx,concise,p26,synth,perturb,baseline,docs")
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    want = lambda k: not only or k in only
    t00 = time.time()
    sys.stdout.reconfigure(encoding="utf-8")   # bảng có tiếng Việt, console Windows mặc định cp1252

    def blk_build():
        step_cmd("dựng", "data DB (system3.data.build)", ["-m", "system3.data.build"])
        step_cmd("dựng", "DB V10.6 (rebuild_v106_db --force)", ["eval/rebuild_v106_db.py", "--force"])
    def blk_tests():
        step_cmd("test", "test_data", ["-m", "system3.data.tests.test_data"])
        for t in ("memory_test", "context_test", "answer_llm_test", "planner_hybrid_test", "p20_api_test", "p23_input_test", "p26_memory_test"):
            step_cmd("test", f"server/tests/{t}", [f"server/tests/{t}.py"])
        step_cmd("test", "server/smoke_test", ["server/smoke_test.py"])
        step_cmd("test", "eval/selftest", ["eval/selftest.py"])
    def blk_dev():
        step_cmd("DEV", "run.py answer_adapter --split all", ["eval/run.py", "--adapter", "answer_adapter:adapter", "--name", "ra_dev", "--split", "all"])
        d = J("ra_dev")["cases"]
        old = [r for r in d if r["split"] == "dev" and not OLD_EXCL.match(r["id"])]
        rate = lambda k: [r[k] for r in old if r[k] is not None]
        t1, bh, fb = rate("top1"), rate("behavior_ok"), rate("fab")
        add("DEV cũ", f"top-1 ({len(old)} ca)", pc(sum(t1), len(t1)), ">= 95%", sum(t1) / len(t1) >= .95)
        add("DEV cũ", "đúng hành vi", pc(sum(bh), len(bh)), ">= 96%", sum(bh) / len(bh) >= .96)
        add("DEV cũ", "bịa số", pc(sum(fb), len(fb)), "<= 3%", sum(fb) / len(fb) <= .03)
        oos = [r for r in old if r["category"] == "out_of_scope"]
        k = sum(r["behavior_ok"] for r in oos)
        add("DEV cũ", "ngoài phạm vi", f"{k}/{len(oos)}", "30/30", (k, len(oos)) == (30, 30))
        dv = [r for r in d if r["split"] == "dev"]
        add("DEV gộp", f"top-1 ({len(dv)} ca), tham khảo", pc(sum(bool(r['top1']) for r in dv if r['top1'] is not None), sum(r['top1'] is not None for r in dv)), "-", True)
        ho = [r for r in d if r["split"] == "holdout"]
        add("HOLDOUT cũ", f"top-1 ({len(ho)} ca), tham khảo", pc(sum(bool(r['top1']) for r in ho if r['top1'] is not None), sum(r['top1'] is not None for r in ho)), "-", True)
    def blk_ctx():
        step_cmd("ctx", "run_ctx.py", ["eval/run_ctx.py", "--name", "ra_ctx"])
        r = J("ra_ctx")
        k = sum(x["ok"] for x in r)
        add("ctx", "ctx-dev + ctx-hold", f"{k}/{len(r)}", ">= 89/91", len(r) == 91 and k >= 89)
        step_cmd("ctx", "run_ctx.py --split ctx-p23", ["eval/run_ctx.py", "--name", "ra_ctx_p23", "--split", "ctx-p23"])
        r = J("ra_ctx_p23")
        k = sum(x["ok"] for x in r)
        add("ctx", "ctx-p23", f"{k}/{len(r)}", "26/26", (k, len(r)) == (26, 26))
    def blk_concise():
        step_cmd("focus", "run_concise.py --no-blind", ["eval/run_concise.py", "--name", "ra_concise", "--no-blind"])
        m = re.search(r"\| DEV \| (\d+) \| (\d+)% \((\d+)/(\d+)\) \| (\d+)/(\d+) \|", J("ra_concise")["table_md"])
        if m:
            f, n, x, tot = int(m[3]), int(m[4]), int(m[5]), int(m[6])
            add("focus", "DEV focus", pc(f, n), ">= 95%", f / n >= .95)
            add("focus", "DEV task thừa", f"{x}/{tot}", "<= 2%", x / tot <= .02)
        else:
            add("focus", "DEV focus", "không đọc được bảng", ">= 95%", False)
    def blk_p26():
        step_cmd("p26", "run_p26.py", ["eval/run_p26.py", "--name", "ra_p26"])
        s = J("ra_p26")["summary"]
        add("p26", "bộ nhớ người dùng", f"{s['ok']}/{s['n']}", "tất cả đạt", s["ok"] == s["n"])
    def blk_synth():
        t0 = time.time()
        code, out = sh(["eval/synth_retrieval.py"])
        (RES / "synth.txt").write_text(out, encoding="utf-8")
        tr, te = re.search(r"\[train\].*?top1=([\d.]+)%", out), re.search(r"\[test\].*?top1=([\d.]+)%", out)
        gl = re.search(r"\[glued\] test: ([\d.]+)%", out)
        add("synth", "TEST-seed top-1", f"{te[1]}%" if te else "?", ">= 94%", bool(te) and float(te[1]) >= 94)
        add("synth", "TRAIN-seed top-1 (chênh TEST <= 5đ)", f"{tr[1]}%" if tr else "?", "-", bool(tr and te) and abs(float(tr[1]) - float(te[1])) <= 5)
        add("synth", "glued TEST", f"{gl[1]}%" if gl else "?", ">= 90%", bool(gl) and float(gl[1]) >= 90)
        add("synth", f"chạy ({time.time() - t0:.0f}s)", f"exit {code}", "exit 0", code == 0)
    def blk_perturb():
        step_cmd("perturb", "perturb.py", ["eval/perturb.py", "--name", "ra"])
        r = J("perturb_ra")
        n = sum(v[1] for v in r["by"].values())
        add("perturb", "bất biến", f"{r['rate']:.2f}% ({sum(v[0] for v in r['by'].values())}/{n})", ">= 98%", r["rate"] >= 98)
    def blk_baseline():
        step_cmd("baseline V10.6", "run.py baseline_adapter --split dev", ["eval/run.py", "--adapter", "baseline_adapter:adapter", "--name", "v106_rerun", "--split", "dev"])
        code, out = sh(["eval/p28_baseline_cmp.py"])
        m = re.search(r"lệch lớn nhất ([\d.]+) điểm", out)
        add("baseline V10.6", "lệch top-1/top-3/hành vi so baseline.json (185 id)", f"{m[1]} điểm %" if m else "?", "<= 2 điểm %", code == 0)
        print(out)
    def blk_blind():
        print("[with-blind] chạy bộ mù/team (chỉ người điều phối) — không đọc kết quả, chỉ chạy script", file=sys.stderr)
        for s in ("run_pseudo.py", "run_team.py"):
            step_cmd("mù/team", s, [f"eval/{s}"], "chạy được (số: xem script)")
    def blk_docs():
        step_cmd("docs", "check_docs.py", ["eval/check_docs.py"], "sạch")

    if want("build") and not a.skip_build:
        guard("build", blk_build)
    for k, f in (("tests", blk_tests), ("dev", blk_dev), ("ctx", blk_ctx), ("concise", blk_concise), ("p26", blk_p26)):
        if want(k):
            guard(k, f)
    if want("synth") and not a.quick:
        guard("synth", blk_synth)
    if want("perturb") and not a.quick:
        guard("perturb", blk_perturb)
    if want("baseline"):
        guard("baseline", blk_baseline)
    if a.with_blind:
        guard("blind", blk_blind)
    if want("docs"):
        guard("docs", blk_docs)

    print("\n| nhóm | số đo | kết quả | ngưỡng | |\n|---|---|---|---|---|")
    for g, l, got, thr, ok in rows:
        print(f"| {g} | {l} | {got} | {thr} | {'ĐẠT' if ok else 'TRƯỢT'} |")
    print(f"\n{len(rows) - len(fails)}/{len(rows)} đạt, {time.time() - t00:.0f}s." + ("" if not fails else "\nTRƯỢT: " + "; ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

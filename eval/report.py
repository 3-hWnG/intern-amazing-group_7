"""Mục 3.6 của kế hoạch: báo cáo số liệu MỘT lệnh (các bảng A-D trong docs/PLAN_TUAN_TOI.md).
Chạy (thư mục gốc):  PYTHONIOENCODING=utf-8 python eval/report.py [--llm] [--out eval/results/report.md]
  mặc định: chạy `S3_USE_LLM=0` (không cần GPU): golden set theo status và bộ gốc, bộ khuôn theo chủ đề, tốc độ CPU. ~2 phút.
  --llm   : thêm cột tốc độ khi bật LLM (cần Ollama chạy và model đã kéo về; ~3 phút).
Bảng E (dữ liệu đúng nguồn) cần người điền phiếu: `python eval/sample_dataset_check.py --score <file>`.
Ghi bảng ra --out (mặc định eval/results/report.md; thư mục results bị .gitignore, dán vào docs khi cần)."""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
ap = argparse.ArgumentParser()
ap.add_argument("--llm", action="store_true")
ap.add_argument("--out", default=os.path.join(HERE, "results", "report.md"))
a = ap.parse_args()
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "S3_USE_LLM": "0"}


def run(*cmd, e=env):
    r = subprocess.run([PY, "run_server.py", *cmd], cwd=ROOT, env=e, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"lỗi khi chạy {' '.join(cmd)}:\n{r.stderr[-800:]}")
    return r.stdout.strip()


t0 = time.time()
out = [f"# Báo cáo evaluation System 3 ({time.strftime('%Y-%m-%d %H:%M')})", "",
       "Planner luật, `S3_USE_LLM=0` (trừ cột tốc độ có LLM). Số chính thức là hàng `blind`; `dev` đã tune nên luôn cao hơn.", ""]
for title, args in (("A. Golden set Thủ tục theo status", ("eval/run_golden.py", "thu-tuc", "--by", "status")),
                    ("B. Golden set Thủ tục theo bộ gốc", ("eval/run_golden.py", "thu-tuc", "--by", "source"))):
    print(title, flush=True)
    out += [f"## {title}", "", run(*args), ""]
print("C. khuôn câu hỏi", flush=True)
run("eval/build_template_set.py")
out += ["## C. Bộ khuôn câu hỏi theo chủ đề (dễ hơn câu thật, dùng để so chủ đề và bắt hồi quy)", "",
        run("eval/run_golden.py", "template_thu-tuc", "--by", "type"), ""]

lat = {}
for llm in ((0, 1) if a.llm else (0,)):
    print(f"D. tốc độ llm={llm}", flush=True)
    run("eval/measure_latency.py", "--llm", str(llm), "--name", "report", e={k: v for k, v in env.items() if llm == 0 or k != "S3_USE_LLM"})
    lat[llm] = json.load(open(os.path.join(HERE, "results", f"latency_report_llm{llm}.json"), encoding="utf-8"))
kinds = [k for k in ("simple", "complex", "clarify", "out", "llm") if any(k in v for v in lat.values())]
names = {"simple": "đơn giản", "complex": "phức tạp (nhiều ý hoặc nhiều lượt)", "clarify": "hỏi lại", "out": "ngoài phạm vi", "llm": "có bước sinh chữ bằng LLM"}
f = lambda v, k: f"{v[k]['p50']} / {v[k]['p95']}" if k in v else "-"
hdr = "| Loại câu | LLM tắt (CPU), p50 / p95 ms |" + (" LLM bật, p50 / p95 ms |" if a.llm else "")
out += ["## D. Tốc độ", "", hdr, "|---|---|" + ("---|" if a.llm else "")]
out += [f"| {names[k]} | {f(lat[0], k)} |" + (f" {f(lat[1], k)} |" if a.llm else "") for k in kinds]
out += ["", f"(mỗi loại tối đa 30 câu, mẫu cố định theo seed; tổng thời gian chạy báo cáo {time.time() - t0:.0f} s)", ""]
text = "\n".join(out)
os.makedirs(os.path.dirname(a.out), exist_ok=True)
open(a.out, "w", encoding="utf-8").write(text)
print("\n" + text)
print(f"\nghi {a.out}")

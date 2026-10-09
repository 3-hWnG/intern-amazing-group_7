"""NV5 — bộ đo chung cho độ chính xác, tốc độ, hành vi (System 4 Friendly / Chuyên gia) trên model THẬT.

    python system4/eval/bench.py run NAME [--set KEY=VALUE ...] [--split dev|exam|all] [--repeat N] [--suites a,b] [--no-behavior]
    python system4/eval/bench.py compare results/bench/A.json results/bench/B.json ...
    python system4/eval/bench.py swap            # thời gian Ollama đổi qua lại 2 model (Strict qwen3:4b <-> Friendly Instruct)
    python system4/eval/bench.py strict --model M --name N   # bộ đo System 3 (Strict) với model M (câu 1D)

"run" tự bật một server riêng (cổng 8399, dữ liệu riêng ở system4/eval/bench_runtime — không đụng web thật), ghi cài đặt
NAME (+ --set) vào settings.json của nó, nạp 4 bộ dữ liệu một lần (danh sách lớp GIẢ, chính sách Word, du lịch, thủ tục),
gỡ mọi model khỏi card đồ hoạ trước khi đo, hỏi thử 2 câu cho nóng máy rồi chạy bộ câu bench_cases.py + 22 tình huống
hành vi của nv2_behavior.py. Kết quả: system4/eval/results/bench/NAME.json. Chấm bằng luật, không nhờ AI chấm.
"bài thi cuối" (split exam) chỉ dùng để nghiệm thu: khi chỉnh tham số chỉ nhìn split dev.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PYROOT = REPO.parent / "pyroot"
PY = REPO / ".venv" / "Scripts" / "python.exe"
RUNTIME = HERE / "bench_runtime"
OUT_DIR = HERE / "results" / "bench"
PORT = 8399
BASE = f"http://127.0.0.1:{PORT}"
sys.path.insert(0, str(HERE))
INSTRUCT = "qwen3:4b-instruct-2507-q4_K_M"

# Cấu hình đặt tên sẵn (ghi đè cài đặt mặc định của config.py). --set thêm / sửa từng khoá.
PRESETS = {
    "today": {},
    "inst07": {"FRIENDLY_MODEL": INSTRUCT, "THINK_MODEL": "qwen3:4b", "FRIENDLY_TEMPERATURE": 0.7},
    "inst02": {"FRIENDLY_MODEL": INSTRUCT, "THINK_MODEL": "qwen3:4b", "FRIENDLY_TEMPERATURE": 0.2},
}

UNSURE = ("khong co thong tin", "khong tim thay", "khong co trong du lieu", "chua co thong tin", "khong biet", "khong ro", "khong the",
          "chua ro", "khong chac", "khong co du lieu", "khong duoc cung cap", "chua duoc cung cap", "khong co san", "lien he",
          "khong de cap", "chua co du lieu", "khong nam trong", "khong co ghi", "khong ghi", "khong co muc", "chua duoc cap nhat",
          "khong co thong tin chinh thuc", "chua the xac nhan", "khong xac dinh", "khong co ten", "chua biet", "khong nho")


def fold(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    return re.sub(r"\s+", " ", "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d"))


# ------------------------------------------------------------------ chấm
def score(check: dict, content: str, meta: dict) -> tuple[bool, list[str]]:
    """Trả (đạt, các lý do trượt). Mọi so khớp chữ: không phân biệt hoa thường / dấu."""
    f, why = fold(content), []
    titles = [s.get("title", "") for s in (meta.get("sources") or []) + (meta.get("consulted") or [])]
    if "all" in check and not all(fold(x) in f for x in check["all"]):
        why.append("thiếu: " + ", ".join(x for x in check["all"] if fold(x) not in f))
    if "any" in check and not any(fold(x) in f for x in check["any"]):
        why.append("không có ý nào trong: " + " | ".join(check["any"]))
    if "none" in check and any(fold(x) in f for x in check["none"]):
        why.append("có chữ cấm: " + ", ".join(x for x in check["none"] if fold(x) in f))
    for rx in check.get("no_regex", []):
        m = re.search(rx, content, re.I)
        if m:
            why.append(f"chi tiết bịa: {m.group()!r}")
    if check.get("refusal") and not any(p in f for p in UNSURE):
        why.append("không nói là không có / không biết")
    if check.get("source") and not any(fold(check["source"])[:50] in fold(t) or fold(t) in fold(check["source"]) for t in titles):
        why.append(f"nguồn sai (có: {titles[:3]})")
    if "ask_back" in check and bool(meta.get("choices")) != check["ask_back"]:
        why.append("không hỏi lại" if check["ask_back"] else "hỏi lại thừa")
    for x in check.get("choices_all", []):
        if not any(fold(x) in fold(c) for c in meta.get("choices") or []):
            why.append(f"thiếu lựa chọn {x}")
    if check.get("small_talk"):
        if meta.get("guard") == "Chỉ trả lời từ dữ liệu" or any(p in f for p in ("khong co trong du lieu", "khong co thong tin", "khong tim thay")):
            why.append("câu xã giao bị trả lời 'không có trong dữ liệu'")
        if meta.get("sources") or meta.get("consulted"):
            why.append("câu xã giao mà vẫn hiện nguồn")
        if meta.get("choices"):
            why.append("câu xã giao mà hỏi lại")
    return not why, why


# ------------------------------------------------------------------ server riêng
def unload_models():
    """Gỡ mọi model Ollama khỏi card đồ hoạ (giữa các cấu hình, để cấu hình trước không làm sai số đo)."""
    try:
        import ollama
        for m in ollama.Client().ps().models:
            subprocess.run(["ollama", "stop", m.model], capture_output=True, timeout=60)
    except Exception as e:
        print("  (không gỡ được model:", e, ")")


def start_server(settings: dict, log_name: str) -> subprocess.Popen:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "settings.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(PYROOT), PYTHONIOENCODING="utf-8", S4_ENABLED="1", S3_USE_LLM="0", APP_PORT=str(PORT),
               S4_RUNTIME_DIR=str(RUNTIME), S3_DB_PATH=str(RUNTIME / "s3.db"),
               LLM_MODEL=settings.get("FRIENDLY_MODEL", "qwen3:4b"))   # System 3 nạp sẵn model này lúc khởi động: dùng chung, khỏi chiếm thêm
    log = open(RUNTIME / f"server_{log_name}.log", "w", encoding="utf-8")
    p = subprocess.Popen([str(PY), "main.py"], cwd=REPO / "server", env=env, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(180):
        try:
            if httpx.get(BASE + "/health", timeout=2).status_code == 200:
                return p
        except httpx.HTTPError:
            pass
        if p.poll() is not None:
            raise SystemExit(f"server không chạy được, xem {log.name}")
        time.sleep(1)
    p.kill()
    raise SystemExit("server không lên sau 180 giây")


def stop_server(p: subprocess.Popen):
    p.terminate()
    try:
        p.wait(20)
    except subprocess.TimeoutExpired:
        p.kill()


class Client:
    def __init__(self):
        self.c = httpx.Client(base_url=BASE, timeout=600)
        cred = {"username": "bench", "password": "matkhau123"}
        if self.c.post("/s4/auth/login", json=cred).status_code != 200:
            assert self.c.post("/s4/auth/signup", json=cred).status_code == 200, "không tạo được tài khoản bench"
        self.ds = {}

    def ensure_datasets(self):
        """Nạp 4 bộ dữ liệu một lần cho bench_runtime (lần sau dùng lại; đổi bộ đọc tệp thì server tự xử lý lại)."""
        files = {"class": HERE / "data" / "ds_lop_gia.xlsx", "tourism": HERE / "data" / "tourism_records.xlsx",
                 "procedures": HERE / "data" / "MAU_100_THU_TUC.xlsx", "policy": policy_docx()}
        have = {d["filename"]: d for d in self.c.get("/s4/datasets").json()["datasets"]}
        for key, path in files.items():
            if path.name not in have:
                with open(path, "rb") as f:
                    r = self.c.post("/s4/datasets", files={"file": (path.name, f)})
                assert r.status_code == 200, r.text
                print(f"  nạp {path.name}…")
        while True:
            ds = {d["filename"]: d for d in self.c.get("/s4/datasets").json()["datasets"]}
            pending = [n for n in (p.name for p in files.values()) if ds[n]["status"] not in ("ready", "error")]
            if not pending:
                break
            time.sleep(2)
        for key, path in files.items():
            d = ds[path.name]
            assert d["status"] == "ready", f"{path.name}: {d['message']}"
            self.ds[key] = d
        self.active = {k for k, d in self.ds.items() if d["active"]}

    def use(self, keys: list[str]):
        for k, d in self.ds.items():
            want = k in keys
            if want != (k in self.active):
                r = self.c.patch(f"/s4/datasets/{d['id']}", json={"active": want})
                assert r.status_code == 200, r.text
                (self.active.add if want else self.active.discard)(k)

    def forget(self):
        """Xoá bộ nhớ của tài khoản bench: điều nhớ từ câu trước không được ảnh hưởng câu sau."""
        for m in self.c.get("/s4/memory").json()["items"]:
            self.c.delete(f"/s4/memory/{m['id']}")

    def chat(self, text: str, cid: str | None = None) -> dict:
        t0, first, final_first, evs = time.time(), None, None, []
        with self.c.stream("POST", "/s4/chat", json={"text": text, "conversation_id": cid}) as r:
            buf = ""
            for chunk in r.iter_text():
                buf += chunk
                while "\n\n" in buf:
                    line, buf = buf.split("\n\n", 1)
                    if not line.startswith("data: "):
                        continue
                    ev = json.loads(line[6:]); evs.append(ev)
                    if ev["type"] == "delta":
                        first = first or time.time() - t0
                        final_first = final_first or time.time() - t0
                    elif ev["type"] in ("restart", "replace"):
                        final_first = None if ev["type"] == "restart" else (final_first or time.time() - t0)
        total = time.time() - t0
        cid = evs[0]["conversation_id"]
        msg = self.c.get(f"/s4/conversations/{cid}/messages").json()["messages"][-1]
        tr = self.c.get(f"/s4/trace/{msg['id']}").json().get("trace") or {}
        tm = tr.get("timing") or {}
        stats = tm.get("llm_stats") or []
        return {"cid": cid, "content": msg["content"], "meta": msg["meta"], "first_s": round(first or total, 2),
                "final_first_s": round(final_first or total, 2), "total_s": round(total, 2),
                "search_ms": tm.get("search_ms"), "search_parts": tm.get("search_parts"), "table_ms": tm.get("table_ms"),
                "llm_calls": len(stats), "prompt_tokens": sum(s.get("prompt_tokens", 0) for s in stats),
                "prompt_s": round(sum(s.get("prompt_s", 0) for s in stats), 2), "output_tokens": sum(s.get("output_tokens", 0) for s in stats),
                "output_s": round(sum(s.get("output_s", 0) for s in stats), 2), "load_s": round(sum(s.get("load_s", 0) for s in stats), 2),
                "plan": (tr.get("output") or {}).get("plan")}


def policy_docx() -> Path:
    """Tệp Word chính sách giống nv3_specialist.py (tạo lại mỗi lần, nội dung cố định)."""
    import docx
    path = RUNTIME / "chinh_sach_team7.docx"
    if path.exists():
        return path
    RUNTIME.mkdir(parents=True, exist_ok=True)
    d = docx.Document()
    d.add_heading("Chính sách đổi trả", level=1)
    d.add_paragraph("Khách hàng được đổi trả sản phẩm trong vòng 7 ngày kể từ ngày nhận hàng nếu sản phẩm còn nguyên tem và hoá đơn.")
    d.add_heading("Giờ làm việc", level=1)
    d.add_paragraph("Bộ phận hỗ trợ làm việc từ 8 giờ đến 17 giờ 30, thứ Hai đến thứ Bảy. Chủ nhật nghỉ.")
    t = d.add_table(rows=4, cols=2)
    for i, (a, b) in enumerate([("Hạng thành viên", "Ưu đãi"), ("Bạc", "Giảm 5% mọi đơn hàng"), ("Vàng", "Giảm 10% mọi đơn hàng"),
                                ("Kim cương", "Giảm 15% và miễn phí giao hàng")]):
        t.cell(i, 0).text, t.cell(i, 1).text = a, b
    d.save(path)
    return path


# ------------------------------------------------------------------ chạy
def run(args):
    from bench_cases import all_cases
    base = re.split(r"[+@]", args.name)[0]
    if base not in PRESETS:   # tên lạ -> dùng nhầm cài đặt mặc định (model cũ) mà không biết: dừng luôn (lỗi đã gặp khi đo NV5)
        raise SystemExit(f"tên cấu hình phải bắt đầu bằng một trong {list(PRESETS)} (vd. inst02+D), không phải {args.name!r}")
    settings = dict(PRESETS[base])
    for kv in args.set or []:
        k, v = kv.split("=", 1)
        try:
            settings[k] = json.loads(v)
        except ValueError:
            settings[k] = v
    cases = [c for c in all_cases() if (args.split == "all" or c["split"] == args.split)
             and (not args.suites or c["suite"] in args.suites.split(","))]
    print(f"[{args.name}] cài đặt: {settings}\n  {len(cases)} câu × {args.repeat} lần")
    unload_models()
    srv = start_server(settings, args.name)
    try:
        cl = Client()
        cl.ensure_datasets()
        cl.use(["policy"]); cl.chat("Chào bạn")             # nóng máy: model + bge-m3 + reranker
        cl.use([]); cl.chat("Bạn giúp được gì cho mình?")
        runs = []
        for c in cases:
            for rep in range(args.repeat):
                cl.use(c["datasets"])
                cl.forget()
                cid, r = None, None
                for t in c["turns"]:
                    r = cl.chat(t, cid); cid = r["cid"]
                ok, why = score(c["check"], r["content"], r["meta"])
                runs.append({"id": c["id"], "suite": c["suite"], "split": c["split"], "rep": rep, "pass": ok, "why": why,
                             "answer": r["content"][:600], "choices": r["meta"].get("choices"),
                             "sources": [s.get("title") for s in r["meta"].get("sources") or []],
                             "consulted": [s.get("title") for s in r["meta"].get("consulted") or []],
                             "small_talk": r["meta"].get("small_talk"), "grounding": r["meta"].get("grounding"),
                             "ambiguity": r["meta"].get("ambiguity"), "guard": r["meta"].get("guard"),
                             **{k: r[k] for k in ("first_s", "final_first_s", "total_s", "search_ms", "search_parts", "table_ms", "llm_calls",
                                                  "prompt_tokens", "prompt_s", "output_tokens", "output_s", "load_s", "plan")}})
                print(f"  {'PASS' if ok else 'FAIL'} {c['id']:<18} {r['first_s']:>5.1f}s/{r['total_s']:>5.1f}s"
                      + (f"  {'; '.join(why)[:110]}" if why else ""))
        behavior = None
        if not args.no_behavior:
            out = OUT_DIR / f"{args.name}_nv2.json"
            env = dict(os.environ, PYTHONIOENCODING="utf-8", NV2_OUT=str(out))
            print("  22 tình huống hành vi (nv2_behavior.py)…")
            subprocess.run([str(PY), str(HERE / "nv2_behavior.py"), BASE], env=env, capture_output=True, timeout=3600)
            if out.exists():
                behavior = json.loads(out.read_text(encoding="utf-8"))
                print(f"  hành vi: {behavior['summary']['passed']}/{behavior['summary']['total']}")
    finally:
        stop_server(srv)
    res = {"name": args.name, "settings": settings, "split": args.split, "repeat": args.repeat, "time": time.strftime("%Y-%m-%d %H:%M"),
           "runs": runs, "behavior": behavior}
    res["summary"] = summarize(res)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{args.name}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print_table([res])


def _rate(rs):
    return round(100 * sum(r["pass"] for r in rs) / len(rs), 1) if rs else None


def _med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def _p90(xs):
    xs = sorted(x for x in xs if x is not None)
    return round(xs[min(len(xs) - 1, int(len(xs) * 0.9))], 2) if xs else None


def summarize(res: dict) -> dict:
    runs = res["runs"]
    acc = [r for r in runs if r["suite"] in ("accuracy", "halluc")]
    gr = [r for r in runs if r["suite"] == "greeting"]
    b = (res.get("behavior") or {}).get("summary") or {}
    b_fail = (b.get("total", 0) - b.get("passed", 0)) if b else None
    spec = [r for r in runs if r["search_ms"] is not None]
    s = {"accuracy": _rate(acc), "accuracy_dev": _rate([r for r in acc if r["split"] == "dev"]),
         "accuracy_exam": _rate([r for r in acc if r["split"] == "exam"]),
         "acc_only": _rate([r for r in runs if r["suite"] == "accuracy"]), "halluc": _rate([r for r in runs if r["suite"] == "halluc"]),
         "greeting": _rate(gr), "greeting_fails": sum(not r["pass"] for r in gr), "behavior": f"{b.get('passed')}/{b.get('total')}" if b else None,
         "wrong_behavior": sum(not r["pass"] for r in gr) + (b_fail or 0),
         "first_med": _med([r["final_first_s"] for r in runs]), "total_med": _med([r["total_s"] for r in runs]),
         "total_p90": _p90([r["total_s"] for r in runs]), "spec_total_med": _med([r["total_s"] for r in spec]),
         "search_med_ms": _med([r["search_ms"] for r in spec]), "prompt_tokens_med": _med([r["prompt_tokens"] for r in runs]),
         "prompt_s_med": _med([r["prompt_s"] for r in runs]), "output_s_med": _med([r["output_s"] for r in runs]),
         "load_s_sum": round(sum(r["load_s"] or 0 for r in runs), 1),
         "rewrites": sum(bool(r.get("grounding")) for r in runs), "n": len(runs)}
    return s


def print_table(results: list[dict]):
    cols = [("name", "cấu hình"), ("accuracy", "đúng %"), ("accuracy_dev", "dev %"), ("accuracy_exam", "exam %"), ("halluc", "không bịa %"),
            ("greeting", "chào %"), ("behavior", "hành vi"), ("wrong_behavior", "sai hành vi"), ("first_med", "chữ đầu"),
            ("total_med", "cả câu"), ("total_p90", "cả câu p90"), ("search_med_ms", "tìm ms"), ("prompt_s_med", "đọc s"),
            ("output_s_med", "viết s"), ("rewrites", "viết lại")]
    print("\n| " + " | ".join(h for _, h in cols) + " | pareto |")
    print("|" + "---|" * (len(cols) + 1))
    front = pareto(results)
    for r in results:
        s = {**r["summary"], "name": r["name"]}
        print("| " + " | ".join(str(s.get(k, "")) for k, _ in cols) + f" | {'★' if r['name'] in front else ''} |")


def pareto(results: list[dict]) -> set[str]:
    """Không cấu hình nào khác tốt hơn hoặc bằng ở cả 3 trục (đúng cao, nhanh, ít sai hành vi) và hơn hẳn ở ít nhất 1 trục."""
    pts = {r["name"]: (r["summary"]["accuracy"] or 0, -(r["summary"]["total_med"] or 1e9), -(r["summary"]["wrong_behavior"] or 0))
           for r in results}
    return {n for n, p in pts.items() if not any(all(q[i] >= p[i] for i in range(3)) and q != p for m, q in pts.items() if m != n)}


def compare(args):
    res = [json.loads(Path(f).read_text(encoding="utf-8")) for f in args.files]
    for r in res:
        r["summary"] = summarize(r)
    print_table(res)
    if args.detail:   # câu nào khác nhau giữa các cấu hình (chỉ split dev, không xem bài thi cuối)
        by = {}
        for r in res:
            for x in r["runs"]:
                if x["split"] == "dev":
                    by.setdefault(x["id"], {}).setdefault(r["name"], []).append(x["pass"])
        for cid, d in by.items():
            vals = {n: sum(v) / len(v) for n, v in d.items()}
            if len(set(vals.values())) > 1:
                print(f"  {cid:<20} " + "  ".join(f"{n}={v:.0%}" for n, v in vals.items()))


def swap(args):
    """Đo Ollama nạp lại model khi người dùng chuyển Strict (qwen3:4b) <-> Friendly (Instruct), có bge-m3 đang nạp."""
    import ollama
    cl = ollama.Client()
    unload_models()
    cl.embed(model="bge-m3", input=["khởi động"], keep_alive="30m")
    out = []
    for i in range(3):
        for m in ("qwen3:4b", INSTRUCT):
            t0 = time.time()
            r = cl.generate(model=m, prompt="Chào", options={"num_ctx": 8192, "num_predict": 1}, keep_alive="30m", think=False)
            out.append((m, round(r.load_duration / 1e9, 2), round(time.time() - t0, 2)))
            print(f"  lần {i + 1} {m:<32} nạp {out[-1][1]:>5.2f}s  cả lệnh {out[-1][2]:>5.2f}s")
    print("  đang nạp:", [(m.model, round(m.size_vram / 2**30, 2)) for m in cl.ps().models])
    unload_models()


def strict(args):
    """Bộ đo System 3 (Strict) với một model khác (câu 1D, phương án "Instruct cho cả Strict")."""
    env = dict(os.environ, PYTHONPATH=str(PYROOT), PYTHONIOENCODING="utf-8", S3_USE_LLM="1", LLM_MODEL=args.model)
    unload_models()
    subprocess.run([str(PY), "run.py", "--adapter", "answer_adapter:adapter", "--name", args.name, "--split", args.split],
                   cwd=PYROOT / "system3" / "eval", env=env)   # adapter của System 3 tự tìm server/ qua đường dẫn pyroot/system3


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run"); a.add_argument("name"); a.add_argument("--set", action="append")
    a.add_argument("--split", default="dev"); a.add_argument("--repeat", type=int, default=1); a.add_argument("--suites")
    a.add_argument("--no-behavior", action="store_true")
    a = sub.add_parser("compare"); a.add_argument("files", nargs="+"); a.add_argument("--detail", action="store_true")
    sub.add_parser("swap")
    a = sub.add_parser("strict"); a.add_argument("--model", required=True); a.add_argument("--name", required=True)
    a.add_argument("--split", default="dev")
    args = ap.parse_args()
    {"run": run, "compare": compare, "swap": swap, "strict": strict}[args.cmd](args)

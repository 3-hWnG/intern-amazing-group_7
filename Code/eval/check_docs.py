"""Kiểm tài liệu so với số đo và code (Phase 24). Chạy: python eval/check_docs.py   (exit 0 = sạch, 1 = có lỗi)

Kiểm: (1) số trong README so với file kết quả MỚI NHẤT trong eval/results/ (bộ không-mù); (2) số bộ mù/bộ team khớp bảng BLIND dưới đây
và khớp giữa các tài liệu; (3) đường dẫn trong liên kết/`code`/khối lệnh có tồn tại; (4) mọi server/tests/*_test.py có trong SETUP và CONTRIBUTING;
(5) `_EVENTS`, timeout trong config.py khớp tài liệu, không còn gate cũ; (6) file có thẻ FINAL-PRODUCT: được nêu trong FINAL_PRODUCT_CHECKLIST.md.
QUY TẮC BỘ MÙ (docs/EVAL.md): script KHÔNG mở file kết quả của HOLDOUT-2/3/4, pseudo_real, bộ team (BLIND_RE loại chúng khi chọn file);
số của chúng do người điều phối ghi vào BLIND bên dưới, nên chỉ kiểm được nhất quán giữa tài liệu, không kiểm với kết quả chạy.
"""
import json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # thư mục chứa run_server.py (tên gì cũng được)
RES = ROOT / "eval" / "results"
BLIND_RE = re.compile(r"(h[234]|pseudo|pr2|team|coord|final_llm)", re.I)    # không bao giờ đọc
# Số bộ mù/bộ team do người điều phối chạy (2026-10-07, sau Phase 23). Cập nhật CÙNG LÚC với README khi chạy lại.
BLIND = {"HOLDOUT-4": ["60/77", "89/106", "8/16"], "pseudo_real 2": ["19/28", "23/34", "0/3"], "Bộ team": ["8/10"]}
DOCS = ["README.md", "docs/SETUP.md", "docs/ARCHITECTURE.md", "docs/EVAL.md", "docs/CONTRIBUTING.md", "docs/KNOWN_ISSUES.md",
        "docs/FINAL_PRODUCT_CHECKLIST.md", "docs/BAO_CAO_DOT4.md", "eval/README.md", "server/README.md", "retrieval/README.md",
        "server/COPY_NOTES.md", "knowledge/README.md", "eval/REPRODUCE.md", "eval/vendor_v106/SOURCE.md"]
CURRENT = ["README.md", "docs/SETUP.md", "docs/ARCHITECTURE.md", "docs/EVAL.md", "docs/CONTRIBUTING.md", "docs/KNOWN_ISSUES.md", "server/README.md"]
NOPATH = {"server/COPY_NOTES.md"}      # liệt kê tên file của V10.6 (lịch sử), không phải đường dẫn trong repo này
HIST = re.compile(r"trước|lúc đó|Phase 19|gốc|cũ|lần đo|đợt 4|ban đầu|lỗi thời|đã bỏ|còn 5", re.I)
err, skip, ok = [], [], []


def text(p):
    return (ROOT / p).read_text(encoding="utf-8")


def pct(x, nd=1):
    return f"{100 * x:.{nd}f}%".replace(".", ",")


def expect(doc, needle, why):
    (ok if needle in text(doc) else err).append(f"{doc}: {'khớp' if needle in text(doc) else 'THIẾU'} {needle!r} ({why})")


def newest(pred, pattern="*.json"):
    """File kết quả không-mù mới nhất thoả pred(data)."""
    fs = sorted((f for f in RES.glob(pattern) if not BLIND_RE.search(f.name) and not f.name.startswith("v106")), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in fs:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if pred(d):
            return f, d
    return None, None


def line_with(doc, key):
    return next((l for l in text(doc).splitlines() if key in l), "")


# ---------------------------------------------------------------- (1) số với results
def check_numbers():
    f, d = newest(lambda d: isinstance(d, dict) and "summary" in d and d["summary"].get("dev", {}).get("n", 0) >= 500)
    if not f:
        skip.append("DEV 523: không có file kết quả (eval/results/*.json) -> bỏ qua")
    else:
        s = d["summary"]["dev"]
        expect("README.md", f"{pct(s['top1'])} / {pct(s['behavior'])} / {pct(s['fab'])}", f"DEV gộp {s['n']} ({f.name})")
        for doc in ("README.md", "docs/EVAL.md"):
            expect(doc, str(s["n"]), "số ca DEV")
        old = [r for r in d["cases"] if r["split"] == "dev" and not re.match(r"p(16|18|19|23)", r["id"])]
        rate = lambda k: [r[k] for r in old if r[k] is not None]
        t1, bh, fb = rate("top1"), rate("behavior_ok"), rate("fab")
        a, b, c = sum(t1) / len(t1), sum(bh) / len(bh), sum(fb) / len(fb)
        expect("README.md", f"{pct(a)} / {pct(b)} / {pct(c)}", f"DEV cũ {len(old)} ({f.name})")
        expect("docs/EVAL.md", f"{pct(a)} ({sum(t1)}/{len(t1)})", "gate DEV cũ top-1")
        expect("docs/EVAL.md", f"{pct(b)} ({sum(bh)}/{len(bh)})", "gate DEV cũ hành vi")
        oos = [r for r in d["cases"] if r["split"] == "dev" and r["category"] == "out_of_scope"]
        k = f"{sum(r['behavior_ok'] for r in oos)}/{len(oos)}"
        (ok if k in line_with("README.md", "ngoài phạm vi") else err).append(f"README.md: ngoài phạm vi {k} ({f.name})")
    # ctx
    f, d = newest(lambda d: isinstance(d, list) and d and "cat" in d[0] and "ok" in d[0] and len(d) >= 80)
    if f:
        expect("README.md", f"{sum(r['ok'] for r in d)}/{len(d)}", f"ctx ({f.name})")
    else:
        skip.append("ctx 91: không có file kết quả -> bỏ qua")
    f, d = newest(lambda d: isinstance(d, list) and d and "ok" in d[0] and all(str(r.get("id", "")).startswith("p23-") for r in d))
    if f:
        expect("README.md", f"ctx-p23: {sum(r['ok'] for r in d)}/{len(d)}", f"ctx-p23 ({f.name})")
    else:
        skip.append("ctx-p23: không có file kết quả -> bỏ qua")
    # concise
    f, d = newest(lambda d: isinstance(d, dict) and isinstance(d.get("table_md"), str) and "summary" not in d)
    if f:
        for key, doc_key in (("DEV", "DEV focus"), ("HOLDOUT cũ", "HOLDOUT cũ focus")):
            m = re.search(r"\| " + key + r" \| (\d+) \| (\d+)% \((\d+/\d+)\) \| (\d+/\d+) \|", d["table_md"])
            if m:
                expect("README.md", f"{m.group(2)}% ({m.group(3)})", f"{key} focus ({f.name})")
                expect("README.md", m.group(4), f"{key} task thừa ({f.name})")
    else:
        skip.append("concise: không có file kết quả -> bỏ qua")
    # perturb
    f, d = newest(lambda d: isinstance(d, dict) and "by" in d and "rate" in d, "perturb_*.json")
    if f:
        a, b = sum(v[0] for v in d["by"].values()), sum(v[1] for v in d["by"].values())
        expect("README.md", pct(d["rate"] / 100, 2), f"perturb ({f.name})")
        expect("README.md", f"{a:,}/{b:,}".replace(",", "."), "perturb số phép thử")
    else:
        skip.append("perturb: không có file kết quả -> bỏ qua")
    # synth (log do người chạy lưu: python eval/synth_retrieval.py > eval/results/synth.txt)
    p = RES / "synth.txt"
    if p.exists():
        t = p.read_text(encoding="utf-8", errors="replace")
        tr, te = re.search(r"\[train\].*?top1=([\d.]+)%", t), re.search(r"\[test\].*?top1=([\d.]+)%", t)
        gt, ge = re.search(r"\[glued\] train: ([\d.]+)%", t), re.search(r"\[glued\] test: ([\d.]+)%", t)
        if tr and te:
            expect("README.md", f"{tr.group(1)}% / {te.group(1)}%".replace(".", ","), "synth TRAIN / TEST")
        if gt and ge:
            expect("README.md", f"{gt.group(1)}% / {ge.group(1)}%".replace(".", ","), "synth glued TRAIN / TEST")
    else:
        skip.append("synth: không có eval/results/synth.txt -> bỏ qua")
    # bước sinh chữ (Phase 27): composer_<tên>.json mới nhất (score_composer.py); số trong EVAL.md/README phải khớp
    f, d = newest(lambda d: isinstance(d, dict) and "rows" in d and "timeout" in d, "composer_*.json")
    if f:
        rows, n = d["rows"], len(d["rows"])
        allok = lambda r, m: all(v is not False for v in r[m].values())
        off, on = sum(allok(r, "off") for r in rows), sum(allok(r, "on") for r in rows)
        expect("docs/EVAL.md", f"{off}/{n} ({100 * off / n:.0f}%) | {on}/{n} ({100 * on / n:.0f}%)", f"bước sinh chữ đạt cả 5 TẮT | BẬT ({f.name})")
        expect("README.md", f"{100 * on / n:.0f}% ({on}/{n}) so với {100 * off / n:.0f}% ({off}/{n})", f"README bước sinh chữ ({f.name})")
        expect("docs/EVAL.md", f"Lượt gọi LLM: {sum(len(r['llm_ms']) for r in rows)}, timeout {sum(len(r['llm_err']) for r in rows)}", f"lượt gọi/timeout ({f.name})")
    else:
        skip.append("composer: không có results/composer_*.json -> bỏ qua")


# ---------------------------------------------------------------- (2) số bộ mù, bộ team
def check_blind():
    for key, nums in BLIND.items():
        row = line_with("README.md", key)
        for n in nums:
            (ok if n in row else err).append(f"README.md: dòng {key!r} {'có' if n in row else 'THIẾU'} {n} (bảng BLIND)")
    ki = text("docs/KNOWN_ISSUES.md")
    for n in ("8/10", "TC03", "TC06"):
        (ok if n in ki else err).append(f"KNOWN_ISSUES.md: {'có' if n in ki else 'THIẾU'} {n}")
    for doc in CURRENT:
        for i, l in enumerate(text(doc).splitlines(), 1):
            if re.search(r"58/77|7/10 PASS|75% \(58", l) and not HIST.search(l):
                err.append(f"{doc}:{i}: số bộ mù/bộ team cũ không đánh dấu 'trước/cũ': {l.strip()[:90]}")


# ---------------------------------------------------------------- (3) đường dẫn, lệnh
_names = None


def exists(tok, doc):
    global _names
    tok = tok.strip().rstrip(".,;:)").replace("\\", "/")
    while tok.startswith(("./", "../")):
        tok = tok.split("/", 1)[1]
    if _names is None:
        _names = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if ".git" not in p.parts and "__pycache__" not in p.parts]
    if (ROOT / tok).exists() or (ROOT.parent / tok).exists() or (ROOT / Path(doc).parent / tok).exists():
        return True
    return any(n == tok or n.endswith("/" + tok) for n in _names)


SKIP_PATH = re.compile(r"[<>*{}$=()|\[\]]|^(repo|Database|Backend|Frontend|http|~)|(^|/)(runtime|\.venv|\.git)(/|$)|\.env$|\.db$|\.docx$|\.pdf$|^results/(<|baseline_stripped)")
EXT = r"(?:md|py|jsonl|json|sql|txt|html|js|css)"


def check_paths():
    for doc in DOCS:
        t = text(doc)
        toks = set(m.group(1) for m in re.finditer(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", t) if not m.group(1).startswith("http"))
        toks |= set(m.group(1) for m in re.finditer(r"`([^`\s]+\." + EXT + r")`", t))
        for tok in ([] if doc in NOPATH else sorted(toks)):
            if SKIP_PATH.search(tok) or tok.startswith("/"):
                continue
            if not exists(tok, doc):
                err.append(f"{doc}: đường dẫn không tồn tại: {tok}")
        # lệnh python trong khối mã và trong `code`
        cmds = [l for blk in re.findall(r"```[a-z]*\n(.*?)```", t, re.S) for l in blk.splitlines()] + re.findall(r"`(python[^`]*)`", t)
        for l in cmds:
            for m in re.finditer(r"python3?\s+(?:-m\s+([\w.]+)|([\w./\\-]+\.py))", l):
                if m.group(1):
                    mod = m.group(1)
                    if mod.startswith("system3."):
                        rel = mod.split(".", 1)[1].replace(".", "/")
                        good = (ROOT / (rel + ".py")).exists() or (ROOT / rel / "__init__.py").exists() or (ROOT / rel / "__main__.py").exists()
                        if not good:
                            err.append(f"{doc}: lệnh trỏ module không có: python -m {mod}")
                elif not exists(m.group(2), doc) and not SKIP_PATH.search(m.group(2)):
                    err.append(f"{doc}: lệnh trỏ script không có: {m.group(2)}")
            for m in re.finditer(r"--adapter\s+(\w+):(\w+)", l):
                if m.group(1).startswith("my_"):
                    continue                      # ví dụ minh hoạ trong eval/README.md
                f = ROOT / "eval" / (m.group(1) + ".py")
                if not f.exists() or not re.search(rf"^(def {m.group(2)}\b|{m.group(2)}\s*=)", f.read_text(encoding="utf-8"), re.M):
                    err.append(f"{doc}: --adapter {m.group(1)}:{m.group(2)} không có")


# ---------------------------------------------------------------- (4)(5)(6) nhất quán với code
def check_code():
    for p in sorted((ROOT / "server" / "tests").glob("*_test.py")):
        for doc in ("docs/SETUP.md", "docs/CONTRIBUTING.md"):
            (ok if p.stem in text(doc) else err).append(f"{doc}: test {p.stem} {'có' if p.stem in text(doc) else 'THIẾU'}")
    for doc in ("docs/CONTRIBUTING.md", "eval/README.md"):
        (ok if "check_docs" in text(doc) else err).append(f"{doc}: {'có' if 'check_docs' in text(doc) else 'THIẾU'} check_docs.py trong gate")
    for doc in ("README.md", "docs/SETUP.md"):
        (ok if "run_server.py" in text(doc) else err).append(f"{doc}: {'có' if 'run_server.py' in text(doc) else 'THIẾU'} launcher")
    # _EVENTS
    try:
        sys.path.insert(0, str(ROOT))
        from run_server import register_package
        register_package(ROOT)
        from system3.retrieval import context
        n = len(context.EVENTS)
        for doc in ("README.md", "retrieval/README.md", "docs/ARCHITECTURE.md"):
            nums = [int(m.group(1)) for l in text(doc).splitlines() if "_EVENTS" in l or "sự kiện đời sống" in l for m in re.finditer(r"(\d+) sự kiện", l)]
            (ok if nums and all(x == n for x in nums) else err).append(f"{doc}: số sự kiện {nums} so với code {n}")
    except Exception as e:
        skip.append(f"_EVENTS: không import được retrieval.context ({type(e).__name__}) -> bỏ qua")
    # timeout
    cfg = text("server/config.py")
    vals = {k: re.search(k + r'\s*=\s*float\(_str\("' + k + r'",\s*"([\d.]+)"\)', cfg) for k in ("PLANNER_LLM_TIMEOUT", "ANSWER_LLM_TIMEOUT")}
    arch = text("docs/ARCHITECTURE.md")
    for k, m in vals.items():
        if not m:
            err.append(f"server/config.py: không thấy {k}")
            continue
        v = float(m.group(1))
        (ok if k in arch and f"{v:g} s" in arch else err).append(f"ARCHITECTURE.md: bảng timeout {k}={v:g} s")
    if len({m.group(1) for m in vals.values() if m}) > 1:
        err.append("server/config.py: hai timeout LLM khác nhau (quyết định: cùng 7 s)")
    if re.search(r"^TIMEOUT\s*=\s*\d", text("server/answer/llm_answer.py"), re.M):
        err.append("server/answer/llm_answer.py: TIMEOUT cứng; phải lấy từ config.ANSWER_LLM_TIMEOUT")
    for doc in CURRENT:
        for i, l in enumerate(text(doc).splitlines(), 1):
            if re.search(r"(timeout|quá hạn)[^\n]{0,30}\b5\s?(s|giây)\b", l, re.I) and not HIST.search(l):
                err.append(f"{doc}:{i}: còn 'timeout 5 s' không đánh dấu cũ: {l.strip()[:90]}")
            if re.search(r"focus[^\n]*\b90\s?%", l, re.I) and not HIST.search(l):
                err.append(f"{doc}:{i}: gate DEV focus 90% (B1: thống nhất ≥ 95%): {l.strip()[:90]}")
    for doc in ("docs/CONTRIBUTING.md", "docs/EVAL.md"):
        expect(doc, "≥ 95%", "gate DEV focus")
    # số ca DEV / ctx trong EVAL
    cs = [json.loads(l) for l in (ROOT / "eval" / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    dev = [c for c in cs if c.get("split", "dev") == "dev"]
    pref = {p: sum(c["id"].startswith(p) for c in dev) for p in ("p16", "p18", "p19", "p23")}
    row = line_with("docs/EVAL.md", "| DEV |")
    for n in [len(dev), len(dev) - sum(pref.values()), *pref.values()]:
        (ok if str(n) in row else err).append(f"EVAL.md: dòng DEV {'có' if str(n) in row else 'THIẾU'} {n} (cases.jsonl)")
    cx = [json.loads(l)["split"] for l in (ROOT / "eval" / "cases_ctx.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    row = line_with("docs/EVAL.md", "| ctx |")
    for n in [len(cx), *(cx.count(s) for s in set(cx))]:
        (ok if str(n) in row else err).append(f"EVAL.md: dòng ctx {'có' if str(n) in row else 'THIẾU'} {n} (cases_ctx.jsonl)")
    # thẻ FINAL-PRODUCT
    chk = text("docs/FINAL_PRODUCT_CHECKLIST.md")
    tagged = sorted({p.relative_to(ROOT).as_posix() for ext in ("py", "js", "sql") for p in ROOT.rglob("*." + ext)
                     if "eval/" not in p.relative_to(ROOT).as_posix() and "FINAL-PRODUCT:" in p.read_text(encoding="utf-8", errors="replace")})
    for f in tagged:
        (ok if f in chk else err).append(f"FINAL_PRODUCT_CHECKLIST.md: file có thẻ {f} {'được nêu' if f in chk else 'KHÔNG được nêu'}")
    if not tagged:
        err.append("không có thẻ FINAL-PRODUCT: nào trong code")
    for doc in ("README.md", "docs/CONTRIBUTING.md"):
        expect(doc, "FINAL_PRODUCT_CHECKLIST.md", "liên kết checklist")
    expect("README.md", "KNOWN_ISSUES.md", "liên kết lỗi đã biết")
    # đường dẫn máy tác giả
    for doc in DOCS:
        for i, l in enumerate(text(doc).splitlines(), 1):
            if re.search(r"(?<![\w])[CDE]:(?:\\|/[A-Za-z_]+/)", l) and "Windows" not in l:
                err.append(f"{doc}:{i}: đường dẫn máy tác giả (dùng <ROOT>): {l.strip()[:90]}")
    # Phase 28: mã eval không còn đường dẫn cứng D:\ ; vendor V10.6 đủ file và ghi commit (không mở file ca của bộ mù)
    skip_py = re.compile(r"(cases_h|build_h|cases_pseudo|cases_team|run_team|run_pseudo|check_docs)")
    for p in (ROOT / "eval").glob("*.py"):
        if skip_py.search(p.name):
            continue
        for i, l in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.search(r"[\"'](?:[A-Za-z]:\|[A-Za-z]:/)", l) and not l.lstrip().startswith("#"):
                err.append(f"eval/{p.name}:{i}: đường dẫn tuyệt đối cứng: {l.strip()[:80]}")
    src = text("eval/vendor_v106/SOURCE.md")
    for f in ("retrieval.py", "search.py", "textutil.py", "paths.py", "import_db.py", "__init__.py", "schema_procedures.sql"):
        (ok if (ROOT / "eval/vendor_v106/Database/pipeline" / f).is_file() and f in src else err).append(f"vendor_v106: {f} có file và có trong SOURCE.md")
    expect("eval/vendor_v106/SOURCE.md", "83567403c61b65a9f447b13f8f023527dc15fb97", "commit V10.6")


if __name__ == "__main__":
    for fn in (check_numbers, check_blind, check_paths, check_code):
        fn()
    for m in skip:
        print("SKIP", m)
    for m in err:
        print("LOI ", m)
    print(f"check_docs: {len(ok)} khớp, {len(err)} lỗi, {len(skip)} bỏ qua")
    sys.exit(1 if err else 0)

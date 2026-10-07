"""Harness đo System 3.   python run.py [--adapter module:func] [--name baseline] [--category rag_basic] [--limit N]

Adapter: adapter(turns) -> dict
    turns: [{"role": "user"|"assistant", "text": str}, ...]  (lượt cuối là user)
    trả về {
      "tasks": [{"proc_id": str|None, "candidates": [proc_id xếp hạng], "fields": [...], "quantity": str|None}],
      "behavior": "answer"|"apologize"|"clarify",
      "answer_text": str,           # "" nếu adapter chưa sinh câu trả lời
      "latency_ms": float,          # bỏ trống => harness tự đo
      "extra": {...}                # tùy chọn, vd {"is_strong": bool}
    }
Chỉ dùng stdlib. Đọc procedures.db chỉ-đọc để biết số/ngày nào CÓ trong nguồn.
"""
import argparse, importlib, json, os, re, sqlite3, statistics, sys, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rules_scorer import score_rule  # noqa: E402
DB = os.environ.get("S3_DB") or os.environ.get("S3_DATA_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "runtime", "system3.db")   # DB của System 3 (repo V10.6 cũ không còn)

# --------------------------------------------------------------- nguồn ------
_blob = {}


def source_blob(pid):
    if pid in _blob:
        return _blob[pid]
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    p = c.execute("select * from procedures where proc_id=? and status='active' order by row_id limit 1", (pid,)).fetchone()
    parts = []
    if p:
        parts += [str(v) for v in dict(p).values() if v is not None]
        for tb in ("procedure_fees", "checklist_items", "procedure_files", "procedure_steps", "procedure_methods",
                   "legal_basis", "procedure_cases", "online_services"):
            parts += [" ".join(str(v) for v in dict(r).values()) for r in c.execute(f"select * from {tb} where row_id=?", (p["row_id"],))]
    try:    # Phase 23d: lệ phí bù từ corpus nhóm cũng là nguồn hợp lệ
        parts += [r[0] for r in c.execute("select amount_text from team_fee_overlay where proc_id=?", (pid,))]
    except sqlite3.Error:
        pass
    c.close()
    _blob[pid] = " ".join(parts)
    return _blob[pid]


def _num(s):
    s = s.strip()
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        return int(re.sub(r"[.,]", "", s))
    try:
        return int(float(s.replace(",", ".")))
    except ValueError:
        return None


NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
AMT_RE = re.compile(r"(\d+(?:[.,\s]\d{3})*(?:[.,]\d+)?)\s*(đồng|đ\b|vnđ|vnd|nghìn|ngàn|triệu)", re.I)
TIME_RE = re.compile(r"(\d+)\s*(ngày|giờ|tháng|tuần|phút)", re.I)
FREE_RE = re.compile(r"miễn\s*(lệ\s*)?phí|không\s*(mất|tốn|phải\s*đóng|thu)\s*(lệ\s*)?(phí|tiền)|0\s*đồng|free", re.I)
NPS_RE = re.compile(r"không công bố|chưa công bố|chưa được công bố|chưa có thông tin|không có thông tin|chưa được ghi|không ghi|không nêu|chưa nêu|"
                    r"không có dữ liệu|chưa có dữ liệu|hội đồng nhân dân|do .{0,40}quy định|không cung cấp|chưa cập nhật", re.I)
PHONE_RE = re.compile(r"(?<!\d)0\d{9,10}(?!\d)|\b1900\s?\d{4}\b")
HOURS_RE = re.compile(r"\b\d{1,2}\s*(h|giờ)\s*\d{0,2}\s*(-|–|đến)\s*\d{1,2}\s*(h|giờ)", re.I)


def allowed_numbers(case, pids):
    nums = set()
    text = " ".join(source_blob(p) for p in pids) + " " + " ".join(t["text"] for t in case["turns"])
    for m in NUM_RE.finditer(text):
        v = _num(m.group(0))
        if v is not None:
            nums.add(v)
    return nums


def has_overlay(pids):
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return any(c.execute("select 1 from team_fee_overlay where proc_id=?", (p,)).fetchone() for p in pids)
    except sqlite3.Error:
        return False
    finally:
        c.close()


def fabricated(case, answer, pids):
    """Trả về danh sách lý do 'bịa' trong câu trả lời."""
    exp, why = case["expected"], []
    ok = allowed_numbers(case, pids)
    for m in AMT_RE.finditer(answer):
        v = _num(m.group(1).replace(" ", "."))
        if v is None:
            continue
        mult = {"nghìn": 1000, "ngàn": 1000, "triệu": 1_000_000}.get(m.group(2).lower(), 1)
        if v not in ok and v * mult not in ok:
            why.append(f"tiền:{m.group(0)}")
    for m in TIME_RE.finditer(answer):
        if int(m.group(1)) not in ok:
            why.append(f"thời gian:{m.group(0)}")
    for fn in exp.get("forbidden_numbers", []):
        if fn in answer:
            why.append(f"xác nhận số sai:{fn}")
    if exp.get("forbid_phone") and PHONE_RE.search(answer):
        why.append("số điện thoại bịa")
    if exp.get("forbid_hours") and HOURS_RE.search(answer):
        why.append("giờ làm việc bịa")
    # 'miễn phí' khi nguồn không nói miễn: bịa kiểu nguy hiểm nhất
    if exp.get("missing_numeric_fields") and "fees" in exp["missing_numeric_fields"] and not exp.get("free_text_in_source") and not has_overlay(pids):
        if FREE_RE.search(answer):
            why.append("suy ra miễn phí")
    return why


# -------------------------------------------------------------- chấm điểm ---
def cands_of(t):
    c = list(t.get("candidates") or [])
    if t.get("proc_id") and t["proc_id"] not in c[:1]:
        c = [t["proc_id"]] + [x for x in c if x != t["proc_id"]]
    return c


def score_case(case, out):
    exp = case["expected"]
    r = dict(id=case["id"], category=case["category"], split=case.get("split", "dev"), behavior_ok=out.get("behavior") == exp["behavior"],
             top1=None, top3=None, fields_ok=None, fab=None, fab_why=[], nps_ok=None, cite_ok=None,
             latency_ms=out.get("latency_ms"), extra=out.get("extra") or {}, got_behavior=out.get("behavior"))
    scorable = [t for t in exp["tasks"] if t["acceptable_proc_ids"]]
    if exp["behavior"] == "answer" and scorable:
        used, t1, t3, fo = set(), [], [], []
        outs = out.get("tasks") or []
        for et in scorable:
            acc, hit1, hit3, mj = set(et["acceptable_proc_ids"]), None, None, None
            for j, ot in enumerate(outs):
                if j not in used and cands_of(ot)[:1] and cands_of(ot)[0] in acc:
                    hit1 = j; break
            if hit1 is None:
                for j, ot in enumerate(outs):
                    if j not in used and acc & set(cands_of(ot)[:3]):
                        hit3 = j; break
            mj = hit1 if hit1 is not None else hit3
            if mj is not None:
                used.add(mj)
            t1.append(hit1 is not None)
            t3.append(mj is not None)
            if mj is not None and outs[mj].get("fields") is None:
                fo.append(None)  # adapter không trích fields => không chấm
            else:
                fo.append(mj is not None and set(outs[mj].get("fields") or []) == set(et["fields"]))
        r["top1"], r["top3"] = all(t1), all(t3)
        r["fields_ok"] = None if (out.get("fields_supported") is False or all(x is None for x in fo)) else all(bool(x) for x in fo)
    elif exp["behavior"] == "answer" and not scorable and exp["tasks"] == []:
        pass  # chitchat: chỉ chấm hành vi
    r["rule_kind"], r["rule_ok"], r["rule_detail"] = score_rule(case, out, cands_of)
    ans = out.get("answer_text") or ""
    if ans:
        pids = {p for t in exp["tasks"] for p in t["acceptable_proc_ids"]}
        r["fab_why"] = fabricated(case, ans, pids)
        r["fab"] = bool(r["fab_why"])
        if exp["must_say_not_published"] and not has_overlay(pids):     # có overlay nhóm: trả lệ phí kèm nguồn thay vì "không công bố"
            r["nps_ok"] = bool(out.get("says_not_published", None) if "says_not_published" in out else NPS_RE.search(ans))
        if exp["citation_tokens"]:
            r["cite_ok"] = any(tk.lower() in ans.lower() for tk in exp["citation_tokens"])
    return r


def pct(xs):
    xs = [x for x in xs if x is not None]
    return f"{100 * sum(xs) / len(xs):.0f}% ({sum(xs)}/{len(xs)})" if xs else "-"


def pctl(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return "-"
    return f"{xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]:.0f}"


def table(results):
    by = defaultdict(list)
    for r in results:
        by[r["category"]].append(r)
    rows = ["| Hạng mục | n | top-1 | top-3 | đúng fields | đúng hành vi | bịa số | nói 'không công bố' | trích nguồn | is_strong sai | p50 ms | p95 ms |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]

    def row(name, rs):
        strong = [bool(r["extra"].get("is_strong")) for r in rs if "is_strong" in r["extra"]]
        return (f"| {name} | {len(rs)} | {pct([r['top1'] for r in rs])} | {pct([r['top3'] for r in rs])} | {pct([r['fields_ok'] for r in rs])} | "
                f"{pct([r['behavior_ok'] for r in rs])} | {pct([r['fab'] for r in rs])} | {pct([r['nps_ok'] for r in rs])} | "
                f"{pct([r['cite_ok'] for r in rs])} | {pct(strong) if strong and name in ('out_of_scope', 'hallucination_unsupported') else '-'} | "
                f"{pctl([r['latency_ms'] for r in rs], .5)} | {pctl([r['latency_ms'] for r in rs], .95)} |")
    for cat in sorted(by):
        rows.append(row(cat, by[cat]))
    rows.append(row("**TỔNG**", results))
    return "\n".join(rows)


def rate(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


def summary(results):
    """Số tổng cho 1 split: top-1, top-3, hành vi, bịa số, và 4 loại chấm luật."""
    d = {"n": len(results), "top1": rate([r["top1"] for r in results]), "top3": rate([r["top3"] for r in results]),
         "behavior": rate([r["behavior_ok"] for r in results]), "fab": rate([r["fab"] for r in results])}
    for k in ("condition", "compare", "negation", "order"):
        d[k] = rate([r["rule_ok"] for r in results if r.get("rule_kind") == k])
    return d


def fmt(v):
    return "-" if v is None else f"{100 * v:.1f}%"


def split_report(results):
    sm = {sp: summary([r for r in results if r["split"] == sp]) for sp in ("dev", "holdout", "holdout2", "holdout3")}
    hk = next((k for k in ("holdout3", "holdout2") if sm[k]["n"]), "holdout")
    rows = [f"| Số đo | DEV | {hk.upper()} | chênh ({hk.upper()} - DEV, điểm %) |", "|---|---|---|---|"]
    rows.append(f"| n câu | {sm['dev']['n']} | {sm[hk]['n']} | |")
    for k, lab in (("top1", "top-1"), ("top3", "top-3"), ("behavior", "đúng hành vi"), ("fab", "bịa số (thấp tốt)"),
                   ("condition", "luật: điều kiện"), ("compare", "luật: so sánh"), ("negation", "luật: phủ định"), ("order", "luật: thứ tự")):
        a, b = sm["dev"][k], sm[hk][k]
        rows.append(f"| {lab} | {fmt(a)} | {fmt(b)} | {'-' if a is None or b is None else f'{100 * (b - a):+.1f}'} |")
    return "\n".join(rows), sm


# -------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="baseline_adapter:adapter")
    ap.add_argument("--name", default=None, help="tên file kết quả (mặc định: timestamp)")
    ap.add_argument("--category")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--split", choices=["dev", "holdout", "holdout2", "holdout3", "p16aside", "all"], default="all",
                    help="HOLDOUT chỉ nên chạy khi nghiệm thu, không dùng để tune")
    a = ap.parse_args()
    mod, fn = a.adapter.split(":")
    adapter = getattr(importlib.import_module(mod), fn)
    cases = [json.loads(l) for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8")]
    if a.split in ("holdout2", "holdout3"):   # bộ MÙ, tách file; không nằm trong "all" để khỏi bị tune
        cases = [json.loads(l) for l in open(os.path.join(HERE, "cases_h%s.jsonl" % a.split[-1]), encoding="utf-8")]
    elif a.split == "p16aside":   # bộ "để riêng" của Phase 16, tách file, không nằm trong "all"
        cases = [json.loads(l) for l in open(os.path.join(HERE, "cases_p16_aside.jsonl"), encoding="utf-8")]
    elif a.split != "all":
        cases = [c for c in cases if c.get("split", "dev") == a.split]
    if a.category:
        cases = [c for c in cases if c["category"] == a.category]
    if a.limit:
        cases = cases[:a.limit]
    results = []
    for c in cases:
        t0 = time.perf_counter()
        try:
            out = adapter(c["turns"]) or {}
        except Exception as e:  # adapter lỗi = ca fail, không dừng cả bộ
            out = {"tasks": [], "behavior": "error", "answer_text": "", "extra": {"error": repr(e)}}
        out.setdefault("latency_ms", (time.perf_counter() - t0) * 1000)
        res = score_case(c, out)
        res["question"] = c["turns"][-1]["text"]
        res["source"] = c.get("source")
        res["got_tasks"] = [{"cands": cands_of(t)[:3], "fields": t.get("fields")} for t in (out.get("tasks") or [])]
        res["answer_text"] = (out.get("answer_text") or "")[:600]
        results.append(res)
    md = {}
    for sp in ("dev", "holdout", "holdout2", "holdout3"):
        rs = [r for r in results if r["split"] == sp]
        if rs:
            md[sp] = table(rs)
            print(f"\n## {sp.upper()} ({len(rs)} câu)\n{md[sp]}")
    sr, sm = split_report(results)
    print(f"\n## DEV vs HOLDOUT\n{sr}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    name = a.name or time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(HERE, "results", f"{name}.json")
    json.dump({"adapter": a.adapter, "n": len(results), "table_md": md, "split_report_md": sr, "summary": sm, "cases": results},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nĐã ghi {path}")


if __name__ == "__main__":
    main()

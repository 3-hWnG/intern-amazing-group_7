"""Phase 27: bộ chấm RIÊNG cho bước sinh chữ (Answer Composer). Mỗi ca trong cases_composer.jsonl chạy hai lần: TẮT (llm=None, bản bằng code) và BẬT (Ollama qwen3:4b).
Chấm bằng LUẬT (không LLM): (a) đủ ý, (b) không sai số, (c) không đảo nghĩa có/không, (d) không bịa cơ quan/văn bản, (e) độ dài hợp lý.
In bảng bật/tắt, timeout, p50/p95, số ca bật TỆ hơn tắt; ghi results/composer_<name>.json; --sample ghi results/composer_sample20.md (20 ca, seed 27, để người chấm).
Chạy (cần Ollama): cd eval && PYTHONIOENCODING=utf-8 PYTHONPATH=<ROOT> python score_composer.py --name x [--sample] [--timeout 7]
Chỉ 1 worker, tuần tự; --limit N để thử nhanh. Tự nạp model (warm-up) trước khi đo trừ khi --no-warm."""
import argparse, json, os, random, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ap = argparse.ArgumentParser()
ap.add_argument("--name", default="composer"); ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--sample", action="store_true"); ap.add_argument("--timeout", type=float, default=0)
ap.add_argument("--no-warm", action="store_true")
args = ap.parse_args()
if args.timeout:
    os.environ["ANSWER_LLM_TIMEOUT"] = str(args.timeout)
from build_composer_set import run_case  # noqa: E402  (đặt sys.path)
from answer import answerer as A  # noqa: E402
from answer.verifier import _DOC, _CODE  # noqa: E402
from system3.data.textutil import fold  # noqa: E402
import run as R  # noqa: E402  (source_blob)

TIMEOUT = float(os.environ.get("ANSWER_LLM_TIMEOUT", "7.0"))


def text_of(a):
    return "\n\n".join(f"{b.get('title', '')}\n{b['text']}" + "".join(f"\n{s['label']} {s['url']}" for s in b.get("sources", [])) for b in a["blocks"])


def sections(a):
    """Các đoạn do bước sinh chữ phụ trách: đoạn 'Về điều kiện bạn nêu' và khối 'So sánh'."""
    out = []
    for b in a["blocks"]:
        if b.get("title") == "So sánh":
            out.append(b["text"])
        else:
            out += [p for p in b["text"].split("\n\n") if p.startswith("Về điều kiện bạn nêu")]
    return out


_ints = lambda s: {x.lstrip("0") or "0" for x in re.findall(r"\d+", s or "")}
AG = re.compile(r"\b(Sở|Bộ|Cục|Chi cục|Phòng|Ủy ban nhân dân|UBND|Công an|Tòa án|Kho bạc|Bảo hiểm xã hội|Văn phòng|Ban)\s+(\w+)")
POL = [("duoc", "khong duoc"), ("phai", "khong phai"), ("can", "khong can"), ("co", "khong co"), ("bat buoc", "khong bat buoc")]
tok = lambda s: {t for t in re.findall(r"[0-9a-z]+", fold(s)) if len(t) > 1}


def pos_neg(s, pos, neg):
    f = fold(s)
    return bool(re.search(rf"(?<!khong )\b{pos}\b", f)), bool(re.search(rf"\b{neg}\b", f))


def flip(point, source):
    """Ý đảo nghĩa so với câu nguồn gần nhất (trùng chữ >= 50%): có/không, được/không được... lệch cực."""
    pt = tok(point)
    best, bs = None, 0.0
    for sent in re.split(r"[.;\n]", source):
        sc = len(pt & tok(sent)) / max(len(pt), 1)
        if sc > bs:
            best, bs = sent, sc
    if best is None or bs < 0.5:
        return []
    out = []
    for pos, neg in POL:
        pp, pn = pos_neg(point, pos, neg)
        sp, sn = pos_neg(best, pos, neg)
        if (pn and not pp and sp and not sn) or (sn and not sp and pp and not pn):
            out.append(f"{pos}/{neg}")
    return out


def score(case, a, routed, question, pts, passages):
    """-> {tiêu chí: (đạt, lý do)}."""
    txt, secs = text_of(a), sections(a)
    body = "\n".join(b.get("title", "") + "\n" + b["text"] for b in a["blocks"])      # không gồm dòng nguồn (không do bước sinh chữ viết)
    sec = "\n".join(secs)
    pids = [t.procedure_id for t in routed.tasks if t.route == "direct"]
    blob = " ".join(R.source_blob(p) for p in pids)
    r = {}
    # (a) đủ ý
    if "compare" in case["triggers"] and not case["checks"] and not case.get("own_conditions") and len(pids) >= 2 and not any(t.conditions for t in routed.tasks):
        ok = all(len(tok(t.procedure_label) & tok(txt)) / max(len(tok(t.procedure_label)), 1) >= 0.6 for t in routed.tasks if t.route == "direct")
        r["a"] = (ok, "so sánh: nêu cả hai thủ tục")
    else:
        keys = [k for c in case["checks"] for k in c.get("keys", [])] + case.get("own_conditions", [])
        names = set().union(*[tok(t.procedure_label) for t in routed.tasks]) if routed.tasks else set()
        # điều kiện LIÊN QUAN = điều kiện planner rút ra mà chữ đặc trưng (ngoài tên thủ tục) có trong câu hỏi; planner hay gán nhầm mục điều kiện không do người dùng nêu
        conds = [c for t in routed.tasks for c in t.conditions if len((tok(c) - names) & tok(question)) / max(len(tok(c) - names), 1) >= 0.4]
        if not keys and not conds:
            r["a"] = (None, "không có điều kiện liên quan do người dùng nêu (n/a)")
        else:
            ok = any(fold(k) in fold(txt) for k in keys) or any(len(tok(c) & tok(sec)) / max(len(tok(c)), 1) >= 0.5 for c in conds)
            r["a"] = (ok, "thiếu ý của mục điều kiện liên quan")
    # (b) không sai số: số trong câu trả lời có trong nguồn thủ tục (hoặc câu hỏi)
    bad = _ints(body) - _ints(blob) - _ints(question)
    r["b"] = (not bad, "số lạ " + str(sorted(bad)[:5]))
    # (c) không đảo nghĩa (chỉ ý do LLM sinh; bản bằng code trích nguyên văn)
    pst = " ".join(p["text"] for p in passages)
    fl = [(p["text"][:60], f) for p in pts for f in [flip(p["text"], pst)] if f]
    r["c"] = (not fl, "đảo " + str(fl[:2]))
    # (d) không bịa cơ quan/văn bản
    fb = fold(blob + " " + question)
    miss = [m.group(0) for m in _DOC.finditer(fold(body)) if m.group(0) not in fb]
    miss += [c for c in _CODE.findall(body) if fold(c) not in fb]
    miss += [m.group(0) for m in AG.finditer(body) if fold(m.group(1) + " " + m.group(2)) not in fb]
    r["d"] = (not miss, "lạ " + str(miss[:4]))
    # (e) độ dài hợp lý: phần sinh chữ <= 1000 ký tự, mỗi gạch đầu dòng <= 300 (không tính "(theo: nguồn)")
    strip = lambda l: re.sub(r"\s*\(theo:[^)]*\)\s*$", "", l)
    lines = [strip(l) for s in secs for l in s.split("\n")]
    r["e"] = (sum(map(len, lines)) <= 1000 and all(len(l) <= 300 for l in lines), f"dài {sum(map(len, lines))}, ý dài nhất {max(map(len, lines), default=0)}")
    return r


def main():
    cases = [json.loads(l) for l in open(os.path.join(HERE, "cases_composer.jsonl"), encoding="utf-8")]
    if args.limit:
        cases = cases[:args.limit]
    from core.llm import chat_json, warm_up
    if not args.no_warm:
        os.environ["S3_NO_WARMUP"] = "0"
        warm_up()
    calls = []

    def timed(system, user, schema=None, timeout=None, **kw):
        t0 = time.perf_counter()
        err = None
        try:
            return chat_json(system, user, schema=schema, timeout=timeout, **kw)
        except Exception as e:
            err = type(e).__name__ + ": " + str(e)[:80]
            raise
        finally:
            calls.append({"ms": (time.perf_counter() - t0) * 1000, "err": err, "in": len(user)})

    timed.__module__ = "core.llm"      # để llm_answer._ready() coi hàm bọc này là client thật (kiểm model đã nạp)
    rec = []
    orig = A.compose

    def wrap(llm, passages, request, question="", issues=None):
        iss = []
        n0 = len(calls)
        pts = orig(llm, passages, request, question, iss)
        rec.append({"passages": [p for p in passages if p["text"].strip()], "request": request, "pts": pts, "issues": iss, "call": calls[n0] if len(calls) > n0 else None})
        if issues is not None:
            issues.extend(iss)
        return pts
    A.compose = wrap
    rows = []
    for c in cases:
        t0 = time.perf_counter()
        a0, r0, q = run_case(c["turns"], None)
        off_ms = (time.perf_counter() - t0) * 1000
        rec.clear()
        t0 = time.perf_counter()
        a1, r1, _ = run_case(c["turns"], timed)
        on_ms = (time.perf_counter() - t0) * 1000
        pts = [p for x in rec for p in x["pts"]]
        pas = [p for x in rec for p in x["passages"]]
        s0, s1 = score(c, a0, r0, q, [], []), score(c, a1, r1, q, pts, pas)
        worse = [k for k in "abcde" if s0[k][0] is not False and s1[k][0] is False and s0[k][0]]
        better = [k for k in "abcde" if s1[k][0] and s0[k][0] is False]
        rejected = sum(1 for x in rec for i in x["issues"] if i.startswith("bỏ ý"))
        calls_c = [x["call"] for x in rec if x["call"]]
        rows.append({"id": c["id"], "src": c["src"], "q": c["turns"][-1]["text"], "triggers": c["triggers"],
                     "off": {k: v[0] for k, v in s0.items()}, "on": {k: v[0] for k, v in s1.items()},
                     "on_why": {k: v[1] for k, v in s1.items() if v[0] is False}, "off_why": {k: v[1] for k, v in s0.items() if v[0] is False},
                     "worse": worse, "better": better, "changed": text_of(a0) != text_of(a1),
                     "kept": len(pts), "rejected": rejected, "llm_err": [x["err"] for x in calls_c if x["err"]],
                     "llm_ms": [round(x["ms"]) for x in calls_c], "off_ms": round(off_ms), "on_ms": round(on_ms),
                     "off_sec": sections(a0), "on_sec": sections(a1), "passages": [{"label": p["label"], "text": p["text"][:700]} for p in pas],
                     "issues": [i for x in rec for i in x["issues"]]})
        print(f"{c['id']:24s} {'/'.join(c['triggers']):10s} kept={len(pts)} rej={rejected} err={len(rows[-1]['llm_err'])} on={on_ms:6.0f}ms worse={worse} better={better}", flush=True)
    A.compose = orig
    summarize(rows)
    json.dump({"timeout": TIMEOUT, "rows": rows}, open(os.path.join(HERE, "results", f"composer_{args.name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if args.sample:
        sample(rows)


def pc(x):
    return f"{x[0]}/{x[1]} ({100 * x[0] / max(x[1], 1):.0f}%)"


def summarize(rows):
    n = len(rows)
    print(f"\n## Bật vs tắt trên {n} ca (timeout {TIMEOUT:g}s)\n\n| tiêu chí | TẮT | BẬT |\n|---|---|---|")
    names = {"a": "(a) đủ ý", "b": "(b) không sai số", "c": "(c) không đảo nghĩa", "d": "(d) không bịa cơ quan/văn bản", "e": "(e) độ dài hợp lý"}
    for k in "abcde":
        m = [r for r in rows if r["on"][k] is not None]
        print(f"| {names[k]} (n={len(m)}) | {pc((sum(bool(r['off'][k]) for r in m), len(m)))} | {pc((sum(bool(r['on'][k]) for r in m), len(m)))} |")
    allok = lambda r, m: all(v is not False for v in r[m].values())
    print(f"| đạt cả 5 | {pc((sum(allok(r, 'off') for r in rows), n))} | {pc((sum(allok(r, 'on') for r in rows), n))} |")
    calls = [m for r in rows for m in r["llm_ms"]]
    errs = [e for r in rows for e in r["llm_err"]]
    pctl = lambda v, q: sorted(v)[min(len(v) - 1, int(q * len(v)))] if v else 0
    tos = [e for e in errs if "imeout" in e or "timed out" in e.lower()]
    print(f"\nLượt gọi LLM: {len(calls)}; lỗi {pc((len(errs), len(calls)))} (trong đó timeout {len(tos)}); p50 {pctl(calls, .5)} ms, p95 {pctl(calls, .95)} ms, max {max(calls, default=0)} ms")
    for e in sorted(set(errs)):
        print("  lỗi:", e, errs.count(e))
    kept, rej = sum(r["kept"] for r in rows), sum(r["rejected"] for r in rows)
    print(f"Ý do LLM đề xuất: {kept + rej}; verifier loại {rej} ({100 * rej / max(kept + rej, 1):.0f}%); giữ {kept}. Ca bật ra khác bản tắt: {sum(r['changed'] for r in rows)}/{n}")
    on_t, off_t = [r["on_ms"] for r in rows], [r["off_ms"] for r in rows]
    print(f"Tổng thời gian trả lời cả ca (không gồm hàng đợi): TẮT p50 {pctl(off_t, .5)} p95 {pctl(off_t, .95)} ms | BẬT p50 {pctl(on_t, .5)} p95 {pctl(on_t, .95)} max {max(on_t)} ms")
    w = [r for r in rows if r["worse"]]
    print(f"Ca BẬT TỆ hơn TẮT (đạt ở tắt, trượt ở bật): {len(w)}; ca bật TỐT hơn: {sum(1 for r in rows if r['better'])}")
    for r in w:
        print("  TỆ", r["id"], r["worse"], {k: r["on_why"].get(k) for k in r["worse"]})
    for kind in ("condition", "compare"):
        sub = [r for r in rows if kind in r["triggers"]]
        print(f"  [{kind}] {len(sub)} ca: đạt cả 5 TẮT {sum(allok(r, 'off') for r in sub)}, BẬT {sum(allok(r, 'on') for r in sub)}; tệ hơn {sum(1 for r in sub if r['worse'])}; có ý giữ {sum(1 for r in sub if r['kept'])}")
    for src in ("composer", "dev", "ctx"):
        sub = [r for r in rows if r["src"].startswith(src)]
        if sub:
            print(f"  [nguồn {src}] {len(sub)} ca: có ý LLM giữ {sum(1 for r in sub if r['kept'])}, timeout/lỗi {sum(1 for r in sub if r['llm_err'])}, tệ hơn {sum(1 for r in sub if r['worse'])}")


def sample(rows):
    pick = random.Random(27).sample(rows, min(20, len(rows)))
    L = ["# Mẫu 20 ca để người chấm (Answer Composer, Phase 27)", "",
         "Chọn ngẫu nhiên có seed cố định (`random.Random(27).sample`) từ `cases_composer.jsonl`; sinh bởi `score_composer.py --sample`. **Chưa có điểm nào**: người chấm tự điền.",
         "Cách chấm gợi ý: mỗi ca cho 1 điểm cho TẮT và 1 cho BẬT (1 = sai/đáng ngờ, 2 = dùng được, 3 = rõ và đúng) và ghi bên nào tốt hơn. 'Nguồn' là các đoạn dữ liệu thật đưa cho LLM.", ""]
    for i, r in enumerate(pick, 1):
        L += [f"## {i}. {r['id']} ({r['src']}, kích hoạt: {', '.join(r['triggers'])})", "", f"**Câu hỏi:** {r['q']}", "", "**Bản TẮT (code):**", ""]
        L += [("> " + s.replace("\n", "\n> ")) for s in r["off_sec"]] + (["> (không có phần so sánh/điều kiện riêng; chỉ các khối theo từng thủ tục)"] if not r["off_sec"] else [])
        L += ["", "**Bản BẬT (LLM):**", ""]
        L += [("> " + s.replace("\n", "\n> ")) for s in r["on_sec"]] + (["> (không có)"] if not r["on_sec"] else [])
        L += ["", f"_Ghi chú máy: bản bật {'khác' if r['changed'] else 'GIỐNG'} bản tắt; ý giữ {r['kept']}, ý bị loại {r['rejected']}, lỗi LLM {r['llm_err'] or 'không'}._", "", "<details><summary>Nguồn đưa cho LLM</summary>", ""]
        L += [f"- **{p['label']}**: {p['text'][:400].replace(chr(10), ' ')}" for p in r["passages"]]
        L += ["", "</details>", "", "Điểm người chấm: TẮT __ / BẬT __ ; tốt hơn: ____ ; ghi chú: ____", ""]
    open(os.path.join(HERE, "results", "composer_sample20.md"), "w", encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    main()

"""Chạy golden set (eval/golden/<domain>.jsonl) qua adapter System 3 và in bảng theo status / nguồn / loại.
Chạy: PYTHONIOENCODING=utf-8 S3_USE_LLM=0 python run_server.py eval/run_golden.py [domain] [--by status|source|type]   (mặc định thu-tuc, by status)
Ghi eval/results/golden_<domain>.json. Chấm: hành vi đúng; ca answer có đáp án: top-1 (task đầu) và top-3 (ứng viên) nằm trong tập đáp án; đúng trường (ca một thủ tục có
danh sách trường kỳ vọng: tập trường trả về = tập kỳ vọng, bộ blind cũ gọi documents/fee/place/time thì đổi sang components/fees/address/processing_time; "conditions" không đổi nên luôn tính lệch); đủ ý (ca nhiều thủ tục: mọi thủ tục kỳ vọng đều có mặt).
Số chính thức là hàng status=blind (không tune). Số dev luôn cao hơn."""
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dom = args[0] if args else "thu-tuc"
by = sys.argv[sys.argv.index("--by") + 1] if "--by" in sys.argv else "status"
path = os.path.join(HERE, "golden", dom + ".jsonl")
cases = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
if not cases:
    sys.exit(f"{dom}: golden set rỗng (chưa có bộ có đáp án)")

ALIAS = {"documents": "components", "fee": "fees", "place": "address", "time": "processing_time"}    # tên trường của các bộ blind cũ
rows = []
if any(c["expected"].get("list_domain") for c in cases):
    from orchestrator import _list_request   # adapter không đi qua orchestrator nên ý "liệt kê" phải gọi trực tiếp
    from system3.data import api as _api
    _conn = _api.connect()


def list_row(c):
    txt = _list_request(c["question"])
    names = [l.split(". ", 1)[1] for l in (txt or "").splitlines() if l[:1].isdigit() and ". " in l]
    ok = [bool(_conn.execute("select 1 from procedures where name=? and domain like ?", (n, "%" + c["expected"]["list_domain"] + "%")).fetchone()) for n in names]
    return dict(id=c["id"], status=c["status"], source=c["source"], type=c["type"], beh="answer", got="answer" if txt else "none", beh_ok=bool(names),
                scored=False, multi=False, all_ok=False, fields_chk=False, fields_ok=False, top1=False, top3=False, ms=None,
                dom_prec=(sum(ok) / len(ok)) if ok else 0.0)


for c in cases:
    if c["expected"].get("list_domain"):
        rows.append(list_row(c))
        continue
    out = answer_adapter.adapter(c["turns"])
    exp = c["expected"]
    ids = {p for t in exp["tasks"] for p in t["proc_ids"]}
    tops = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
    cands = [x for t in out["tasks"] for x in t.get("candidates", [])]
    scored = exp["behavior"] == "answer" and bool(ids)
    multi = scored and len(exp["tasks"]) >= 2
    want = {ALIAS.get(f, f) for f in exp["tasks"][0]["fields"]} if exp["tasks"] and not multi else set()
    got_f = {ALIAS.get(f, f) for f in ((out["tasks"] or [{}])[0].get("fields") or [])} if out["tasks"] else set()
    all_ok = multi and all(any(p in tops for p in t["proc_ids"]) for t in exp["tasks"])
    rows.append(dict(id=c["id"], status=c["status"], source=c["source"], type=c["type"], beh=exp["behavior"], got=out["behavior"],
                     beh_ok=out["behavior"] == exp["behavior"], scored=scored,
                     multi=multi, all_ok=all_ok, fields_chk=scored and not multi and bool(want), fields_ok=bool(want) and got_f == want,
                     top1=scored and bool(tops) and tops[0] in ids, top3=scored and any(x in ids for x in cands[:3]),
                     ms=out.get("latency_ms")))


def table(key):
    g = collections.defaultdict(list)
    for r in rows:
        g[r[key]].append(r)
    L = [f"| {key} | số ca | hành vi đúng | top-1 | top-3 | đúng trường | đủ ý (nhiều thủ tục) | hỏi lại đúng | từ chối đúng |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in sorted(g.items()):
        s = [r for r in v if r["scored"]]
        cl = [r for r in v if r["beh"] == "clarify"]
        ap = [r for r in v if r["beh"] == "apologize"]
        pc = lambda a, b: f"{a}/{b} ({a / b:.0%})" if b else "-"
        fc = [r for r in v if r["fields_chk"]]
        mu = [r for r in v if r["multi"]]
        L.append(f"| {k} | {len(v)} | {pc(sum(r['beh_ok'] for r in v), len(v))} | {pc(sum(r['top1'] for r in s), len(s))} | "
                 f"{pc(sum(r['top3'] for r in s), len(s))} | {pc(sum(r['fields_ok'] for r in fc), len(fc))} | {pc(sum(r['all_ok'] for r in mu), len(mu))} | {pc(sum(r['beh_ok'] for r in cl), len(cl))} | {pc(sum(r['beh_ok'] for r in ap), len(ap))} |")
    return "\n".join(L)


md = table(by)
lr = [x for x in rows if "dom_prec" in x]
if lr:
    md += f"\n\nliệt kê: {sum(x['beh_ok'] for x in lr)}/{len(lr)} câu có trả danh sách; trung bình {sum(x['dom_prec'] for x in lr) / len(lr):.0%} mục trong danh sách đúng lĩnh vực được hỏi."
print(md)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump({"domain": dom, "by": by, "table_md": md, "rows": rows}, open(os.path.join(HERE, "results", f"golden_{dom}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

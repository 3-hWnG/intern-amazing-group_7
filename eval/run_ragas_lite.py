"""Mục 3.5 của kế hoạch: 4 chỉ số kiểu RAGAS (faithfulness, answer relevancy, context precision, context recall) với giám khảo là
Ollama local (cùng model với System 3). KHÔNG dùng thư viện ragas (kéo LangChain, cần cấu hình giám khảo riêng): viết lại ngắn từ định nghĩa.
Chạy:  PYTHONIOENCODING=utf-8 python run_server.py eval/run_ragas_lite.py [--n 30] [--seed 5] [--name x]   (cần Ollama; ~10 phút / 30 ca)
  Hai pha để không phải đổi model GPU giữa từng ca (mỗi lần đổi ~7 s): `--phase build` sinh câu trả lời bằng model của hệ thống và ghi
  eval/results/ragas_dataset_<name>.json; `--phase score` chấm bằng `--judge-model` (vd qwen2.5:7b). Mặc định `--phase both` (như cũ).
  `--blind K`: lấy thêm K ca từ bộ golden status=blind (câu hỏi gần thật hơn bộ khuôn). Chỉ số `num_ok`: mọi số >= 3 chữ số trong câu trả lời có trong ngữ cảnh (luật, không cần LLM).

Khác RAGAS gốc (phải ghi vào báo cáo):
  - faithfulness: giám khảo tách câu trả lời thành các ý rồi đánh dấu từng ý có/không nằm trong ngữ cảnh (RAGAS cũng làm vậy).
  - answer relevancy: giám khảo cho 0/1/2 xem câu trả lời có trả lời đúng câu hỏi không (RAGAS gốc sinh câu hỏi ngược rồi so embedding).
  - context precision: tỉ lệ đoạn ngữ cảnh liên quan tới câu hỏi, KHÔNG có trọng số theo thứ hạng.
  - context recall: không có câu trả lời mẫu, nên "tham chiếu" = nội dung các trường đáp án trong DB (expected.fields của golden set); giám khảo
    tách tham chiếu thành các ý và kiểm từng ý có trong ngữ cảnh hệ thống lấy ra. Đo truy xuất + chọn trường, không đo chữ viết của câu trả lời.
  - ngữ cảnh = các đoạn field_chunks của thủ tục hệ thống chọn (đúng thứ Answerer dùng), không phải toàn bộ prompt.
Kiểm giám khảo bằng đối chứng âm trên cùng ca: (a) chèn một ý bịa vào câu trả lời -> faithfulness phải giảm; (b) ghép câu trả lời với câu hỏi
của ca khác -> relevancy phải giảm. Nếu hai đối chứng không tách rõ thì điểm của giám khảo không dùng được."""
import argparse, json, os, random, re, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402
from core.llm import chat_json  # noqa: E402
from system3.data import api  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=30)
ap.add_argument("--seed", type=int, default=5)
ap.add_argument("--name", default="x")
ap.add_argument("--phase", choices=("build", "score", "both"), default="both")
ap.add_argument("--judge-model", default=None, help="model giám khảo (mặc định: model của hệ thống)")
ap.add_argument("--blind", type=int, default=0, help="số ca lấy thêm từ golden status=blind")
a = ap.parse_args()

CTX_MAX = 3500      # ký tự ngữ cảnh đưa cho giám khảo (model 4B, tránh tràn)
FAKE = "Thủ tục này được miễn phí hoàn toàn và được giải quyết ngay trong 1 giờ tại bất kỳ cơ quan nào."
conn = api.connect()
SYS = "Bạn là giám khảo chấm hệ thống hỏi đáp thủ tục hành chính. Chỉ dựa vào văn bản được đưa, không dùng kiến thức ngoài. Trả lời đúng JSON yêu cầu."


def J(user, props):
    schema = {"type": "object", "properties": props, "required": list(props)}
    try:    # một lần gọi hỏng/quá hạn chỉ làm ca đó thành "không chấm được" (None), không làm sập cả lượt chạy dài
        return chat_json(SYS, user, schema, think=False, timeout=600, **({"model": a.judge_model} if a.judge_model else {}))
    except Exception as e:
        print("  giám khảo lỗi:", str(e)[:120], flush=True)
        return {}


def faithfulness(ctx, ans):
    r = J(f"NGỮ CẢNH:\n{ctx}\n\nCÂU TRẢ LỜI:\n{ans}\n\nTách câu trả lời thành các ý nhỏ (mỗi ý một khẳng định). Với từng ý, supported=true nếu NGỮ CẢNH nói rõ ý đó, "
          "ngược lại false. Bỏ qua lời chào, lời mời hỏi thêm.",
          {"claims": {"type": "array", "items": {"type": "object", "properties": {"claim": {"type": "string"}, "supported": {"type": "boolean"}},
                                              "required": ["claim", "supported"]}}})
    cl = r.get("claims") or []
    return (sum(1 for c in cl if c.get("supported")) / len(cl)) if cl else None


def relevancy(q, ans):
    r = J(f"CÂU HỎI: {q}\n\nCÂU TRẢ LỜI:\n{ans}\n\nChấm score: 2 = trả lời đúng và đủ điều được hỏi; 1 = trả lời một phần hoặc lan man; 0 = không trả lời điều được hỏi.",
          {"score": {"type": "integer", "enum": [0, 1, 2]}})
    return (r["score"] / 2) if "score" in r else None


def precision(q, chunks):
    body = "\n".join(f"[{i + 1}] {c[:600]}" for i, c in enumerate(chunks))
    r = J(f"CÂU HỎI: {q}\n\nCÁC ĐOẠN NGỮ CẢNH:\n{body}\n\nVới từng đoạn, relevant=true nếu đoạn có thông tin giúp trả lời câu hỏi, ngược lại false. Trả đúng {len(chunks)} giá trị theo thứ tự.",
          {"relevant": {"type": "array", "items": {"type": "boolean"}}})
    v = (r.get("relevant") or [])[:len(chunks)]
    return (sum(v) / len(v)) if v else None


def recall(ref, ctx):
    r = J(f"THAM CHIẾU (thông tin đúng cần có):\n{ref}\n\nNGỮ CẢNH HỆ THỐNG LẤY RA:\n{ctx}\n\nTách THAM CHIẾU thành các ý nhỏ. Với từng ý, in_context=true nếu NGỮ CẢNH có ý đó, ngược lại false.",
          {"statements": {"type": "array", "items": {"type": "object", "properties": {"s": {"type": "string"}, "in_context": {"type": "boolean"}},
                                                    "required": ["s", "in_context"]}}})
    st = r.get("statements") or []
    return (sum(1 for s in st if s.get("in_context")) / len(st)) if st else None


def chunks_of(pid, fields):
    names = list(dict.fromkeys(fields)) or ["explanation", "components", "fees", "processing_time"]
    return [c["text"].strip() for c in api.fields(conn, pid, names) if c["status"] == "present" and c["text"].strip()]


def pool():
    rows = []
    gold = {}                                 # đáp án mẫu của ca composer nằm ở bộ gốc (theo id); ca tự soạn không có thì không chấm recall
    for fn in ("cases.jsonl", "cases_ctx.jsonl"):
        for l in open(os.path.join(HERE, fn), encoding="utf-8"):
            g = json.loads(l)
            gold[g["id"]] = g["expected"]
    for l in open(os.path.join(HERE, "cases_composer.jsonl"), encoding="utf-8"):
        c = json.loads(l)
        rows.append(dict(c, src="composer", expected=gold.get(c["id"]) or dict(tasks=[])))
    for l in open(os.path.join(HERE, "golden", "template_thu-tuc.jsonl"), encoding="utf-8"):
        c = json.loads(l)
        if c["type"] in ("components", "fees", "time", "steps", "explain", "multi_field", "legal") and len(c["expected"]["tasks"]) == 1:
            rows.append(dict(id=c["id"], turns=c["turns"], src="template", expected=dict(behavior="answer", tasks=[dict(acceptable_proc_ids=c["expected"]["tasks"][0]["proc_ids"], fields=c["expected"]["tasks"][0]["fields"])])))
    return rows


ALIAS = {"documents": "components", "fee": "fees", "place": "address", "time": "processing_time"}


def blind_pool():
    rows = []
    for l in open(os.path.join(HERE, "golden", "thu-tuc.jsonl"), encoding="utf-8"):
        c = json.loads(l)
        e = c["expected"]
        if c["status"] == "blind" and e["behavior"] == "answer" and len(e["tasks"]) == 1 and e["tasks"][0]["proc_ids"] and e["tasks"][0]["fields"]:
            f = [ALIAS.get(x, x) for x in e["tasks"][0]["fields"]]
            rows.append(dict(id=c["id"], turns=c["turns"], src="blind", expected=dict(behavior="answer", tasks=[dict(acceptable_proc_ids=e["tasks"][0]["proc_ids"], fields=f)])))
    return rows


def numbers_ok(ans, ctx):
    """Luật: mọi số tiền / số ngày / số giờ trong câu trả lời (số đi kèm đồng, đ, ngày, giờ, tháng) có trong ngữ cảnh, bỏ dấu chấm/phẩy hàng nghìn.
    Không xét mã thủ tục, năm, số văn bản (nằm ở phần căn cứ pháp lý, không nằm trong ngữ cảnh trường đã chọn nên cho âm tính giả)."""
    norm = lambda t: re.sub(r"(?<=\d)[.,](?=\d)", "", t)
    unit = r"(?:đồng|đ|vnđ|vnd|ngày|giờ|tháng)"
    have = set(re.findall(r"\d+", norm(ctx)))
    return all(n in have for n in re.findall(r"(\d+)\s*" + unit, norm(ans), flags=re.I))


DS = os.path.join(HERE, "results", f"ragas_dataset_{a.name}.json")


def build():
    """Pha 1: chọn ca, chạy hệ thống, ghi câu hỏi + câu trả lời + ngữ cảnh + tham chiếu. Dùng model của hệ thống (không đổi model giữa chừng)."""
    rng = random.Random(a.seed)
    P = pool()
    comp = [c for c in P if c["src"] == "composer"]
    tpl = [c for c in P if c["src"] == "template"]
    bl = rng.sample(blind_pool(), a.blind) if a.blind else []
    rest = a.n - len(bl)
    pick = rng.sample(comp, min(rest // 2, len(comp))) + rng.sample(tpl, min(rest - rest // 2, len(tpl))) + bl
    data = []
    for i, c in enumerate(pick):
        q = c["turns"][-1]["text"] if c["turns"][-1]["role"] == "user" else c["turns"][-2]["text"]
        out = answer_adapter.adapter(c["turns"])
        exp = c["expected"]["tasks"]
        if out["behavior"] != "answer" or not out["tasks"]:
            print(f"[{i + 1}/{len(pick)}] bỏ {c['id']}: hành vi {out['behavior']}", flush=True)
            continue
        ctx_chunks, ref_chunks = [], []
        for t in out["tasks"]:
            ctx_chunks += chunks_of(t["proc_id"], t.get("fields") or [f for e in exp for f in (e.get("fields") or [])])
        for e in [e for e in exp if e.get("acceptable_proc_ids")]:
            ref_chunks += chunks_of(e["acceptable_proc_ids"][0], e.get("fields") or [])
        data.append(dict(id=c["id"], src=c["src"], q=q, ans=out["answer_text"], ctx_chunks=ctx_chunks, ref_chunks=ref_chunks))
        print(f"[{i + 1}/{len(pick)}] {c['id']:24s} ctx={len(ctx_chunks)} ans={len(out['answer_text'])} ký tự", flush=True)
    os.makedirs(os.path.dirname(DS), exist_ok=True)
    json.dump({"seed": a.seed, "n": len(data), "cases": data}, open(DS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ghi {DS}: {len(data)} ca", flush=True)


def score():
    """Pha 2: chấm từng ca bằng giám khảo (--judge-model) + hai đối chứng âm + kiểm số theo luật."""
    data = json.load(open(DS, encoding="utf-8"))["cases"]
    part = DS.replace("ragas_dataset_", "ragas_partial_").replace(".json", ".jsonl")    # chấm xong ca nào ghi ngay, chạy lại thì bỏ qua ca đã xong
    done = {}
    if os.path.exists(part):
        for l in open(part, encoding="utf-8"):
            r = json.loads(l)
            done[r["id"]] = r
    rows = []
    for i, d in enumerate(data):
        t0 = time.time()
        if d["id"] in done:
            rows.append(done[d["id"]])
            continue
        ctx = "\n---\n".join(d["ctx_chunks"])[:CTX_MAX]
        ref = "\n---\n".join(d["ref_chunks"])[:CTX_MAX]
        ans, q = d["ans"], d["q"]
        r = dict(id=d["id"], src=d["src"], q=q, answer_len=len(ans), n_ctx=len(d["ctx_chunks"]), num_ok=numbers_ok(ans, ctx),
                 faith=faithfulness(ctx, ans), rel=relevancy(q, ans), prec=precision(q, d["ctx_chunks"]) if d["ctx_chunks"] else None,
                 rec=recall(ref, ctx) if ref else None, faith_neg=faithfulness(ctx, ans + "\n" + FAKE))
        r["_ans"] = ans
        rows.append(r)
        open(part, "a", encoding="utf-8").write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[{i + 1}/{len(data)}] {d['id']:24s} faith={r['faith']} rel={r['rel']} prec={r['prec']} rec={r['rec']} faith_neg={r['faith_neg']}  ({time.time() - t0:.0f}s)", flush=True)
    for i, r in enumerate(rows):                          # đối chứng âm (b): ghép câu trả lời với câu hỏi của ca khác
        other = rows[(i + len(rows) // 2) % len(rows)]
        r["rel_neg"] = relevancy(other["q"], r["_ans"]) if len(rows) > 1 else None
    for r in rows:
        r.pop("_ans")
    m = lambda k, rs=rows: (statistics.mean(x[k] for x in rs if x.get(k) is not None) if any(x.get(k) is not None for x in rs) else None)
    n_scored = lambda k, rs=rows: f"{sum(x.get(k) is not None for x in rs)}/{len(rs)}"
    summ = {}
    for name, rs in (("all", rows),) + tuple((s_, [r for r in rows if r["src"] == s_]) for s_ in ("composer", "template", "blind")):
        if not rs:
            continue
        summ[name] = dict(n=len(rs), **{k: m(k, rs) for k in ("faith", "rel", "prec", "rec", "faith_neg", "rel_neg")},
                          scored={k: n_scored(k, rs) for k in ("faith", "rel", "prec", "rec")},
                          num_ok=sum(1 for x in rs if x["num_ok"]) / len(rs))
        print(name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in summ[name].items()}, flush=True)
    # đối chứng: giám khảo có bắt được ý bịa cài sẵn / câu trả lời lạc đề không
    fp = [r for r in rows if r["faith"] is not None and r["faith_neg"] is not None]
    rp = [r for r in rows if r["rel"] and r["rel_neg"] is not None]
    ctrl = dict(planted_claim_caught=f"{sum(r['faith_neg'] < r['faith'] for r in fp)}/{len(fp)}",
                mismatched_answer_caught=f"{sum(r['rel_neg'] < r['rel'] for r in rp)}/{len(rp)}",
                rel_zero_on_correct=f"{sum(r['rel'] == 0 for r in rows if r['rel'] is not None)}/{sum(r['rel'] is not None for r in rows)}")
    print("đối chứng:", ctrl, flush=True)
    json.dump({"summary": summ, "controls": ctrl, "judge": a.judge_model or "model hệ thống", "rows": rows, "seed": a.seed},
              open(os.path.join(HERE, "results", f"ragas_lite_{a.name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if a.phase in ("build", "both"):
    build()
if a.phase in ("score", "both"):
    score()

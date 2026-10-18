"""G4.1 (P11): thử các tín hiệu "nên hỏi lại" trên dev (golden) + cases_p30 — KHÔNG dùng bộ mù.
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> S3_USE_LLM=0 python run_server.py eval/clarify_signals.py   (reranker chạy trên GPU nếu có)
Với mỗi câu một lượt: hành vi hiện tại của bộ luật, top-5 ứng viên, điểm reranker (câu hỏi x tên thủ tục), "độ rộng cụm chính"
(cụm terms của bộ luật xuất hiện liền trong tên bao nhiêu thủ tục / bao nhiêu họ). In bảng được/mất khi thêm từng luật:
  A. reranker: điểm cao nhất < S, chênh hạng 1-2 < M, hai bản đầu khác họ  -> hỏi lại
  B. độ rộng: cụm <= T chữ, khớp >= K thủ tục thuộc >= H họ, không trùng đúng tên thủ tục nào -> hỏi lại
"+n" = ca cần hỏi lại được sửa đúng; "-n" = ca cần trả lời bị đổi sang hỏi lại (làm sai). Chọn trên dev + p30-tune, kiểm trên p30-held/fresh.
Kết quả 18/10 (bản 3): cả A và B đều lỗ ròng trên bộ chọn ngưỡng -> G4.1 không đưa luật nào vào (xem docs/KE_HOACH_THUC_THI_2026-10-19.md)."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from retrieval.query import understand, _fold  # noqa: E402
from system3.data import api  # noqa: E402

conn = api.connect()
have = {r[0] for r in conn.execute("SELECT proc_id FROM procedures WHERE status='active'")}
names = {r[0]: r[1] for r in conn.execute("SELECT proc_id, name FROM procedures WHERE status='active'")}
folded = {p: " " + re.sub(r"\s+", " ", _fold(n)) + " " for p, n in names.items()}
syn = {r[0]: r[1] for r in conn.execute("SELECT raw_term, canonical_keyword FROM synonyms")}


def head(pid):
    f = api.family_of(conn, pid)
    return f["head"] if f else pid


heads = {p: head(p) for p in names}
try:
    from system3.system4.server.search import rerank_pairs
except Exception:   # chạy không có System 4: bỏ tín hiệu A
    rerank_pairs = lambda pairs: None   # noqa: E731

cases = []
for l in open(os.path.join(HERE, "golden", "thu-tuc.jsonl"), encoding="utf-8"):
    c = json.loads(l) if l.strip() else None
    if c and c["status"] == "dev" and not c["expected"].get("list_domain"):
        us = [t for t in c["turns"] if t["role"] == "user" and t.get("text")]
        if len(c["turns"]) == 1 and us:
            cases.append(("dev", us[0]["text"], c["expected"]["behavior"]))
for l in open(os.path.join(HERE, "cases_p30.jsonl"), encoding="utf-8"):
    if l.strip():
        c = json.loads(l)
        cases.append(("p30-" + c["split"], c["question"], c["expected"]["behavior"]))

rows = []
for st, q, exp in cases:
    pc = pre_check(q)
    p = make_plan([{"role": "user", "text": pc["text"]}])
    r = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
    t0 = p.tasks[0] if p.tasks else None
    cands = [x for x in dict.fromkeys(([t0.procedure_id] if t0 and t0.procedure_id else []) + list((t0.candidates if t0 else []) or [])) if x in have][:5]
    rr = rerank_pairs([(pc["text"], names[x]) for x in cands]) if cands else None
    stem = " ".join(understand(conn, pc["text"], syn).terms)
    hit = [p_ for p_, n in folded.items() if stem and f" {stem} " in n]
    rows.append(dict(set=st, exp=exp, got=r.behavior, one=len(p.tasks) == 1, cands=cands, rr=rr or [], nterms=len(stem.split()),
                     n_match=len(hit), n_heads=len({heads[x] for x in hit}), exact=any(n.strip() == stem for n in folded.values())))


def rule_a(r, M, S):
    rr = r["rr"]
    if r["got"] != "answer" or not r["one"] or len(rr) < 2:
        return False
    o = sorted(range(len(rr)), key=lambda i: -rr[i])
    return rr[o[0]] < S and rr[o[0]] - rr[o[1]] < M and heads[r["cands"][o[0]]] != heads[r["cands"][o[1]]]


def rule_b(r, K, H, T):
    return r["got"] == "answer" and r["one"] and not r["exact"] and r["nterms"] <= T and r["n_match"] >= K and r["n_heads"] >= H


def gain(rule, sets):
    g = sum(1 for r in rows if r["set"] in sets and r["exp"] == "clarify" and rule(r))
    l = sum(1 for r in rows if r["set"] in sets and r["exp"] == "answer" and rule(r))
    return f"+{g} -{l}"


sys.stdout.reconfigure(encoding="utf-8")
for sets in (("dev", "p30-tune"), ("p30-held", "p30-fresh")):
    cl = [r for r in rows if r["set"] in sets and r["exp"] == "clarify"]
    print(f"{'/'.join(sets)}: hỏi lại đúng hiện tại {sum(r['got'] == 'clarify' for r in cl)}/{len(cl)}")
    for M in (0.3, 0.6, 1.0, 1.5):
        print("  A M=%.1f: " % M + "  ".join(f"S={S}:{gain(lambda r: rule_a(r, M, S), sets)}" for S in (-2, 0, 1, 3, 99)))
    for K in (3, 5, 8):
        print("  B K=%d: " % K + "  ".join(f"H={H},T={T}:{gain(lambda r: rule_b(r, K, H, T), sets)}" for H in (2, 3) for T in (2, 3, 4)))

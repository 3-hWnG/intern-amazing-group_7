"""Đo nhanh System 3 trên bộ DEV (real_v1) khi sửa câu khó. Mặc định chế độ luật + DB bản 3, như real_v1.

    python run_server.py eval/hard/dev.py                         # real_v1 (dev): chỉ số + so mốc
    python run_server.py eval/hard/dev.py --dump out.jsonl        # + chi tiết từng câu (đoạn, ứng viên, điểm) để phân tích lỗi
    python run_server.py eval/hard/dev.py --set eval/cases_h4.json --name h4    # bộ khác (hồi quy bộ dễ)
    python run_server.py eval/hard/dev.py --final real_v2 --name real_v2_<cấu hình>   # CHỈ khi đã đóng băng code: chạy bộ test một lần

Bộ test real_v2 bị chặn nếu không có --final (tránh lỡ nhìn bộ test khi đang sửa). Kết quả: eval/results/<name>.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
ROOT = os.path.dirname(EVAL)
os.environ.setdefault("S3_USE_LLM", "0")
os.environ.setdefault("S3_PLANNER_MODE", "rules")
os.environ.setdefault("S3_NO_WARMUP", "1")
os.environ.setdefault("S3_DATA_DB", os.path.join(ROOT, "data", "runtime", "knowledge", "3-423eff02f8.db"))
sys.path[:0] = [EVAL, HERE]
import answer_adapter  # noqa: E402
from metrics import summarize, baselines, line  # noqa: E402
from thermal import guard, low_priority  # noqa: E402

SETS = {"real_v1": "real_v1/cases_real_v1_labeled.json", "real_v2": "real_v2/cases_real_v2_labeled.json"}


def judge(c: dict, out: dict) -> dict:
    exp = c["expect_ids"]
    tops = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
    cands = [x for t in out["tasks"] for x in t.get("candidates", [])]
    ranked = list(dict.fromkeys(tops[:1] + cands))[:5]      # MRR@5: thủ tục đầu rồi danh sách ứng viên (cùng nguồn với top-1 / top-3)
    rr = next((1 / (i + 1) for i, p in enumerate(ranked) if p in exp), 0.0)
    return {"rr": round(rr, 4), "ranked": ranked, "id": c["id"], "q": c["q"], "beh": c["beh"], "exp": exp, "got": out["behavior"], "tops": tops[:2],
            "top1": bool(tops) and tops[0] in exp, "top3": any(x in exp for x in cands[:3]), "stratum": c.get("stratum"),
            "routes": out["extra"].get("routes"), "ms": round(out["latency_ms"], 1)}


def detail(text: str) -> dict:
    """Đoạn câu, ứng viên đầu và điểm của bộ xếp hạng (chỉ để phân tích lỗi trên dev)."""
    from planner.planner import _index
    from system3.retrieval.rank import resolve
    res = resolve(_index(), [{"role": "user", "text": text}])
    return {"segs": [{"text": s.text[:160], "terms": s.query.terms[:20], "fields": s.query.fields, "reason": s.reason, "pid": s.proc_id,
                      "decision": s.decision, "hits": [{"pid": h.proc_id, "name": h.name[:70], "score": h.score, "cov": h.cov, "prec": h.prec,
                                                         "him": h.hi_match, "hix": h.hi_miss, "n": h.nmatch} for h in s.hits[:4]]}
                     for s in res.segments]}


def main(argv: list[str]) -> None:
    args = {k: v for k, v in zip(argv[::2], argv[1::2])}
    final = args.get("--final")
    src = SETS.get(final) if final else args.get("--set", SETS["real_v1"])
    if "real_v2" in src and not final:
        raise SystemExit("real_v2 là bộ TEST: chỉ chạy với --final real_v2 sau khi đóng băng code.")
    name = args.get("--name", "dev_" + os.path.splitext(os.path.basename(src))[0])
    low_priority()
    cases = json.load(open(os.path.join(EVAL, src), encoding="utf-8"))
    rows, dump = [], []
    t0 = time.time()
    duty = float(os.environ.get("THERMAL_DUTY", "0.5"))     # nghỉ = duty × thời gian vừa chạy (máy không quá 70 °C)
    for c in cases:
        guard(every=3, label=c["id"])
        tq = time.time()
        if "turns" in c:            # bộ nhiều lượt (cases_h4...): chấm lượt cuối như run_pseudo
            hist = []
            for t in c["turns"]:
                hist.append({"role": "user", "text": t["q"]})
                out = answer_adapter.adapter(hist)
                hist.append({"role": "assistant", "text": out["answer_text"]})
            c = {**c, "q": c["turns"][-1]["q"], "beh": c["turns"][-1]["beh"], "expect_ids": c["turns"][-1]["expect_ids"]}
        else:
            out = answer_adapter.adapter([{"role": "user", "text": c["q"]}])
        r = judge(c, out)
        rows.append(r)
        if "--dump" in args and not final:
            dump.append({**r, **detail(c["q"]), "answer": out["answer_text"][:300]})
        time.sleep(min(2.0, (time.time() - tq) * duty))
    s = summarize(rows)
    print(line(name, s), f"  ({time.time() - t0:.0f} s)")
    if not final:
        b = baselines(rows)
        print(line("  mốc luôn từ chối", b["always_apologize"]))
    os.makedirs(os.path.join(EVAL, "results"), exist_ok=True)
    json.dump({"name": name, "src": src, "env": {k: v for k, v in os.environ.items() if k.startswith("S3_")}, "summary": s, "rows": rows},
              open(os.path.join(EVAL, "results", name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if dump:
        with open(args["--dump"], "w", encoding="utf-8") as f:
            for d in dump:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])

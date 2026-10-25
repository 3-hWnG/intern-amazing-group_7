"""Hiệu chỉnh ngưỡng phương án B (retrieval/semantic.py) trên bộ DEV real_v1: chấm reranker MỘT lần cho mọi câu, rồi mô phỏng quyết định
trên lưới (S3_SEM_TAU_OOS, S3_SEM_TAU_SWAP) không gọi lại model. Chọn theo chỉ số chính đã ghi trước: độ chính xác cân bằng (answer + apologize),
hoà thì lấy "trả lời đúng trọn" cao hơn. Không chạy trên real_v2.

    python run_server.py eval/hard/sem_grid.py score  [--name X]     # chạy luật (theo biến môi trường hiện tại) + chấm reranker, ghi eval/results/sem_X.json
    python run_server.py eval/hard/sem_grid.py grid   [--name X]     # mô phỏng lưới ngưỡng từ tệp trên
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
os.environ["S3_SEMANTIC"] = "0"          # bước "score": lấy quyết định của LUẬT, reranker chấm riêng
sys.path[:0] = [EVAL, HERE]
from metrics import summarize, line  # noqa: E402
from thermal import guard, low_priority  # noqa: E402

SCOPE = {"status", "complaint", "petition", "legal", "internal", "not_in_db", "info"}


def score(name: str) -> None:
    import answer_adapter
    from planner.planner import _index
    from system3.retrieval.rank import resolve
    from system3.retrieval.query import strip_letter
    from system3.retrieval import semantic
    from system3.data import api
    low_priority()
    conn = api.connect()
    in_scope = {r[0] for r in conn.execute("SELECT proc_id FROM proc_flat WHERE in_scope = 1")}
    cases = json.load(open(os.path.join(EVAL, "real_v1", "cases_real_v1_labeled.json"), encoding="utf-8"))
    out = []
    for c in cases:
        guard(every=3, label=c["id"])
        t0 = time.time()
        o = answer_adapter.adapter([{"role": "user", "text": c["q"]}])
        tops = [t["proc_id"] for t in o["tasks"] if t.get("proc_id")]
        res = resolve(_index(), [{"role": "user", "text": c["q"]}])
        segs = res.segments
        eligible = bool(segs) and not any(s.reason in ("chitchat", "order_unknown") or s.inherited for s in segs) \
            and not (len(tops) > 1 and len(c["q"].split()) <= 30)
        rule_ids = [h.proc_id for s in segs for h in s.hits[:5]]
        qt = semantic.query_text(c["q"], segs)
        cands = semantic.candidates(conn, qt, rule_ids)
        sc = semantic.score(qt, cands)
        ranked = sorted(((x["proc_id"], s) for x, s in zip(cands, sc)), key=lambda x: -x[1])
        out.append({"id": c["id"], "beh": c["beh"], "exp": c["expect_ids"], "rule_got": o["behavior"], "rule_tops": tops[:2],
                    "rule_cands": [x for t in o["tasks"] for x in t.get("candidates", [])][:3],
                    "scope": any(r[1] in SCOPE for r in o["extra"].get("routes") or []), "eligible": eligible,
                    "ranked": [(p, round(s, 3)) for p, s in ranked[:8]], "in_scope": [p for p, _ in ranked[:8] if p in in_scope]})
        time.sleep(min(2.0, (time.time() - t0) * float(os.environ.get("THERMAL_DUTY", "0.5"))))
    json.dump({"env": {k: v for k, v in os.environ.items() if k.startswith("S3_")}, "rows": out},
              open(os.path.join(EVAL, "results", f"sem_{name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ghi", len(out), "câu")


def simulate(rows: list[dict], tau_oos: float, tau_swap: float, tau_rescue: float = 99.0) -> list[dict]:
    """Bản sao quyết định của semantic.decide + planner._semantic (keep / none / swap / rescue) trên điểm đã chấm."""
    res = []
    for r in rows:
        got, tops, cands = r["rule_got"], list(r["rule_tops"]), list(r["rule_cands"])
        if r["eligible"] and r["ranked"] and not r["scope"]:
            best, bs = r["ranked"][0]
            pick = tops[0] if tops else None
            rs = next((s for p, s in r["ranked"] if p == pick), None)
            if pick is None:
                if bs >= tau_rescue:
                    got, tops = "answer", [best]
                    cands = [p for p, _ in r["ranked"][:3]]
            elif bs < tau_oos:
                got, tops = "apologize", []
            elif best != pick and rs is not None and bs - rs >= tau_swap:
                got, tops = "answer", [best]
                cands = [p for p, _ in r["ranked"][:3]]
        res.append({"id": r["id"], "beh": r["beh"], "got": got, "top1": bool(tops) and tops[0] in r["exp"],
                    "top3": any(x in r["exp"] for x in cands[:3])})
    return res


def grid(name: str) -> None:
    rows = json.load(open(os.path.join(EVAL, "results", f"sem_{name}.json"), encoding="utf-8"))["rows"]
    base = summarize(simulate(rows, -99, 99))
    print(line("luật (không B)", base), f" chặt {strict(base):.3f}")
    best = []
    for tau_oos in [x / 2 for x in range(-16, 9)]:
        for tau_swap in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 99.0):
            for tau_rescue in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 99.0):
                s = summarize(simulate(rows, tau_oos, tau_swap, tau_rescue))
                best.append((strict(s), s["balanced2"], tau_oos, tau_swap, tau_rescue, s))
    # TIÊU CHÍ CHỌN NGƯỠNG trên dev (24/10, ghi lại sau hai lượt lưới đầu, trước mọi lượt chạy real_v2):
    #   tối đa "cân bằng" (answer + apologize) VỚI RÀNG BUỘC số câu "trả lời đúng trọn" không thấp hơn khi chỉ dùng luật;
    #   hoà -> trả lời đúng trọn cao hơn -> ngưỡng bảo thủ hơn (đổi / cứu ít hơn).
    # Lý do: (1) cân bằng thường tính "trả lời" là đúng cả khi trả lời SAI thủ tục — chọn theo nó, B đổi thủ tục bừa (top-1 65% -> 35% trên nền A);
    # (2) "cân bằng chặt" = trung bình(đúng trọn, recall từ chối) chọn cấu hình từ chối gần hết (luôn từ chối đã được 0,5).
    ok = [b for b in best if b[5]["end2end"]["k"] >= base["end2end"]["k"]]
    ok.sort(key=lambda x: (-x[1], -x[5]["end2end"]["k"], -x[3], -x[4], x[2]))
    print("-- chọn (cân bằng, ràng buộc đúng trọn >= luật):")
    for b in ok[:6]:
        print(line(f"oos={b[2]:+.1f} sw={b[3]:.1f} rs={b[4]:.0f}", b[5]), f" chặt {b[0]:.3f}")
    print("-- theo cân bằng chặt:")
    for b in sorted(best, key=lambda x: (-x[0], -x[1]))[:2]:
        print(line(f"oos={b[2]:+.1f} sw={b[3]:.1f} rs={b[4]:.0f}", b[5]), f" chặt {b[0]:.3f}")
    print("-- theo cân bằng thường (không ràng buộc):")
    for b in sorted(best, key=lambda x: (-x[1], -x[0]))[:2]:
        print(line(f"oos={b[2]:+.1f} sw={b[3]:.1f} rs={b[4]:.0f}", b[5]), f" chặt {b[0]:.3f}")
    if ok:
        b = ok[0]
        print(f"CHỌN: S3_SEM_TAU_OOS={b[2]} S3_SEM_TAU_SWAP={b[3]} S3_SEM_TAU_RESCUE={b[4]}")


def strict(s: dict) -> float:
    return round((s["end2end"]["p"] + s["recall"]["apologize"]["p"]) / 2, 4)


if __name__ == "__main__":
    a = sys.argv[1:]
    nm = a[a.index("--name") + 1] if "--name" in a else "dev"
    {"score": score, "grid": grid}[a[0]](nm)

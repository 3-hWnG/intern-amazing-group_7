"""Mẫu golden cho cổng kiểm khi Áp dụng phiên bản (G2.4): cùng ~150 ca cố định của eval/equality.py (phân tầng, seed cố định),
chạy trên MỘT DB thủ tục, LLM tắt; chấm hành vi + top-1 như run_golden (mã đáp án đổi qua proc_lineage của DB đó, ca không ghép
được thì loại) và ghi sha1 câu trả lời để đếm số câu trả lời đổi giữa hai DB. In một dòng JSON.
Chạy: python run_server.py eval/gate_sample.py --db <đường dẫn DB> [--n 150]
Đây KHÔNG phải lượt đo đầy đủ (không tính vào ngân sách 3 lần eval)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import equality  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--n", type=int, default=150)
    a = ap.parse_args()
    equality.setup_env(a.db)
    from system3.data import api
    conn = api.connect(a.db)
    have = {r[0] for r in conn.execute("SELECT proc_id FROM procedures WHERE status='active'")}
    lin = api.lineage(conn)
    cases = [json.loads(l) for l in open(equality.GOLDEN, encoding="utf-8") if l.strip()]
    sample = [c for c in equality.pick(cases, a.n) if not c["expected"].get("list_domain")]
    res = equality.run_cases(sample)
    beh = n = top1 = n_top = excluded = 0
    per = {}   # id -> [hành vi đúng, top-1 đúng | None]: cổng kiểm so hai DB trên phần ca chấm được ở CẢ HAI
    for c in sample:
        exp = c["expected"]
        ids = set()
        ok = True
        for t in exp.get("tasks", []):
            for p in t["proc_ids"]:
                q = p if p in have else lin.get(p)
                ok = ok and bool(q)
                if q:
                    ids.add(q)
        if not ok:
            excluded += 1
            continue
        r = res[c["id"]]
        n += 1
        b_ok = r["behavior"] == exp["behavior"]
        beh += b_ok
        t_ok = None
        if exp["behavior"] == "answer" and ids:
            n_top += 1
            t_ok = bool(r["proc_ids"]) and r["proc_ids"][0] in ids
            top1 += t_ok
        per[c["id"]] = [b_ok, t_ok]
    print(json.dumps({"db": a.db, "n": n, "behavior": beh, "n_top1": n_top, "top1": top1, "excluded": excluded,
                      "behavior_rate": beh / n if n else None, "top1_rate": top1 / n_top if n_top else None,
                      "cases": per, "answers": {k: v["sha1"] for k, v in res.items()}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

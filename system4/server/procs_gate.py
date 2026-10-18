"""Cổng kiểm khi Áp dụng phiên bản dữ liệu thủ tục (G2.4, P07). Gán procs.gate_fn khi nạp.

Chạy eval/gate_sample.py (cùng ~150 ca golden cố định của mẫu so khớp, LLM tắt) trên DB đang dùng và DB mới, mỗi DB một tiến trình
con (đệm của Planner không lẫn giữa hai DB). CHẶN nếu top-1 hoặc hành vi trên DB mới tụt quá MAX_DROP điểm % so với DB đang dùng.
Không chạy bộ eval đầy đủ. Kết quả (số đo hai bên + số câu trả lời đổi) ghi vào manifest của phiên bản mới."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from . import procs

MAX_DROP = 3.0   # điểm %
REPO = Path(__file__).resolve().parents[2]


def sample(db: Path, timeout: int = 900) -> dict:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", S3_USE_LLM="0", S3_NO_WARMUP="1", S3_PLANNER_MODE="rules",
               OLLAMA_HOST="http://127.0.0.1:1")
    for k in ("S4_ENABLED", "ABI_API_KEY"):
        env.pop(k, None)
    r = subprocess.run([sys.executable, str(REPO / "run_server.py"), str(REPO / "eval" / "gate_sample.py"), "--db", str(db)],
                       cwd=str(REPO), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError("Chạy mẫu kiểm thất bại: " + (r.stderr or r.stdout)[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def gate(cur_db: Path, new_db: Path) -> dict:
    a, b = sample(cur_db), sample(new_db)
    both = sorted(set(a["cases"]) & set(b["cases"]))   # ca chấm được trên cả hai DB (mã đáp án có / ghép được ở cả hai)
    pct = lambda xs: 100.0 * sum(xs) / len(xs) if xs else 0.0
    beh_a, beh_b = [a["cases"][k][0] for k in both], [b["cases"][k][0] for k in both]
    tk = [k for k in both if a["cases"][k][1] is not None and b["cases"][k][1] is not None]
    top_a, top_b = [a["cases"][k][1] for k in tk], [b["cases"][k][1] for k in tk]
    d_top, d_beh = pct(top_a) - pct(top_b), pct(beh_a) - pct(beh_b)
    changed = sum(1 for k, v in b["answers"].items() if a["answers"].get(k) != v)
    ok = d_top <= MAX_DROP and d_beh <= MAX_DROP
    why = [] if ok else [f"top-1 tụt {d_top:.1f} điểm" if d_top > MAX_DROP else "", f"hành vi tụt {d_beh:.1f} điểm" if d_beh > MAX_DROP else ""]
    strip = lambda x: {k: v for k, v in x.items() if k not in ("answers", "cases")}
    return {"ok": ok, "common_cases": len(both), "common_top1_cases": len(tk),
            "common": {"behavior_cur": round(pct(beh_a), 2), "behavior_new": round(pct(beh_b), 2),
                       "top1_cur": round(pct(top_a), 2), "top1_new": round(pct(top_b), 2)}, "reason": "; ".join(w for w in why if w) + (f" (ngưỡng {MAX_DROP:g})" if not ok else ""),
            "current": strip(a), "new": strip(b), "drop_top1_pts": round(d_top, 2), "drop_behavior_pts": round(d_beh, 2),
            "answers_changed": changed, "max_drop": MAX_DROP}


procs.gate_fn = gate

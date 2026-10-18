"""Mẫu so khớp đầu ra (G0.2): ~150 ca cố định của eval/golden/thu-tuc.jsonl (phân tầng theo source × type, seed cố định), chạy qua
answer_adapter với LLM tắt, ghi (hành vi, mã thủ tục, sha1 câu trả lời) để phát hiện mọi thay đổi câu trả lời ngoài ý muốn.
Chạy:
    python run_server.py eval/equality.py --record base          # ghi mốc eval/runtime/equality_base.json
    python run_server.py eval/equality.py --compare base         # chạy lại, in các ca khác mốc (mã thoát 1 nếu có)
    ... [--db <đường dẫn DB thủ tục>]   mặc định: DB cố định eval/runtime/fixture_snapshot.db (eval/fixture_db.py)
    ... [--n 150] [--show 20]
Quy ước: việc CỐ Ý đổi câu trả lời thì đọc diff, ghi lý do vào commit, rồi --record lại mốc."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20261019
GOLDEN = HERE / "golden" / "thu-tuc.jsonl"
OUT_DIR = HERE / "runtime"


def pick(cases: list[dict], n: int = 150, seed: int = SEED) -> list[dict]:
    """Phân tầng theo (source, type): mỗi tầng ít nhất 1 ca, phần còn lại chia theo tỷ lệ (làm tròn theo phần dư lớn nhất)."""
    groups: dict[tuple, list[dict]] = collections.defaultdict(list)
    for c in cases:
        groups[(c["source"], c["type"])].append(c)
    keys = sorted(groups)
    n = max(n, len(keys))
    extra = n - len(keys)
    quota = {k: len(groups[k]) / len(cases) * extra for k in keys}
    alloc = {k: 1 + int(quota[k]) for k in keys}
    for k in sorted(keys, key=lambda k: (-(quota[k] - int(quota[k])), k))[: n - sum(alloc.values())]:
        alloc[k] += 1
    rng = random.Random(seed)
    out = []
    for k in keys:
        g = sorted(groups[k], key=lambda c: c["id"])
        out += rng.sample(g, min(alloc[k], len(g)))
    return sorted(out, key=lambda c: c["id"])


def setup_env(db: str | None) -> str:
    if not db:
        sys.path.insert(0, str(HERE))
        import fixture_db
        db = str(fixture_db.ensure(quiet=True))
    tmp = tempfile.mkdtemp(prefix="s3eq_")
    os.environ.update(S3_DATA_DB=db, S3_DB_PATH=os.path.join(tmp, "s3.db"), S3_USE_LLM="0", S3_NO_WARMUP="1",
                      S3_PLANNER_MODE="rules", OLLAMA_HOST="http://127.0.0.1:1", S4_WARMUP="0", S4_ABI_SYNC="0")
    return db


def run_cases(sample: list[dict]) -> dict:
    sys.path.insert(0, str(HERE))
    import answer_adapter

    def replay(turns):
        hist = []
        for t in turns:
            if t["role"] == "assistant" and not t["text"].strip() and hist:
                t = {"role": "assistant", "text": answer_adapter.adapter(hist)["answer_text"]}
            hist.append(t)
        return hist

    res = {}
    for c in sample:
        if c["expected"].get("list_domain"):
            from orchestrator import _list_request
            text = _list_request(c["question"]) or ""
            beh, pids = ("answer" if text else "none"), []
        else:
            out = answer_adapter.adapter(replay(c["turns"]))
            text, beh = out["answer_text"], out["behavior"]
            pids = [t["proc_id"] for t in out["tasks"] if t.get("proc_id")]
        res[c["id"]] = {"behavior": beh, "proc_ids": pids, "sha1": hashlib.sha1(text.encode("utf-8")).hexdigest(),
                        "question": c.get("question") or c["turns"][-1]["text"], "text": text}
    return res


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--record", metavar="TÊN")
    g.add_argument("--compare", metavar="TÊN")
    ap.add_argument("--db")
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--show", type=int, default=20, help="số ca khác in chi tiết")
    a = ap.parse_args()
    db = setup_env(a.db)
    cases = [json.loads(l) for l in open(GOLDEN, encoding="utf-8") if l.strip()]
    sample = pick(cases, a.n)
    res = run_cases(sample)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if a.record:
        p = OUT_DIR / f"equality_{a.record}.json"
        p.write_text(json.dumps({"db": db, "n": len(res), "seed": SEED, "cases": res}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"đã ghi mốc {len(res)} ca -> {p}")
        return 0
    base = json.loads((OUT_DIR / f"equality_{a.compare}.json").read_text(encoding="utf-8"))["cases"]
    diff = [k for k in sorted(set(base) | set(res)) if base.get(k, {}).get("sha1") != res.get(k, {}).get("sha1")
            or base.get(k, {}).get("behavior") != res.get(k, {}).get("behavior")
            or base.get(k, {}).get("proc_ids") != res.get(k, {}).get("proc_ids")]
    kinds = collections.Counter()
    for k in diff:
        b, r = base.get(k, {}), res.get(k, {})
        kind = ("hành vi" if b.get("behavior") != r.get("behavior") else
                "mã thủ tục" if b.get("proc_ids") != r.get("proc_ids") else "chữ")
        kinds[kind] += 1
        if sum(kinds.values()) <= a.show:
            print(f"── {k} [{kind}] {r.get('question') or b.get('question')}")
            if kind != "chữ":
                print(f"   mốc: {b.get('behavior')} {b.get('proc_ids')}  ->  nay: {r.get('behavior')} {r.get('proc_ids')}")
            else:
                import difflib
                for line in list(difflib.unified_diff(b.get("text", "").splitlines(), r.get("text", "").splitlines(), "mốc", "nay", n=0, lineterm=""))[2:12]:
                    print("   " + line)
    print(f"\n{len(res)} ca; khác mốc '{a.compare}': {len(diff)}" + (f" ({dict(kinds)})" if diff else ""))
    return 1 if diff else 0


if __name__ == "__main__":
    raise SystemExit(main())

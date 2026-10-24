"""Gộp nhãn real_v2 (eval/real_v2/_work/b*.jsonl, gán tay theo docs/eval 3 ngày/REAL_V1_GUIDE.md) -> real_v2_labels.json + bộ để chạy.
Kiểm: đủ 348 id, không trùng, `beh` hợp lệ, mọi `expect_ids` có trong DB bản 3; `answer` phải có expect_ids.

    python eval/real_v2/build_labeled.py
"""
import glob
import json
import os
import sqlite3
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "..", "data", "runtime", "knowledge", "3-423eff02f8.db")
BEH = {"answer", "clarify", "apologize", "skip"}
FIELDS = {"documents", "conditions", "fee", "time", "place", "legal_basis"}


def main():
    cases = json.load(open(os.path.join(HERE, "cases_real_v2.json"), encoding="utf-8"))
    labels = [json.loads(l) for f in sorted(glob.glob(os.path.join(HERE, "_work", "b*.jsonl"))) for l in open(f, encoding="utf-8") if l.strip()]
    ids = [x["id"] for x in labels]
    assert len(ids) == len(set(ids)), [i for i, n in Counter(ids).items() if n > 1]
    assert set(ids) == {c["id"] for c in cases}, set(c["id"] for c in cases) ^ set(ids)
    db = sqlite3.connect(DB)
    known = {r[0]: r[1] for r in db.execute("SELECT proc_id, in_scope FROM proc_flat")}
    for x in labels:
        assert x["beh"] in BEH, x
        assert set(x["fields"]) <= FIELDS, x
        assert all(p in known for p in x["expect_ids"]), x
        assert (x["beh"] == "answer") <= bool(x["expect_ids"]), x
        assert x["beh"] != "apologize" or not x["expect_ids"], x
    by = {x["id"]: x for x in labels}
    final = [{**{k: c[k] for k in ("id", "stratum", "source")}, "q": c["text"], **{k: by[c["id"]][k] for k in ("beh", "expect_ids", "fields", "notes")}}
             for c in cases]
    json.dump(final, open(os.path.join(HERE, "real_v2_labels.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    run = [{k: x[k] for k in ("id", "q", "beh", "expect_ids", "fields", "notes", "stratum", "source")} for x in final if x["beh"] != "skip"]
    json.dump(run, open(os.path.join(HERE, "cases_real_v2_labeled.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("nhãn:", dict(Counter(x["beh"] for x in final)))
    print("bộ chạy:", len(run), dict(Counter(x["beh"] for x in run)))
    for st in ("random", "chude"):
        print(st, dict(Counter(x["beh"] for x in run if x["stratum"] == st)))
    ans = [x for x in run if x["beh"] == "answer"]
    print("answer có >1 mã chấp nhận:", sum(len(x["expect_ids"]) > 1 for x in ans), "/", len(ans))
    print("mã ngoài in_scope trong answer:", [(x["id"], p) for x in ans for p in x["expect_ids"] if known[p] != 1])
    print("thủ tục đáp án:", Counter(p for x in ans for p in x["expect_ids"][:1]).most_common(12))


if __name__ == "__main__":
    main()

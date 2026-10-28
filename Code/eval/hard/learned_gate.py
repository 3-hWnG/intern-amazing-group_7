"""Baseline sau (post-hoc, phản biện 27/10): cổng ngoài phạm vi HỌC từ dev thay cho cổng luật viết tay.

Naive Bayes đa thức trên n-gram từ (1-2) và n-gram ký tự (3-5) của câu đã bỏ dấu, phân loại "phải từ chối" / "không". Ngưỡng log-odds chọn
bằng 5-fold trên DEV (cao nhất balanced accuracy của hai lớp từ chối / không), rồi học lại trên cả dev. Ghép: cổng bảo từ chối thì từ chối,
không thì giữ quyết định của BẢN GỐC (mọi cờ tắt, eval/hard/results/test*/real_v*_off.json). Mỗi bộ test chấm MỘT lần:
  - test 1 (real_v2): học trên real_v1 (282), như vòng 1;
  - test 2 (real_v4): học trên dev595 (real_v1 + real_v2), như vòng 2.
Không dùng gì của bộ test để chọn.

    python run_server.py eval/hard/learned_gate.py
"""
import json
import math
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
ROOT = os.path.dirname(EVAL)
sys.path.insert(0, ROOT)
from data.textutil import fold  # noqa: E402

SEED, FOLDS, ALPHA = 20261027, 5, 0.5


def feats(q: str) -> Counter:
    t = " ".join(fold(q or "").split())
    w = t.split()
    c = Counter(w)
    c.update(" ".join(p) for p in zip(w, w[1:]))
    s = f" {t} "
    for n in (3, 4, 5):
        c.update("#" + s[i:i + n] for i in range(len(s) - n + 1))
    return c


class NB:
    def fit(self, X, y):
        self.cnt = {0: Counter(), 1: Counter()}
        for x, t in zip(X, y):
            self.cnt[t].update(x)
        self.tot = {k: sum(v.values()) for k, v in self.cnt.items()}
        self.V = len(set(self.cnt[0]) | set(self.cnt[1]))
        n1 = sum(y)
        self.prior = math.log((n1 + 1) / (len(y) - n1 + 1))
        return self

    def score(self, x):        # log-odds của lớp 1 (phải từ chối)
        s = self.prior
        for f, k in x.items():
            p1 = (self.cnt[1][f] + ALPHA) / (self.tot[1] + ALPHA * self.V)
            p0 = (self.cnt[0][f] + ALPHA) / (self.tot[0] + ALPHA * self.V)
            s += k * math.log(p1 / p0)
        return s / max(1, sum(x.values())) ** 0.5     # chuẩn hoá theo độ dài để câu dài không áp đảo


def bal(y, p):
    r1 = sum(a and b for a, b in zip(y, p)) / max(1, sum(y))
    r0 = sum((not a) and (not b) for a, b in zip(y, p)) / max(1, len(y) - sum(y))
    return (r1 + r0) / 2


def pick_threshold(X, y):
    idx = list(range(len(y)))
    random.Random(SEED).shuffle(idx)
    scores = [None] * len(y)
    for k in range(FOLDS):
        te = set(idx[k::FOLDS])
        m = NB().fit([X[i] for i in idx if i not in te], [y[i] for i in idx if i not in te])
        for i in te:
            scores[i] = m.score(X[i])
    cands = sorted(set(round(s, 3) for s in scores))
    return max(cands, key=lambda t: (bal(y, [s >= t for s in scores]), -abs(t)))


def run(train_files, test_name, base_file):
    train = [c for f in train_files for c in json.load(open(os.path.join(EVAL, f), encoding="utf-8"))]
    X = [feats(c["q"]) for c in train]
    y = [int(c["beh"] == "apologize") for c in train]
    thr = pick_threshold(X, y)
    model = NB().fit(X, y)
    cases = json.load(open(os.path.join(EVAL, {"real_v2": "real_v2/cases_real_v2_labeled.json", "real_v4": "real_v4/cases_real_v4_labeled.json"}[test_name]),
                           encoding="utf-8"))
    base = {r["id"]: r for r in json.load(open(os.path.join(HERE, base_file), encoding="utf-8"))["rows"]}
    rows = []
    for c in cases:
        b = base[c["id"]]
        gate = model.score(feats(c["q"])) >= thr
        got = "apologize" if gate else b["got"]
        rows.append({"id": c["id"], "beh": c["beh"], "exp": c["expect_ids"], "got": got, "tops": [] if gate else b["tops"],
                     "top1": False if gate else b["top1"], "gate": bool(gate)})
    na = sum(r["beh"] == "answer" for r in rows)
    nr = sum(r["beh"] == "apologize" for r in rows)
    ans = sum(r["got"] == "answer" and r["beh"] == "answer" for r in rows)
    ref = sum(r["got"] == "apologize" and r["beh"] == "apologize" for r in rows)
    e2e = sum(r["got"] == "answer" and r["beh"] == "answer" and r["top1"] for r in rows)
    answered = sum(r["got"] == "answer" for r in rows)
    summ = {"train": train_files, "n_train": len(train), "threshold": thr, "n": len(rows), "behavior": sum(r["got"] == r["beh"] for r in rows),
            "balanced": round((ans / na + ref / nr) / 2, 4), "answer_ok": ans, "refusals": ref, "n_refuse": nr, "e2e": e2e, "n_answer": na,
            "answered": answered, "precision": round(e2e / answered, 3) if answered else None}
    out = os.path.join(HERE, "results", "test" if test_name == "real_v2" else "test_v4", f"{test_name}_learned_gate.json")
    json.dump({"name": f"{test_name}_learned_gate", "summary": summ, "rows": rows}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(test_name, summ)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run(["real_v1/cases_real_v1_labeled.json"], "real_v2", "results/test/real_v2_off.json")
    run(["hard/dev595/cases_dev_r1r2.json"], "real_v4", "results/test_v4/real_v4_off.json")

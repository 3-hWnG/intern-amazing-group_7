"""Baseline sau (post-hoc, phản biện vòng 2, 27/10): cổng ngoài phạm vi học từ dev, mạnh hơn Naive Bayes.

Hồi quy logistic (L2, cân bằng lớp) trên embedding BGE-M3 của câu hỏi (cùng model với phương án B, qua Ollama), dự đoán "phải từ chối".
Hệ số điều chuẩn và ngưỡng chọn bằng 5-fold trên DEV (cao nhất balanced accuracy từ chối / không), rồi học lại trên cả dev. Ghép như
learned_gate.py: cổng bảo từ chối thì từ chối, không thì giữ quyết định của bản gốc. Mỗi bộ test chấm MỘT lần:
  - test 1 (real_v2): học trên real_v1 (282); test 2 (real_v4): học trên dev595 (real_v1 + real_v2).
Embedding lưu đệm ở results/emb_questions.npz (chỉ vector, theo mã câu).

    python run_server.py eval/hard/learned_gate_emb.py
"""
import json
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
ROOT = os.path.dirname(EVAL)
sys.path[:0] = [ROOT, EVAL]
from system3.retrieval import semantic  # noqa: E402

SEED, FOLDS = 20261027, 5
CACHE = os.path.join(HERE, "results", "emb_questions.npz")
SETS = {"real_v1": "real_v1/cases_real_v1_labeled.json", "real_v2": "real_v2/cases_real_v2_labeled.json",
        "real_v4": "real_v4/cases_real_v4_labeled.json"}


def embeddings(cases):
    have = dict(np.load(CACHE)) if os.path.exists(CACHE) else {}
    todo = [c for c in cases if c["id"] not in have]
    if todo:
        v = semantic._embed([c["q"][:2000] for c in todo], semantic.model_kind())
        have.update({c["id"]: v[i] for i, c in enumerate(todo)})
        np.savez(CACHE, **have)
    return np.vstack([have[c["id"]] for c in cases])


def fit(X, y, lam, iters=400, lr=0.5):
    n, d = X.shape
    w, b = np.zeros(d), 0.0
    cw = np.where(y == 1, len(y) / (2 * y.sum()), len(y) / (2 * (len(y) - y.sum())))
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ w + b)))
        g = cw * (p - y)
        w -= lr * (X.T @ g / n + lam * w)
        b -= lr * g.mean()
    return w, b


def bal(y, p):
    return ((p[y == 1]).mean() + (~p[y == 0]).mean()) / 2


def cv_scores(X, y, lam):
    idx = list(range(len(y)))
    random.Random(SEED).shuffle(idx)
    s = np.zeros(len(y))
    for k in range(FOLDS):
        te = np.array(idx[k::FOLDS]); tr = np.array([i for i in idx if i not in set(te)])
        w, b = fit(X[tr], y[tr], lam)
        s[te] = X[te] @ w + b
    return s


def choose(X, y):
    best = None
    for lam in (1e-3, 1e-2, 1e-1):
        s = cv_scores(X, y, lam)
        for t in np.unique(np.round(s, 2)):
            v = bal(y, s >= t)
            if best is None or v > best[0] + 1e-9:
                best = (v, lam, float(t))
    return best


def run(train_sets, test_name, base_file):
    train = [c for k in train_sets for c in json.load(open(os.path.join(EVAL, SETS[k]), encoding="utf-8"))]
    test = json.load(open(os.path.join(EVAL, SETS[test_name]), encoding="utf-8"))
    Xtr, Xte = embeddings(train), embeddings(test)
    y = np.array([int(c["beh"] == "apologize") for c in train])
    cvbal, lam, thr = choose(Xtr, y)
    w, b = fit(Xtr, y, lam)
    base = {r["id"]: r for r in json.load(open(os.path.join(HERE, base_file), encoding="utf-8"))["rows"]}
    rows = []
    for c, x in zip(test, Xte):
        bse = base[c["id"]]
        gate = bool(x @ w + b >= thr)
        rows.append({"id": c["id"], "beh": c["beh"], "exp": c["expect_ids"], "got": "apologize" if gate else bse["got"],
                     "tops": [] if gate else bse["tops"], "top1": False if gate else bse["top1"], "gate": gate})
    na = sum(r["beh"] == "answer" for r in rows); nr = sum(r["beh"] == "apologize" for r in rows)
    ans = sum(r["got"] == "answer" and r["beh"] == "answer" for r in rows)
    ref = sum(r["got"] == "apologize" and r["beh"] == "apologize" for r in rows)
    e2e = sum(r["got"] == "answer" and r["beh"] == "answer" and r["top1"] for r in rows)
    answered = sum(r["got"] == "answer" for r in rows)
    summ = {"train": train_sets, "n_train": len(train), "lambda": lam, "threshold": thr, "cv_balanced": round(float(cvbal), 4), "n": len(rows),
            "behavior": sum(r["got"] == r["beh"] for r in rows), "balanced": round((ans / na + ref / nr) / 2, 4), "answer_ok": ans,
            "refusals": ref, "n_refuse": nr, "e2e": e2e, "n_answer": na, "answered": answered,
            "precision": round(e2e / answered, 3) if answered else None}
    out = os.path.join(HERE, "results", "test" if test_name == "real_v2" else "test_v4", f"{test_name}_learned_gate_emb.json")
    json.dump({"name": f"{test_name}_learned_gate_emb", "summary": summ, "rows": rows}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(test_name, summ)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run(["real_v1"], "real_v2", "results/test/real_v2_off.json")
    run(["real_v1", "real_v2"], "real_v4", "results/test_v4/real_v4_off.json")

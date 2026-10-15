# -*- coding: utf-8 -*-
"""rank_metrics.py - chỉ số xếp hạng cho tầng truy hồi (A4 MRR, A5 nDCG@k).

Thuần hàm, không phụ thuộc hệ thống, có selftest ở cuối (python rank_metrics.py).
Quy ước: độ liên quan nhị phân (id nằm trong tập acceptable = 1, còn lại = 0).
"""
import math


def first_rank(cands, acceptable):
    """Hạng (1-indexed) của ứng viên đúng đầu tiên; None nếu không có."""
    for i, c in enumerate(cands, 1):
        if c in acceptable:
            return i
    return None


def reciprocal_rank(cands, acceptable):
    """RR = 1/hạng của ứng viên đúng đầu tiên; 0 nếu không có."""
    r = first_rank(cands, acceptable)
    return 1.0 / r if r else 0.0


def ndcg_at_k(cands, acceptable, k=5):
    """nDCG@k nhị phân. DCG cộng 1/log2(i+1) cho mỗi ứng viên đúng trong top-k
    (mỗi id đúng chỉ tính một lần); IDCG = đặt min(|acceptable|, k) đáp án lên đầu."""
    if not acceptable:
        return None
    seen, dcg = set(), 0.0
    for i, c in enumerate(cands[:k], 1):
        if c in acceptable and c not in seen:
            seen.add(c)
            dcg += 1.0 / math.log2(i + 1)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(acceptable), k) + 1))
    return dcg / idcg


def best_match(outs_cands, used, acceptable, k=5):
    """Chọn trong các task đầu ra CHƯA dùng (outs_cands[j]) task cho RR cao nhất.
    Trả (j, rr, ndcg) hoặc (None, 0.0, 0.0) nếu không task nào chứa đáp án."""
    best = (None, 0.0, 0.0)
    for j, cands in enumerate(outs_cands):
        if j in used:
            continue
        rr = reciprocal_rank(cands, acceptable)
        if rr > best[1]:
            best = (j, rr, ndcg_at_k(cands, acceptable, k) or 0.0)
    return best


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _selftest():
    acc = {"A"}
    assert reciprocal_rank(["A", "B"], acc) == 1.0
    assert reciprocal_rank(["B", "A"], acc) == 0.5
    assert abs(reciprocal_rank(["B", "C", "A"], acc) - 1 / 3) < 1e-9
    assert reciprocal_rank(["B", "C"], acc) == 0.0
    assert ndcg_at_k(["A"], acc) == 1.0
    assert abs(ndcg_at_k(["B", "A"], acc) - 1 / math.log2(3)) < 1e-9
    assert ndcg_at_k(["B", "C", "D", "E", "F", "A"], acc, k=5) == 0.0     # ngoài top-k
    two = {"A", "B"}                                                      # 2 đáp án: A,B lên đầu = 1.0
    assert abs(ndcg_at_k(["A", "B", "X"], two) - 1.0) < 1e-9
    assert ndcg_at_k(["A", "X", "B"], two) < 1.0
    assert abs(ndcg_at_k(["A", "A", "A"], two) - (1.0 / (1 + 1 / math.log2(3)))) < 1e-9   # lặp id không cộng thêm
    assert ndcg_at_k(["A"], set()) is None
    j, rr, nd = best_match([["X", "A"], ["A"]], set(), acc)
    assert (j, rr) == (1, 1.0)
    j, rr, nd = best_match([["X", "A"], ["A"]], {1}, acc)
    assert (j, rr) == (0, 0.5)
    assert best_match([["X"]], set(), acc) == (None, 0.0, 0.0)
    print("rank_metrics selftest OK")


if __name__ == "__main__":
    _selftest()

"""Độ đồng thuận giữa hai người gán nhãn real_v1 (Ngày 2). Xem docs/eval 3 ngày/REAL_V1_GUIDE.md §7.

    python eval/real_v1/real_v1_agree.py                              # System 3: eval/real_v1/real_v1_labels_A.json vs _B.json
    python eval/real_v1/real_v1_agree.py --s4                         # System 4: system4/eval/real_v1/real_v1_s4_labels_A.json vs _B.json
    python eval/real_v1/real_v1_agree.py A.json B.json [--write]      # tệp khác; --write ghi sườn eval/real_v1/REAL_V1_ASSUMPTIONS.md (không đè nếu đã có)
    python eval/real_v1/real_v1_agree.py --selftest

System 3: Cohen's kappa trên beh (answer / clarify / apologize; câu skip tính riêng), % expect_ids khớp hệt / tập con trên câu cả hai gán
answer, danh sách câu bất đồng. System 4: khớp drop, refusal, ask_back, và any/all của check.
Báo cả hai con số kể cả khi thấp. Không cần thư viện ngoài.
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BEH = ("answer", "clarify", "apologize")


def kappa(a: list, b: list) -> float:
    """Cohen's kappa cho hai danh sách nhãn cùng độ dài."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def load(path: str) -> dict:
    rows = json.load(open(path, encoding="utf-8"))
    out = {}
    for r in rows:
        if r["id"] in out:
            sys.exit(f"{path}: id lặp {r['id']}")
        out[r["id"]] = r
    return out


def s3(A: dict, B: dict) -> list[str]:
    ids = sorted(set(A) & set(B))
    print(f"A {len(A)} nhãn, B {len(B)} nhãn, chung {len(ids)}; chỉ A: {len(set(A) - set(B))}, chỉ B: {len(set(B) - set(A))}")
    bad = [r["id"] for r in list(A.values()) + list(B.values()) if r.get("beh") not in BEH + ("skip",)]
    if bad:
        sys.exit(f"beh không hợp lệ ở: {sorted(set(bad))[:10]}")
    skip = [i for i in ids if "skip" in (A[i]["beh"], B[i]["beh"])]
    both_skip = [i for i in skip if A[i]["beh"] == B[i]["beh"] == "skip"]
    print(f"skip: A {sum(A[i]['beh'] == 'skip' for i in ids)}, B {sum(B[i]['beh'] == 'skip' for i in ids)}, cả hai {len(both_skip)}, lệch {len(skip) - len(both_skip)}")
    kept = [i for i in ids if i not in skip]
    a, b = [A[i]["beh"] for i in kept], [B[i]["beh"] for i in kept]
    k = kappa(a, b) if kept else float("nan")
    print(f"\nbeh trên {len(kept)} câu cả hai không skip: khớp {sum(x == y for x, y in zip(a, b))}/{len(kept)} ({sum(x == y for x, y in zip(a, b)) / max(len(kept), 1):.1%}), Cohen's kappa = {k:.3f}")
    c = Counter(zip(a, b))
    print("ma trận (hàng A, cột B):")
    print("          " + "".join(f"{x:>11}" for x in BEH))
    for x in BEH:
        print(f"{x:>10}" + "".join(f"{c[(x, y)]:>11}" for y in BEH))
    both_ans = [i for i in kept if A[i]["beh"] == B[i]["beh"] == "answer"]
    exact = [i for i in both_ans if set(A[i]["expect_ids"]) == set(B[i]["expect_ids"])]
    sub = [i for i in both_ans if i not in exact and (set(A[i]["expect_ids"]) <= set(B[i]["expect_ids"]) or set(B[i]["expect_ids"]) <= set(A[i]["expect_ids"]))]
    print(f"\nexpect_ids trên {len(both_ans)} câu cả hai gán answer: khớp hệt {len(exact)} ({len(exact) / max(len(both_ans), 1):.1%}), một bên là tập con {len(sub)}, "
          f"lệch hẳn {len(both_ans) - len(exact) - len(sub)}")
    return [i for i in ids if i not in both_skip and (A[i]["beh"] != B[i]["beh"] or (A[i]["beh"] == "answer" and set(A[i]["expect_ids"]) != set(B[i]["expect_ids"])))]


def _norm(x) -> str:
    return " ".join(str(x).lower().split())


def answers_agree(a: dict, b: dict) -> bool:
    """Hai nhãn đáp án (check) khớp khi cùng không có đáp án, hoặc có một chuỗi của bên này nằm trong (hoặc bằng) chuỗi của bên kia.
    Gồm any, all và num (số đếm): 'đứt gãy, phối tảng và uốn nếp' (any) khớp ['đứt gãy', 'phối tảng', 'uốn nếp'] (all); '19' khớp num 19."""
    def toks(c):
        t = [_norm(x) for x in (c.get("any") or []) + (c.get("all") or [])]
        if c.get("num") is not None:
            t.append(_norm(c["num"]))
        return [x for x in t if x]
    ta, tb = toks(a), toks(b)
    if not ta and not tb:
        return True
    return any(x in y or y in x for x in ta for y in tb)


def s4(A: dict, B: dict) -> list[str]:
    ids = sorted(set(A) & set(B))
    print(f"A {len(A)} nhãn, B {len(B)} nhãn, chung {len(ids)}")

    def ck(r, k):
        return (r.get("check") or {}).get(k)

    dis = []
    for name, f in (("drop", lambda r: bool(r.get("drop"))), ("refusal", lambda r: bool(ck(r, "refusal"))), ("ask_back", lambda r: bool(ck(r, "ask_back"))),
                    ("urgent", lambda r: r.get("urgent")), ("needs_image", lambda r: r.get("needs_image"))):
        d = [i for i in ids if f(A[i]) != f(B[i])]
        print(f"{name:>9}: khớp {len(ids) - len(d)}/{len(ids)} ({(len(ids) - len(d)) / max(len(ids), 1):.1%})")
        dis += d
    both = [i for i in ids if not A[i].get("drop") and not B[i].get("drop")]
    d = [i for i in both if not answers_agree(A[i].get("check") or {}, B[i].get("check") or {})]   # any / all / num: khớp khi có chung ý (xem answers_agree)
    print(f"{'đáp án':>9}: khớp {len(both) - len(d)}/{len(both)} ({(len(both) - len(d)) / max(len(both), 1):.1%}) trên câu cả hai không drop (any/all/num, khớp khi giao nhau)")
    dis += d
    print(f"kappa của refusal trên {len(both)} câu không drop: {kappa([bool(ck(A[i], 'refusal')) for i in both], [bool(ck(B[i], 'refusal')) for i in both]):.3f}")
    return sorted(set(dis))


def describe(r: dict) -> str:
    return r["beh"] + (f"({','.join(r['expect_ids'])})" if r.get("beh") == "answer" and r.get("expect_ids") else "") if "beh" in r else json.dumps(
        {"drop": r.get("drop"), "check": r.get("check")}, ensure_ascii=False)


def report(A, B, cases, dis, write):
    print(f"\nbất đồng cần thống nhất: {len(dis)} câu")
    lines = []
    for i in dis:
        q = (cases.get(i) or {}).get("text") or (cases.get(i) or {}).get("q") or "?"
        print(f"  {i} | {q[:80]} | A: {describe(A[i])} | B: {describe(B[i])}")
        lines.append(f"- {i} | {q} | <nhãn cuối> | A: {describe(A[i])}, B: {describe(B[i])} | <lý do thống nhất>")
    if write:
        out = os.path.join(HERE, "REAL_V1_ASSUMPTIONS.md")
        if os.path.exists(out):
            print(f"\n{out} đã có, không ghi đè")
        else:
            open(out, "w", encoding="utf-8").write("# real_v1: bất đồng giữa A và B và nhãn thống nhất\n\nFormat: id | câu hỏi | nhãn cuối | A, B | lý do.\n\n" + "\n".join(lines) + "\n")
            print(f"\nđã ghi sườn {out}")


def selftest():
    assert abs(kappa(list("aabb"), list("aabb")) - 1) < 1e-9
    assert abs(kappa(list("aabb"), list("bbaa")) - (-1)) < 1e-9
    assert abs(kappa(list("aaaa"), list("aaaa")) - 1) < 1e-9
    k = kappa(["answer"] * 6 + ["apologize"] * 4, ["answer"] * 5 + ["clarify"] + ["apologize"] * 4)
    assert abs(k - 0.8148) < 0.001, k   # po 0.9, pe 0.46
    A = {"x1": {"id": "x1", "beh": "answer", "expect_ids": ["1"]}, "x2": {"id": "x2", "beh": "clarify", "expect_ids": []}, "x3": {"id": "x3", "beh": "skip"}}
    B = {"x1": {"id": "x1", "beh": "answer", "expect_ids": ["1", "2"]}, "x2": {"id": "x2", "beh": "clarify", "expect_ids": []}, "x3": {"id": "x3", "beh": "skip"}}
    dis = s3(A, B)
    assert dis == ["x1"], dis
    assert answers_agree({"any": ["đứt gãy, phối tảng và uốn nếp"]}, {"all": ["đứt gãy", "phối tảng", "uốn nếp"]})
    assert answers_agree({"any": ["19"]}, {"num": 19}) and answers_agree({}, {}) and not answers_agree({"any": ["Hà Nội"]}, {"any": ["Huế"]})
    print("\nselftest OK")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selftest" in sys.argv:
        return selftest()
    is4 = "--s4" in sys.argv
    base = os.path.join(ROOT, "system4", "eval", "real_v1", "real_v1_s4_labels_") if is4 else os.path.join(HERE, "real_v1_labels_")
    pa, pb = (args + [None, None])[:2] if args else (base + "A.json", base + "B.json")
    A, B = load(pa), load(pb)
    paths = [os.path.join(ROOT, "system4", "eval", "real_v1", f) for f in ("cases_real_v1_s4.json", "cases_real_v1_s4_bang.json")] if is4 else [os.path.join(HERE, "cases_real_v1.json")]
    cpath = " + ".join(os.path.basename(p) for p in paths)
    cases = {r["id"]: r for p in paths if os.path.exists(p) for r in json.load(open(p, encoding="utf-8"))}
    if cases:
        unknown = (set(A) | set(B)) - set(cases)
        if unknown:
            sys.exit(f"id không có trong {cpath}: {sorted(unknown)[:10]}")
        print(f"phủ: A {len(set(A) & set(cases))}/{len(cases)}, B {len(set(B) & set(cases))}/{len(cases)} câu của {cpath}")
    dis = (s4 if is4 else s3)(A, B)
    report(A, B, cases, dis, "--write" in sys.argv)


if __name__ == "__main__":
    main()

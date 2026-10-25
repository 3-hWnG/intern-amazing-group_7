"""Runner và công cụ đo độ đồng thuận cho bộ mù thứ tư real_v4_s4.

    python system4/eval/real_v4_s4/run_real_v4_s4.py agree    # đo đồng thuận giữa nhãn A và nhãn B
    python system4/eval/real_v4_s4/run_real_v4_s4.py build    # ghép 128 câu Phần A + 88 câu Phần B -> cases_real_v4_s4_labeled.json (216 câu)
    python system4/eval/real_v4_s4/run_real_v4_s4.py hash     # xuất bảng mã băm SHA256 cho LOCK.md
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _norm(x) -> str:
    return " ".join(str(x).lower().split())


def kappa(a: list, b: list) -> float:
    """Cohen's kappa cho 2 danh sách nhãn cùng độ dài."""
    n = len(a)
    if n == 0:
        return 1.0
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def answers_agree(a: dict, b: dict) -> bool:
    """Hai nhãn đáp án khớp khi cùng là refusal/ask_back hoặc có ít nhất 1 phần tử giao thoa."""
    if a.get("refusal") or b.get("refusal"):
        return bool(a.get("refusal")) == bool(b.get("refusal"))
    if a.get("ask_back") or b.get("ask_back"):
        return bool(a.get("ask_back")) == bool(b.get("ask_back"))

    def toks(c):
        t = [_norm(x) for x in (c.get("any") or []) + (c.get("all") or [])]
        if c.get("num") is not None:
            if isinstance(c["num"], list):
                t.extend([_norm(x) for x in c["num"]])
            else:
                t.append(_norm(c["num"]))
        return [x for x in t if x]

    ta, tb = toks(a), toks(b)
    if not ta and not tb:
        return True
    return any(x in y or y in x for x in ta for y in tb)


def run_agree() -> dict:
    file_a = HERE / "real_v4_s4_labels_A.json"
    file_b = HERE / "real_v4_s4_labels_B.json"

    if not file_a.exists() or not file_b.exists():
        sys.exit(f"Thiếu file nhãn: {file_a} hoặc {file_b}")

    rows_a = {r["id"]: r for r in json.loads(file_a.read_text(encoding="utf-8"))}
    rows_b = {r["id"]: r for r in json.loads(file_b.read_text(encoding="utf-8"))}

    common_ids = sorted(set(rows_a) & set(rows_b))
    n = len(common_ids)
    print(f"Tổng số câu gán nhãn độc lập: {n}")

    # 1. Khớp từ chối (refusal)
    ref_a = [bool((rows_a[i].get("check") or {}).get("refusal")) for i in common_ids]
    ref_b = [bool((rows_b[i].get("check") or {}).get("refusal")) for i in common_ids]
    k_ref = kappa(ref_a, ref_b)
    acc_ref = sum(x == y for x, y in zip(ref_a, ref_b)) / n

    # 2. Khớp hỏi lại (ask_back)
    ask_a = [bool((rows_a[i].get("check") or {}).get("ask_back")) for i in common_ids]
    ask_b = [bool((rows_b[i].get("check") or {}).get("ask_back")) for i in common_ids]
    k_ask = kappa(ask_a, ask_b)
    acc_ask = sum(x == y for x, y in zip(ask_a, ask_b)) / n

    # 3. Khớp nội dung đáp án (any/all/num/refusal/ask_back)
    ans_match = [answers_agree(rows_a[i].get("check") or {}, rows_b[i].get("check") or {}) for i in common_ids]
    acc_ans = sum(ans_match) / n

    # Tổng thể loại nhãn: answer / refusal / ask_back
    def label_type(r):
        ck = r.get("check") or {}
        if ck.get("refusal"):
            return "refusal"
        if ck.get("ask_back"):
            return "ask_back"
        return "answer"

    typ_a = [label_type(rows_a[i]) for i in common_ids]
    typ_b = [label_type(rows_b[i]) for i in common_ids]
    k_overall = kappa(typ_a, typ_b)

    print(f"1. Khớp refusal: {acc_ref:.1%} (kappa = {k_ref:.3f})")
    print(f"2. Khớp ask_back: {acc_ask:.1%} (kappa = {k_ask:.3f})")
    print(f"3. Khớp đáp án (semantically agree): {acc_ans:.1%}")
    print(f"4. Cohen's kappa hành vi tổng thể: κ = {k_overall:.3f}")

    diff_ids = [i for i, ok in zip(common_ids, ans_match) if not ok or (rows_a[i].get("check") != rows_b[i].get("check"))]
    print(f"Số câu có khác biệt chi tiết cần thống nhất: {len(diff_ids)}/{n}")

    return {
        "total_cases": n,
        "raw_agreement": acc_ans,
        "cohen_kappa_behavior": k_overall,
        "diff_count": len(diff_ids)
    }


def build_labeled_set():
    file_a = HERE / "cases_real_v4_s4.json"
    file_b = HERE / "real_v4_s4_labels_final.json"

    cases_a = json.loads(file_a.read_text(encoding="utf-8"))
    cases_b = json.loads(file_b.read_text(encoding="utf-8"))

    combined = cases_a + cases_b
    out_file = HERE / "cases_real_v4_s4_labeled.json"
    out_file.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã tạo {out_file.name}: {len(combined)} câu (Phần A: {len(cases_a)}, Phần B: {len(cases_b)})")


def compute_hashes():
    data_dir = HERE / "data"
    files_to_hash = sorted(list(data_dir.glob("*.xlsx")) + [data_dir / "manifest.json"])
    script_files = [
        HERE / "build_v4.py",
        HERE / "make_cases_v4.py",
        HERE / "run_real_v4_s4.py"
    ]
    json_files = [
        HERE / "cases_real_v4_s4.json",
        HERE / "cases_real_v4_s4_B.json",
        HERE / "real_v4_s4_labels_A.json",
        HERE / "real_v4_s4_labels_B.json",
        HERE / "real_v4_s4_labels_final.json",
        HERE / "cases_real_v4_s4_labeled.json"
    ]

    all_files = files_to_hash + script_files + json_files
    print("\n| File | sha256 |")
    print("|---|---|")
    result = {}
    for f in all_files:
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        rel_path = f.relative_to(HERE.parent.parent.parent).as_posix()
        print(f"| `{rel_path}` | `{h}` |")
        result[rel_path] = h
    return result


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "agree"
    if cmd in ("agree", "--agree"):
        run_agree()
    elif cmd in ("build", "--build"):
        build_labeled_set()
    elif cmd in ("hash", "--hash"):
        compute_hashes()
    elif cmd in ("all", "--all"):
        run_agree()
        build_labeled_set()
        compute_hashes()
    else:
        print(f"Lệnh không hợp lệ: {cmd}. Dùng 'agree', 'build', 'hash', hoặc 'all'.")


if __name__ == "__main__":
    main()

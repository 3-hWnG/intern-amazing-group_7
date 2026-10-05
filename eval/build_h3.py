"""Dựng cases_h3.jsonl (HOLDOUT-3 mù) độc lập: nạp phần DSL của build_cases.py (cắt trước 'import cases_new',
KHÔNG ghi cases.jsonl), chạy cases_h3.run, đổi id 'hold-' -> 'h3-'. Chạy: python build_h3.py"""
import json, os, sys, types
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "build_cases.py"), encoding="utf-8").read().split("import cases_new")[0]
B = types.ModuleType("B"); B.__file__ = os.path.join(HERE, "build_cases.py")
exec(compile(src, "build_cases.py", "exec"), B.__dict__)
import cases_h3
B.CASES.clear(); B.ERR.clear(); B._n.clear()  # bỏ 185 câu DEV dựng ở phần đầu build_cases
cases_h3.run(B)
assert not B.ERR, "\n".join(B.ERR)
out = []
for c in B.CASES:
    assert c["split"] == "holdout3"
    c["id"] = c["id"].replace("hold-", "h3-", 1)
    out.append(c)
with open(os.path.join(HERE, "cases_h3.jsonl"), "w", encoding="utf-8") as f:
    for c in out:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print(len(out), dict(Counter(c["category"] for c in out)))

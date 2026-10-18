"""Ghi nhãn: python research/clarify/label.py "0:X 1:O 2:A 3:C ..."  (ghi đè nhãn cũ cùng số). Nhãn: A trả lời · C hỏi lại · O từ chối · X loại (không phải câu hỏi)."""
import json, os, sys
P = "research/clarify/labels.json"
d = json.load(open(P, encoding="utf-8")) if os.path.exists(P) else {}
for tok in " ".join(sys.argv[1:]).split():
    n, lab = tok.split(":")
    assert lab in ("A", "C", "O", "X"), tok
    d[n] = lab
json.dump(dict(sorted(d.items(), key=lambda kv: int(kv[0]))), open(P, "w", encoding="utf-8"), indent=0)
print(len(d), "nhãn;", {k: list(d.values()).count(k) for k in "ACOX"})

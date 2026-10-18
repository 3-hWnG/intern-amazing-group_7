"""In mẫu để gán nhãn: câu hỏi + 3 thủ tục gần nhất trong dữ liệu (KHÔNG in hành vi của hệ thống). python research/clarify/show.py <từ> <đến>"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
a, b = int(sys.argv[1]), int(sys.argv[2])
for l in open("research/clarify/sample.jsonl", encoding="utf-8"):
    x = json.loads(l)
    if a <= x["n"] < b:
        q = x["q"] if len(x["q"]) <= 330 else x["q"][:240] + " … " + x["q"][-90:]
        print(f"{x['n']} [{x['src']}] {q}")
        print("     ~ " + " | ".join(n[:70] for n in x["cand_names"][:3]))

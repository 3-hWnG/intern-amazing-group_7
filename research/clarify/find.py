"""Tra tên thủ tục trong DB bản 3 (proc_flat): python research/clarify/find.py "cụm 1" "cụm 2" ...  (* = trong phạm vi trả lời)"""
import sqlite3, sys, glob
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from data.textutil import fold
c = sqlite3.connect(sorted(glob.glob("data/runtime/knowledge/3-*.db"))[-1])
for t in sys.argv[1:]:
    rows = c.execute("SELECT in_scope, name, province FROM proc_flat WHERE name_fold LIKE ? ORDER BY in_scope DESC, province IS NOT NULL, length(name)", (f"%{fold(t)}%",)).fetchall()
    print(f"== {t}: {len(rows)} (trong phạm vi {sum(r[0] for r in rows)})")
    for s, n, p in rows[:8]:
        print(("  * " if s else "    ") + n[:110] + (f"  [{p}]" if p else ""))

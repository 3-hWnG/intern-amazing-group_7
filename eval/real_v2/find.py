"""Tra proc_id khi GÁN NHÃN (REAL_V1_GUIDE.md mục 4, cách 3): đọc thẳng bảng proc_flat của DB bản 3 bằng SQLite, KHÔNG qua truy hồi của hệ thống.

    python eval/real_v2/find.py "tam tru" "xac nhan"     # mọi thủ tục có TẤT CẢ các cụm (chữ bỏ dấu) trong tên; in_scope=1 trước
    python eval/real_v2/find.py -a "tam tru"              # kể cả bản riêng của tỉnh / ngoài cấp xã
"""
import os
import sqlite3
import sys
import unicodedata

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "runtime", "knowledge", "3-423eff02f8.db")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def main(args):
    allv = "-a" in args
    terms = [fold(a) for a in args if a != "-a"]
    c = sqlite3.connect(DB)
    rows = c.execute("SELECT proc_id, name, in_scope, province, levels FROM proc_flat").fetchall()
    hits = [r for r in rows if all(t in fold(r[1]) for t in terms) and (allv or r[2] == 1)]
    hits.sort(key=lambda r: (-r[2], r[3] or "", r[1]))
    for pid, name, ins, prov, lv in hits[:40]:
        print(f"{pid} in={ins} {('['+prov+'] ') if prov else ''}{name[:120]} | {lv}")
    print(f"({len(hits)} kết quả)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])

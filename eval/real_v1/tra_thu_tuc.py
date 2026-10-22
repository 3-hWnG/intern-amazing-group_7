"""Tra nhanh thủ tục bản 3 theo từ khoá, để gán nhãn và để demo (không dùng truy hồi của hệ thống).

    python eval/real_v1/tra_thu_tuc.py "tam tru" "chung minh nhan dan"      # mỗi cụm một lần tra; chữ có hoặc không dấu đều được
    python eval/real_v1/tra_thu_tuc.py "dang ky + tam tru"                  # dấu + = phải có đủ các từ
    python eval/real_v1/tra_thu_tuc.py --id 1.116410                        # xem một mã: tên, cơ quan, trường hợp, link Cổng

Tự mở rộng viết tắt (CMND -> chứng minh nhân dân, CCCD -> căn cước, GPLX -> giấy phép lái xe, BHXH, BHYT, LLTP...). Dấu `*` = trong phạm vi trả lời
(cấp xã dùng chung toàn quốc, `in_scope = 1`). Cần DB bản 3 đã dựng (`data/runtime/knowledge/*.db`) và `data/snapshot/procedures_v3.jsonl`.
"""
import glob
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from data.textutil import fold  # noqa: E402

ALIAS = {"cmnd": "chung minh nhan dan", "cccd": "can cuoc", "gplx": "giay phep lai xe", "bhxh": "bao hiem xa hoi", "bhyt": "bao hiem y te",
         "lltp": "ly lich tu phap", "gcn": "giay chung nhan", "hktt": "ho khau thuong tru", "kt3": "tam tru", "dkkd": "dang ky kinh doanh"}


def db():
    dbs = sorted(glob.glob(os.path.join(ROOT, "data", "runtime", "knowledge", "*.db")))
    best = None
    for p in dbs:
        c = sqlite3.connect(p)
        if c.execute("select count(*) from proc_flat").fetchone()[0] == 1517:   # bản 3
            best = c
    if best is None:
        sys.exit("không thấy DB bản 3 (1.517 thủ tục) trong data/runtime/knowledge")
    return best


def expand(term: str) -> str:
    return " ".join(ALIAS.get(w, w) for w in fold(term).split())


def search(c, query: str, limit=12):
    parts = [expand(p).strip() for p in query.split("+")]
    cond = " and ".join("name_fold like ?" for _ in parts)
    rows = c.execute(f"select proc_id,name,in_scope,province from proc_flat where {cond} order by in_scope desc, province is not null, length(name) limit ?",
                     [f"%{p}%" for p in parts] + [limit]).fetchall()
    n = c.execute(f"select count(*),sum(in_scope) from proc_flat where {cond}", [f"%{p}%" for p in parts]).fetchone()
    return rows, n


def info(pid: str):
    for line in open(os.path.join(ROOT, "data", "snapshot", "procedures_v3.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if r["proc_id"] == pid:
            return r
    return None


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--id":
        r = info(args[1])
        if not r:
            sys.exit("không có mã này")
        print(r["proc_id"], r["name"])
        print("cơ quan:", r.get("executing_agency"), "| tỉnh:", r.get("province"))
        print("link:", r.get("portal_url"))
        seen = []
        for ch in r.get("checklist") or []:
            cn = ch.get("case_name")
            if cn and cn not in seen:
                seen.append(cn)
        for cn in seen[:12]:
            print("  trường hợp:", cn[:150])
        return
    c = db()
    for q in args:
        rows, n = search(c, q)
        print(f"== {q}: {n[0]} thủ tục ({n[1] or 0} trong phạm vi)")
        for pid, name, ins, prov in rows:
            print(f"  {'*' if ins else ' '}{pid} {name[:100]}{' [' + prov + ']' if prov else ''}")


if __name__ == "__main__":
    main()

"""G4.2: bộ đo riêng cho liệt kê / đếm (text-to-SQL). Đáp án do CODE tính từ proc_flat (chỉ thủ tục trong phạm vi), không do LLM.
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> python run_server.py eval/build_listsql_set.py   -> eval/cases_listsql.jsonl
Khuôn: liệt kê / đếm theo lĩnh vực, lĩnh vực + nộp trực tuyến, lĩnh vực + số ngày giải quyết, liệt kê / đếm theo chữ trong tên.
Mỗi ca: {id, split (dev|test, xen kẽ theo seed), kind, question, gold: {"names": [...]} hoặc {"count": n}}.
Chỉnh lời dặn chỉ được nhìn split dev; số báo cáo là split test."""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "server"))
from system3.data import api  # noqa: E402
from system3.data.textutil import fold  # noqa: E402

rng = random.Random(42)
c = api.connect()
q = lambda sql, *a: c.execute(sql, a).fetchall()
doms = [d for d, n in q("SELECT domain, COUNT(*) n FROM proc_flat WHERE in_scope=1 GROUP BY domain HAVING n >= 3 ORDER BY n DESC")]
KW = ["khai sinh", "kết hôn", "khai tử", "giám hộ", "chứng thực", "thường trú", "tạm trú", "hộ kinh doanh", "hợp tác xã",
      "trợ cấp", "mai táng", "thương binh", "liệt sĩ", "căn cước", "đất", "nuôi con nuôi", "giấy phép", "đăng ký"]
cases = []


def names(where, *a):
    return [r[0] for r in q(f"SELECT name FROM proc_flat WHERE in_scope=1 AND {where} ORDER BY name", *a)]


def add(kind, question, gold):
    cases.append({"kind": kind, "question": question, "gold": gold})


L1 = ["Liệt kê các thủ tục thuộc lĩnh vực {d}.", "Cho mình danh sách thủ tục lĩnh vực {d}", "Lĩnh vực {d} có những thủ tục nào?"]
C1 = ["Có bao nhiêu thủ tục về {d}?", "Lĩnh vực {d} có mấy thủ tục?", "Đếm giúp mình số thủ tục lĩnh vực {d}"]
for i, d in enumerate(doms[:16]):
    add("list_domain", L1[i % 3].format(d=d), {"names": names("domain=?", d)})
    add("count_domain", C1[i % 3].format(d=d), {"count": len(names("domain=?", d))})
for d in doms[:12]:
    on = names("domain=? AND online=1", d)
    if on:
        add("list_domain_online", f"Những thủ tục nào thuộc lĩnh vực {d} nộp trực tuyến được?", {"names": on})
for d in doms[:12]:
    ds = sorted({r[0] for r in q("SELECT days_max FROM proc_flat WHERE in_scope=1 AND domain=? AND days_max IS NOT NULL", d)})
    if len(ds) >= 2:
        n = int(ds[len(ds) // 2]) or 1
        add("list_domain_days", f"Liệt kê các thủ tục lĩnh vực {d} giải quyết trong vòng {n} ngày", {"names": names("domain=? AND days_max<=?", d, n)})
for i, kw in enumerate(KW):
    got = names("name_fold LIKE ?", f"%{fold(kw)}%")
    if len(got) >= 2:
        add("list_kw", (["Liệt kê các thủ tục liên quan đến {k}", "Những thủ tục nào có chữ \"{k}\" trong tên?"][i % 2]).format(k=kw), {"names": got})
        add("count_kw", (["Có bao nhiêu thủ tục liên quan đến {k}?", "Có mấy thủ tục {k}?"][i % 2]).format(k=kw), {"count": len(got)})
rng.shuffle(cases)
for i, x in enumerate(cases):
    x["id"], x["split"] = f"ls-{i:03d}", "dev" if i % 2 == 0 else "test"
out = os.path.join(HERE, "cases_listsql.jsonl")
with open(out, "w", encoding="utf-8") as f:
    for x in sorted(cases, key=lambda x: x["id"]):
        f.write(json.dumps({k: x[k] for k in ("id", "split", "kind", "question", "gold")}, ensure_ascii=False) + "\n")
print(len(cases), "ca ->", out)

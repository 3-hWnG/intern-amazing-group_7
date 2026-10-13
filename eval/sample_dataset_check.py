"""Mục 3.4 của kế hoạch: lấy mẫu bản ghi thủ tục để đối chiếu với nguồn (cổng dichvucong.gov.vn).

Chạy:  python eval/sample_dataset_check.py [--n 50] [--seed 7]
Ghi `eval/results/dataset_check_sample.json` (mẫu cố định theo seed) và `eval/results/dataset_check_sheet.md`
(phiếu đối chiếu: mỗi bản ghi một khối, cột "đúng/sai" để người kiểm điền tay).
Sau khi điền: `python eval/sample_dataset_check.py --score eval/results/dataset_check_verdicts.json` tính tỷ lệ đúng.

Lấy mẫu phân tầng theo `domain` (lĩnh vực) để không dồn vào vài lĩnh vực lớn. Mỗi bản ghi kiểm 6 trường mà người dân hay hỏi.
"""
import argparse, json, random, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshot" / "procedures.jsonl"
OUT = ROOT / "eval" / "results"
FIELDS = ["name", "executing_agency", "processing_time_text", "fees", "legal_basis", "decision_number"]


def load():
    return [json.loads(l) for l in SNAP.open(encoding="utf-8")]


def sample(rows, n, seed):
    rng = random.Random(seed)
    by = collections.defaultdict(list)
    for r in rows:
        by[r.get("domain") or "?"].append(r)
    for v in by.values():
        rng.shuffle(v)
    keys = sorted(by)
    rng.shuffle(keys)
    out = []
    while len(out) < n and any(by.values()):          # vòng tròn qua các lĩnh vực
        for k in keys:
            if by[k] and len(out) < n:
                out.append(by[k].pop())
    return out


def brief(r):
    fees = "; ".join(f"{f.get('amount_value')} đ ({(f.get('amount_text') or '')[:60]})" for f in (r.get("fees") or [])[:3]) or "(không có)"
    law = "; ".join(l.get("doc_code", "") for l in (r.get("legal_basis") or [])[:4]) or "(không có)"
    return {"name": r["name"], "executing_agency": r.get("executing_agency") or "(trống)",
            "processing_time_text": r.get("processing_time_text") or "(trống)", "fees": fees,
            "legal_basis": law, "decision_number": r.get("decision_number") or "(trống)"}


def write_sheet(rows):
    OUT.mkdir(exist_ok=True)
    (OUT / "dataset_check_sample.json").write_text(
        json.dumps([r["proc_id"] for r in rows], ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# Phiếu đối chiếu dữ liệu với nguồn", "",
         f"{len(rows)} bản ghi, lấy mẫu phân tầng theo lĩnh vực. Mở `portal_url`, so từng trường, điền đúng / sai / không thấy trên nguồn.", ""]
    for i, r in enumerate(rows, 1):
        b = brief(r)
        L += [f"## {i}. {b['name']}", f"- proc_id: `{r['proc_id']}` · lĩnh vực: {r.get('domain')} · nguồn: {r.get('portal_url')}"]
        L += [f"- {k}: {b[k]}  →  [ ] đúng  [ ] sai  [ ] không thấy" for k in FIELDS[1:]]
        L.append("")
    (OUT / "dataset_check_sheet.md").write_text("\n".join(L), encoding="utf-8")


def score(path):
    v = json.load(open(path, encoding="utf-8"))   # {proc_id: {field: "đúng"|"sai"|"không thấy"}}
    c = collections.Counter(x for d in v.values() for x in d.values())
    t = sum(c.values()) or 1
    print(f"{len(v)} bản ghi, {t} ô: đúng {c['đúng']} ({c['đúng']/t:.0%}), sai {c['sai']}, không thấy {c['không thấy']}")
    bf = collections.defaultdict(collections.Counter)
    for d in v.values():
        for k, x in d.items():
            bf[k][x] += 1
    for k, cc in bf.items():
        print(f"  {k}: " + ", ".join(f"{a} {b}" for a, b in cc.items()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--score")
    a = ap.parse_args()
    if a.score:
        score(a.score)
    else:
        rows = sample(load(), a.n, a.seed)
        write_sheet(rows)
        print(f"ghi {len(rows)} bản ghi, {len({r.get('domain') for r in rows})} lĩnh vực -> eval/results/dataset_check_sheet.md")

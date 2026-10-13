"""Mục 3.2 của kế hoạch: gom các bộ test có sẵn về MỘT định dạng chung, mỗi domain một file trong eval/golden/.
Chạy: python eval/build_golden.py     (idempotent; không viết câu mới, chỉ chuyển định dạng)

Một dòng JSON:
  id, domain, type, turns [{role,text}] (lượt cuối là user), question (= lượt user cuối),
  expected {behavior: answer|clarify|apologize, tasks: [{proc_ids, fields}]},
  source (bộ gốc), status: dev | holdout-used | blind (xem docs/EVAL.md về việc không tune trên blind)

Domain có sẵn: thu-tuc (domain 1, System 3). tro-chuyen-chung (domain 2, Friendly) chưa có bộ nào có đáp án
đối chiếu được (hội thoại tự do không có đáp án đúng/sai); file được tạo rỗng để ghi rõ chỗ thiếu.
"""
import collections, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "golden"


def jl(name):
    return [json.loads(l) for l in (HERE / name).open(encoding="utf-8") if l.strip()]


def turns_of(c):
    return c["turns"]


def from_cases(name, status_of):
    for c in jl(name):
        e = c["expected"]
        yield dict(id=c["id"], type=c["category"], turns=turns_of(c), source=name,
                   status=status_of(c),
                   expected=dict(behavior=e.get("behavior", "answer"),
                                 tasks=[dict(proc_ids=t["acceptable_proc_ids"], fields=t.get("fields") or []) for t in e.get("tasks", [])]))


def from_flat(name, status, kind):
    """cases_h4/h5/h6/pseudo_real*.json: q, expect_ids, beh, fields (một số có `turns` nhiều lượt)."""
    for c in json.load((HERE / name).open(encoding="utf-8")):
        items = [(c["id"], [{"role": "user", "text": c["q"]}], c)] if "q" in c else []
        if "turns" in c:
            hist = []
            for i, t in enumerate(c["turns"]):
                hist = hist + [{"role": "user", "text": t["q"]}]
                items.append((f"{c['id']}.{i+1}", list(hist), t))
                hist = hist + [{"role": "assistant", "text": ""}]
        for cid, turns, t in items:
            yield dict(id=cid, type=kind, turns=turns, source=name, status=status,
                       expected=dict(behavior=t["beh"], tasks=[dict(proc_ids=t["expect_ids"], fields=t.get("fields") or [])] if t.get("expect_ids") else []))


def from_team():
    for c in json.load((HERE / "cases_team.json").open(encoding="utf-8")):
        turns = [{"role": "user", "text": q} for q in c["turns"]]
        yield dict(id=c["id"], type=c["group"], turns=turns[-1:] if len(turns) == 1 else turns, source="cases_team.json", status="blind",
                   expected=dict(behavior=c["beh"], tasks=[dict(proc_ids=c["procs"], fields=[])] if c.get("procs") else []))


def main():
    rows = []
    rows += from_cases("cases.jsonl", lambda c: "holdout-used" if c.get("split") == "holdout" else "dev")
    rows += from_cases("cases_p16_aside.jsonl", lambda c: "dev")
    rows += from_cases("cases_ctx.jsonl", lambda c: "dev")
    rows += from_cases("cases_h2.jsonl", lambda c: "holdout-used")      # bị lộ một phần
    rows += from_cases("cases_h3.jsonl", lambda c: "blind")
    for name, kind in (("cases_h4.json", "blind-h4"), ("cases_h5.json", "blind-h5"), ("cases_h6.json", "blind-h6"),
                       ("cases_pseudo_real.json", "pseudo-real"), ("cases_pseudo_real2.json", "pseudo-real"), ("cases_pseudo_real3.json", "pseudo-real")):
        rows += from_flat(name, "blind", kind)
    rows += from_team()
    seen, out = set(), []
    for r in rows:
        key = r["id"]
        if key in seen:
            continue
        seen.add(key)
        r["domain"] = "thu-tuc"
        r["question"] = next(t["text"] for t in reversed(r["turns"]) if t["role"] == "user")
        out.append(r)
    OUT.mkdir(exist_ok=True)
    with (OUT / "thu-tuc.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (OUT / "tro-chuyen-chung.jsonl").write_text("", encoding="utf-8")
    c = collections.Counter(r["status"] for r in out)
    b = collections.Counter(r["expected"]["behavior"] for r in out)
    print(f"thu-tuc: {len(out)} ca; status {dict(c)}; hành vi {dict(b)}")
    print("tro-chuyen-chung: 0 ca (chưa có bộ có đáp án)")


if __name__ == "__main__":
    main()

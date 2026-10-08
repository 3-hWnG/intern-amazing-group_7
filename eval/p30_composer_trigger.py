"""Phase 30 (họ B): đếm số lượt mà bước LLM sinh chữ (Answer Composer) sẽ được gọi vì task có `conditions`, trên bộ KHÔNG mù:
cases.jsonl (DEV + holdout cũ), cases_ctx.jsonl, cases_p26.jsonl, cases_composer.jsonl (ca tự soạn own-*).
Mỗi lượt có điều kiện được phân loại:
  user  : phần chữ ĐẶC TRƯNG của mục condition_index được chọn (bỏ chữ trong tên thủ tục + chữ hư) có trong lời người dùng (>= 1 chữ nội dung) -> điều kiện do người dùng nêu thật;
  spur  : không có chữ nội dung nào của mục xuất hiện trong lời người dùng (khớp bằng chữ hư/chữ trong tên) -> điều kiện Planner/Policy tự gán.
Chạy: python run_server.py eval/p30_composer_trigger.py [--name p30_trig] [-v]. Ghi results/<name>.json."""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(HERE, "..", "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from policy.policy import _TOK, _CGEN  # noqa: E402
from system3.data import api  # noqa: E402
from system3.data.textutil import fold  # noqa: E402
from system3.retrieval.query import STOP  # noqa: E402

conn = api.connect()
FILES = ["cases.jsonl", "cases_ctx.jsonl", "cases_p26.jsonl", "cases_composer.jsonl"]


def turns_of(c):
    if "turns" in c:
        return c["turns"]
    return [{"role": "user", "text": c["question"]}]


def classify(rt, user_text):
    name = set(_TOK.findall(fold(rt.procedure_label)))
    user = set(_TOK.findall(fold(user_text))) - STOP
    out = []
    for cond in rt.conditions:
        tk = {t for t in _TOK.findall(fold(cond)) if len(t) > 1 and t not in name and t not in _CGEN and t not in STOP}
        out.append("user" if any(t in user for t in tk) else "spur")
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--name", default="p30_trig"); ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    seen, rows = set(), []
    for fn in FILES:
        for l in open(os.path.join(HERE, fn), encoding="utf-8"):
            c = json.loads(l)
            key = c["id"]
            if key in seen:
                continue
            seen.add(key)
            turns = turns_of(c)
            if turns[-1]["role"] != "user":
                continue
            pc = pre_check(turns[-1]["text"])
            turns = turns[:-1] + [{"role": "user", "text": pc["text"]}]
            p = make_plan(turns, use_llm=False)
            r = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
            for rt in r.tasks:
                if rt.route == "direct" and rt.conditions:
                    rows.append({"id": c["id"], "file": fn, "q": pc["text"][:100], "proc": rt.procedure_label[:50], "conds": [x[:80] for x in rt.conditions], "cls": classify(rt, pc["text"])})
                    if a.v:
                        print(rows[-1]["id"], rows[-1]["cls"], rows[-1]["q"], "|", rows[-1]["conds"])
    n = len(seen)
    spur = sum(1 for r in rows if "spur" in r["cls"] and "user" not in r["cls"])
    print(f"{len(rows)} lượt gọi composer / {n} ca; điều kiện do người dùng nêu: {len(rows) - spur}; tự gán/khớp chữ hư: {spur}")
    json.dump({"n_cases": n, "triggers": len(rows), "spurious": spur, "rows": rows}, open(os.path.join(HERE, "results", a.name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

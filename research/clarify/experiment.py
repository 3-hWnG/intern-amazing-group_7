"""So các cách hỏi lại (công tắc môi trường) trên dev (golden, một lượt), cases_p30 và câu thật đã gán nhãn — KHÔNG dùng bộ mù.
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> S3_USE_LLM=0 python run_server.py research/clarify/experiment.py [tên cấu hình ...]
Mỗi cấu hình = các công tắc bật. Nhãn: A trả lời · C hỏi lại · O từ chối. Thẻ hỏi TỈNH (D5) với câu nhãn A tính là đúng ở cột "A đúng*".
Ghi research/clarify/results_<cấu hình>.json (hành vi từng câu) để xem ca nào đổi."""
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "eval"), os.path.join(ROOT, "server")]
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from system3.data import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
FLAGS = {"M1": "S3_CLARIFY_FILLER", "M2": "S3_CLARIFY_NOPROC"}   # M3 (cụm chung nhiều họ) đã thử, không đổi ca nào -> gỡ khỏi code
CONFIGS = {"base": [], "M1": ["M1"], "M2": ["M2"], "M1+M2": ["M1", "M2"]}
names = sys.argv[1:] or list(CONFIGS)
rows = [json.loads(l) for l in open(os.path.join(HERE, "features.jsonl"), encoding="utf-8")]
conn = api.connect()


def run(flags):
    for k, env in FLAGS.items():
        os.environ[env] = "1" if k in flags else "0"
    out = []
    for r in rows:
        pc = pre_check(r["q"])
        p = make_plan([{"role": "user", "text": pc["text"]}])
        res = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
        beh = {"chitchat": "answer"}.get(res.behavior, res.behavior)
        out.append({"q": r["q"], "set": r["set"], "label": r["label"], "beh": beh, "kind": (res.clarify or {}).get("kind", "")})
    return out


def table(name, out):
    g = collections.defaultdict(list)
    for o in out:
        g[o["set"].split("-")[0]].append(o)
    line = [f"{name:<12}"]
    for s in ("dev", "p30", "real"):
        v = g[s]
        C = [o for o in v if o["label"] == "C"]
        A = [o for o in v if o["label"] == "A"]
        O = [o for o in v if o["label"] == "O"]
        c_ok = sum(o["beh"] == "clarify" for o in C)
        a_ok = sum(o["beh"] == "answer" for o in A)
        a_ok2 = sum(o["beh"] == "answer" or o["kind"] == "province" for o in A)
        o_ok = sum(o["beh"] == "apologize" for o in O)
        beh = sum({"A": "answer", "C": "clarify", "O": "apologize"}[o["label"]] == o["beh"] for o in v)
        line.append(f"{s}: C {c_ok}/{len(C)} A {a_ok}/{len(A)} (A* {a_ok2}) O {o_ok}/{len(O)} | hành vi {beh}/{len(v)}")
    print("  ".join(line), flush=True)


for n in names:
    out = run(CONFIGS[n])
    json.dump(out, open(os.path.join(HERE, f"results_{n}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    table(n, out)

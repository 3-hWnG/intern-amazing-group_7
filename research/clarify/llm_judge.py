"""M4: nhờ model trả lời (qwen3 4B, Ollama) phán câu đã đủ rõ để chọn MỘT thủ tục chưa — chỉ với câu ngắn (<= 15 chữ) mà luật đã chọn trả lời.
    PYTHONIOENCODING=utf-8 S3_DATA_DB=<db bản 3> S3_CLARIFY_FILLER=1 S3_CLARIFY_NOPROC=1 python run_server.py research/clarify/llm_judge.py
Ghi research/clarify/llm_judge.json. Không dùng bộ mù."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "eval"), os.path.join(ROOT, "server")]
from core.llm import chat_json  # noqa: E402
from planner import plan as make_plan  # noqa: E402
from policy import check, pre_check  # noqa: E402
from system3.data import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
conn = api.connect()
name = lambda p: conn.execute("SELECT name FROM procedures WHERE proc_id=?", (p,)).fetchone()[0]
MODE = os.environ.get("JUDGE_MODE", "pick")
SYSTEM = ("Bạn giúp một trợ lý thủ tục hành chính cấp xã. Cho câu hỏi của người dân và danh sách thủ tục đánh số. "
          "Chọn số của thủ tục người dân cần. Phần lớn câu hỏi chỉ cần thủ tục thông dụng nhất. "
          "Chỉ trả 0 khi câu hỏi hợp NGANG NHAU với từ hai thủ tục khác hẳn nhau và không thể đoán. Chỉ trả JSON.")
SCHEMA = {"type": "object", "properties": {"chon": {"type": "integer"}}, "required": ["chon"]}
rows = [json.loads(l) for l in open(os.path.join(HERE, "features.jsonl"), encoding="utf-8")]
out, t0 = [], time.time()
for r in rows:
    if len(r["q"].split()) > 15:
        continue
    pc = pre_check(r["q"])
    p = make_plan([{"role": "user", "text": pc["text"]}])
    res = check(p, user_text=pc["text"], conn=conn, flags=pc["flags"])
    if res.behavior != "answer" or len(res.tasks) != 1 or res.tasks[0].route != "direct":
        continue
    t = p.tasks[0]
    cands = [c for c in dict.fromkeys([res.tasks[0].procedure_id] + list(t.candidates or []))][:5]
    user = f"Câu hỏi: {r['q']}\nCác thủ tục:\n" + "\n".join(f"{i}. {name(c)}" for i, c in enumerate(cands, 1))
    try:
        d = chat_json(SYSTEM, user, schema=SCHEMA, think=False, timeout=30, num_predict=20)
        clear = d.get("chon") not in (0, None)
    except Exception as e:   # noqa: BLE001
        clear = None
    out.append({"set": r["set"], "label": r["label"], "q": r["q"], "clear": clear})
print(len(out), "câu,", f"{time.time() - t0:.0f}s")
json.dump(out, open(os.path.join(HERE, f"llm_judge_{MODE}.json"), "w", encoding="utf-8"), ensure_ascii=False)
for s in ("dev", "p30", "real"):
    v = [o for o in out if o["set"].startswith(s)]
    C = [o for o in v if o["label"] == "C"]; A = [o for o in v if o["label"] == "A"]; O = [o for o in v if o["label"] == "O"]
    print(f"{s}: C được hỏi lại {sum(o['clear'] is False for o in C)}/{len(C)} | A bị hỏi lại thừa {sum(o['clear'] is False for o in A)}/{len(A)}"
          f" | O (đang trả lời nhầm) chuyển sang hỏi lại {sum(o['clear'] is False for o in O)}/{len(O)} | lỗi gọi {sum(o['clear'] is None for o in v)}")

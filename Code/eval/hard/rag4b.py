"""Baseline ngoài cho bài báo 1 (trưởng nhóm duyệt 25/10/2026): RAG thường + model 4B TỰ QUYẾT trả lời / hỏi lại / từ chối.

Không dùng luật của System 3. Mỗi câu:
  1. bge-m3 (Ollama) lấy 5 thủ tục trong phạm vi (in_scope = 1, 542 thủ tục) gần nghĩa nhất với câu hỏi nguyên văn
     (cùng chỉ mục vector với phương án B, retrieval/semantic.py);
  2. qwen3:4b-instruct nhận câu hỏi + 5 tên thủ tục, trả JSON {"action": answer | clarify | refuse, "choice": 0..5}.
     Model chọn SỐ THỨ TỰ trong danh sách, không tự viết mã thủ tục.
Chọn prompt trên DEV như hệ thống của nhóm (công bằng): v1 viết trước lượt chạy đầu; sau lượt v1 trên dev (model chọn "clarify" quá
nhiều: 123/220 câu từ chối, 39/55 câu trả lời) viết thêm đúng hai biến thể, ghi trước khi chạy chúng: v2 = quy tắc quyết định theo thứ tự,
chỉ hỏi lại khi không rõ người hỏi muốn làm việc gì; v3 = v2 + mô tả thủ tục (tên, lĩnh vực, kết quả, đối tượng như phương án B).
Chọn biến thể có độ chính xác cân bằng cao nhất trên dev (hoà thì trả lời đúng trọn), rồi chạy test (real_v2) MỘT lần. RAG4B_PROMPT=v1|v2|v3.
Chấm như eval/hard/dev.py (metrics.summarize). Đầu ra model lưu đệm ở eval/hard/results/rag4b_cache.jsonl để chấm lại không gọi model.

    python run_server.py eval/hard/rag4b.py --name dev_rag4b
    python run_server.py eval/hard/rag4b.py --final real_v2 --name real_v2_rag4b
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
ROOT = os.path.dirname(EVAL)
os.environ.setdefault("S3_DATA_DB", os.path.join(ROOT, "data", "runtime", "knowledge", "3-423eff02f8.db"))
sys.path[:0] = [EVAL, HERE, os.path.join(ROOT, "server")]
from metrics import summarize, line  # noqa: E402
from thermal import guard, low_priority  # noqa: E402

SETS = {"real_v1": "real_v1/cases_real_v1_labeled.json", "real_v2": "real_v2/cases_real_v2_labeled.json",
        "real_v4": "real_v4/cases_real_v4_labeled.json"}
CACHE = os.path.join(HERE, "results", "rag4b_cache.jsonl")
K = 5
ACTIONS = ("answer", "clarify", "refuse")
GOT = {"answer": "answer", "clarify": "clarify", "refuse": "apologize"}
SCHEMA = {"type": "object", "properties": {"action": {"type": "string", "enum": list(ACTIONS)}, "choice": {"type": "integer", "minimum": 0, "maximum": K}},
          "required": ["action", "choice"]}
SYSTEM = """Bạn là trợ lý của bộ phận một cửa cấp xã. Bạn nhận câu hỏi của người dân và 5 thủ tục hành chính có thể liên quan do hệ thống tìm kiếm đưa ra.
Hãy quyết định cách xử lý, KHÔNG viết câu trả lời. Trả JSON {"action", "choice"}.
action:
- "answer": người hỏi muốn biết cách làm, giấy tờ, nơi nộp, thời gian, lệ phí hoặc điều kiện của một thủ tục hành chính, và đúng MỘT thủ tục trong danh sách khớp với điều họ cần. choice = số thứ tự của thủ tục đó (1-5).
- "clarify": người hỏi hỏi về thủ tục, nhưng từ hai thủ tục trong danh sách trở lên đều có thể đúng mà câu hỏi không đủ thông tin để chọn, hoặc câu hỏi không nêu thủ tục nào. choice = 0.
- "refuse": câu hỏi không phải hỏi cách làm thủ tục (hỏi tình trạng hồ sơ của chính mình, khiếu nại, kiến nghị, hỏi luật hay mức phạt, chế độ nội bộ của cán bộ, chuyện khác), hoặc không thủ tục nào trong danh sách khớp. choice = 0."""
SYSTEM_V2 = """Bạn là cán bộ bộ phận một cửa cấp xã. Bạn nhận câu hỏi của người dân và 5 thủ tục hành chính có thể liên quan do hệ thống tìm kiếm đưa ra.
Hãy quyết định cách xử lý, KHÔNG viết câu trả lời. Trả JSON {"action", "choice"}. Xét lần lượt:
1. Câu hỏi KHÔNG hỏi cách làm một thủ tục (hỏi tình trạng hồ sơ của chính mình, khiếu nại, kiến nghị, hỏi luật hay mức phạt, chế độ nội bộ của cán bộ, chuyện khác) -> "refuse", choice = 0.
2. Có hỏi cách làm thủ tục (giấy tờ, nơi nộp, thời gian, lệ phí, điều kiện, các bước) và một thủ tục trong danh sách khớp với việc người hỏi cần làm -> "answer", choice = số thứ tự của thủ tục khớp nhất (1-5). Hai thủ tục gần giống nhau thì chọn cái khớp nhất, không hỏi lại.
3. Câu hỏi hoàn toàn không cho biết người hỏi muốn làm việc gì (ví dụ "thủ tục cần giấy tờ gì?") -> "clarify", choice = 0.
4. Có hỏi cách làm thủ tục nhưng không thủ tục nào trong danh sách khớp -> "refuse", choice = 0."""
PROMPTS = {"v1": SYSTEM, "v2": SYSTEM_V2, "v3": SYSTEM_V2}


def _load_cache() -> dict:
    out = {}
    if os.path.exists(CACHE):
        for l in open(CACHE, encoding="utf-8"):
            if l.strip():
                d = json.loads(l)
                out[d["key"]] = d["out"]
    return out


def decide(q: str, cands: list[dict], cache: dict) -> dict:
    from core.llm import chat_json, model_name
    v = os.environ.get("RAG4B_PROMPT", "v1")
    system = PROMPTS[v]
    show = (lambda c: c["text"]) if v == "v3" else (lambda c: c["name"])
    user = "Câu hỏi:\n" + q[:1800] + "\n\nCác thủ tục:\n" + "\n".join(f"{i + 1}. {show(c)}" for i, c in enumerate(cands))
    key = hashlib.sha1(f"{model_name()}|{system}|{user}".encode("utf-8")).hexdigest()
    if key in cache:
        return cache[key]
    try:
        raw = chat_json(system, user, schema=SCHEMA, think=False, timeout=60.0, num_predict=40)
    except Exception as exc:          # lỗi / quá hạn: ghi lại, tính là từ chối (hệ thống không trả lời được)
        raw = {"error": str(exc)[:200]}
    out = {"action": raw.get("action") if raw.get("action") in ACTIONS else None, "choice": raw.get("choice"), "raw": raw}
    cache[key] = out
    with open(CACHE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"key": key, "q": q[:120], "out": out}, ensure_ascii=False) + "\n")
    return out


def main(argv: list[str]) -> None:
    from system3.retrieval import semantic
    args = {k: v for k, v in zip(argv[::2], argv[1::2])}
    final = args.get("--final")
    src = SETS[final] if final else SETS["real_v1"]
    name = args.get("--name", "dev_rag4b")
    low_priority()
    cases = json.load(open(os.path.join(EVAL, src), encoding="utf-8"))
    conn = sqlite3.connect(os.environ["S3_DATA_DB"])
    cache = _load_cache()
    rows, bad = [], 0
    duty = float(os.environ.get("THERMAL_DUTY", "0.5"))
    t0 = time.time()
    for c in cases:
        guard(every=3, label=c["id"])
        tq = time.time()
        q = c["q"]
        cands = semantic.candidates(conn, q[:2000], [], k_dense=K)[:K]
        d = decide(q, cands, cache)
        act, ch = d["action"], d["choice"]
        ok_choice = isinstance(ch, int) and 1 <= ch <= len(cands)
        if act is None or (act == "answer" and not ok_choice):
            bad += 1
        got = GOT.get(act, "apologize") if not (act == "answer" and not ok_choice) else "apologize"
        tops = [cands[ch - 1]["proc_id"]] if got == "answer" else []
        ids = [x["proc_id"] for x in cands]
        exp = c.get("expect_ids") or []
        ranked = list(dict.fromkeys(tops + ids))[:5]
        rr = next((1 / (i + 1) for i, p in enumerate(ranked) if p in exp), 0.0)
        rows.append({"rr": round(rr, 4), "ranked": ranked, "id": c["id"], "q": q, "beh": c["beh"], "exp": exp, "got": got, "tops": tops,
                     "top1": bool(tops) and tops[0] in exp, "top3": any(x in exp for x in ids[:3]), "stratum": c.get("stratum"),
                     "llm": {"action": act, "choice": ch}, "ms": round((time.time() - tq) * 1000, 1)})
        time.sleep(min(2.0, (time.time() - tq) * duty))
    s = summarize(rows)
    print(line(name, s), f"  ({time.time() - t0:.0f} s, đầu ra hỏng {bad})")
    os.makedirs(os.path.join(EVAL, "results"), exist_ok=True)
    json.dump({"name": name, "src": src, "env": {"model": os.environ.get("LLM_MODEL", ""), "k": K, "prompt": os.environ.get("RAG4B_PROMPT", "v1")}, "summary": s, "bad_outputs": bad, "rows": rows},
              open(os.path.join(EVAL, "results", name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])

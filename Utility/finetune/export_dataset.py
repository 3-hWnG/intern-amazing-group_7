"""Xuất dữ liệu fine-tune từ hội thoại THẬT được người dùng chấm "Phù hợp".

Không dùng dataset có sẵn. Mỗi mẫu = (prompt ĐÚNG như lúc chạy -> đầu ra tốt):

    understand  ngữ cảnh + tin nhắn          -> JSON ý định/hỏi lại/truy vấn (messages.intent_json)
    answer      Evidence Pack + câu hỏi      -> câu trả lời có trích dẫn [S#]

Hỏi lại (kind=clarify) được chấm Phù hợp cũng thành mẫu understand — dạy mô hình
biết LÚC NÀO cần hỏi. Đây là fine-tune HÀNH VI (in -> out), không nhồi kiến thức.

    .venv\\Scripts\\python.exe finetune\\export_dataset.py
    .venv\\Scripts\\python.exe finetune\\export_dataset.py --include-unrated-pass
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Utility/finetune/ -> parents[1] = Utility, parents[2] = goc du an.
_ROOT = HERE.parents[1]
sys.path.insert(0, str(_ROOT / "Backend"))
sys.path.insert(0, str(_ROOT))

from config import DB_PATH, MODEL_KNOWLEDGE_CUTOFF  # noqa: E402
from prompts import templates as T  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(HERE / "data" / "train.jsonl"))
    parser.add_argument("--include-unrated-pass", action="store_true",
                        help="thêm câu trả lời PASS kiểm chứng dù chưa được chấm")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT m.*,"
        " (SELECT verdict FROM feedback f WHERE f.message_id = m.id ORDER BY f.id DESC LIMIT 1) rating,"
        " (SELECT pack_json FROM evidence e WHERE e.message_id = m.id ORDER BY e.id DESC LIMIT 1) pack_json"
        " FROM messages m WHERE m.role = 'assistant' ORDER BY m.id").fetchall()

    samples, counts = [], {"understand": 0, "answer": 0}
    for r in rows:
        good = r["rating"] == "phu_hop" or (
            args.include_unrated_pass and r["rating"] is None and r["verdict"] == "PASS")
        if not good or r["kind"] not in ("answer", "clarify") or not r["intent_json"]:
            continue
        prior = [dict(p) for p in conn.execute(
            "SELECT role, content, kind FROM messages WHERE conversation_id = ? AND id < ?"
            " ORDER BY id", (r["conversation_id"], r["id"])).fetchall()]
        if not prior or prior[-1]["role"] != "user":
            continue
        question, history = prior[-1]["content"], prior[:-1][-10:]
        intent = json.loads(r["intent_json"])
        when = datetime.fromisoformat(r["created_at"])
        today = when.strftime("%d/%m/%Y")

        samples.append({"task": "understand", "message_id": r["id"], "messages": [
            {"role": "system", "content": T.understand_system(today, when.year)},
            {"role": "user", "content": T.understand_user(question, history, "", {})},
            {"role": "assistant", "content": json.dumps(intent, ensure_ascii=False)},
        ]})
        counts["understand"] += 1

        if r["kind"] == "answer" and r["pack_json"] and r["verdict"] == "PASS":
            pack = json.loads(r["pack_json"])
            samples.append({"task": "answer", "message_id": r["id"], "messages": [
                {"role": "system", "content": T.answer_system(today, MODEL_KNOWLEDGE_CUTOFF, pack, {})},
                *T.history_messages("", history),
                {"role": "user", "content": T.answer_user(question, intent.get("standalone_question", ""))},
                {"role": "assistant", "content": r["content"]},
            ]})
            counts["answer"] += 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(s, ensure_ascii=False) + "\n" for s in samples)
    out.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    print(f"{len(samples)} mẫu ({counts}) -> {out}  sha256:{digest}")
    if not samples:
        print("Chưa có mẫu nào: dùng ứng dụng, bấm 👍 Phù hợp cho câu trả lời tốt rồi chạy lại.")


if __name__ == "__main__":
    main()

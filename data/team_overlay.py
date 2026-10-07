"""Bù lệ phí từ corpus tuyển chọn của nhóm (data/snapshot/team_corpus.json, nhánh V10.6).
Chỉ dùng khi cổng KHÔNG có lệ phí (fees_clean.kind='none') và tên thủ tục khớp CHÍNH XÁC (bỏ dấu, bỏ 'Thủ tục'). Không đè dữ liệu cổng."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .textutil import fold

CORPUS = Path(__file__).parent / "snapshot" / "team_corpus.json"
SCHEMA = "CREATE TABLE team_fee_overlay (proc_id TEXT NOT NULL, amount_text TEXT NOT NULL, team_id TEXT NOT NULL);"
SOURCE_LABEL = "Bộ dữ liệu nhóm (chuẩn hóa từ cổng)"


def _key(name: str) -> str:
    return re.sub(r"^thu tuc ", "", fold(name)).strip(" .")


def build(conn) -> int:
    conn.execute(SCHEMA)
    by_name: dict[str, list[str]] = {}
    for pid, name in conn.execute("SELECT proc_id, name FROM procedures"):
        by_name.setdefault(_key(name), []).append(pid)
    no_fee = {p for (p,) in conn.execute("SELECT proc_id FROM fees_clean WHERE kind='none'")} - \
             {p for (p,) in conn.execute("SELECT proc_id FROM fees_clean WHERE kind!='none'")}
    n = 0
    for e in json.load(open(CORPUS, encoding="utf-8")):
        texts = list(dict.fromkeys((f.get("amount_text") or "").strip() for f in e.get("fees", [])))
        for pid in by_name.get(_key(e["name"]), []):
            if pid in no_fee:
                for t in filter(None, texts):
                    conn.execute("INSERT INTO team_fee_overlay VALUES (?,?,?)", (pid, t, e["procedure_id"]))
                    n += 1
    return n

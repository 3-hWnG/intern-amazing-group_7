"""Lineage mã thủ tục (G2.3, P08): Cổng cấp lại mã cho thủ tục cũ (Đăng ký thường trú 1.004222 -> 1.116788...), nên mã trong
golden set, thống kê, trạng thái hội thoại của bản trước không còn trong bản mới. Bảng proc_lineage(old_id, new_id, method) của
mỗi DB phiên bản nối mã cũ -> mã trong bản này:
  1. source_id   : cùng ID nội bộ của Cổng (UUID)
  2. name_province: cùng tên chuẩn hoá (bỏ dấu, bỏ "Thủ tục") và cùng tỉnh, và chỉ một ứng viên
  3. manual      : danh sách người duyệt (data/snapshot/lineage_manual.json {"mã cũ": "mã mới"})
  Không ghép được: new_id NULL, method 'unmatched' (đưa vào danh sách cho người duyệt).
Mã cũ lấy từ data/snapshot/procedures.jsonl (bản Gốc — không gian mã của golden set) và các tệp trong S3_LINEAGE_REFS
(System 4 truyền các phiên bản đang giữ)."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from . import SNAPSHOT
from .textutil import fold

SCHEMA = """CREATE TABLE proc_lineage (old_id TEXT PRIMARY KEY, new_id TEXT, method TEXT NOT NULL, old_name TEXT NOT NULL DEFAULT '');"""
MANUAL = SNAPSHOT / "lineage_manual.json"


def _key(name: str, province) -> tuple[str, str]:
    return re.sub(r"^thu tuc ", "", fold(name or "")).strip(" ."), province or ""


def _refs() -> list[Path]:
    out = [SNAPSHOT / "procedures.jsonl"]
    for p in (os.environ.get("S3_LINEAGE_REFS") or "").split(os.pathsep):
        if p.strip() and Path(p).is_file() and Path(p) not in out:
            out.append(Path(p))
    return out


def build(conn) -> dict:
    conn.executescript(SCHEMA)
    cur = conn.execute("SELECT proc_id, source_id, name, province FROM procedures WHERE status='active'").fetchall()
    ids = {r[0] for r in cur}
    by_sid = {r[1]: r[0] for r in cur if r[1]}
    by_name: dict[tuple, list[str]] = {}
    for r in cur:
        by_name.setdefault(_key(r[2], r[3]), []).append(r[0])
    manual = json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.is_file() else {}
    seen: dict[str, tuple] = {}
    for ref in _refs():
        for line in ref.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            old = r["proc_id"]
            if old in ids or old in seen:
                continue
            if old in manual and manual[old] in ids:
                seen[old] = (manual[old], "manual", r.get("name", ""))
            elif r.get("source_id") and r["source_id"] in by_sid:
                seen[old] = (by_sid[r["source_id"]], "source_id", r.get("name", ""))
            elif len(by_name.get(_key(r.get("name"), r.get("province")), [])) == 1:
                seen[old] = (by_name[_key(r.get("name"), r.get("province"))][0], "name_province", r.get("name", ""))
            else:
                seen[old] = (None, "unmatched", r.get("name", ""))
    conn.executemany("INSERT INTO proc_lineage VALUES (?,?,?,?)", [(o, n, m, nm) for o, (n, m, nm) in seen.items()])
    count: dict[str, int] = {}
    for _, m, _ in seen.values():
        count[m] = count.get(m, 0) + 1
    return count


def mapping(conn) -> dict[str, str]:
    """{mã cũ: mã trong DB này} (chỉ các mã ghép được). DB dựng trước G2.3 không có bảng -> {}."""
    try:
        return {r[0]: r[1] for r in conn.execute("SELECT old_id, new_id FROM proc_lineage WHERE new_id IS NOT NULL")}
    except Exception:
        return {}

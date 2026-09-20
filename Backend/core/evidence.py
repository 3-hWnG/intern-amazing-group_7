"""Lấy bằng chứng: MCP search (+ tệp đính kèm của hội thoại) -> Evidence Pack.

Evidence Pack là thứ DUY NHẤT mô hình được dùng làm kiến thức khi trả lời.
Mỗi nguồn có id S1, S2... để câu trả lời trích dẫn và bộ kiểm chứng đối chiếu.
"""

from __future__ import annotations

from config import ATTACH_TOP_K, EVIDENCE_MAX_CHARS, EVIDENCE_TOP_K, SEARCH_MAX_QUERIES
from core import mcp_client


def _renumber(pack: dict) -> dict:
    for i, source in enumerate(pack.get("sources") or [], 1):
        source["id"] = f"S{i}"
    return pack


def gather(question: str, queries: list[str], conversation_id: int | None = None,
           official_bias: bool = True) -> dict:
    queries = [q for q in queries if q] or [question]
    if official_bias:
        # thêm một truy vấn bám nguồn chính thống; engine vẫn xếp hạng tất cả
        queries = queries + [f"{queries[0]} site:gov.vn"]
    queries = list(dict.fromkeys(queries))[:SEARCH_MAX_QUERIES]
    pack = mcp_client.search_evidence(question, queries, EVIDENCE_TOP_K)
    if conversation_id:
        _add_attachments(pack, question, conversation_id)
    return _renumber(pack)


def _add_attachments(pack: dict, query: str, conversation_id: int) -> None:
    from core import chunk_index, resources
    if not resources.has_attachments(conversation_id):
        return
    hits = chunk_index.search(query, conversation_id, top_k=ATTACH_TOP_K)
    extra = [{
        "id": "", "title": f"Tệp đính kèm: {h['filename']}", "url": "",
        "domain": h["filename"], "trust": "attachment", "published_at": "",
        "retrieved_at": pack.get("retrieved_at", ""), "snippet": h["content"][:300],
        "content": h["content"][:1500], "fetched": True, "score": round(h["score"], 2),
    } for h in hits]
    if extra:
        pack["sources"] = extra + list(pack.get("sources") or [])
        pack.setdefault("diagnostics", []).append(f"tệp đính kèm -> {len(extra)} đoạn")


def merge(old: dict, new: dict) -> dict:
    """Tra bổ sung sau khi kiểm chứng chê thiếu bằng chứng: nguồn MỚI đứng trước."""
    seen = {s.get("url") or s.get("title") for s in old.get("sources") or []}
    fresh = [s for s in new.get("sources") or [] if (s.get("url") or s.get("title")) not in seen]
    combined, used = [], 0
    for source in fresh[:3] + list(old.get("sources") or []):
        size = len(source.get("content") or "")
        if len(combined) >= EVIDENCE_TOP_K + 2 or used + size > EVIDENCE_MAX_CHARS + 2000:
            break
        combined.append(source)
        used += size
    out = dict(old)
    out["sources"] = combined
    out["queries"] = list(dict.fromkeys((old.get("queries") or []) + (new.get("queries") or [])))
    out["diagnostics"] = (old.get("diagnostics") or []) + ["-- tra bổ sung --"] + (new.get("diagnostics") or [])
    return _renumber(out)


def public_sources(pack: dict | None, answer: str = "") -> list[dict]:
    """Nguồn hiển thị dưới câu trả lời: chỉ nguồn được trích dẫn (nếu có trích dẫn)."""
    sources = (pack or {}).get("sources") or []
    cited = [s for s in sources if f"[{s['id']}]" in answer or f"{s['id']}," in answer
             or f"{s['id']}]" in answer]
    return [{"id": s["id"], "title": s.get("title", ""), "url": s.get("url", ""),
             "domain": s.get("domain", ""), "trust": s.get("trust", ""),
             "published_at": s.get("published_at", "")}
            for s in (cited or sources)]

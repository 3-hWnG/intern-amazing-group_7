"""Giữ ngữ cảnh hội thoại dài (NV2, 5A): tóm tắt phần cũ + các tin gần nhất, vừa với độ dài ngữ cảnh của model.

Tóm tắt gắn với nhánh: chỉ dùng khi tin cuối được tóm tắt (summary_upto) nằm trên nhánh đang xem.
"""
from __future__ import annotations

from . import db, llm, settings

KEEP_RECENT = 6   # số tin gần nhất không bao giờ bị tóm tắt
SCHEMA = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}


def tokens(text: str) -> int:
    return len(text) // 3 + 1   # ước lượng thô cho tiếng Việt


def as_prompt(m: dict) -> dict:
    """Tin lưu trong DB -> tin gửi cho model. Tin hỏi lại kèm các lựa chọn đã đưa để model biết mình đã hỏi gì."""
    text = m["content"]
    if m["role"] == "assistant" and m["meta"].get("choices"):
        text += "\n(Các lựa chọn đã đưa: " + "; ".join(m["meta"]["choices"]) + ")"
    return {"role": m["role"], "content": text}


def _usable(path: list[dict]) -> list[dict]:
    return [m for m in path if m["status"] != "error" and m["content"]]


def history(cid: str, path: list[dict], system_len: int) -> tuple[str, list[dict]]:
    """(tóm tắt, các tin gửi kèm) cho các tin trên nhánh TRƯỚC tin mới của người dùng."""
    summary, upto = db.get_summary(cid)
    ids = [m["id"] for m in path]
    if summary and upto in ids:
        path = path[ids.index(upto) + 1:]
    else:
        summary = ""
    n = settings.get("FRIENDLY_HISTORY_MESSAGES")
    msgs = [as_prompt(m) for m in _usable(path)][-n:] if n else []
    budget = int(settings.get("FRIENDLY_NUM_CTX") * 0.75) - tokens(summary) - system_len // 3
    while msgs and sum(tokens(m["content"]) for m in msgs) > budget:
        msgs.pop(0)   # vẫn quá dài: bỏ tin cũ nhất (phần đó đã/ sẽ nằm trong tóm tắt)
    return summary, msgs


def maybe_summarize(cid: str) -> bool:
    """Chạy sau mỗi lượt: phần chưa tóm tắt quá dài (hoặc quá số tin gửi kèm) thì gộp phần cũ vào tóm tắt."""
    path = db.get_path(cid)
    summary, upto = db.get_summary(cid)
    ids = [m["id"] for m in path]
    rest = path[ids.index(upto) + 1:] if summary and upto in ids else path
    if not (summary and upto in ids):
        summary = ""
    usable = _usable(rest)
    too_long = sum(tokens(m["content"]) for m in usable) > settings.get("SUMMARY_TRIGGER") * settings.get("FRIENDLY_NUM_CTX")
    too_many = len(usable) > max(settings.get("FRIENDLY_HISTORY_MESSAGES"), KEEP_RECENT)
    if not (too_long or too_many) or len(rest) <= KEEP_RECENT:
        return False
    old = rest[:-KEEP_RECENT]
    convo = "\n".join(f"{'Người dùng' if m['role'] == 'user' else 'Trợ lý'}: {as_prompt(m)['content']}" for m in _usable(old))
    out = llm.chat_json([
        {"role": "system", "content": "Tóm tắt cuộc trò chuyện giữa người dùng và trợ lý bằng tiếng Việt, gọn trong khoảng 10 câu. "
                                      "Giữ lại: thông tin người dùng đã cung cấp, câu hỏi chính, kết luận và việc còn dang dở. "
                                      "Nếu có tóm tắt cũ, gộp nó vào bản mới."},
        {"role": "user", "content": (f"Tóm tắt cũ:\n{summary}\n\n" if summary else "") + f"Đoạn hội thoại:\n{convo}"}], SCHEMA, timeout=120)
    text = " ".join(str(out.get("summary", "")).split())
    if not text:
        return False
    db.set_summary(cid, text, old[-1]["id"])
    return True

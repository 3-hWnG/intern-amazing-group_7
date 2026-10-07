"""Bộ nhớ dài hạn của từng người (NV2, 4A + công tắc A/B):
- auto     : sau mỗi câu trả lời, AI tự trích điều đáng nhớ từ tin nhắn của người dùng
- explicit : chỉ khi người dùng bảo "hãy nhớ…" (hoặc "hãy quên…")
Điều nhớ được đưa vào lời dặn hệ thống ở MỌI hội thoại Friendly của người đó, để khỏi hỏi lại.
"""
from __future__ import annotations

from . import db, llm, settings
from .lang import normalize

_REMEMBER = [normalize(p) for p in ("hãy nhớ", "nhớ giúp", "nhớ hộ", "ghi nhớ", "nhớ rằng", "nhớ là", "lưu lại", "remember")]
_FORGET = [normalize(p) for p in ("hãy quên", "quên đi", "quên giúp", "quên việc", "quên chuyện", "đừng nhớ", "không cần nhớ",
                                  "xoá ký ức", "xóa ký ức", "forget")]

SCHEMA = {"type": "object", "properties": {
    "add": {"type": "array", "items": {"type": "string"}},
    "remove": {"type": "array", "items": {"type": "integer"}}}, "required": ["add", "remove"]}

PROMPT = """Bạn là bộ phận ghi nhớ của một trợ lý. Đọc TIN NHẮN CỦA NGƯỜI DÙNG và trích những thông tin LÂU DÀI về chính người dùng, \
đáng nhớ cho các lần trò chuyện sau: tên, tuổi, nghề nghiệp, nơi ở, gia đình, sở thích, mục tiêu, hoàn cảnh, cách muốn được xưng hô.
Không ghi: câu hỏi, lời chào, cảm xúc nhất thời, yêu cầu một lần, thông tin về người hay việc khác, điều đã có trong danh sách.
Mỗi điều mới là một câu ngắn tiếng Việt, bắt đầu bằng "Người dùng".
Nếu tin nhắn cho thấy một điều đã nhớ không còn đúng, hoặc người dùng bảo quên điều đó, đưa SỐ THỨ TỰ của điều đó vào "remove".
Không có gì thì trả {"add": [], "remove": []}.
Ví dụ: "Hôm nay trời đẹp nhỉ" -> {"add": [], "remove": []}
Ví dụ: "Mình là Lan, làm kế toán ở Đà Nẵng" -> {"add": ["Người dùng tên là Lan", "Người dùng làm kế toán", "Người dùng sống ở Đà Nẵng"], "remove": []}
Ví dụ (đã nhớ "1. Người dùng sống ở Đà Nẵng"): "Mình mới chuyển ra Hà Nội" -> {"add": ["Người dùng sống ở Hà Nội"], "remove": [1]}"""


def mode(user_id: int) -> str:
    return db.get_memory_mode(user_id) or settings.get("MEMORY_DEFAULT_MODE")


def triggers(text: str) -> tuple[bool, bool]:
    n = normalize(text)
    return any(p in n for p in _REMEMBER), any(p in n for p in _FORGET)


def update(user_id: int, user_text: str, mem_mode: str | None = None) -> dict:
    """Cập nhật bộ nhớ sau một lượt. Trả {"added": [...], "removed": [...]} (rỗng nếu không đổi)."""
    mem_mode = mem_mode or mode(user_id)
    want_remember, want_forget = triggers(user_text)
    if mem_mode == "explicit" and not (want_remember or want_forget):
        return {"added": [], "removed": []}
    items = db.list_memories(user_id)
    known = "\n".join(f"{i}. {m['text']}" for i, m in enumerate(items, 1)) or "(chưa có)"
    hint = ""
    if mem_mode == "explicit":
        hint = "\nNgười dùng vừa chủ động bảo nhớ hoặc quên: chỉ ghi/xoá đúng điều họ bảo."
    out = llm.chat_json([{"role": "system", "content": PROMPT + hint},
                         {"role": "user", "content": f"Đã nhớ:\n{known}\n\nTIN NHẮN CỦA NGƯỜI DÙNG:\n{user_text}"}], SCHEMA)
    removed = []
    for i in sorted({i for i in out.get("remove", []) if isinstance(i, int) and 1 <= i <= len(items)}, reverse=True):
        db.delete_memory(user_id, items[i - 1]["id"])
        removed.append(items[i - 1]["text"])
    have = {normalize(m["text"]) for m in items if m["text"] not in removed}
    added = []
    for f in out.get("add", []):
        f = " ".join(str(f).split())
        n = normalize(f)
        # chỉ nhận câu đúng dạng "Người dùng …" (lọc câu AI chép nguyên tin nhắn), không trùng điều đã nhớ
        if not n.startswith("nguoi dung") or not (10 <= len(f) <= 200) or "khong co thong tin" in n:
            continue
        if any(n == h or n in h for h in have):
            continue
        db.add_memory(user_id, f, settings.get("MEMORY_MAX_ITEMS"))
        have.add(n)
        added.append(f)
    return {"added": added, "removed": removed}

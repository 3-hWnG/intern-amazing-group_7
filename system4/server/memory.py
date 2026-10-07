"""Bộ nhớ dài hạn của từng người (NV2, 4A + công tắc A/B; nới lỏng theo yêu cầu: chỉ nhớ điều hữu ích):
- auto     : AI trích điều đáng nhớ, nhưng CHỈ chạy khi tin nhắn có dấu hiệu người dùng tự kể về mình
             (tên, sở thích, thông tin ổn định) hoặc bảo nhớ/quên — không chạy với mọi tin nhắn
- explicit : chỉ khi người dùng bảo "hãy nhớ…" (hoặc "hãy quên…")
Điều nhớ được đưa vào lời dặn hệ thống ở MỌI hội thoại Friendly của người đó, để khỏi hỏi lại.
"""
from __future__ import annotations

import re
import unicodedata

from . import db, llm, settings
from .lang import normalize

_REMEMBER = [normalize(p) for p in ("hãy nhớ", "nhớ giúp", "nhớ hộ", "ghi nhớ", "nhớ rằng", "nhớ là", "lưu lại", "remember")]
_FORGET = [normalize(p) for p in ("hãy quên", "quên đi", "quên giúp", "quên việc", "quên chuyện", "đừng nhớ", "không cần nhớ",
                                  "xoá ký ức", "xóa ký ức", "forget")]

# Dấu hiệu người dùng tự kể về mình: có đại từ ngôi thứ nhất + một từ chỉ thông tin cá nhân (so khớp có dấu)
_SELF = ("tôi", "mình", "em", "tớ", "tao", "tui")
_FACT = ("tên", "là", "thích", "ghét", "yêu", "mê", "không ăn", "dị ứng", "sống", "ở", "quê", "làm", "nghề", "tuổi",
         "sinh năm", "có con", "có vợ", "có chồng", "đang học", "sinh viên", "học sinh", "gọi tôi", "gọi mình", "gọi em", "xưng")


def worth_checking(text: str) -> bool:
    """Code lọc trước (không gọi AI): tin nhắn có thể chứa thông tin đáng nhớ về chính người dùng không."""
    t = " " + re.sub(r"[^\w]+", " ", unicodedata.normalize("NFC", text or "").lower()) + " "
    return any(f" {w} " in t for w in _SELF) and any(f" {w} " in t for w in _FACT)


SCHEMA = {"type": "object", "properties": {
    "add": {"type": "array", "items": {"type": "string"}},
    "remove": {"type": "array", "items": {"type": "integer"}}}, "required": ["add", "remove"]}

PROMPT = """Bạn là bộ phận ghi nhớ của một trợ lý. Đọc TIN NHẮN CỦA NGƯỜI DÙNG và chỉ ghi những thông tin HỮU ÍCH, LÂU DÀI về chính người dùng:
tên và cách muốn được xưng hô; điều họ thích, không thích; thông tin ổn định họ tự kể về bản thân (nghề, nơi sống, gia đình); \
hoặc điều họ bảo nhớ.
Không ghi: câu hỏi, lời chào, cảm xúc nhất thời, yêu cầu một lần, thông tin về người hay việc khác, điều đã có trong danh sách. \
Phần lớn tin nhắn KHÔNG có gì cần ghi.
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
    if not (want_remember or want_forget) and (mem_mode == "explicit" or not worth_checking(user_text)):
        return {"added": [], "removed": []}   # không gọi AI: đỡ tốn GPU, câu sau không phải chờ
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

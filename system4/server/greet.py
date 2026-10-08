"""NV5: nhận biết câu xã giao (chào / cảm ơn / tạm biệt) khi đang bật bộ dữ liệu — phần do code làm.

Quy tắc của người dùng: tin nhắn NGẮN (tối đa GREETING_MAX_WORDS chữ) VÀ có từ chào hỏi -> câu xã giao.
"Hi, mình muốn hỏi thủ tục X" dài hơn nên vẫn đi đường tra dữ liệu. Ngay sau khi AI vừa hỏi lại (có nút lựa chọn),
"ok" / "dạ" là câu trả lời cho câu hỏi đó, không phải xã giao.
Từ có dấu so khớp nguyên dạng; bản không dấu chỉ nhận cho từ dài / cụm từ ("cam on", "chao") để "da" (dạ) không nhầm "Đà".
"""
from __future__ import annotations
import re
import unicodedata

from . import settings

_QUESTION = re.compile(r"\?|\b(gì|nào|sao|bao nhiêu|mấy|ở đâu|khi nào|ai|không nhỉ|chưa)\b")


def _fold(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return unicodedata.normalize("NFC", "".join(c for c in t if unicodedata.category(c) != "Mn")).replace("đ", "d")


def _words(t: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", (t or "").lower()))


def _has(phrase_words: list[str], words: list[str]) -> bool:
    n = len(phrase_words)
    return n > 0 and any(words[i:i + n] == phrase_words for i in range(len(words) - n + 1))


def has_greeting_word(text: str) -> bool:
    words = _words(text)
    folded = [w if _fold(w) == w else "\0" for w in words]   # chỉ chữ người dùng gõ KHÔNG dấu mới so bản không dấu ("vàng" ≠ "vâng")
    for p in str(settings.get("GREETING_WORDS") or "").split("|"):
        pw = _words(p)
        if not pw:
            continue
        if _has(pw, words):
            return True
        fp = [_fold(w) for w in pw]
        if (len(pw) > 1 or len(fp[0]) >= 4) and _has(fp, folded):
            return True
    return False


def asked_back(history_path: list[dict]) -> bool:
    last = next((m for m in reversed(history_path) if m["role"] == "assistant"), None)
    return bool(last and (last.get("meta") or {}).get("choices"))


def is_greeting(text: str, history_path: list[dict]) -> bool:
    """Quy tắc code: ngắn + có từ chào hỏi + không phải đang trả lời câu hỏi lại của AI."""
    return (0 < len(_words(text)) <= settings.get("GREETING_MAX_WORDS") and has_greeting_word(text)
            and not asked_back(history_path))


def looks_like_question(text: str) -> bool:
    """Dùng khi AI nói "xã giao" nhưng code không thấy câu chào: có dấu hỏi / từ hỏi / dài -> coi là câu hỏi về dữ liệu."""
    t = unicodedata.normalize("NFC", (text or "").lower())
    return bool(_QUESTION.search(t)) or len(_words(t)) > 2 * settings.get("GREETING_MAX_WORDS")


SMALL_TALK_INSTRUCTION = ("Tin nhắn này là câu xã giao (chào hỏi, cảm ơn hoặc tạm biệt). Đáp lại tự nhiên, ngắn gọn, đúng giọng người dùng; "
                          "không tra dữ liệu, không nói \"không có trong dữ liệu\". Có thể mời người dùng hỏi về dữ liệu họ đang bật.")

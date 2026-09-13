"""Nhận diện câu xã giao. Rẻ, không dùng vector, không gọi LLM.

Thay cho centroid router cũ: baseline v0 cho thấy cosine với trung bình 53 câu
mẫu không phân biệt được gì (LUAT 0.54 cho câu đúng, XAGIAO 0.51 cho "Hello").
Hơn nữa lớp nào NHIỀU câu mẫu hơn lại bị trung bình hoá mạnh hơn -> càng thêm
câu mẫu càng khó kích hoạt. Ở đây chỉ cần một bộ lọc đơn giản và tường minh.

v5 — sửa ba lỗi của bản trước:

1. So khớp BẰNG NHAU với tập câu mẫu (`q in GREETINGS | THANKS | ...`) nên chỉ
   cần thừa một chữ hoặc gõ sai một ký tự là trượt. "Thank you so muchc, Good
   bye" fold thành "thank you so muchc good bye", không nằm trong tập nào, mà
   nhánh dự phòng lại đòi <= 3 chữ (câu này 5 chữ) -> lọt xuống truy hồi và bị
   trả lời như một thủ tục hành chính.
2. `is_smalltalk()` so khớp BẰNG NHAU còn `reply()` so khớp CHỨA -> hai hàm bất
   đồng về việc câu nào thuộc nhóm nào. Nay cả hai dùng chung `_labels()`.
3. ADMIN_HINTS so khớp CHỨA trần trụi nên "cap", "phi", "xe" khớp cả vào giữa
   từ khác. Nay so khớp theo ranh giới từ.

Cách làm: tách câu theo dấu ngắt; mỗi vế phải là một cụm xã giao (khớp đúng,
hoặc gần đúng theo difflib để chịu lỗi gõ). Chỉ khi MỌI vế đều xã giao thì cả
câu mới là xã giao — nhờ vậy "Cảm ơn, cho hỏi thủ tục khai sinh" vẫn đi tiếp
xuống truy hồi thay vì bị nuốt thành lời chào.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from domain.text import fold

GREETINGS = {
    "xin chao", "chao", "chao ban", "chao anh", "chao chi", "hello", "helo",
    "hi", "hey", "alo", "chao buoi sang", "chao buoi chieu", "chao buoi toi",
    "good morning", "good afternoon", "good evening", "he lo", "xin chao ban",
}
THANKS = {
    "cam on", "cam on ban", "cam on nhe", "cam on nhieu", "cam on nhieu nhe",
    "cam on ban nhieu", "xin cam on", "thanks", "thank you", "thank you so much",
    "thanks a lot", "thank u", "tks", "thks", "ty", "ok cam on", "oke cam on",
}
BYE = {
    "tam biet", "tam biet ban", "bye", "byebye", "bye bye", "goodbye",
    "good bye", "chao nhe", "chao tam biet", "see you", "hen gap lai",
    "minh di day", "toi di day",
}
IDENTITY = {
    "ban la ai", "ban ten gi", "ban ten la gi", "ban lam duoc gi",
    "ban co the lam gi", "gioi thieu", "gioi thieu ban than", "ban la gi",
    "may la ai",
}
# Tiếng đệm xác nhận. Tách riêng vì KHÔNG nên kết thúc hội thoại như BYE.
ACK = {
    "ok", "oke", "okie", "okay", "vang", "da", "da vang", "u", "um", "uh",
    "duoc roi", "ro roi", "hieu roi", "biet roi", "the thoi",
}

_CATEGORIES = (
    ("identity", IDENTITY),
    ("bye", BYE),
    ("thanks", THANKS),
    ("greeting", GREETINGS),
    ("ack", ACK),
)

# Dấu hiệu "đây là câu hành chính" -> chắc chắn KHÔNG phải xã giao.
ADMIN_HINTS = [
    "thu tuc", "ho so", "giay", "giay to", "dang ky", "cap", "cap lai",
    "cap moi", "le phi", "phi", "bao lau", "bao nhieu", "o dau", "nop",
    "khai sinh", "khai tu", "ket hon", "ly hon", "can cuoc", "cccd", "cmnd",
    "ho chieu", "tam tru", "thuong tru", "cu tru", "con dau", "xay dung",
    "dat dai", "kinh doanh", "tro cap", "chung thuc", "luu tru", "visa",
    "thi thuc", "bien so", "xe", "hanh chinh", "mot cua", "ubnd", "cong an",
]
# Câu hỏi tiếp chỉ nêu khía cạnh, không nhắc tên thủ tục: "mất bao lâu?",
# "lệ phí bao nhiêu?". Đây là trường hợp DUY NHẤT được phép mượn ngữ cảnh cũ.
FACET_HINTS = [
    "bao lau", "bao nhieu", "bao nhieu tien", "may ngay", "may buoi",
    "o dau", "nop o dau", "lam o dau", "khi nao", "the nao", "nhu the nao",
    "can gi", "can chuan bi gi", "gom gi", "gom nhung gi", "can nhung gi",
    "giay to", "ho so", "le phi", "phi", "thoi gian", "dia diem", "mat bao lau",
    "cai do", "thu tuc do", "cai nay", "no",
]


def _word_re(items) -> re.Pattern:
    alts = "|".join(sorted((re.escape(x) for x in items), key=len, reverse=True))
    return re.compile(rf"(?<![a-z0-9])(?:{alts})(?![a-z0-9])")


_ADMIN_RE = _word_re(ADMIN_HINTS)
_FACET_RE = _word_re(FACET_HINTS)

_SPLIT_RE = re.compile(r"[,.;:!?\n\-]+")
_FUZZY_MIN = 0.85          # chịu được ~1 ký tự sai trên cụm 10+ ký tự
_FUZZY_MIN_LEN = 4         # ngắn hơn thì bắt buộc khớp đúng, tránh khớp bừa


def _norm(text: str) -> str:
    """Fold + bỏ ký tự không phải chữ/số + gom khoảng trắng."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", fold(text))).strip()


def has_admin_signal(text: str) -> bool:
    """Câu có nhắc tới chuyện hành chính không? (khớp theo ranh giới từ)"""
    return bool(_ADMIN_RE.search(_norm(text)))


def is_facet_followup(text: str) -> bool:
    """Câu ngắn hỏi tiếp về một khía cạnh của thủ tục đang nói tới."""
    return bool(_FACET_RE.search(_norm(text)))


def _match(segment: str) -> str | None:
    """Một vế câu thuộc nhóm xã giao nào, hay không thuộc nhóm nào?"""
    if not segment:
        return None
    if _ADMIN_RE.search(segment):
        return None
    for name, phrases in _CATEGORIES:
        if segment in phrases:
            return name
    if len(segment) < _FUZZY_MIN_LEN:
        return None
    best_name, best_ratio = None, 0.0
    for name, phrases in _CATEGORIES:
        for phrase in phrases:
            ratio = SequenceMatcher(None, segment, phrase).ratio()
            if ratio > best_ratio:
                best_name, best_ratio = name, ratio
    return best_name if best_ratio >= _FUZZY_MIN else None


def _labels(text: str) -> list[str] | None:
    """Nhãn của từng vế, hoặc None nếu có bất kỳ vế nào không phải xã giao."""
    segments = [_norm(s) for s in _SPLIT_RE.split(fold(text or ""))]
    segments = [s for s in segments if s]
    if not segments:
        return ["greeting"]                 # câu rỗng -> chào cho lịch sự
    names = [_match(s) for s in segments]
    if any(n is None for n in names):
        return None
    return names


def is_smalltalk(text: str) -> bool:
    return _labels(text) is not None


def reply(text: str) -> str:
    names = _labels(text) or []
    if "identity" in names:
        return ("Mình là trợ lý tra cứu thủ tục hành chính. Bạn hỏi về hồ sơ, "
                "thời gian, lệ phí hoặc nơi nộp của một thủ tục cụ thể nhé.")
    if "bye" in names and "thanks" in names:
        return ("Dạ không có gì ạ. Chào bạn, cần tra cứu thủ tục gì bạn quay "
                "lại nhé.")
    if "bye" in names:
        return "Dạ vâng, chào bạn. Cần hỗ trợ thủ tục gì bạn quay lại nhé."
    if "thanks" in names:
        return "Dạ không có gì. Bạn cần tra cứu thủ tục nào nữa không ạ?"
    if "ack" in names and "greeting" not in names:
        return "Dạ vâng. Bạn cần tra cứu thủ tục nào nữa không ạ?"
    return ("Chào bạn. Mình tra cứu giúp thủ tục hành chính: cần giấy tờ gì, "
            "mất bao lâu, lệ phí bao nhiêu, nộp ở đâu. Bạn cần thủ tục nào ạ?")

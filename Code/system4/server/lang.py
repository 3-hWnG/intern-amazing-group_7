"""Ngôn ngữ (NV2, 3B): chỉ hỗ trợ tiếng Việt, không để lọt chữ ngoài bảng chữ Latin.

- is_vietnamese(text): đoán tin nhắn người dùng có phải tiếng Việt (kể cả gõ không dấu)
- LatinFilter: lọc từng mẩu chữ AI sinh ra; bỏ chữ Hán/Cyrillic/... và emoji, đếm số ký tự đã bỏ
"""
from __future__ import annotations
import re
import unicodedata

# Chữ có dấu chỉ tiếng Việt dùng (ă â đ ê ô ơ ư + các dấu thanh trong khối Latin Extended Additional)
_VI_MARK = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯẠ-ỹ]")
_NON_LATIN_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

# Từ tiếng Việt hay gặp khi gõ không dấu
_VI_WORDS = set("""
toi ban minh la khong ko k co cua gi nao lam sao duoc dc cho voi nhu the nay do oi a roi chua giup hoi can muon biet
nhe nha nhi vay ve cac nhung mot hai ba nam thang ngay gio bao nhieu tai vi neu thi ma de con anh chi em ong cam on
xin chao chao duoc khi nao o dau ai tao may ho chung minh oke uh um da vang day phai biet hieu viec tien gia mua ban
hoc lam viec nha cua chi tiet huong dan thu tuc giay to ho so dang ky
""".split())
# Từ tiếng Anh hay gặp (không trùng với từ tiếng Việt không dấu ở trên)
_EN_WORDS = set("""
the is are was were what how why when where who which you your i my me we our it this that these those can could would
should will please yes no not do does did have has had be been with for from about and or but
if of in on at to an help tell explain need want know give show write make get there here they them their its
""".split())
# Người Việt cũng hay gõ: không tính là tiếng Anh
_NEUTRAL = {"hi", "hello", "hey", "ok", "okay", "oke", "thanks", "thank", "bye", "alo", "test", "yes", "no"}


def _strip_marks(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D")


def is_vietnamese(text: str) -> bool:
    """True nếu là tiếng Việt hoặc quá ngắn/không rõ (không xin lỗi oan với "ok", "?", số...)."""
    t = unicodedata.normalize("NFC", text or "")
    if _VI_MARK.search(t):
        return True
    letters = _NON_LATIN_LETTER.findall(t)
    if letters and sum(not _is_latin(c) for c in letters) > len(letters) * 0.3:
        return False   # phần lớn là chữ Hán, Cyrillic, Thái...
    words = [w.lower() for w in _WORD.findall(_strip_marks(t)) if w.lower() not in _NEUTRAL]
    if not words:
        return True
    vi = sum(w in _VI_WORDS for w in words)
    en = sum(w in _EN_WORDS for w in words)
    if vi >= en and vi > 0:
        return True
    if en >= 2 or (en >= 1 and len(words) <= 3 and vi == 0):
        return False
    return len(words) <= 2   # câu dài không nhận ra từ nào -> coi là ngôn ngữ khác; 1-2 từ lạ -> bỏ qua


def _is_latin(c: str) -> bool:
    o = ord(c)
    return o < 0x250 or 0x1E00 <= o <= 0x1EFF


def allowed(c: str) -> bool:
    """Ký tự được phép hiện: Latin (cả tiếng Việt), số, dấu câu, ký hiệu thường dùng. Chặn chữ khác và emoji."""
    o = ord(c)
    if o < 0x250 or 0x1E00 <= o <= 0x1EFF or 0x0300 <= o <= 0x036F:   # Latin + dấu kết hợp
        return True
    if 0x2000 <= o <= 0x206F:   # dấu câu chung (gạch ngang, ngoặc kép cong, …) trừ ký tự nối emoji
        return o not in (0x200D,)
    if 0x20A0 <= o <= 0x20CF or 0x2100 <= o <= 0x214F or 0x2190 <= o <= 0x22FF or 0x2460 <= o <= 0x24FF:
        return True   # tiền tệ (₫ €), ký hiệu chữ (№ ™), mũi tên, toán, số khoanh
    if 0x2500 <= o <= 0x257F:   # kẻ khung
        return True
    return False


class LatinFilter:
    """Lọc dần theo từng mẩu chữ: giữ ký tự allowed(), bỏ phần còn lại.
    removed_letters đếm chữ cái lạ (Hán, Cyrillic…), removed_other đếm emoji/ký hiệu."""

    def __init__(self):
        self.removed_letters = 0
        self.removed_other = 0
        self.kept = 0

    def feed(self, text: str) -> str:
        out = []
        for c in text:
            if allowed(c):
                out.append(c)
            elif c.isalpha():
                self.removed_letters += 1
            else:
                self.removed_other += 1
        self.kept += len(out)
        return "".join(out)

    def heavy_leak(self) -> bool:
        """Lọt nhiều chữ lạ tới mức câu trả lời có thể bị mất ý -> nên viết lại."""
        return self.removed_letters >= max(8, 0.05 * (self.kept + self.removed_letters))


def normalize(text: str) -> str:
    """Chữ thường, bỏ dấu, gộp khoảng trắng: dùng để khớp cụm từ của guardrail và câu nhắc nhớ."""
    return re.sub(r"\s+", " ", _strip_marks(text or "").lower()).strip()

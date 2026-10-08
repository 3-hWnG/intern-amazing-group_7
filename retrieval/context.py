"""Trạng thái hội thoại + dấu hiệu diễn ngôn (luật + dữ liệu, không LLM).

Nguyên nhân gốc của lỗi nối câu hỏi (đo ở eval/cases_ctx.jsonl): câu nối tiếp trộn LẪN hai loại chữ —
  (1) chữ DIỄN NGÔN ("cái đó", "quay lại", "ý tôi là", "nó", "lúc nãy", "nếu ... thì sao") và
  (2) chữ NGHIỆP VỤ (tên thủ tục),
nên chữ loại (1) bị đem đi xếp hạng như tên thủ tục, còn "có/không kế thừa" chỉ dựa vào MỘT điều kiện
("câu không còn chữ nào"). Ở đây: tách loại (1) ra TRƯỚC khi xếp hạng (markers), giữ trạng thái rõ ràng
(ConvState) và quyết định kế thừa theo tín hiệu (xem rank._decide).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from system3.data.search import _fold

from .refs import neg_in_name

HISTORY_MAX = 8
STORY_MAX = 2

# cụm đã bỏ dấu -> (cờ, giá trị). Cụm bị CẮT khỏi câu trước khi xếp hạng. Cụm dài khớp trước.
_PH: dict[tuple, tuple] = {}
for _ph, _flag, _val in [
    ("cai do", "anaph", 1), ("cai nay", "anaph", 1), ("cai kia", "anaph", 1), ("thu tuc nay", "anaph", 1),
    ("thu tuc do", "anaph", 1), ("thu tuc kia", "anaph", 1), ("vay thi", "anaph", 1), ("nhu vay", "anaph", 1),
    ("o tren", "anaph", 1), ("nhu tren", "anaph", 1), ("viec do", "anaph", 1), ("viec nay", "anaph", 1),
    ("y toi la", "corr", 1), ("y minh la", "corr", 1), ("y em la", "corr", 1), ("y toi hoi", "corr", 1),
    ("y minh hoi", "corr", 1), ("y em hoi", "corr", 1), ("nham roi", "corr", 1), ("sai roi", "corr", 1), ("a khong", "corr", 1),
    ("khong phai", "corr", 1), ("ko phai", "corr", 1),
    ("quay lai", "back", "any"), ("tro lai", "back", "any"), ("luc nay", "back", "any"), ("hoi nay", "back", "any"),
    ("vua nay", "back", "any"), ("luc dau", "back", "first"), ("ban dau", "back", "first"),
    ("cai dau tien", "back", "first"), ("cai truoc do", "back", "prev"), ("cai truoc", "back", "prev"),
    ("viec truoc", "back", "prev"), ("cai ban nay", "back", "prev"),
    ("chac khong", "meta", "verify"), ("co dung khong", "meta", "verify"), ("dung khong", "meta", "verify"), ("ngan gon hon", "meta", 1),
    ("ngan hon", "meta", 1), ("chi tiet hon", "meta", 1), ("viet lai", "meta", 1), ("noi lai", "meta", 1),
]:
    _PH[tuple(_ph.split())] = (_flag, _val)
_PH_SORTED = sorted(_PH, key=len, reverse=True)
_CONN = re.compile(r"^(?:(?:a|ok|oke|uh|um|da|vang|ua|ah)\s+)*(?:con|the con|vay con|vay|roi|the|tiep theo|ngoai ra|them nua|vay la)(?:\s|$)")
_AMOUNT = re.compile(r"^(?:(?:a|ok|oke|uh|um|da|vang|ua|ah)\s+)*(?:the |vay |con |roi )*(?:het )?bao nhieu(?: tien| the| vay| a| nhi| nhe)*\s*$")     # "thế bao nhiêu", "bao nhiêu vậy": câu cụt hỏi tiền
_TAIL = re.compile(r"(?:thi|vay) (?:sao|the nao|lam sao|nhu the nao|ra sao|duoc khong|co sao khong|co duoc khong)\s*$|^(?:sao|the nao)\s*$")
_NEED = re.compile(r"\bcan (?:phai )?(?:lam|dang ky|khai bao|nop|xin|chuan bi|di)\b.*\bgi\b|\b(?:phai|nen) lam (?:gi|sao)\b")
_COND = re.compile(r"(?:^|\s)(?:neu|truong hop|trong truong hop|doi voi)(?:\s|$)|(?:^|\s)(?:toi|em|minh|tui)\s+la\b.{1,25}\bthi\b")


# Nhãn lượt hội thoại ở ĐẦU câu ("Turn 2:", "User:", "Câu 2:", "Q:", "Bạn:", "Hỏi:", "Lượt 2 -", "[User]", "2)", "- ", "> "): không phải lời người dùng.
# Nguyên nhân gốc lỗi: chữ lạ ("turn") bị đem đi xếp hạng như tên thủ tục nên câu nối "vậy thời gian giải quyết..." bị coi là có chữ nghiệp vụ lạ -> độc lập -> ngoài phạm vi.
# Nhãn chữ cần dấu hai chấm; nhãn có số chấp nhận thêm . ) - để "Câu 2 là gì" không bị cắt.
_LBL_WORD = (r"turn|user|human|customer|client|question|ques|query|prompt|me|you|q|u|a|c|lượt|luot|lần|lan|câu hỏi|cau hoi|câu|cau|người dùng|nguoi dung|người hỏi|nguoi hoi|"
             r"khách|khach|bạn|ban|tôi|toi|mình|minh|hỏi|hoi|hỏi đáp|hoi dap|dân|dan|công dân|cong dan|người dân|nguoi dan")
_LBL_BOT = r"assistant|bot|ai|system|trợ lý|tro ly|trả lời|tra loi|đáp|dap|đáp án|bot trả lời"
_LBL = re.compile(r"^\s*(?:"
                  r"[-–—•*·>#~]+\s*|"                                                       # gạch đầu dòng, trích dẫn
                  r"[\[(\{<]\s*(?:(?:%s)\s*(?:no\.?|số|so)?\s*\d{0,2}|\d{1,2})\s*[\])\}>]\s*[:：.-]?\s*|"        # [User] (Turn 2) <Q2>
                  r"(?:(?:%s)\s*(?:no\.?|số|so)?\s*\d{1,2}(?:\s*/\s*\d{1,2})?\s*[:：.)\]\-–—]\s*)|"          # Turn 2: | Câu 2. | Q2) | Lượt 2 -
                  r"(?:(?:%s)\s*[:：]\s*)|"                                                 # User: | Q: | Bạn:
                  r"\d{1,2}\s*[.)\]:]\s+|"                                                  # 2. | 2) | 2:  (phải có khoảng trắng sau: không cắt "2.000")
                  r"\d{1,2}\s*[-–—]\s+"                                                    # 2 - 
                  r")" % (_LBL_WORD, _LBL_WORD, _LBL_WORD), re.I)


_LBL_B = re.compile(r"^\s*(?:%s)\s*[:：]\s*" % _LBL_BOT, re.I)
_EMOJI = re.compile("[🀀-🫿☀-➿⬀-⯿️‍]+")
_WRAP = "\"'“”‘’«»`*_~"
# Lời đệm lịch sự/xưng hô ở ĐẦU và CUỐI câu ("Dạ cho em hỏi ...", "Ad ơi ...", "... ạ", "... giúp mình với ạ"): không phải nghiệp vụ; còn nằm lại thì nó chặn
# (KHÔNG cắt lời chào: chào/alo/hello là tín hiệu xã giao của _is_chitchat) các luật neo đầu/cuối câu (câu cụt "thì sao", "bao nhiêu", điều kiện "nếu ... thì") và thêm chữ lạ. Chỉ cắt khi phần còn lại >= 2 chữ.
_POL_LEAD = re.compile(r"^\s*(?:(?:ad|admin|bot|bạn|anh|chị) ơi|(?:dạ|vâng)|"
                       r"(?:cho|xin)\s+(?:em |mình |tôi |tui |con |anh |chị )?hỏi(?: về| chút| xíu)?|(?:em|mình|tôi|tui) (?:muốn|cần|xin|định) hỏi(?: về| chút| xíu)?)(?=[\s,.:;!?]|$)[\s,.:;!]*", re.I)
_POL_TAIL = re.compile(r"(?:[\s,]+(?:ạ|nhé|nha|nhỉ|nhen|với ạ|giúp (?:mình|em|tôi|tui)(?: với)?(?: nhé| nha| ạ)?|dạ|ạ))+(?=[\s?.!]*$)", re.I)


def strip_labels(text: str, role: str = "user") -> str:
    """Làm sạch ĐẦU VÀO trước mọi bước hiểu câu: emoji, khoảng trắng thừa (\n, \t), ngoặc kép bao quanh, nhãn lượt ("Turn 2:", "User:", "Câu 2:", "Q:", "Bạn:", "Hỏi:",
    "2)", "- ", "> "), lời đệm lịch sự đầu/cuối câu. Không bỏ nếu chỉ còn rỗng. Lời trợ lý: chỉ bỏ nhãn chữ ("Assistant:") để không phá danh sách đánh số "1) A 2) B"."""
    t = unicodedata.normalize("NFC", text or "")
    if role != "user":
        m = _LBL_B.match(t)
        return t[m.end():] if m else t
    t = re.sub(r"\s+", " ", _EMOJI.sub(" ", t)).strip()
    for _ in range(4):
        t0 = t
        t = t.strip(_WRAP + " ") if t[:1] in _WRAP and t[-1:] in _WRAP + "?.!" else t.lstrip(_WRAP + " ")
        for rx in (_LBL, _POL_LEAD):
            m = rx.match(t)
            if m and len(t[m.end():].split()) >= (1 if rx is _LBL else 2):
                t = t[m.end():]
        if t == t0:
            break
    m = _POL_TAIL.search(t)
    if m and len(t[:m.start()].split()) >= 2:
        t = t[:m.start()] + t[m.end():].strip()
    return t.strip() or (text or "").strip()


def markers(text: str) -> tuple[str, dict]:
    """-> (câu đã cắt chữ diễn ngôn, cờ). cờ: anaph | corr | meta (hỏi lại/diễn đạt lại) | back(any/first/prev) | conn | tail | cond | need (True/giá trị)."""
    toks = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+", text or "")]
    fw = [_fold(t[0]) for t in toks]
    flags: dict = {}
    cut, i = [], 0
    while i < len(toks):
        hit = next((p for p in _PH_SORTED if tuple(fw[i:i + len(p)]) == p), None)
        if hit and neg_in_name(fw, i, len(hit)):          # "không phải xin phép..." là chữ trong tên thủ tục, không phải sửa ý
            hit = None
        if hit:
            f, v = _PH[hit]
            flags[f] = v
            cut.append((toks[i][1], toks[i + len(hit) - 1][2]))
            i += len(hit)
        elif toks[i][0].lower() == "cơ" and (i + 1 == len(toks) or fw[i + 1] == "ma" or (text[toks[i][2]:toks[i + 1][1]].strip() != "")):                     # "hỏi thường trú cơ (mà)": tiểu từ nhấn/đối lập (cuối câu/trước "mà"/trước dấu câu), không phải "cơ quan"
            flags["corr"] = 1
            cut.append((toks[i][1], toks[i][2]))
            i += 1
        elif toks[i][0].lower() == "nó" or (i == 0 and fw[i] == "no" and len(toks) > 1 and fw[1] in ("mat", "co", "can", "phai", "do", "o")):
            flags["anaph"] = 1               # "nó mất bao lâu": đại từ, không phải chữ "nợ"
            cut.append((toks[i][1], toks[i][2]))
            i += 1
        else:
            i += 1
    t = text or ""
    for a, b in reversed(cut):
        t = t[:a] + " " + t[b:]
    f = " ".join(fw)
    if _CONN.search(f):
        flags["conn"] = 1
    if _TAIL.search(f):
        flags["tail"] = 1
    if _AMOUNT.search(f):
        flags["tail"] = flags["amount"] = 1
        t = ""            # cả câu là "bao nhiêu": bỏ hết để "thế bao" không bị đọc thành "thẻ bảo (hiểm)" sau khi bỏ dấu
    if _COND.search(f):
        flags["cond"] = 1
    if _NEED.search(f):
        flags["need"] = 1          # câu hỏi mở "cần làm/đăng ký gì" không nêu tên thủ tục
    return t, flags


@dataclass
class ConvState:
    """Trạng thái hội thoại: thủ tục đang nói, các thủ tục đã nói (cũ -> mới), mục (field) đang hỏi, lời kể chưa gắn thủ tục.
    Fact của người dùng ở bảng session_facts (đã gắn proc_id), không nhân đôi ở đây."""
    topic: str | None = None
    history: list = field(default_factory=list)   # theo lần nói gần nhất (cũ -> mới)
    order: list = field(default_factory=list)     # theo lần nói ĐẦU TIÊN (cho "cái thứ nhất", "cái đầu tiên")
    fields: list = field(default_factory=list)
    story: list = field(default_factory=list)
    loose: bool = False                           # thủ tục đang nói do SUY RA từ lời kể (chưa được người dùng gọi tên): lượt sau nới lỏng cổng "chữ lạ"

    def note(self, pid: str, fields: list | None = None) -> None:
        if pid in self.history:
            self.history.remove(pid)
        self.history = (self.history + [pid])[-HISTORY_MAX:]
        if pid not in self.order:
            self.order = (self.order + [pid])[-HISTORY_MAX:]
        self.topic, self.story, self.loose = pid, [], False
        self.fields = list(fields or [])      # mục của LƯỢT GẦN NHẤT (rỗng = hỏi chung): câu nối/sửa ý kế thừa đúng mục vừa hỏi, không lấy mục cũ của thủ tục khác

    def add_story(self, text: str) -> None:
        self.story = (self.story + [text])[-STORY_MAX:]

    def to_dict(self) -> dict:
        return {"topic": self.topic, "history": list(self.history), "order": list(self.order), "fields": list(self.fields), "story": list(self.story), "loose": self.loose}

    @classmethod
    def from_dict(cls, d: dict | None) -> "ConvState":
        d = d or {}
        return cls(d.get("topic"), list(d.get("history") or []), list(d.get("order") or d.get("history") or []),
                   list(d.get("fields") or []), list(d.get("story") or []), bool(d.get("loose")))


# SỰ KIỆN ĐỜI SỐNG -> họ thủ tục. Người dân kể hoàn cảnh bằng từ KHÔNG nằm trong tên thủ tục ("vừa mất" ~ khai tử, "vào lớp 6" ~ tuyển sinh THCS).
# Vì sao KHÔNG dựng tự động từ condition_index: chỉ 894 dòng không-phải-"who" cho 1.350 thủ tục, phần lớn là tiêu đề hồ sơ ("Hồ sơ của người nhận con nuôi"),
# không có từ khoá sự kiện (đo: "người chết"/"bỏ rơi"/"qua đời" 0 dòng); cột keywords gần như trống (89/1.350). Vì vậy bảng là cụm từ khoá -> cụm gợi ý (tên thủ tục),
# còn "họ thủ tục" thật do bộ xếp hạng quyết định (hint đi qua rank như một câu hỏi). test: server/tests/context_test.py kiểm mọi hint đều ra đúng thủ tục có trong kho.
# Quy ước regex: chạy trên chữ đã bỏ dấu; viết theo từng NHÓM (người thân, thời điểm, động từ) để không phụ thuộc đại từ ("em/tôi/mình/nhà tôi").
_KIN = r"(?:chong|vo|bo|ba|me|ma|cha|ong|ba|anh|chi|em|con|chu|bac|di|cau|cu|nguoi(?: than| nha| trong nha)?|nha)"
_PRON = r"(?:\s(?:em|toi|minh|tui|cua em|cua toi|cua minh|nha em|nha toi|nha minh|co|bi))?"
EVENTS: list[tuple[str, str]] = [
    # sinh con
    (r"\b(?:be|con|chau|em be|cai be)\b" + _PRON + r"(?: moi| vua| sap| da)? (?:sinh|chao doi|ra doi)\b|\bsinh (?:con|be|chau|em be)\b|\b(?:vua|moi) sinh\b|\bsap sinh\b", "đăng ký khai sinh"),
    # kết hôn
    (r"(?<!cai )(?<!muc )(?<!so )\bcuoi\b(?! cung)|\bdam cuoi\b|\blay (?:vo|chong)\b|\bket hon\b", "đăng ký kết hôn"),
    # người thân qua đời (không nhầm "mất giấy/mất thẻ/mất việc": động từ "mất" đứng cuối cụm hoặc theo thời điểm)
    (r"\bqua doi\b|\btu tran\b|\bnguoi (?:than )?(?:vua |moi |da )?(?:chet|mat)\b|\b" + _KIN + _PRON + r"(?: vua| moi| da)? (?:mat|chet|qua doi|tu tran)(?!\s+(?:giay|the|so|ho|bang|can|tien|viec|dien|nuoc|xe|dat|nha|tich|chung)\b)\b", "đăng ký khai tử"),
    # thường trú / chuyển hộ khẩu
    (r"\b(?:chuyen|nhap|doi) (?:so )?ho khau\b|\bho khau\b.{0,25}\bchuyen (?:ve|den|di|sang)\b|\bnhap khau\b", "đăng ký thường trú"),
    # chỗ ở
    (r"\bo tro\b|\bthue tro\b|\bchuyen (?:len|den|ve|cho o|nha)\b", "đăng ký tạm trú"),
    # kinh doanh nhỏ
    (r"\bmo (?:quan|tiem|cua hang)\b|\bban hang\b|\bbuon ban\b|\bkinh doanh nho\b", "đăng ký hộ kinh doanh"),
    # con vào cấp 2
    (r"\b(?:vao|len|hoc) lop (?:6|sau)\b|\bvao cap (?:2|hai)\b|\bchuyen cap\b|\bhet cap (?:1|mot)\b", "tuyển sinh trung học cơ sở"),
    # người già không lương hưu
    (r"\b(?:khong|chua) (?:co|duoc|huong) (?:luong )?huu\b|\b(?:hon|tren|du|tu du) (?:7[0-9]|[89][0-9]) tuoi\b|\b(?:nguoi gia|cu gia|ong ba gia)\b.{0,25}\b(?:tro cap|tien hang thang|duoc nhan)\b", "trợ cấp hưu trí xã hội"),
    # trẻ bị bỏ rơi / nhận nuôi
    (r"\bbi bo roi\b|\bmo coi\b|\bxin (?:mot )?(?:be|chau|dua tre)\b|\bnhan (?:mot |ve )?(?:be|chau|dua tre|dua be)\b.{0,15}\bnuoi\b|\bnhan nuoi\b", "đăng ký việc nuôi con nuôi trong nước"),
    # hộ nghèo
    (r"\b(?:nha|gia dinh|nha em|nha toi) (?:em |toi |minh )?(?:rat |qua )?(?:ngheo|can ngheo)\b|\bthoat ngheo\b|\bhoan canh kho khan\b", "công nhận hộ nghèo"),
    # tai nạn lao động
    (r"\b(?:bi |gap )?tai nan (?:khi |luc )?(?:di )?(?:lam|lao dong|o cong ty|trong cong ty)\b|\bbi thuong (?:khi|luc) (?:di )?lam\b|\bbenh nghe nghiep\b", "chế độ tai nạn lao động bệnh nghề nghiệp"),
    # có công với cách mạng
    (r"\bco cong (?:voi )?cach mang\b|\bnguoi co cong\b|\bthuong binh\b|\bliet si\b", "người có công"),
]
_EVENTS = [(re.compile(rx), h) for rx, h in EVENTS]


def event_hints(text: str) -> tuple[str, str]:
    """-> (gợi ý tên thủ tục, câu đã bỏ phần diễn đạt sự kiện [đã bỏ dấu]) để nơi gọi kiểm tra còn chữ nghiệp vụ lạ hay không."""
    # "cuối" (thứ tự) và "cưới" (kết hôn) cùng gấp thành "cuoi": đánh dấu "cuối" CÓ DẤU trước khi bỏ dấu để không khớp nhầm sự kiện;
    # chữ gõ không dấu thì loại các cách dùng thứ tự ("cái cuoi", "cuoi cung") bằng chính regex.
    f = _fold((text or "").lower().replace("cuối", "cuoiq"))
    hints, rest = [], f
    has_ho_khau = bool(re.search(r"\bho khau\b", f))
    has_mai_tang = bool(re.search(r"\b(?:mai tang|ma chay|hoa tang)\b", f))
    for rx, h in _EVENTS:
        if h == "đăng ký tạm trú" and has_ho_khau:
            continue
        if rx.search(f):
            if h == "đăng ký khai tử" and has_mai_tang:
                hints.append("hỗ trợ chi phí mai táng")
            else:
                hints.append(h)
            rest = rx.sub(" ", rest)
    return " ".join(hints), rest.replace("cuoiq", "cuoi")

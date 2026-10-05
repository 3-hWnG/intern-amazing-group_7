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
from dataclasses import dataclass, field

from system3.data.search import _fold

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
    ("chac khong", "meta", 1), ("co dung khong", "meta", 1), ("dung khong", "meta", 1), ("ngan gon hon", "meta", 1),
    ("ngan hon", "meta", 1), ("chi tiet hon", "meta", 1), ("viet lai", "meta", 1), ("noi lai", "meta", 1),
]:
    _PH[tuple(_ph.split())] = (_flag, _val)
_PH_SORTED = sorted(_PH, key=len, reverse=True)
_CONN = re.compile(r"^(?:(?:a|ok|oke|uh|um|da|vang|ua|ah)\s+)*(?:con|the con|vay con|vay|roi|the|tiep theo|ngoai ra|them nua|vay la)(?:\s|$)")
_TAIL = re.compile(r"(?:thi|vay) (?:sao|the nao|lam sao|nhu the nao|ra sao|duoc khong|co sao khong|co duoc khong)\s*$|^(?:sao|the nao)\s*$")
_NEED = re.compile(r"\bcan (?:phai )?(?:lam|dang ky|khai bao|nop|xin|chuan bi|di)\b.*\bgi\b|\b(?:phai|nen) lam (?:gi|sao)\b")
_COND = re.compile(r"(?:^|\s)(?:neu|truong hop|trong truong hop|doi voi)(?:\s|$)")


def markers(text: str) -> tuple[str, dict]:
    """-> (câu đã cắt chữ diễn ngôn, cờ). cờ: anaph | corr | meta (hỏi lại/diễn đạt lại) | back(any/first/prev) | conn | tail | cond | need (True/giá trị)."""
    toks = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+", text or "")]
    fw = [_fold(t[0]) for t in toks]
    flags: dict = {}
    cut, i = [], 0
    while i < len(toks):
        hit = next((p for p in _PH_SORTED if tuple(fw[i:i + len(p)]) == p), None)
        if hit:
            f, v = _PH[hit]
            flags[f] = v
            cut.append((toks[i][1], toks[i + len(hit) - 1][2]))
            i += len(hit)
        elif toks[i][0].lower() == "cơ":                     # "hỏi thường trú cơ (mà)": tiểu từ nhấn/đối lập, không phải chữ "co"
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
        if fields:
            self.fields = list(fields)

    def add_story(self, text: str) -> None:
        self.story = (self.story + [text])[-STORY_MAX:]

    def to_dict(self) -> dict:
        return {"topic": self.topic, "history": list(self.history), "order": list(self.order), "fields": list(self.fields), "story": list(self.story), "loose": self.loose}

    @classmethod
    def from_dict(cls, d: dict | None) -> "ConvState":
        d = d or {}
        return cls(d.get("topic"), list(d.get("history") or []), list(d.get("order") or d.get("history") or []),
                   list(d.get("fields") or []), list(d.get("story") or []), bool(d.get("loose")))


# lời kể sự kiện đời sống -> tên thủ tục thường gặp (từ vựng của người dân KHÔNG nằm trong tên thủ tục).
# ponytail: bảng tay 5 sự kiện phổ biến nhất; mở rộng bằng log thật, hoặc dựng từ condition_index.
_EVENTS = [
    (re.compile(r"\b(?:be|con) (?:moi |vua )?(?:sinh|chao doi)\b|\bsinh (?:con|be|em be)\b|\b(?:vua|moi) sinh\b"), "đăng ký khai sinh"),
    (re.compile(r"\bcuoi\b|\bdam cuoi\b|\blay (?:vo|chong)\b|\bket hon\b"), "đăng ký kết hôn"),
    (re.compile(r"\bqua doi\b|\btu tran\b|\b(?:chong|vo|bo|me|ong|ba|con|nguoi than)(?: toi| minh)?(?: vua| moi)? (?:mat|qua doi)\b"), "đăng ký khai tử"),
    (re.compile(r"\bo tro\b|\bthue tro\b|\bchuyen (?:len|den|ve|cho o|nha)\b"), "đăng ký tạm trú"),
    (re.compile(r"\bmo (?:quan|tiem|cua hang)\b|\bban hang\b|\bbuon ban\b|\bkinh doanh nho\b"), "đăng ký hộ kinh doanh"),
]


def event_hints(text: str) -> tuple[str, str]:
    """-> (gợi ý tên thủ tục, câu đã bỏ phần diễn đạt sự kiện [đã bỏ dấu]) để nơi gọi kiểm tra còn chữ nghiệp vụ lạ hay không."""
    f = _fold(text)
    hints, rest = [], f
    for rx, h in _EVENTS:
        if rx.search(f):
            hints.append(h)
            rest = rx.sub(" ", rest)
    return " ".join(hints), rest

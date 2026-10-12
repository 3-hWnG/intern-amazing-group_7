"""Tham chiếu trong hội thoại, không LLM: thứ tự ("cái thứ hai", "số 2", "cái cuối") và phủ định ("không phải X").

Nguyên nhân gốc cũ: hai việc này đều là CHỈ DẪN về danh sách/ứng viên chứ không phải tên thủ tục; đưa nguyên câu vào
xếp hạng thì chữ của X (hoặc "hai", "đầu") lại kéo đúng thủ tục bị loại.
"""
from __future__ import annotations

import re

from system3.data.search import _fold

_NUM = {"nhat": 1, "mot": 1, "hai": 2, "ba": 3, "bon": 4, "tu": 4, "nam": 5}
_MARK = r"(?:cai|so|muc|y|phuong an|cau|chon|lay|thu tu|dap an|lua chon|thu tuc)"
_NUMW = r"(nhat|mot|hai|ba|bon|\d)"
# "cái thứ hai", "số 2", "chọn 1", "lấy cái 3", "thứ 3", "phương án thứ ba"
_ORD_N = re.compile(rf"\b(?:{_MARK}\s+)*(?:thu\s+)?{_NUMW}\b")
_ORD_POS = re.compile(r"\b(?:(?:cai|y|muc|phuong an|cau|dap an|lua chon)\s+)?(dau tien|dau|cuoi cung|sau cung|cuoi|chot|sau|duoi|tren|truoc|giua|o giua|o tren|o duoi|ben tren|ben duoi)\b")
_FILLER = {"ua", "uh", "um", "do", "day", "nay", "kia", "a", "nhe", "nha", "di", "nhi", "ma", "thi", "con", "oi", "da", "va",
           "cai", "thu", "chon", "lay", "so", "muc", "y", "phuong", "an", "cau", "o", "la", "luon", "ha", "chot", "tren", "duoi", "sau", "truoc"}


def ordinal(text: str) -> tuple[str, str] | None:
    """-> (kiểu, rest): kiểu 'n:2' | 'first' | 'last' | 'middle'; rest = phần câu còn lại SAU KHI bỏ cụm thứ tự (đã bỏ dấu).
    None nếu không phải tham chiếu thứ tự thuần (còn chữ nghiệp vụ lạ thì coi là câu hỏi mới)."""
    # "thứ tư" (= 4) và "thứ tự" (= trật tự) cùng gấp thành "thu tu": phân biệt khi còn dấu rồi mới bỏ dấu
    f = _fold(re.sub(r"(?<!\w)(thứ|số|mục|cái|ý|câu) tư(?!\w)", r"  bốn", (text or "").lower()))
    kind, span = None, None
    m = _ORD_POS.search(f)
    # "đâu" (ở đâu) và "cưới" gấp dấu thành "dau"/"cuoi" trùng "đầu"/"cuối": chữ trần chỉ là thứ tự khi có từ chỉ định (cái/mục...) hoặc còn dấu "đầu"/"cuối"
    if m and m.group(0) == m.group(1) and m.group(1) in ("dau", "cuoi") and not re.search(r"đầu|cuối", (text or "").lower()):
        m = None
    if m and m.group(0) == m.group(1) and m.group(1) in ("sau", "truoc", "tren", "duoi", "chot"):
        m = None
    if m and (m.group(0) != m.group(1) or len(f.split()) <= 6 or "thu" in f.split() or "cai" in f.split()):
        w = m.group(1)
        if w in ("dau tien", "dau", "tren", "truoc", "o tren", "ben tren"):
            kind = "first"
        elif w in ("cuoi cung", "sau cung", "cuoi", "chot", "sau", "duoi", "o duoi", "ben duoi"):
            kind = "last"
        elif w in ("giua", "o giua"):
            kind = "middle"
        span = m.span()
    else:
        for m in _ORD_N.finditer(f):
            explicit = m.group(0) != m.group(1)           # có từ chỉ định (cái/số/thứ/chọn...)
            if explicit or f.strip() == m.group(1):
                w = m.group(1)
                kind, span = f"n:{int(w) if w.isdigit() else _NUM[w]}", m.span()
                break
    if kind is None:
        return None
    rest = f[:span[0]] + " " + f[span[1]:]
    return kind, rest


def pure_reference(rest_folded: str, idx_vocab: set[str], field_cues: list[str]) -> bool:
    """Phần còn lại chỉ là hư từ + cụm chỉ-field (phí/mất bao lâu...), không chứa chữ nghiệp vụ."""
    from .query import STOP
    cue_words = {w for c in field_cues for w in c.split()}     # chữ nào thuộc cụm chỉ-field đều là đệm
    return not any(t in idx_vocab and t not in _FILLER and t not in STOP and t not in cue_words for t in rest_folded.split())


def pick(kind: str, n: int) -> int | None:
    """kiểu thứ tự + số phần tử -> chỉ số 0-based (None nếu ngoài khoảng/không xác định)."""
    if n <= 0:
        return None
    if kind == "first":
        return 0
    if kind == "last":
        return n - 1
    if kind == "middle":
        return (n - 1) // 2 if n >= 3 else None
    i = int(kind.split(":")[1]) - 1
    return i if 0 <= i < n else None


_LIST_SPLIT = re.compile(r"(?:^|\s)(\d)\)\s*")


def options_from_text(text: str) -> list[str]:
    """'Bạn muốn hỏi thủ tục nào? 1) A 2) B' -> ['A','B'] (nhãn có thể bị cắt '…')."""
    parts = _LIST_SPLIT.split(text or "")
    out = []
    for i in range(1, len(parts) - 1, 2):
        if int(parts[i]) == len(out) + 1:
            out.append(parts[i + 1].strip().rstrip("…").rstrip(".").strip())
    return out if len(out) >= 2 else []


# ---------------------------------------------------------------- phủ định
_NEG_TRIG = [("khong", "phai"), ("ko", "phai"), ("k", "phai"), ("hok", "phai"), ("chang", "phai"), ("dau", "phai"),
             ("dung", "nham", "voi"), ("dung", "nham"), ("dung", "dua"), ("dung", "lay"), ("dung", "chon"),
             ("khong", "lay"), ("khong", "can"), ("khong", "phai", "la")]
NAME_NEG: set = set()      # (dấu hiệu phủ định + 2 chữ kế) nằm TRONG tên thủ tục thật ("không phải xin phép", "không phải là bất động sản"); Index nạp
_NEG_VARIANT = ("khong", "co")      # chỉ khi X mở đầu bằng dấu hiệu biến thể (xem _VARIANT_HEAD)
_VARIANT_HEAD = {"yeu", "loai", "ban", "dang", "truong"}
_X_STOP = set("nhe nha nhá dau thoi ma hay a oi di nhi can thi lam phi nop mat bao giay la nhung minh toi ban cho hoi online "
              "duoc khong voi va hoac cung roi nua day do ak ah".split())
_X_LEAD = {"la", "loai", "ban", "dang", "truong", "hop", "cai"}


def neg_in_name(fw: list[str], i: int, n: int) -> bool:
    """Cụm phủ định bắt đầu ở fw[i] (dài n chữ) cùng 2 chữ kế trùng một đoạn tên thủ tục thật => là tên, không phải phủ định."""
    nola = tuple(fw[i:i + n]) + tuple([w for w in fw[i + n:i + n + 3] if w != "la"][:2])     # "không phải cộng tác viên" ~ "không phải là cộng tác viên" (hệ từ "là" có/không đều là tên)
    return tuple(fw[i:i + n + 2]) in NAME_NEG or nola in NAME_NEG


def load_name_neg(names_toks: list[list[str]]) -> None:
    """Nạp từ tên thủ tục đã bỏ dấu (Index gọi một lần)."""
    NAME_NEG.clear()
    for toks in names_toks:
        for k in range(len(toks)):
            for trig in _NEG_TRIG:
                if tuple(toks[k:k + len(trig)]) == trig:
                    NAME_NEG.add(tuple(toks[k:k + len(trig) + 2]))
                    NAME_NEG.add(trig + tuple([w for w in toks[k + len(trig):k + len(trig) + 3] if w != "la"][:2]))


def extract_negation(text: str, vocab: set[str]) -> tuple[str, list[list[str]]]:
    """'... không phải X ...' -> (câu đã bỏ cụm phủ định, [token_X đã bỏ dấu]).
    Chỉ nhận khi X có chữ thuộc từ vựng tên thủ tục (tránh nuốt 'không phải chủ hộ').
    ponytail: X kết thúc ở dấu câu/hư từ; không hiểu phủ định lồng ('không phải A hay B' chỉ lấy A)."""
    toks = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+|[^\w\s]", text or "")]
    fw = [_fold(t[0]) for t in toks]
    out, neg, i, cut = [], [], 0, []
    while i < len(toks):
        hit = None
        for trig in sorted(_NEG_TRIG + [_NEG_VARIANT], key=len, reverse=True):
            if tuple(fw[i:i + len(trig)]) == trig:
                hit = trig
                break
        if not hit or neg_in_name(fw, i, len(hit)):
            i += 1
            continue
        j = i + len(hit)
        while j < len(toks) and fw[j] in _X_LEAD:
            j += 1
        k = j
        while k < len(toks) and k - j < 8 and re.match(r"\w", toks[k][0]) and fw[k] not in _X_STOP:
            k += 1
        xs = [w for w in fw[j:k] if w]
        if hit == _NEG_VARIANT and not (xs and xs[0] in _VARIANT_HEAD):
            i += 1
            continue
        if xs and any(w in vocab for w in xs):
            start = i - 1 if i > 0 and fw[i - 1] == "chu" else i
            neg.append(xs)
            while k + 1 < len(toks) and fw[k] in ("hay", "hoac"):       # "không phải A hay B": B cũng bị loại (vế phủ định liệt kê)
                k2 = k + 1
                while k2 < len(toks) and k2 - k < 9 and re.match(r"\w", toks[k2][0]) and fw[k2] not in _X_STOP:
                    k2 += 1
                xs2 = [w for w in fw[k + 1:k2] if w]
                if not any(w in vocab for w in xs2):
                    break
                neg.append(xs2)
                k = k2
            cut.append((toks[start][1], toks[k - 1][2]))
            i = k
        else:
            i += 1
    t = text or ""
    for a, b in reversed(cut):
        t = t[:a] + " " + t[b:]
    return t, neg


# ---------------------------------------------------------------- so sánh
_CMP_CUES = [("khac", "nhau"), ("khac", "gi"), ("khac", "sao"), ("khac", "biet"), ("khac", "o"), ("khac", "khong"), ("khac", "ko"),
             ("giong", "hay", "khac"), ("giong", "nhau"), ("so", "sanh"), ("diem", "khac"), ("cai", "nao"), ("hay", "khac")]
_CMP_CONN = [("so", "voi"), ("voi",), ("vs",), ("va",), ("hay",), ("and",)]


def split_compare(text: str) -> list[str] | None:
    """'A với B khác nhau thế nào' -> [A, B] (hai thủ tục tách riêng, mỗi bên >= 2 chữ). None nếu không phải câu so sánh.
    ponytail: tách ở liên từ đầu tiên TRƯỚC cụm so sánh; B thiếu chữ đầu (\"thường xuyên\" của \"công nhận hộ nghèo...\") không mượn lại từ A."""
    toks = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+", text or "")]
    fw = [_fold(t[0]) for t in toks]
    cue = next((i for i in range(len(fw)) for c in _CMP_CUES if tuple(fw[i:i + len(c)]) == c), None)
    if cue is None:
        return None
    lo = cue + 2 if tuple(fw[cue:cue + 2]) == ("so", "sanh") else 0   # 'so sánh A và B': vế nằm SAU cụm
    hi = len(fw) if lo else cue
    for i in range(lo, hi):
        for c in _CMP_CONN:
            if tuple(fw[i:i + len(c)]) == c and i - lo >= 2:
                j = i + len(c)
                a = text[toks[lo][1]:toks[i - 1][2]]
                b_end = hi
                for k in range(j, len(fw)):          # B dừng ở cụm so sánh / dấu phẩy
                    if any(tuple(fw[k:k + len(cc)]) == cc for cc in _CMP_CUES):
                        b_end = k
                        break
                else:
                    b_end = len(fw)
                if b_end - j >= 2:
                    return [a.strip(), text[toks[j][1]:toks[b_end - 1][2]].strip()]
    return None

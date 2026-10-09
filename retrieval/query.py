"""Tách câu hỏi thành: tên thủ tục (để TRA) + field cần hỏi + tỉnh + điều kiện thô.

Bài học đo được (eval/BASELINE.md): từ chỉ field ("cần giấy tờ gì", "mất bao nhiêu") làm
hỏng truy vấn FTS/AND. Ở đây mọi cụm chỉ-field bị TÁCH RA thành `fields`, không vứt đi.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from system3.data.search import _PROVINCE_PATTERNS, _fold, synonyms_map

# field -> cụm (đã bỏ dấu). Cụm dài khớp trước. Tên field = SECTION_CUES của bảng cũ.
FIELD_CUES: dict[str, list[str]] = {
    "components": ["can nhung giay to gi", "can giay to gi", "can ho so gi", "can nhung giay gi", "can giay gi", "giay gi", "mang nhung gi", "mang gi", "ho so the nao", "ho so nhu the nao", "ho so ra sao", "nop cai gi", "nop nhung gi", "phai nop gi", "giay to", "ho so gom", "ho so", "thanh phan", "can nhung gi", "can gi", "can chuan bi",
                   "chuan bi gi", "chuan bi nhung gi", "mang theo", "can mang"],
    "fees": ["thu bao nhieu", "dong bao nhieu", "phai dong bao nhieu", "ton tien", "ton phi", "le phi bao nhieu tien", "le phi bao nhieu", "co thu phi khong", "thu phi", "het bao nhieu", "mat bao nhieu", "le phi", "mien phi", "co mat phi", "mat phi", "bao nhieu tien", "ton bao nhieu", "mat bao nhieu tien",
             "co mat tien", "mat tien", "phi la", "phi bao nhieu", "phi"],
    "processing_time": ["thoi gian xu ly ho so", "thoi han xu ly ho so", "thoi gian giai quyet ho so", "thoi han giai quyet ho so", "xu ly ho so", "giai quyet ho so", "thoi gian xu ly", "thoi han xu ly", "han xu ly", "bao gio co ket qua", "khi nao co ket qua", "bao gio xong", "khi nao xong", "khi nao nhan duoc", "bao gio nhan duoc", "co ket qua sau", "co ket qua", "mat may bua", "may bua", "may hom", "may tuan", "mat may ngay", "het may ngay", "bao nhieu lau", "lau khong", "mat bao lau", "bao lau", "may ngay", "thoi gian giai quyet", "thoi han giai quyet", "thoi gian", "thoi han",
                        "mat bao nhieu ngay", "bao nhieu ngay", "nhan ket qua sau"],
    "address": ["nop ho so o dia chi", "nop ho so tai dia chi", "nop ho so tai", "nop cho ai", "den dau nop", "di dau nop", "dia chi nao", "dia chi", "nop o dau", "nop tai dau", "dia diem", "noi nop", "nop ho so o dau", "o dau"],
    "online": ["nop ho so truc tuyen", "nop ho so online", "ho so truc tuyen", "ho so online", "nop ho so tren mang", "tren mang", "nop tren mang", "truc tuyen", "online", "cong dich vu cong", "cong dvc", "dich vu cong", "qua mang", "nop mang"],
    "methods": ["nop qua buu dien", "nop buu dien", "gui buu dien", "buu dien", "cach nop", "nop ho so bang hinh thuc nao", "nop ho so bang cach nao", "nop ho so qua hinh thuc nao", "nop bang hinh thuc nao", "bang hinh thuc nao", "bang nhung hinh thuc", "hinh thuc nao", "nhung hinh thuc", "hinh thuc nop", "nop truc tiep", "qua buu dien", "buu chinh", "cach thuc nop"],
    "files": ["bieu mau", "mau don", "mau to khai", "to khai mau", "tai mau", "file mau", "tai ve"],
    "agency": ["ai lam", "den dau de lam", "den dau lam", "ai tiep nhan ho so", "co quan tiep nhan ho so", "co quan thuc hien", "co quan tiep nhan", "ai tiep nhan", "do co quan nao giai quyet", "co quan nao giai quyet", "ai giai quyet", "co quan nao", "co quan giai quyet", "ai giai quyet", "cap nao", "noi nao giai quyet", "to chuc nao"],
    "steps": ["cac buoc thuc hien", "buoc thuc hien", "trinh tu thuc hien", "cach thuc hien", "can lam gi", "gom nhung buoc nao", "cac buoc", "buoc nao", "quy trinh", "trinh tu", "lam the nao", "lam sao",
              "cach lam", "huong dan lam", "thuc hien the nao", "thuc hien nhu the nao", "nhu the nao", "the nao"],
    "explanation": ["la gi", "dieu kien", "doi tuong nao", "ai duoc", "co duoc khong"],
    "meta": ["co quan nao ban hanh", "ai ban hanh", "ban hanh", "so hieu", "link", "duong link", "van ban nao quy dinh", "van ban quy dinh", "thong tu nao quy dinh", "nghi dinh nao quy dinh", "can cu vao van ban nao", "van ban nao", "thong tu nao", "nghi dinh nao", "luat nao", "quy dinh nao", "dua tren quy dinh nao", "dua tren", "quyet dinh cong bo", "trich dan", "duong dan", "lay thong tin o dau", "lay thong tin", "lay tu dau", "nguon", "can cu phap ly", "co so phap ly", "van ban phap luat", "van ban", "quyet dinh so", "nghi dinh", "luat nao",
             "can cu"],
}
# cụm chứa cụm chỉ-field nhưng là DANH TỪ ("giấy tờ cá nhân" trong lời kể), không phải mục được hỏi
NOT_FIELD = ("giay to ca nhan", "giay to tuy than", "ho so ca nhan", "ban sao giay to", "ban chinh giay to")
_FIELD_VERBS = {"giai", "quyet", "thuc", "hien", "xong", "lam"}
_CUE_WORDS = {w for cs in FIELD_CUES.values() for c in cs for w in c.split()}
# Lượng từ/hư từ/động từ đệm: không phải tên thủ tục. KHÔNG gồm những chữ có thể là nghiệp vụ.
STOP = set("""toi minh muon t tao ko k hok dc duoc giup xin oi nhe nhi vay gi cho hoi la va voi con cua thi
nay nua het hay da se rat nhieu moi can muon phai co khong nao bao the sao a u on nha
bi nhung cac mot nhu o tai de ma ve thoi roi lai lam xong biet ban em anh bac
di den ra vao len xuong neu ay do kia day ben nhe chu theo trong tren duoi dau
ok oke okie okay uh um ua ah ak ad admin z zay zi nop
chao hello hi alo da hem hok hen nghen ne nghe noi hom bua chua ranh xiu chut tui tao may chi
mk mik e vi viec bn ha hay haha thanks cam on xin lam on gium giup muon biet hieu roi hoi vu cai""".split())
# Gõ tắt/văn nói đổi THÀNH cụm chuẩn TRƯỚC khi tìm cụm chỉ-field (nếu để sau, "mất bn tiền" không khớp "mất bao nhiêu").
PRE_SYN = {"hso": "ho so", "onl": "online", "ow": "o", "bn": "bao nhieu", "j": "gi", "gj": "gi", "dc": "duoc", "dg": "dang", "r": "roi", "ntn": "nhu the nao", "sao z": "sao",
           # teencode theo NHÓM (đo từ lỗi gõ ở DEV/synth): phủ định (ko/kg/khg/kh/k/hok -> không; "hk" = hộ khẩu, giữ ở EXTRA_SYN), viết tắt từ hỏi/mục (tg, lp, vb, xn), f/ph
           "ko": "khong", "kg": "khong", "khg": "khong", "kh": "khong", "k": "khong", "hok": "khong", "tg": "thoi gian", "lp": "le phi", "vb": "van ban", "xn": "xac nhan",
           "fi": "phi", "vs": "voi", "đc": "duoc"}
# Một số chữ trên là nghiệp vụ nếu đứng trong cụm đặc thù; giữ nguyên cụm trước khi bỏ stop.
KEEP_PHRASES = ["con nho", "cho thue", "cap lai", "lam lai"]

_DROP_PHRASES = ("nho tu van", "xin tu van", "tim hieu", "tu van", "can biet", "muon biet", "huong dan", "linh vuc", "thong tin ve thu tuc", "cho minh hoi", "cho toi hoi", "cho hoi", "vui long", "lam on", "thu tuc", "ho so thu tuc",
                 "binh thuong", "thuong thoi", "phai lam sao", "phai lam gi", "phai lam nhung gi", "lam giay to", "lam giay")
_SEG_SPLIT = re.compile(r"\s*(?:[?;,.]|(?<!\w)(?:còn|với lại|và|sau đó|ngoài ra)(?!\w))\s*")
# "nếu/trường hợp <điều kiện> thì <câu chính>": điều kiện KHÔNG phải tên thủ tục.
# gõ không dấu ("neu ... thi", "truong hop") cũng là câu điều kiện: COND_W dùng chung cho mọi regex điều kiện (rank.py)
COND_W = r"(?:nếu|neu|trường hợp|truong hop|đối với|doi voi)"
_THI = r"(?:thì|thi)"
_COND_RE = re.compile(r"^(?:.*?\s)?" + COND_W + r"\s+(.+?)\s*(?:" + _THI + r"|,)\s+(.+)$", re.S)
_COND_TAIL_RE = re.compile(r"^(.+?)\s*,?\s*(?:nếu|neu|trong trường hợp|trong truong hop)\s+(.+)$", re.S)
_TAIL_Y = re.compile(r"^(?:sao|the nao|ra sao|nhu the nao|lam sao|duoc khong|co duoc khong)\W*$")
_COND_THI_RE = re.compile(r"^(\S+(?:\s+\S+){2,}?)\s+" + _THI + r"\s+(.+)$", re.S)     # "nhà em thuê trọ thì đăng ký thường trú được không": hoàn cảnh (>= 3 chữ) rồi 'thì' + câu chính


@dataclass
class Query:
    raw: str
    terms: list[str] = field(default_factory=list)      # đã bỏ dấu (để khớp)
    accented: list[str] = field(default_factory=list)   # chữ gốc có dấu, song song với `terms`
    fields: list[str] = field(default_factory=list)
    provinces: list[str] = field(default_factory=list)
    flags: dict = field(default_factory=dict)           # free_fee, legal, ...

    @property
    def procedure_query(self) -> str:
        return " ".join(self.terms)


_SPOKEN = re.compile(r"(?<!\w)(?:hổng|hông|hông|hok|hem)(?!\w)")


def _norm_keep_accent(text: str) -> str:
    return re.sub(r"[^\w\s]", " ", (text or "").lower().replace("đ", "đ")).strip()


# Cụm chứa chữ trùng STOP nhưng là nghiệp vụ: giữ nguyên (đo: "bản sao", "căn cước", "làm lại" mất chữ).
PROTECT = ("ky lai", "ban sao", "ban chinh", "ban dich", "cap lai", "lam lai", "can cuoc", "can cu", "cho thue",
           "cha me con", "con nuoi", "giay to ca nhan", "cap doi", "ho so", "cho phep")
# Viết tắt/gõ tắt/sai chính tả hay gặp, MỞ RỘNG SAU KHI bỏ stop (để canonical không bị stop nuốt).
EXTRA_SYN = {"hso": "ho so", "bn": "bao nhieu", "onl": "online", "onlinee": "online", "ng": "nguoi",
             "giay tow": "giay to", "tow": "to", "ki": "ky", "kí": "ky", "kj": "ky", "dky": "dang ky",
             "dk": "dang ky", "tt": "thuong tru", "tamtru": "tam tru",
             "gp": "giay phep", "gcn": "giay chung nhan", "cccd": "can cuoc cong dan", "cmnd": "chung minh nhan dan", "gks": "giay khai sinh",
             "hk": "ho khau", "hkd": "ho kinh doanh", "dkkd": "dang ky kinh doanh", "qsdd": "quyen su dung dat", "gtlq": "giay to lien quan",
             "ub": "uy ban", "ubnd": "uy ban nhan dan", "ho tich": "ho tich"}
# Viết tắt nằm TRONG tên thủ tục ("Giải quyết hưởng chế độ TNLĐ, BNN", "Giải quyết hưởng BHXH một lần"): Index khai triển trong tên, câu hỏi cũng khai triển,
# nên người dân gõ "tai nạn lao động" hay "TNLĐ" đều khớp. Giá trị có dấu (để khớp dấu). Liệt kê từ các chữ HOA trong tên (xem tests).
NAME_ABBR = {"bhxh": "bảo hiểm xã hội", "bhyt": "bảo hiểm y tế", "bhtn": "bảo hiểm thất nghiệp", "bhtnld": "bảo hiểm tai nạn lao động",
             "tnld": "tai nạn lao động", "bnn": "bệnh nghề nghiệp", "ubnd": "ủy ban nhân dân", "hdnd": "hội đồng nhân dân", "nld": "người lao động",
             "bhtnlđ": "bảo hiểm tai nạn lao động", "tnlđ": "tai nạn lao động", "hđnd": "hội đồng nhân dân", "nlđ": "người lao động"}
ABBR_ACTIVE: set = set()      # viết tắt ĐƯỢC khai triển: chỉ những chữ xuất hiện trong >= 3 tên (dùng như tên việc thật); chữ nằm lẻ trong danh sách liệt kê ("BHXH, BHYT, BHTN") thì giữ nguyên. Index nạp.
# Từ ĐỜI THƯỜNG -> cụm trong tên thủ tục. Khác bảng trên: đây là nghĩa chứ không phải viết tắt, và khớp THEO CÓ DẤU (trước khi bỏ dấu):
# bỏ dấu thì "đóng cửa" trùng "(hoạt) động của", "lý di" trùng "xử lý di (dời)".
# ponytail: bảng tay ~20 cụm hay gặp, người gõ không dấu thì không được lợi; mở rộng bằng log thật. Chỉ thêm cụm chuẩn có trong tên thủ tục của kho.
COLLOQUIAL = [(r"độc thân", "tình trạng hôn nhân"), (r"báo tử", "khai tử"), (r"ly dị", "ly hôn"),
              (r"nhận (?:về )?nuôi|nhận con nuôi", "nuôi con nuôi"), (r"đẻ", "sinh"),
              (r"đóng cửa", "chấm dứt hoạt động"), (r"nghỉ kinh doanh|tạm dừng kinh doanh", "tạm ngừng kinh doanh"),
              (r"sổ đỏ|sổ hồng", "giấy chứng nhận quyền sử dụng đất"),
              (r"sao y|photo công chứng", "chứng thực bản sao"), (r"người tàn tật|tật nguyền", "người khuyết tật"),
              (r"(?:lấy|cưới) (?:vợ|chồng)", "kết hôn"),
              (r"(?:giấy )?(?:chứng nhận|xác nhận)(?: là)? chưa (?:từng )?(?:đăng ký )?kết hôn", "giấy xác nhận tình trạng hôn nhân"),
              (r"xóa (?:tên )?(?:trong |khỏi )?(?:sổ )?hộ khẩu", "xóa đăng ký thường trú"),
              (r"(?:đổi|sửa|thay) (?:họ|ngày sinh|năm sinh|quê quán|dân tộc)|(?:đổi|sửa|thay) tên (?:cho )?(?:con|bé|cháu)|(?:sửa|đổi) tên trong (?:giấy )?khai sinh|sai (?:họ|tên|ngày sinh|năm sinh) (?:trong )?(?:giấy )?khai sinh|(?:sửa|chỉnh sửa|đính chính) (?:giấy )?khai sinh", "thay đổi cải chính bổ sung thông tin hộ tịch")]
_COLLOQUIAL_RE = [(re.compile(r"(?<!\w)(?:" + p + r")(?!\w)"), r) for p, r in COLLOQUIAL]
# người gõ KHÔNG DẤU ("doc than", "sao y") cũng được lợi: bản bỏ dấu của cùng luật, chỉ chạy khi cả câu không có dấu; bỏ luật ngắn (bỏ dấu "đẻ" thành "de" trùng "để")
_COLLOQUIAL_FOLD = [(re.compile(r"(?<!\w)(?:" + _fold(p) + r")(?!\w)"), r) for p, r in COLLOQUIAL if len(_fold(p)) >= 7]


def _colloquial(text: str) -> str:
    for rx, rep in _COLLOQUIAL_RE:
        text = rx.sub(rep, text)
    if text == _fold(text):
        for rx, rep in _COLLOQUIAL_FOLD:
            text = rx.sub(rep, text)
    return text


# Cặp chữ liền kề có trong TÊN thủ tục (Index nạp lúc dựng). Chữ trùng STOP mà đứng trong cặp này là nghiệp vụ ("thôi làm", "nộp tiền", "mẫu mới"): giữ.
# ponytail: biến toàn cục (1 DB/tiến trình); đổi thành tham số nếu cần nhiều kho.
NAME_BIGRAMS: set = set()
NAME_NGRAMS: set = set()      # bigram + trigram trong tên (dùng cho split_segments)
EXTRA_KNOWN: set = set()      # chữ diễn ngôn/thứ tự/xã giao (rank.py nạp): cũng là từ vựng để tách chữ dính ("chắckhông", "cuốicùng", "thìsao")
VOCAB: set = set()            # chữ (đã bỏ dấu) trong tên/lĩnh vực của kho (Index nạp): từ vựng để tách chữ gõ dính liền


# ---- tách chữ DÍNH LIỀN ("kethon", "dangkykhaisinh", "muondangky") --------------------------------------------------------------------------------------
# Nguyên nhân gốc của lỗi: chữ dính là MỘT token lạ nên không khớp chữ nào của kho -> "không tìm thấy thủ tục" (hoặc cổng chữ lạ chặn). Chữ dính chỉ là các âm tiết
# thiếu dấu cách, nên tách bằng quy hoạch động trên TỪ VỰNG CỦA KHO: mỗi mảnh phải là âm tiết hợp lệ (quy tắc âm đầu + vần + âm cuối) VÀ có trong từ vựng
# (tên thủ tục, lĩnh vực, chữ chỉ mục, chữ dừng, viết tắt); ưu tiên cách tách có nhiều cặp/bộ ba chữ LIỀN KỀ trong tên thủ tục (cụm dài nhất có trong từ vựng), rồi ít mảnh nhất.
# Từ nước ngoài ("karaoke", "bitcoin") không tách được thành âm tiết hợp lệ nên không bị biến thành chữ nghiệp vụ.
_ONSET = r"(?:ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdghklmnpqrstvx])?"
_SYL = re.compile(r"^" + _ONSET + r"[aeiouy]{1,3}(?:ng|nh|ch|[cmnpt])?$")
_ABBR_PIECE = {"dk", "dky", "hk", "tt", "hso", "gp", "gks", "gcn", "hkd", "cccd", "cmnd", "ubnd", "ko", "dc", "bn", "xn", "tg", "lp", "vb"}
_known_cache: tuple = (None, set())
CUE_BIGRAMS = {(a, b) for cs in FIELD_CUES.values() for c in cs for a, b in zip(c.split(), c.split()[1:])}      # cặp chữ liền kề trong cụm chỉ-mục ("ở đâu", "bao lâu", "nộp ở"): cũng là bằng chứng tách chữ dính


def _known() -> set:
    global _known_cache
    key = (len(VOCAB), len(STOP), len(EXTRA_KNOWN))
    if _known_cache[0] != key:
        _known_cache = (key, VOCAB | STOP | _CUE_WORDS | EXTRA_KNOWN | set(PRE_SYN) | set(EXTRA_SYN))
    return _known_cache[1]


_ONE = {"y", "o", "a", "e", "u", "i"}       # chữ MỘT ký tự có trong tên thủ tục ("y tế", "nhà ở"): chỉ nhận khi kề một cặp chữ có trong tên


def _piece_ok(w: str, known: set) -> bool:
    if w not in known:
        return False
    if len(w) == 1:
        return w in _ONE
    return bool(_SYL.match(w)) or w in _ABBR_PIECE or w in PRE_SYN or w in STOP or (3 <= len(w) <= 6 and w in VOCAB) or (len(w) >= 3 and (w in _CUE_WORDS or w in EXTRA_KNOWN))      # viết tắt trong tên ("bhxh", "abtc") không phải âm tiết nhưng là chữ của kho


def _typo_of_vocab(tok: str) -> bool:
    """tok cách một chữ của kho đúng một phép sửa Damerau (xoá/thêm/đổi/hoán vị 1 ký tự)."""
    L = "abcdefghijklmnopqrstuvwxyz"
    sp = [(tok[:i], tok[i:]) for i in range(len(tok) + 1)]
    cand = {a + b[1:] for a, b in sp if b} | {a + b[1] + b[0] + b[2:] for a, b in sp if len(b) > 1} | {a + c + b[1:] for a, b in sp if b for c in L} | {a + c + b for a, b in sp for c in L}
    cand.discard(tok)
    return any(c in VOCAB for c in cand)


def unglue(folded_tok: str) -> list[str] | None:
    """Chữ (đã bỏ dấu, chỉ a-z) dính liền -> các âm tiết/chữ trong từ vựng, hoặc None khi không tách được an toàn.
    ponytail: DP vét cạn theo (vị trí, hai mảnh trước) trên chữ <= 70 ký tự; chấm điểm theo cặp/bộ ba liền kề trong tên thủ tục, chưa dùng tần suất.
    Nâng cấp: trọng số IDF/tần suất khi kho có nhiều cụm trùng điểm."""
    n = len(folded_tok)
    known = _known()
    if n < 4 or n > 70 or not folded_tok.isalpha() or folded_tok in known:
        return None
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def best(i: int, prev: str, prev2: str):
        if i == n:
            return (0.0, ())
        res = None
        for j in range(i + 1, n + 1):
            w = folded_tok[i:j]
            if not _piece_ok(w, known):
                continue
            sc = 4.0 * ((prev, w) in NAME_BIGRAMS or (prev, w) in CUE_BIGRAMS) + 2.0 * ((prev2, prev, w) in NAME_NGRAMS) - (3.0 if len(w) == 1 else 0.3)
            r = best(j, w, prev)
            if r is None:
                continue
            cand = (sc + r[0], (w,) + r[1])
            if res is None or cand[0] > res[0]:
                res = cand
        return res
    r = best(0, "", "")
    if r is None or len(r[1]) < 2:
        return None
    pcs = list(r[1])
    link = [(a, b) in NAME_BIGRAMS or (a, b) in CUE_BIGRAMS for a, b in zip(pcs, pcs[1:])]
    if any(len(w) == 1 and not ((k and link[k - 1]) or (k < len(link) and link[k])) for k, w in enumerate(pcs)):
        return None       # chữ một ký tự không kề cặp nào trong tên ("ka|ra|o|ke" trong "karaoke"): không tách
    if not any(link) and not all(len(w) >= 2 and (w in VOCAB or w in STOP or w in _CUE_WORDS or w in EXTRA_KNOWN or w in _ABBR_PIECE or w in PRE_SYN) for w in pcs):
        return None       # không cặp liền kề nào trong tên và còn mảnh chỉ là viết tắt: có thể chỉ là chữ lạ tình cờ ghép được, không tách
    if n < 6 and not any(link) and not all(w in STOP or w in EXTRA_KNOWN or w in _CUE_WORDS or w in PRE_SYN or w in _ABBR_PIECE for w in pcs):
        return None       # chữ ngắn (4-5 ký tự) cần có cặp trong tên mới tách (tránh biến lỗi gõ ngắn thành hai chữ)
    if not any(link) and _typo_of_vocab(folded_tok):
        return None       # chỉ cách một lỗi gõ (thêm/bớt/đổi/hoán vị 1 ký tự) so với MỘT chữ của kho và không có cặp liền kề: là lỗi chính tả (Index._fix sửa), không phải chữ dính
    return pcs


def unglue_text(text: str) -> str:
    """Tách mọi chữ dính trong câu (chữ thường, có dấu hoặc không). Giữ dấu cho từng mảnh khi bỏ dấu không đổi độ dài (NFC)."""
    def fix(m):
        tok = m.group(0)
        f = _fold(tok).replace(" ", "").lower()
        pcs = unglue(f) if len(f) == len(tok) else None
        if not pcs:
            return tok
        out, k = [], 0
        for w in pcs:
            out.append(tok[k:k + len(w)])
            k += len(w)
        return " ".join(out)
    return re.sub(r"[^\W\d_]{4,70}", fix, text)
# Mở đầu văn nói/kể lể: cái cần hỏi đứng SAU "(cho) em hỏi / muốn hỏi / hỏi về". Chỉ cắt khi phần sau còn >= 2 chữ.
_LEAD_RE = re.compile(r"^.*?(?<!\w)(?:(?:muon|can|dinh|xin) hoi|cho (?:em |minh |toi |tui |con |anh |chi |mk )?hoi|hoi (?:ve|vu|xiu|chut)|"
                      r"(?:bac|ad|admin|bot|anh|chi|co|chu) oi)(?: (?:ve|vu|xiu|chut|cai|thu tuc|ne|nha|a))*\s")
_LEAD_FILL = re.compile(r"(?<!\w)(?:thu tuc|the nao|sao|nhe|nha|a|z|ne|ha|voi)(?!\w)")


# Hư từ quá phổ biến: nằm trong rất nhiều cặp tên ("hộ có", "ở nhà") nên cặp-tên KHÔNG đủ để giữ lại.
_FUNC = set("cho co la va voi cua thi ma nay do de tai trong nhu khong gi a o duoc nao".split())


def _protected(words: list[str]) -> set[int]:
    keep: set[int] = set()
    for i in range(len(words)):
        if words[i] not in _FUNC and ((i + 1 < len(words) and (words[i], words[i + 1]) in NAME_BIGRAMS) or (i and (words[i - 1], words[i]) in NAME_BIGRAMS)):
            keep.add(i)
    for ph in PROTECT:
        pw = ph.split()
        for i in range(len(words) - len(pw) + 1):
            if words[i:i + len(pw)] == pw:
                keep.update(range(i, i + len(pw)))
    return keep


_RX_CUES = [(re.compile(r" (?:chi phi|dong tien|phai dong|tien phi)(?= (?:la|het|bao nhieu|the nao|khong|ko|ra sao|nhieu|vay)(?: |$)| $)"), "fees"),
           (re.compile(r"^ (?:chi phi|tien phi|phi) (?=(?:dang ky|cap|gia han|xoa|chung thuc|lam|xin|khai|tach|doi|thong bao|cong nhan)(?: |$))"), "fees")]
_SRC = re.compile(r"\b(?:lay thong tin|nguon|trich dan|duong dan|link)\b")
_ONLINE_Q = re.compile(r"\b(?:duoc|dc)\s*(?:khong|ko|k|hok|hong)\b|\bco (?:the )?nop\b|\blink\b")
_TIME_NUM = re.compile(r"\b\d+\s*(?:ngay|tuan|thang|gio)\b")
_FEE_NUM = re.compile(r"\d[\d.,]*\s*(?:dong|d|vnd|nghin|k|trieu)\b")


_STEPS_EXPLICIT = re.compile(r"\b(?:cac buoc|buoc thuc hien|buoc nao|trinh tu|quy trinh|cach thuc hien|cach lam|huong dan lam|lam sao|lam the nao|can lam gi|thuc hien the nao|thuc hien nhu the nao)\b")


def _tidy_fields(q: Query, f0: str) -> None:
    """Hậu xử lý cụm chỉ-field: một cụm là TRẠNG NGỮ/hoàn cảnh chứ không phải mục được hỏi thì bỏ ('nộp online mất bao nhiêu tiền' hỏi phí),
    cụm yếu ('là gì') chỉ tính khi không có mục nào khác, hỏi nguồn thì không kèm 'ở đâu'/'cổng DVC'.
    ponytail: luật theo cụm, chưa hiểu cú pháp; câu kể dài nhiều mệnh đề có thể sót."""
    f = q.fields
    if _FEE_NUM.search(f0) and "fees" not in f:
        f.append("fees")
    if _TIME_NUM.search(f0) and re.search(r"\b(?:mat|het|trong|sau)\b", f0) and "processing_time" not in f:
        f.append("processing_time")
    if "meta" in f and _SRC.search(f0):
        for x in ("address", "online", "agency"):
            if x in f and not (x == "online" and re.search(r"\bnop\b|truc tuyen|online", f0)):
                f.remove(x)
    if "explanation" in f and len(f) > 1 and not re.search(r"dieu kien|doi tuong|ai duoc|co duoc khong", f0):
        f.remove("explanation")
    if "steps" in f and len(f) > 1 and not _STEPS_EXPLICIT.search(f0):
        f.remove("steps")             # "thời gian giải quyết/lệ phí/hồ sơ thế nào/như thế nào": 'thế nào' chỉ là từ hỏi của mục kia, không phải các bước
    if "files" in f and "address" in f and re.search(r"\btai\b", f0):
        f.remove("address")           # "biểu mẫu tải ở đâu": hỏi nơi tải mẫu, không phải nơi nộp
    if "online" in f and len(f) > 1 and not _ONLINE_Q.search(f0):
        f.remove("online")


_SUBJ = re.compile(r"^ (?:gia dinh|nha|vo chong|ong|ba|bo|me|con|cha|anh|chi|em|chau|co|chu|bac|e)(?: (?:toi|em|minh|tui|cua toi|cua em|cua minh))?(?= (?:can|muon|dang|vua|se|phai|di|xin|hoi|dinh) )")
_MODAL_GO = re.compile(r" (?:can|muon|phai|nen|dinh|se|xin) (?:di|den|ra|len|vao) (?=(?:khai|dang|xoa|lam|nop|xin|tach|chung|cap|doi|gia|thong|dk|ky) )")
_BENEF = re.compile(r" cho (me|bo|cha|ba|ong|vo|chong|anh|chi|chau|bac|chu|di|cau|co)(?: (?:em|toi|minh|tui|cua em|cua toi|cua minh))?(?= )")


def _phi_in_name(folded: str) -> bool:
    """'phí' đứng trong tên thủ tục ("hỗ trợ chi phí y tế", "kinh phí", "học phí"): cặp (chữ trước, phí) có trong tên thật thì không phải câu hỏi lệ phí."""
    return any((m.group(1), "phi") in NAME_BIGRAMS for m in re.finditer(r" (\w+) phi(?= )", folded))


def _squash(text: str) -> str:
    return re.sub(r"[^\W\d_]+", lambda m: m.group(0) if _fold(m.group(0)) in EXTRA_SYN or _fold(m.group(0)) in PRE_SYN else re.sub(r"(\w)\1{2,}", r"\1", m.group(0)), text)


def understand(conn, text: str, syn: dict | None = None) -> Query:
    q = Query(raw=text)
    text = _squash(text or "")                  # kéo dài chữ ("khôngggg", "đăngggg ký"): bỏ lặp từ 3 lần trở lên (trừ viết tắt thật như "cccd")
    folded = f" {_fold(_SPOKEN.sub('không', _colloquial(unglue_text((text or '').lower()))))} "     # 'hổng/hông' (không) khác 'hỏng' (hư): xử lý TRƯỚC khi bỏ dấu
    for pat, name in _PROVINCE_PATTERNS:
        if f" {pat} " in folded:
            folded = folded.replace(f" {pat} ", " ")
            if name not in q.provinces:
                q.provinces.append(name)
    syn = dict(syn if syn is not None else synonyms_map(conn))
    single = {}
    for raw_term, canon in syn.items():       # cụm nhiều chữ: mở rộng ngay; 1 chữ: để sau stop
        t = _fold(raw_term)
        if " " in t:
            if f" {t} " in folded:
                folded = folded.replace(f" {t} ", f" {_fold(canon)} ")
        else:
            single[t] = _fold(canon)
    for raw_term, canon in list(EXTRA_SYN.items()) + [(k, _fold(v)) for k, v in NAME_ABBR.items() if k in ABBR_ACTIVE]:
        t = _fold(raw_term)
        if " " in t:
            folded = folded.replace(f" {t} ", f" {_fold(canon)} ")
        else:
            single.setdefault(t, _fold(canon))
    folded = " " + " ".join(PRE_SYN.get(w, w) for w in folded.split()) + " "
    folded = _SUBJ.sub(" ", folded, count=1)           # "gia đình cần đi khai tử": chủ ngữ + động từ yêu cầu, không phải chữ của tên thủ tục
    folded = _MODAL_GO.sub(" ", folded)               # "cần đi khai tử", "muốn đến đăng ký": 'đi/đến' là động từ đưa đường, 'đi khai' tình cờ có trong tên khác
    for m in list(_BENEF.finditer(folded)):          # "khai tử cho mẹ em": người thụ hưởng là người nhà, không phải chữ của tên thủ tục
        if ("cho", m.group(1)) not in NAME_BIGRAMS:
            folded = folded.replace(m.group(0), " ", 1)
    f2 = folded.strip() + " "
    m = _LEAD_RE.match(f2)
    if m and len(_LEAD_FILL.sub(" ", f2[m.end():]).split()) >= 2:
        folded = " " + f2[m.end():]
    for ph in _DROP_PHRASES:
        folded = folded.replace(f" {ph} ", " ")
    # cụm chỉ-field -> fields, gỡ khỏi câu (dài trước)
    cues = sorted(((c, f) for f, cs in FIELD_CUES.items() for c in cs), key=lambda cf: -len(cf[0]))
    for cue, fname in cues:
        if f" {cue} " in folded and not any(cue in ph and f" {ph} " in folded for ph in NOT_FIELD) and not (cue == "phi" and _phi_in_name(folded)):
            if fname not in q.fields:
                q.fields.append(fname)
            if cue == "o dau":
                q.flags["where"] = True       # "X ở đâu" chung chung (không nói nộp/địa chỉ): nơi làm = cơ quan khi cổng không ghi địa điểm (Policy)
            folded = folded.replace(f" {cue} ", " | ")      # '|' chặn nối cặp chữ qua chỗ vừa gỡ (bảo vệ bigram tên thủ tục)
    for rx, fname in _RX_CUES:       # cụm mơ hồ với tên thủ tục ("hỗ trợ chi phí mai táng"): chỉ là câu hỏi khi đứng cuối câu hoặc kèm từ hỏi
        if rx.search(folded):
            if fname not in q.fields:
                q.fields.append(fname)
            folded = rx.sub(" | ", folded)
    f0 = _fold(text)
    _tidy_fields(q, f0)
    if re.search(r"\bmien\b", f0):
        q.flags["asks_free"] = True
    toks = folded.split()
    keep = _protected(toks)
    words: list[str] = []
    for i, w in enumerate(toks):
        if w == "|" or (i not in keep and (w in STOP or w.isdigit())):
            continue
        words.extend(single.get(w, w).split())
    if q.fields and words and set(words) <= _FIELD_VERBS:
        words = []          # chỉ còn động từ đệm của cụm hỏi mục ("giải quyết [trong bao lâu]", "thực hiện [các bước]"): không phải tên thủ tục
    # chữ có dấu tương ứng: lấy từ câu gốc theo vị trí đã bỏ dấu
    orig = {}
    for w in re.findall(r"\w+", (text or "").lower()):
        orig.setdefault(_fold(w), w)
    q.terms = words
    q.accented = [orig.get(w, w) for w in words]
    return q


def strip_condition(text: str) -> tuple[str, str]:
    """-> (câu chính, điều kiện thô). Điều kiện đi vào Query.flags['condition'], không vào tên thủ tục.
    ponytail: regex; Planner LLM tách điều kiện/context chính xác hơn."""
    t = (text or "").strip()
    low = t.lower()
    m = _COND_RE.match(low)
    if m and m.group(2).strip():
        return m.group(2).strip(), m.group(1).strip()
    m = _COND_TAIL_RE.match(low)
    if m and m.group(1).strip():
        return m.group(1).strip(), m.group(2).strip()
    m = _COND_THI_RE.match(low)
    if m and not _TAIL_Y.match(_fold(m.group(2)).strip()):      # "còn lệ phí thì sao": vế sau chỉ là câu cụt, không phải câu chính
        return m.group(2).strip(), m.group(1).strip()
    return t, ""


def _joins(lw: list[str], d: str, rw: list[str]) -> bool:
    """Ranh giới (lw | d | rw) nằm TRONG một tên thủ tục? Cần cả cặp lẫn bộ ba chữ quanh ranh giới có trong tên (bộ ba tránh nối nhầm
    "...bao nhiêu tiền; cấp lại ..." chỉ vì ("tiền","cấp") tình cờ có trong một tên)."""
    if not lw or not rw:
        return False
    mid = [d] if d else []
    seq = lw[-2:] + mid + rw[:2]
    if (lw[-1], *mid, rw[0]) not in NAME_NGRAMS and not (d and (lw[-1], d) in NAME_NGRAMS and (d, rw[0]) in NAME_NGRAMS):
        return False
    tri = [tuple(seq[i:i + 3]) for i in range(len(seq) - 2)]
    return not tri or any(t in NAME_NGRAMS for t in tri)


def split_segments(text: str) -> list[str]:
    """Luật tách multi-intent (fallback của Planner): ?, ;, 'còn', 'và', 'với lại', dấu phẩy.
    Không tách tại chỗ nằm TRONG một tên thủ tục ("Cấp, cấp lại ...", "Công nhận và giải quyết ..."): cặp chữ hai bên ranh giới
    (kèm từ nối nếu là chữ) có trong NAME_BIGRAMS thì nối lại.
    ponytail: tách thô theo từ nối; Planner LLM thay thế sau. Đoạn quá ngắn gộp vào đoạn trước."""
    t = (text or "").lower().strip()
    pieces = re.split(r"(\s*(?:[?;,.]|(?<!\w)(?:còn|với lại|voi lai|và|va|sau đó|sau do|ngoài ra|ngoai ra)(?!\w))\s*)", t)   # [đoạn, nối, đoạn, ...]
    segs = [pieces[0]]
    for i in range(1, len(pieces) - 1, 2):
        d, nxt = _fold(pieces[i]), pieces[i + 1]
        lw, rw = _fold(segs[-1]).split()[-1:], _fold(nxt).split()[:1]
        if d in ("?", "."):       # hết câu: ranh giới thật
            segs.append(nxt)
        elif _joins(_fold(segs[-1]).split(), d, _fold(nxt).split()):
            segs[-1] += pieces[i] + nxt
        else:
            segs.append(nxt)
    segs = [s.strip() for s in segs if s and s.strip()]
    return segs or [t]

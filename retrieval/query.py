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
    "components": ["nop cai gi", "nop nhung gi", "phai nop gi", "giay to", "ho so gom", "ho so", "thanh phan", "can nhung gi", "can gi", "can chuan bi",
                   "chuan bi gi", "chuan bi nhung gi", "mang theo", "can mang"],
    "fees": ["le phi bao nhieu tien", "le phi bao nhieu", "co thu phi khong", "thu phi", "het bao nhieu", "mat bao nhieu", "le phi", "mien phi", "co mat phi", "mat phi", "bao nhieu tien", "ton bao nhieu", "mat bao nhieu tien",
             "co mat tien", "mat tien", "phi la", "phi bao nhieu", "phi"],
    "processing_time": ["mat may bua", "may bua", "may hom", "may tuan", "mat may ngay", "het may ngay", "bao nhieu lau", "lau khong", "mat bao lau", "bao lau", "may ngay", "thoi gian giai quyet", "thoi han giai quyet", "thoi gian", "thoi han",
                        "mat bao nhieu ngay", "bao nhieu ngay", "nhan ket qua sau"],
    "address": ["nop cho ai", "den dau nop", "di dau nop", "dia chi nao", "dia chi", "nop o dau", "nop tai dau", "dia diem", "noi nop", "nop ho so o dau", "o dau"],
    "online": ["tren mang", "nop tren mang", "truc tuyen", "online", "cong dich vu cong", "cong dvc", "link", "duong link", "dich vu cong", "qua mang", "nop mang"],
    "methods": ["hinh thuc nop", "nop truc tiep", "qua buu dien", "buu chinh", "cach thuc nop"],
    "files": ["bieu mau", "mau don", "mau to khai", "to khai mau", "tai mau", "file mau", "tai ve"],
    "agency": ["do co quan nao giai quyet", "co quan nao giai quyet", "ai giai quyet", "co quan nao", "co quan giai quyet", "ai giai quyet", "cap nao", "noi nao giai quyet", "to chuc nao"],
    "steps": ["gom nhung buoc nao", "cac buoc", "buoc nao", "quy trinh", "trinh tu", "lam the nao", "lam sao",
              "cach lam", "huong dan lam", "thuc hien the nao", "thuc hien nhu the nao", "nhu the nao", "the nao"],
    "explanation": ["la gi", "dieu kien", "doi tuong nao", "ai duoc", "co duoc khong"],
    "meta": ["van ban nao quy dinh", "van ban quy dinh", "thong tu nao quy dinh", "nghi dinh nao quy dinh", "can cu vao van ban nao", "van ban nao", "thong tu nao", "nghi dinh nao", "luat nao", "quy dinh nao", "dua tren quy dinh nao", "dua tren", "quyet dinh cong bo", "trich dan", "duong dan", "lay thong tin o dau", "lay thong tin", "lay tu dau", "nguon", "can cu phap ly", "co so phap ly", "van ban phap luat", "van ban", "quyet dinh so", "nghi dinh", "luat nao",
             "can cu"],
}
_CUE_WORDS = {w for cs in FIELD_CUES.values() for c in cs for w in c.split()}
# Lượng từ/hư từ/động từ đệm: không phải tên thủ tục. KHÔNG gồm những chữ có thể là nghiệp vụ.
STOP = set("""toi minh muon t tao ko k hok dc duoc giup xin oi nhe nhi vay gi cho hoi la va voi con cua thi
nay nua het hay da se rat nhieu moi can muon phai co khong nao bao the sao a u on nha
bi nhung cac mot nhu o tai de ma ve thoi roi lai lam xong biet ban em anh bac
di den ra vao len xuong neu ay do kia day ben nhe chu theo trong tren duoi dau
ok oke okie okay uh um ua ah ak ad admin z zay zi nop
chao hello hi alo da hem hok hen nghen ne nghe noi hom bua chua ranh xiu chut tui tao may chi
mk bn ha hay haha thanks cam on xin lam on gium giup muon biet hieu roi hoi vu cai""".split())
# Gõ tắt/văn nói đổi THÀNH cụm chuẩn TRƯỚC khi tìm cụm chỉ-field (nếu để sau, "mất bn tiền" không khớp "mất bao nhiêu").
PRE_SYN = {"bn": "bao nhieu", "j": "gi", "gj": "gi", "dc": "duoc", "dg": "dang", "r": "roi", "ntn": "nhu the nao", "sao z": "sao"}
# Một số chữ trên là nghiệp vụ nếu đứng trong cụm đặc thù; giữ nguyên cụm trước khi bỏ stop.
KEEP_PHRASES = ["con nho", "cho thue", "cap lai", "lam lai"]

_DROP_PHRASES = ("thong tin ve thu tuc", "cho minh hoi", "cho toi hoi", "cho hoi", "vui long", "lam on", "thu tuc", "ho so thu tuc",
                 "binh thuong", "thuong thoi", "phai lam sao", "phai lam gi", "phai lam nhung gi", "lam giay to", "lam giay", "giay gi")
_SEG_SPLIT = re.compile(r"\s*(?:[?;,.]|(?<!\w)(?:còn|với lại|và|sau đó|ngoài ra)(?!\w))\s*")
# "nếu/trường hợp <điều kiện> thì <câu chính>": điều kiện KHÔNG phải tên thủ tục.
_COND_RE = re.compile(r"^(?:.*?\s)?(?:nếu|trường hợp|đối với)\s+(.+?)\s*(?:thì|,)\s+(.+)$", re.S)
_COND_TAIL_RE = re.compile(r"^(.+?)\s*,?\s*(?:nếu|trong trường hợp)\s+(.+)$", re.S)


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


# Cặp chữ liền kề có trong TÊN thủ tục (Index nạp lúc dựng). Chữ trùng STOP mà đứng trong cặp này là nghiệp vụ ("thôi làm", "nộp tiền", "mẫu mới"): giữ.
# ponytail: biến toàn cục (1 DB/tiến trình); đổi thành tham số nếu cần nhiều kho.
NAME_BIGRAMS: set = set()
NAME_NGRAMS: set = set()      # bigram + trigram trong tên (dùng cho split_segments)
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


def understand(conn, text: str, syn: dict | None = None) -> Query:
    q = Query(raw=text)
    folded = f" {_fold(_SPOKEN.sub('không', (text or '').lower()))} "     # 'hổng/hông' (không) khác 'hỏng' (hư): xử lý TRƯỚC khi bỏ dấu
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
    for raw_term, canon in EXTRA_SYN.items():
        t = _fold(raw_term)
        if " " in t:
            folded = folded.replace(f" {t} ", f" {_fold(canon)} ")
        else:
            single.setdefault(t, _fold(canon))
    folded = " " + " ".join(PRE_SYN.get(w, w) for w in folded.split()) + " "
    f2 = folded.strip() + " "
    m = _LEAD_RE.match(f2)
    if m and len(_LEAD_FILL.sub(" ", f2[m.end():]).split()) >= 2:
        folded = " " + f2[m.end():]
    for ph in _DROP_PHRASES:
        folded = folded.replace(f" {ph} ", " ")
    # cụm chỉ-field -> fields, gỡ khỏi câu (dài trước)
    cues = sorted(((c, f) for f, cs in FIELD_CUES.items() for c in cs), key=lambda cf: -len(cf[0]))
    for cue, fname in cues:
        if f" {cue} " in folded:
            if fname not in q.fields:
                q.fields.append(fname)
            folded = folded.replace(f" {cue} ", " | ")      # '|' chặn nối cặp chữ qua chỗ vừa gỡ (bảo vệ bigram tên thủ tục)
    if re.search(r"\bmien\b", _fold(text)):
        q.flags["asks_free"] = True
    toks = folded.split()
    keep = _protected(toks)
    words: list[str] = []
    for i, w in enumerate(toks):
        if w == "|" or (i not in keep and (w in STOP or w.isdigit())):
            continue
        words.extend(single.get(w, w).split())
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
    pieces = re.split(r"(\s*(?:[?;,.]|(?<!\w)(?:còn|với lại|và|sau đó|ngoài ra)(?!\w))\s*)", t)   # [đoạn, nối, đoạn, ...]
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

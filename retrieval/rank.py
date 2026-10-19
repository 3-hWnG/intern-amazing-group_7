"""Xếp hạng thủ tục: IDF theo âm tiết trọn vẹn + phạt lệch dấu + cụm liền kề + cổng phạm vi.

Vì sao không dùng thẳng FTS5 + `is_strong` (đo ở eval/BASELINE.md):
  · bỏ dấu làm "hộ chiếu" trùng "hộ/hỗ" -> strong sai; ở đây chữ có dấu lệch bị nhân 0.35.
  · tỉ lệ âm tiết không phân biệt chữ hiếm/chữ thường; ở đây dùng IDF, chữ không có trong kho
    (karaoke, chiếu…) mang trọng số lớn nhất nên kéo `cov` xuống -> tự rơi khỏi phạm vi.
"""
from __future__ import annotations

import difflib
import math
import re
import unicodedata
from dataclasses import dataclass, field

from system3.data.search import _fold

from . import query as _query
from .query import Query, understand, split_segments, strip_condition, FIELD_CUES, STOP, NAME_ABBR, COND_W
from .variants import choose_variant
from .refs import ordinal, pure_reference, pick, options_from_text, extract_negation, split_compare, load_name_neg
from .context import ConvState, markers, event_hints, strip_labels, _PH

ACCENT_MISMATCH = 0.35     # chữ có dấu của người dùng không khớp dấu trong tên
PREC_BASE = 0.7          # phần điểm không phụ thuộc độ ngắn gọn của tên (biến thể dài bị phạt)
CONTEXT_MISS = 0.5         # trọng số phạt chữ có trong kho nhưng không nằm trong thủ tục này
DOMAIN_FACTOR = 0.4        # khớp ở lĩnh vực thay vì tên
ACCEPT_SCORE = 0.55        # ngưỡng nhận ứng viên (chỉnh theo eval nửa DEV)
ACCEPT_COV = 0.5
COMPLETE_BONUS = 0.06
PREFIX_BONUS = 0.06
PREFIX_PREC = 0.55         # sàn độ chính xác khi chữ của câu hỏi (theo thứ tự) là phần đầu tên lõi của thủ tục
UNCERTAIN_SCORE = 0.85     # dưới mức này Planner nên cho LLM xác nhận ứng viên
UNCERTAIN_COV = 0.9
AMBIG_GAP = 0.06
NEAR_GAP = 0.25            # hỏi lại: ứng viên cùng "bằng chứng" (cov, khối lượng chữ khớp) với top; chênh điểm chỉ do độ dài tên nên cho rộng
PROVINCE_PEN = 0.06        # bản riêng của một tỉnh mà câu hỏi không nêu tỉnh: nhường bản của bộ/ngành
NEAR_PREC = 0.4            # ứng viên mà câu hỏi phủ tên kém hẳn top (tên dài chỉ chứa chữ của câu như một phần nhỏ: "ghi vào sổ ... việc kết hôn ...") không phải anh em gần
NAMED_PREC = 0.95          # top có tên lõi nằm trọn trong câu hỏi => người dùng đã gọi đúng tên, không hỏi lại
EXTRA_IDF = 3.0          # chữ có IDF >= mức này coi là 'hiếm'
UNCERTAIN_EXTRAS = 3
# Chữ 'sự kiện' đổi nghĩa thủ tục (mất, hủy, thu hồi…): tên có mà câu hỏi không có => phạt (đo: 'làm hộ chiếu' ≠ 'trình báo MẤT hộ chiếu').
EVENT_TOKENS = {'mat', 'hong', 'huy', 'xoa'}
EVENT_BIGRAMS = {('thu', 'hoi'), ('cham', 'dut'), ('tam', 'dung'), ('tam', 'ngung'), ('dung', 'thuc'), ('dinh', 'chinh'), ('chua', 'du')}
EVENT_PENALTY = 0.35
# Tên MỞ ĐẦU bằng động từ vòng đời (đổi/cấp lại/gia hạn/điều chỉnh...): thủ tục dành cho người ĐÃ có giấy; câu hỏi không nhắc vòng đời đó thì nhường bản gốc ("xin giấy xác nhận khuyết tật" != "Đổi, cấp lại Giấy xác nhận khuyết tật").
LIFECYCLE_LEAD = [("doi",), ("cap", "lai"), ("gia", "han"), ("dieu", "chinh"), ("thay", "doi"), ("sua", "doi"), ("bo", "sung"), ("dang", "ky", "lai"), ("tiep", "tuc"), ("cap", "dieu", "chinh"), ("cap", "doi")]
LIFECYCLE_PENALTY = 0.12
LIFE_WORDS = {"cap", "lai", "doi", "gia", "han", "thay", "sua", "bo", "sung", "huy", "thu", "hoi", "xoa", "lam", "tiep", "tuc", "dieu", "chinh"}   # động từ vòng đời: không đủ để GỌI TÊN thủ tục
LIFECYCLE_CUES = {"mat", "hong", "rach", "that", "lac", "het", "han", "sai", "nham", "loi"}     # câu nói giấy bị mất/hỏng/hết hạn/sai => đang hỏi vòng đời (cấp lại/đổi/gia hạn), không phạt
_CIRCUMSTANCE = {'bi', 'mat', 'chay', 'rach', 'nat', 'hong', 'huy', 'tieu', 'lai', 'cap', 'xin', 'lam', 'giay', 'chung', 'nhan'}
VERTICAL = ("Thuế", "Hải quan")
CHITCHAT = set("chao xin hello hi alo cam on ban ten ai khoe ok oke vang da tam biet bye thanks thank you tro ly "
               "ad admin bot nhieu hom nay hoi vay thoi nha nhe nhen oi a ban tot qua tuyet gioi hay hen gap lai".split())
_ALL_CUES = [c for cs in FIELD_CUES.values() for c in cs]
_query.EXTRA_KNOWN.update((CHITCHAT - {"you", "thank", "thanks", "hello", "hi", "bye", "ok", "oke", "alo", "ad", "bot", "ten"}) | {w for ph in _PH for w in ph} | {"cuoi", "cung", "giua", "dau", "tien", "thu", "nhat", "mot", "hai", "ba", "bon"})     # chữ diễn ngôn/xã giao/thứ tự: từ vựng để tách chữ dính ("chắckhông", "cuốicùng")
# Chủ đề NGOÀI hệ thống (thủ tục hành chính cấp xã): chặn dù có chữ trùng tình cờ với tên thủ tục. Chữ đã bỏ dấu.
# ponytail: danh sách tay, bổ sung khi log thật gặp thêm chủ đề; không thay cho cổng chữ-đặc-trưng bên dưới.
OOS_TOPICS = re.compile(
    r"(?<!\w)(doi tuyen|bong da|bong chuyen|the thao|world cup|v league|cau thu|huan luyen vien|tran dau|"
    r"ca si|ca sy|bai hat|am nhac|phim anh|dien vien|karaoke|concert|truyen hinh thuc te|"
    r"toa an|khoi kien|ban an|luat su|(?:nop don|kien) .{0,12}(?<!\w)toa(?!\w)|(?<!\w)toa (?:nao|so tham|phuc tham)|"
    r"nhan hieu|so huu tri tue|ban quyen|sang che|kieu dang cong nghiep|thuong hieu|"
    r"thi (?:lay )?(?:bang|giay phep) lai|hoc lai xe|thi lai xe|(?:lam|xin|cap moi|dang ky) (?:moi )?(?:bang|giay phep) lai xe|"
    r"(?:muon|xin|can|nop don|lam thu tuc|thu tuc)(?: \w+){0,3} ly (?:hon|di)|xin viec|tim viec|"
    r"uong thuoc|chua benh|trieu chung|ke don thuoc|dau (?:dau|bung|rang|lung)|"
    r"visa|nhap quoc tich|nhap tich|thoi quoc tich|"
    r"diem thi|thi dai hoc|thi tot nghiep|tieng anh|ngoai ngu|dich (?:giup|cau|sang)|gia vang|gia xang|thoi tiet|chung khoan|bitcoin|tien ao|co phieu|"
    r"gio (?:mo cua|lam viec)|may gio|lich lam viec|thu bay co lam viec|"
    r"that nghiep|tro cap that nghiep|bao hiem that nghiep|giay chung sinh|"
    r"nau (?:an|pho|com)|cong thuc nau|du lich|dat (?:ve|phong)|ve may bay|khach san)(?!\w)")
_PASSPORT = re.compile(r"(?<!\w)ho chieu(?!\w)")
_PASSPORT_OK = re.compile(r"(?<!\w)(mat|trinh bao|bi mat|that lac)(?!\w)")
NAME_FULL_COV = 0.6        # sàn cov khi câu hỏi chứa đủ chữ đặc trưng của tên (câu kể dài: 'công ty em ... gia hạn tạm trú ...')
WEAK_PREC = 0.1            # xem cổng "bằng chứng yếu" trong _resolve_text
GENERIC_COV = 0.8
WEAK_PREC2 = 0.12          # (c) câu phủ rất ít tên thủ tục dài VÀ còn chữ không khớp ("xin cấp lại sổ hộ khẩu giấy" ~ "đăng ký lại phương tiện ... hộ khẩu thường trú"): láng giềng, không phải thủ tục
WEAK_COV2 = 0.9
RESIDUAL_SCORE = 0.9       # mảnh phụ (<=3 chữ) khớp yếu hơn mức này bị coi là phần đệm của ý trước
NEAR_MASS = 2.0            # top khớp nhiều chữ hơn ứng viên khác >= mức này => người dùng ĐÃ nêu từ phân biệt, không hỏi lại
HI_IDF = 3.0               # chữ 'đặc trưng' của kho tên thủ tục (đo: chieu 6.3, tuyen 4.8, uong 6.8; ho/dang/ky < 3)
_PREFIX_RE = re.compile(r"^(?:\([^)]{2,30}\)\s*|[^-–]{2,40}?\s[-–]\s)")


def _lead(p: dict, tset: set):
    """Tên MỞ ĐẦU bằng động từ vòng đời (đổi/cấp lại/gia hạn...) mà câu hỏi không nhắc vòng đời đó -> trả cụm đầu (bị phạt, và không coi là 'anh em gần' của bản gốc)."""
    lead = next((l for l in LIFECYCLE_LEAD if tuple(p["ctoks"][:len(l)]) == l), None)
    return lead if lead and not set(lead).issubset(tset) and not (tset & LIFECYCLE_CUES) else None


def _core_name(name: str) -> str:
    """Phần LÕI của tên thủ tục: bỏ chú thích trong ngoặc.
    Nguyên nhân gốc của chọn nhầm anh em: độ chính xác `prec` chia cho độ dài CẢ tên, nên bản có chú thích dài
    ("Chứng thực chữ ký trong các giấy tờ, văn bản (áp dụng cho cả ...)") luôn thua bản anh em có tên ngắn dù người dùng gõ đúng đầu tên."""
    return re.sub(r"\([^)]*\)?", " ", name).strip()


def _is_prefix(terms: list[str], ctoks: list[str]) -> bool:
    """terms (đúng thứ tự) là phần đầu của tên lõi; chữ hư (STOP) trong tên được phép bị bỏ qua."""
    i = 0
    for t in terms:
        while i < len(ctoks) and ctoks[i] != t and ctoks[i] in STOP:
            i += 1
        if i >= len(ctoks) or ctoks[i] != t:
            return False
        i += 1
    return True


def _dam1(a: str, b: str) -> bool:
    """Khoảng cách Damerau-Levenshtein <= 1 (thêm/bớt/đổi/hoán vị 1 ký tự)."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        d = [i for i in range(la) if a[i] != b[i]]
        if len(d) == 1:
            return True
        return len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]]
    if la > lb:
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


@dataclass
class Hit:
    proc_id: str
    name: str
    domain: str
    score: float
    cov: float
    province: str | None
    default_variant: bool
    head: str
    flags: list = field(default_factory=list)   # vertical:<cơ quan> | province_only | expired
    prec: float = 0.0
    mass: float = 0.0     # tổng IDF các chữ khớp
    nmatch: int = 0
    extras: int = 0       # số chữ HIẾM trong tên mà câu hỏi không có (biến thể/khác việc)
    hi_match: float = 0.0  # tổng IDF chữ ĐẶC TRƯNG của câu hỏi có trong tên thủ tục (đúng dấu)
    hi_miss: float = 0.0   # tổng IDF chữ đặc trưng (có trong kho) của câu hỏi KHÔNG có trong tên
    cmass: float = 0.0     # như mass nhưng chỉ chữ nằm trong TÊN LÕI (không tính chữ khớp trong chú thích/ngoặc)


@dataclass
class Segment:
    text: str
    query: Query
    hits: list = field(default_factory=list)
    proc_id: str | None = None        # đã chọn (None = chưa/không tìm được)
    inherited: bool = False
    reason: str = ""                  # in_scope | out_of_scope | no_match | flagged:<x> | chitchat | field_only
    uncertain: bool = False           # cần LLM xác nhận ứng viên đầu (điểm/độ phủ thấp)
    ambiguous: bool = False           # có ứng viên khác nhóm điểm sát nhau -> có thể cần hỏi lại
    near: list = field(default_factory=list)   # >=3 proc_id khác nhóm, điểm sát nhau (kể cả top): Policy hỏi lại
    relation: str = "independent"     # compare khi tách từ câu so sánh
    decision: str = ""                # new | follow_up | new_related | return | correction | story | independent (xem _contextualize)
    why: str = ""                     # lý do quyết định, ghi vào trace
    oos_topic: bool = False           # chủ đề ngoài hệ thống (OOS_TOPICS/hộ chiếu): không bao giờ kế thừa
    evidence: str = "none"            # legal_basis khi người dùng hỏi lại độ chắc chắn ("chắc không?")


@dataclass
class Result:
    segments: list
    behavior: str                      # answer | apologize
    chitchat: bool = False
    state: ConvState | None = None     # trạng thái SAU lượt này (đề xuất; orchestrator ghi đè bằng thủ tục thực sự đã trả lời)
    ctx: dict = field(default_factory=dict)   # quyết định ngữ cảnh của lượt cuối (cho trace)


class Index:
    def __init__(self, conn):
        rows = conn.execute(
            "SELECT p.proc_id, p.name, p.domain, p.province, p.agency_levels,"
            "       COALESCE(f.default_variant,0) AS dv, COALESCE(f.head,'') AS head"
            "  FROM procedures p LEFT JOIN families f ON f.proc_id=p.proc_id"
            " WHERE p.status='active'").fetchall()
        self.conn = conn
        self.procs, df, ddf = [], {}, {}
        _ab = re.compile(r"(?<!\w)(" + "|".join(sorted(NAME_ABBR, key=len, reverse=True)) + r")(?!\w)", re.I)
        _cnt: dict = {}
        for r in rows:
            for a in {m.lower() for m in _ab.findall(r["name"])}:
                _cnt[a] = _cnt.get(a, 0) + 1
        self.abbr = {a for a, c in _cnt.items() if c >= 3}          # viết tắt dùng như tên việc thật (>= 3 tên): khai triển; còn lại giữ nguyên
        _query.ABBR_ACTIVE = set(self.abbr) | {_fold(a) for a in self.abbr}

        for r in rows:
            name = r["name"]
            core = unicodedata.normalize("NFC", _PREFIX_RE.sub("", name, count=1) if r["province"] else name)     # NFC: đầu vào được chuẩn hoá NFC (context.strip_labels), tên trong DB có thể là NFD ("HỢP NHẤT" gõ rời dấu) -> khớp dấu không bị lệch
            core = re.sub(r"^th[ủu] t[ụu]c\s+", "", core, flags=re.I)   # 'Thủ tục' mở đầu không phải chữ phân biệt: không phạt tên có/không có nó
            core = _ab.sub(lambda m: NAME_ABBR[m.group(1).lower()] if m.group(1).lower() in self.abbr else m.group(1), core)   # khai triển viết tắt trong tên (cả dấu lẫn không dấu)
            toks = _fold(core).split()
            ctoks = _fold(_core_name(core)).split() or toks      # tên "lõi": bỏ ngoặc/liệt kê sau dấu ';' (phần giải thích, không phải việc cần làm)
            acc = set(re.findall(r"\w+", core.lower()))
            dtoks = set(_fold(r["domain"]).split())
            p = dict(proc_id=r["proc_id"], name=name, domain=r["domain"], province=r["province"],
                     levels=r["agency_levels"] or "", dv=bool(r["dv"]), head=r["head"],
                     toks=toks, ctoks=ctoks, ctokset=set(ctoks), tokset=set(toks), acc=acc, dtoks=dtoks,
                     bigrams={(a, b) for a, b in zip(toks, toks[1:])})
            self.procs.append(p)
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n = len(self.procs)
        self.idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        self.max_idf = max(self.idf.values())
        dvocab = {t for p in self.procs for t in p["dtoks"]}
        self.vocab = set(self.idf) | dvocab
        # chữ không nằm trong tên: nặng nếu LẠ với cả kho mô tả (karaoke), nhẹ nếu là chữ chung (dựa, trên).
        cdf = {}
        for (txt,) in conn.execute("SELECT description_folded FROM procedures_fts"):
            for t in set((txt or "").split()):
                cdf[t] = cdf.get(t, 0) + 1
        self.cdf = cdf
        self.n = n
        self._vocab_list = sorted(self.vocab)
        self._by_len = {}
        for v in self._vocab_list:
            self._by_len.setdefault(len(v), []).append(v)
        self.syn = None
        self._byid = {p["proc_id"]: p for p in self.procs}
        # lĩnh vực (domain) -> thủ tục cấp xã không gắn tỉnh, bản gốc trước (đại diện khi người dùng chỉ nêu tên lĩnh vực)
        self.domains: dict = {}
        for p in self.procs:
            if "Xã/Phường" in p["levels"] and not p["province"] and ";" not in p["domain"]:
                self.domains.setdefault(p["domain"], []).append(p)
        for ps in self.domains.values():
            ps.sort(key=lambda p: (not p["dv"], len(p["name"])))
        load_name_neg([p["toks"] for p in self.procs])
        _query.VOCAB = set(self.vocab)
        _query.NAME_BIGRAMS = {bg for p in self.procs for bg in p["bigrams"]}
        _query.NAME_NGRAMS = _query.NAME_BIGRAMS | {t for p in self.procs for t in zip(p["toks"], p["toks"][1:], p["toks"][2:])}   # cho query.understand giữ chữ nghiệp vụ trùng STOP

    def byid(self, pid: str):
        return self._byid.get(pid)

    def by_label(self, label: str) -> str | None:
        """Nhãn trong thẻ hỏi lại (có thể bị cắt) -> proc_id; ưu tiên bản cấp xã, không gắn tỉnh."""
        lb = re.sub(r"^thu tuc ", "", _fold(label))     # khớp cách Index bỏ 'Thủ tục' đầu tên
        if not lb:
            return None
        c = [p for p in self.procs if " ".join(p["toks"]) == lb] or             [p for p in self.procs if " ".join(p["toks"]).startswith(lb) or lb.startswith(" ".join(p["toks"]))] or             [p for p in self.procs if len(lb.split()) >= 3 and " ".join(p["toks"]).endswith(" " + lb)]   # nhãn rút gọn bỏ phần đầu chung của các bản
        c.sort(key=lambda p: (bool(p["province"]), "Xã/Phường" not in p["levels"], len(p["name"])))
        return c[0]["proc_id"] if c else None

    # ---- chấm điểm -------------------------------------------------------
    def _fix(self, term: str, prev: str | None = None, nxt: str | None = None) -> str:
        """Sai chính tả nhẹ: gần đúng 1 chữ trong kho (chỉ khi chữ lạ và đủ dài).
        Ưu tiên ứng viên tạo thành bigram hợp lệ trong CSDL với từ đứng trước hoặc sau."""
        if term in self.vocab or len(term) < 4:
            return term
        best = [v for v in self._by_len.get(len(term), []) + self._by_len.get(len(term) - 1, [])
                + self._by_len.get(len(term) + 1, []) if v[0] == term[0] and _dam1(term, v)]
        if best:
            bg_cands = [v for v in best if (prev and (prev, v) in _query.NAME_BIGRAMS) or (nxt and (v, nxt) in _query.NAME_BIGRAMS)]
            if bg_cands:
                return max(bg_cands, key=lambda v: (len(v) == len(term), self.idf.get(v, 0)))
            return max(best, key=lambda v: (len(v) == len(term), self.idf.get(v, 0)))
        m = difflib.get_close_matches(term, self._vocab_list, n=1, cutoff=0.88)
        return m[0] if m else term

    def _weight(self, t: str) -> float:
        if t in self.idf:
            return self.idf[t]
        if t in self.vocab:      # chỉ có trong tên lĩnh vực
            return 1.0
        c = self.cdf.get(t, 0)
        if c == 0:
            return self.max_idf  # lạ hoàn toàn
        return max(0.3, self.max_idf * (1 - min(1.0, math.log(1 + c) / math.log(1 + self.n))) * 0.6)

    def rank(self, q: Query, limit: int = 5) -> list[Hit]:
        if not q.terms:
            return []
        fixed = []
        for i, t in enumerate(q.terms):
            prev_t = fixed[-1] if i > 0 else None
            nxt_t = q.terms[i + 1] if i + 1 < len(q.terms) else None
            fixed.append(self._fix(t, prev_t, nxt_t))
        terms = fixed
        accs = [a if fixed[i] == t else fixed[i] for i, (t, a) in enumerate(zip(q.terms, q.accented))]
        w = [self._weight(t) for t in terms]
        total = sum(w) or 1.0
        prov_set = {_fold(x) for x in q.provinces}
        tset = set(terms)
        seen_t: set = set()
        uniq = []       # chữ lặp lại trong câu ("TNLĐ ... TNLĐ", "người dịch ... người dịch") chỉ tính MỘT lần: khớp theo tập chữ, lặp không phải bằng chứng thêm
        for t, a, wt in zip(terms, accs, w):
            if t not in seen_t:
                seen_t.add(t)
                uniq.append((t, a, wt))
        hits: list[Hit] = []
        for p in self.procs:
            m = 0.0
            mname = 0.0
            miss = 0.0
            him = hix = 0.0
            for t, a, wt in uniq:
                hi = self.idf.get(t, 0) >= HI_IDF
                if t in p["tokset"]:
                    f = 1.0 if (a == t or a in p["acc"]) else ACCENT_MISMATCH
                    if hi:
                        him, hix = (him + wt, hix) if f == 1.0 else (him, hix + wt)
                    m += wt * f
                    if t in p["ctokset"]:
                        mname += wt * f       # chữ nằm trong chú thích/liệt kê (ngoài tên lõi) góp vào cov nhưng không vào độ chính xác của tên
                    miss += wt * (1 - f)
                elif t in p["dtoks"]:
                    m += wt * DOMAIN_FACTOR
                    miss += wt * (1 - DOMAIN_FACTOR)
                else:
                    if hi:
                        hix += wt
                    # chữ có trong kho (thuộc thủ tục khác/ngữ cảnh) nhẹ hơn chữ LẠ hoàn toàn
                    miss += wt * (CONTEXT_MISS if t in self.vocab else 1.0)
            if m <= 0:
                continue
            cov = m / (m + miss)
            name_w = sum(self.idf[t] for t in p["ctoks"] if self.idf.get(t, 9) > 1.5) or 1.0
            prec = min(1.0, mname / name_w)
            adj = [(a, b) for a, b in zip(terms, terms[1:])]
            phrase = (sum(1 for bg in adj if bg in p["bigrams"]) / len(adj)) if adj else 0.0
            if prec >= 0.95 and sum(1 for t in terms if t in p["tokset"]) >= 2:
                cov = max(cov, NAME_FULL_COV)    # cả tên thủ tục nằm trọn trong câu: lời kể dài không được kéo cov xuống
            prec_eff = prec
            if len(terms) >= 2 and _is_prefix(terms, p["ctoks"]):
                prec_eff = max(prec, PREFIX_PREC + (1 - PREFIX_PREC) * prec)   # câu hỏi LÀ phần đầu tên: tên dài không bị coi là "lệch" so với bản anh em ngắn (vẫn ưu tiên tên ngắn hơn)
            score = cov * (PREC_BASE + (1 - PREC_BASE) * prec_eff) + 0.12 * phrase
            if cov >= 0.99 and sum(1 for t in terms if t in p["tokset"]) >= 3:
                score += COMPLETE_BONUS
                if len(terms) >= 4 and _is_prefix(terms, p["ctoks"]):
                    score += PREFIX_BONUS      # người dùng gõ ĐẦU tên một thủ tục dài và đủ mọi chữ: hơn bản chỉ khớp rời rạc nhiều chỗ (tên ngắn hơn chứa chữ lẻ)    # tên chứa MỌI chữ người dùng nói: hơn tên ngắn gọn hơn nhưng thiếu chữ (cắt đầu tên: "chuyển đổi nhà trẻ..." vs "giải thể nhà trẻ...")
            if q.provinces:
                if p["province"] and _fold(p["province"]) in prov_set:
                    score += 0.08
                elif p["province"]:
                    score -= 0.05
            elif p["province"]:
                score -= PROVINCE_PEN
            ev = (p['tokset'] & EVENT_TOKENS) | {a for (a, b) in EVENT_BIGRAMS if (a, b) in p['bigrams']}
            if ev and not (ev & (set(q.terms) | {a for (a, b) in zip(q.terms, q.terms[1:]) if (a, b) in EVENT_BIGRAMS})):
                score -= EVENT_PENALTY
            lead = _lead(p, tset)
            if lead:
                score -= LIFECYCLE_PENALTY
            if p["dv"]:
                score += 0.03
            extras = sum(1 for t in p['tokset'] if t not in terms and self.idf.get(t, 0) >= EXTRA_IDF)
            hits.append((score, cov, p, prec, m, sum(1 for t in terms if t in p['tokset']), extras, him, hix, mname))
        hits.sort(key=lambda x: -x[0])
        out = []
        for score, cov, p, prec, mass, nmatch, extras, him, hix, cmass in hits[:limit]:
            fl = []
            for v in VERTICAL:
                if v in p["domain"].split(";") or any(part.strip() == v for part in p["domain"].split(";")):
                    fl.append(f"vertical:{v}")
            if "Xã/Phường" not in p["levels"]:
                fl.append("province_only")
            out.append(Hit(p["proc_id"], p["name"], p["domain"], round(score, 3), round(cov, 3),
                           p["province"], p["dv"], p["head"], fl, round(prec, 3), round(mass, 2), nmatch, extras, round(him, 2), round(hix, 2), round(cmass, 2)))
        return out


def _negated(h: Hit, negs: list[list[str]], pos_terms: list[str]) -> bool:
    toks = set(_fold(h.name).split())
    for xs in negs:
        x = {t for t in xs if t not in ("co", "la")}
        if x and x <= toks and not x <= set(pos_terms):
            return True
    return False


# Cấu trúc chào hỏi/cảm ơn/tạm biệt/hỏi bot là ai-làm được gì/hỏi thăm. Có dấu hiệu này mà KHÔNG còn chữ nghiệp vụ nào (IDF tên thủ tục cao) => xã giao,
# kể cả khi kèm từ lóng ("chào ad, mình mới biết trang này, ad khỏe hông").
_GREET = re.compile(r"(?<!\w)(?:xin chao|chao(?: buoi \w+)?|hello|hi|alo|hey|hallo|cam on|thanks?|thank you|tam biet|bye(?: bye)?|hen gap lai|"
                    r"khoe (?:khong|hong|hok|ko|chua|k)|ban (?:la ai|ten (?:gi|la gi))|ten (?:gi|la gi)|(?:giup|lam) duoc (?:gi|nhung gi|viec gi)|biet lam (?:gi|nhung gi)|"
                    r"co (?:do|ai) khong|co (?:o day|mat) khong|tuyet voi|gioi qua|hay qua|tot qua)(?!\w)")
_SOCIAL = set("hoi chut xiu hong duoc trang web nay lan dau vo vao truy cap biet ten sang trua chieu toi buoi khoe tro ly bot ai ban may tao nhi nhe ne ha minh moi "
              "nhieu nhe a oi ad admin em anh chi bac co chu day do kia".split())


def _is_chitchat(q: Query, idx: Index) -> bool:
    if q.fields:
        return False
    f = f" {_fold(q.raw)} "
    ts = [t for t in re.split(r"\W+", f) if t]
    if ts and all(t in CHITCHAT or t in {"nhe", "nha", "a", "oi", "vay", "la", "gi", "khong", "co", "the", "lam", "duoc"} for t in ts)             and not any(t in idx.vocab for t in q.terms if t not in CHITCHAT):
        return True
    if not _GREET.search(f):
        return False
    rest = [t for t in _GREET.sub(" ", f).split() if t not in CHITCHAT and t not in _SOCIAL and t not in STOP]
    return not any(idx.idf.get(t, 0) >= 2.5 for t in rest)


_FOLLOW = re.compile(r"\b(chac khong|co dung khong|dung khong|ngan gon hon|ngan hon|chi tiet hon|viet lai|noi lai)\b")


def _has_proc_terms(idx: Index, q: Query) -> bool:
    return any(t in idx.vocab and t not in CHITCHAT for t in q.terms)


def _ref_options(idx: Index, turns: list[dict], shown: list[dict] | None, st: ConvState | None = None) -> list:
    """Danh sách mà "cái thứ hai" trỏ vào: ưu tiên danh sách đánh số trong câu trợ lý ngay trước, rồi tới
    `shown_procedures`, rồi tới thứ tự các thủ tục đã nói trong hội thoại (st.order, cũ -> mới; [0] là thứ nhất).
    Phần tử None = nhãn không khớp thủ tục nào."""
    prev = turns[-2] if len(turns) >= 2 and turns[-2]["role"] == "assistant" else None
    labels = options_from_text(prev["text"]) if prev else []
    if labels:
        return [idx.by_label(lb) for lb in labels]
    if shown:
        return [x["proc_id"] for x in sorted(shown, key=lambda x: x.get("ordinal", 0))]
    return list(st.order) if st else []


def _carry(st: ConvState, segs: list) -> None:
    """Cập nhật trạng thái theo kết quả của một lượt (replay hoặc đề xuất)."""
    done = [s for s in segs if s.proc_id]
    for s in done:
        st.note(s.proc_id, s.query.fields)
        st.loose = s.decision == "story"
    if not done and segs and not segs[0].oos_topic and segs[0].reason not in ("chitchat", "order_unknown") and event_hints(segs[0].text)[0]:
        st.add_story(segs[0].text)


def resolve(idx: Index, turns: list[dict], accept: float | None = None, shown: list[dict] | None = None,
            state: ConvState | dict | None = None) -> Result:
    """turns = [{"role","text"}]; lượt cuối là user.
    Trạng thái hội thoại (ConvState) lấy từ `state` (orchestrator lưu DB) hoặc dựng lại bằng cách chạy lại các lượt user trước.
    Mỗi segment mang `decision`/`why`: follow_up | new_related | return | correction | story | independent | new."""
    accept = ACCEPT_SCORE if accept is None else accept
    turns = [{**t, "text": _query.unglue_text(strip_labels(t["text"], t["role"])) if t["role"] == "user" else strip_labels(t["text"], t["role"])} for t in turns]     # nhãn lượt ("Turn 2:", "Q:", "2)") của cả lịch sử lẫn câu cuối không phải lời người dùng; chữ dính liền được tách TRƯỚC khi tách ý/xếp hạng (tách ý dùng cặp chữ liền kề)
    user_turns = [t["text"] for t in turns if t["role"] == "user"]
    if state is not None:
        st = state if isinstance(state, ConvState) else ConvState.from_dict(state)
        st = ConvState.from_dict(st.to_dict())
    else:
        st = ConvState()
        for text in user_turns[:-1]:
            _carry(st, _resolve_text(idx, text, st, accept, list(st.order)))
    before = st.to_dict()
    segs = _resolve_text(idx, user_turns[-1], st, accept, _ref_options(idx, turns, shown, st))
    ok = [s for s in segs if s.proc_id]
    chit = len(segs) == 1 and segs[0].reason == "chitchat"
    behavior = "answer" if (ok or chit) else "apologize"
    after = ConvState.from_dict(before)
    _carry(after, segs)
    ctx = {"decision": segs[0].decision if len(segs) == 1 else ",".join(s.decision for s in segs),
           "why": " | ".join(s.why for s in segs if s.why), "topic_before": before["topic"], "history": before["history"], "state_before": before}
    return Result(segs, behavior, chit, after, ctx)


# Ngưỡng quyết định (chọn theo ctx-dev; xem eval/README.md):
NAMED_PREC_CTX = 0.2      # phần khối lượng tên thủ tục được câu hỏi phủ tối thiểu để coi là "gọi tên" (khớp chữ chung 'đăng ký ... xã' phủ ~0.1)
WEAK_NAME = 0.45      # tỉ lệ khối lượng IDF chữ hiếm của câu KHÔNG nằm trong tên thủ tục đứng đầu: cao hơn => tên thủ tục mới phủ yếu
RELATED_DOMAIN = True  # thủ tục mới cùng lĩnh vực với thủ tục đang nói => "liên quan" (kế thừa mục đang hỏi khi có từ nối)


def _hit_of(sg: Segment):
    return next((h for h in sg.hits if h.proc_id == sg.proc_id), None)


def _related(idx: Index, a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    pa, pb = idx.byid(a), idx.byid(b)
    return bool(pa and pb and set(pa["domain"].split(";")) & set(pb["domain"].split(";")))


def _back_target(idx: Index, st: ConvState, q: Query, kind: str) -> str | None:
    """Dấu hiệu quay lại -> thủ tục ĐÃ NÓI: có tên (khớp chữ nghiệp vụ) thì chọn theo tên; không thì theo vị trí."""
    ts = [t for t in q.terms if t in idx.vocab]
    if ts:
        best, bs = None, 0.0
        for pid in st.history:                      # cũ -> mới: hoà điểm lấy cái gần nhất
            p = idx.byid(pid)
            sc = sum(idx._weight(t) for t in ts if p and t in p["tokset"]) / sum(idx._weight(t) for t in ts)
            if sc >= bs and sc >= 0.5:
                best, bs = pid, sc
        return best
    if kind == "first":
        return st.order[0] if st.order else None
    return st.history[-2] if len(st.history) >= 2 else None


def _is_named(sg: Segment) -> bool:
    """Đoạn đã có tên thủ tục chắc: khớp >= 2 chữ và chữ hiếm của câu phần lớn nằm trong tên."""
    h = _hit_of(sg)
    if not (sg.proc_id and h and h.nmatch >= 2 and h.prec >= NAMED_PREC_CTX):
        return False
    mass = h.hi_match + h.hi_miss
    if h.hi_match <= 0:                     # chỉ khớp chữ CHUNG ("đăng ký", "xin"): chưa gọi tên thủ tục nào
        return False
    return not (mass > 0 and h.hi_miss / mass > WEAK_NAME)


def _contextualize(idx: Index, st: ConvState, segs: list, mk: dict, negs: list) -> None:
    """Bước quyết định minh bạch: mỗi đoạn là (i) follow_up cùng thủ tục, (ii) new_related, (iii) return (quay lại thủ tục cũ),
    (iv) independent/new, (v) correction. Tín hiệu: có/không tên thủ tục mới (độ phủ chữ hiếm), từ nối/đại từ/câu cụt/điều kiện,
    field-only, chữ nghiệp vụ lạ còn dư, dấu hiệu sửa ý. Không đoán: không tín hiệu nối thì KHÔNG kế thừa."""
    strong = bool(mk.get("cond") or mk.get("tail"))
    medium = bool(mk.get("conn") or mk.get("anaph") or mk.get("need"))
    for sg in segs:
        if sg.decision:
            continue
        h = _hit_of(sg)
        mass = (h.hi_match + h.hi_miss) if h else 0.0
        weak = bool(h and mass > 0 and h.hi_miss / mass > WEAK_NAME)
        # chữ lạ HOÀN TOÀN (không có trong kho, gõ sai cũng không sửa được: "turn", "lol") chỉ hạ độ tin cậy, không phải bằng chứng của thủ tục mới:
        # trước đây _weight(chữ lạ) = max_idf nên một chữ lạ đủ để chặn kế thừa -> "độc lập" -> ngoài phạm vi dù câu có từ nối + mục hỏi.
        stray = [t for t in sg.query.terms if idx._fix(t) not in idx.vocab]
        distinct = any(idx._weight(t) >= HI_IDF for t in sg.query.terms if t not in stray)
        # tên mỏng: đang có chủ đề + câu mang tín hiệu nối + thủ tục xếp đầu không phủ chắc (khớp <2 chữ) => không coi là thủ tục mới
        # (chữ lạ còn dư chỉ chặn việc kế thừa khi thủ tục đang nói do người dùng GỌI TÊN; thủ tục suy ra từ lời kể thì nới)
        thin = bool(st.topic and (strong or medium or sg.query.fields) and not _is_named(sg) and (not distinct or st.loose))
        weak = weak or thin
        if sg.proc_id and not weak:                               # có tên thủ tục mới, đủ phủ
            pid = sg.proc_id
            if negs or mk.get("corr"):
                sg.decision, sg.why = "correction", "người dùng sửa ý: bỏ thủ tục bị phủ định/nêu lại thủ tục đúng"
                if not sg.query.fields:
                    sg.query.fields = list(st.fields) or ([] if st.topic else ["components"])     # "không phải X, ý tôi là Y": vẫn hỏi đúng mục vừa hỏi; câu đầu chỉ nêu hoàn cảnh ("không phải trường hợp X") thì hỏi hồ sơ
            elif not st.topic:
                sg.decision, sg.why = "new", "đầu hội thoại / chưa có thủ tục đang nói"
            elif pid == st.topic:
                sg.decision, sg.why = "follow_up", "nêu lại đúng thủ tục đang nói"
            elif pid in st.history:
                sg.decision, sg.why = "return", "nêu thủ tục đã nói trước đó"
                if (mk.get("conn") or mk.get("tail")) and not sg.query.fields and st.fields:
                    sg.query.fields = list(st.fields)
                    sg.why += "; kế thừa mục đang hỏi " + ",".join(st.fields)
            elif _related(idx, pid, st.topic):
                sg.decision, sg.why = "new_related", "thủ tục mới cùng lĩnh vực với thủ tục đang nói"
                if (mk.get("conn") or mk.get("tail")) and not sg.query.fields and st.fields:
                    sg.query.fields = list(st.fields)            # "thế còn kết hôn?" sau "khai tử cần gì" -> vẫn hỏi giấy tờ
                    sg.why += "; kế thừa mục đang hỏi " + ",".join(st.fields)
            else:
                sg.decision, sg.why = "independent", "thủ tục mới khác lĩnh vực, không kế thừa gì"
            continue
        can = st.topic and not sg.oos_topic and not sg.reason.startswith("flagged") and sg.reason != "chitchat"
        if can and (strong or ((medium or sg.query.fields) and (not distinct or st.loose))):
            sg.proc_id, sg.inherited, sg.reason = st.topic, True, "in_scope"
            sg.uncertain, sg.ambiguous, sg.near = bool(stray), False, []      # chữ lạ: chỉ hạ độ tin cậy
            sg.decision = "follow_up"
            sg.why = ("câu điều kiện/câu cụt \"thì sao\" không nêu thủ tục mới" if strong else
                      "từ nối/đại từ/hỏi mục, không còn chữ nghiệp vụ lạ") + (", tên thủ tục mới phủ yếu" if weak else "") + (f"; chữ lạ {stray} chỉ hạ độ tin cậy" if stray else "")
        else:
            sg.decision = "independent"
            sg.why = ("chủ đề ngoài phạm vi" if sg.oos_topic else "chữ nghiệp vụ lạ còn dư, không nối" if distinct and st.topic
                      else "không có tín hiệu nối" if st.topic else "chưa có thủ tục đang nói")


_POLARITY = {"khong", "phai", "la"}


def _contiguous(idx: Index, q: Query, h: Hit) -> bool:
    """Câu hỏi là phần ĐẦU (cụm gốc) tên lõi của `h` -> `h` là một dạng/anh em thật của cụm đó dù tên dài.
    Nguyên nhân gốc của việc bỏ sót hỏi lại: phạt `prec` (câu / độ dài cả tên) loại các anh em có tên dài ("gia hạn" ~ "Gia hạn giấy phép lao động đối với ..."),
    nên cụm gốc chung ("gia hạn", "xét tuyển", "thu hồi") chỉ còn 1-2 ứng viên và Policy trả lời luôn. Chỉ nới cho cụm ĐỨNG ĐẦU tên: cụm nằm giữa/cuối tên dài
    ("thường trú" ~ "Cấp giấy xác nhận công dân Việt Nam thường trú ở khu vực biên giới") vẫn bị NEAR_PREC loại, tránh hỏi thừa khi một thủ tục đã gọi đúng."""
    ts = [idx._fix(t) for t in q.terms]
    return len(ts) >= 1 and _is_prefix(ts, idx.byid(h.proc_id)["ctoks"])


def _near(idx: Index, q: Query, top: Hit, hits: list) -> list[str]:
    """>= 3 NHÓM thủ tục gần nhau mà câu hỏi không phân biệt được -> trả proc_id đại diện mỗi nhóm (Policy hỏi lại); ngược lại [].
    Nhóm = các thủ tục có tên lõi là mở rộng theo tiền tố của nhau (cùng family: "đăng ký khai sinh" ~ "... lưu động") hoặc chỉ khác
    nhau về phủ định/hệ từ ("người dịch là CTV" ~ "không phải là CTV"); mỗi nhóm đếm một lần.
    Ứng viên: không cờ phạm vi, không bản riêng tỉnh (trừ khi câu nêu tỉnh), điểm sát top, khối lượng chữ khớp không kém top đáng kể
    (kém nhiều = người dùng đã nêu từ phân biệt cho top)."""
    if top.prec >= NAMED_PREC or [idx._fix(t) for t in q.terms] == idx.byid(top.proc_id)["ctoks"]:
        return []      # người dùng gõ ĐÚNG nguyên tên lõi của top (kể cả khi tên khác chứa trọn tên đó: "khám bệnh, chữa bệnh BHYT" ~ "Ký hợp đồng khám bệnh, chữa bệnh BHYT") là đã gọi tên
    pool, local = [top], set()
    for h in hits:
        if h is top or h.flags or h.proc_id == top.proc_id:
            continue
        if h.score >= top.score - NEAR_GAP and h.cov >= top.cov - 0.05 and top.cmass - h.cmass < NEAR_MASS and (h.prec >= NEAR_PREC * top.prec or (_contiguous(idx, q, h) and not (top.province and h.province and not q.provinces))):
            if h.province and not q.provinces and not top.province:
                local.add(h.proc_id)      # bản riêng của tỉnh: KHÔNG là lựa chọn để hiện, nhưng là bằng chứng nhóm thủ tục này có nhiều dạng (đếm vào số nhóm)
            pool.append(h)
    if len(pool) < 3:
        return []
    own = idx.byid(top.proc_id)["tokset"]
    others = set().union(*(idx.byid(h.proc_id)["tokset"] for h in pool if h is not top))
    if any(t in own and t not in others and (idx.idf.get(t, 0) >= HI_IDF or t in LIFE_WORDS) for t in {idx._fix(t) for t in q.terms}):
        return []      # người dùng đã nêu chữ hiếm CHỈ có ở thủ tục đứng đầu ("... sang Lào"): đủ phân biệt, không hỏi lại
    ct = {h.proc_id: idx.byid(h.proc_id)["ctoks"] for h in pool}
    parent = {h.proc_id: h.proc_id for h in pool}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tset = {idx._fix(t) for t in q.terms}    # câu hỏi chỉ gồm chữ của tên chung nhóm ("hỗ trợ chi phí mai táng"): các bản khác nhau ở phần SAU tên chung (đối tượng...) => mỗi bản là một lựa chọn, không gộp
    def core_seq(t):     # bỏ chữ phủ định/hệ từ: "là CTV" ~ "không phải là CTV" chỉ là hai đáp án của MỘT câu hỏi
        return [w for w in t if w not in _POLARITY]
    for i, a in enumerate(pool):
        for b in pool[i + 1:]:
            ta, tb = ct[a.proc_id], ct[b.proc_id]
            n = min(len(ta), len(tb))
            same_fam = a.head and a.head == b.head and tset != set(a.head.split())
            if ta[:n] == tb[:n] or same_fam or core_seq(ta) == core_seq(tb):
                parent[find(a.proc_id)] = find(b.proc_id)
    reps, seen = [], set()
    for h in pool:                       # pool đã theo điểm giảm dần: đại diện nhóm = bản điểm cao nhất
        r = find(h.proc_id)
        if r not in seen:
            seen.add(r)
            reps.append(h.proc_id)
    shown = [r for r in reps if r not in local]
    return shown if len(reps) >= 3 and len(shown) >= 2 else []      # >= 3 dạng (kể cả bản riêng tỉnh), nhưng chỉ hiện các dạng không gắn tỉnh (cần >= 2)


def _merge_same(segs: list) -> list:
    """Hai đoạn cùng một thủ tục (lời kể + câu hỏi, 'giấy tờ' và 'lệ phí' tách ở dấu phẩy) là MỘT ý: gộp mục, không đếm thành task thứ hai."""
    out: list = []
    for sg in segs:
        d = next((o for o in out if o.proc_id and o.proc_id == sg.proc_id and "compare" not in (o.relation, sg.relation)), None)
        if d is None:
            out.append(sg)
            continue
        d.query.fields += [f for f in sg.query.fields if f not in d.query.fields]
        d.near = d.near if sg.near else []        # chỉ hỏi lại khi MỌI đoạn gộp đều mơ hồ (đoạn kia đã nêu đủ tên thì thôi)
    return out


_TAIL_SEG = re.compile(r"(?:thi|vay) (?:sao|the nao|ra sao)\s*$")


def _share_fields(segs: list, tail: bool = False) -> None:
    """Ý nối trong MỘT câu dùng chung mục: "A mất bao nhiêu tiền, B thì sao" -> B cũng hỏi phí; "khai sinh, khai tử, kết hôn cần giấy tờ gì" -> mục ở cuối áp cho cả danh sách."""
    if tail:
        for i, sg in enumerate(segs):
            if i and not sg.query.fields and _TAIL_SEG.search(_fold(sg.text)):
                sg.query.fields = list(segs[i - 1].query.fields)
        return
    for i in range(len(segs) - 2, -1, -1):
        if not segs[i].query.fields and segs[i].proc_id and segs[i + 1].query.fields:
            segs[i].query.fields = list(segs[i + 1].query.fields)


NARR_PREC = 0.35     # đoạn lời kể: tên thủ tục khớp yếu hơn mức này (độ chính xác theo tên lõi)
_ASK_W = {"muốn", "cần", "xin", "hỏi", "nhờ", "phải", "nên", "nếu", "làm", "muon", "can", "hoi", "nho", "phai", "nen", "neu", "lam"}   # chữ có dấu khớp đúng dấu; chữ ASCII (gõ không dấu) khớp bản không dấu: "cán bộ" không phải "cần"


_NEG_W = {"không", "khong", "ko", "chẳng", "chang", "chả", "cha", "chưa", "chua"}
_PAST_W = {"đi", "di", "đang", "dang", "từng", "tung", "đã", "da", "vừa", "vua", "mới", "moi", "bị", "bi"}   # "từng làm thanh niên xung phong": làm = nghề, không phải yêu cầu


_Q_TAIL = re.compile(r"\b(?:khong|ko|k|duoc khong|dc ko|sao|the nao|ha|nhi)\s*[?]?\s*$")


def _asks(text: str) -> bool:
    """Câu có động từ YÊU CẦU (muốn/cần/xin/hỏi/làm/nếu/trường hợp...) hoặc trợ từ nghi vấn, khác lời kể."""
    if _Q_TAIL.search(_fold(text or "")):
        return True
    ws = re.findall(r"\w+", (text or "").lower())
    for i, w in enumerate(ws):
        if w in _ASK_W:
            if i and ws[i - 1] in _NEG_W:
                continue            # "không muốn nhận nữa", "không cần": phủ định, là lời kể
            if w in ("làm", "lam") and ((i and ws[i - 1] in _PAST_W) or ws[i + 1:i + 2] in (["việc"], ["viec"], ["ăn"], ["an"], ["nghề"], ["nghe"])):
                continue
            return True
        if w in ("trường", "truong") and ws[i + 1:i + 2] in (["hợp"], ["hop"]):
            return True
    return False


def _req(sg) -> bool:
    return bool(sg.query.fields) or _asks(sg.text)


def _prec(sg) -> float:
    h = next((x for x in sg.hits if x.proc_id == sg.proc_id), None) or (sg.hits[0] if sg.hits else None)
    return h.prec if h is not None and sg.proc_id else 0.0


def _dangling(segs: list) -> bool:
    reqs = [sg for sg in segs if _req(sg)]
    return len(segs) >= 2 and len(reqs) == 1 and _prec(reqs[0]) < 0.5


_SITUATION = re.compile(r"\b(?:tung|chua|khong co|khong con|la|ly hon|nuoc ngoai|khac)\b")


_COND_START = re.compile(r"^" + COND_W + r"\b")


def _attach_orphans(segs: list, cmp) -> list:
    """Đoạn "Nếu <hoàn cảnh> thì <hỏi mục>" KHÔNG ra thủ tục nào (chữ của hoàn cảnh) mà đứng sau một đoạn đã có thủ tục: là phần điều kiện/mục hỏi của thủ tục đó, không phải ý thứ hai
    (ý thứ hai thật không mở đầu bằng 'nếu/trường hợp')."""
    if cmp or len(segs) < 2:
        return segs
    out: list = []
    for sg in segs:
        prev = next((o for o in reversed(out) if o.proc_id), None)
        if prev is not None and not sg.proc_id and _COND_START.match(sg.text.strip().lower()):
            prev.query.fields += [f for f in sg.query.fields if f not in prev.query.fields]
            cond = strip_condition(sg.text)[1] or sg.text.strip()
            prev.query.flags["condition"] = "; ".join(([prev.query.flags["condition"]] if prev.query.flags.get("condition") else []) + [cond])
            continue
        out.append(sg)
    return out


def _lose_to_cond(target, lost: list) -> None:
    """Lời kể bị bỏ khỏi danh sách ý nhưng nêu HOÀN CẢNH ("tôi từng ly hôn", "con sinh ở nhà") -> điều kiện của câu hỏi: Policy/Answerer đối chiếu condition_index."""
    texts = [sg.text.strip() for sg in lost if len(sg.text.split()) >= 3 and _SITUATION.search(_fold(sg.text))]
    if texts:
        target.query.flags["condition"] = "; ".join(([target.query.flags["condition"]] if target.query.flags.get("condition") else []) + texts)


def _drop_narrative(segs: list) -> list:
    """Lời kể hoàn cảnh ("tôi là cán bộ", "con tôi bị khuyết tật", "gia đình thuộc diện hộ nghèo") KHÔNG phải ý thứ hai: đoạn không có mục hỏi, không có từ
    xin/muốn/cần/làm/nếu và không gọi tên thủ tục rõ (hoặc không ra thủ tục) bị bỏ khi còn đoạn hỏi thật.
    Tín hiệu tách ý thứ hai là ý được NÊU RIÊNG (mục hỏi hoặc động từ yêu cầu), không phải việc có chữ khớp một thủ tục láng giềng.
    ponytail: chỉ bỏ, không ghép chữ của lời kể vào đoạn hỏi; lời kể chứa tên thủ tục duy nhất ('con tôi bị khuyết tật, muốn xin giấy xác nhận') có thể chọn nhầm."""
    if len(segs) < 2 or all(_req(sg) for sg in segs) or not any(_req(sg) for sg in segs):
        return segs
    best = max(_prec(sg) for sg in segs if _req(sg))
    keep = [sg for sg in segs if _req(sg) or _prec(sg) >= max(NARR_PREC, 0.5 * best)]
    first = next((sg for sg in keep if _req(sg)), None)
    if first is not None:
        _lose_to_cond(first, [sg for sg in segs if sg not in keep])
    return keep


_STEPS_WORD = re.compile(r"\b(?:cac buoc|buoc|trinh tu|quy trinh|cach thuc|cach lam|lam sao|lam the nao|thu tuc)\b")


def _cond_steps(main: str, fields: list) -> list:
    """"nếu X thì tôi cần làm gì" (câu chính chỉ có 'làm gì', không nêu mục): giấy tờ/hồ sơ + điều kiện X, không phải các bước."""
    if fields == ["steps"] and re.search(r"\blam gi\b", _fold(main)) and not _STEPS_WORD.search(_fold(main)):
        return ["components"]
    return fields


def _cond_fields(idx: Index, frag: str, fq: Query, allow: bool) -> None:
    """Câu điều kiện "nếu/trường hợp X thì Y": mục được hỏi nằm ở Y; cụm trong X ("nộp trực tuyến", "qua bưu chính") là hoàn cảnh, không phải mục.
    Không có mục nào ở Y thì hỏi hồ sơ/giấy tờ theo trường hợp (kèm đoạn điều kiện ở Policy/Answerer)."""
    if not allow:
        return
    main, cond = strip_condition(frag)
    if not cond or not (re.search(r"\b" + COND_W + r"\b", frag.lower()) or not understand(idx.conn, cond, idx.syn).fields):
        return      # "A thì B" không có 'nếu': chỉ coi A là hoàn cảnh khi A không chứa cụm hỏi mục ("đăng ký thường trú bao lâu thì có kết quả" không phải câu điều kiện)
    mq = understand(idx.conn, main, idx.syn)
    if not re.search(r"\b" + COND_W + r"\b", frag.lower()) and len(mq.terms) < 2:
        return      # "nhà em có người vừa mất thì phải làm thủ tục gì": vế trước là SỰ KIỆN dẫn tới thủ tục, vế sau không nêu thủ tục -> không phải câu điều kiện
    mf = mq.fields
    if re.search(r"\b" + COND_W + r"\b", frag.lower()):
        mf = _cond_steps(main, mf)
    if re.search(r"\b" + COND_W + r"\b", frag.lower()):
        fq.flags["condition"] = cond          # chỉ điều kiện nêu rõ ('nếu/trường hợp') mới thành điều kiện để đối chiếu; "mẹ em mất thì ..." là sự kiện, không ghi chú
    if len(mq.terms) >= 2:      # câu chính tự gọi tên thủ tục: xếp hạng theo câu chính, chữ của hoàn cảnh ("ở nhờ nhà người quen") không lẫn vào tên thủ tục
        h = idx.rank(mq, limit=1)
        if h and h[0].prec >= 0.5 and h[0].hi_match > 0:
            fq.terms, fq.accented = list(mq.terms), list(mq.accented)
    fq.fields = (["components"] if set(mf) <= {"meta"} else []) + list(mf)      # chỉ hỏi nguồn/căn cứ thì vẫn cần phần nội dung theo trường hợp (hồ sơ)


_CLAUSE = re.compile(r"\s+(?:nhưng|nhung|mà|ma|và|va|rồi|roi|tuy|nên|nen|còn|con)\s+|\s*[,;]\s*")


def _cond_head(idx: Index, main: str):
    """Câu "nếu <việc chính, rồi hoàn cảnh phụ> thì <hỏi mục không nêu thủ tục>" ("nếu tôi đăng ký khai tử cho người đã chết nhưng người đó có hộ khẩu ... và được tổ chức tang lễ
    ở nơi khác thì tôi cần làm gì"): thủ tục là việc nêu ĐẦU TIÊN trong vế điều kiện; phần sau ranh giới mệnh đề (nhưng/mà/và/dấu phẩy) là hoàn cảnh của nó. Trước đây cả câu bị tách ở
    'và' thành hai ý và mảnh hoàn cảnh ('tổ chức tang lễ') mượn vài chữ chung của thủ tục khác ('thông báo tổ chức lễ hội') thành task thứ hai.
    -> (đầu = phần nêu thủ tục, hoàn cảnh (đoạn sau ranh giới, hoặc cả vế điều kiện), mục) hoặc None khi câu không thuộc dạng này (thủ tục nêu ở vế sau, hay đầu vế không gọi tên được).
    ponytail: ranh giới mệnh đề bằng từ nối cố định; chưa phân tích cú pháp."""
    if not re.search(r"\b" + COND_W + r"\b", main.lower()):
        return None
    m = re.match(r"^(.*?)\b" + COND_W + r"\s+(.+)\s+(?:thì|thi)\s+(.+)$", main.lower(), re.S)      # 'thì' CUỐI CÙNG: dấu phẩy trong vế điều kiện ("..., ông mất tại bệnh viện, ...") không kết thúc điều kiện
    if not m or understand(idx.conn, m.group(3), idx.syn).terms:
        return None
    if len(understand(idx.conn, m.group(1), idx.syn).terms) >= 2:
        return None       # thủ tục đã nêu TRƯỚC 'nếu' ("đăng ký giám hộ nếu ...", "tôi muốn tách hộ. Nếu ..."): vế điều kiện chỉ là hoàn cảnh, đường cũ lo
    cond, m2 = m.group(2).strip(), m.group(3).strip()
    parts = _CLAUSE.split(cond, maxsplit=1)
    head = parts[0].strip()
    hq = understand(idx.conn, head, idx.syn)
    if len(hq.terms) < 2:
        return None
    h = idx.rank(hq, limit=1)
    if not h or (h[0].prec < 0.5 and h[0].cov < 0.9) or h[0].hi_match <= 0:      # đầu gọi tên chắc: phủ tên >= 50% HOẶC mọi chữ của đầu nằm trong tên (tên dài có chú thích)
        return None
    rest = cond[len(parts[0]):].strip(" ,;") if len(parts) > 1 else ""
    rest = re.sub(r"^(?:nhưng|nhung|mà|ma|và|va|rồi|roi|tuy|nên|nen|còn|con)\s+", "", rest)
    mq = understand(idx.conn, m2, idx.syn)
    return head, rest or cond, (_cond_steps(m2, mq.fields) if mq.fields else ["components"])


DOMAIN_MIN = 5       # lĩnh vực có >= số thủ tục cấp xã này mới coi là "nhóm chung quá rộng"


def _phrase(idx: Index, q: Query, top: Hit) -> float:
    """Tỉ lệ cặp chữ LIỀN KỀ của câu hỏi cũng liền kề trong tên thủ tục (câu gõ đầu/giữa tên ~ 1.0; chữ rời rạc lấy từ nhiều chỗ của tên dài ~ thấp)."""
    ts = [idx._fix(t) for t in q.terms]
    adj = list(zip(ts, ts[1:]))
    bg = idx.byid(top.proc_id)["bigrams"]
    return sum(1 for b in adj if b in bg) / len(adj) if adj else 1.0


def _domain_near(idx: Index, q: Query, top: Hit) -> list[str]:
    """Câu CHỈ nêu tên lĩnh vực ("hộ tịch", "đất đai", "cư trú") mà không phải tên một thủ tục nào: nhóm chung quá rộng -> trả đại diện (mỗi họ một bản) để hỏi lại.
    Điều kiện: các chữ của câu (bỏ 've') là MỘT ĐOẠN LIỀN của tên lĩnh vực; không thủ tục nào có tên lõi gồm đúng các chữ đó.
    ("thẻ căn cước", "chứng thực bản sao" có chữ ngoài tên lĩnh vực nên không phải câu chung.)"""
    ts = [idx._fix(t) for t in q.terms if t != "ve"]
    if not ts:
        return []
    n = len(ts)
    for dom, ps in idx.domains.items():
        dt = _fold(dom).split()
        if len(ps) >= DOMAIN_MIN and any(dt[i:i + n] == ts for i in range(len(dt) - n + 1)):
            if any(p["ctoks"] == ts for p in idx.procs):
                return []         # trùng đúng tên một thủ tục ("tách hộ"): không phải câu chung
            reps, heads = [], set()
            for p in ps:
                if p["head"] not in heads:
                    heads.add(p["head"])
                    reps.append(p["proc_id"])
                if len(reps) == 4:
                    break
            return reps if len(reps) >= 3 else []
    return []


def _resolve_text(idx: Index, text: str, st: ConvState, accept: float, options: list | None = None, events: bool = True, one: bool = False) -> list[Segment]:
    if idx.syn is None:
        idx.syn = {r[0]: r[1] for r in idx.conn.execute("SELECT raw_term, canonical_keyword FROM synonyms")}
    whole = understand(idx.conn, text, idx.syn)
    o = ordinal(text)
    if o and pure_reference(o[1], idx.vocab, _ALL_CUES):      # "cái thứ hai", "số 2, phí bao nhiêu?"
        i = pick(o[0], len(options or []))
        pid = options[i] if i is not None else None
        # ponytail: không có danh sách / ngoài khoảng -> không đoán, trả no_procedure (xin lỗi/hỏi rõ)
        return [Segment(text, whole, proc_id=pid, inherited=True, reason="in_scope" if pid else "order_unknown",
                        decision="return" if pid else "independent", why="chỉ thứ tự trong danh sách đã nói/đã hiện")]
    if _is_chitchat(whole, idx):
        return [Segment(text, whole, reason="chitchat", decision="independent", why="xã giao")]
    main, negs = extract_negation(text, idx.vocab)           # "không phải X": bỏ X khỏi truy vấn, loại thủ tục chứa X
    if negs and not understand(idx.conn, main, idx.syn).terms:
        main, negs = text, []
    main, mk = markers(main)                                  # tách chữ diễn ngôn (cái đó, quay lại, ý tôi là...) khỏi chữ nghiệp vụ
    if negs:
        mk["corr"] = 1
    whole = understand(idx.conn, main, idx.syn)
    if mk.get("back") and st.history:                         # (iii) quay lại thủ tục cũ
        pid = _back_target(idx, st, whole, mk["back"])
        if pid:
            return [Segment(text, whole, proc_id=pid, inherited=True, reason="in_scope", decision="return",
                            why=f"dấu hiệu quay lại ({mk['back']}) -> thủ tục đã nói")]
    if st.topic and (mk.get("cond") or mk.get("tail")):       # (i) hỏi tiếp bằng điều kiện: "còn nếu bé sinh ở nhà thì sao"
        m2, cond = strip_condition(main)
        mq = understand(idx.conn, m2, idx.syn)
        if cond and not mq.terms:
            mq.flags["condition"] = cond
            mq.fields = _cond_steps(m2, mq.fields) or list(st.fields) or ["components"]     # "còn nếu ... thì sao": hỏi tiếp mục đang nói, chưa có thì hỏi hồ sơ/giấy tờ theo trường hợp
            return [Segment(text, mq, proc_id=st.topic, inherited=True, reason="in_scope", decision="follow_up",
                            why="câu điều kiện, phần chính không nêu thủ tục mới")]
    if mk.get("amount") and st.topic and not whole.terms:      # "thế bao nhiêu": câu cụt hỏi tiền về thủ tục đang nói
        whole.fields = ["fees"]
        return [Segment(text, whole, proc_id=st.topic, inherited=True, reason="in_scope", decision="follow_up", why="câu cụt hỏi \"bao nhiêu\" -> lệ phí của thủ tục đang nói")]
    if mk.get("meta") and st.topic and not whole.terms:
        whole.fields = whole.fields or list(st.fields)       # "ngắn gọn hơn", "chắc không?": cùng mục vừa hỏi
        return [Segment(text, whole, proc_id=st.topic, inherited=True, reason="in_scope", decision="follow_up", why="hỏi lại/diễn đạt lại câu trước",
                        evidence="legal_basis" if mk["meta"] == "verify" else "none")]
    parts, qs = [], []
    cmp = split_compare(main)
    ch = None if (cmp or one) else _cond_head(idx, main)
    for frag in (cmp or ([main] if one else ([ch[0]] if ch else split_segments(main)))):
        fq = understand(idx.conn, frag, idx.syn)
        _cond_fields(idx, frag, fq, cmp is None)
        if ch:                                   # "nếu <việc chính + hoàn cảnh> thì cần làm gì": MỘT ý; hoàn cảnh là điều kiện, mục mặc định = hồ sơ/giấy tờ
            fq.flags["condition"], fq.fields = ch[1], list(ch[2])
        if parts and not cmp and len(fq.terms) < 2 and not fq.fields:   # mảnh quá ngắn/ngữ cảnh: gộp vào mảnh trước
            parts[-1] += " " + frag
            qs[-1] = understand(idx.conn, parts[-1], idx.syn)
            _cond_fields(idx, parts[-1], qs[-1], True)
        else:
            parts.append(frag)
            qs.append(fq)

    # đoạn không có thủ tục (chỉ field) -> gộp field vào đoạn kề có thủ tục; ví dụ "giấy tờ và lệ phí khai sinh"
    segs: list[Segment] = []
    carry_fields: list[str] = []
    for i, (s, q) in enumerate(zip(parts, qs)):
        if not q.terms:
            carry_fields += [f for f in q.fields if f not in carry_fields]
            continue
        if carry_fields:
            q.fields = carry_fields + [f for f in q.fields if f not in carry_fields]
            carry_fields = []
        segs.append(Segment(s, q))
    if not segs:   # toàn field / chỉ chữ diễn ngôn: hỏi tiếp về thủ tục đang nói
        seg = Segment(text, whole, reason="field_only")
        if st.topic:
            seg.proc_id, seg.inherited, seg.reason = st.topic, True, "in_scope"
            seg.decision, seg.why = "follow_up", "câu cụt/chỉ hỏi mục, không nêu thủ tục"
        else:
            seg.decision, seg.why = "independent", "câu cụt nhưng chưa có thủ tục đang nói"
        return [seg]
    if carry_fields:
        for f in carry_fields:
            if f not in segs[-1].query.fields:
                segs[-1].query.fields.append(f)
    # đoạn cuối chỉ có tên thủ tục ngắn không rõ: cho phép kế thừa field của đoạn trước (hiếm; bỏ)
    for sg in segs:
        sg.hits = idx.rank(sg.query, limit=15)
        if negs:
            keep = [h for h in sg.hits if not _negated(h, negs, sg.query.terms)]
            sg.hits = keep or sg.hits
        top = sg.hits[0] if sg.hits else None
        fq = _fold(sg.text)
        tm = OOS_TOPICS.search(fq)
        # chủ đề trong danh sách chặn nhưng CHÍNH TÊN thủ tục top có cụm đó ("khám bệnh, chữa bệnh BHYT") => thủ tục có thật trong kho
        topic_out = bool(tm and not (top and tm.group(1) in _fold(top.name))) or bool(_PASSPORT.search(fq) and not _PASSPORT_OK.search(fq))
        sg.oos_topic = topic_out
        if top and top.flags:    # ưu tiên bản không bị cờ nếu điểm sát nhau
            alt = next((h for h in sg.hits if not h.flags and h.score >= top.score - 0.08), None)
            top = alt or top
        if top and top.extras >= 10:
            top_toks = set(_fold(top.name).split())
            qterms = sg.query.terms
            top_matched = {t for t in qterms if t in top_toks}
            for h in sg.hits[1:]:
                if h.score >= top.score - 0.04 and h.prec >= 2.0 * top.prec and h.extras <= 4 and not h.flags:
                    alt_toks = set(_fold(h.name).split())
                    alt_matched = {t for t in qterms if t in alt_toks}
                    subst_miss = [t for t in top_matched if t not in alt_matched and t not in _CIRCUMSTANCE and idx.idf.get(t, 0) >= 3.0]
                    if not subst_miss:
                        sg.hits[0], sg.hits[sg.hits.index(h)] = h, top
                        top = h
                        break
        if not top:
            sg.reason = "no_match"
        elif topic_out or (top.hi_match == 0 and top.hi_miss > 0 and top.prec < NAMED_PREC_CTX * 2.5):
            # cổng chữ-đặc-trưng: KHÔNG chữ hiếm nào của câu hỏi nằm trong tên thủ tục => khớp tình cờ bằng chữ chung.
            # ponytail: chỉ chặn khi 0 chữ hiếm khớp (chữ hiếm thừa như 'nộp','tốn' làm so tỉ lệ bị sai); chủ đề tình cờ vẫn dựa OOS_TOPICS
            sg.reason = "out_of_scope"
        elif top.score < accept or top.cov < ACCEPT_COV:
            sg.reason = "out_of_scope"
        elif (top.prec < WEAK_PREC and top.hi_miss > 0) or (top.hi_match == 0 and top.cov < GENERIC_COV) or (top.prec < WEAK_PREC2 and top.cov < WEAK_COV2 and _phrase(idx, sg.query, top) < 0.5):
            # bằng chứng yếu: (a) câu chỉ phủ một mẩu rất nhỏ của tên dài VÀ còn chữ đặc trưng không khớp; (b) chỉ khớp chữ chung ("đăng ký") mà còn chữ lạ ("lớp 1")
            sg.reason = "out_of_scope"
        elif any(f.startswith("vertical") or f == "province_only" for f in top.flags):
            sg.reason = "flagged:" + ",".join(top.flags)
        else:
            sg.proc_id, sg.reason = top.proc_id, "in_scope"
            _alt = choose_variant(idx, sg, top.proc_id, text)      # đổi sang biến thể anh em cùng họ khi câu hỏi nói ra trục khác biệt (xem variants.py)
            if _alt:
                sg.proc_id = _alt
            sg.uncertain = top.score < UNCERTAIN_SCORE or top.cov < UNCERTAIN_COV or top.extras >= UNCERTAIN_EXTRAS
            sg.ambiguous = any(h.head != top.head and h.score >= top.score - AMBIG_GAP for h in sg.hits[1:])
            sg.near = _near(idx, sg.query, top, sg.hits) or _domain_near(idx, sg.query, top)
    if len(segs) > 1 and not cmp:
        # mảnh sau dấu phẩy/"và" ngắn mà khớp yếu ("có kết quả", "bằng hình thức nào") là phần đệm của ý trước, không phải thủ tục mới
        def _weak(sg):
            top = sg.hits[0] if sg.hits else None
            return len(sg.query.terms) <= 3 and (top is None or (top.score < RESIDUAL_SCORE and top.prec < 0.5)
                                                 or not any(idx._weight(t) >= HI_IDF for t in sg.query.terms))      # chỉ toàn chữ chung ("giải quyết", "thực hiện"): phần đệm của cụm hỏi mục, không phải thủ tục
        # mảnh ĐẦU yếu ("nhà em ở phường này, ...") là lời dẫn của người kể, không phải thủ tục: bỏ nếu phía sau còn mảnh mạnh
        while len(segs) > 1 and _weak(segs[0]) and not all(_weak(x) for x in segs[1:]):
            segs[1].query.fields = segs[0].query.fields + [f for f in segs[1].query.fields if f not in segs[0].query.fields]
            _lose_to_cond(segs[1], [segs[0]])
            segs = segs[1:]
        def _borrowed(sg):
            # mảnh sau chỉ MƯỢN vài chữ chung của một thủ tục khác: khớp <= 3 chữ, tên thủ tục được phủ < 50% và phần lớn chữ HIẾM của mảnh không nằm trong tên đó
            # ("tổ chức tang lễ ở nơi khác" ~ "thông báo tổ chức lễ hội": trùng 'tổ chức', 'lễ'; 'tang' không có). Mảnh như vậy là hoàn cảnh/phần đệm của ý trước, không phải task thứ hai.
            top = sg.hits[0] if sg.hits else None
            mass = (top.hi_match + top.hi_miss) if top else 0.0
            return bool(top and mass > 0 and top.nmatch <= 3 and top.prec < 0.5 and top.hi_miss / mass > WEAK_NAME)
        keep = [segs[0]]
        for sg in segs[1:]:
            if _weak(sg) or _borrowed(sg):
                keep[-1].query.fields += [f for f in sg.query.fields if f not in keep[-1].query.fields and not (f == "explanation" and _borrowed(sg))]      # 'là gì' của mảnh mượn chữ không phải mục hỏi
            else:
                keep.append(sg)
        segs = keep
    segs = _attach_orphans(segs, cmp)
    all_segs = segs
    if not cmp:
        _share_fields(segs, tail=True)
        if not one and _dangling(segs):       # một câu hỏi duy nhất nhưng KHÔNG nêu tên thủ tục ("..., muốn xin giấy xác nhận"): tên nằm ở lời kể -> xếp hạng cả câu như một ý
            alt = _resolve_text(idx, main, st, accept, options, False, one=True)
            req = next(sg for sg in segs if _req(sg))
            under = not any(idx._weight(t) >= HI_IDF and t not in LIFE_WORDS for t in req.query.terms)      # câu hỏi riêng chỉ có động từ vòng đời ("xin cấp lại"): không gọi tên thủ tục nào
            if alt and alt[0].proc_id and (under or _prec(alt[0]) > _prec(req) + 0.05):      # ghép lời kể khi câu hỏi riêng không đủ tên, hoặc tên thủ tục khớp tốt hơn
                return alt
        all_segs, segs = segs, _drop_narrative(segs)
        _share_fields(segs)
    if cmp and len(segs) == 2:
        shared = list(dict.fromkeys(f for sg in segs for f in sg.query.fields)) or ["explanation"]    # so sánh: mục nêu ở một vế áp cho cả hai; không nêu thì lấy mô tả
        for sg in segs:
            sg.relation, sg.near, sg.query.fields = "compare", [], list(shared)      # hai vế đã chọn rõ, không hỏi lại
    merged = " ".join(st.story + [text])                  # (e) lời kể ở lượt trước (nếu có) + câu hiện tại
    hint, rest = event_hints(merged)
    # câu nói về việc KHÁC có chữ 'đám cưới' ("xin giấy phép tổ chức đám cưới ngoài trời"): còn chữ nghiệp vụ lạ ngoài sự kiện => không đoán
    odd = sum(idx._weight(t) >= HI_IDF for t in understand(idx.conn, rest, idx.syn).terms if len(t) >= 4 and t not in ("phuong",) and t not in _fold(hint).split()) >= 3   # ponytail: đếm >=3 chữ hiếm lạ; đủ cho ca đo được, chưa phải mô hình
    if events and hint and not odd and not any(_is_named(sg) and _hit_of(sg).prec >= 0.3 for sg in all_segs) and not any(sg.oos_topic for sg in segs):
        alt = _resolve_text(idx, hint + " " + merged, ConvState(), accept, events=False, one=True)   # sự kiện đời sống ("bé mới sinh") -> tên thủ tục thường gặp
        if any(s.proc_id for s in alt):
            for s in alt:
                s.decision, s.why = "story", "lời kể sự kiện đời sống (" + hint + ") ghép với câu hỏi -> thủ tục"
            return _merge_same(alt)
    _contextualize(idx, st, segs, mk, negs)
    segs = _merge_same(segs)
    for sg in segs:
        if sg.query.flags.get("condition") and not sg.query.fields:
            sg.query.fields = ["components"]      # nêu hoàn cảnh mà không hỏi mục nào: hồ sơ/giấy tờ theo trường hợp đó
    return segs

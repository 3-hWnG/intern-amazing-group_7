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
from dataclasses import dataclass, field

from system3.data.search import _fold

from . import query as _query
from .query import Query, understand, split_segments, strip_condition, FIELD_CUES, STOP
from .refs import ordinal, pure_reference, pick, options_from_text, extract_negation, split_compare
from .context import ConvState, markers, event_hints

ACCENT_MISMATCH = 0.35     # chữ có dấu của người dùng không khớp dấu trong tên
PREC_BASE = 0.7          # phần điểm không phụ thuộc độ ngắn gọn của tên (biến thể dài bị phạt)
CONTEXT_MISS = 0.5         # trọng số phạt chữ có trong kho nhưng không nằm trong thủ tục này
DOMAIN_FACTOR = 0.4        # khớp ở lĩnh vực thay vì tên
ACCEPT_SCORE = 0.55        # ngưỡng nhận ứng viên (chỉnh theo eval nửa DEV)
ACCEPT_COV = 0.5
COMPLETE_BONUS = 0.06
UNCERTAIN_SCORE = 0.85     # dưới mức này Planner nên cho LLM xác nhận ứng viên
UNCERTAIN_COV = 0.9
AMBIG_GAP = 0.06
EXTRA_IDF = 3.0          # chữ có IDF >= mức này coi là 'hiếm'
UNCERTAIN_EXTRAS = 3
# Chữ 'sự kiện' đổi nghĩa thủ tục (mất, hủy, thu hồi…): tên có mà câu hỏi không có => phạt (đo: 'làm hộ chiếu' ≠ 'trình báo MẤT hộ chiếu').
EVENT_TOKENS = {'mat', 'hong', 'huy', 'xoa'}
EVENT_BIGRAMS = {('thu', 'hoi'), ('cham', 'dut'), ('tam', 'dung'), ('tam', 'ngung'), ('dung', 'thuc'), ('dinh', 'chinh')}
EVENT_PENALTY = 0.35
VERTICAL = ("Thuế", "Hải quan")
CHITCHAT = set("chao xin hello hi alo cam on ban ten ai khoe ok oke vang da tam biet bye thanks thank you tro ly "
               "ad admin bot nhieu hom nay hoi vay thoi nha nhe nhen oi a ban tot qua tuyet gioi hay hen gap lai".split())
_ALL_CUES = [c for cs in FIELD_CUES.values() for c in cs]
# Chủ đề NGOÀI hệ thống (thủ tục hành chính cấp xã): chặn dù có chữ trùng tình cờ với tên thủ tục. Chữ đã bỏ dấu.
# ponytail: danh sách tay, bổ sung khi log thật gặp thêm chủ đề; không thay cho cổng chữ-đặc-trưng bên dưới.
OOS_TOPICS = re.compile(
    r"(?<!\w)(doi tuyen|bong da|bong chuyen|the thao|world cup|v league|cau thu|huan luyen vien|tran dau|"
    r"ca si|ca sy|bai hat|am nhac|phim anh|dien vien|karaoke|concert|truyen hinh thuc te|"
    r"toa an|khoi kien|ban an|luat su|(?:nop don|kien) .{0,12}(?<!\w)toa(?!\w)|(?<!\w)toa (?:nao|so tham|phuc tham)|"
    r"nhan hieu|so huu tri tue|ban quyen|sang che|kieu dang cong nghiep|thuong hieu|"
    r"thi (?:lay )?(?:bang|giay phep) lai|hoc lai xe|thi lai xe|"
    r"uong thuoc|chua benh|trieu chung|ke don thuoc|dau (?:dau|bung|rang|lung)|"
    r"visa|nhap quoc tich|nhap tich|thoi quoc tich|"
    r"diem thi|thi dai hoc|thi tot nghiep|tieng anh|ngoai ngu|dich (?:giup|cau|sang)|gia vang|gia xang|thoi tiet|chung khoan|bitcoin|tien ao|co phieu|"
    r"nau (?:an|pho|com)|cong thuc nau|du lich|dat (?:ve|phong)|ve may bay|khach san)(?!\w)")
_PASSPORT = re.compile(r"(?<!\w)ho chieu(?!\w)")
_PASSPORT_OK = re.compile(r"(?<!\w)(mat|trinh bao|bi mat|that lac)(?!\w)")
NAME_FULL_COV = 0.6        # sàn cov khi câu hỏi chứa đủ chữ đặc trưng của tên (câu kể dài: 'công ty em ... gia hạn tạm trú ...')
RESIDUAL_SCORE = 0.9       # mảnh phụ (<=3 chữ) khớp yếu hơn mức này bị coi là phần đệm của ý trước
NEAR_MASS = 2.0            # top khớp nhiều chữ hơn ứng viên khác >= mức này => người dùng ĐÃ nêu từ phân biệt, không hỏi lại
HI_IDF = 3.0               # chữ 'đặc trưng' của kho tên thủ tục (đo: chieu 6.3, tuyen 4.8, uong 6.8; ho/dang/ky < 3)
_PREFIX_RE = re.compile(r"^(?:\([^)]{2,30}\)\s*|[^-–]{2,40}?\s[-–]\s)")


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
        for r in rows:
            name = r["name"]
            core = _PREFIX_RE.sub("", name, count=1) if r["province"] else name
            core = re.sub(r"^th[ủu] t[ụu]c\s+", "", core, flags=re.I)   # 'Thủ tục' mở đầu không phải chữ phân biệt: không phạt tên có/không có nó
            toks = _fold(core).split()
            acc = set(re.findall(r"\w+", core.lower()))
            dtoks = set(_fold(r["domain"]).split())
            p = dict(proc_id=r["proc_id"], name=name, domain=r["domain"], province=r["province"],
                     levels=r["agency_levels"] or "", dv=bool(r["dv"]), head=r["head"],
                     toks=toks, tokset=set(toks), acc=acc, dtoks=dtoks,
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
        _query.NAME_BIGRAMS = {bg for p in self.procs for bg in p["bigrams"]}
        _query.NAME_NGRAMS = _query.NAME_BIGRAMS | {t for p in self.procs for t in zip(p["toks"], p["toks"][1:], p["toks"][2:])}   # cho query.understand giữ chữ nghiệp vụ trùng STOP

    def byid(self, pid: str):
        return self._byid.get(pid)

    def by_label(self, label: str) -> str | None:
        """Nhãn trong thẻ hỏi lại (có thể bị cắt) -> proc_id; ưu tiên bản cấp xã, không gắn tỉnh."""
        lb = re.sub(r"^thu tuc ", "", _fold(label))     # khớp cách Index bỏ 'Thủ tục' đầu tên
        if not lb:
            return None
        c = [p for p in self.procs if " ".join(p["toks"]) == lb] or             [p for p in self.procs if " ".join(p["toks"]).startswith(lb) or lb.startswith(" ".join(p["toks"]))]
        c.sort(key=lambda p: (bool(p["province"]), "Xã/Phường" not in p["levels"], len(p["name"])))
        return c[0]["proc_id"] if c else None

    # ---- chấm điểm -------------------------------------------------------
    def _fix(self, term: str) -> str:
        """Sai chính tả nhẹ: gần đúng 1 chữ trong kho (chỉ khi chữ lạ và đủ dài)."""
        if term in self.vocab or len(term) < 4:
            return term
        best = [v for v in self._by_len.get(len(term), []) + self._by_len.get(len(term) - 1, [])
                + self._by_len.get(len(term) + 1, []) if v[0] == term[0] and _dam1(term, v)]
        if best:
            return max(best, key=lambda v: self.idf.get(v, 0))
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
        terms = [self._fix(t) for t in q.terms]
        accs = [a if self._fix(t) == t else self._fix(t) for t, a in zip(q.terms, q.accented)]
        w = [self._weight(t) for t in terms]
        total = sum(w) or 1.0
        prov_set = {_fold(x) for x in q.provinces}
        hits: list[Hit] = []
        for p in self.procs:
            m = 0.0
            mname = 0.0
            miss = 0.0
            him = hix = 0.0
            for t, a, wt in zip(terms, accs, w):
                hi = self.idf.get(t, 0) >= HI_IDF
                if t in p["tokset"]:
                    f = 1.0 if (a == t or a in p["acc"]) else ACCENT_MISMATCH
                    if hi:
                        him, hix = (him + wt, hix) if f == 1.0 else (him, hix + wt)
                    m += wt * f
                    mname += wt * f
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
            name_w = sum(self.idf[t] for t in p["toks"] if self.idf.get(t, 9) > 1.5) or 1.0
            prec = min(1.0, mname / name_w)
            adj = [(a, b) for a, b in zip(terms, terms[1:])]
            phrase = (sum(1 for bg in adj if bg in p["bigrams"]) / len(adj)) if adj else 0.0
            if prec >= 0.95 and sum(1 for t in terms if t in p["tokset"]) >= 2:
                cov = max(cov, NAME_FULL_COV)    # cả tên thủ tục nằm trọn trong câu: lời kể dài không được kéo cov xuống
            score = cov * (PREC_BASE + (1 - PREC_BASE) * prec) + 0.12 * phrase
            if cov >= 0.99 and sum(1 for t in terms if t in p["tokset"]) >= 3:
                score += COMPLETE_BONUS    # tên chứa MỌI chữ người dùng nói: hơn tên ngắn gọn hơn nhưng thiếu chữ (cắt đầu tên: "chuyển đổi nhà trẻ..." vs "giải thể nhà trẻ...")
            if q.provinces:
                if p["province"] and _fold(p["province"]) in prov_set:
                    score += 0.08
                elif p["province"]:
                    score -= 0.05
            elif p["province"]:
                score -= 0.03
            ev = (p['tokset'] & EVENT_TOKENS) | {a for (a, b) in EVENT_BIGRAMS if (a, b) in p['bigrams']}
            if ev and not (ev & (set(q.terms) | {a for (a, b) in zip(q.terms, q.terms[1:]) if (a, b) in EVENT_BIGRAMS})):
                score -= EVENT_PENALTY
            if p["dv"]:
                score += 0.03
            extras = sum(1 for t in p['tokset'] if t not in terms and self.idf.get(t, 0) >= EXTRA_IDF)
            hits.append((score, cov, p, prec, m, sum(1 for t in terms if t in p['tokset']), extras, him, hix))
        hits.sort(key=lambda x: -x[0])
        out = []
        for score, cov, p, prec, mass, nmatch, extras, him, hix in hits[:limit]:
            fl = []
            for v in VERTICAL:
                if v in p["domain"].split(";") or any(part.strip() == v for part in p["domain"].split(";")):
                    fl.append(f"vertical:{v}")
            if "Xã/Phường" not in p["levels"]:
                fl.append("province_only")
            out.append(Hit(p["proc_id"], p["name"], p["domain"], round(score, 3), round(cov, 3),
                           p["province"], p["dv"], p["head"], fl, round(prec, 3), round(mass, 2), nmatch, extras, round(him, 2), round(hix, 2)))
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
NAMED_PREC = 0.2      # phần khối lượng tên thủ tục được câu hỏi phủ tối thiểu để coi là "gọi tên" (khớp chữ chung 'đăng ký ... xã' phủ ~0.1)
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
    if not (sg.proc_id and h and h.nmatch >= 2 and h.prec >= NAMED_PREC):
        return False
    mass = h.hi_match + h.hi_miss
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
        distinct = any(idx._weight(t) >= HI_IDF for t in sg.query.terms)
        # tên mỏng: đang có chủ đề + câu mang tín hiệu nối + thủ tục xếp đầu không phủ chắc (khớp <2 chữ) => không coi là thủ tục mới
        # (chữ lạ còn dư chỉ chặn việc kế thừa khi thủ tục đang nói do người dùng GỌI TÊN; thủ tục suy ra từ lời kể thì nới)
        thin = bool(st.topic and (strong or medium or sg.query.fields) and not _is_named(sg) and (not distinct or st.loose))
        weak = weak or thin
        if sg.proc_id and not weak:                               # có tên thủ tục mới, đủ phủ
            pid = sg.proc_id
            if negs or mk.get("corr"):
                sg.decision, sg.why = "correction", "người dùng sửa ý: bỏ thủ tục bị phủ định/nêu lại thủ tục đúng"
            elif not st.topic:
                sg.decision, sg.why = "new", "đầu hội thoại / chưa có thủ tục đang nói"
            elif pid == st.topic:
                sg.decision, sg.why = "follow_up", "nêu lại đúng thủ tục đang nói"
            elif pid in st.history:
                sg.decision, sg.why = "return", "nêu thủ tục đã nói trước đó"
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
            sg.uncertain, sg.ambiguous, sg.near = False, False, []
            sg.decision = "follow_up"
            sg.why = ("câu điều kiện/câu cụt \"thì sao\" không nêu thủ tục mới" if strong else
                      "từ nối/đại từ/hỏi mục, không còn chữ nghiệp vụ lạ") + (", tên thủ tục mới phủ yếu" if weak else "")
        else:
            sg.decision = "independent"
            sg.why = ("chủ đề ngoài phạm vi" if sg.oos_topic else "chữ nghiệp vụ lạ còn dư, không nối" if distinct and st.topic
                      else "không có tín hiệu nối" if st.topic else "chưa có thủ tục đang nói")


def _resolve_text(idx: Index, text: str, st: ConvState, accept: float, options: list | None = None) -> list[Segment]:
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
            return [Segment(text, mq, proc_id=st.topic, inherited=True, reason="in_scope", decision="follow_up",
                            why="câu điều kiện, phần chính không nêu thủ tục mới")]
    if mk.get("meta") and st.topic and not whole.terms:
        return [Segment(text, whole, proc_id=st.topic, inherited=True, reason="in_scope", decision="follow_up", why="hỏi lại/diễn đạt lại câu trước")]
    parts, qs = [], []
    cmp = split_compare(main)
    for frag in (cmp or split_segments(main)):
        fq = understand(idx.conn, frag, idx.syn)
        if parts and not cmp and len(fq.terms) < 2 and not fq.fields:   # mảnh quá ngắn/ngữ cảnh: gộp vào mảnh trước
            parts[-1] += " " + frag
            qs[-1] = understand(idx.conn, parts[-1], idx.syn)
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
        sg.hits = idx.rank(sg.query, limit=15 if negs else 5)
        if negs:
            keep = [h for h in sg.hits if not _negated(h, negs, sg.query.terms)]
            sg.hits = (keep or sg.hits)[:5]
        top = sg.hits[0] if sg.hits else None
        fq = _fold(sg.text)
        tm = OOS_TOPICS.search(fq)
        # chủ đề trong danh sách chặn nhưng CHÍNH TÊN thủ tục top có cụm đó ("khám bệnh, chữa bệnh BHYT") => thủ tục có thật trong kho
        topic_out = bool(tm and not (top and tm.group(1) in _fold(top.name))) or bool(_PASSPORT.search(fq) and not _PASSPORT_OK.search(fq))
        sg.oos_topic = topic_out
        if top and top.flags:    # ưu tiên bản không bị cờ nếu điểm sát nhau
            alt = next((h for h in sg.hits if not h.flags and h.score >= top.score - 0.08), None)
            top = alt or top
        if not top:
            sg.reason = "no_match"
        elif topic_out or (top.hi_match == 0 and top.hi_miss > 0):
            # cổng chữ-đặc-trưng: KHÔNG chữ hiếm nào của câu hỏi nằm trong tên thủ tục => khớp tình cờ bằng chữ chung.
            # ponytail: chỉ chặn khi 0 chữ hiếm khớp (chữ hiếm thừa như 'nộp','tốn' làm so tỉ lệ bị sai); chủ đề tình cờ vẫn dựa OOS_TOPICS
            sg.reason = "out_of_scope"
        elif top.score < accept or top.cov < ACCEPT_COV:
            sg.reason = "out_of_scope"
        elif any(f.startswith("vertical") or f == "province_only" for f in top.flags):
            sg.reason = "flagged:" + ",".join(top.flags)
        else:
            sg.proc_id, sg.reason = top.proc_id, "in_scope"
            sg.uncertain = top.score < UNCERTAIN_SCORE or top.cov < UNCERTAIN_COV or top.extras >= UNCERTAIN_EXTRAS
            sg.ambiguous = any(h.head != top.head and h.score >= top.score - AMBIG_GAP for h in sg.hits[1:])
            seen_heads, near, ts = {top.head or top.proc_id}, [top.proc_id], set(_fold(top.name).split())
            for h in sg.hits[1:]:
                k = h.head or h.proc_id
                if k not in seen_heads and h.score >= top.score - AMBIG_GAP and not h.flags and top.mass - h.mass < NEAR_MASS and not (ts <= set(_fold(h.name).split()) or set(_fold(h.name).split()) <= ts):   # ponytail: biến thể/đặc biệt hoá của top không tính
                    seen_heads.add(k)
                    near.append(h.proc_id)
            sg.near = near if len(near) >= 3 else []
    if len(segs) > 1 and not cmp:
        # mảnh sau dấu phẩy/"và" ngắn mà khớp yếu ("có kết quả", "bằng hình thức nào") là phần đệm của ý trước, không phải thủ tục mới
        def _weak(sg):
            top = sg.hits[0] if sg.hits else None
            return len(sg.query.terms) <= 3 and (top is None or top.score < RESIDUAL_SCORE)
        # mảnh ĐẦU yếu ("nhà em ở phường này, ...") là lời dẫn của người kể, không phải thủ tục: bỏ nếu phía sau còn mảnh mạnh
        while len(segs) > 1 and _weak(segs[0]) and not all(_weak(x) for x in segs[1:]):
            segs[1].query.fields = segs[0].query.fields + [f for f in segs[1].query.fields if f not in segs[0].query.fields]
            segs = segs[1:]
        keep = [segs[0]]
        for sg in segs[1:]:
            if _weak(sg):
                keep[-1].query.fields += [f for f in sg.query.fields if f not in keep[-1].query.fields]
            else:
                keep.append(sg)
        segs = keep
    if cmp and len(segs) == 2:
        for sg in segs:
            sg.relation, sg.near = "compare", []      # so sánh: hai vế đã chọn rõ, không hỏi lại
    merged = " ".join(st.story + [text])                  # (e) lời kể ở lượt trước (nếu có) + câu hiện tại
    hint, rest = event_hints(merged)
    # câu nói về việc KHÁC có chữ 'đám cưới' ("xin giấy phép tổ chức đám cưới ngoài trời"): còn chữ nghiệp vụ lạ ngoài sự kiện => không đoán
    odd = sum(idx._weight(t) >= HI_IDF for t in understand(idx.conn, rest, idx.syn).terms if len(t) >= 4 and t not in ("phuong",)) >= 3   # ponytail: đếm >=3 chữ hiếm lạ; đủ cho ca đo được, chưa phải mô hình
    if hint and not odd and not any(_is_named(sg) and _hit_of(sg).prec >= 0.3 for sg in segs) and not any(sg.oos_topic for sg in segs):
        alt = _resolve_text(idx, merged + " " + hint, ConvState(), accept)   # sự kiện đời sống ("bé mới sinh") -> tên thủ tục thường gặp
        if any(s.proc_id for s in alt):
            for s in alt:
                s.decision, s.why = "story", "lời kể sự kiện đời sống (" + hint + ") ghép với câu hỏi -> thủ tục"
            return alt
    _contextualize(idx, st, segs, mk, negs)
    return segs

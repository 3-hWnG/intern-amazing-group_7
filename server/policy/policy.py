"""Box 4: kiểm tra Plan do Planner sinh ra, gắn chính sách, chọn đường đi (router) cho TỪNG task.

Không gọi LLM. Mọi quyết định ở đây là luật + dữ liệu, nên test được và gỡ lỗi được.
Guardrail (đánh số theo PLAN_SYSTEM3.md Phase 4):
  1 schema/enum (Planner đã lọc; ở đây lọc lại)   2 procedure_id thật + còn hiệu lực
  3 điều kiện/ngữ cảnh phải có căn cứ trong lời người dùng   4 giới hạn (≤3 task, ≤2000 ký tự, ≤1 thẻ hỏi lại)
  5 không có số thì không đoán (field_status)   6 không hỏi điều đã biết
  7 phạm vi (ngành dọc, cấp tỉnh, hết hiệu lực)   8 chống chèn lệnh   9 che PII khi ghi log
"""
from __future__ import annotations

import os
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field, asdict

from system3.data import api as data_api
from system3.data.search import _PROVINCE_PATTERNS
from system3.data.textutil import fold
from system3.retrieval.context import strip_labels
from system3.retrieval.query import EXTRA_SYN, FIELD_CUES, PRE_SYN, STOP, _DROP_PHRASES

MAX_TASKS = 3
MAX_CHARS = 2000
VERTICAL = {"Thuế": "cơ quan Thuế", "Hải quan": "cơ quan Hải quan"}

# route: direct (tra CSDL thủ tục) | apologize | clarify | chitchat | note (chỉ ghi nhận thông tin người dùng kể)
# reason (khi apologize): not_found | not_commune_level | vertical_agency | expired | injection | off_topic

_INJECTION = re.compile(
    r"\b(bo qua (moi )?(huong dan|chi dan|quy tac)|ignore (all |previous |the )?(instructions|rules)|prompt he thong|system prompt|"
    r"quen (vai tro|moi thu)|tu gio ban la|ban khong con la|developer mode|jailbreak|"
    r"quen (het )?(cac |moi |tat ca )?(lenh|huong dan|quy tac|chi dan)|(in|cho biet|tiet lo|noi) .{0,20}(huong dan|chi dan|lenh) he thong)\b")
_PHONE = re.compile(r"(?<!\d)(0\d{9,10}|\+84\d{9,10})(?!\d)")
_ID = re.compile(r"(?<!\d)\d{9}(?!\d)|(?<!\d)\d{12}(?!\d)")


@dataclass
class RoutedTask:
    route: str = "direct"
    reason: str = ""
    action: str = ""
    procedure_id: str | None = None
    procedure_label: str = ""
    fields: list = field(default_factory=list)
    quantity: str = "none"
    conditions: list = field(default_factory=list)       # đã lọc theo căn cứ
    dropped_conditions: list = field(default_factory=list)
    soft_conditions: list = field(default_factory=list)  # hoàn cảnh do Planner LUẬT rút từ câu ("nếu X thì..."): chỉ để ghi chú bằng code, không nhờ LLM giải thích (khỏi thêm độ trễ)
    cases: list = field(default_factory=list)            # mục condition_index (tên trường hợp) khớp CHẮC với hoàn cảnh: Answerer chỉ trả giấy tờ của các trường hợp này
    context_facts: list = field(default_factory=list)
    evidence_demand: str = "none"
    relation: str = "independent"
    field_status: dict = field(default_factory=dict)     # field -> present|absent_confirmed|unknown
    variants: dict = field(default_factory=dict)         # {default, others:[{proc_id,label}]} khi thủ tục có nhiều dạng
    vertical_agency: str = ""


@dataclass
class Routed:
    tasks: list = field(default_factory=list)
    clarify: dict | None = None        # {question, options[{label, proc_id}], allow_free_text}
    flags: list = field(default_factory=list)   # injection | overflow | truncated | plan_fallback
    behavior: str = "answer"           # answer | apologize | clarify | chitchat
    memory_note: dict | None = None    # Phase 26: hồ sơ đã ảnh hưởng quyết định này {kind: pick|shrink|variant, subject, proc_id, procedure}

    def to_dict(self):
        return asdict(self)


# FINAL-PRODUCT: [B3] hàm che PII đã có nhưng chỉ dùng cho trace; bản cuối gọi nó trước khi ghi messages.content/plan_json/session_facts/title (mục 2)
def mask_pii(text: str) -> str:
    """Guardrail 9: che CCCD/CMND/SĐT trước khi ghi log."""
    return _ID.sub("[ID]", _PHONE.sub("[SDT]", text or ""))


def pre_check(text: str) -> dict:
    """Chạy TRƯỚC Planner: -> {text (đã cắt), flags}. Nội dung người dùng chỉ là DỮ LIỆU, không bao giờ là lệnh."""
    flags = []
    t = strip_labels(text or "")           # nhãn lượt/số thứ tự đầu câu ("Turn 2:", "Q:", "2)") không phải lời người dùng
    if len(t) > MAX_CHARS:
        t, flags = t[:MAX_CHARS], flags + ["truncated"]
    if _INJECTION.search(fold(t)):
        flags.append("injection")
    return {"text": t, "flags": flags}


_TOK = re.compile(r"[0-9a-z]+")


def grounded(snippet: str, user_text: str, facts: list[str]) -> bool:
    """Guardrail 3: ≥60% âm tiết của cụm có trong lời người dùng hoặc ngữ cảnh đã biết."""
    toks = [t for t in _TOK.findall(fold(snippet)) if len(t) > 1]
    if not toks:
        return False
    hay = set(_TOK.findall(fold(user_text + " " + " ".join(facts))))
    return sum(1 for t in toks if t in hay) / len(toks) >= 0.6


def _vertical(domain: str) -> str:
    for part in (domain or "").split(";"):
        if part.strip() in VERTICAL:
            return VERTICAL[part.strip()]
    return ""


_CGEN = set("dang ky thu tuc ho so truong hop doi voi cho viec cua va hoac theo trong tai ve nguoi cong dan viet nam gom nha em toi minh tui ban ong ba anh chi con chau gia dinh bac chu co di".split())
# Từ ĐỜI THƯỜNG chỉ hoàn cảnh -> chữ trong TÊN TRƯỜNG HỢP của condition_index (người dân nói "ở chùa", bộ đội, ở trọ; dữ liệu viết "cơ sở tín ngưỡng, cơ sở tôn giáo"...).
# ponytail: bảng tay ~8 nhóm; chỉ dùng để khớp mục điều kiện, không đổi truy hồi thủ tục. Mở rộng theo log thật.
_SITUATION = [(re.compile(rx), syn) for rx, syn in [
    (r"\b(chua|nha tho|thanh that|tu vien|den tho|mieu|nha nguyen|giao xu|tu hanh|tin nguong|ton giao)\b", "co so tin nguong co so ton giao"),
    (r"\b(bo doi|quan nhan|chien si|doanh trai|don vi quan doi|dong quan)\b", "don vi dong quan quan doi cong an nhan dan"),
    (r"\b(o tro|nha tro|thue tro|thue nha|muon nha|o nho|nha nguoi quen|nha ban be|nha ho hang)\b", "thue muon o nho"),
    (r"\b(duong lao|mai am|bao tro xa hoi|tro giup xa hoi|neo don|mo coi)\b", "co so tro giup xa hoi cham soc nuoi duong"),
    (r"\b(theo danh sach|ca chuc|tap the|ky tuc xa|nhieu nguoi cung luc|cong nhan|nhan vien)\b", "theo danh sach"),
    (r"\b(ly di|ly than|tung ly hon|da ly hon)\b", "ly hon"),
    (r"\b(uy quyen|nho nguoi khac|nho nguoi than)\b", "uy quyen"),
]]


def _aug(user_text: str) -> str:
    f = fold(user_text)
    return user_text + " " + " ".join(syn for rx, syn in _SITUATION if rx.search(f))


_CUE_RX = re.compile(r"(?<![0-9a-z])(?:" + "|".join(sorted({c for cs in FIELD_CUES.values() for c in cs}, key=len, reverse=True)) + r")(?![0-9a-z])")


def _user_words(user_text: str) -> set:
    """Chữ NỘI DUNG của lời người dùng để đối chiếu mục điều kiện: bỏ cụm hỏi mục ("cần giấy tờ gì", "lệ phí bao nhiêu"), chữ hư/xưng hô/lời đệm (STOP: "là", "muốn", "em", "cho", "hỏi"...);
    chữ do bảng hoàn cảnh `_SITUATION` thêm vào (đã chọn tay) thì giữ.
    Nguyên nhân gốc (Phase 30): trước đây MỌI chữ của câu đều được đem so, nên một chữ hư đứng riêng trong đúng một mục anh em ("là" trong "... có công trình phụ trợ là nhà ở", "ở/nhà" trong "nhà ở công vụ")
    đủ làm mục đó "khớp" -> câu "Lệ phí đăng ký thường trú là bao nhiêu?" bị gán điều kiện "thường trú tại cơ sở tín ngưỡng" (gọi bước LLM sinh chữ thừa ở ~60% ca có điều kiện)
    và, tệ hơn, `cond_hit` coi như người dùng đã nêu từ phân biệt nên KHÔNG hỏi lại ("em muốn bảo hiểm y tế" trả lời luôn một thủ tục)."""
    return set(_user_seq(user_text))


def _user_seq(user_text: str) -> list:
    """Như `_user_words` nhưng giữ thứ tự (để nhận cụm 2 chữ nội dung liền nhau như "ủy quyền")."""
    f = _CUE_RX.sub(" ", fold(user_text))
    extra = " ".join(syn for rx, syn in _SITUATION if rx.search(fold(user_text)))
    return [t for t in _TOK.findall(f) if t not in STOP] + _TOK.findall(extra)


def adds_info(cond: str, label: str) -> bool:
    """Mảnh điều kiện phải cho THÊM thông tin ngoài tên thủ tục: còn ít nhất một chữ nội dung không nằm trong tên thủ tục, không phải chữ hư/chữ chung/cụm hỏi mục.
    ("đăng ký tạm trú" cho thủ tục "Đăng ký tạm trú" = chỉ lặp tên -> không phải điều kiện; "chủ nhà ở nước ngoài" thì có.)"""
    name = set(_TOK.findall(fold(label)))
    return any(len(t) > 1 and t not in name and t not in _CGEN for t in _user_words(cond))


def _match_conditions(conn, pid: str, label: str, user_text: str) -> list[str]:
    """Chọn mục condition_index mà người dùng nêu hoàn cảnh: chữ ĐẶC TRƯNG của mục (không có trong tên thủ tục, ít trùng với
    các mục anh em) có trong lời người dùng. Chọn mục điểm cao nhất, cần >= 1 chữ độc nhất hoặc >= 3 chữ chung.
    ponytail: khớp chữ, không hiểu nghĩa ("tu hành ở chùa" != "cơ sở tín ngưỡng"); LLM/Phase 11 lo phần ngữ nghĩa."""
    rows = [r["text"] for r in data_api.conditions(conn, pid) if r["type"] != "who" or r["source"] == "case"]    # 'who' kiểu đối tượng chung ("Công dân Việt Nam") bỏ; 'who' là tên TRƯỜNG HỢP (source=case) giữ
    if len(rows) < 2:
        return []
    name = set(_TOK.findall(fold(label)))
    user = _user_words(user_text)
    toks = [{t for t in _TOK.findall(fold(x)) if len(t) > 1 and t not in name and t not in _CGEN} for x in rows]
    best, best_s = None, 0.0
    useq = _user_seq(user_text)
    ubi = {(a, b) for a, b in zip(useq, useq[1:])}
    for x, tk in zip(rows, toks):
        sc = sum(1.0 / sum(1 for o in toks if t in o) for t in tk if t in user)
        # cụm 2 chữ nội dung liền nhau có ở cả câu hỏi và mục ("ủy quyền") là bằng chứng đủ dù cả nhóm anh em cùng có cụm đó
        rq = [t for t in _TOK.findall(fold(x)) if len(t) > 1 and t not in name and t not in _CGEN and t not in STOP]
        if any(b in ubi for b in zip(rq, rq[1:])):
            sc = max(sc, 0.99)
        if sc > best_s:
            best, best_s = x, sc
    return [best] if best and best_s >= 0.99 else []


def _strong_case(conn, pid: str, label: str, row: str, user_text: str) -> bool:
    """Hoàn cảnh khớp mục `row` đủ chắc để CHỈ trả giấy tờ của trường hợp đó: >= 2 chữ đặc trưng của mục có trong lời người dùng và chiếm >= 35% chữ đặc trưng
    (khớp một chữ lẻ như 'công nhân' ~ 'Công an nhân dân' thì chỉ ghi chú, không cắt hồ sơ)."""
    name = set(_TOK.findall(fold(label)))
    user = _user_words(user_text)
    tk = {t for t in _TOK.findall(fold(row)) if len(t) > 1 and t not in name and t not in _CGEN}
    hit = sum(1 for t in tk if t in user)
    return hit >= 2 and hit >= 0.35 * len(tk)


_STOP = set("thu tuc cho hoi toi minh muon can lam gi nhu the nao va cua o la de duoc co khong a nhe".split())


def _names_candidate(conn, pids: list[str], user_text: str, partial: bool = True) -> bool:
    """Phase 26: câu hỏi đã nêu rõ MỘT ứng viên -> hồ sơ KHÔNG được can thiệp (chỉ ưu tiên khi người dùng chưa nói rõ). Rõ khi:
    (a) nguyên tên một ứng viên (>= 15 ký tự) nằm trong câu; hoặc (b) (partial) cụm chữ nội dung của câu (>= 3 chữ, bỏ lời đệm đầu/cuối)
    là một đoạn LIỀN trong tên của đúng MỘT ứng viên ('đăng ký thành lập tổ hợp tác' chỉ nằm trong một tên; câu cụt như 'phê duyệt dự án' nằm trong nhiều tên thì chưa rõ)."""
    f = " ".join(_TOK.findall(fold(user_text)))
    w = f.split()
    while w and w[0] in _STOP:
        w.pop(0)
    while w and w[-1] in _STOP:
        w.pop()
    phrase, inside = " ".join(w), 0
    for pid in pids:
        r = conn.execute("SELECT name FROM procedures WHERE proc_id=? AND status='active'", (pid,)).fetchone()
        if not r:
            continue
        full = " ".join(_TOK.findall(fold(r[0])))
        n = full[len("thu tuc "):] if full.startswith("thu tuc ") else full
        if len(n) >= 15 and n in f:
            return True
        inside += len(w) >= 3 and f" {phrase} " in f" {full} "
    return partial and inside == 1


def filter_by_subject(conn, pids: list[str], memory: dict | None, user_text: str = "", check_named: bool = True) -> tuple[list[str], dict | None]:
    """Phase 26: lọc ứng viên theo đối tượng đã nhớ. -> (ứng viên mới, ghi chú | None).
    - đúng 1 ứng viên hợp (và mọi ứng viên khác chắc chắn không hợp): kind='pick'
    - 2..n-1 hợp: kind='shrink' (chỉ giữ các ứng viên hợp)
    - ứng viên không khai đối tượng nào = chưa biết -> giữ (không loại vì thiếu dữ liệu); không hợp ai/hợp hết -> không đổi.
    Không đụng khi câu hỏi nêu nguyên tên một ứng viên."""
    if not memory or not memory.get("subjects") or len(pids) < 2 or (check_named and _names_candidate(conn, pids, user_text)):
        return pids, None
    subs = data_api.subjects_of(conn, pids)
    hit = [p for p in pids if not subs[p] or subs[p] & memory["subjects"]]
    if len(hit) == len(pids) or not hit:
        return pids, None
    kind = "pick" if len(hit) == 1 and subs[hit[0]] else "shrink" if len(hit) >= 2 else None
    return (hit, {"kind": kind, "subject": memory["label"]}) if kind else (pids, None)


def _memory_variant(conn, head: str, dv: str, memory: dict, user_text: str) -> str | None:
    """Phase 26: bản mặc định của nhóm không hợp đối tượng đã nhớ mà có biến thể hợp (không gắn tỉnh, cấp xã, không ngành dọc) -> biến thể đó."""
    vs = data_api.variants(conn, head)
    subs = data_api.subjects_of(conn, [v["proc_id"] for v in vs])
    if not subs.get(dv) or subs[dv] & memory["subjects"] or _names_candidate(conn, [dv], user_text, partial=False):
        return None
    for v in vs:
        if v["proc_id"] == dv or v["province"] or not subs[v["proc_id"]] & memory["subjects"]:
            continue
        r = conn.execute("SELECT domain, agency_levels FROM procedures WHERE proc_id=? AND status='active'", (v["proc_id"],)).fetchone()
        if r and not _vertical(r["domain"]) and "Xã/Phường" in (r["agency_levels"] or ""):
            return v["proc_id"]
    return None


_NEUTRAL = STOP - {"con", "anh", "chi", "bac"}      # chữ hư/xưng hô; "con", "anh", "chị", "bác" là ĐỐI TƯỢNG (khai sinh cho con) nên không bỏ
_NAME_OK = {"giay"}                                 # "giấy khai sinh" = "khai sinh"
_MAX_FAMILY_OPTS = 6
_MIN_REAL_VARIANTS = 3                              # ít hơn: giữ bản mặc định + nút "dạng khác" (bản chính chiếm ưu thế: "giám hộ" so với "giám hộ có yếu tố nước ngoài")


def real_variants(conn, head: str) -> list[str]:
    """Phase 31: các dạng THẬT của một họ thủ tục (proc_id, bản mặc định trước) = bản không gắn tỉnh, cấp xã, không ngành dọc, tên lõi khác nhau
    (bỏ "Thủ tục", dấu câu, hoa/thường) và nội dung hồ sơ (`components`) khác nhau. Bản tỉnh trùng nội dung và tên gần như trùng ("... hoạt động cách mạng" ~ "... cách mạng.") không tính.
    Chỉ cần xét họ có >= 3 dạng không gắn tỉnh (ít hơn: giữ bản mặc định + nút "dạng khác")."""
    vs = [v for v in data_api.variants(conn, head) if not v["province"]]
    if len(vs) < _MIN_REAL_VARIANTS:
        return []
    out, names, bodies = [], set(), set()
    for v in vs:
        r = conn.execute("SELECT domain, agency_levels FROM procedures WHERE proc_id=? AND status='active'", (v["proc_id"],)).fetchone()
        if not r or _vertical(r["domain"]) or "Xã/Phường" not in (r["agency_levels"] or ""):
            continue
        nm = " ".join(sorted(set(_TOK.findall(re.sub(r"^thu tuc ", "", fold(v["name"]))))))
        body = " ".join(c["text"] for c in data_api.fields(conn, v["proc_id"], ["components"]))
        bk = " ".join(_TOK.findall(fold(body)))
        if nm in names or (bk and bk in bodies):
            continue
        names.add(nm)
        bodies.add(bk)
        out.append(v["proc_id"])
    return out


_KIN = {"con", "cháu", "ông", "bà", "bố", "ba", "cha", "mẹ", "anh", "chị", "vợ", "chồng", "chú", "bác", "dì", "cậu", "bé", "mợ", "thím"}   # đối tượng (người thụ hưởng) có dấu: không lẫn "đi", "đâu", "nói"
_KIN_PLAIN = {"con", "chau", "ong", "cha", "me", "chong", "anh", "be", "vo"}      # câu gõ KHÔNG dấu: chỉ nhận chữ ít nhập nhằng ("ba", "bo", "chi", "di" bỏ)


def _kin(txt: str) -> Counter:
    t = unicodedata.normalize("NFC", txt).lower()
    plain = fold(t) == t                       # không có chữ có dấu nào
    return Counter(w for w in re.findall(r"\w+", t) if w in (_KIN_PLAIN if plain else _KIN))


def _names_family_only(head: str, label: str, user_text: str, pquery: str, facts_text: str = "") -> bool:
    """Lời người dùng CHỈ nêu tên chung của họ thủ tục (không thêm gì): (1) bộ hiểu câu (`procedure_query`, đã sửa gõ tắt/chữ dính) còn đủ chữ đặc trưng của tên chung;
    (2) câu gốc sau khi bỏ cụm hỏi mục, lời đệm của truy hồi (`query._DROP_PHRASES`: "tìm hiểu", "tư vấn", "cho mình hỏi"...) và chữ hư/xưng hô (STOP) KHÔNG còn chữ nào ngoài tên chung.
    Chữ còn lại = người dùng đã nói thêm: từ phân biệt ("lưu động", "nước ngoài", "quá hạn"), hoàn cảnh ("nếu người mất không có giấy báo tử"), phủ định ("không phải khai sinh"), đối tượng.
    Chữ đối tượng ("cho con", "cho bố tôi") kiểm riêng, đếm số lần so với tên thủ tục ("nhận cha, mẹ, con cho CON tôi" có chữ "con" thứ hai). Fact đã kể: chữ nội dung nào ngoài tên chung cũng coi là đã nói thêm."""
    h = [t for t in head.split() if t not in _CGEN and t not in _NEUTRAL]
    u = {t for t in _TOK.findall(fold(pquery)) if t not in _CGEN and t not in _NEUTRAL}
    f = {t for t in _user_words_keep(user_text + " " + facts_text) if t not in _CGEN} - set(h)
    return bool(h) and set(h) <= u and not f and not (_kin(user_text) - _kin(label))


_SHORT = {**EXTRA_SYN, **PRE_SYN}
_CUES_LONG = sorted({c for cs in FIELD_CUES.values() for c in cs}, key=len, reverse=True)


def _user_words_keep(user_text: str) -> list:
    f = " " + " ".join(_SHORT.get(t, t) for t in _TOK.findall(fold(user_text))) + " "      # "dk" -> "dang ky", "tg" -> "thoi gian"... (bảng viết tắt của bộ hiểu câu)
    for cue in _CUES_LONG:                     # cụm hỏi mục, dài trước (như query.py: "bao nhieu tien" trước "het bao nhieu")
        f = f.replace(f" {cue} ", " ")
    for pat, _ in _PROVINCE_PATTERNS:          # tên tỉnh/thành không chọn dạng nào (bản theo tỉnh không phải dạng thật)
        f = f.replace(f" {pat} ", " ")
    for ph in _DROP_PHRASES:                   # lời đệm của truy hồi ("tìm hiểu", "tư vấn", "cho mình hỏi", "thông thường"...)
        f = f.replace(f" {ph} ", " ")
    return [t for t in _TOK.findall(f) if t not in _NEUTRAL and t not in _NAME_OK]


def check(plan, *, user_text: str, conn=None, facts: list[str] | None = None,
          known_procs: list[str] | None = None, flags: list[str] | None = None, no_clarify: bool = False,
          memory: dict | None = None) -> Routed:
    """plan: planner.Plan (hoặc đối tượng có .tasks/.needs_clarification/.source).
    memory (Phase 26): {subjects:set[str], label} từ hồ sơ người dùng; None = hành vi y hệt trước Phase 26."""
    conn = conn or data_api.connect()
    facts = facts or []
    out = Routed(flags=list(flags or []))
    if plan.source == "fallback":
        out.flags.append("plan_fallback")
    if "injection" in out.flags:
        out.behavior = "apologize"
        out.tasks = [RoutedTask(route="apologize", reason="injection")]
        return out

    raw = list(plan.tasks)
    cond_hits: list[bool] = []
    var_note = None
    if len(raw) > MAX_TASKS:
        out.flags.append("overflow")
    for t in raw[:MAX_TASKS]:
        cond_hit = False
        rt = RoutedTask(action=t.action, procedure_id=t.procedure_id, fields=[f for f in t.fields],
                        quantity=t.quantity, evidence_demand=t.evidence_demand, relation=t.relation)
        # --- không cần thủ tục
        if t.action == "chitchat":
            rt.route = "chitchat"
        elif t.action == "provide_info":
            rt.route = "note"
            rt.context_facts = [c for c in t.context_facts if grounded(c, user_text, facts)]
        elif not t.procedure_id:
            rt.route, rt.reason = "apologize", ("off_topic" if t.action == "out_of_scope" and not t.candidates else "not_found")
        else:
            row = conn.execute("SELECT name, domain, agency_levels FROM procedures WHERE proc_id=? AND status='active'",
                               (t.procedure_id,)).fetchone()
            if row is None:
                exp = data_api.is_expired(conn, t.procedure_id)
                rt.route, rt.reason = "apologize", ("expired" if exp else "not_found")
            else:
                rt.procedure_label = row["name"]
                va = _vertical(row["domain"])
                if va:
                    rt.route, rt.reason, rt.vertical_agency = "apologize", "vertical_agency", va
                elif "Xã/Phường" not in (row["agency_levels"] or ""):
                    rt.route, rt.reason = "apologize", "not_commune_level"
                else:
                    rt.route = "direct"
        # --- biến thể: người dùng không nói dạng nào -> trả bản mặc định của nhóm (không hỏi lại)
        if rt.route == "direct" and getattr(t, "refers_to", "new") != "last":   # chọn theo thứ tự/nút: không đổi sang bản mặc định
            fam = data_api.family_of(conn, rt.procedure_id)
            if fam and fam["n_members"] > 1:
                dv = data_api.default_variant(conn, fam["head"])
                if dv and dv != rt.procedure_id:
                    dname = conn.execute("SELECT name FROM procedures WHERE proc_id=? AND status='active'", (dv,)).fetchone()
                    mods = set(_TOK.findall(fold(rt.procedure_label))) - set(_TOK.findall(fold(dname[0] if dname else "")))
                    if dname and mods and not (mods & set(_TOK.findall(fold(user_text)))):
                        rt.procedure_id, rt.procedure_label = dv, dname[0]
            if memory and memory.get("subjects") and fam and fam["n_members"] > 1:   # Phase 26: đang ở bản mặc định -> ưu tiên bản hợp đối tượng đã nhớ
                dv = data_api.default_variant(conn, fam["head"])
                mv = _memory_variant(conn, fam["head"], dv, memory, user_text) if dv and rt.procedure_id == dv else None
                if mv:
                    mname = conn.execute("SELECT name FROM procedures WHERE proc_id=?", (mv,)).fetchone()[0]
                    rt.procedure_id, rt.procedure_label = mv, mname
                    var_note = var_note or {"kind": "variant", "subject": memory["label"], "proc_id": mv, "procedure": mname}
        # --- căn cứ cho điều kiện / ngữ cảnh (guardrail 3)
        for c in t.conditions:
            if not adds_info(c, rt.procedure_label or t.procedure_label):      # mảnh chỉ lặp tên thủ tục/chữ hư: không phải điều kiện (Phase 30)
                continue
            (((rt.soft_conditions if getattr(plan, "source", "") == "rules" else rt.conditions) if grounded(c, user_text, facts) else rt.dropped_conditions)).append(c)
        rt.context_facts = [c for c in t.context_facts if grounded(c, user_text, facts)]
        if rt.route == "direct":     # nhánh trường hợp (luật): hoàn cảnh người dùng nêu khớp mục condition_index của thủ tục
            for ct in _match_conditions(conn, rt.procedure_id, rt.procedure_label, user_text):
                cond_hit = True          # hoàn cảnh đã chỉ vào mục riêng của thủ tục này: coi như đã nêu từ phân biệt
                if ct not in rt.conditions:
                    rt.conditions.append(ct)
                if _strong_case(conn, rt.procedure_id, rt.procedure_label, ct, user_text):
                    rt.cases.append(ct)
        # --- chuẩn hoá quantity theo field (LLM nhỏ hay quên)
        if "fees" in rt.fields and rt.quantity == "none":
            rt.quantity = "amount"
        if "processing_time" in rt.fields and rt.quantity == "none":
            rt.quantity = "duration"
        if "meta" in rt.fields and rt.evidence_demand == "none":
            rt.evidence_demand = "legal_basis"
        # --- trạng thái từng field (guardrail 5) + biến thể
        if rt.route == "direct":
            if getattr(t, "where", False) and "address" in rt.fields:     # "làm ở đâu" chung chung: cổng không ghi địa điểm thì trả cơ quan giải quyết
                def _has(f):
                    return any(c["text"].strip() for c in data_api.fields(conn, rt.procedure_id, [f]))
                if not _has("address") and _has("agency"):
                    rt.fields = ["agency" if f == "address" else f for f in rt.fields]
            names = rt.fields or ["components", "fees", "processing_time", "address"]
            have = {r["field"]: r["status"] for r in data_api.fields(conn, rt.procedure_id, names)}
            rt.field_status = {f: have.get(f, "unknown") for f in names}
            fam = data_api.family_of(conn, rt.procedure_id)
            if fam and fam["n_members"] > 1:
                vs = data_api.variants(conn, fam["head"])
                rt.variants = {"default": next((v["proc_id"] for v in vs if v["default_variant"]), rt.procedure_id),
                               "others": [{"proc_id": v["proc_id"], "label": v["name"]}
                                          for v in vs if v["proc_id"] != rt.procedure_id][:4]}
        out.tasks.append(rt)
        cond_hits.append(cond_hit)

    # --- clarify bằng LUẬT (đã duyệt): >=3 thủ tục khác nhóm, điểm sát nhau, người dùng chưa nêu từ phân biệt -> hỏi lại, không đoán.
    # Sau khi đã trả lời thẻ (no_clarify) thì chọn ứng viên gần ý nhất, không hỏi lần 2. 2 biến thể gần nhau: giữ bản mặc định + nút.
    if not no_clarify and not known_procs and len(out.tasks) == 1 and out.tasks[0].route == "direct":
        near = list(getattr(raw[0], "near", []) or [])
        fam_q, rv = "", []
        if len(near) < 2 and getattr(raw[0], "refers_to", "new") != "last" and not cond_hits[0] and os.environ.get("S3_FAMILY_CLARIFY", "0") == "1":     # S3_FAMILY_CLARIFY=1 bật hỏi lại họ nhiều dạng (Phase 31; mặc định TẮT từ 2026-10-08) (bản mặc định + nút)
            # Phase 31: câu chỉ nêu tên chung của họ thủ tục có >= 3 dạng THẬT (khai sinh, kết hôn, khai tử...) -> hỏi lại thay vì trả bản mặc định
            fam = data_api.family_of(conn, out.tasks[0].procedure_id)
            rv = real_variants(conn, fam["head"]) if fam and fam["n_members"] >= _MIN_REAL_VARIANTS else []
            if len(rv) >= _MIN_REAL_VARIANTS and out.tasks[0].procedure_id in rv and _names_family_only(fam["head"], out.tasks[0].procedure_label, user_text, getattr(raw[0], "procedure_query", "") or "", " ".join(facts)):
                near, fam_q = rv, fam["head"]
        if len(near) >= 2 and getattr(raw[0], "refers_to", "new") != "last" and not cond_hits[0]:
            near, note = filter_by_subject(conn, near, memory, user_text, check_named=not fam_q)      # Phase 26: hồ sơ thu hẹp ứng viên (không có hồ sơ: không đổi)
            if note and note["kind"] == "pick":
                import copy
                t2 = copy.copy(raw[0])
                t2.procedure_id, t2.refers_to = near[0], "last"
                t2.action = "ask_field" if t2.fields else "find_procedure"
                p2 = copy.copy(plan)
                p2.tasks, p2.needs_clarification = [t2], False
                res = check(p2, user_text=user_text, conn=conn, facts=facts, flags=flags, no_clarify=True)
                if res.tasks and res.tasks[0].route == "direct":
                    res.memory_note = {**note, "proc_id": near[0], "procedure": res.tasks[0].procedure_label}
                    return res
                near, note = (rv if fam_q else list(getattr(raw[0], "near", []) or [])), None      # chọn xong mà không trả lời được: bỏ, giữ hành vi cũ
            opts = []
            for pid in near[:_MAX_FAMILY_OPTS if fam_q else 4]:
                r = conn.execute("SELECT name FROM procedures WHERE proc_id=? AND status='active'", (pid,)).fetchone()
                if r:
                    opts.append({"label": r[0][:110], "proc_id": pid})
            if len(opts) >= 2:
                q = "Thủ tục này có nhiều dạng khác nhau tuỳ trường hợp. Bạn muốn hỏi dạng nào?" if fam_q else "Bạn muốn hỏi về thủ tục nào?"
                if note:
                    q += f" (Theo hồ sơ của bạn - đối tượng: {note['subject']} - mình chỉ hiện các thủ tục phù hợp; không thấy thì bạn gõ tên thủ tục nhé.)"
                out.clarify = {"question": q, "options": opts, "allow_free_text": True}
                out.behavior = "clarify"
                out.memory_note = note
                return out

    # --- clarify: tối đa 1 thẻ/lượt; chỉ khi LLM xin VÀ chưa có thủ tục nào chắc (guardrail 4, 6)
    chosen = [t for t in out.tasks if t.route == "direct"]
    if getattr(plan, "needs_clarification", False) and not chosen and not known_procs:
        opts, seen = [], set()
        for t in raw:
            for pid in t.candidates[:4]:
                if pid not in seen:
                    seen.add(pid)
                    r = conn.execute("SELECT name FROM procedures WHERE proc_id=? AND status='active'", (pid,)).fetchone()
                    if r:
                        opts.append({"label": r[0][:110], "proc_id": pid})
        if opts:
            out.clarify = {"question": "Bạn muốn hỏi về thủ tục nào?", "options": opts[:4], "allow_free_text": True}
            out.behavior = "clarify"
            return out

    out.memory_note = var_note
    kinds = {t.route for t in out.tasks}
    if "direct" in kinds:
        out.behavior = "answer"
    elif kinds <= {"chitchat", "note"} and kinds:
        out.behavior = "chitchat"
    else:
        out.behavior = "apologize"
    return out

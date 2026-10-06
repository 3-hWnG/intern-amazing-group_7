"""Box 4: kiểm tra Plan do Planner sinh ra, gắn chính sách, chọn đường đi (router) cho TỪNG task.

Không gọi LLM. Mọi quyết định ở đây là luật + dữ liệu, nên test được và gỡ lỗi được.
Guardrail (đánh số theo PLAN_SYSTEM3.md Phase 4):
  1 schema/enum (Planner đã lọc; ở đây lọc lại)   2 procedure_id thật + còn hiệu lực
  3 điều kiện/ngữ cảnh phải có căn cứ trong lời người dùng   4 giới hạn (≤3 task, ≤2000 ký tự, ≤1 thẻ hỏi lại)
  5 không có số thì không đoán (field_status)   6 không hỏi điều đã biết
  7 phạm vi (ngành dọc, cấp tỉnh, hết hiệu lực)   8 chống chèn lệnh   9 che PII khi ghi log
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from system3.data import api as data_api
from system3.data.textutil import fold

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

    def to_dict(self):
        return asdict(self)


def mask_pii(text: str) -> str:
    """Guardrail 9: che CCCD/CMND/SĐT trước khi ghi log."""
    return _ID.sub("[ID]", _PHONE.sub("[SDT]", text or ""))


def pre_check(text: str) -> dict:
    """Chạy TRƯỚC Planner: -> {text (đã cắt), flags}. Nội dung người dùng chỉ là DỮ LIỆU, không bao giờ là lệnh."""
    flags = []
    t = text or ""
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


_CGEN = set("dang ky thu tuc ho so truong hop doi voi cho viec cua va hoac theo trong tai ve nguoi cong dan viet nam gom".split())
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


def _match_conditions(conn, pid: str, label: str, user_text: str) -> list[str]:
    """Chọn mục condition_index mà người dùng nêu hoàn cảnh: chữ ĐẶC TRƯNG của mục (không có trong tên thủ tục, ít trùng với
    các mục anh em) có trong lời người dùng. Chọn mục điểm cao nhất, cần >= 1 chữ độc nhất hoặc >= 3 chữ chung.
    ponytail: khớp chữ, không hiểu nghĩa ("tu hành ở chùa" != "cơ sở tín ngưỡng"); LLM/Phase 11 lo phần ngữ nghĩa."""
    rows = [r["text"] for r in data_api.conditions(conn, pid) if r["type"] != "who" or r["source"] == "case"]    # 'who' kiểu đối tượng chung ("Công dân Việt Nam") bỏ; 'who' là tên TRƯỜNG HỢP (source=case) giữ
    if len(rows) < 2:
        return []
    name = set(_TOK.findall(fold(label)))
    user = set(_TOK.findall(fold(_aug(user_text))))
    toks = [{t for t in _TOK.findall(fold(x)) if len(t) > 1 and t not in name and t not in _CGEN} for x in rows]
    best, best_s = None, 0.0
    for x, tk in zip(rows, toks):
        sc = sum(1.0 / sum(1 for o in toks if t in o) for t in tk if t in user)
        if sc > best_s:
            best, best_s = x, sc
    return [best] if best and best_s >= 0.99 else []


def _strong_case(conn, pid: str, label: str, row: str, user_text: str) -> bool:
    """Hoàn cảnh khớp mục `row` đủ chắc để CHỈ trả giấy tờ của trường hợp đó: >= 2 chữ đặc trưng của mục có trong lời người dùng và chiếm >= 35% chữ đặc trưng
    (khớp một chữ lẻ như 'công nhân' ~ 'Công an nhân dân' thì chỉ ghi chú, không cắt hồ sơ)."""
    name = set(_TOK.findall(fold(label)))
    user = set(_TOK.findall(fold(_aug(user_text))))
    tk = {t for t in _TOK.findall(fold(row)) if len(t) > 1 and t not in name and t not in _CGEN}
    hit = sum(1 for t in tk if t in user)
    return hit >= 2 and hit >= 0.35 * len(tk)


def check(plan, *, user_text: str, conn=None, facts: list[str] | None = None,
          known_procs: list[str] | None = None, flags: list[str] | None = None, no_clarify: bool = False) -> Routed:
    """plan: planner.Plan (hoặc đối tượng có .tasks/.needs_clarification/.source)."""
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
        # --- căn cứ cho điều kiện / ngữ cảnh (guardrail 3)
        for c in t.conditions:
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
        if len(near) >= 3 and getattr(raw[0], "refers_to", "new") != "last" and not cond_hits[0]:
            opts = []
            for pid in near[:4]:
                r = conn.execute("SELECT name FROM procedures WHERE proc_id=? AND status='active'", (pid,)).fetchone()
                if r:
                    opts.append({"label": r[0][:110], "proc_id": pid})
            if len(opts) >= 3:
                out.clarify = {"question": "Bạn muốn hỏi về thủ tục nào?", "options": opts, "allow_free_text": True}
                out.behavior = "clarify"
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

    kinds = {t.route for t in out.tasks}
    if "direct" in kinds:
        out.behavior = "answer"
    elif kinds <= {"chitchat", "note"} and kinds:
        out.behavior = "chitchat"
    else:
        out.behavior = "apologize"
    return out

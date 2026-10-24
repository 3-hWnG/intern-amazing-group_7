"""Planner: luật nhanh -> (nếu cần) Qwen3-4B với danh sách ứng viên -> Plan. Hỏng thì dựng plan bằng luật.

LLM KHÔNG tự điền procedure_id: nó chọn chỉ số `cand`; mã thật lấy từ kết quả retrieval (Phase 2).
"""
from __future__ import annotations

import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass, field, asdict

from system3.data import api as data_api
from system3.data.textutil import fold
from system3.retrieval import Index
from system3.retrieval.rank import resolve, Segment, ACCEPT_SCORE

from . import hybrid
from .prompt import SYSTEM, HYBRID_SYSTEM, HYBRID_SYSTEM_DRAFT, draft_text, user_message
from .schema import PLAN_SCHEMA, HYBRID_SCHEMA, MAX_TASKS, FIELDS, ACTIONS

_COND = re.compile(r"\b(neu|truong hop|doi voi|boi vi|tre han|qua han|bi mat)\b")


@dataclass
class Task:
    action: str = "ask_field"
    procedure_id: str | None = None
    procedure_label: str = ""
    procedure_query: str = ""
    refers_to: str = "new"            # new | last
    fields: list = field(default_factory=list)
    quantity: str = "none"
    conditions: list = field(default_factory=list)
    context_facts: list = field(default_factory=list)
    evidence_demand: str = "none"
    relation: str = "independent"
    candidates: list = field(default_factory=list)     # [proc_id] để Box 4 kiểm lại
    uncertain: bool = False
    ambiguous: bool = False
    where: bool = False                                # "ở đâu" chung chung: address -> agency nếu cổng không ghi địa điểm (Policy)
    near: list = field(default_factory=list)           # >=3 ứng viên khác nhóm, điểm sát nhau -> Policy hỏi lại (luật)


@dataclass
class Plan:
    tasks: list = field(default_factory=list)
    needs_clarification: bool = False
    source: str = "rules"             # rules | llm | fallback
    llm_ms: float = 0.0
    note: str = ""
    llm_trace: dict = field(default_factory=dict)   # Phase 19: nhật ký Planner hybrid (-> trace["planner_llm"]); {} khi mode=rules
    ctx: dict = field(default_factory=dict)     # quyết định ngữ cảnh (follow_up|new_related|return|correction|story|independent) + lý do
    intent: str = ""                            # phương án C (reader.py): ý định model đọc được ("" = thủ tục / không đọc); Policy từ chối khi khác "thu_tuc"
    state: dict = field(default_factory=dict)   # ConvState SAU lượt này (đề xuất; orchestrator ghi lại theo thủ tục thực sự trả lời)

    def to_dict(self):
        return asdict(self)


_idx: Index | None = None
_conn = None
_idx_path: str | None = None
_idx_lock = threading.Lock()


def _index():
    """Chỉ mục tên thủ tục của DB đang dùng. G2.1: khoá theo đường dẫn DB của phiên bản — đổi phiên bản (System 4 đổi con trỏ)
    thì lượt sau tự dựng lại chỉ mục, không cần khởi động lại. Kết nối cũ không đóng ngay (lượt đang chạy có thể còn dùng)."""
    global _idx, _conn, _idx_path
    path = str(data_api.active_db_path())
    if _idx is None or _idx_path != path:
        with _idx_lock:
            if _idx is None or _idx_path != path:
                conn = sqlite3.connect(path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                from system3.retrieval import query as _q
                _q._known_cache = (None, set())   # từ vựng tách chữ dính tính lại theo kho mới
                idx = Index(conn)
                _conn, _idx, _idx_path = conn, idx, path
    return _idx


def _label(conn, proc_id):
    r = conn.execute("SELECT name FROM procedures WHERE proc_id=? AND status='active'", (proc_id,)).fetchone()
    return r[0] if r else proc_id


def _from_rules(segs: list[Segment], conn) -> Plan:
    tasks = []
    for s in segs[:MAX_TASKS]:
        if s.reason == "chitchat":
            tasks.append(Task(action="chitchat"))
            continue
        if not s.proc_id:
            tasks.append(Task(action="out_of_scope", procedure_query=s.query.procedure_query,
                              candidates=[h.proc_id for h in s.hits[:5]]))
            continue
        act = "ask_field" if s.query.fields else "find_procedure"
        t = Task(action=act, procedure_id=s.proc_id, procedure_label=_label(conn, s.proc_id),
                 procedure_query=s.query.procedure_query, refers_to="last" if s.inherited else "new",
                 fields=list(s.query.fields), candidates=[h.proc_id for h in s.hits[:5]],
                 uncertain=s.uncertain, ambiguous=s.ambiguous, near=list(s.near), relation=s.relation, where=bool(s.query.flags.get("where")))
        if "fees" in t.fields:
            t.quantity = "amount"
        elif "processing_time" in t.fields:
            t.quantity = "duration"
        if s.query.flags.get("condition"):
            t.conditions = [s.query.flags["condition"]]       # hoàn cảnh người dùng nêu ("nếu X thì ..."): Policy kiểm căn cứ, Answerer đối chiếu condition_index
        if "meta" in t.fields or s.evidence != "none":
            t.evidence_demand = "legal_basis"
        tasks.append(t)
    return Plan(tasks=tasks, source="rules")


def _llm_reason(text: str, segs: list[Segment], has_history: bool) -> str:
    """Lý do gọi LLM ('' = dùng luật). Đo trên 185 câu: LLM 4B chỉ thắng khi có điều kiện/ngữ cảnh kể;
    uncertain/ambiguous đơn thuần để luật xử lý (LLM làm tụt fields, 2-6 s/lần)."""
    if any(s.reason == "chitchat" for s in segs):
        return ""
    if _COND.search(fold(text)):
        return "conditional"
    if len(text) > 90 and (text.count(".") + text.count("?")) >= 2:
        return "multi_sentence"
    # ponytail: không chọn được thủ tục chỉ gọi LLM khi có lịch sử (câu nối tiếp); câu đơn lẻ ngoài phạm vi để luật trả out_of_scope
    if has_history and any(not s.proc_id for s in segs):
        return "no_procedure"
    return ""


def _cand_list(segs: list[Segment]) -> list[dict]:
    """Ứng viên cho LLM: hợp top-3 của từng đoạn (điểm đủ, không cờ lạ), tối đa 9."""
    cands, seen = [], set()
    for s in segs:
        for h in s.hits[:3]:
            if h.proc_id not in seen and not h.flags and h.score >= ACCEPT_SCORE - 0.1:
                seen.add(h.proc_id)
                cands.append({"proc_id": h.proc_id, "label": h.name[:110],
                              "group": s.text[:60] if len(segs) > 1 else ""})
    return cands[:9]


def _mk_task(pid: str, fields: list, label_: str) -> Task:
    return Task(action="ask_field" if fields else "find_procedure", procedure_id=pid, procedure_label=label_, fields=list(fields),
                quantity="amount" if "fees" in fields else ("duration" if "processing_time" in fields else "none"), candidates=[pid])


def _hybrid(rule_plan: Plan, turns, question, segs, res, conn, last_proc, facts, llm_chat_json) -> Plan:
    """Kế hoạch luật + đề xuất Qwen3-4B (timeout PLANNER_LLM_TIMEOUT). Trả rule_plan đã (có thể) sửa; ghi rule_plan.llm_trace.
    ponytail: chạy đồng bộ trong Planner (Policy cần kế hoạch cuối, không có bước độc lập đáng kể để chồng); thread chỉ để hết hạn cứng theo đồng hồ thật.
    Nâng cấp: bắt đầu LLM ngay sau resolve và làm việc phụ (nạp facts, mở DB) trong lúc chờ."""
    import config
    from answer.answerer import FIELD_TITLE
    cfg = hybrid.get_config()
    tr = rule_plan.llm_trace = {"mode": "hybrid", "called": False, "threshold": cfg["confidence"], "timeout_s": cfg["timeout"], "draft": cfg["draft"],
                                "model": __import__("core.llm", fromlist=["model_name"]).model_name(), "rule_plan": hybrid._summ(rule_plan.tasks)}
    if any(s.reason == "chitchat" for s in segs) or any(s.reason == "order_unknown" for s in segs):
        tr.update(skip="chitchat/thứ tự không rõ: luật quyết", decision="none", final_plan=tr["rule_plan"])
        return rule_plan
    cands = _cand_list(segs)
    for s in segs:       # thủ tục luật đã chọn luôn có trong danh sách (kể cả điểm thấp / kế thừa) để LLM có thể đồng ý
        if s.proc_id and s.proc_id not in {c["proc_id"] for c in cands}:
            cands.append({"proc_id": s.proc_id, "label": _label(conn, s.proc_id)[:110], "group": ""})
    last = next((s.proc_id for s in segs if s.inherited and s.proc_id), None) or last_proc
    hist = [f"{'Người dùng' if t['role'] == 'user' else 'Trợ lý'}: {t['text'][:120]}" for t in turns[:-1]]
    draft = ""
    if cfg["draft"]:
        ix = {c["proc_id"]: i for i, c in enumerate(cands)}
        draft = draft_text([{"cand": -2 if t.refers_to == "last" and t.procedure_id == last else ix.get(t.procedure_id, -1), "fields": t.fields} for t in rule_plan.tasks])
    msg = user_message(question, cands, _label(conn, last) if last else "", facts or [], hist, draft)
    if llm_chat_json is None:
        from core.llm import chat_json as llm_chat_json
    raw, info = hybrid.ask(HYBRID_SYSTEM_DRAFT if cfg["draft"] else HYBRID_SYSTEM, msg, llm_chat_json, cfg["timeout"], config.PLANNER_LLM_NUM_PREDICT, HYBRID_SCHEMA)
    tr.update(called=True, ms=info["ms"], timeout=info["timeout"], error=info["error"], cached=info["cached"])
    rule_plan.llm_ms = info["ms"]
    if raw is None:
        tr.update(decision="none", reason="LLM lỗi/quá hạn/JSON hỏng: giữ kế hoạch luật", final_plan=tr["rule_plan"])
        return rule_plan
    try:
        conf = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    llm = hybrid.parse_tasks(raw, cands, last, conn, set(FIELD_TITLE) - {"legal_basis"})
    ops = hybrid.diff(rule_plan.tasks, llm)
    from policy import check

    def vet(p):
        r = check(p, user_text=question, conn=conn, facts=facts or [])
        return r.behavior, [t.route for t in r.tasks]
    hybrid.merge(rule_plan, ops, conf, cfg["confidence"], conn, set(FIELD_TITLE) - {"legal_basis"}, vet, _label, _mk_task)
    acc = sum(1 for o in ops if o["accepted"])
    tr.update(confidence=conf, llm_tasks=[{"action": t["action"], "proc": t["pid"], "fields": t["fields"]} for t in llm], proposals=ops,
              decision=("none" if not ops else "accepted" if acc == len(ops) else "partial" if acc else "rejected"),
              changed=bool(acc), final_plan=hybrid._summ(rule_plan.tasks))
    return rule_plan


def _semantic(rule_plan: Plan, question: str, segs: list[Segment], conn) -> None:
    """Phương án B (24/10, retrieval/semantic.py): reranker chấm lại thủ tục cho câu hỏi ĐẦU (không kế thừa ngữ cảnh) mà luật chọn
    tối đa một thủ tục, hoặc câu kể dài (> 30 chữ). Điểm tốt nhất dưới ngưỡng -> không có thủ tục phù hợp; thủ tục khác hơn hẳn -> đổi.
    Nhiều lượt, xã giao, chọn theo thứ tự, câu ngắn hỏi nhiều thủ tục: giữ nguyên luật. Bật bằng S3_SEMANTIC=1."""
    from system3.retrieval import semantic
    if not semantic.enabled() or not segs or any(s.reason in ("chitchat", "order_unknown") or s.inherited for s in segs):
        return
    direct = [t for t in rule_plan.tasks if t.procedure_id]
    if len(direct) > 1 and len(question.split()) <= 30:
        return
    rule_ids = [h.proc_id for s in segs for h in s.hits[:5]]
    rule_pick = direct[0].procedure_id if direct else None
    try:
        d = semantic.decide(conn, semantic.query_text(question, segs), rule_ids, rule_pick)
    except Exception as exc:        # model / Ollama lỗi -> giữ kế hoạch luật (không làm hỏng câu trả lời)
        rule_plan.llm_trace["semantic"] = {"error": str(exc)[:200]}
        return
    rule_plan.llm_trace["semantic"] = d
    ranked = [pid for pid, _ in d["ranked"]]
    if d["action"] == "none":
        rule_plan.tasks = [Task(action="out_of_scope", procedure_query=segs[0].query.procedure_query, candidates=ranked[:5])]
        rule_plan.note = "semantic:none"
    elif d["action"] in ("swap", "rescue"):
        fields = list(dict.fromkeys(f for t in rule_plan.tasks for f in t.fields))
        t = _mk_task(d["pick"], fields, _label(conn, d["pick"]))
        t.candidates = [d["pick"]] + [x for x in ranked if x != d["pick"]][:4]
        rule_plan.tasks = [t]
        rule_plan.note = "semantic:" + d["action"]


def _reader(rule_plan: Plan, question: str, segs: list[Segment], conn) -> None:
    """Phương án C (24/10, reader.py): model 4B phân loại ý định + gọi tên thủ tục bằng chữ; luật xếp hạng TÊN đó trên cùng kho.
    Chỉ câu hỏi đầu (không kế thừa ngữ cảnh), không xã giao. Bật bằng S3_READER=1."""
    from . import reader
    if not reader.enabled() or not segs or any(s.reason in ("chitchat", "order_unknown") or s.inherited for s in segs):
        return
    r = reader.read(question)
    rule_plan.llm_trace["reader"] = r
    if r is None:
        return
    if r["intent"] != "thu_tuc":
        if os.environ.get("S3_READER_INTENT", "1") == "1":       # =0: bóc tách, chỉ dùng TÊN thủ tục model đọc, bỏ phân loại ý định
            rule_plan.intent = r["intent"]
        return
    name = r["procedure"].strip()
    direct = [t for t in rule_plan.tasks if t.procedure_id]
    if not name or (len(direct) > 1 and len(question.split()) <= 30):
        return
    from system3.retrieval.query import understand
    idx = _index()
    hits = idx.rank(understand(conn, name, idx.syn), limit=5)
    top = hits[0] if hits else None
    if not top or top.flags or top.score < ACCEPT_SCORE or top.cov < 0.5:
        return
    top3 = [h.proc_id for h in hits[:3]]
    if direct and direct[0].procedure_id in top3:
        return            # luật trên cả câu đã chọn một thủ tục khớp tên model đọc: giữ
    fields = list(dict.fromkeys(f for t in rule_plan.tasks for f in t.fields))
    t = _mk_task(top.proc_id, fields, _label(conn, top.proc_id))
    t.candidates = top3
    rule_plan.tasks = [t]
    rule_plan.note = "reader:swap"


def plan(turns: list[dict], *, last_proc: str | None = None, facts: list[str] | None = None,
         use_llm: bool | None = None, llm_chat_json=None, shown: list[dict] | None = None, state: dict | None = None,
         mode: str | None = None) -> Plan:
    # ponytail: Planner chạy LUẬT mặc định (đo: LLM 4B không tăng top-1, chậm 2-6 s); S3_PLANNER_LLM=1 mới bật nhánh LLM. LLM chỉ còn sinh chữ ở Answerer.
    if use_llm is None:
        use_llm = os.environ.get("S3_PLANNER_LLM") == "1"
    idx = _index()
    conn = _conn
    question = [t for t in turns if t["role"] == "user"][-1]["text"]
    res = resolve(idx, turns, shown=shown, state=state)
    segs = res.segments
    rule_plan = _from_rules(segs, conn)
    rule_plan.ctx, rule_plan.state = res.ctx, res.state.to_dict() if res.state else {}
    _semantic(rule_plan, question, segs, conn)
    _reader(rule_plan, question, segs, conn)
    if mode is None:
        mode = hybrid.get_config()["mode"]
    if mode == "hybrid":          # Phase 19: luật luôn có kế hoạch; LLM nền chỉ sửa khi confidence >= ngưỡng và qua kiểm Policy/dữ liệu
        return _hybrid(rule_plan, turns, question, segs, res, conn, last_proc, facts, llm_chat_json)
    reason = _llm_reason(question, segs, len(turns) > 1) if use_llm else ""
    if not reason or any(s.reason == "order_unknown" for s in segs):   # 'cái thứ hai' mà không có danh sách: không để LLM đoán
        return rule_plan

    cands = _cand_list(segs)
    last = next((s.proc_id for s in segs if s.inherited and s.proc_id), None) or last_proc
    last_label = _label(conn, last) if last else ""
    hist = [f"{'Người dùng' if t['role'] == 'user' else 'Trợ lý'}: {t['text'][:120]}" for t in turns[:-1]]
    msg = user_message(question, cands, last_label, facts or [], hist)
    if llm_chat_json is None:
        from core.llm import chat_json as llm_chat_json
    t0 = time.perf_counter()
    try:
        from config import PLANNER_NUM_PREDICT, PLANNER_TIMEOUT
        raw = llm_chat_json(SYSTEM, msg, schema=PLAN_SCHEMA, think=False, timeout=PLANNER_TIMEOUT,
                            num_predict=PLANNER_NUM_PREDICT)
    except Exception as exc:        # Ollama sập/timeout cứng -> plan bằng luật (guardrail 12)
        rule_plan.source, rule_plan.note = "fallback", f"llm_error({reason}): {exc}"[:200]
        rule_plan.llm_ms = round((time.perf_counter() - t0) * 1000)
        return rule_plan
    ms = (time.perf_counter() - t0) * 1000
    out = _from_llm(raw, cands, last, conn, rule_plan, segs, res.chitchat)
    out.llm_ms, out.note = round(ms), f"{reason}:{out.note}" if out.note else reason
    out.ctx, out.state = rule_plan.ctx, rule_plan.state
    return out


def _from_llm(raw: dict, cands: list[dict], last: str | None, conn, fallback: Plan, segs=None, rule_chitchat=False) -> Plan:
    tasks_raw = raw.get("tasks") if isinstance(raw, dict) else None
    if not tasks_raw:
        fallback.source, fallback.note = "fallback", "llm_empty"
        return fallback
    tasks = []
    rule_fields = [list(s.query.fields) for s in (segs or [])]
    union = sorted({f for fl in rule_fields for f in fl}, key=FIELDS.index)
    for j, r in enumerate(tasks_raw[:MAX_TASKS]):
        act = r.get("action") if r.get("action") in ACTIONS else "ask_field"
        c = r.get("cand", -1)
        pid, refers = None, "new"
        if c == -2 and last:
            pid, refers = last, "last"
        elif isinstance(c, int) and 0 <= c < len(cands):
            pid = cands[c]["proc_id"]
        # Đồng thuận: luật đã chọn chắc (không mơ hồ) mà LLM chọn khác -> giữ luật; LLM chỉ được PHỦ QUYẾT khi luật không chắc.
        # (đo ở eval: LLM 4B ghi đè lựa chọn đúng của luật làm top-1 tụt 84% -> 82%)
        sg = segs[j] if segs and len(segs) == len(tasks_raw) else None
        if sg is not None and sg.proc_id and not sg.ambiguous and act not in ("chitchat", "provide_info", "correct_previous"):
            if pid != sg.proc_id and (pid is not None or not sg.uncertain):
                pid = sg.proc_id
        fl = [f for f in r.get("fields", []) if f in FIELDS]
        # Fields: luật cue đáng tin hơn 4B (đo: LLM liệt kê cả 11 mục / bỏ sót). Dùng luật khi có; LLM chỉ khi luật không bắt được gì.
        if j < len(rule_fields) and rule_fields[j]:
            fl = rule_fields[j]
        elif len(tasks_raw) == 1 and union:
            fl = union
        elif len(fl) > 4:
            fl = fl[:4]
        if act == "chitchat" and not rule_chitchat:      # 4B hay gọi mọi câu lạc đề là chitchat
            act, pid = "out_of_scope", None
        if pid is None and act in ("ask_field", "find_procedure", "check_condition"):
            act = "out_of_scope"
        tasks.append(Task(action=act, procedure_id=pid, procedure_label=_label(conn, pid) if pid else "",
                          refers_to=refers, fields=fl, quantity=r.get("quantity", "none"),
                          conditions=list(r.get("conditions", [])), context_facts=list(r.get("facts", [])),
                          evidence_demand=r.get("evidence", "none"), relation=r.get("relation", "independent"),
                          candidates=[x["proc_id"] for x in cands]))
    return Plan(tasks=tasks, needs_clarification=bool(raw.get("clarify")), source="llm")

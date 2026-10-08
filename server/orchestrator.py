"""Box 1-2: điều phối một lượt hỏi-đáp. pre_check -> Planner -> Policy/Router -> Answerer -> cập nhật bộ nhớ.

Hợp đồng trả về (giữ nguyên từ bản stub):
  {"kind": answer|clarify|apologize|chitchat|error, "blocks": [...], "clarify": None|{question, options[str], allow_free_text, meta},
   "plan": dict, "trace": dict}
Hàm chạy trong thread của hàng đợi (đồng bộ, 1 worker).
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field

from answer import answer
from db import store
from planner import plan as make_plan
from policy import check, mask_pii, pre_check
from system3.data import api as data_api
from system3.data.textutil import fold
from system3.retrieval.context import ConvState
from system3.retrieval.refs import ordinal, pick


@dataclass
class Turn:
    conversation_id: str
    text: str
    reply_to: int | None = None            # message_id của thẻ clarify đang trả lời
    history: list[dict] = field(default_factory=list)          # <=5 lượt gần nhất, chưa gồm text này
    session_facts: list[dict] = field(default_factory=list)    # [{kind, text}]
    shown_procedures: list[dict] = field(default_factory=list) # [{proc_id, label, ordinal}]
    reply_to_clarify: dict | None = None   # thẻ clarify của reply_to (nếu có)
    state: dict | None = None              # ConvState dạng dict; None = đọc từ DB (rồi None nữa = dựng lại từ history)
    memory: dict | None = None             # Phase 26: {subjects:set, label} từ user_memory.for_policy; None = không có hồ sơ (hành vi cũ)
    pick_proc: str | None = None           # Phase 31: nút "dạng khác" gửi kèm proc_id đã chọn (không phải câu hỏi mới nên không được hỏi lại)


def flat_text(r: dict) -> str:
    """Nội dung tin nhắn trợ lý lưu vào lịch sử. Thẻ hỏi lại kèm danh sách ĐÁNH SỐ ("1) A 2) B"): lượt sau người dùng gõ "cái thứ hai"
    thì retrieval.refs.options_from_text đọc lại đúng các lựa chọn của thẻ (trước đây chỉ lưu câu hỏi nên "cái thứ hai" trỏ nhầm vào danh sách đã trả lời)."""
    flat = "\n\n".join(f"{b.get('title', '')}\n{b['text']}".strip() for b in r.get("blocks", []))
    clar = r.get("clarify")
    if not flat and clar:
        flat = (clar.get("question", "") + " " + " ".join(f"{i}) {o}" for i, o in enumerate(clar.get("options", []), 1))).strip()
    return flat


def _turns(turn: Turn, text: str) -> list[dict]:
    hist = [{"role": m["role"], "text": m["content"]} for m in turn.history]
    return hist + [{"role": "user", "text": text}]


def _resolve_clarify(turn: Turn) -> tuple[str, str | None]:
    """Trả lời thẻ hỏi lại: nút bấm -> chốt thẳng thủ tục; ô gõ -> ghép với câu hỏi gốc, Planner tự hiểu (KHÔNG hỏi lần 2)."""
    cl = turn.reply_to_clarify or {}
    meta = cl.get("meta") or {}
    ids = meta.get("option_ids") or {}
    if turn.text in ids:
        return meta.get("original_question", turn.text), ids[turn.text]
    o = ordinal(turn.text)                 # gõ "cái thứ hai": trỏ vào danh sách nút của thẻ (đúng thứ tự hiển thị)
    if o and ids:
        i = pick(o[0], len(ids))
        if i is not None:
            return f"{meta.get('original_question', '')} {turn.text}".strip(), list(ids.values())[i]
    return (f"{meta.get('original_question', '')} {turn.text}").strip(), None


_RESET = ("hoi viec khac", "chu de khac", "chu de moi", "quen di", "bat dau lai")
_RESET_RE = re.compile(r"(?<![0-9a-z])(?:" + "|".join(_RESET) + r")(?![0-9a-z])")


def _reset_request(text: str) -> str | None:
    """Luật đơn giản (không LLM): người dùng nói rõ chuyển việc -> phần còn lại của câu ("" nếu chỉ là lệnh)."""
    f = fold(text)
    if not _RESET_RE.search(f):
        return None
    f = _RESET_RE.sub(" ", f)
    return " ".join(w for w in re.findall(r"[0-9a-z]+", f) if w not in ("nhe", "di", "oi", "minh", "toi", "ban"))


def _strip_reset(text: str) -> str:
    """Bỏ cụm 'hỏi việc khác'... khỏi câu GỐC (giữ dấu) để Planner không truy hồi theo chữ 'khác'/'mới'."""
    chars, idx = [], []
    for i, ch in enumerate(text):
        for g in (" " if ch.isspace() else fold(ch)):
            chars.append(g)
            idx.append(i)
    spans = []
    for m in _RESET_RE.finditer("".join(chars)):
        s, e = idx[m.start()], idx[m.end() - 1] + 1
        while e < len(text) and not fold(text[e]) and not text[e].isspace():
            e += 1
        spans.append((s, e))
    for s, e in reversed(spans):
        text = text[:s] + " " + text[e:]
    return re.sub(r"\s+", " ", text).strip(" \t,;:.-–—!?")



def _head(conn, pid: str | None) -> str | None:
    fam = data_api.family_of(conn, pid) if pid else None
    return fam["head"] if fam else None


def _facts_for(conn, session_facts: list[dict], pids: list[str]) -> list[str]:
    """Fact còn hiệu lực cho các thủ tục này: cùng family, hoặc fact cũ không gắn thủ tục.
    ponytail: so family với mọi pid; không có pid nào (chưa biết thủ tục) -> giữ hết."""
    heads = {_head(conn, p) for p in pids if p}
    return [f["text"] for f in session_facts
            if not heads or not f.get("proc_id") or _head(conn, f["proc_id"]) in heads]


def handle_turn(turn: Turn) -> dict:
    t0 = time.perf_counter()
    text, forced_pid = turn.text, None
    answered_clarify = bool(turn.reply_to_clarify)
    if answered_clarify:
        text, forced_pid = _resolve_clarify(turn)
    elif turn.pick_proc:                   # Phase 31: bấm nút "dạng khác" = chọn thẳng thủ tục đó (tên dạng mặc định trùng tên chung của họ, gửi như câu hỏi mới sẽ bị hỏi lại)
        answered_clarify, forced_pid = True, turn.pick_proc
    elif _reset_request(text) is not None:
        rest = _reset_request(text)
        store.reset_session(turn.conversation_id)
        turn.session_facts, turn.shown_procedures, turn.state = [], [], None
        if len(rest.split()) < 2:
            return {"kind": "chitchat", "clarify": None, "plan": {}, "trace": {"question": "", "reset": True},
                    "blocks": [{"title": "", "sources": [],
                                "text": "Mình đã bỏ qua các thông tin bạn kể trước đó. Bạn muốn hỏi về thủ tục nào?"}]}
        text = _strip_reset(text) or text

    pc = pre_check(text)
    state = turn.state if turn.state is not None else store.get_state(turn.conversation_id)
    last_proc = (state or {}).get("topic") or (turn.shown_procedures[-1]["proc_id"] if turn.shown_procedures else None)
    conn = data_api.connect()
    facts = _facts_for(conn, turn.session_facts, [last_proc])
    # FINAL-PRODUCT: [B3] trace đã che PII; messages/plan_json thì chưa (mục 2)
    trace = {"question": mask_pii(turn.text), "flags": pc["flags"]}

    t1 = time.perf_counter()
    plan = make_plan(_turns(turn, pc["text"]), last_proc=last_proc, facts=facts, shown=turn.shown_procedures, state=state)
    trace["plan_ms"] = int((time.perf_counter() - t1) * 1000)
    trace["plan_source"] = plan.source
    if plan.llm_trace:                     # Phase 19: nhật ký Planner hybrid (gọi hay không, ms, đề xuất, confidence, chấp nhận/từ chối + lý do, kế hoạch cuối)
        trace["planner_llm"] = plan.llm_trace
    trace["ctx"] = {k: v for k, v in plan.ctx.items() if k != "state_before"}      # quyết định ngữ cảnh + lý do

    if forced_pid:                         # người dùng bấm chọn thủ tục: ghi đè mọi ứng viên
        for t in plan.tasks:
            if t.action in ("ask_field", "find_procedure", "check_condition", "out_of_scope"):
                t.procedure_id, t.refers_to, t.action = forced_pid, "last", ("ask_field" if t.fields else "find_procedure")
                break
        else:
            from planner.planner import Task
            plan.tasks.insert(0, Task(action="find_procedure", procedure_id=forced_pid))
        plan.needs_clarification = False

    pids = [t.procedure_id for t in plan.tasks if t.procedure_id]
    if pids:                               # đổi thủ tục khác family: fact cũ không được rò sang
        facts = _facts_for(conn, turn.session_facts, pids)
    routed = check(plan, user_text=pc["text"], conn=conn, facts=facts, flags=pc["flags"],
                   known_procs=[last_proc] if (last_proc and answered_clarify) else None, no_clarify=answered_clarify,
                   memory=None if answered_clarify else turn.memory)

    # Không hỏi lần 2: đã trả lời thẻ hỏi lại mà Planner vẫn xin hỏi -> lấy ứng viên đầu, nói rõ giả định.
    assumed = ""
    if routed.clarify and answered_clarify:
        pid = routed.clarify["options"][0]["proc_id"]
        plan.needs_clarification = False
        plan.tasks[0].procedure_id = pid
        plan.tasks[0].action = "ask_field" if plan.tasks[0].fields else "find_procedure"
        routed = check(plan, user_text=pc["text"], conn=conn, facts=facts, flags=pc["flags"], no_clarify=True)
        assumed = routed.tasks[0].procedure_label if routed.tasks else ""

    # Đưa tình huống đã kể ở lượt trước vào điều kiện khi dữ liệu thủ tục có nhắc (không bịa liên quan)
    for rt in routed.tasks:
        rfacts = _facts_for(conn, turn.session_facts, [rt.procedure_id]) if rt.route == "direct" else []
        if rfacts:
            cond_texts = [c["text"] for c in data_api.conditions(conn, rt.procedure_id)]
            for f in rfacts:
                if f not in rt.conditions and any(_ov(f, c) >= 0.6 for c in cond_texts):
                    rt.conditions.append(f)

    ans = answer(routed, conn=conn, question=turn.text, llm=_answer_llm())
    if assumed and ans["blocks"]:
        ans["blocks"].insert(0, {"title": "", "sources": [],
                                 "text": f"Mình hiểu bạn đang hỏi về «{assumed}». Nếu chưa đúng, bạn gõ lại tên thủ tục nhé."})

    mn = routed.memory_note                # Phase 26: nói rõ hồ sơ đã ảnh hưởng (người dùng sửa được: "bạn nói lại nhé")
    if mn and mn["kind"] in ("pick", "variant") and ans["blocks"]:
        what = "chọn" if mn["kind"] == "pick" else "chọn bản"
        ans["blocks"].insert(0, {"title": "", "sources": [],
                                 "text": f"Theo hồ sơ của bạn (đối tượng: {mn['subject']}) mình {what} «{mn['procedure']}». Nếu chưa đúng, bạn nói lại nhé."})
    if mn:
        trace["memory"] = mn

    clarify = ans.get("clarify")
    if clarify:                            # UI nhận options là chuỗi; mã thủ tục để trong meta
        clarify = {"question": clarify["question"], "allow_free_text": True,
                   "options": [o["label"] for o in clarify["options"]],
                   "meta": {"option_ids": {o["label"]: o["proc_id"] for o in clarify["options"]},
                            "original_question": text,
                            "fields": sorted({f for t in plan.tasks for f in t.fields})}}

    # ---- bộ nhớ: trạng thái hội thoại theo thủ tục THỰC SỰ đã trả lời (không theo đề xuất của resolve: biến thể mặc định, nút chọn, giả định)
    new_state = ConvState.from_dict(plan.ctx.get("state_before") or state)
    direct = [rt for rt in routed.tasks if rt.route == "direct"] if not clarify else []
    for rt in direct:
        new_state.note(rt.procedure_id, rt.fields)
    new_state.loose = bool((plan.state or {}).get("loose")) if direct else new_state.loose
    if not direct:
        new_state.story = list((plan.state or {}).get("story", new_state.story))
    store.set_state(turn.conversation_id, new_state.to_dict())
    trace["state"] = new_state.to_dict()
    # ---- bộ nhớ
    for rt in routed.tasks:
        if rt.route == "direct" and not clarify:
            store.add_shown(turn.conversation_id, rt.procedure_id, rt.procedure_label)
        for c in rt.context_facts:
            store.add_fact(turn.conversation_id, "fact", c, rt.procedure_id or "")

    trace.update(routed=routed.to_dict(), verify=ans["verify"], total_ms=int((time.perf_counter() - t0) * 1000),
                 llm_ms=plan.llm_ms)
    res = {"kind": ans["kind"] if not clarify else "clarify", "blocks": ans["blocks"], "clarify": clarify,
           "plan": plan.to_dict(), "trace": trace}
    if answered_clarify and forced_pid:    # Phase 26: gợi ý "Nhớ đối tượng ...?" (UI hỏi, người dùng bấm mới lưu)
        from user_memory import suggest_after_pick
        sg = suggest_after_pick(forced_pid, list(((turn.reply_to_clarify or {}).get("meta") or {}).get("option_ids", {}).values()), turn.memory)
        if sg:
            res["memory_suggest"] = sg
    return res


# FINAL-PRODUCT: [AI] công tắc AI là biến môi trường S3_USE_LLM của tiến trình (POST /config đổi cho mọi người). Bản cuối: quyết định nhóm có cho người dùng thường tắt AI không (mục 4)
def _answer_llm():
    """LLM chỉ có MỘT việc: sinh chữ (giải thích điều kiện, so sánh) ở Answerer; ý không qua verify bị bỏ, lỗi -> bản bằng code.
    ponytail: S3_USE_LLM=0 tắt hẳn (đo/độ trễ); câu trả lời chỉ gửi SAU khi verify xong (answer() chạy đồng bộ)."""
    if os.environ.get("S3_USE_LLM", "1") != "1":
        return None
    from core.llm import chat_json
    return chat_json


def _ov(a: str, b: str) -> float:
    import re
    ta = [t for t in re.findall(r"[0-9a-z]+", fold(a)) if len(t) > 1]
    tb = set(re.findall(r"[0-9a-z]+", fold(b)))
    return sum(1 for t in ta if t in tb) / len(ta) if ta else 0.0

"""Hiểu câu hỏi và quyết định đi đường nào: tra cứu / hỏi lại / trò chuyện / ngoài phạm vi.

Hai lời gọi LLM, cả hai JSON có schema, temperature 0 — không có luật bắt từ khoá:

    understand  ý định + câu hỏi độc lập + tỉnh/xã + thiếu gì + câu hỏi lại + truy vấn
    gate        MỘT quyết định hẹp: search | ask | greeting | other

Tách "có hỏi lại không" ra một bộ gác riêng vì đo được: mô hình 1.5B để một mình
quyết định trong JSON lớn thì hỏi lại gần như mọi câu (clarification accuracy 43%),
chặn cả những câu hỏi chung đã đủ để trả lời.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime

from config import (CLARIFY_ENABLED, PROFILE_MEMORY_ENABLED, SEARCH_MAX_QUERIES,
                    UNDERSTAND_FEWSHOT)
from core import llm
from domain.text import fold, tokenize
from prompts import templates as T

PROCEDURE_INTENTS = [i for i in T.INTENTS if i not in ("unknown", "chitchat", "out_of_scope")]


@dataclass
class Understanding:
    intent: str = "unknown"
    standalone_question: str = ""
    province: str = ""
    ward: str = ""
    missing_information: list[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarifying_question: str = ""
    search_queries: list[str] = field(default_factory=list)
    gate: str = ""               # search | ask | greeting | other
    route: str = "search"        # search | clarify | chitchat | out_of_scope

    def as_dict(self) -> dict:
        return asdict(self)


def _s(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _similar(a: str, b: str) -> float:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def _copied_example(raw: dict, question: str, year: int) -> bool:
    """Mô hình nhỏ gặp câu lạ hay chép nguyên JSON của một ví dụ mẫu."""
    got = fold(_s(raw.get("standalone_question")))
    return any(got == fold(answer["standalone_question"]) and _similar(message, question) < 0.5
               for message, _, answer in T.understand_examples(year))


def understand(question: str, history: list[dict], summary: str, profile: dict) -> Understanding:
    now = datetime.now()
    system = T.understand_system(now.strftime("%d/%m/%Y"), now.year)
    user = T.understand_user(question, history, summary, profile)

    raw = llm.chat_json("understand", system, user, T.UNDERSTAND_SCHEMA,
                        T.understand_example_messages(now.year) if UNDERSTAND_FEWSHOT else None)
    if UNDERSTAND_FEWSHOT and _copied_example(raw, question, now.year):
        raw = llm.chat_json("understand", system, user, T.UNDERSTAND_SCHEMA)   # chạy lại không có ví dụ

    intent = _s(raw.get("intent")) or "unknown"
    if intent not in T.INTENTS:
        intent = "unknown"
    queries = list(dict.fromkeys(_s(q) for q in raw.get("search_queries") or [] if _s(q)))
    return Understanding(
        intent=intent,
        standalone_question=_s(raw.get("standalone_question")) or question,
        province=_s(raw.get("province")),
        ward=_s(raw.get("ward")),
        missing_information=[_s(x) for x in raw.get("missing_information") or [] if _s(x)][:4],
        needs_clarification=bool(raw.get("needs_clarification")),
        clarifying_question=_s(raw.get("clarifying_question")),
        # chừa một chỗ cho truy vấn bám nguồn chính thống (core/evidence.py)
        search_queries=queries[:max(1, SEARCH_MAX_QUERIES - 1)],
    )


def gate(question: str, history: list[dict]) -> str:
    raw = llm.chat_json("understand", T.GATE_SYSTEM, T.gate_user(question, history),
                        T.GATE_SCHEMA, T.gate_example_messages())
    decision = _s(raw.get("decision"))
    return decision if decision in ("search", "ask", "greeting", "other") else "search"


def analyze(question: str, history: list[dict], summary: str, profile: dict) -> Understanding:
    u = understand(question, history, summary, profile)
    u.gate = gate(question, history)
    small_talk = u.intent in ("chitchat", "out_of_scope")
    # Thủ tục CỤ THỂ (không tính "other") -> tin bộ hiểu ý định khi hai bộ bất đồng.
    specific = u.intent in PROCEDURE_INTENTS and u.intent != "other"
    # Chỉ CHẶN để hỏi lại khi cả hai bộ cùng thấy thiếu thông tin.
    wants_clarify = u.needs_clarification or u.intent == "unknown" or small_talk

    if u.gate == "other" and not specific:
        # Nhờ làm việc ngoài phạm vi -> câu từ chối CỐ ĐỊNH. Không giao cho mô hình
        # tự từ chối: mô hình nhỏ làm theo yêu cầu (đã thấy nó làm thơ thật).
        u.route = "out_of_scope"
    elif u.gate == "greeting" and not specific:
        u.route = "chitchat"
    elif u.gate == "search" and small_talk:
        # Bất đồng: bộ gác thấy là câu hỏi thủ tục. Câu rất ngắn kiểu "cảm ơn nha"
        # thì tin bộ hiểu ý định; còn lại nghiêng về TRA CỨU — trả lời nhầm một lời
        # chào rẻ hơn nhiều so với từ chối một câu hỏi thủ tục thật.
        if len(question.split()) <= 5:
            u.route = "chitchat" if u.intent == "chitchat" else "out_of_scope"
        else:
            u.route = "search"
            u.standalone_question, u.search_queries = question, []
    elif u.gate == "ask" and wants_clarify and CLARIFY_ENABLED and not _just_clarified(history):
        u.route = "clarify"
        if not u.clarifying_question or small_talk:
            u.clarifying_question = T.GENERIC_CLARIFY
    else:
        u.route = "search"
    return u


def _just_clarified(history: list[dict]) -> bool:
    """Trợ lý vừa hỏi lại ở lượt trước -> không hỏi dồn, tra cứu với thông tin đang có."""
    last = next((m for m in reversed(history) if m["role"] == "assistant"), None)
    return bool(last and last.get("kind") == "clarify")


# --------------------------------------------------------------------------
# bộ nhớ dài hạn: tỉnh/thành, xã/phường của người dùng
# --------------------------------------------------------------------------
_PREFIX_RE = re.compile(r"^(thanh pho|tp|tinh|phuong|xa|dac khu|thi tran)\s+")
_ALIASES = {"ho chi minh": ["hcm", "tphcm", "sai gon", "saigon"], "ha noi": ["hn", "hanoi"]}


def _grounded(value: str, user_text: str) -> bool:
    """Chỉ ghi nhớ địa phương người dùng THẬT SỰ đã gõ — mô hình nhỏ hay chép ví dụ."""
    core = _PREFIX_RE.sub("", re.sub(r"[^a-z0-9 ]", " ", fold(value)).strip()).strip()
    if not core:
        return False
    hay = f" {re.sub(r'[^a-z0-9]+', ' ', fold(user_text))} "
    if f" {core} " in hay:
        return True
    return any(canon in core and any(f" {a} " in hay for a in aliases)
               for canon, aliases in _ALIASES.items())


def profile_update(u: Understanding, question: str, history: list[dict], profile: dict) -> dict:
    if not PROFILE_MEMORY_ENABLED:
        return {}
    user_text = " ".join([question] + [m["content"] for m in history if m["role"] == "user"])
    changes = {}
    for key in ("province", "ward"):
        value = getattr(u, key)
        if value and value != (profile or {}).get(key) and _grounded(value, user_text):
            changes[key] = value
    return changes

"""Điều phối. File này CHỈ ráp các tầng lại, không chứa logic nghiệp vụ riêng.

Luồng:
    xã giao? -> trả lời ngắn
    đang chờ trả lời câu hỏi lại? -> ghép với câu hỏi gốc
    truy hồi -> phân tầng
        A: in thẳng bản ghi (mặc định không qua LLM -> không thể bịa)
        B: hỏi lại cho rõ
        C: tra nguồn chính thống -> LLM tóm tắt
        D: kiến thức chung, ghi rõ KHÔNG chắc chắn
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from config import FACTCHECK_MAX_RETRIES
from core import factcheck, formatter, llm, retrieval, smalltalk, websearch
from core.tiers import Tier, decide
from domain.records import Procedure
from prompts import templates

TIER_A_STYLE = "template"      # "template" (an toàn) | "llm" (mượt hơn, có kiểm chứng)


@dataclass
class AnswerPlan:
    tier: Tier
    confidence: float = 0.0
    text: str | None = None            # có sẵn -> stream thẳng
    system: str | None = None          # cần LLM -> stream từ model
    user: str | None = None
    history: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    record: Procedure | None = None
    sources: list[str] = field(default_factory=list)
    factcheck_summary: str = ""
    pending_to_set: dict | None = None   # caller chịu trách nhiệm lưu (DB hay RAM)
    top_row_id: int | None = None        # thủ tục đang nói tới, để nhớ ngữ cảnh


def _resolve_pending(question: str, pending: dict):
    """Người dùng trả lời câu hỏi lại của tầng B: '1', '2' hoặc mô tả rõ hơn."""
    choice = re.fullmatch(r"\s*([1-3])\s*[.)]?\s*", question or "")
    options = pending.get("row_ids") or []
    if choice:
        i = int(choice.group(1)) - 1
        if 0 <= i < len(options):
            return options[i], pending.get("question", "")
    return None, pending.get("question", "")


FOLLOWUP_MAX_WORDS = 9      # câu ngắn hơn mức này được coi là hỏi tiếp


def build(question: str, *, pending: dict | None = None,
          history: list | None = None, context_hint: str = "") -> AnswerPlan:
    """Thuần nghiệp vụ: không đọc/ghi CSDL, không biết gì về phiên đăng nhập.

    `pending` là trạng thái "đang chờ làm rõ" do caller lấy ra và truyền vào;
    nếu cần đặt lại, plan.pending_to_set sẽ chứa payload để caller tự lưu.
    """
    question = (question or "").strip()
    history = history or []
    original = ""

    # -- đang chờ người dùng làm rõ (XÉT TRƯỚC bộ lọc xã giao) -------------
    # v5: trước đây bộ lọc xã giao chạy trước, nên khi tầng B đang hỏi lại mà
    # người dùng gõ "ok"/"vâng" thì câu đó bị nuốt thành lời xã giao và trạng
    # thái chờ (đã bị caller pop khỏi DB) biến mất im lặng.
    if pending:
        row_id, original = _resolve_pending(question, pending)
        if row_id is not None:
            from domain.records import by_row_id
            record = by_row_id().get(row_id)
            if record:
                return AnswerPlan(tier=Tier.A_DATABASE, confidence=1.0,
                                  text=formatter.render_record(record), record=record)

    if smalltalk.is_smalltalk(question):
        return AnswerPlan(tier=Tier.A_DATABASE, text=smalltalk.reply(question),
                          confidence=1.0)

    if original:
        question = f"{original} {question}".strip()

    # Câu hỏi ngắn kiểu "tốn bao nhiêu tiền?" không đủ thông tin để truy hồi.
    # Ghép thêm tên thủ tục vừa nói tới thì nó tìm đúng bản ghi cũ.
    #
    # v5: điều kiện cũ CHỈ đếm số chữ. Vì vậy mọi câu ngắn — kể cả câu chia tay
    # — đều bị ghép tên thủ tục vừa nói tới, rồi truy hồi lại chính thủ tục đó
    # với độ tin cậy ~0.92 > TIER_A_MIN_CONFIDENCE. Chính tính năng làm cho
    # "hỏi tiếp" chạy đúng lại biến lời tạm biệt thành một thủ tục.
    # Nay bắt buộc câu ngắn đó phải THỰC SỰ hỏi về thủ tục: có từ hành chính,
    # hoặc là một câu hỏi khía cạnh trơ ("bao lâu", "ở đâu", "lệ phí").
    search_query = question
    if (context_hint
            and len(question.split()) <= FOLLOWUP_MAX_WORDS
            and (smalltalk.has_admin_signal(question)
                 or smalltalk.is_facet_followup(question))):
        search_query = f"{question} {context_hint}"

    candidates = retrieval.retrieve(search_query)
    tier = decide(candidates)
    top = candidates[0] if candidates else None
    confidence = top.confidence if top else 0.0

    # -- A: trả lời từ cơ sở dữ liệu ---------------------------------------
    if tier is Tier.A_DATABASE and top:
        if TIER_A_STYLE == "template":
            return AnswerPlan(tier=tier, confidence=confidence, candidates=candidates,
                              record=top.record, top_row_id=top.row_id,
                              text=formatter.render_record(top.record))
        return _generate_checked(question, candidates, tier, confidence)

    # -- B: hỏi lại cho rõ --------------------------------------------------
    if tier is Tier.B_CLARIFY and candidates:
        return AnswerPlan(tier=tier, confidence=confidence, candidates=candidates,
                          text=formatter.render_clarify(candidates),
                          top_row_id=top.row_id if top else None,
                          pending_to_set={
                              "question": question,
                              "row_ids": [c.row_id for c in candidates[:3]],
                          })

    # -- C: tra nguồn chính thống ------------------------------------------
    web = websearch.search(question)
    if web.ok:
        return AnswerPlan(tier=Tier.C_WEB, confidence=confidence, candidates=candidates,
                          sources=web.sources, history=history,
                          system=templates.SYSTEM_WEB,
                          user=templates.user_web(question, web.context))

    # -- D: kiến thức chung, nói rõ không chắc ------------------------------
    return AnswerPlan(tier=Tier.D_GENERAL, confidence=confidence, candidates=candidates,
                      history=history,
                      system=templates.SYSTEM_GENERAL,
                      user=templates.user_general(question))


def _generate_checked(question, candidates, tier, confidence) -> AnswerPlan:
    """Tầng A bản 'llm': sinh -> kiểm chứng bằng luật -> sinh lại -> bỏ cuộc về template."""
    record = candidates[0].record
    context = templates.build_context(candidates[:1])
    answer = llm.complete(templates.SYSTEM_RAG, templates.user_rag(question, context))
    result = factcheck.check(answer, record)

    attempts = 0
    while not result.ok and attempts < FACTCHECK_MAX_RETRIES:
        attempts += 1
        answer = llm.complete(
            templates.SYSTEM_RAG,
            templates.user_retry(question, context, result.summary()),
        )
        result = factcheck.check(answer, record)

    if not result.ok:
        return AnswerPlan(tier=tier, confidence=confidence, candidates=candidates,
                          record=record, text=formatter.render_record(record),
                          factcheck_summary=f"không đạt ({result.summary()}) -> in bản ghi gốc")

    return AnswerPlan(tier=tier, confidence=confidence, candidates=candidates,
                      record=record, text=answer, factcheck_summary="đạt")

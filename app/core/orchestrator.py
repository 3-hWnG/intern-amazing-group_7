"""Bộ điều phối — pipeline của docs/ARCHITECTURE.md + PLAN_target_state_verifier.md:

    ngữ cảnh (tóm tắt + lịch sử + hồ sơ người dùng + BỐI CẢNH THỦ TỤC)
      └─ HIỂU: ý định + MỤC TIÊU + tên thủ tục + truy vấn      (LLM, JSON)
      └─ GÁC : search | ask | greeting | other                  (LLM, 1 câu hỏi hẹp)
           ├─ greeting      -> đáp ngắn
           ├─ other         -> từ chối (câu cố định)
           ├─ ask           -> HỎI LẠI
           └─ search        -> MCP (truy vấn có mang mục tiêu) -> Evidence Pack
                └─ không có nguồn -> nói thật, không trả lời chay
                └─ SOẠN câu trả lời bám mục tiêu                (LLM)
                     └─ KIỂM CHỨNG (luật + LLM)
                          ├─ PASS -> trả lời
                          └─ FAIL -> tra bổ sung / viết lại -> vẫn FAIL: lược bỏ + cảnh báo

Thuần nghiệp vụ: không đọc/ghi CSDL (chat_routes lo), nên evaluate.py gọi thẳng được.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

import developer_mode
from config import MAX_VERIFY_RETRIES, VERIFIER_ENABLED
from core import answer, evidence, intent, llm, verifier
from prompts import templates as T


@dataclass
class TurnInput:
    question: str
    history: list[dict] = field(default_factory=list)   # {"role","content","kind"}
    summary: str = ""
    profile: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)           # bối cảnh thủ tục (giả thuyết)
    turn_index: int = 0
    conversation_id: int | None = None


@dataclass
class TurnResult:
    kind: str = "answer"        # answer | clarify | chitchat | out_of_scope | no_evidence | error
    text: str = ""
    draft: str = ""             # bản nháp TRƯỚC kiểm chứng (cho nhật ký truy nguyên)
    verdict: str = ""           # PASS | FAIL | "" (không kiểm chứng)
    intent: dict = field(default_factory=dict)
    evidence: dict | None = None
    sources: list[dict] = field(default_factory=list)
    verification: dict = field(default_factory=dict)
    profile_update: dict = field(default_factory=dict)
    state_update: dict = field(default_factory=dict)
    target_in_evidence: bool | None = None
    timings: dict = field(default_factory=dict)


def run_turn(inp: TurnInput, status: Callable[[str], None] = lambda _: None) -> TurnResult:
    dev = developer_mode.turn(inp.question, inp.conversation_id)
    res = TurnResult()
    clock = time.time()

    def lap(name: str, since: float) -> int:
        ms = int((time.time() - since) * 1000)
        res.timings[name] = res.timings.get(name, 0) + ms
        return ms

    try:
        # 1-2. hiểu ý định + mục tiêu + bối cảnh ---------------------------
        status("Đang phân tích câu hỏi…")
        t = time.time()
        u = intent.analyze(inp.question, inp.history, inp.summary, inp.profile,
                           inp.state, inp.turn_index)
        res.intent = u.as_dict()
        res.profile_update = intent.profile_update(u, inp.question, inp.history, inp.profile)
        res.state_update = intent.state_update(u, inp.state or {}, inp.turn_index)
        dev.event("understand", ms=lap("understand", t), **res.intent)

        if u.route == "chitchat":
            t = time.time()
            res.kind, res.text = "chitchat", answer.chitchat(inp.question, inp.history)
            dev.event("chitchat", ms=lap("answer", t))
            return res
        if u.route == "out_of_scope":
            res.kind, res.text = "out_of_scope", T.OUT_OF_SCOPE_TEXT
            return res

        # 3. hỏi lại khi thiếu thông tin ---------------------------------
        if u.route == "clarify":
            res.kind, res.text = "clarify", u.clarifying_question
            dev.event("clarify", missing=u.missing_information)
            return res

        # 4. tra cứu qua MCP -> Evidence Pack ------------------------------
        question = u.standalone_question or inp.question
        status("Đang tra cứu nguồn chính thống qua MCP…")
        t = time.time()
        pack = evidence.gather(question, u.search_queries, u.target, inp.conversation_id)
        res.evidence = pack
        res.target_in_evidence = evidence.mentions_target(pack, u.target)
        dev.event("search", ms=lap("search", t), transport=pack.get("transport", ""),
                  queries=pack.get("queries"), n_sources=len(pack.get("sources") or []),
                  target=u.target, target_in_evidence=res.target_in_evidence,
                  error=pack.get("error", ""), diagnostics="\n".join(pack.get("diagnostics") or []))
        if not pack.get("sources"):
            res.kind, res.text = "no_evidence", T.NO_EVIDENCE_TEXT
            return res

        # 5. soạn câu trả lời bám mục tiêu ---------------------------------
        status(f"Đã đọc {len(pack['sources'])} nguồn — đang soạn câu trả lời…")
        t = time.time()
        draft = answer.generate(inp.question, question, u.target, pack, inp.summary,
                                inp.history, inp.profile)
        res.draft = draft
        dev.event("answer", ms=lap("answer", t), chars=len(draft))

        # 6. kiểm chứng -> sửa ---------------------------------------------
        if VERIFIER_ENABLED:
            researched = False
            for attempt in range(MAX_VERIFY_RETRIES + 1):
                status("Đang kiểm chứng câu trả lời với nguồn…")
                t = time.time()
                v = verifier.verify(inp.question, question, u.target, pack, draft)
                dev.event("verify", ms=lap("verify", t), attempt=attempt,
                          verdict="PASS" if v.passed else "FAIL",
                          issues=v.rule_issues + v.unsupported_claims, soft=v.soft_issues,
                          answers_target=v.answers_target, explanation=v.explanation,
                          draft=draft[:600])
                if v.passed or attempt == MAX_VERIFY_RETRIES:
                    break
                if not v.evidence_sufficient and v.better_search_query and not researched:
                    status("Kiểm chứng chưa đạt — đang tra cứu bổ sung…")
                    t = time.time()
                    extra = evidence.gather(question, [v.better_search_query], u.target,
                                            None, official_bias=False)
                    pack = evidence.merge(pack, extra)
                    res.evidence, researched = pack, True
                    res.target_in_evidence = evidence.mentions_target(pack, u.target)
                    dev.event("research", ms=lap("search", t), query=v.better_search_query,
                              n_sources=len(pack["sources"]),
                              target_in_evidence=res.target_in_evidence)
                status("Kiểm chứng chưa đạt — đang viết lại câu trả lời…")
                t = time.time()
                draft = answer.generate(inp.question, question, u.target, pack, inp.summary,
                                        inp.history, inp.profile, fix_notes=v.fix_notes())
                res.draft = draft
                dev.event("rewrite", ms=lap("answer", t), chars=len(draft))
            res.verdict = "PASS" if v.passed else "FAIL"
            res.verification = v.as_dict()
            if not v.passed:
                draft = verifier.apply_fail_policy(draft, v, u.target, res.target_in_evidence)

        res.kind, res.text = "answer", draft
        res.sources = evidence.public_sources(pack, draft)
        return res

    except llm.LLMError as exc:
        res.kind = "error"
        res.text = ("Mình không kết nối được mô hình ngôn ngữ nên chưa trả lời được. "
                    f"Kiểm tra Ollama đang chạy và đã tải mô hình.\n\nChi tiết: {exc}")
        dev.event("error", note=str(exc))
        return res
    finally:
        res.timings["total"] = int((time.time() - clock) * 1000)
        dev.set(kind=res.kind, verdict=res.verdict, intent=res.intent.get("intent", ""),
                target=res.intent.get("target", ""),
                procedure=res.intent.get("procedure", ""),
                standalone=res.intent.get("standalone_question", ""),
                queries=(res.evidence or {}).get("queries", []),
                target_in_evidence=res.target_in_evidence,
                sources=[s.get("url") or s.get("title") for s in res.sources],
                timings=res.timings)
        dev.finish()

"""HỆ THỐNG 1 — WEB SEARCH. Pipeline đang chạy từ V10.2, không đổi logic.

Nút "Web search" trên giao diện bật đúng hệ thống này; tắt thì lượt hỏi đi vào
`system_retrieval.py` (Hệ thống 2 — CSDL nội bộ). Bộ chọn nằm ở
`orchestrator.py`. Sơ đồ đầy đủ: Documentation/ARCHITECTURE.md.

    ngữ cảnh (tóm tắt + lịch sử + hồ sơ người dùng)
      └─ HIỂU: ý định + ngữ cảnh + thiếu gì + truy vấn         (LLM, JSON)
           ├─ chitchat      -> đáp ngắn
           ├─ out_of_scope  -> từ chối lịch sự
           ├─ thiếu thông tin -> HỎI LẠI
           └─ TRA CỨU qua MCP -> Evidence Pack
                └─ không có nguồn -> nói thật, không trả lời chay
                └─ SOẠN câu trả lời từ Evidence Pack             (LLM)
                     └─ KIỂM CHỨNG (luật + LLM)
                          ├─ PASS -> trả lời
                          └─ FAIL -> tra bổ sung / viết lại (MAX_VERIFY_RETRIES) -> vẫn FAIL: cảnh báo

Thuần nghiệp vụ: không đọc/ghi CSDL (chat_routes lo), nên evaluate.py gọi thẳng được.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

import developer_mode
from config import MAX_VERIFY_RETRIES, SYSTEM_WEBSEARCH, VERIFIER_ENABLED
from core import answer, evidence, intent, llm, verifier
from core.turn import TurnInput, TurnResult
from prompts import templates as T


def run_turn(inp: TurnInput, status: Callable[[str], None] = lambda _: None) -> TurnResult:
    dev = developer_mode.turn(inp.question, inp.conversation_id)
    res = TurnResult(system=SYSTEM_WEBSEARCH)
    clock = time.time()

    def lap(name: str, since: float) -> int:
        ms = int((time.time() - since) * 1000)
        res.timings[name] = res.timings.get(name, 0) + ms
        return ms

    try:
        if inp.direct_search:
            # Cách 3: Người dùng đã chọn 1 gợi ý hoặc tự nhập nội dung tra cứu -> Đi thẳng vào MCP DuckDuckGo!
            question = inp.question
            u = intent.understand(question, [], "", {})
            search_queries = u.search_queries or [question]
            res.intent = {"intent": u.intent, "standalone_question": question, "search_queries": search_queries}
            dev.event("direct_search", query=question, intent=u.intent)
        else:
            # 1-2. hiểu ý định + ngữ cảnh ------------------------------------
            status("Đang phân tích câu hỏi…")
            t = time.time()
            u = intent.analyze(inp.question, inp.history, inp.summary, inp.profile)
            res.intent = u.as_dict()
            res.profile_update = intent.profile_update(u, inp.question, inp.history, inp.profile)
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
                res.choices = u.choices
                dev.event("clarify", missing=u.missing_information, choices=u.choices)
                return res

            question = u.standalone_question or inp.question
            search_queries = u.search_queries

        # 4. tra cứu qua MCP -> Evidence Pack ------------------------------
        status("Đang gửi DuckDuckGo qua MCP…" if inp.direct_search else "Đang tra cứu nguồn chính thống qua MCP…")
        t = time.time()
        pack = evidence.gather(question, search_queries, inp.conversation_id)
        res.evidence = pack
        dev.event("search", ms=lap("search", t), transport=pack.get("transport", ""),
                  queries=pack.get("queries"), n_sources=len(pack.get("sources") or []),
                  error=pack.get("error", ""), diagnostics="\n".join(pack.get("diagnostics") or []))
        if not pack.get("sources"):
            res.kind, res.text = "no_evidence", T.NO_EVIDENCE_TEXT
            res.choices = intent.generate_prompt_choices(inp.question, u, datetime.now().year)
            return res

        # 5. soạn câu trả lời ---------------------------------------------
        status(f"Đã đọc {len(pack['sources'])} nguồn — đang soạn câu trả lời…")
        t = time.time()
        # Lọc lịch sử: nếu câu hỏi hiện tại chuyển sang một thủ tục mới khác với lịch sử,
        # không truyền lịch sử của thủ tục cũ vào để tránh mô hình 1.5B bị lẫn lộn giấy tờ
        hist = inp.history
        if hist and u.intent in intent.PROCEDURE_INTENTS:
            _, prev_intent = intent._extract_recent_procedure(hist)
            if prev_intent and prev_intent != u.intent:
                hist = []

        draft = answer.generate(inp.question, question, pack, inp.summary,
                                hist, inp.profile)
        dev.event("answer", ms=lap("answer", t), chars=len(draft))

        # 6. kiểm chứng -> sửa ---------------------------------------------
        if VERIFIER_ENABLED:
            researched = False
            for attempt in range(MAX_VERIFY_RETRIES + 1):
                status("Đang kiểm chứng câu trả lời với nguồn…")
                t = time.time()
                v = verifier.verify(inp.question, question, pack, draft)
                dev.event("verify", ms=lap("verify", t), attempt=attempt,
                          verdict="PASS" if v.passed else "FAIL",
                          issues=v.rule_issues + v.unsupported_claims, soft=v.soft_issues,
                          explanation=v.explanation, draft=draft[:600])
                if v.passed or attempt == MAX_VERIFY_RETRIES:
                    break
                if not v.evidence_sufficient and v.better_search_query and not researched:
                    status("Kiểm chứng chưa đạt — đang tra cứu bổ sung…")
                    t = time.time()
                    extra = evidence.gather(question, [v.better_search_query], None)
                    pack = evidence.merge(pack, extra)
                    res.evidence, researched = pack, True
                    dev.event("research", ms=lap("search", t), query=v.better_search_query,
                              n_sources=len(pack["sources"]))
                status("Kiểm chứng chưa đạt — đang viết lại câu trả lời…")
                t = time.time()
                draft = answer.generate(inp.question, question, pack, inp.summary,
                                        inp.history, inp.profile, fix_notes=v.fix_notes())
                dev.event("rewrite", ms=lap("answer", t), chars=len(draft))
            res.verdict = "PASS" if v.passed else "FAIL"
            res.verification = v.as_dict()
            if not v.passed:
                draft = verifier.apply_fail_policy(draft, v)

            # Nếu AI không chắc chắn (kiểm chứng FAIL hoặc câu trả lời không tìm thấy đủ căn cứ), cung cấp 3 gợi ý MCP
            if (not v.passed or not v.evidence_sufficient or verifier.says_not_found(draft)) and not res.choices:
                res.choices = intent.generate_prompt_choices(inp.question, u, datetime.now().year)

        # Đã tra cứu có nguồn thì phục vụ câu trả lời cho người dân kèm nguồn đối chiếu, không tự gán not_in_sources
        res.kind = "answer"
        res.text = draft
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
                standalone=res.intent.get("standalone_question", ""),
                queries=(res.evidence or {}).get("queries", []),
                sources=[s.get("url") or s.get("title") for s in res.sources],
                timings=res.timings)
        dev.finish()

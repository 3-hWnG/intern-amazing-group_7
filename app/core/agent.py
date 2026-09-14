"""Vòng lặp agent — bộ điều phối v6. Thay cho core/pipeline.py.

    câu hỏi
      └─ xã giao?            -> trả lời ngắn, không tra gì
      └─ MÔ HÌNH TỰ CHỌN công cụ (tối đa AGENT_MAX_STEPS vòng):
            search_procedures | get_procedure | search_attachments
            | search_web | none
      └─ sinh câu trả lời từ bằng chứng thu được (hoặc không có bằng chứng nào)
      └─ có bản ghi -> kiểm chứng bằng luật -> sinh lại -> bỏ cuộc về bản ghi gốc

Khác biệt với pipeline cũ, nói bằng một câu: ở đây KHÔNG có nhánh nào ép mô
hình phải tra bảng, và KHÔNG có nhánh nào cấm nó dùng hiểu biết chung. Bảng
thủ tục là một công cụ, không phải cái cũi.

File này CHỈ điều phối. Truy hồi ở core/retrieval.py, công cụ ở core/tools.py,
prompt ở prompts/agent_templates.py, kiểm chứng ở core/factcheck.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from config import (AGENT_DECISION_OPTIONS, AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL,
                    AGENT_MAX_STEPS, AGENT_TOOL_MODE, ANSWER_STYLE,
                    EXACT_ON_FACET, FACTCHECK_ENABLED, FACTCHECK_MAX_RETRIES,
                    EVIDENCE_MIN_CONFIDENCE, FOLLOWUP_MAX_WORDS,
                    FOLLOWUP_STICKY, TIER_A_MIN_CONFIDENCE,
                    TIER_B_MIN_CONFIDENCE, WEB_FORCE_PHRASES)
import developer_mode
from core import factcheck, formatter, llm, smalltalk, tools
from core.tiers import Tier
from domain.records import Procedure
from domain.text import fold
from prompts import agent_templates as T

DIGEST_TURNS = 4            # số lượt gần nhất đưa vào prompt CHỌN công cụ

@dataclass
class AgentPlan:
    """Cùng hình dạng với AnswerPlan cũ nên chat_routes không phải viết lại."""
    tier: Tier = Tier.D_GENERAL
    kind: str = "none"                       # procedures|attachments|web|mixed|none|smalltalk
    confidence: float = 0.0
    text: str | None = None                  # có sẵn -> phát thẳng
    system: str | None = None                # cần LLM -> stream từ model
    user: str | None = None
    history: list = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    record: Procedure | None = None
    top_row_id: int | None = None
    factcheck_summary: str = ""
    steps: list[str] = field(default_factory=list)
    evidence: str = ""
    diagnostics: str = ""        # nhật ký tra web, cho bảng Dev


_WEB_FORCE_RE = re.compile(
    r"(?<![a-z0-9])(?:%s)(?![a-z0-9])"
    % "|".join(sorted((re.escape(x) for x in WEB_FORCE_PHRASES),
                      key=len, reverse=True)))

# Từ thuộc về phần RA LỆNH, không thuộc về thứ người dùng muốn tra.
# Gộp từ WEB_FORCE_PHRASES + các tiếng đệm hay đi kèm.
# CẨN THẬN khi thêm từ vào đây. Từ vựng hành chính đầy những tiếng trùng với
# tiếng đệm sau khi bỏ dấu:
#   "thu" = thủ (thủ tục)      -> từng biến "thủ tục nhập tịch" thành "tục nhập tịch"
#   "ho"  = hồ / hộ            -> từng biến "hộ chiếu" thành "chiếu"
#   "lam" = làm, "ban" = bản/bạn
# Không được thêm bốn tiếng đó vào đây.
_COMMAND_WORDS = {w for phrase in WEB_FORCE_PHRASES for w in phrase.split()} | {
    "de", "tra", "loi", "giup", "minh", "toi", "em", "cho", "xem", "di",
    "nhe", "voi", "a", "dum", "kiem", "cuu", "tim", "gium",
}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", fold(text or ""))).strip()


def user_asked_for_web(question: str) -> bool:
    """Người dùng nói thẳng "tra trên mạng đi" / "dùng web search".

    Đây KHÔNG phải guardrail lên mô hình mà là MỆNH LỆNH của người dùng — ở lần
    chạy thử, mô hình 1.5B còn trả lời "tôi không thể sử dụng công cụ như vậy
    vì có thể vi phạm quyền riêng tư", trong khi công cụ đó có sẵn ngay cạnh.
    """
    return bool(_WEB_FORCE_RE.search(_normalise(question)))


def _web_query(question: str) -> str:
    """Bỏ phần ra lệnh, GIỮ NGUYÊN DẤU phần còn lại.

    Phải giữ dấu: DuckDuckGo tra tiếng Việt không dấu cho kết quả tệ hơn hẳn.
    Nên lọc theo TỪ trên bản gốc, thay vì cắt chuỗi trên bản đã bỏ dấu.
    """
    kept = [w for w in (question or "").split()
            if _normalise(w) and _normalise(w) not in _COMMAND_WORDS]
    return " ".join(kept).strip(" ,.?!:;") or question


def _digest(history: list, limit: int = DIGEST_TURNS) -> str:
    """Vài lượt gần nhất, cắt ngắn — prompt chọn công cụ càng gọn càng chuẩn."""
    if not history:
        return ""
    lines = []
    for turn in history[-limit:]:
        role = getattr(turn, "role", "user")
        content = (getattr(turn, "content", "") or "").replace("\n", " ")
        who = "Công dân" if role == "user" else "Trợ lý"
        lines.append(f"{who}: {content[:180]}")
    return "\n".join(lines)


def _tier_for(kind: str, confidence: float, has_web: bool = False) -> Tier:
    """Nhãn hiển thị. LƯU Ý: đây CHỈ là nhãn, không còn điều khiển luồng nữa.

    Trộn nhiều nguồn mà có web ở trong -> hạ xuống nhãn C: một phần câu trả lời
    CHƯA đối chiếu với dữ liệu nội bộ, nói thẳng ra vẫn hơn.
    """
    if kind == "web" or (kind == "mixed" and has_web):
        return Tier.C_WEB
    if kind in ("procedures", "attachments", "mixed"):
        # Nhãn xanh "Từ cơ sở dữ liệu thủ tục" chỉ dành cho bản ghi ĐÁNG TIN.
        # Trước đây khớp 0.20 cũng được dán nhãn đó — nhãn nói dối, người dân tin.
        if confidence < TIER_B_MIN_CONFIDENCE:
            return Tier.D_GENERAL
        return Tier.A_DATABASE
    return Tier.D_GENERAL


def _decide(question: str, manifest: str, digest: str, current, observations,
            allow_attachments: bool) -> dict:
    """Một lượt chọn công cụ. Trả về {"tool","query","row_id"}."""
    context = digest
    if observations:
        seen = "\n".join(
            f"Đã gọi {o.tool}({o.query}) -> "
            + (f"có {len(o.text.splitlines())} dòng kết quả" if o.ok else f"thất bại: {o.note}")
            for o in observations
        )
        context = f"{context}\n\nĐÃ TRA CỨU:\n{seen}".strip()

    if AGENT_TOOL_MODE == "native":
        calls = llm.chat_tools(
            T.DECISION_SYSTEM,
            T.decision_user(question, manifest, context, current),
            tools=tools.specs(include_attachments=allow_attachments),
        )
        if calls:
            first = calls[0]
            args = first.get("arguments") or {}
            return {"tool": first["name"],
                    "query": str(args.get("query", "") or ""),
                    "row_id": args.get("row_id")}
        return {"tool": "none", "query": "", "row_id": None}

    raw = llm.complete_json(
        T.DECISION_SYSTEM,
        T.decision_user(question, manifest, context, current),
        schema=T.DECISION_SCHEMA,
        options=AGENT_DECISION_OPTIONS,
    )
    tool = str(raw.get("tool") or "none").strip()
    if tool not in tools.NAMES:
        tool = "none"
    if tool == "search_attachments" and not allow_attachments:
        tool = "search_procedures"
    return {"tool": tool,
            "query": str(raw.get("query") or "").strip(),
            "row_id": raw.get("row_id")}


def _evidence_block(observations: list) -> tuple[str, str, list[str]]:
    """Gộp bằng chứng -> (văn bản, loại, nguồn)."""
    usable = [o for o in observations if o.ok and o.text]
    if not usable:
        return "", "none", []

    kinds = {o.kind for o in usable}
    kind = kinds.pop() if len(kinds) == 1 else "mixed"

    blocks, sources = [], []
    for obs in usable:
        header = ""
        if obs.kind == "procedures" and obs.confidence:
            # Nói thẳng độ khớp cho mô hình biết. Khớp yếu thì nó tự dè dặt,
            # thay vì bị một cái ngưỡng cứng chặn lại như bản cũ.
            if obs.confidence < TIER_B_MIN_CONFIDENCE:
                header = ("(độ khớp thấp: %.2f — có thể KHÔNG phải thủ tục "
                          "người dân đang hỏi, hãy nói rõ nếu không chắc)\n"
                          % obs.confidence)
            elif obs.confidence < TIER_A_MIN_CONFIDENCE:
                header = "(độ khớp trung bình: %.2f)\n" % obs.confidence
        blocks.append(header + obs.text)
        for src in obs.sources:
            if src not in sources:
                sources.append(src)
    return "\n\n".join(blocks), kind, sources


# ==========================================================================
# điểm vào
# ==========================================================================
def build(question: str, *, history: list | None = None,
          conversation_id: int | None = None, manifest: str = "",
          current: tuple[int, str] | None = None,
          allow_attachments: bool = False,
          force_web: bool = False) -> AgentPlan:
    """Thuần nghiệp vụ: không đọc/ghi CSDL, không biết gì về phiên đăng nhập."""
    question = (question or "").strip()
    history = history or []
    dev = developer_mode.turn(question, conversation_id)
    facet = T.wants_exact(question) if EXACT_ON_FACET else ""
    dev.set(facet=facet, current=list(current) if current else None,
            manifest_lines=len(manifest.splitlines()) if manifest else 0)

    # -- xã giao: rẻ, không gọi LLM, không tra gì --------------------------
    if smalltalk.is_smalltalk(question):
        dev.event("smalltalk", matched=True)
        dev.set(kind="smalltalk", tools=[])
        dev.finish()
        # kind="smalltalk" -> giao diện KHÔNG gắn nhãn độ tin cậy. Dán
        # "Thông tin chung - KHÔNG chắc chắn" lên một lời chào là vô nghĩa.
        return AgentPlan(tier=Tier.A_DATABASE, kind="smalltalk", confidence=1.0,
                         text=smalltalk.reply(question), steps=["smalltalk"])

    digest = _digest(history)
    observations: list = []
    steps: list[str] = []
    tried: set[tuple[str, str]] = set()

    # -- người dùng YÊU CẦU tra web (nút Web, hoặc nói thẳng trong câu) -----
    # Bỏ qua hẳn bước chọn công cụ: đây là MỆNH LỆNH, không phải gợi ý.
    forced_web = force_web or user_asked_for_web(question)
    if forced_web:
        query = question if force_web else _web_query(question)
        obs = tools.run("search_web", query=query, conversation_id=conversation_id)
        observations.append(obs)
        steps.append(f"web:theo yêu cầu người dùng({query[:40]})"
                     + ("" if obs.ok else " ✗" + (f": {obs.note}" if obs.note else "")))

        # Kèm luôn bản ghi nội bộ đang nói tới. Nếu không, mô hình chỉ có kết
        # quả web trong tay và sẽ lấy số của một thủ tục gần giống: đã thấy nó
        # gán "145 USD" (thẻ tạm trú cho người nước ngoài) cho thủ tục gia hạn
        # tạm trú trong nước, trong khi bản ghi nội bộ ghi rõ 7.000đ.
        if obs.ok and current:
            inner = tools.run("get_procedure", row_id=current[0],
                              conversation_id=conversation_id)
            if inner.ok:
                observations.append(inner)
                steps.append(f"kèm bản ghi nội bộ «{current[1]}» để neo số liệu")
                dev.event("anchor", row_id=current[0], title=current[1],
                          reason="ép tra web — số liệu phải neo vào dữ liệu nội bộ")
        if not obs.ok:
            # Tra không ra thì NÓI THẬT là tra không ra, đừng lặng lẽ trả lời chay.
            dev.event("web_failed", note=obs.note, diagnostics=obs.diagnostics)
            dev.set(kind="none", tools=list(steps), diagnostics=obs.diagnostics)
            dev.finish()
            return AgentPlan(
                diagnostics=obs.diagnostics,
                tier=Tier.D_GENERAL, kind="none", history=history, steps=steps,
                system=T.SYSTEM_OPEN,
                user=(f"CÂU HỎI: {question}\n\n"
                      f"(Đã thử tra nguồn chính thống trên mạng nhưng không lấy "
                      f"được kết quả: {obs.note}. Hãy nói thật với người dân điều "
                      f"đó, rồi trả lời phần bạn biết chắc — tuyệt đối không bịa "
                      f"số liệu thời sự.)"))

    # -- vòng lặp chọn công cụ ---------------------------------------------
    for _ in range(0 if forced_web else max(1, AGENT_MAX_STEPS)):
        choice = _decide(question, manifest, digest, current,
                         observations, allow_attachments)
        tool = choice["tool"]
        query = choice["query"] or question
        row_id = choice["row_id"]

        # GUARDRAIL DUY NHẤT — xem chú thích ở config.py.
        # Tắt khi cắm mô hình lớn: nó tự biết lúc nào cần tra.
        if (tool == "none" and not observations
                and AGENT_FORCE_RETRIEVAL_ON_ADMIN_SIGNAL
                and smalltalk.has_admin_signal(question)):
            tool, query = "search_procedures", question
            steps.append("guardrail:ép tra cứu")

        if tool == "none":
            steps.append("none")
            break

        key = (tool, str(row_id) if tool == "get_procedure" else query)
        if key in tried:            # đừng gọi lại đúng cái vừa gọi
            break
        tried.add(key)

        dev.event("decision", tool=tool, query=query, row_id=row_id)
        obs = tools.run(tool, query=query, row_id=row_id,
                        conversation_id=conversation_id)
        observations.append(obs)
        dev.event("tool", tool=tool, query=query, ok=obs.ok,
                  evidence_kind=obs.kind,
                  confidence=round(obs.confidence, 3), note=obs.note,
                  title=obs.record.ten if obs.record else "",
                  diagnostics=obs.diagnostics)
        steps.append(f"{tool}({(str(row_id) if tool == 'get_procedure' else query)[:40]})"
                     f"{'' if obs.ok else ' ✗' + (': ' + obs.note if obs.note else '')}")

        if obs.ok and obs.kind in ("procedures", "attachments") \
                and obs.confidence >= TIER_A_MIN_CONFIDENCE:
            break               # đã chắc chắn, không cần tra thêm

    # -- NGỮ CẢNH DÍNH ----------------------------------------------------
    # Câu hỏi tiếp nối ("nộp ở đâu?", "tốn nhiều tiền?", "đến nơi đâu để nộp hồ
    # sơ?") phải nói về thủ tục ĐANG nói tới. Truy hồi lại từ đầu bằng mấy chữ
    # đó gần như chắc chắn ra nhầm: đang nói "gia hạn tạm trú" (nộp ở Công an
    # Xã) mà truy hồi trả về thủ tục khác ở mức 0.20-0.43.
    #
    # Điều kiện nới ra: hỏi vào MỘT trường, HOẶC chỉ là một câu ngắn. Bộ nhận
    # diện trường không thể phủ hết mọi cách nói của người Việt.
    short_followup = len(question.split()) <= FOLLOWUP_MAX_WORDS
    if FOLLOWUP_STICKY and current and not forced_web and (facet or short_followup):
        proc = [o for o in observations if o.ok and o.kind == "procedures"]
        best = max((o.confidence for o in proc), default=0.0)
        if best < TIER_A_MIN_CONFIDENCE:
            row_id, name = current
            back = tools.run("get_procedure", row_id=row_id,
                             conversation_id=conversation_id)
            if back.ok:
                observations = [o for o in observations
                                if not (o.ok and o.kind == "procedures")] + [back]
                steps.append(f"ngữ cảnh dính: quay lại «{name}» "
                             f"(truy hồi mới chỉ {best:.2f})")
                dev.event("sticky", row_id=row_id, title=name,
                          fresh_confidence=round(best, 3),
                          reason="câu hỏi tiếp nối, truy hồi mới không đủ chắc")

    # -- SÀN ĐỘ TIN CẬY ---------------------------------------------------
    # Còn sót bản ghi quá yếu thì BỎ HẲN. Thà nói "mình chưa có thủ tục này"
    # còn hơn in nguyên bản ghi khai sinh ra cho người đang hỏi về tạm trú.
    weak = [o for o in observations
            if o.ok and o.kind == "procedures" and o.confidence < EVIDENCE_MIN_CONFIDENCE]
    if weak:
        observations = [o for o in observations if o not in weak]
        for o in weak:
            steps.append(f"bỏ bằng chứng yếu ({o.confidence:.2f} < "
                         f"{EVIDENCE_MIN_CONFIDENCE})")
            dev.event("dropped_weak", confidence=round(o.confidence, 3),
                      title=o.record.ten if o.record else "",
                      floor=EVIDENCE_MIN_CONFIDENCE)

    evidence, kind, sources = _evidence_block(observations)
    top = next((o for o in observations if o.ok and o.record), None)
    confidence = top.confidence if top else (
        max([o.confidence for o in observations if o.ok], default=0.0))

    has_web = any(o.ok and o.kind == "web" for o in observations)
    system = T.system_for(kind, facet)
    plan = AgentPlan(
        tier=_tier_for(kind, confidence, has_web), kind=kind, confidence=confidence,
        history=history, sources=sources, steps=steps, evidence=evidence,
        record=top.record if top else None,
        top_row_id=top.row_id if top else None,
        diagnostics="\n".join(o.diagnostics for o in observations if o.diagnostics),
    )

    def done(p: AgentPlan) -> AgentPlan:
        """Mọi đường ra đều đi qua đây — ghi vết rồi trả kế hoạch."""
        dev.set(kind=p.kind, tier=p.tier.value, confidence=round(p.confidence, 3),
                tools=list(p.steps), sources=list(p.sources),
                factcheck=p.factcheck_summary, evidence_chars=len(p.evidence),
                mode="text" if p.text is not None else "stream",
                diagnostics=p.diagnostics)
        dev.finish()
        return p

    # -- không có bằng chứng: trợ lý bình thường, stream thẳng -------------
    if not evidence:
        plan.system = system
        plan.user = T.user_answer(question, "")
        return done(plan)

    # -- có bản ghi + bật kiểm chứng: sinh xong mới phát ------------------
    if plan.record is not None and ANSWER_STYLE == "template":
        plan.text = formatter.render_record(plan.record)
        plan.factcheck_summary = "in nguyên bản ghi (ANSWER_STYLE=template)"
        return done(plan)

    if plan.record is not None and FACTCHECK_ENABLED:
        answer, summary = _generate_checked(question, evidence, system,
                                            plan.record, history, dev)
        plan.text = answer
        plan.factcheck_summary = summary
        return done(plan)

    # -- bằng chứng từ web / tệp đính kèm: stream thẳng -------------------
    plan.system = system
    plan.user = T.user_answer(question, evidence)
    return done(plan)


def _generate_checked(question: str, evidence: str, system: str,
                      record: Procedure, history: list,
                      dev=None) -> tuple[str, str]:
    """Sinh -> kiểm chứng bằng luật -> sinh lại -> bỏ cuộc về bản ghi gốc.

    Không stream được vì phải có TOÀN BỘ câu trả lời mới kiểm tra được số liệu.
    chat_routes phát lại theo từng mẩu để giao diện vẫn có hiệu ứng gõ chữ.
    """
    answer = llm.complete(system, T.user_answer(question, evidence), history)
    result = factcheck.check(answer, record)
    if dev is not None:
        dev.event("generate", chars=len(answer), factcheck_ok=result.ok,
                  problem="" if result.ok else result.summary())

    attempts = 0
    while not result.ok and attempts < FACTCHECK_MAX_RETRIES:
        attempts += 1
        answer = llm.complete(
            system, T.user_retry(question, evidence, result.summary()), history)
        result = factcheck.check(answer, record)
        if dev is not None:
            dev.event("regenerate", attempt=attempts, factcheck_ok=result.ok,
                      problem="" if result.ok else result.summary())

    if not result.ok:
        return (formatter.render_record(record),
                f"không đạt ({result.summary()}) -> in bản ghi gốc")
    return answer, "đạt" if attempts == 0 else f"đạt sau {attempts} lần sinh lại"

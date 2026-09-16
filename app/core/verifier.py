"""Kiểm chứng bản nháp TRƯỚC khi trả lời người dân — BA TẦNG (PLAN §8).

    A. mục tiêu (target) có tồn tại không?        -> core/intent.py
    B. bản nháp có trả lời đúng mục tiêu không?   -> MỘT câu hỏi hẹp cho LLM
    C. từng chi tiết có bám nguồn không?          -> luật, ngày càng có cấu trúc

Không nhồi cả ba vào một prompt: đo được rằng mô hình 1.5B nhận bài kiểm tra lớn
thì gật đầu với mọi thứ ("bản nháp đáp ứng đầy đủ..."), còn khi chỉ phải trả lời
MỘT câu hỏi hẹp thì nó làm đúng (bài học từ bộ gác hỏi lại: 43% -> 100%).

Tầng C là hệ heuristic, không phải chứng minh: tên cơ quan, tên văn bản, và con
số phải xuất hiện trong ĐOẠN nguồn nói về đúng mục tiêu — mạnh hơn nhiều so với
"có xuất hiện đâu đó trong Evidence Pack" (lỗ hổng từng cho lọt "5-25 ngày").
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime

from config import VERIFY_FAIL_POLICY, VERIFY_GROUNDING_STRICT, VERIFY_TARGET_CHECK
from core import evidence as evidence_mod
from core import llm
from domain.text import DAYS_RE, DOC_NO_RE, MONEY_RE, fold, tidy_answer
from prompts import templates as T

BRACKET_RE = re.compile(r"\[([^\]\n]{0,400})\]")
NOT_FOUND_RE = re.compile(r"[^.\n]*chưa nêu rõ[^.\n]*\.?", re.IGNORECASE)
# "Bộ Xây dựng", "Sở Tư pháp", "Cục Cảnh sát QLHC" — tên riêng, phải có trong nguồn.
# "UBND cấp xã", "Công an cấp xã" là cách gọi chung (chữ thường) nên không bị bắt.
AGENCY_RE = re.compile(
    r"\b(Bộ|Sở|Cục|Tổng cục|Chi cục|Kho bạc|Trung tâm|Phòng)\s+"
    r"([A-ZÀ-ỸĐ][^\s,.;:()\[\]]*(?:\s+[a-zA-ZÀ-ỹĐđ][^\s,.;:()\[\]]*){0,3})")
LAW_NAMED_RE = re.compile(
    r"\b(?:Luật|Bộ luật|Pháp lệnh)\s+[A-ZÀ-ỸĐ][\wÀ-ỹ]*(?:\s+[\wÀ-ỹ]+){0,3}\s+năm\s+\d{4}")
LAW_NUMBERED_RE = re.compile(
    r"\b(?:Nghị định|Thông tư|Quyết định|Nghị quyết)\s+(?:số\s+)?\d{1,4}[/-][\w/-]+")


@dataclass
class Verification:
    passed: bool = True
    rule_issues: list[str] = field(default_factory=list)       # lỗi CỨNG -> FAIL
    soft_issues: list[str] = field(default_factory=list)       # ghi nhận, không đánh trượt
    unverified_details: list[str] = field(default_factory=list)
    ungrounded_names: list[str] = field(default_factory=list)  # cơ quan / văn bản không có trong nguồn
    missing_citations: bool = False
    bad_citations: list[str] = field(default_factory=list)
    echo: bool = False
    too_short: bool = False
    contradiction: bool = False
    placeholders: list[str] = field(default_factory=list)
    answers_target: bool | None = None       # tầng B
    target: str = ""
    llm_verdict: str = ""
    answers_question: bool = True
    unsupported_claims: list[str] = field(default_factory=list)
    wrong_situation: bool = False
    evidence_sufficient: bool = True
    better_search_query: str = ""
    explanation: str = ""

    def fix_notes(self) -> str:
        """Chỉ dẫn sửa CỤ THỂ — không đưa nguyên văn lời phê (mô hình nhỏ chép lại)."""
        notes = []
        label = T.TARGET_LABELS.get(self.target, "")
        if self.answers_target is False and label:
            notes.append(f"- Tài liệu CÓ phần nói về {label}: hãy đọc kỹ và dùng đúng phần "
                         f"đó để trả lời ngay câu đầu, kèm [S#]. Không được nói là tài liệu "
                         f"không có.")
        if self.unverified_details:
            notes.append("- Bỏ các chi tiết không có trong tài liệu: " + "; ".join(self.unverified_details))
        if self.ungrounded_names:
            notes.append("- Không nêu cơ quan / văn bản không có trong tài liệu: "
                         + "; ".join(self.ungrounded_names))
        notes += [f"- Bỏ hoặc sửa ý không có trong tài liệu: {c}" for c in self.unsupported_claims[:3]]
        if self.bad_citations:
            notes.append("- Chỉ ghi số tài liệu có thật: " + ", ".join(self.bad_citations) + " không tồn tại.")
        if self.missing_citations:
            notes.append("- Ghi số tài liệu [S#] sau mỗi ý có thông tin cụ thể.")
        if self.contradiction:
            notes.append("- Chọn MỘT: hoặc trả lời dựa trên tài liệu, hoặc nói 'tài liệu "
                         "chưa nêu rõ' rồi dừng. Không được làm cả hai.")
        if self.too_short or self.placeholders:
            notes.append("- Viết câu trả lời đầy đủ thành câu cho người dân; không để chỗ trống "
                         "trong ngoặc vuông. Ngoặc vuông chỉ dùng cho số tài liệu như [S1].")
        if not self.answers_question:
            notes.append("- Trả lời thẳng vào điều người dùng hỏi.")
        if self.wrong_situation:
            notes.append("- Chỉ nêu thủ tục đúng trường hợp của người dùng.")
        return "\n".join(notes) or "- Trả lời ngắn gọn, đúng câu hỏi, chỉ dùng thông tin trong tài liệu."

    def as_dict(self) -> dict:
        return asdict(self)


def _is_citation(inner: str) -> bool:
    return bool(re.fullmatch(r"\s*S\d+(\s*[,;]\s*S\d+)*\s*", inner, re.IGNORECASE))


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def _duration(text: str) -> str:
    m = re.match(r"0*(\d+)\s*(\w+)", fold(text))
    return f"{m.group(1)}{m.group(2)}" if m else fold(text)


def _flat(text: str) -> str:
    return re.sub(r"\s+", "", fold(text))


# ==========================================================================
# TẦNG C — chi tiết có bám nguồn không (luật, không dùng LLM)
# ==========================================================================
def rule_check(answer: str, pack: dict, v: Verification, target: str = "") -> None:
    sources = pack.get("sources") or []
    evidence = "\n".join(f"{s.get('title', '')}\n{s.get('snippet', '')}\n{s.get('content', '')}"
                         for s in sources)

    ids = {s["id"].upper() for s in sources if s.get("id")}
    cited = {x.upper() for group in re.findall(r"\[([^\]]*)\]", answer)
             for x in re.findall(r"S\d+", group, re.IGNORECASE)}
    v.bad_citations = sorted(cited - ids)
    v.missing_citations = not cited and len(answer) > 200
    if v.bad_citations:
        v.rule_issues.append("Trích dẫn nguồn không tồn tại: " + ", ".join(v.bad_citations))
    if v.missing_citations:
        # Mô hình nhỏ hay quên ghi [S#] dù nội dung đúng nguồn. Không đánh trượt vì
        # lý do này: con số / tên cơ quan vẫn bị đối chiếu cứng ngay bên dưới.
        v.soft_issues.append("Câu trả lời không ghi nguồn [S#] cho các ý.")

    # Ngoặc vuông CHỈ được chứa số tài liệu; còn lại là chỗ trống mô hình tự đặt.
    v.placeholders = [m for m in BRACKET_RE.findall(answer) if not _is_citation(m)]
    if v.placeholders:
        v.rule_issues.append("Ngoặc vuông chỉ dùng cho số tài liệu, câu trả lời có: "
                             + "; ".join(f"[{p}]" for p in v.placeholders[:3])[:120])

    # Con số phải nằm trong ĐOẠN nói về đúng mục tiêu, không phải "đâu đó trong pack".
    scope = evidence
    if VERIFY_GROUNDING_STRICT and target:
        focused = evidence_mod.target_passages(pack, target)
        if focused:
            scope = focused
    numbers = {_digits(n) for n in re.findall(r"\d[\d.,]*", scope)}
    for money in dict.fromkeys(m.strip() for m in MONEY_RE.findall(answer)):
        if _digits(money) not in numbers:
            v.unverified_details.append(money)
    durations = {_duration(d) for d in DAYS_RE.findall(scope)}
    for d in dict.fromkeys(x.strip() for x in DAYS_RE.findall(answer)):
        if _duration(d) not in durations:
            v.unverified_details.append(d)

    flat_all = _flat(evidence)
    for doc in dict.fromkeys(DOC_NO_RE.findall(answer)):
        if _flat(doc) not in flat_all:
            v.unverified_details.append(doc)
    v.rule_issues += [f"Chi tiết không có trong nguồn: {d}" for d in v.unverified_details]

    # Tên cơ quan và tên văn bản: "Bộ Xây dựng cấp giấy phép" trong khi nguồn nói
    # UBND cấp xã là kiểu sai nguy hiểm nhất mà kiểm tra con số không bắt được.
    if VERIFY_GROUNDING_STRICT:
        names = [m.group(0).strip() for m in AGENCY_RE.finditer(answer)]
        names += LAW_NAMED_RE.findall(answer) + LAW_NUMBERED_RE.findall(answer)
        for name in dict.fromkeys(names):
            if _flat(name) not in flat_all:
                v.ungrounded_names.append(name)
        v.rule_issues += [f"Cơ quan / văn bản không có trong nguồn: {n}"
                          for n in v.ungrounded_names]

    # Vừa nói "tài liệu chưa nêu rõ" vừa liệt kê tiếp -> câu trả lời tự mâu thuẫn,
    # người dân không biết tin câu nào.
    v.contradiction = bool(NOT_FOUND_RE.search(answer)) and len(
        NOT_FOUND_RE.sub("", answer).strip()) > 200
    if v.contradiction:
        v.rule_issues.append("Câu trả lời vừa nói 'chưa nêu rõ' vừa trả lời tiếp — tự mâu thuẫn.")

    low = answer.lower()
    v.echo = any(marker.lower() in low for marker in T.ECHO_MARKERS)
    if v.echo:
        v.rule_issues.append("Câu trả lời chép lại khung prompt / nhắc tới việc kiểm chứng.")

    flat = re.sub(r"\s+", " ", answer).strip()
    v.too_short = len(flat) < 60
    if v.too_short:
        v.rule_issues.append("Câu trả lời quá ngắn hoặc chỉ là chỗ trống.")


# ==========================================================================
# TẦNG B — MỘT câu hỏi hẹp: có trả lời đúng mục tiêu không?
# ==========================================================================
def answers_target(question: str, target: str, draft: str) -> bool | None:
    if not VERIFY_TARGET_CHECK or not T.TARGET_LABELS.get(target):
        return None
    raw = llm.chat_json("verify", T.TARGET_CHECK_SYSTEM,
                        T.target_check_user(question, target, draft),
                        T.TARGET_CHECK_SCHEMA, T.target_check_example_messages())
    value = raw.get("answers_target")
    return bool(value) if value is not None else None


def verify(question: str, standalone: str, target: str, pack: dict, draft: str) -> Verification:
    v = Verification(target=target)
    rule_check(draft, pack, v, target)

    asked = standalone or question
    v.answers_target = answers_target(asked, target, draft)
    if v.answers_target is False:
        label = T.TARGET_LABELS.get(target, "điều người dùng hỏi")
        v.rule_issues.append(f"Câu trả lời không nói vào khía cạnh được hỏi ({label}).")

    raw = llm.chat_json("verify", T.verify_system(datetime.now().strftime("%d/%m/%Y")),
                        T.verify_user(question, standalone, pack, draft), T.VERIFY_SCHEMA)
    v.llm_verdict = str(raw.get("verdict") or "")
    v.answers_question = raw.get("answers_question") is not False
    v.unsupported_claims = [str(x).strip() for x in raw.get("unsupported_claims") or []
                            if str(x).strip()][:5]
    v.wrong_situation = raw.get("wrong_situation") is True
    v.evidence_sufficient = raw.get("evidence_sufficient") is not False
    v.better_search_query = str(raw.get("better_search_query") or "").strip()
    v.explanation = str(raw.get("explanation") or "").strip()

    # Mô hình nhỏ đôi khi phán FAIL mà không chỉ ra được lỗi nào -> không tính.
    llm_fail = v.llm_verdict == "FAIL" and bool(
        v.unsupported_claims or not v.answers_question or v.wrong_situation
        or not v.evidence_sufficient)
    v.passed = not v.rule_issues and not llm_fail
    return v


# ==========================================================================
# hết lượt sửa mà vẫn FAIL -> nói thật, không để chi tiết bịa lọt ra ngoài
# ==========================================================================
def apply_fail_policy(draft: str, v: Verification, target: str = "",
                      target_in_evidence: bool | None = None) -> str:
    if VERIFY_FAIL_POLICY == "refuse":
        return T.VERIFY_REFUSAL

    # Nguồn không hề nói về khía cạnh được hỏi -> nói thẳng, đừng trả lời vòng quanh.
    if v.answers_target is False and target_in_evidence is False:
        return T.target_missing_text(target)

    # bỏ nhãn tự bịa trong ngoặc, giữ lại câu chữ quanh nó và các trích dẫn [S#]
    body = BRACKET_RE.sub(lambda m: m.group(0) if _is_citation(m.group(1)) else "", draft)
    body = re.sub(r"^[ \t]*:[ \t]*", "", body, flags=re.MULTILINE)
    # tự mâu thuẫn: giữ phần trả lời thật, bỏ câu "chưa nêu rõ"
    if v.contradiction:
        body = NOT_FOUND_RE.sub("", body)

    drop = ([d.lower() for d in v.unverified_details] + [n.lower() for n in v.ungrounded_names]
            + [m.lower() for m in T.ECHO_MARKERS])
    kept = [line for line in body.splitlines()
            if not any(key and key in line.lower() for key in drop)]
    cleaned = tidy_answer("\n".join(kept))

    if len(cleaned) < 60:
        # đã nói thẳng là nguồn không có, không cần cảnh báo thêm
        return T.target_missing_text(target) if T.TARGET_LABELS.get(target) else T.NOT_IN_SOURCES_TEXT
    # Câu trả lời vốn đã là lời từ chối -> đừng dán thêm cảnh báo "chưa xác nhận đầy đủ".
    if NOT_FOUND_RE.search(cleaned) and len(cleaned) < 400:
        return cleaned
    note = T.VERIFY_WARNING
    if len(cleaned) < len(draft.strip()):
        note += " " + T.VERIFY_STRIPPED
    return f"{cleaned}\n\n{note}"

"""Kiểm chứng bản nháp TRƯỚC khi trả lời người dùng.

Hai lớp, bổ trợ nhau:

  1. Luật (rẻ, chắc chắn) — đúng những thứ mô hình nhỏ hay làm sai nhất:
       - trích dẫn [S#] có trỏ vào nguồn thật không, có trích dẫn không
       - mọi số tiền / thời hạn / số hiệu văn bản trong bản nháp có nằm trong tài liệu không
       - có chép lại khung prompt không
  2. LLM kiểm chứng (JSON, temperature 0) — trả lời đúng câu hỏi chưa, chi tiết
     nào không có trong tài liệu, có áp dụng nhầm trường hợp không, tài liệu đủ chưa.

PASS khi cả hai lớp đều ổn. FAIL -> orchestrator tra bổ sung / viết lại với
ghi chú sửa lỗi cụ thể. Hết lượt mà vẫn FAIL -> lược bỏ chi tiết không khớp nguồn
và cảnh báo, không bao giờ để con số bịa lọt tới người dân.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime

from config import VERIFY_FAIL_POLICY
from core import llm
from domain.text import DAYS_RE, DOC_NO_RE, MONEY_RE, fold, tidy_answer, tokenize
from prompts import templates as T


@dataclass
class Verification:
    passed: bool = True
    rule_issues: list[str] = field(default_factory=list)       # lỗi CỨNG -> FAIL
    soft_issues: list[str] = field(default_factory=list)       # ghi nhận, không đánh trượt
    unverified_details: list[str] = field(default_factory=list)
    missing_citations: bool = False
    bad_citations: list[str] = field(default_factory=list)
    echo: bool = False
    too_short: bool = False
    contradiction: bool = False
    placeholders: list[str] = field(default_factory=list)
    llm_verdict: str = ""
    answers_question: bool = True
    unsupported_claims: list[str] = field(default_factory=list)
    wrong_situation: bool = False
    evidence_sufficient: bool = True
    better_search_query: str = ""
    explanation: str = ""

    def fix_notes(self) -> str:
        """Chỉ dẫn sửa CỤ THỂ cho lần viết lại — không đưa nguyên văn lời phê (mô hình nhỏ chép lại)."""
        notes = []
        if self.unverified_details:
            notes.append("- Bỏ các chi tiết không có trong tài liệu: " + "; ".join(self.unverified_details))
        notes += [f"- Bỏ hoặc sửa ý không có trong tài liệu: {c}" for c in self.unsupported_claims[:3]]
        if self.bad_citations:
            notes.append("- Chỉ ghi số tài liệu có thật: " + ", ".join(self.bad_citations) + " không tồn tại.")
        if self.missing_citations:
            notes.append("- Ghi số tài liệu [S#] sau mỗi ý có thông tin cụ thể.")
        if self.echo:
            notes.append("- Không chép lại tiêu đề, nhãn hay định dạng của phần hướng dẫn và tài liệu.")
        if self.too_short or self.placeholders:
            notes.append("- Viết câu trả lời đầy đủ thành câu cho người dân; không để chỗ trống "
                         "trong ngoặc vuông. Ngoặc vuông chỉ dùng cho số tài liệu như [S1].")
        if self.contradiction:
            notes.append("- Tài liệu có thông tin liên quan: trả lời thẳng bằng thông tin đó, "
                         "không mở đầu bằng \"chưa nêu rõ\".")
        if not self.answers_question:
            notes.append("- Trả lời thẳng vào điều người dùng hỏi.")
        if self.wrong_situation:
            notes.append("- Chỉ nêu thủ tục đúng trường hợp của người dùng.")
        return "\n".join(notes) or "- Trả lời ngắn gọn, đúng câu hỏi, chỉ dùng thông tin trong tài liệu."

    def as_dict(self) -> dict:
        return asdict(self)


BRACKET_RE = re.compile(r"\[([^\]\n]{0,200})\]")


def _is_citation(inner: str) -> bool:
    return bool(re.fullmatch(r"\s*S\d+(\s*[,;]\s*S\d+)*\s*", inner, re.IGNORECASE))


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def _duration(text: str) -> str:
    m = re.match(r"0*(\d+)\s*(\w+)", fold(text))
    return f"{m.group(1)}{m.group(2)}" if m else fold(text)


def rule_check(answer: str, pack: dict, v: Verification) -> None:
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
        # lý do này: con số / số văn bản vẫn bị đối chiếu cứng ngay bên dưới.
        v.soft_issues.append("Câu trả lời không ghi nguồn [S#] cho các ý.")

    # Ngoặc vuông CHỈ được chứa số tài liệu. Mọi thứ khác là chỗ trống hoặc nhãn
    # mô hình tự bịa ra: "[Tài liệu chưa nêu rõ...]", "[Nghiên cứu tài liệu]", "[Bước 1]:".
    v.placeholders = [m for m in BRACKET_RE.findall(answer) if not _is_citation(m)]
    if v.placeholders:
        v.rule_issues.append("Ngoặc vuông chỉ dùng cho số tài liệu, câu trả lời có: "
                             + "; ".join(f"[{p}]" for p in v.placeholders[:3])[:120])

    numbers = {_digits(n) for n in re.findall(r"\d[\d.,]*", evidence)}
    for money in dict.fromkeys(m.strip() for m in MONEY_RE.findall(answer)):
        if _digits(money) not in numbers:
            v.unverified_details.append(money)
    durations = {_duration(d) for d in DAYS_RE.findall(evidence)}
    for d in dict.fromkeys(x.strip() for x in DAYS_RE.findall(answer)):
        if _duration(d) not in durations:
            v.unverified_details.append(d)
    flat = re.sub(r"\s", "", fold(evidence))
    for doc in dict.fromkeys(DOC_NO_RE.findall(answer)):
        if re.sub(r"\s", "", fold(doc)) not in flat:
            v.unverified_details.append(doc)
    v.rule_issues += [f"Chi tiết không có trong nguồn: {d}" for d in v.unverified_details]

    first, _, rest = answer.strip().partition("\n")
    if says_not_found(first) and has_substance(rest):
        v.rule_issues.append("Câu đầu nói tài liệu chưa nêu rõ nhưng phía sau lại liệt kê chi tiết.")
        v.contradiction = True

    low = answer.lower()
    v.echo = any(marker.lower() in low for marker in T.ECHO_MARKERS)
    if v.echo:
        v.rule_issues.append("Câu trả lời chép lại khung prompt / nhắc tới việc kiểm chứng.")

    # Mô hình nhỏ đôi khi trả về đúng một chỗ trống kiểu "[Tài liệu chưa nêu rõ...]".
    flat = re.sub(r"\s+", " ", answer).strip()
    v.too_short = len(flat) < 60 or bool(re.fullmatch(r"[\[(].{0,120}[\])]", flat))
    if v.too_short:
        v.rule_issues.append("Câu trả lời quá ngắn hoặc chỉ là chỗ trống.")


def verify(question: str, standalone: str, pack: dict, draft: str) -> Verification:
    v = Verification()
    rule_check(draft, pack, v)

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


_POINTER_RE = re.compile(r"truy cập|tham khảo|để biết thêm|liên hệ|hỏi bộ phận|cổng dịch vụ công",
                         re.IGNORECASE)


def says_not_found(text: str) -> bool:
    low = (text or "").lower()
    return "chưa nêu rõ" in low or "không tìm thấy thông tin" in low


def detail_lines(text: str) -> list[str]:
    """Dòng mang thông tin thật: không phải câu dẫn cụt ("bạn sẽ cần:"), không phải
    câu "chưa nêu rõ", không phải lời chỉ đường ("truy cập ... để biết thêm")."""
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if (len(line) < 15 or line.endswith(":") or says_not_found(line)
                or _POINTER_RE.search(line)):
            continue
        out.append(line)
    return out


def has_substance(text: str) -> bool:
    return len(" ".join(detail_lines(text))) >= 40


def is_not_found_answer(text: str) -> bool:
    """Câu trả lời chỉ nói "tài liệu chưa nêu rõ" (kèm chỉ đường) — không phải câu trả lời thật."""
    return says_not_found(text) and not has_substance(text)


def _drop_empty_headings(lines: list[str]) -> list[str]:
    """Bỏ dòng tiêu đề ("+ Người nữ phải chuẩn bị:") mà các ý bên dưới đã bị lược hết."""
    out = []
    for i, line in enumerate(lines):
        if line.strip().endswith(":"):
            nxt = next((l for l in lines[i + 1:] if l.strip()), "")
            if not nxt or nxt.strip().endswith(":"):
                continue
        out.append(line)
    return out


def apply_fail_policy(draft: str, v: Verification) -> str:
    """Hết lượt sửa mà vẫn FAIL: lược bỏ dòng có chi tiết không khớp nguồn, rồi nói thật."""
    if VERIFY_FAIL_POLICY == "refuse":
        return T.VERIFY_REFUSAL

    # bỏ nhãn tự bịa trong ngoặc, giữ lại câu chữ quanh nó và các trích dẫn [S#]
    body = BRACKET_RE.sub(lambda m: m.group(0) if _is_citation(m.group(1)) else "", draft)
    body = re.sub(r"^[ \t]*:[ \t]*", "", body, flags=re.MULTILINE)

    drop = [d.lower() for d in v.unverified_details] + [m.lower() for m in T.ECHO_MARKERS]
    claims = [set(tokenize(c)) for c in v.unsupported_claims]
    claims = [c for c in claims if len(c) >= 2]

    def unsupported(line: str) -> bool:
        """Dòng lặp lại một ý mà LLM kiểm chứng chỉ ra là không có trong tài liệu.
        Ý bịa bằng chữ (không có con số) chỉ bắt được theo cách này."""
        words = set(tokenize(line))
        return bool(words) and any(len(words & c) / len(c) >= 0.6 for c in claims)

    kept = [line for line in body.splitlines()
            if not any(key and key in line.lower() for key in drop) and not unsupported(line)]
    cleaned = tidy_answer("\n".join(_drop_empty_headings(kept)))

    if not has_substance(cleaned):
        return T.NOT_IN_SOURCES_TEXT        # đã nói thẳng là nguồn không có, không cần cảnh báo thêm
    note = T.VERIFY_WARNING
    if len(cleaned) < len(draft.strip()):
        note += " " + T.VERIFY_STRIPPED
    return f"{cleaned}\n\n{note}"

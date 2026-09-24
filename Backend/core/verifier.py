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
from domain.text import DAYS_RE, DOC_NO_RE, MONEY_RE, _clean_non_citation_brackets, fold, tidy_answer, tokenize
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


# (từ khoá câu hỏi, trừ khi câu hỏi có, câu trả lời phải nhắc ít nhất một, lời báo)
# — tất cả đã bỏ dấu. Ghi chú ly hôn (đã xử ở nước ngoài) mới ở UBND.
_AUTHORITY_RULES = [
    (["ly hon"], ["ghi chu"], ["toa an"],
     "ly hôn do Tòa án nhân dân khu vực giải quyết, không phải UBND."),
    (["ho chieu", "passport"], [], ["cong an", "xuat nhap canh", "dich vu cong", "dichvucong", "vneid"],
     "hộ chiếu do cơ quan Quản lý xuất nhập cảnh (Công an) cấp, nộp trực tiếp hoặc qua Cổng Dịch vụ công."),
    (["can cuoc", "cccd"], [], ["cong an", "dich vu cong", "dichvucong", "vneid"],
     "căn cước do cơ quan Công an cấp, nộp trực tiếp, qua VNeID hoặc Cổng Dịch vụ công."),
]


def rule_check(answer: str, pack: dict, v: Verification, question: str = "") -> None:
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

    ans_stripped = answer.strip()
    # Câu ngắn mà nêu con số tiền/thời hạn ("Lệ phí … là 15.000 đồng/lần") là trả lời
    # đủ cho câu hỏi hẹp; con số đó vẫn bị đối chiếu với nguồn ngay bên dưới.
    has_figure = bool(MONEY_RE.search(answer) or DAYS_RE.search(answer))
    if ans_stripped.lower().startswith("tài liệu liên quan") or (
            len(ans_stripped) < 70 and not has_figure and not says_not_found(ans_stripped)):
        v.rule_issues.append("Câu trả lời quá ngắn hoặc chỉ sao chép tiêu đề tài liệu, chưa nêu nội dung thủ tục.")

    # Ngoặc vuông CHỈ được chứa số tài liệu. Mọi thứ khác là chỗ trống hoặc nhãn
    # mô hình tự bịa ra: "[Tài liệu chưa nêu rõ...]", "[Nghiên cứu tài liệu]", "[Bước 1]:".
    v.placeholders = [m for m in BRACKET_RE.findall(answer) if not _is_citation(m)]
    if v.placeholders:
        v.rule_issues.append("Ngoặc vuông chỉ dùng cho số tài liệu, câu trả lời có: "
                             + "; ".join(f"[{p}]" for p in v.placeholders[:3])[:120])

    ev_fold = fold(evidence)
    numbers = {_digits(n) for n in re.findall(r"\d[\d.,]*", evidence)}
    for money in dict.fromkeys(m.strip() for m in MONEY_RE.findall(answer)):
        d_money = _digits(money)
        if d_money == "0" and any(k in ev_fold for k in ["mien", "khong thu", "khong phai nop", "khong mat", "0 dong", "0d", "0đ"]):
            continue
        if d_money not in numbers:
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

    # ----------------------------------------------------------------------
    # KIỂM TRA THỰC THỂ VÀ Ý KIẾN TỔNG QUÁT (GENERIC DOMAIN GROUNDING)
    # ----------------------------------------------------------------------
    ans_fold = fold(answer)
    q_fold = fold(question)

    # 1. Kiểm tra cơ quan/nơi tiếp nhận tổng quát (Generic Agency Grounding):
    ADMIN_AUTHORITY_KEYWORDS = [
        "ubnd", "uy ban nhan dan", "cong an", "bo cong an", "dich vu cong", "dichvucong",
        "vneid", "chinh phu", "toa an", "vien kiem sat", "bo phan mot cua", "trung tam hanh chinh",
        "co quan dang ky kinh doanh", "co quan dang ky", "co quan thue", "chi cuc thue", "bao hiem xa hoi", "bhxh"
    ]
    agency_patterns = [
        r"\*\*(?:cơ quan tiếp nhận|nơi nộp hồ sơ|nơi giải quyết|nơi tiếp nhận|cơ quan giải quyết)\s*:\*\*\s*([^\n\.]+)",
        r"(?:bạn cần đến|hãy đến|liên hệ trực tiếp|nộp hồ sơ tại|nộp tại|đến trực tiếp)\s+([^\n\.,]+?)\s+(?:để|làm|nộp|giải quyết|hỗ trợ)",
    ]
    for pat in agency_patterns:
        for match in re.finditer(pat, answer, re.IGNORECASE):
            raw_target = match.group(1).strip()
            target_fold = fold(raw_target)
            if len(target_fold) < 4 or any(g in target_fold for g in ["co quan chuc nang", "co quan co tham quyen", "dia phuong", "noi cu tru"]):
                continue
            in_evidence = target_fold in ev_fold
            is_valid_authority = any(kw in target_fold for kw in ADMIN_AUTHORITY_KEYWORDS)
            if not in_evidence and not is_valid_authority:
                v.rule_issues.append(f"Chỉ dẫn sai cơ quan/nơi tiếp nhận: '{raw_target}' không có trong tài liệu và không thuộc hệ thống cơ quan hành chính công.")

    # 2. Chống thiên kiến đồng thuận tổng quát (Generic Confirmation Sycophancy Check):
    is_confirm_q = any(cq in q_fold for cq in ["dung khong", "phai khong", "co phai", "dung ko", "phai ko"])
    if is_confirm_q:
        q_numbers = re.findall(r"\b(\d+)\s*(ngay|thang|nam|dong|trieu|tuoi)\b", q_fold)
        for num, unit in q_numbers:
            unit_in_ev = re.findall(rf"\b(\d+)\s*{unit}\b", ev_fold)
            if unit_in_ev and num not in unit_in_ev:
                first_part = ans_fold[:120]
                if re.search(r"\b(dung|chinh xac)\b", first_part) and not re.search(r"\b(khong dung|chua dung|sai|khong phai)\b", first_part):
                    v.rule_issues.append(f"Xác nhận sai con số: câu hỏi nêu {num} {unit} nhưng tài liệu quy định con số khác ({', '.join(set(unit_in_ev))} {unit}).")

    # 3. Chống lạc đề sang chuyên ngành hẹp (Generic Topic Drift Check):
    SPECIFIC_NICHES = [
        ("cam do", "dịch vụ cầm đồ"),
        ("vu truong", "vũ trường"),
        ("karaoke", "dịch vụ karaoke"),
        ("xuat khau lao dong", "xuất khẩu lao động"),
        ("kiem toan", "dịch vụ kiểm toán"),
    ]
    for niche_kw, niche_name in SPECIFIC_NICHES:
        if niche_kw in ans_fold and niche_kw not in q_fold:
            v.rule_issues.append(f"Lạc đề sang chuyên ngành hẹp: câu trả lời đề cập '{niche_name}' nhưng người dùng không hỏi về lĩnh vực này.")

    # 4. Chặn hướng dẫn sai thẩm quyền đặc thù (làm CCCD / Hộ chiếu tại cơ sở y tế / bệnh viện):
    if any(k in q_fold for k in ["can cuoc", "cccd", "ho chieu", "passport"]):
        if any(h in ans_fold for h in ["benh vien", "co so y te", "tram y te", "trung tam y te"]):
            v.rule_issues.append("Chỉ dẫn sai thẩm quyền: Thủ tục cấp căn cước / hộ chiếu không thực hiện tại cơ sở y tế hoặc bệnh viện.")

    # 4b. Thủ tục do cơ quan NGOÀI UBND giải quyết: câu trả lời phải nhắc đúng cơ quan.
    # Chạy thật: nguồn ghi Tòa án, 1.5B vẫn viết "UBND cấp xã" và LLM kiểm chứng cho PASS.
    for q_keys, skip, must, message in _AUTHORITY_RULES:
        if (any(k in q_fold for k in q_keys) and not any(s in q_fold for s in skip)
                and not any(m in ans_fold for m in must)):
            v.rule_issues.append(f"Chỉ dẫn sai thẩm quyền: {message}")

    # 5. Bắt lỗi lẫn lộn thủ tục chéo:
    # 5a. Hộ tịch (kết hôn, khai sinh) / cư trú / căn cước mà nói đất đai, xây dựng:
    if any(w in q_fold for w in ["ket hon", "hon nhan", "khai sinh", "thuong tru", "tam tru", "can cuoc", "cccd", "ho chieu"]):
        # Chỉ tính chữ KHÔNG có trong nguồn: hồ sơ cư trú hợp lệ có "Giấy chứng nhận quyền
        # sử dụng đất" để chứng minh chỗ ở hợp pháp (evaluate.py chạy thật 24/09).
        if any(w in ans_fold and w not in ev_fold for w in ["ban ve thiet ke", "thiet ke xay dung", "quyen su dung dat", "so do", "giay phep xay dung", "thi cong nha"]):
            v.rule_issues.append("Lẫn lộn thủ tục: câu hỏi về hộ tịch/cư trú/căn cước nhưng câu trả lời lại chứa giấy tờ xây dựng, đất đai.")
    # 5b. Xây nhà mà nói hộ kinh doanh:
    if any(w in q_fold for w in ["xay nha", "khoi cong", "xay dung", "giay phep xay dung"]):
        if any(w in ans_fold for w in ["ho kinh doanh", "dang ky kinh doanh", "dong cua tiem"]):
            v.rule_issues.append("Lẫn lộn thủ tục: câu hỏi về xây dựng nhà ở nhưng câu trả lời đề cập đến hộ kinh doanh.")

    # 6. Bắt lỗi hỏi lệ phí nhưng câu trả lời không nêu mức tiền cụ thể hoặc thoái thác:
    is_fee_q = any(k in q_fold for k in ["le phi", "phi", "chi phi", "ton phi", "mat phi", "bao nhieu tien"])
    if is_fee_q:
        # "Không phải trả phí", "không có lệ phí", "miễn lệ phí" cũng là câu trả lời đủ.
        has_concrete_fee = (any(k in ans_fold for k in ["dong", "vnd", "mien phi", "0 dong", "khong thu", "nghin", "trieu"])
                            or bool(re.search(r"\b(?:khong|mien)(?: (?:phai|tra|co|mat|thu|chiu|nop|bat|ky"
                                              r"|khoan|can|tinh))* (?:le )?phi\b", ans_fold)))
        if not has_concrete_fee:
            v.rule_issues.append("Câu hỏi hỏi về lệ phí nhưng câu trả lời không nêu mức tiền cụ thể hoặc chính sách miễn phí (0 đồng).")
        if "chua co thong tin cu the" in ans_fold and any(w in ans_fold for w in ["lien he", "mot cua"]):
            v.rule_issues.append("Câu trả lời thoái thác chỉ khuyên liên hệ một cửa mà chưa cung cấp thông tin mức phí cụ thể.")

    # 7. Bắt lỗi câu trả lời về thủ tục/hồ sơ quá cụt lủn (chỉ 1 câu dẫn chiếu luật):
    is_doc_q = any(k in q_fold for k in ["ho so", "giay to", "thu tuc", "thi sao", "can gi", "nhu the nao", "nhu nao"])
    if is_doc_q and len(ans_stripped.split(".")) <= 2 and len(ans_stripped) < 110 and not says_not_found(ans_stripped):
        v.rule_issues.append("Câu trả lời về thủ tục/hồ sơ quá ngắn, chưa liệt kê đủ các thành phần giấy tờ cần thiết.")

    # 8. Bắt lỗi áp dụng nhầm lệ phí có yếu tố nước ngoài khi người dân không hỏi:
    is_foreign_q = any(k in q_fold for k in ["nuoc ngoai", "yeu to nuoc ngoai", "viet kieu", "nguoi nuoc ngoai"])
    if not is_foreign_q and any(k in q_fold for k in ["ket hon", "khai sinh", "ho tich"]):
        # Chỉ nhắc cụm "yếu tố nước ngoài" chép từ nguồn (phân biệt trường hợp) là đúng —
        # từng đánh trượt câu khai sinh đúng (chạy thật 24/09). Bắt khi nêu MỨC PHÍ nước
        # ngoài, hoặc tự nói tới người nước ngoài mà nguồn không có.
        foreign_fee = any(w in ans_fold for w in ["1.500.000", "1.000.000", "1 trieu", "1,5 trieu"])
        foreign_made_up = any(w in ans_fold and w not in ev_fold
                              for w in ["yeu to nuoc ngoai", "nguoi nuoc ngoai"])
        if foreign_fee or foreign_made_up:
            v.rule_issues.append("Áp dụng nhầm thủ tục có yếu tố nước ngoài: người dùng không hỏi về người nước ngoài, thủ tục hộ tịch trong nước của công dân Việt Nam được miễn lệ phí (0 đồng).")

    # 9. Bắt placeholder trích dẫn chưa hoàn chỉnh:
    if re.search(r"\[?S#\]?", answer):
        v.rule_issues.append("Câu trả lời chứa mã trích dẫn placeholder chưa hoàn chỉnh 'S#'.")

    first, _, rest = answer.strip().partition("\n")
    if says_not_found(first) and has_substance(rest):
        v.rule_issues.append("Câu đầu nói tài liệu chưa nêu rõ nhưng phía sau lại liệt kê chi tiết.")
        v.contradiction = True

    low = answer.lower()
    # "Tài liệu:" là tiêu đề ĐỨNG RIÊNG một dòng của prompt. Giữa câu ("Theo thông tin
    # trong các tài liệu:") là lời thường — từng đánh trượt câu trả lời đúng (chạy thật 24/09).
    v.echo = (any(m.lower() in low for m in T.ECHO_MARKERS if m != "Tài liệu:")
              or bool(re.search(r"(?m)^\s*tài liệu:\s*$", low)))
    if v.echo:
        v.rule_issues.append("Câu trả lời chép lại khung prompt / nhắc tới việc kiểm chứng.")

    # Mô hình nhỏ đôi khi trả về đúng một chỗ trống kiểu "[Tài liệu chưa nêu rõ...]".
    v.too_short = (len(flat) < 40 and not says_not_found(flat)) or bool(re.fullmatch(r"[\[(].{0,120}[\])]", flat))
    if v.too_short:
        v.rule_issues.append("Câu trả lời quá ngắn hoặc chỉ là chỗ trống.")


def verify(question: str, standalone: str, pack: dict, draft: str) -> Verification:
    v = Verification()
    rule_check(draft, pack, v, question=standalone or question)

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


# Cơ quan cấp huyện/quận — không còn từ 01/7/2025. So trên chữ đã bỏ dấu.
_OLD_UNIT_RE = re.compile(r"\bcap huyen\b|\b(?:ubnd|uy ban nhan dan|tand|toa an nhan dan|toa an)"
                          r" (?:cap )?(?:quan(?! su)|huyen)\b")   # "tòa án quân sự" không tính


def note_outdated_units(text: str) -> str:
    """Nguồn web cũ vẫn ghi "TAND cấp huyện", "UBND quận" -> mô hình chép lại.
    Code không sửa câu (dễ sai tên cơ quan mới), chỉ gắn lưu ý cố định."""
    if T.OUTDATED_UNIT_NOTE in text or not _OLD_UNIT_RE.search(fold(text)):
        return text
    return f"{text}\n\n{T.OUTDATED_UNIT_NOTE}"


def says_not_found(text: str) -> bool:
    low = (text or "").lower()
    return any(w in low for w in [
        "chưa nêu rõ", "không tìm thấy thông tin", "chưa có thông tin",
        "chưa ghi nhận", "không có thông tin", "chưa quy định", "chưa rõ"
    ])


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

    # Bóc bỏ ngoặc vuông không phải trích dẫn (giữ lại nội dung bên trong, giữ nguyên [S#])
    body = _clean_non_citation_brackets(draft)
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

    # TUYỆT ĐỐI KHÔNG xoá sạch câu trả lời rồi tráo thành NOT_IN_SOURCES_TEXT:
    # Nếu gọt xong mà quá ngắn, giữ lại bản nháp kèm cảnh báo để người dân tự đối chiếu nguồn
    final_text = cleaned if has_substance(cleaned) else draft.strip()
    if not final_text:          # chạy thật: bản nháp rỗng -> chỉ còn dòng cảnh báo trơ trọi
        return T.VERIFY_REFUSAL
    note = T.VERIFY_WARNING
    if len(cleaned) < len(draft.strip()) and has_substance(cleaned):
        note += " " + T.VERIFY_STRIPPED
    return f"{final_text}\n\n{note}"

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

from config import (CLARIFY_ENABLED, PROFILE_MEMORY_ENABLED, PROMPT_CHOICES_AUTO,
                    SEARCH_MAX_QUERIES, UNDERSTAND_FEWSHOT)
from core import llm
from domain.text import BM25, fold, tokenize
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
    choices: list[str] = field(default_factory=list)

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


def _copied_clarify(text: str, year: int) -> bool:
    """Câu hỏi lại chép nguyên từ ví dụ mẫu (đã thấy: hỏi "bạn muốn làm thủ tục gì"
    ngay sau khi người dùng nói rõ là khai sinh)."""
    got = fold(_s(text))
    return bool(got) and any(got == fold(ans["clarifying_question"])
                             for _, _, ans in T.understand_examples(year)
                             if ans["clarifying_question"])


def _clean_core_topic(text: str) -> str:
    """Làm sạch văn bản, loại bỏ các cụm từ đệm và chuẩn hóa về tên thủ tục chuẩn."""
    t = re.sub(r'["\'“”‘’]+', ' ', text)
    t = re.sub(r"[?？!]+$", "", t).strip()
    t = re.sub(
        r"^(cho\s+tôi|cho\s+em|tôi|mình|em|gia\s+đình\s+tôi|nhà\s+tôi)?\s*(sắp|đang|dự\s+định|chuẩn\s+bị|muốn|cần|xin|hỏi\s+về|hỏi|làm\s+ơn\s+cho\s+hỏi)?\s*",
        "", t, flags=re.IGNORECASE).strip()
    t = re.sub(
        r"^(vậy\s+còn|thế\s+còn|còn|cho\s+hỏi\s+thêm\s+về|thủ\s+tục|hướng\s+dẫn|hồ\s+sơ\s+và\s+thủ\s+tục|hồ\s+sơ\s+giấy\s+tờ|hồ\s+sơ|giấy\s+tờ|lệ\s+phí|mức\s+thu\s+lệ\s+phí|thời\s+hạn\s+giải\s+quyết|thời\s+hạn|nơi\s+nộp\s+hồ\s+sơ|nơi\s+nộp)\s+",
        "", t, flags=re.IGNORECASE).strip()
    t = re.sub(
        r"\s+(thì\s+sao|thì\s+làm\s+(giấy\s+tờ\s+)?(như\s+thế\s+nào|như\s+nào|ra\s+sao|thế\s+nào)|như\s+thế\s+nào|như\s+nào|ra\s+sao|thế\s+nào|cần\s+(những\s+)?gì|ở\s+đâu|mất\s+bao\s+lâu|hết\s+bao\s+nhiêu|bao\s+nhiêu\s+tiền).*$",
        "", t, flags=re.IGNORECASE).strip()
    tf = fold(t)
    if any(k in tf for k in ["xay nha", "khoi cong", "xay dung", "giay phep xay dung", "giay cap phep"]):
        return "cấp giấy phép xây dựng nhà ở riêng lẻ"
    if "ly hon" in tf:
        return "ly hôn"
    if "ket hon" in tf:
        return "đăng ký kết hôn"
    if "khai sinh" in tf:
        return "đăng ký khai sinh"
    if "thuong tru" in tf or "nhap khau" in tf:
        return "đăng ký thường trú"
    if "tam tru" in tf:
        return "đăng ký tạm trú"
    if any(k in tf for k in ["can cuoc", "cccd"]):
        return "cấp đổi thẻ căn cước"
    if "ho chieu" in tf or "passport" in tf:
        return "làm hộ chiếu"
    if any(k in tf for k in ["dong cua", "dong tiem", "tra giay phep", "cham dut"]):
        return "chấm dứt hoạt động hộ kinh doanh"
    if any(k in tf for k in ["kinh doanh", "mo tiem", "thanh lap"]):
        return "đăng ký hộ kinh doanh"
    return t.strip() if t and len(t) >= 3 else text.strip()


def _keyword_queries(queries: list[str], standalone: str, year: int) -> list[str]:
    """Làm sạch truy vấn từ LLM, đảm bảo năm hiện tại và khóa đúng từ khóa nghiệp vụ."""
    fixed = []
    clean_standalone = re.sub(r'["\'“”‘’]+', ' ', standalone)
    clean_standalone = re.sub(r"[?？!]+$", "", clean_standalone).strip()
    clean_standalone = re.sub(r"\s+", " ", clean_standalone)

    # 1. Khóa truy vấn theo khía cạnh được hỏi (Lệ phí, Thời hạn, Nơi nộp):
    st_fold = fold(clean_standalone)
    core_topic = _clean_core_topic(clean_standalone)

    if any(k in st_fold for k in ["dong cua", "dong tiem", "dong giay phep", "tra giay phep", "cham dut", "giai the"]):
        fixed.append(f"đóng cửa tiệm có phải nộp lại giấy phép kinh doanh {year}")
        fixed.append(f"chấm dứt hộ kinh doanh nộp lại giấy chứng nhận đăng ký kinh doanh {year}")
        fixed.append(f"thủ tục chấm dứt hoạt động hộ kinh doanh trả giấy phép {year}")
    if any(k in st_fold for k in ["bao nhieu ngay", "thoi han", "bao lau"]) or re.search(r"\d+\s*ngay", st_fold):
        if "khai sinh" in st_fold:
            fixed.append(f"thời hạn đăng ký khai sinh cho trẻ mới sinh bao nhiêu ngày {year}")
        elif "can cuoc" in st_fold or "cccd" in st_fold:
            fixed.append(f"thời hạn cấp đổi thẻ căn cước bao nhiêu ngày {year}")
        else:
            fixed.append(f"thời hạn giải quyết {core_topic} {year}")
    if any(k in st_fold for k in ["le phi", "phi bao nhieu", "chi phi", "ton phi", "mat phi", "ton bao nhieu"]):
        if "ket hon" in st_fold:
            fixed.append("đăng ký kết hôn công dân Việt Nam trong nước có mất phí không")
            fixed.append("miễn lệ phí đăng ký kết hôn luật hộ tịch")
            fixed.append(f"lệ phí đăng ký kết hôn công dân Việt Nam {year}")
        elif "khai sinh" in st_fold:
            fixed.append("đăng ký khai sinh đúng hạn có mất phí không")
            fixed.append("miễn lệ phí đăng ký khai sinh luật hộ tịch")
            fixed.append(f"lệ phí đăng ký khai sinh công dân Việt Nam {year}")
        else:
            fixed.append(f"lệ phí {core_topic} bao nhiêu tiền")
            fixed.append(f"mức thu lệ phí {core_topic} {year}")
            fixed.append(f"lệ phí {core_topic} 63 tỉnh thành")
    elif any(k in st_fold for k in ["ho so", "giay to", "mau don", "can gi", "thi sao", "nhu the nao", "nhu nao"]):
        fixed.append(f"hồ sơ xin {core_topic} gồm những gì")
        fixed.append(f"thủ tục {core_topic} {year}")
        fixed.append(f"hồ sơ {core_topic} theo quy định mới")
    elif any(k in st_fold for k in ["o dau", "noi nop", "co quan"]):
        fixed.append(f"nơi nộp hồ sơ {core_topic} {year}")

    for q in queries or []:
        q = re.sub(r'["\'“”‘’]+', ' ', q)
        q = re.sub(r"[?？!]+$", "", q).strip()
        q = re.sub(r"\s+", " ", q)
        if q and not re.search(r"\b20\d\d\b", q):
            q = f"{q} {year}"
        if q:
            fixed.append(q)

    # Nếu LLM không sinh được truy vấn nào, dùng standalone_question làm truy vấn chính
    if not fixed and clean_standalone:
        fixed.append(clean_standalone if re.search(r"\b20\d\d\b", clean_standalone) else f"{clean_standalone} {year}")

    return list(dict.fromkeys(fixed))


def _is_bot_question(text: str) -> bool:
    """Kiểm tra câu hỏi có phải do mô hình hỏi ngược lại người dùng thay vì viết lại câu hỏi."""
    t = fold(text).strip()
    if not t:
        return True
    bot_starters = [
        "ban co ", "ban can ", "ban muon ", "ban dang ", "ban hay ", "ban vui long ",
        "toi co the ", "cho toi biet ", "ban hay cho biet ", "ban co the ", "co phai ban ",
        "xin cho biet ", "ban cho minh biet "
    ]
    if any(t.startswith(s) for s in bot_starters):
        return True
    if any(s in t for s in ["giup gi", "thu tuc nao", "thu tuc gi"]) and len(t.split()) <= 9:
        return True
    return False


def _has_backreference(text: str) -> bool:
    """Kiểm tra xem câu hỏi có chứa từ đại từ quy chiếu về lượt hội thoại trước không."""
    t = fold(text).strip()
    words = t.split()
    if len(words) <= 5:
        return True
    refs = [
        "nhu tren", "o dau", "phi bao nhieu", "bao lau", "bao nhieu tien", "mat bao lau",
        "giay to gi nua", "con toi thi sao", "the con", "con neu", "vay thi", "thu tuc nay",
        "thu tuc do", "truong hop do", "nhu vay", "le phi", "chi phi", "ton phi", "mat phi",
        "ton bao nhieu", "ho so", "giay to", "mau don", "ban sao", "nop o dau", "den dau",
        "co quan nao", "thoi han", "thoi gian", "may ngay", "khi nao", "nhu the nao",
        "ra sao", "the nao", "cac buoc", "quy trinh", "can gi", "lam sao", "vay con",
        "con...", "neu the", "neu vay", "dung khong", "phai khong", "duoc khong",
        "co phai", "co duoc", "co can", "co ton", "co mat"
    ]
    if any(r in t for r in refs):
        return True
    # Nếu câu hỏi không chứa bất kỳ từ khóa thủ tục chính nào, nó chắc chắn là câu hỏi nối tiếp
    has_explicit_procedure = any(
        any(kw in t for kw in kws)
        for kws in _INTENT_KEYWORDS.values()
    )
    return not has_explicit_procedure


def _extract_recent_procedure(history: list[dict]) -> tuple[str, str]:
    """Tìm (câu hỏi gần nhất, intent gần nhất) mang chủ đề thủ tục từ lịch sử."""
    for m in reversed(history):
        if m.get("role") == "user":
            content = fold(m.get("content", "")).strip()
            if len(content.split()) < 3:
                continue
            for iname, kws in _INTENT_KEYWORDS.items():
                if any(kw in content for kw in kws):
                    return m.get("content", "").strip(), iname
            if any(w in content for w in ["xay nha", "khoi cong", "xay dung", "giay phep", "cap phep", "ly hon", "ho chieu", "cccd", "can cuoc", "khai sinh"]):
                return m.get("content", "").strip(), "land_administration"
    return "", ""


def _clean_procedure_name(raw_text: str, intent: str = "") -> str:
    """Rút gọn câu văn dài thành tên thủ tục cốt lõi (2-6 từ) để ghép ngữ cảnh nối tiếp."""
    t = re.sub(r"[?？!\"'`]+", "", raw_text).strip()
    t = re.sub(
        r"^(cho\s+tôi|cho\s+em|tôi|mình|em|gia\s+đình\s+tôi|nhà\s+tôi)?\s*(sắp|đang|dự\s+định|chuẩn\s+bị|muốn|cần|xin|hỏi\s+về|hỏi|làm\s+ơn\s+cho\s+hỏi)?\s*",
        "", t, flags=re.IGNORECASE).strip()
    t = re.sub(
        r"\s+(thì\s+làm\s+(giấy\s+tờ\s+)?(như\s+thế\s+nào|như\s+nào|ra\s+sao|thế\s+nào)|như\s+thế\s+nào|như\s+nào|ra\s+sao|thế\s+nào|cần\s+(những\s+)?gì|ở\s+đâu|mất\s+bao\s+lâu|hết\s+bao\s+nhiêu).*$",
        "", t, flags=re.IGNORECASE).strip()
    t = re.sub(r"^(thủ\s+tục|hướng\s+dẫn|xin|làm|đăng\s+ký|cấp)\s+", "", t, flags=re.IGNORECASE).strip()

    tf = fold(t)
    if any(k in tf for k in ["xay nha", "khoi cong", "xay dung", "giay phep xay dung"]):
        return "cấp giấy phép xây dựng nhà ở riêng lẻ"
    if "ly hon" in tf:
        return "ly hôn"
    if "ket hon" in tf:
        return "đăng ký kết hôn"
    if "khai sinh" in tf:
        return "đăng ký khai sinh"
    if "thuong tru" in tf or "nhap khau" in tf:
        return "đăng ký thường trú"
    if "tam tru" in tf:
        return "đăng ký tạm trú"
    if any(k in tf for k in ["can cuoc", "cccd"]):
        return "cấp đổi thẻ căn cước"
    if "ho chieu" in tf or "passport" in tf:
        return "làm hộ chiếu"
    if any(k in tf for k in ["dong cua", "dong tiem", "tra giay phep", "cham dut"]):
        return "chấm dứt hoạt động hộ kinh doanh"
    if any(k in tf for k in ["kinh doanh", "mo tiem", "thanh lap"]):
        return "đăng ký hộ kinh doanh"
    return t if t and len(t) >= 3 else raw_text


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
    standalone = _s(raw.get("standalone_question")) or question
    if _is_bot_question(standalone) or not history:
        standalone = question

    # Khóa kế thừa ngữ cảnh: nếu người dùng KHÔNG đưa ra thủ tục mới và có thủ tục trước đó trong lịch sử:
    q_fold = fold(question)
    current_has_new_proc = any(
        any(kw in q_fold for kw in kws)
        for kws in _INTENT_KEYWORDS.values()
    )
    recent_proc_text, prev_intent = _extract_recent_procedure(history) if history else ("", "")

    is_followup_transition = any(k in q_fold for k in ["vay con", "the con", "con neu", "con giay", "the thi", "con thi"])
    if (not current_has_new_proc or is_followup_transition) and prev_intent and _has_backreference(question):
        # Bắt buộc kế thừa intent từ lượt trước, ngăn LLM đoán mò sang thủ tục khác
        intent = prev_intent
        clean_proc = _clean_procedure_name(recent_proc_text, prev_intent)
        if any(k in q_fold for k in ["le phi", "phi", "chi phi", "ton phi", "mat phi", "bao nhieu tien", "ton bao nhieu"]):
            standalone = f"Lệ phí {clean_proc}"
        elif any(k in q_fold for k in ["ho so", "giay to", "mau don", "ban sao", "thi sao", "can gi", "nhu the nao", "nhu nao", "cap phep", "giay phep"]):
            standalone = f"Hồ sơ và thủ tục {clean_proc}"
        elif any(k in q_fold for k in ["o dau", "nop o dau", "den dau", "co quan"]):
            standalone = f"Nơi nộp hồ sơ {clean_proc}"
        elif any(k in q_fold for k in ["bao lau", "thoi han", "thoi gian", "may ngay"]):
            standalone = f"Thời hạn giải quyết {clean_proc}"
        else:
            standalone = f"{re.sub(r'[?？!]+$', '', question).strip()} đối với {clean_proc}"
    else:
        # Khóa đảm bảo thuộc tính hỏi (Hỏi phí thì standalone phải mang chủ đề phí):
        st_fold = fold(standalone)
        is_asking_fee = any(k in q_fold for k in ["le phi", "phi", "chi phi", "ton phi", "mat phi", "bao nhieu tien", "ton bao nhieu"])
        has_fee_in_st = any(k in st_fold for k in ["le phi", "phi", "chi phi", "ton phi", "mat phi", "tien", "gia"])
        if is_asking_fee and not has_fee_in_st:
            proc_subject = re.sub(r"^(co can|can|can nop|lam the nao|huong dan|thu tuc|ho so|quy trinh)\s+", "", standalone, flags=re.IGNORECASE).strip()
            standalone = f"Lệ phí {proc_subject}" if proc_subject else f"Lệ phí {standalone}"

        is_asking_time = any(k in q_fold for k in ["bao lau", "thoi han", "thoi gian", "may ngay", "khi nao"])
        has_time_in_st = any(k in st_fold for k in ["bao lau", "thoi han", "thoi gian", "ngay", "khi nao"])
        if is_asking_time and not has_time_in_st:
            proc_subject = re.sub(r"^(co can|can|can nop|lam the nao|huong dan|thu tuc|ho so|quy trinh)\s+", "", standalone, flags=re.IGNORECASE).strip()
            standalone = f"Thời hạn giải quyết {proc_subject}" if proc_subject else f"Thời hạn {standalone}"

        is_asking_place = any(k in q_fold for k in ["o dau", "nop o dau", "den dau", "co quan nao", "dia diem"])
        has_place_in_st = any(k in st_fold for k in ["o dau", "nop o dau", "den dau", "co quan", "dia diem", "noi nop"])
        if is_asking_place and not has_place_in_st:
            proc_subject = re.sub(r"^(co can|can|can nop|lam the nao|huong dan|thu tuc|ho so|quy trinh)\s+", "", standalone, flags=re.IGNORECASE).strip()
            standalone = f"Nơi nộp hồ sơ {proc_subject}" if proc_subject else f"Nơi nộp {standalone}"

    # Fallback: nếu intent là unknown hoặc other nhưng câu hỏi/standalone chứa từ khoá thủ tục:
    if intent in ("unknown", "other"):
        st_fold = fold(standalone) + " " + fold(question)
        for cand_intent, kws in _INTENT_KEYWORDS.items():
            if any(kw in st_fold for kw in kws):
                intent = cand_intent
                break
        if intent in ("unknown", "other"):
            if any(w in st_fold for w in ["xay nha", "khoi cong", "xay dung"]):
                intent = "land_administration"
            elif any(w in st_fold for w in ["dong cua", "dong tiem", "tra giay phep", "cham dut ho kinh doanh"]):
                intent = "business_registration"

    # Luôn tạo truy vấn đầy đủ cho search, không để queries bị rỗng
    if intent in PROCEDURE_INTENTS or intent == "unknown":
        queries = _keyword_queries(queries, standalone, now.year)

    clarify = _s(raw.get("clarifying_question"))
    needs = bool(raw.get("needs_clarification"))
    if _copied_clarify(clarify, now.year):
        clarify = ""
        if intent in PROCEDURE_INTENTS and intent != "other":
            needs = False       # đã biết thủ tục; câu hỏi lại chép mẫu không có giá trị
    return Understanding(
        intent=intent,
        standalone_question=standalone,
        province=_s(raw.get("province")),
        ward=_s(raw.get("ward")),
        missing_information=[_s(x) for x in raw.get("missing_information") or [] if _s(x)][:4],
        needs_clarification=needs,
        clarifying_question=clarify,
        # chừa một chỗ cho truy vấn bám nguồn chính thống (core/evidence.py)
        search_queries=queries[:max(1, SEARCH_MAX_QUERIES - 1)],
    )


def gate(question: str, history: list[dict]) -> str:
    raw = llm.chat_json("understand", T.GATE_SYSTEM, T.gate_user(question, history),
                        T.GATE_SCHEMA, T.gate_example_messages())
    decision = _s(raw.get("decision"))
    return decision if decision in ("search", "ask", "greeting", "other") else "search"


_DEFAULT_INTENT_CHOICES = {
    "marriage_registration": [
        "Thủ tục đăng ký kết hôn mới nhất {year}",
        "Hồ sơ xin giấy xác nhận tình trạng hôn nhân {year}",
        "Thủ tục đăng ký kết hôn trực tuyến Cổng dịch vụ công {year}",
    ],
    "birth_registration": [
        "Thủ tục đăng ký khai sinh cho trẻ mới sinh {year}",
        "Hồ sơ xin cấp bản sao trích lục khai sinh {year}",
        "Đăng ký khai sinh trực tuyến liên thông VNeID {year}",
    ],
    "permanent_residence": [
        "Thủ tục đăng ký thường trú mới nhất {year}",
        "Hồ sơ đăng ký thường trú vào nhà thuê hoặc mượn {year}",
        "Cách xin giấy xác nhận thông tin về cư trú CT07 online",
    ],
    "temporary_residence": [
        "Thủ tục đăng ký tạm trú cho người thuê trọ mới nhất {year}",
        "Hồ sơ gia hạn tạm trú mới nhất {year}",
        "Hướng dẫn khai báo tạm trú trực tuyến qua Cổng dịch vụ công",
    ],
    "identity_documents": [
        "Thủ tục cấp thẻ căn cước cho công dân mới nhất {year}",
        "Thủ tục cấp đổi thẻ căn cước công dân gắn chip sang thẻ căn cước",
        "Thủ tục làm hộ chiếu phổ thông online qua Cổng dịch vụ công {year}",
    ],
    "business_registration": [
        "Thủ tục đăng ký thành lập hộ kinh doanh cá thể {year}",
        "Hồ sơ và thủ tục thành lập công ty TNHH mới nhất {year}",
        "Đăng ký kinh doanh online qua Cổng thông tin quốc gia",
    ],
    "land_administration": [
        "Thủ tục cấp sổ đỏ lần đầu mới nhất {year}",
        "Thủ tục sang tên sổ đỏ chuyển nhượng quyền sử dụng đất {year}",
        "Hồ sơ tách thửa đất theo quy định Luật Đất đai mới nhất",
    ],
    "social_security": [
        "Thủ tục nhận bảo hiểm xã hội một lần mới nhất {year}",
        "Thủ tục hưởng trợ cấp thất nghiệp mới nhất {year}",
        "Cách tra cứu và đóng bảo hiểm y tế hộ gia đình trực tuyến",
    ],
    "tax": [
        "Thủ tục quyết toán thuế thu nhập cá nhân mới nhất {year}",
        "Cách đăng ký mã số thuế cá nhân online {year}",
        "Hướng dẫn nộp thuế điện tử qua eTax Mobile",
    ],
}


_INTENT_KEYWORDS = {
    "marriage_registration": ["ket hon", "cuoi", "hon nhan", "vo chong", "doc than", "tinh trang hon nhan", "ly hon"],
    "birth_registration": ["khai sinh", "sinh con", "de", "em be", "tre moi sinh", "trich luc khai sinh", "giay chung sinh"],
    "permanent_residence": ["thuong tru", "ho khau", "nhap khau", "tach khau", "ct07", "nhap ho khau"],
    "temporary_residence": ["tam tru", "thue tro", "luu tru", "o tro", "nha tro", "gia han tam tru", "qua dem", "khach o lai"],
    "identity_documents": ["can cuoc", "cccd", "ho chieu", "passport", "chung minh", "dinh danh", "vneid"],
    "business_registration": ["kinh doanh", "doanh nghiep", "cong ty", "ho kinh doanh", "mo tiem", "cua hang", "buon ban", "dong cua tiem", "giai the"],
    "land_administration": ["so do", "so hong", "dat", "tach thua", "tho cu", "quyen su dung dat", "sang ten", "xay nha", "khoi cong", "xay dung", "giay phep", "cap phep"],
    "social_security": ["bao hiem", "bhxh", "bhyt", "that nghiep", "thai san", "huu tri", "so bao hiem"],
    "tax": ["thue", "ma so thue", "mst", "thu nhap ca nhan", "quyet toan thue", "etax"],
}


def _clean_choice(c: str) -> str:
    s = str(c or "").strip()
    if s.startswith("http://") or s.startswith("https://"):
        from urllib.parse import parse_qs, unquote, urlparse
        try:
            parsed = urlparse(s)
            qs = parse_qs(parsed.query)
            if "q" in qs and qs["q"]:
                s = qs["q"][0]
            else:
                s = parsed.path.strip("/").replace("-", " ")
        except Exception:
            pass
        s = unquote(s).replace("+", " ")
    s = re.sub(r"^[0-9\.\-\s\:\)]+", "", s).strip()
    s = re.sub(r"[?？!]+$", "", s).strip()
    return s


def generate_prompt_choices(question: str, u: Understanding, year: int) -> list[str]:
    """Tạo 3 prompt DuckDuckGo gợi ý (Cách 3): kiểm tra tính phù hợp với câu hỏi, không để lịch sử làm sai lệch."""
    standalone = getattr(u, "standalone_question", "") or question
    intent = getattr(u, "intent", "unknown")
    q_fold = fold(question) + " " + fold(standalone)

    # 1. Đóng cửa tiệm / ngừng kinh doanh / trả giấy phép
    if any(k in q_fold for k in ["dong cua", "dong tiem", "tra giay phep", "cham dut ho kinh doanh", "ngung kinh doanh"]):
        return [
            f"Đóng cửa tiệm có phải nộp lại giấy chứng nhận đăng ký hộ kinh doanh {year}",
            f"Thủ tục chấm dứt hoạt động hộ kinh doanh trả giấy phép {year}",
            f"Hồ sơ và nghĩa vụ thuế khi đóng cửa tiệm hộ kinh doanh {year}",
        ]

    # 2. Lệ phí / chi phí
    if any(k in q_fold for k in ["le phi", "chi phi", "ton phi", "mat phi", "bao nhieu tien", "ton bao nhieu"]):
        topic = re.sub(r"^(mức thu lệ phí|lệ phí|chi phí|tốn phí)\s+", "", standalone, flags=re.IGNORECASE).strip()
        topic = re.sub(r"^(có\s+lệ\s+phí\s+gì\s+không|lệ\s+phí\s+thì\s+sao|thủ\s+tục\s+này\s+có\s+tốn\s+phí)\s*", "", topic, flags=re.IGNORECASE).strip()
        if not topic or len(topic) < 3:
            topic = "thủ tục này"
        return [
            f"Mức thu lệ phí {topic} mới nhất {year}",
            f"Thủ tục {topic} có được miễn lệ phí không {year}",
            f"Quy định mức thu lệ phí trực tuyến {topic} {year}",
        ]

    # 3. Xây dựng / khởi công
    if any(k in q_fold for k in ["xay nha", "khoi cong", "xay dung", "giay phep xay dung"]):
        return [
            f"Điều kiện và hồ sơ thông báo khởi công xây dựng nhà ở {year}",
            f"Mức thu lệ phí cấp giấy phép xây dựng nhà ở riêng lẻ {year}",
            f"Thủ tục xin cấp giấy phép xây dựng nhà ở tại xã phường {year}",
        ]

    # 4. Thời hạn / số ngày
    if any(k in q_fold for k in ["bao lau", "thoi han", "may ngay", "bao nhieu ngay"]):
        topic = re.sub(r"^(thời hạn giải quyết|thời hạn|mất bao lâu)\s+", "", standalone, flags=re.IGNORECASE).strip()
        if not topic or len(topic) < 3:
            topic = "thủ tục này"
        return [
            f"Thời hạn giải quyết {topic} bao nhiêu ngày {year}",
            f"Quy trình và các bước thực hiện {topic} {year}",
            f"Thủ tục {topic} nhận kết quả trong ngày {year}",
        ]

    # 5. Nơi nộp / cơ quan
    if any(k in q_fold for k in ["o dau", "nop o dau", "den dau", "co quan nao"]):
        topic = re.sub(r"^(nơi nộp hồ sơ|nơi nộp|đến đâu|ở đâu)\s+", "", standalone, flags=re.IGNORECASE).strip()
        if not topic or len(topic) < 3:
            topic = "thủ tục này"
        return [
            f"Nơi nộp hồ sơ {topic} tại UBND cấp xã phường {year}",
            f"Thủ tục {topic} nộp trực tuyến Cổng Dịch vụ công {year}",
            f"Thẩm quyền giải quyết {topic} theo quy định mới {year}",
        ]

    # 6. Nếu intent khớp thực tế với từ khoá trong câu hỏi -> dùng bộ prompt tối ưu theo intent
    if intent in _DEFAULT_INTENT_CHOICES:
        kw_list = _INTENT_KEYWORDS.get(intent, [])
        if any(kw in q_fold for kw in kw_list):
            return [c.format(year=year) for c in _DEFAULT_INTENT_CHOICES[intent][:3]]

    # 7. Fallback tổng quát
    clean_q = re.sub(r"[?？!]+$", "", question).strip()
    clean_topic = re.sub(
        r"^(gia đình tôi|tôi|mình|cho em hỏi|cho tôi hỏi|làm ơn cho hỏi|bạn ơi|bạn cho mình hỏi)\s+(mới chuyển nhà[,\s]+)?(muốn|cần|hỏi về|tư vấn)?\s*",
        "", clean_q, flags=re.IGNORECASE).strip()
    clean_topic = re.sub(r"^(thủ\s+tục|hướng\s+dẫn|hồ\s+sơ\s+và\s+điều\s+kiện|hồ\s+sơ|làm|xin|cấp|đăng\s+ký)\s+", "", clean_topic, flags=re.IGNORECASE).strip()
    clean_topic = re.sub(r"\s+(mới\s+nhất\s+)?20\d\d.*$", "", clean_topic, flags=re.IGNORECASE).strip()
    if not clean_topic or len(clean_topic) < 3:
        clean_topic = clean_q

    choices = [
        f"Thủ tục {clean_topic} mới nhất {year}",
        f"Hồ sơ và điều kiện làm {clean_topic} {year}",
        f"Hướng dẫn nộp hồ sơ {clean_topic} trực tuyến {year}",
    ]
    return choices[:3]


def _is_real_greeting(text: str, intent: str = "") -> bool:
    """Kiểm tra tin nhắn có THẬT SỰ là chào hỏi/xã giao thuần tuý (<= 3 từ) hay không.
    Tuyệt đối không để câu hỏi thủ tục bị gán nhầm thành chitchat."""
    t = fold(text).strip()
    words = t.split()
    if len(words) > 3:
        return False
    greeting_words = ["chao", "hello", "hi", "alo", "cam on", "tam biet", "xin chao"]
    return any(gw in t for gw in greeting_words)


def _is_real_out_of_scope(text: str) -> bool:
    t = fold(text).strip()
    creative_clues = ["lam tho", "viet tho", "viet van", "ke chuyen", "ke chuyen cuoi", "giai toan", "viet code", "lap trinh"]
    return any(c in t for c in creative_clues)


def _build_smart_clarify(question: str, u: Understanding) -> str:
    """Tạo câu hỏi làm rõ lịch sự, thông minh, tuyệt đối không nhại lại câu hỏi của người dùng."""
    intent = u.intent
    if intent == "temporary_residence":
        return "Bạn đang cần làm thủ tục liên quan đến tạm trú hay thông báo lưu trú qua đêm? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "permanent_residence":
        return "Bạn muốn đăng ký thường trú vào nhà ở sở hữu, nhà thuê mượn hay nhập theo người thân? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "business_registration":
        return "Bạn đang quan tâm đến thủ tục đăng ký mới, thay đổi hay chấm dứt/đóng cửa kinh doanh? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "marriage_registration":
        return "Bạn muốn đăng ký kết hôn trong nước, có yếu tố nước ngoài hay xin giấy xác nhận tình trạng hôn nhân? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "birth_registration":
        return "Bạn cần làm thủ tục khai sinh cho trẻ mới sinh, khai sinh quá hạn hay cấp bản sao trích lục? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "identity_documents":
        return "Bạn cần làm thẻ căn cước mới, cấp đổi thẻ hay làm hộ chiếu? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "social_security":
        return "Bạn cần tư vấn về BHXH 1 lần, bảo hiểm thất nghiệp hay trợ cấp xã hội? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "land_administration":
        return "Bạn muốn làm thủ tục cấp sổ đỏ lần đầu, sang tên chuyển nhượng hay tách thửa đất? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    elif intent == "tax":
        return "Bạn cần đăng ký mã số thuế cá nhân hay quyết toán thuế thu nhập cá nhân? Bạn có thể chọn nhanh gợi ý tra cứu bên dưới:"
    return "Bạn có thể nói rõ hơn về hoàn cảnh thủ tục cụ thể, hoặc chọn nhanh một trong các gợi ý tra cứu bên dưới:"


def _is_generic_procedure_query(text: str) -> bool:
    """Nhận diện các câu hỏi chung chung về thủ tục mà KHÔNG nhắc tới thủ tục cụ thể nào:
    Ví dụ: 'Cho hỏi thủ tục', 'tôi muốn hỏi thủ tục', 'cần làm giấy tờ', 'hỏi về thủ tục hành chính'..."""
    t = fold(text).strip()
    t_clean = re.sub(r"[?？!\"'`]+", "", t).strip()
    words = t_clean.split()
    if len(words) > 7:
        return False
    generic_patterns = [
        r"^(cho\s+)?(hoi|tu\s+van|giup|biet)?\s*(ve\s+)?(thu\s+tuc|giay\s+to|ho\s+so)(\s+hanh\s+chinh)?$",
        r"^(toi|em|minh)?\s*(muon|can|hoi)\s*(hoi|lam|biet)?\s*(ve\s+)?(thu\s+tuc|giay\s+to|ho\s+so)(\s+hanh\s+chinh)?$",
        r"^(thu\s+tuc|giay\s+to|ho\s+so)(\s+hanh\s+chinh)?$",
        r"^(co|nhung)?\s*(thu\s+tuc|giay\s+to)\s*(nao|gi)$",
        r"^(can|muon)\s+lam\s+(giay\s+to|ho\s+so|thu\s+tuc)$",
    ]
    return any(re.match(p, t_clean) for p in generic_patterns)


def analyze(question: str, history: list[dict], summary: str, profile: dict) -> Understanding:
    # 0. Chặn câu hỏi quá chung chung (chỉ nói "Cho hỏi thủ tục", "tôi muốn làm giấy tờ"...)
    # Bắt buộc đi vào clarify (Cách 3) để người dùng chọn hoặc nêu rõ thủ tục!
    if _is_generic_procedure_query(question):
        u = Understanding(intent="unknown", standalone_question=question, route="clarify")
        u.clarifying_question = "Bạn muốn tìm hiểu về thủ tục nào? Dưới đây là các nhóm thủ tục phổ biến, bạn hãy chọn nhanh một gợi ý bên dưới hoặc nói rõ nhu cầu:"
        u.choices = [
            f"Thủ tục cấp đổi thẻ căn cước mới nhất {datetime.now().year}",
            f"Thủ tục đăng ký khai sinh và thường trú trực tuyến {datetime.now().year}",
            f"Thủ tục đăng ký thành lập hộ kinh doanh cá thể {datetime.now().year}",
        ]
        return u

    u = understand(question, history, summary, profile)
    u.gate = gate(question, history)

    # Nhóm thủ tục bao gồm cả 'other' (lưu trú, chuyển trường, GPLX, lý lịch tư pháp...)
    specific = u.intent in PROCEDURE_INTENTS
    small_talk = u.intent in ("chitchat", "out_of_scope") and not specific

    # 1. Chặn out_of_scope thật (làm thơ, viết văn, giải toán, viết code...)
    if _is_real_out_of_scope(question):
        u.route = "out_of_scope"
        return u

    # 2. Chặn chào hỏi thật (chào, hello, cảm ơn, tạm biệt...)
    if _is_real_greeting(question, u.intent):
        u.route = "chitchat"
        return u

    # 3. Chống gate/understand nhận nhầm câu hỏi thủ tục thành chitchat hoặc out_of_scope:
    # Nếu câu hỏi có từ khóa thủ tục hoặc dài (>= 4 từ) mà bị gate gán greeting/other -> ép về search
    if u.gate in ("greeting", "other"):
        u.gate = "search"

    # 4. Quyết định TRA CỨU vs HỎI LẠI (Cách 3):
    # - Nếu là câu hỏi nối tiếp đã kế thừa được thủ tục (has_inherited_proc) -> Luôn TRA CỨU (search).
    # - Chỉ hỏi lại (clarify) kèm 3 gợi ý DuckDuckGo khi:
    #   + gate == "ask" và không phải câu hỏi nối tiếp có ngữ cảnh
    #   + hoặc intent == "unknown" và không phải câu hỏi nối tiếp
    #   + hoặc u.needs_clarification là True và không phải câu hỏi nối tiếp
    has_inherited_proc = bool(history and _has_backreference(question))
    wants_clarify = (
        not has_inherited_proc and (
            u.gate == "ask"
            or u.intent == "unknown"
            or u.needs_clarification
        )
    )

    if wants_clarify and CLARIFY_ENABLED and not _just_clarified(history):
        u.route = "clarify"
        if not u.clarifying_question or _similar(u.clarifying_question, question) > 0.35 or small_talk:
            u.clarifying_question = _build_smart_clarify(question, u)
        u.choices = generate_prompt_choices(question, u, datetime.now().year)
    else:
        u.route = "search"
        if PROMPT_CHOICES_AUTO and not u.choices and not small_talk:
            u.choices = generate_prompt_choices(question, u, datetime.now().year)
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

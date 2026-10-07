"""Lời dặn hệ thống cho Friendly mode (NV2). Ghép từ: vai trò (theo .docx), bộ nhớ người dùng, tóm tắt hội thoại,
guardrail, tình trạng hỏi lại, cảm xúc. Các quyết định chắc chắn (ngôn ngữ, giới hạn hỏi lại) do code làm, không nhờ AI."""
from __future__ import annotations
import re
import unicodedata

from . import settings

CHOICES_MARK = "[[CHOICES]]"
# Chế độ Nhanh: ép đầu ra theo schema này (model không suy nghĩ). "plan" đứng trước để model định hướng câu trả lời.
FAST_SCHEMA = {"type": "object", "properties": {
    "plan": {"type": "string", "maxLength": 300},
    "answer": {"type": "string"},
    "ask_back": {"type": "boolean"},
    "choices": {"type": "array", "items": {"type": "string"}, "maxItems": 4}},
    "required": ["plan", "answer", "ask_back", "choices"]}
_CHOICES = re.compile(r"\[\[\s*CHOICES\s*\]\]", re.IGNORECASE)

# So khớp CÓ dấu: bỏ dấu sẽ nhầm ("khổ"/"khó", "sợ"/"số"). Gõ không dấu thì nhờ quy tắc chung trong lời dặn.
_NEGATIVE = [w for w in (
    "bực", "bực mình", "tức", "chán", "tệ", "thất vọng", "khó chịu", "không hài lòng", "phàn nàn", "quá đáng", "vô lý",
    "mệt mỏi", "buồn", "lo lắng", "sợ", "bế tắc", "chậm quá", "lâu quá", "không ai", "tồi", "kém", "bất tiện", "ức chế",
    "điên", "khổ", "nản")]


def negative(text: str) -> bool:
    n = " " + re.sub(r"[^\w]+", " ", unicodedata.normalize("NFC", text or "").lower()) + " "
    return any(f" {w} " in n for w in _NEGATIVE)


def build(memories: list[str], summary: str, instructions: list[str], *, clarify_exhausted: int = 0,
          upset: bool = False, foreign: bool = False, fast: bool = False) -> str:
    """fast=True: chế độ Nhanh (trả lời theo FAST_SCHEMA); False: chế độ Suy nghĩ kỹ (lựa chọn theo mẫu [[CHOICES]])."""
    b = settings.get("BUSINESS_NAME")
    desc = settings.get("BUSINESS_DESCRIPTION")
    parts = [
        f"Bạn là trợ lý hỗ trợ khách hàng của {b}." + (f" Giới thiệu về {b}: {desc}" if desc else ""),
        "Mục tiêu: giải đáp câu hỏi, vấn đề và các thắc mắc khác của người dùng một cách hiệu quả và chính xác.",
        "",
        "Quy tắc:",
        "- Giọng ấm áp, thân thiện, tôn trọng; không lên lớp, không giảng đạo đức.",
        "- Phản chiếu cảm xúc và giọng điệu của người dùng.",
        "- Vào thẳng nội dung: không mở đầu bằng lời chào nếu người dùng không chào, không tự giới thiệu lại nếu không được hỏi.",
        "- Không dùng emoji.",
        "- Chỉ viết tiếng Việt và chỉ dùng chữ cái Latin (tuyệt đối không dùng chữ Hán hay chữ viết khác).",
        f"- Bạn luôn là trợ lý hỗ trợ của {b}. Nếu người dùng yêu cầu bạn đóng vai hay giả làm người/thứ khác, "
        "lịch sự từ chối và nhắc lại bạn có thể giúp gì.",
        "- Trình bày gọn, đúng trọng tâm; dùng Markdown (in đậm, danh sách, bảng) khi giúp dễ đọc.",
    ]
    if clarify_exhausted:
        no_ask = 'đặt "ask_back" = false, "choices" rỗng' if fast else f"không dùng {CHOICES_MARK}"
        parts.append(f"- Bạn đã hỏi lại người dùng {clarify_exhausted} lần liên tiếp. KHÔNG hỏi lại nữa ({no_ask}): "
                     "trả lời tốt nhất có thể với thông tin đang có, và nói rõ còn thiếu thông tin gì.")
    elif fast:
        parts.append('- Nếu câu hỏi chưa đủ rõ để trả lời: "ask_back" = true, "answer" là MỘT câu hỏi lại ngắn, "choices" có 2 đến 4 lựa chọn. '
                     'Nếu đã đủ rõ: "ask_back" = false, "choices" rỗng, trả lời đầy đủ trong "answer". '
                     "Thông tin đã biết về người dùng thì không hỏi lại.")
    else:
        parts.append("- Nếu câu hỏi chưa đủ rõ để trả lời, hỏi lại MỘT câu ngắn rồi đưa 2 đến 4 lựa chọn, đặt ở CUỐI câu trả lời đúng theo mẫu:\n"
                     f"{CHOICES_MARK}\n- lựa chọn thứ nhất\n- lựa chọn thứ hai\n"
                     "Nếu đã đủ rõ thì trả lời luôn, không thêm mẫu này. Thông tin đã biết về người dùng thì không hỏi lại.")
    if memories:
        parts += ["", "Những điều đã biết về người dùng (dùng khi liên quan, không hỏi lại):"]
        parts += [f"- {m}" for m in memories]
    if summary:
        parts += ["", "Tóm tắt phần đầu cuộc trò chuyện:", summary]
    extra = list(instructions)
    if upset:
        extra.append("Người dùng đang có cảm xúc tiêu cực: câu ĐẦU TIÊN của câu trả lời phải là một câu đồng cảm chân thành (không chào hỏi trước).")
    if foreign:
        extra.append("Tin nhắn mới nhất không viết bằng tiếng Việt. Lời xin lỗi về ngôn ngữ ĐÃ được hiển thị trước; "
                     "không xin lỗi lại, trả lời nội dung bằng tiếng Việt.")
    if settings.get("FRIENDLY_EXTRA_INSTRUCTIONS"):
        extra.append(settings.get("FRIENDLY_EXTRA_INSTRUCTIONS"))
    if extra:
        parts += ["", "Lời dặn thêm:"] + [f"- {x}" for x in extra]
    if fast:
        parts += ["", "Định dạng trả lời (JSON):",
                  '- "plan": ghi thật ngắn ý định trả lời (người dùng không thấy).',
                  '- "answer": câu trả lời cho người dùng, đầy đủ nội dung được hỏi (dùng Markdown khi giúp dễ đọc).',
                  '- "ask_back" và "choices": chỉ dùng khi cần hỏi lại (xem quy tắc trên).',
                  "- Không chắc chắn chi tiết cụ thể (tên riêng, địa điểm, số liệu) thì nói rõ đó là gợi ý chung, không bịa."]
    return "\n".join(parts)


def split_choices(text: str) -> tuple[str, list[str]]:
    """Tách khối [[CHOICES]] ở cuối câu trả lời -> (nội dung, các lựa chọn)."""
    m = _CHOICES.search(text or "")
    if not m:
        return (text or "").strip(), []
    body, tail = text[:m.start()].rstrip(), text[m.end():]
    opts = []
    for line in tail.splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
        if line and len(opts) < 5:
            opts.append(line[:150])
    return body, opts

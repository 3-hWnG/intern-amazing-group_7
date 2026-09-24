"""pipeline.py — System 2: điều phối MỘT lượt hỏi-đáp cho chat_routes.py.

Đặt tên KHÁC "orchestrator.py" có chủ đích — tránh đụng tên với
`app/core/orchestrator.py` (System 1) khi cả hai cùng bị import, tránh nhầm
lẫn giữa `from core import orchestrator` (System 1, class TurnResult) và một
module "orchestrator" thứ hai ở system2/.

Luồng:
  0. intent_type != "procedure" (Fix 1 Ngày Thứ 5, 23/09/2026 — extractor.
     resolve() đã tự bỏ qua FTS5 cho 2 case này, xem extractor.py):
     - "chitchat" -> trả lời chào xã giao ngắn gọn, kind="chitchat".
     - "out_of_scope" -> từ chối lịch sự, kind="out_of_scope".
     CẢ HAI KHÔNG gán `choices` — đồng nhất với app/core/orchestrator.py
     (System 1 cũng loại trừ out_of_scope khỏi auto-choices, xem dòng
     `res.kind != "out_of_scope"`), tránh chat.js::choiceBox() hiểu nhầm
     (useWebSearchSwitch chỉ bật đúng cho kind="not_in_sources").
  1. intent_type == "procedure" nhưng found=False hoặc confident=False (FTS5 +
     LLM1 không tìm ra thủ tục nào đáng tin — có thể xảy ra ở BẤT KỲ lượt
     nào, không riêng Turn 1, ví dụ người dùng đột ngột hỏi thứ hoàn toàn
     ngoài 70 thủ tục dù đang có Thẻ mở):
     trả `kind="not_in_sources"` kèm câu báo lỗi chuẩn (extractor.format_not_found)
     và choices gợi ý chuyển System 1.
  2. found=True, confident=True:
     - Có Thẻ đang mở (Messages.latest_by_kind(..., "procedure_card")) VÀ
       cùng proc_code -> Turn 2+ cùng thủ tục -> LLM 2 Customer Care
       (customer_care.answer_procedure_query), kind="answer".
     - Ngược lại (chưa có Thẻ nào, hoặc đã chuyển sang thủ tục khác)
       -> Turn 1 mới -> render Thẻ (service.render_card), kind="procedure_card".

Trả về đúng instance `core.orchestrator.TurnResult` — KHÔNG dùng dict hay
class tự chế. `app/api/chat_routes.py::_run_job` (dòng ~176-195) truy cập kết
quả bằng attribute (`result.intent`, `result.choices`, `result.evidence`...);
trả dict sẽ AttributeError ngay ở `dict(result.intent)`.
"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
APP_DIR = HERE.parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core.orchestrator import TurnResult  # noqa: E402
from db.repositories import Messages  # noqa: E402

import customer_care  # noqa: E402  (cùng thư mục system2/)
import extractor  # noqa: E402
import service as s2  # noqa: E402

_NOOP_STATUS: Callable[[str], None] = lambda _: None

_CARD_TITLE_RE = re.compile(r'<h3 class="proc-title">\s*📋\s*(.*?)</h3>', re.DOTALL)

# Ngày Thứ 5 (23/09/2026, Fix 2 -- chống ngộ độc lịch sử): mirror ĐÚNG logic đã
# kiểm chứng ở app/prompts/templates.py::history_messages() (System 1) thay vì
# chỉ cắt content[:120] thô -- nếu câu trả lời của Customer Care bắt đầu bằng
# 1 gạch đầu dòng (rất hay gặp, vd "- Hồ sơ gồm:..."), cắt thô vẫn để lọt tên
# thủ tục CŨ vào context của LLM1, không giải quyết đúng gốc vấn đề.
_FILLER_PREFIX_RE = re.compile(
    r"^(từ tài liệu được cung cấp|theo tài liệu|dưới đây là|hướng dẫn cụ thể)[\s:\-]*",
    re.IGNORECASE,
)
_BULLET_PREFIXES = ("-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "#")


def _clean_assistant_text(content: str) -> str:
    """Rút câu mở đầu ngắn gọn (<=140 ký tự) từ 1 lượt trả lời dài của trợ lý
    (Customer Care Turn 2+, chitchat...) để nhét vào lịch sử gửi LLM1 -- bỏ
    hết gạch đầu dòng/checklist thủ tục CŨ, mô hình nhỏ (1.5B) dễ bị "khoá
    cứng" vào thủ tục trước đó nếu thấy nguyên cả bảng dữ liệu cũ trong lịch
    sử. Không tìm được dòng nào sạch -> câu mặc định trung tính."""
    lines = [l.strip() for l in (content or "").split("\n") if l.strip()]
    for l in lines:
        l_clean = _FILLER_PREFIX_RE.sub("", l).strip()
        if l_clean and not l_clean.startswith(_BULLET_PREFIXES):
            return l_clean[:140]
    return "Tôi đã cung cấp thông tin thủ tục theo tài liệu."


def _procedure_name_from_card_html(html_text: str) -> str | None:
    """Rút TÊN thủ tục ra khỏi HTML Thẻ đã lưu (khớp đúng khuôn cố định mà
    service.render_card() sinh ra). Dùng để đưa 1 dòng NGẮN, AN TOÀN (không
    phải HTML thô) vào lịch sử gửi LLM1 — nhét thẳng HTML thô vào prompt sẽ
    làm rối cả LLM1 lẫn phép đo token, và extractor.py trước giờ chỉ được test
    với lịch sử toàn chữ (xem test_extractor.py), CHƯA từng chạy thật với 1
    Thẻ HTML thật nằm trong lịch sử hội thoại."""
    if not html_text:
        return None
    m = _CARD_TITLE_RE.search(html_text)
    if not m:
        return None
    return html_lib.unescape(m.group(1)).strip()


def _history_for_extractor(history: list[dict] | None) -> list[dict]:
    """LLM1 cần thấy TÊN thủ tục đã hiển thị ở lượt trước để bắt đúng
    follow-up ("lệ phí bao nhiêu" không nhắc lại tên) — nhưng không được thấy
    HTML thô của Thẻ, không thấy câu trả lời dài của Customer Care, và KHÔNG
    thấy các lượt chào hỏi/xã giao/ngoài phạm vi (chứa từ 'thủ tục hành chính'
    dễ làm model 1.5B trích nhầm)."""
    out = []
    for h in history or []:
        kind = h.get("kind") or ""
        # ponytail: bỏ qua lượt chitchat/out_of_scope, không chứa thông tin thủ tục
        if kind in ("chitchat", "out_of_scope"):
            continue
        role = h.get("role")
        content = h.get("content") or ""
        if kind == "procedure_card":
            name = _procedure_name_from_card_html(content)
            content = (f"[Đã hiển thị Thẻ thủ tục: {name}]" if name
                       else "[Đã hiển thị Thẻ thông tin thủ tục]")
        elif role == "assistant":
            content = _clean_assistant_text(content)
        else:
            content = content.strip()[:250]
        out.append({"role": role, "content": content})
    return out


def _active_proc_code(active: dict | None) -> str | None:
    if not active or not active.get("intent_json"):
        return None
    try:
        return json.loads(active["intent_json"]).get("proc_code")
    except Exception:
        return None


def run_turn_system2(conv_id: int, question: str, history: list[dict] | None,
                      status: Callable[[str], None] = _NOOP_STATUS) -> TurnResult:
    status("Đang tra cứu CSDL nội bộ…")
    conn = s2.connect()
    try:
        active = Messages.latest_by_kind(conv_id, "procedure_card")
        result = extractor.resolve(question, history=_history_for_extractor(history), conn=conn)
        intent_type = result["extracted"]["intent_type"]

        if intent_type == "chitchat":
            return TurnResult(
                kind="chitchat",
                text=("Xin chào bạn! Tôi là Trợ lý Dịch vụ công, hỗ trợ tra cứu "
                      "thủ tục hành chính. Bạn cần hỏi về thủ tục gì ạ?"),
                intent={"facet": "tong_quan"},
            )
        if intent_type == "out_of_scope":
            return TurnResult(
                kind="out_of_scope",
                text=("Xin lỗi, tôi chỉ hỗ trợ tra cứu thông tin thủ tục hành chính "
                      "nhà nước nên không giúp được việc này. Bạn có câu hỏi nào về "
                      "thủ tục hành chính không?"),
                intent={"facet": "tong_quan"},
            )

        if not result["found"] or not result["confident"]:
            # Lỗi phát hiện 24/09/2026: choices trước đây là NHÃN CTA TĨNH
            # ("Tra cứu Web trực tiếp với System 1") — chat.js::choiceBox()
            # gửi ĐÚNG CHUỖI của choice làm truy vấn thật khi bấm
            # (window.triggerWebSearch(choice)), nên bấm nút này KHÔNG tra
            # cứu câu hỏi của người dùng mà tra cứu đúng cái nhãn nút, khiến
            # System 1 tìm kiếm/tổng hợp câu trả lời cho một chủ đề vô nghĩa.
            # Sửa: gửi từ khóa THẬT (extractor đã chuẩn hoá) làm choices, và
            # nếu extractor không trích được keyword nào thì fallback về
            # đúng câu hỏi gốc của người dùng — KHÔNG BAO GIỜ còn là nhãn.
            fallback_query = result["extracted"].get("primary_keyword") or question
            return TurnResult(
                kind="not_in_sources",
                text=result["message"],
                intent={"facet": result["extracted"]["facet"]},
                choices=[fallback_query],
            )

        new_proc_code = result["primary"]["procedure"]["proc_code"]
        active_proc_code = _active_proc_code(active)

        if active_proc_code and active_proc_code == new_proc_code:
            status("Đang soạn giải đáp từ bảng thủ tục…")
            answer_text = customer_care.answer_procedure_query(
                result["primary"], question, result["extracted"]["facet"], history)
            return TurnResult(
                kind="answer", text=answer_text,
                intent={"proc_code": new_proc_code, "facet": result["extracted"]["facet"]},
            )

        status("Đang dựng Thẻ thủ tục…")
        html_out = s2.render_card(result["primary"], facet=result["extracted"]["facet"],
                                  suggestion=result["suggestion"])
        return TurnResult(
            kind="procedure_card", text=html_out,
            intent={"proc_code": new_proc_code, "facet": result["extracted"]["facet"]},
        )
    finally:
        conn.close()

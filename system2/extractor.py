"""extractor.py — LLM1: trích primary_keyword / province / facet từ câu hỏi
tự nhiên của người dân, nối thẳng vào service.resolve_query().

Batch-test 56 câu (calibrate.py, xem results_calibrate.md) đo được: tầng DB
(FTS5 khớp từ khoá) chỉ tự hiểu đúng 5% câu hỏi thô (0% câu hỏi đơn), trong
khi khớp 100% nếu đưa đúng tên thủ tục chuẩn vào. Đây chính là khoảng trống
module này phải lấp — KHÔNG viết thêm rule bắt từ khoá, dùng LLM.

Tái dùng NGUYÊN VẸN `app/core/llm.py` (cổng Ollama JSON-schema-constrained
của System 1) — chỉ thêm 1 vai mới "extract_s2" vào ROLE_OPTIONS ở đó. Prompt
+ schema định nghĩa RIÊNG ở đây (không đụng app/prompts/templates.py) vì
facet/keyword-cho-FTS5 là khái niệm của System 2, không phải System 1.

Dùng:
    python extractor.py --demo "vk e mới đẻ hôm qua, giờ làm giấy tờ cho bé ntn a"
    python extractor.py --demo "lệ phí bao nhiêu" --history-demo-khai-sinh
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_DIR = HERE.parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core import llm  # noqa: E402

import service as s2  # noqa: E402  (cùng thư mục system2/)

FACET_KEYS = ["tong_quan", "le_phi", "ho_so", "thoi_gian", "noi_nop"]

# Ngày Thứ 5 (23/09/2026, Fix 1): intent_type ép model TỰ phân loại Ý ĐỊNH câu
# hỏi qua JSON schema (Ollama schema-constrained) -- KHÔNG dùng danh sách từ
# khoá cố định kiểu is_chitchat() (dễ vỡ: "chào bạn" tách token sẽ trượt nếu
# check theo từng token). "procedure" là fallback AN TOÀN khi model trả giá
# trị ngoài enum: coi như câu hỏi thủ tục thật (đi tiếp qua FTS5, tối đa ra
# not_in_sources) thay vì âm thầm nuốt mất câu hỏi thật của dân thành 1 câu
# chào xã giao.
INTENT_TYPES = ["procedure", "chitchat", "out_of_scope"]

EXTRACT_S2_SCHEMA = {
    "type": "object",
    "properties": {
        "intent_type": {"type": "string", "enum": INTENT_TYPES},
        "primary_keyword": {"type": "string"},
        "province": {"type": "string"},
        "facet": {"type": "string", "enum": FACET_KEYS},
    },
    "required": ["intent_type", "primary_keyword", "province", "facet"],
}


def _system_prompt() -> str:
    return """Bạn trích thông tin từ câu hỏi của người dân về thủ tục hành chính Việt Nam để đưa vào bộ máy tìm kiếm nội bộ (khớp từ khoá, KHÔNG tự hiểu câu hỏi tự nhiên). Người hỏi hay viết không dấu, viết tắt, sai chính tả, hoặc chỉ hỏi tiếp không nhắc lại tên thủ tục.

Đọc lịch sử hội thoại (nếu có) và câu hỏi mới nhất, trả về JSON:
- intent_type: phân loại Ý ĐỊNH của câu hỏi MỚI NHẤT —
  + procedure = người dân đang hỏi/hỏi tiếp về MỘT thủ tục hành chính cụ thể (tên thủ tục, hồ sơ, lệ phí, thời gian giải quyết, nơi nộp...), kể cả câu hỏi tiếp ngắn gọn không nhắc lại tên thủ tục (vd "lệ phí bao nhiêu", "hồ sơ cần gì"). Câu vừa cảm ơn vừa hỏi tiếp (vd "cảm ơn nhé, thế còn lệ phí thì sao") VẪN LÀ procedure, không phải chitchat.
  + chitchat = CHỈ xã giao thuần tuý, KHÔNG kèm nội dung hỏi thủ tục nào (chào hỏi, cảm ơn, tạm biệt -- vd "chào bạn", "alo", "cảm ơn nhé", "tạm biệt", "chào ạ").
  + out_of_scope = câu hỏi hoàn toàn KHÔNG liên quan thủ tục hành chính nhà nước (nấu ăn, giải toán, thơ ca, tin tức, hỏi về bản thân AI...).
  Khi intent_type là chitchat hoặc out_of_scope, để primary_keyword là chuỗi rỗng "".
- primary_keyword: TÊN THỦ TỤC HÀNH CHÍNH ở dạng chuẩn, có dấu, ngắn gọn (vd "đăng ký khai sinh", "cấp lại thẻ căn cước", "đăng ký kết hôn"). Đây là từ khoá tìm kiếm — CHỈ ghi tên thủ tục, KHÔNG ghi kèm khía cạnh đang hỏi (lệ phí, hồ sơ, thời gian...).
  + Nếu câu hỏi mới không tự nhắc tên thủ tục nào (hỏi tiếp kiểu "lệ phí bao nhiêu", "hồ sơ cần gì", "cái đó nộp ở đâu"), BẮT BUỘC lấy lại đúng tên thủ tục đang nói ở lịch sử gần nhất — tuyệt đối không bịa, không tự đổi sang thủ tục khác.
  + Nếu người dùng chuyển hẳn sang thủ tục mới hoàn toàn, dùng thủ tục mới, không giữ thủ tục cũ.
  + Nếu không suy ra được thủ tục nào cả (kể cả từ lịch sử), để nguyên câu hỏi gốc đã chuẩn hoá lỗi chính tả/viết tắt cơ bản, không bịa tên thủ tục.
- province: tỉnh/thành người dùng nói tới (nơi họ sẽ nộp hồ sơ), giữ nguyên tên như người dùng nói. Không có thì để chuỗi rỗng "".
- facet: khía cạnh người dùng đang hỏi —
  tong_quan = hỏi chung, muốn biết tổng quan thủ tục, hoặc không rõ hỏi khía cạnh nào
  le_phi = hỏi phí, lệ phí, tốn bao nhiêu tiền
  ho_so = hỏi hồ sơ, giấy tờ cần chuẩn bị, thành phần hồ sơ, mẫu đơn
  thoi_gian = hỏi thời gian giải quyết, mất bao lâu, bao nhiêu ngày
  noi_nop = hỏi nộp ở đâu, cơ quan nào giải quyết, làm online/trực tuyến được không

Các lượt mẫu phía trước (nếu có) chỉ minh hoạ cách trả JSON, KHÔNG phải lịch sử thật của người dùng này."""


def _history_digest(history: list[dict] | None, limit: int = 4) -> str:
    if not history:
        return ""
    lines = []
    for turn in history[-limit:]:
        role = "Người dùng" if turn.get("role") == "user" else "Trợ lý"
        content = (turn.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _user_prompt(question: str, history: list[dict] | None) -> str:
    parts = []
    digest = _history_digest(history)
    if digest:
        parts.append(f"Lịch sử gần nhất:\n{digest}")
    parts.append(f"Câu hỏi mới: {question}")
    return "\n\n".join(parts)


def extract(question: str, history: list[dict] | None = None) -> dict:
    """Trả {"intent_type", "primary_keyword", "province", "facet"} — sẵn sàng
    đưa thẳng vào service.resolve_query(conn, primary_keyword, province=province)
    rồi service.render_card(full, facet=facet) khi intent_type=="procedure".

    Không tự bịa: nếu model trả rỗng/thiếu trường, fallback về câu hỏi gốc
    (primary_keyword) / "" (province) / "tong_quan" (facet) / "procedure"
    (intent_type) thay vì crash. Fallback intent_type CỐ Ý là "procedure"
    (fail open): model trả giá trị ngoài enum thì thà đi tiếp qua FTS5 (tối
    đa ra not_in_sources, vẫn có nút chuyển System 1) còn hơn âm thầm nuốt
    mất câu hỏi thật của dân thành 1 câu chào xã giao."""
    raw = llm.chat_json("extract_s2", _system_prompt(), _user_prompt(question, history),
                         EXTRACT_S2_SCHEMA)
    intent_type = raw.get("intent_type") if raw.get("intent_type") in INTENT_TYPES else "procedure"
    keyword = (raw.get("primary_keyword") or "").strip() or question.strip()
    province = (raw.get("province") or "").strip() or None
    facet = raw.get("facet") if raw.get("facet") in FACET_KEYS else "tong_quan"
    return {"intent_type": intent_type, "primary_keyword": keyword, "province": province, "facet": facet}


def format_not_found(question: str, extracted: dict) -> str:
    """Câu báo lỗi chuẩn khi found=False hoặc confident=False (yêu cầu Leader,
    22/09/2026 — dùng để debug): 'Xin lỗi tôi không tìm thấy <keyword AI
    trích> cho câu hỏi <câu gốc của người dùng>'.

    Đặt Ở ĐÂY (extractor.py), KHÔNG đặt trong service.resolve_query(): hàm đó
    chỉ nhận `keyword` (đã trích), không có `question` GỐC — nhét câu gốc vào
    sẽ phải đổi chữ ký resolve_query(), ảnh hưởng cả calibrate.py (gọi thẳng
    resolve_query() với keyword=topic, không có "câu hỏi thô" nào để đưa vào).
    Ở extractor.resolve(), cả 2 giá trị đã có sẵn trong cùng 1 chỗ.

    Có cả 2 giá trị trong câu báo lỗi giúp debug phân biệt: LLM1 trích sai từ
    khoá (keyword vô lý so với câu hỏi) hay tầng DB thật sự không có thủ tục
    đó (keyword hợp lý nhưng vẫn found=False/confident=False)."""
    keyword = extracted.get("primary_keyword") or ""
    return f"Xin lỗi, tôi không tìm thấy '{keyword}' cho câu hỏi '{question}'."


def resolve(question: str, history: list[dict] | None = None, conn=None) -> dict:
    """Pipeline đầy đủ: câu hỏi thô -> extract() (LLM1) -> resolve_query()
    (tầng DB, service.py) -> kết quả kèm `extracted` (facet đã trích, để gọi
    render_card()) và `message` (chuỗi báo lỗi chuẩn, chỉ có giá trị khi
    found=False hoặc confident=False — None nếu tìm được chắc chắn, tầng gọi
    tự quyết định hiện `message` này hay hiện card + cảnh báo).

    intent_type != "procedure" (chitchat/out_of_scope, Fix 1 Ngày Thứ 5): BỎ
    QUA resolve_query() (0 query FTS5, tiết kiệm tài nguyên) — trả thẳng kết
    quả rỗng nhưng GIỮ NGUYÊN `extracted` đầy đủ để pipeline.py đọc
    extracted["intent_type"] mà phân nhánh chitchat/out_of_scope chính xác,
    không gộp lẫn 2 loại lại thành 1.

    Tự mở/đóng connection nếu không truyền `conn`."""
    own_conn = conn is None
    if own_conn:
        conn = s2.connect()
    try:
        extracted = extract(question, history)
        if extracted["intent_type"] != "procedure":
            # ponytail: skip DB query khi không phải thủ tục
            return {
                "found": False, "confident": False, "primary": None, "suggestion": None,
                "extracted": extracted, "message": None,
                "debug": {"intent_type": extracted["intent_type"]},
            }
        result = s2.resolve_query(conn, extracted["primary_keyword"], province=extracted["province"])
        result["extracted"] = extracted
        result["message"] = (None if result["found"] and result["confident"]
                              else format_not_found(question, extracted))
        return result
    finally:
        if own_conn:
            conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo extractor.py + service.py end-to-end")
    ap.add_argument("--demo", required=True, help="Câu hỏi thô cần trích")
    ap.add_argument("--db", default=str(s2.DEFAULT_DB))
    ap.add_argument("--out", default=None, help="Ghi HTML card ra file (mặc định chỉ in JSON)")
    args = ap.parse_args()

    conn = s2.connect(args.db)
    try:
        result = resolve(args.demo, conn=conn)
    finally:
        conn.close()

    print("extracted:", result["extracted"])
    print("found:", result["found"], "confident:", result["confident"])
    if result["found"]:
        print("primary:", result["primary"]["procedure"]["name"])
    if result["suggestion"]:
        print("suggestion:", result["suggestion"]["name"])
    if result["message"]:
        print("message:", result["message"])

    if args.out and result["found"]:
        html = s2.render_card(result["primary"], facet=result["extracted"]["facet"],
                               suggestion=result["suggestion"])
        Path(args.out).write_text(html, encoding="utf-8")
        print(f"-> đã ghi {args.out}")


if __name__ == "__main__":
    main()

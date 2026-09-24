"""customer_care.py — LLM 2 Customer Care: giải đáp chi tiết Turn 2+ khi người
dân vẫn đang hỏi về CÙNG một thủ tục đã mở Thẻ ở Turn 1 (xác nhận bằng so sánh
proc_code — xem pipeline.py). Trả lời BÁM SÁT bảng dữ liệu có cấu trúc (tên,
cơ quan, hình thức nộp, checklist, lệ phí, biểu mẫu) — không tra Web/RAG, vì
dữ liệu đã có sẵn, có cấu trúc, đã kiểm duyệt (System 2 đảm bảo 0% ảo giác).

Out-of-table Guard (bắt buộc, yêu cầu Leader): câu hỏi ngoài bảng niêm yết
(giờ làm việc thứ 7, tên cán bộ thụ lý, số điện thoại bàn, v.v.) -> LLM PHẢI
trả lời trung thực là KHÔNG có trong bảng, hướng dẫn liên hệ trực tiếp cơ quan
tiếp nhận hoặc bấm nút "Tra cứu Web trực tiếp" ở chân thẻ — tuyệt đối không
bịa. Test tự động (test_customer_care.py) chỉ kiểm tra WIRING (đúng role, đúng
dữ liệu bảng, đúng câu hỏi được gửi tới model) — hành vi "có từ chối bịa thật
không" là hành vi của LLM THẬT, phải kiểm tra tay trên Ollama (Kịch bản 6,
xem README/plan Ngày Thứ 4, mục 3.2).

Dùng:
    python customer_care.py --demo "lệ phí bao nhiêu" --proc "đăng ký kết hôn"
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

FACET_LABELS = {
    "tong_quan": "tổng quan", "le_phi": "lệ phí", "ho_so": "hồ sơ",
    "thoi_gian": "thời gian giải quyết", "noi_nop": "nơi nộp",
}


def _table_digest(full: dict) -> str:
    """Đóng gói bảng dữ liệu thủ tục (procedure + checklists + fees + files)
    thành văn bản THUẦN gọn cho system prompt — không phải HTML."""
    p = full["procedure"]
    lines = [
        f"Tên thủ tục: {p.get('name')}",
        f"Cơ quan giải quyết: {p.get('authority') or 'Chưa rõ'}",
        f"Hình thức nộp: {p.get('application_method') or 'Chưa rõ'}",
    ]
    if p.get("receiving_location"):
        lines.append(f"Địa điểm nộp trực tiếp: {p['receiving_location']}")
    if p.get("online_url"):
        lines.append(f"Link nộp trực tuyến: {p['online_url']}")
    lines.append(f"Thời hạn giải quyết: {p.get('duration_desc') or 'Chưa rõ'}")
    if p.get("description"):
        lines.append(f"Mô tả: {p['description']}")

    lines.append("Lệ phí:")
    fees = full.get("fees") or []
    if fees:
        for f in fees:
            cond = f" (điều kiện: {f['condition']})" if f.get("condition") else ""
            lines.append(f"  - {f['fee_type']}: {f['amount_text']}{cond}")
    else:
        lines.append("  - Chưa có thông tin lệ phí.")

    lines.append("Checklist hồ sơ cần chuẩn bị:")
    checklist = full.get("checklists") or []
    if checklist:
        for c in checklist:
            note = f" ({c['note']})" if c.get("note") else ""
            lines.append(f"  - {c['content']}{note}")
    else:
        lines.append("  - Chưa có checklist hồ sơ.")

    lines.append("Biểu mẫu đính kèm:")
    files = full.get("files") or []
    if files:
        for f in files:
            lines.append(f"  - {f['file_name']}")
    else:
        lines.append("  - Chưa có biểu mẫu đính kèm.")

    return "\n".join(lines)


def _system_prompt(facet: str | None) -> str:
    hint = FACET_LABELS.get(facet or "", "")
    focus = f" Người dân vừa hỏi khía cạnh: {hint}." if hint else ""
    return f"""Bạn là Trợ lý Dịch vụ công, trả lời câu hỏi của người dân VỀ MỘT thủ tục hành chính cụ thể, CHỈ DỰA vào bảng dữ liệu niêm yết dưới đây (dữ liệu đã kiểm duyệt).{focus}

QUY TẮC BẮT BUỘC — Out-of-table Guard:
Nếu câu hỏi hỏi về điều KHÔNG có trong bảng (ví dụ: "thứ 7 có làm việc không", "cán bộ nào thụ lý", "có số điện thoại bàn không", giờ giấc cụ thể, tên người phụ trách...), PHẢI trả lời trung thực là thông tin này KHÔNG có trong bảng niêm yết, và hướng dẫn người dân liên hệ trực tiếp cơ quan tiếp nhận hồ sơ (nêu tên cơ quan nếu bảng có) hoặc dùng nút "Tra cứu Web trực tiếp" ở chân thẻ. TUYỆT ĐỐI KHÔNG bịa đặt, không đoán, không suy diễn thông tin ngoài bảng.

Trả lời ngắn gọn, đúng trọng tâm câu hỏi, giọng thân thiện, dễ hiểu cho người dân."""


def _clean_history(history: list[dict] | None, limit: int = 6) -> list[dict]:
    """Loại bỏ các lượt kind="procedure_card" (nội dung là HTML thô của Thẻ,
    KHÔNG phải chữ) khỏi lịch sử gửi LLM — bảng dữ liệu hiện tại đã được đưa
    riêng vào system prompt qua _table_digest(), lịch sử chỉ cần phần hỏi-đáp
    bằng chữ. Nhét thẳng HTML thô vào đây sẽ làm rối mô hình nhỏ."""
    out = [{"role": h.get("role"), "content": h.get("content") or ""}
           for h in (history or []) if h.get("kind") != "procedure_card"]
    return out[-limit:]


def answer_procedure_query(procedure_full: dict, question: str, facet: str | None,
                            history: list[dict] | None = None) -> str:
    """Trả lời câu hỏi chuyên sâu của người dân dựa trên bảng dữ liệu thủ tục
    có cấu trúc (Turn 2+, đã xác nhận cùng proc_code với Thẻ đang mở)."""
    digest = _table_digest(procedure_full)
    user_prompt = f"Bảng dữ liệu thủ tục:\n{digest}\n\nCâu hỏi của người dân: {question}"
    return llm.chat("customer_care_s2", _system_prompt(facet), user_prompt,
                    _clean_history(history))


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo customer_care.py trên DB thật")
    ap.add_argument("--demo", required=True, help="Câu hỏi Turn 2+ cần LLM 2 trả lời")
    ap.add_argument("--proc", required=True, help="Từ khoá/tên thủ tục đang mở (để tra bảng)")
    ap.add_argument("--facet", default="tong_quan", choices=list(FACET_LABELS))
    ap.add_argument("--db", default=str(s2.DEFAULT_DB))
    args = ap.parse_args()

    conn = s2.connect(args.db)
    try:
        result = s2.resolve_query(conn, args.proc)
    finally:
        conn.close()
    if not result["found"]:
        print(f"Không tìm được thủ tục nào khớp '{args.proc}' để demo.")
        return
    print("Đang hỏi LLM 2 về:", result["primary"]["procedure"]["name"])
    print()
    print(answer_procedure_query(result["primary"], args.demo, args.facet))


if __name__ == "__main__":
    main()

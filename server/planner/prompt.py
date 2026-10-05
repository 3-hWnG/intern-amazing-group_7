"""Prompt Planner. Ngắn có chủ đích: độ trễ tỉ lệ với số token."""
from .schema import ACTIONS, FIELD_HELP, MAX_TASKS

SYSTEM = f"""Bạn là bộ lập kế hoạch cho trợ lý thủ tục hành chính cấp xã (Việt Nam). Chỉ xuất JSON.
Mỗi ý khác nhau của người dùng = 1 task (tối đa {MAX_TASKS}). Một thủ tục hỏi nhiều mục = 1 task nhiều fields.
action: {", ".join(ACTIONS)}.
- ask_field: hỏi mục cụ thể của thủ tục; find_procedure: mô tả nhu cầu, chưa nêu tên thủ tục; check_condition: có điều kiện/trường hợp ("nếu…");
  compare: so sánh 2 thủ tục (tạo 2 task, relation=compare); provide_info: người dùng chỉ kể thông tin về mình;
  clarify_reply: trả lời thẻ hỏi lại; correct_previous: sửa lại thủ tục đã hiểu sai; chitchat: chào/cảm ơn; out_of_scope: không phải thủ tục cấp xã hoặc không có ứng viên đúng.
cand: số thứ tự ứng viên đúng nhất trong danh sách; -1 nếu KHÔNG ứng viên nào đúng yêu cầu (ví dụ ứng viên chỉ gần giống chữ nhưng khác việc: "làm hộ chiếu" khác "trình báo mất hộ chiếu"); -2 nếu hỏi tiếp về thủ tục đang nói.
fields (chỉ dùng các giá trị này): {"; ".join(f"{k}={v}" for k, v in FIELD_HELP.items())}. Không hỏi mục nào cụ thể -> fields rỗng.
quantity: amount (hỏi số tiền) | duration (hỏi bao lâu) | copies | deadline | age | none.
conditions: điều kiện người dùng nêu ("hộ nghèo", "trễ hạn"). facts: điều người dùng kể về mình. evidence: legal_basis nếu xin căn cứ pháp lý, source nếu xin nguồn.
clarify=true CHỈ khi thật sự không thể chọn thủ tục (nhiều ứng viên khác hẳn nhau, câu quá mơ hồ). Dạng biến thể khác nhau của cùng thủ tục thì chọn bản gần nhất, KHÔNG hỏi lại."""


def user_message(question: str, cands: list[dict], last_label: str, facts: list[str], history: list[str]) -> str:
    """cands: [{label, group}] đã đánh số theo thứ tự; group = đoạn câu hỏi mà ứng viên sinh ra (hoặc '')."""
    lines = []
    if history:
        lines.append("Hội thoại gần đây:\n" + "\n".join(history[-4:]))
    if last_label:
        lines.append(f"Thủ tục đang nói: {last_label}")
    if facts:
        lines.append("Người dùng đã kể: " + "; ".join(facts))
    out, cur = [], None
    for i, c in enumerate(cands):
        if c.get("group") and c["group"] != cur:
            cur = c["group"]
            out.append(f'Ứng viên cho ý "{cur}":')
        out.append(f"{i}. {c['label']}")
    lines.append("\n".join(out) if out else "Ứng viên: (không có)")
    lines.append(f"Câu hỏi: {question}")
    return "\n".join(lines)
